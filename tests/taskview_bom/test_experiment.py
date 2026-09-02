from __future__ import annotations

import json

from research.taskview_bom.experiment import (
    DERIVATIONS,
    FIXTURES,
    compile_c1,
    load_oracle,
    run_experiment,
)


def test_c1_matches_frozen_c0_except_two_semantic_assertions(tmp_path):
    report, packets = run_experiment(tmp_path)

    assert report["provider_inference_calls"] == 0
    assert report["comparison"]["unexpected_c1_tuples"] == {}
    assert report["comparison"]["unresolved_assertions"] == {
        "acceptable_replacement": [
            ["part:R210", "part:R200", "context:high_vibration_cabinet"],
            ["part:X110", "part:X160", "context:outdoor_enclosure"],
        ]
    }
    assert report["measurements"]["c0_assertions_by_construction_origin"] == {
        "MECHANICAL": 131,
        "SEMANTIC": 2,
        "DERIVED": 47,
    }
    assert report["measurements"]["c1_mechanically_established_tuples"] == 178
    assert report["measurements"]["c0_relation_tuples"] == 180
    assert len(packets) == 2


def test_every_mechanical_base_assertion_has_complete_source_grounding(tmp_path):
    compilation = compile_c1(tmp_path / "c1.sqlite")
    view = compilation.view
    try:
        assertions = view.query(
            """
            SELECT a.assertion_id, a.relation_name
            FROM _tv_assertions AS a
            JOIN _tv_relations AS r ON r.name = a.relation_name
            WHERE a.origin = 'ASSERTED' AND r.mode = 'BASE'
            """
        )
        assert assertions
        for assertion in assertions:
            grounds = view.groundings("ASSERTION", assertion["assertion_id"])
            source_grounds = [ground for ground in grounds if ground["kind"] == "SOURCE"]
            assert source_grounds, assertion
            for ground in source_grounds:
                detail = json.loads(ground["detail"])
                assert set(detail) == {
                    "source",
                    "source_fingerprint",
                    "source_native_location",
                    "construction_method",
                }
                assert detail["source_fingerprint"].startswith("sha256:")

        listing = view.assertion_id_for_tuple(
            "listing_of",
            {"listing": "listing:AC-X100", "part": "part:X100"},
        )
        assert {
            json.loads(ground["detail"])["source"]
            for ground in view.groundings("ASSERTION", listing)
        } == {"manufacturer.csv", "suppliers.json"}
    finally:
        view.close()


def test_fixture_preserves_conflict_discontinuation_and_mechanical_cases(tmp_path):
    compilation = compile_c1(tmp_path / "c1.sqlite")
    view = compilation.view
    try:
        assert view.query(
            "SELECT volts FROM rated_voltage WHERE part_id = 'part:X100' ORDER BY volts"
        ) == [{"volts": 24}, {"volts": 28}]
        assert view.query(
            "SELECT part_id, property FROM spec_conflict"
        ) == [{"part_id": "part:X100", "property": "rated_voltage_v"}]
        assert view.query(
            "SELECT state FROM lifecycle WHERE part_id = 'part:X160'"
        ) == [{"state": "discontinued"}]
        assert view.query(
            "SELECT part_id FROM eligible_part WHERE bom_item_id = 'bom:BOM-A' "
            "ORDER BY part_id"
        ) == [
            {"part_id": "part:X100"},
            {"part_id": "part:X110"},
            {"part_id": "part:X140"},
            {"part_id": "part:X180"},
        ]
        assert view.query("SELECT * FROM acceptable_replacement") == []
        for definition in DERIVATIONS.values():
            assert not any(
                fixture_id in definition["sql"]
                for fixture_id in ("X100", "X110", "R200", "BOM-A", "BOM-C")
            )
    finally:
        view.close()


def test_mutation_invalidation_is_relevant_only_and_rerun_is_correct(tmp_path):
    report, _packets = run_experiment(tmp_path)
    mutation = report["mutation"]

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
    assert mutation["excessive_invalidation"] is False
    assert mutation["rerun_result_correctness"] is True
    assert mutation["stale_after_rerun"] == []


def test_frontier_packets_are_selected_not_whole_world_dumps(tmp_path):
    report, packets = run_experiment(tmp_path)

    selected_records = sum(len(packet["evidence"]) for packet in packets)
    assert selected_records == 8
    assert selected_records < report["measurements"]["total_observations"]
    assert all(
        packet["candidate_assertion"]["relation"] == "acceptable_replacement"
        for packet in packets
    )
    assert all(packet["known_mechanical_facts"] for packet in packets)
    assert all("missing_information" in packet for packet in packets)
    assert report["measurements"]["frontier_packet_to_total_evidence_ratio"] > 1


def test_oracle_fingerprints_and_semantic_groundings_are_frozen():
    oracle, tuples = load_oracle()

    assert oracle["frozen_before_c1_evaluation"] is True
    assert oracle["source_fingerprints"] == {
        name: "sha256:" + __import__("hashlib").sha256(
            (FIXTURES / name).read_bytes()
        ).hexdigest()
        for name in (
            "manufacturer.csv",
            "suppliers.json",
            "bom.csv",
            "engineering_notes.md",
        )
    }
    semantic = oracle["relations"]["acceptable_replacement"]
    assert semantic["origin"] == "SEMANTIC"
    assert len(semantic["assertions"]) == len(tuples["acceptable_replacement"]) == 2
    assert all(assertion["grounding"] for assertion in semantic["assertions"])
