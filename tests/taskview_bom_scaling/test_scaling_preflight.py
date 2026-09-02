from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from research.taskview_bom.experiment import ROOT as BASE_ROOT
from research.taskview_bom_scaling import (
    PROVIDER_INFERENCE_CALLS,
    SEMANTIC_FRONTIER_INFERENCE_AUTHORIZED,
)
from research.taskview_bom_scaling.c2.protocol import (
    LiveInferenceBlocked,
    participant_request,
    run_c2,
    validate_output,
)
from research.taskview_bom_scaling.generate import SCALES_ROOT
from research.taskview_bom_scaling.run import C2_ROOT, RESULTS_ROOT, run


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def completed_run():
    baseline_paths = [
        BASE_ROOT / "report.json",
        BASE_ROOT / "frontier_packets.json",
        BASE_ROOT / "oracle.json",
    ]
    before = {path: _sha256(path) for path in baseline_paths}
    report, preflight = run()
    after = {path: _sha256(path) for path in baseline_paths}
    return report, preflight, before, after


def test_s1_reproduces_and_does_not_overwrite_original(completed_run):
    report, _preflight, before, after = completed_run

    assert before == after
    assert report["baseline_report_preserved_and_reproduced_exactly"] is True
    assert (SCALES_ROOT / "S1" / "manufacturer.csv").read_bytes() == (
        BASE_ROOT / "fixtures" / "manufacturer.csv"
    ).read_bytes()
    assert (SCALES_ROOT / "S1" / "oracle.json").read_bytes() == (
        BASE_ROOT / "oracle.json"
    ).read_bytes()


def test_scaling_curves_preserve_two_tuple_sparse_frontier(completed_run):
    report, _preflight, _before, _after = completed_run
    expected = {
        "S1": {
            "observations": 30,
            "source_records": 30,
            "c0": 180,
            "c1": 178,
            "referents": 33,
            "record_ratio": 8 / 30,
        },
        "S10": {
            "observations": 324,
            "source_records": 324,
            "c0": 1896,
            "c1": 1894,
            "referents": 328,
            "record_ratio": 8 / 324,
        },
        "S100": {
            "observations": 3024,
            "source_records": 3024,
            "c0": 17916,
            "c1": 17914,
            "referents": 3118,
            "record_ratio": 8 / 3024,
        },
    }
    for scale, values in expected.items():
        result = report["scales"][scale]
        measurement = result["measurements"]
        assert measurement["observations"] == values["observations"]
        assert measurement["source_record_count"] == values["source_records"]
        assert measurement["c0_tuples"] == values["c0"]
        assert measurement["c1_tuples"] == values["c1"]
        assert measurement["referents"] == values["referents"]
        assert measurement["unresolved_frontier_tuples"] == 2
        assert measurement["unique_selected_source_records"] == 8
        assert measurement["frontier_record_ratio"] == values["record_ratio"]
        assert measurement["serialized_packet_payload_bytes"] == 4382
        assert result["unexpected_c1_tuples"] == {}

    assert report["hypotheses"][
        "h1_sparse_frontier_survived_controlled_scaling"
    ] is True
    assert (
        report["scales"]["S1"]["measurements"]["frontier_packet_ratio"]
        > report["scales"]["S10"]["measurements"]["frontier_packet_ratio"]
        > report["scales"]["S100"]["measurements"]["frontier_packet_ratio"]
    )


def test_packet_accounting_separates_evidence_context_provenance_and_protocol(
    completed_run,
):
    report, _preflight, _before, _after = completed_run
    for result in report["scales"].values():
        measurement = result["measurements"]
        assert measurement["frontier_raw_evidence_bytes"] == 978
        assert measurement["frontier_normalized_mechanical_context_bytes"] == 1934
        assert measurement["frontier_grounding_provenance_bytes"] == 1337
        assert measurement["frontier_serialization_envelope_bytes"] == 147
        assert measurement["frontier_protocol_schema_bytes"] == 2422
        assert measurement["serialized_packet_payload_bytes"] == 4382
        assert measurement["frontier_metadata_bytes"] == 5840
        assert measurement["frontier_packet_bytes"] == 6818
        assert measurement["total_serialized_frontier_packet_bytes"] == 6818
        assert measurement["per_assertion_packet_payload_bytes"] == [2153, 2229]
        assert measurement["per_assertion_model_visible_bytes"] == [4585, 4661]


def test_distractors_stress_selector_without_entering_packets(completed_run):
    report, _preflight, _before, _after = completed_run
    for scale in ("S10", "S100"):
        tests = report["scales"][scale]["selector_distractor_test"]
        assert len(tests) == 2
        assert all(item["candidate_count"] == 5 for item in tests)
        assert all(item["selected_candidate_count"] == 1 for item in tests)
        assert all(item["relevant_candidate_recall"] == 1.0 for item in tests)
        assert all(item["irrelevant_candidate_inclusion"] == 0 for item in tests)
        assert all(item["selected_source_records"] == 4 for item in tests)

    for scale in ("S10", "S100"):
        manifest = json.loads(
            (SCALES_ROOT / scale / "manifest.json").read_text(encoding="utf-8")
        )
        assert "semantic_frontier_assertions" not in manifest
        supplier = json.loads(
            (SCALES_ROOT / scale / "suppliers.json").read_text(encoding="utf-8")
        )
        assert all(
            not ({"relevant", "frontier", "oracle_label"} & set(listing))
            for listing in supplier["listings"]
        )


def test_relation_granular_mutation_cost_grows_without_behavior_change(
    completed_run,
):
    report, _preflight, _before, _after = completed_run
    recomputed = {"S1": 29, "S10": 330, "S100": 3120}
    for scale, expected_recomputed in recomputed.items():
        mutation = report["scales"][scale]["mutation"]
        assert mutation["source_fingerprint_changed"] is True
        assert mutation["changed_source_observations"] == 1
        assert mutation["changed_base_tuples"] == 2
        assert mutation["stale_derived_relations"] == [
            "eligible_part",
            "temperature_compatible",
        ]
        assert mutation["unaffected_derived_relations"] == [
            "spec_conflict",
            "voltage_compatible",
        ]
        assert mutation["rerun_result_correctness"] is True
        assert mutation["number_of_tuples_recomputed"] == expected_recomputed
        assert (
            mutation["unaffected_tuples_residing_inside_stale_relations"]
            == expected_recomputed
        )


def test_c2_is_frozen_grounded_and_fail_closed(completed_run):
    report, preflight, _before, _after = completed_run
    packets = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted((C2_ROOT / "packets").glob("packet-*.json"))
    ]

    assert len(packets) == 2
    assert preflight["passed"] is True
    assert all(preflight["checks"].values())
    assert report["hypotheses"][
        "h2_bounded_relation_specific_adjudication_preflight_passed"
    ] is True
    assert SEMANTIC_FRONTIER_INFERENCE_AUTHORIZED is False
    assert PROVIDER_INFERENCE_CALLS == 0
    request = participant_request(packets[0])
    assert set(request) == {
        "protocol",
        "packet_schema",
        "output_schema",
        "packet",
    }
    assert "decision" not in json.dumps(request["packet"])

    called = False

    def provider(_packet):
        nonlocal called
        called = True
        return {}

    with pytest.raises(LiveInferenceBlocked):
        run_c2(provider, packets[0])
    assert called is False

    evidence = packets[0]["evidence"][0]
    valid = {
        "decision": "UNRESOLVED",
        "grounds": [
            {
                "source": evidence["source"],
                "record_or_span": evidence["native_location"],
            }
        ],
        "reason": "The supplied evidence does not close the prose qualification.",
    }
    assert validate_output(valid, packets[0]) == valid
    invalid = {
        **valid,
        "grounds": [
            {"source": "external.example", "record_or_span": "invented"}
        ],
    }
    with pytest.raises(ValueError, match="does not resolve"):
        validate_output(invalid, packets[0])


def test_report_ends_at_unauthorized_zero_call_stop_condition(completed_run):
    _report, _preflight, _before, _after = completed_run
    lines = (RESULTS_ROOT / "scaling_report.md").read_text(
        encoding="utf-8"
    ).splitlines()
    assert lines[-2:] == [
        "SEMANTIC_FRONTIER_INFERENCE_AUTHORIZED = False",
        "PROVIDER_INFERENCE_CALLS = 0",
    ]
