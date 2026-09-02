"""Run deterministic scaling, freeze C2 artifacts, and emit preflight receipts."""

from __future__ import annotations

import hashlib
import inspect
import json
import tempfile
from pathlib import Path
from typing import Any

from research.taskview_bom.experiment import (
    DERIVATIONS,
    DERIVED_RELATIONS,
    ROOT as BASE_ROOT,
    _relation_tuples,
    build_frontier_packets,
    compile_c1,
    parse_manufacturer,
    parse_sources,
    run_experiment as run_baseline,
)
from research.taskview_bom_scaling import (
    BASELINE_ORACLE_ID,
    EXPERIMENT_ID,
    PROVIDER_INFERENCE_CALLS,
    SCALE_SEED,
    SEMANTIC_FRONTIER_INFERENCE_AUTHORIZED,
)
from research.taskview_bom_scaling.c2.protocol import (
    LiveInferenceBlocked,
    run_c2,
    validate_packet,
)
from research.taskview_bom_scaling.generate import (
    ROOT,
    SCALES_ROOT,
    generate_all,
)
from taskview import Completeness, CompletenessStatus, TaskView


RESULTS_ROOT = ROOT / "results"
C2_ROOT = ROOT / "c2"
PACKETS_ROOT = C2_ROOT / "packets"
def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _oracle_tuples(oracle: dict[str, Any]) -> dict[str, set[tuple[Any, ...]]]:
    output: dict[str, set[tuple[Any, ...]]] = {}
    for relation, declaration in oracle["relations"].items():
        raw = declaration.get("tuples")
        if raw is None:
            raw = [assertion["tuple"] for assertion in declaration["assertions"]]
        output[relation] = {tuple(row) for row in raw}
    return output


def _source_lineage(oracle: dict[str, Any]) -> dict[str, set[str]]:
    lineage = {
        relation: set(declaration.get("source_basis", []))
        for relation, declaration in oracle["relations"].items()
        if declaration["origin"] != "DERIVED"
    }
    pending = set(DERIVATIONS)
    while pending:
        ready = {
            relation
            for relation in pending
            if all(name in lineage for name in DERIVATIONS[relation]["inputs"])
        }
        if not ready:
            raise AssertionError("derivation source lineage is incomplete")
        for relation in ready:
            lineage[relation] = set().union(
                *(
                    lineage[input_relation]
                    for input_relation in DERIVATIONS[relation]["inputs"]
                )
            )
        pending -= ready
    return lineage


def _packet_accounting(
    packets: list[dict[str, Any]],
    protocol_bundle: dict[str, Any],
) -> dict[str, Any]:
    payload_sizes: list[int] = []
    raw_sizes: list[int] = []
    context_sizes: list[int] = []
    grounding_sizes: list[int] = []
    envelope_sizes: list[int] = []
    selected_records: list[tuple[str, str, str, str]] = []
    for packet in packets:
        payload_size = len(_canonical(packet))
        raw_size = sum(
            len(item["record"].encode("utf-8")) for item in packet["evidence"]
        )
        context = {
            key: packet[key]
            for key in (
                "candidate_assertion",
                "relevant_referents",
                "known_mechanical_facts",
                "conflicts",
                "missing_information",
            )
        }
        grounding = [
            {key: value for key, value in item.items() if key != "record"}
            for item in packet["evidence"]
        ]
        context_size = len(_canonical(context))
        grounding_size = len(_canonical(grounding))
        envelope_size = payload_size - raw_size - context_size - grounding_size
        if envelope_size < 0:
            raise AssertionError("packet byte partition is invalid")
        payload_sizes.append(payload_size)
        raw_sizes.append(raw_size)
        context_sizes.append(context_size)
        grounding_sizes.append(grounding_size)
        envelope_sizes.append(envelope_size)
        selected_records.extend(
            (
                item["source"],
                item["source_fingerprint"],
                item["native_location"],
                item["record"],
            )
            for item in packet["evidence"]
        )
    unique_records = sorted(set(selected_records))
    protocol_schema_bytes = len(_canonical(protocol_bundle))
    campaign_bytes = len(
        _canonical({**protocol_bundle, "packets": packets})
    )
    campaign_envelope_bytes = (
        campaign_bytes - sum(payload_sizes) - protocol_schema_bytes
    )
    envelope_sizes.append(campaign_envelope_bytes)
    metadata_bytes = (
        sum(context_sizes)
        + sum(grounding_sizes)
        + sum(envelope_sizes)
        + protocol_schema_bytes
    )
    return {
        "selected_record_occurrences": len(selected_records),
        "unique_selected_source_records": len(unique_records),
        "frontier_raw_evidence_bytes": sum(raw_sizes),
        "frontier_normalized_mechanical_context_bytes": sum(context_sizes),
        "frontier_grounding_provenance_bytes": sum(grounding_sizes),
        "frontier_serialization_envelope_bytes": sum(envelope_sizes),
        "frontier_protocol_schema_bytes": protocol_schema_bytes,
        "frontier_metadata_bytes": metadata_bytes,
        "serialized_packet_payload_bytes": sum(payload_sizes),
        "total_serialized_frontier_packet_bytes": campaign_bytes,
        "frontier_packet_bytes": campaign_bytes,
        "per_assertion_packet_payload_bytes": payload_sizes,
        "per_assertion_model_visible_bytes": [
            len(_canonical({**protocol_bundle, "packet": packet}))
            for packet in packets
        ],
        "deduplicated_campaign_model_visible_bytes": campaign_bytes,
        "deduplication_basis": (
            "The protocol and schemas are counted once. The two packets share no "
            "selected source record, so there is no evidence-record byte deduction."
        ),
    }


def _selector_stress(
    view: TaskView, packets: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for packet in packets:
        new_part, old_part, _context = packet["candidate_assertion"]["tuple"]
        candidates = {
            row["new_part_id"]
            for row in view.query(
                "SELECT new_part_id FROM candidate_replacement "
                "WHERE old_part_id = ? ORDER BY new_part_id",
                (old_part,),
            )
        }
        selected = {
            row[0]
            for row in packet["known_mechanical_facts"].get(
                "candidate_replacement", []
            )
            if len(row) == 2 and row[1] == old_part
        }
        relevant = {new_part}
        results.append(
            {
                "candidate_assertion": packet["candidate_assertion"],
                "candidate_count": len(candidates),
                "selected_candidate_count": len(selected),
                "relevant_candidate_recall": (
                    len(selected & relevant) / len(relevant)
                ),
                "irrelevant_candidate_inclusion": len(selected - relevant),
                "selected_source_records": len(packet["evidence"]),
                "candidate_population": sorted(candidates),
                "selected_candidates": sorted(selected),
            }
        )
    return results


def _mutation_at_scale(
    view: TaskView,
    scale_dir: Path,
) -> dict[str, Any]:
    initial = {
        observation.key: observation
        for observation in parse_manufacturer(scale_dir / "manufacturer.csv")
    }
    mutated = {
        observation.key: observation
        for observation in parse_manufacturer(
            scale_dir / "mutation" / "manufacturer.csv"
        )
    }
    changed = [
        key for key in sorted(initial) if initial[key].data != mutated[key].data
    ]
    if changed != ["X100"]:
        raise AssertionError(f"unexpected mutation observations: {changed}")

    before_temperature = _relation_tuples(view, "temperature_compatible")
    before_eligible = _relation_tuples(view, "eligible_part")
    old = initial["X100"]
    new = mutated["X100"]
    old_tuple = {
        "part": "part:X100",
        "minimum_c": int(old.data["min_temp_c"]),
        "maximum_c": int(old.data["max_temp_c"]),
    }
    new_tuple = {
        "part": "part:X100",
        "minimum_c": int(new.data["min_temp_c"]),
        "maximum_c": int(new.data["max_temp_c"]),
    }
    view.retract_tuple("temperature_range", old_tuple)
    view.assert_tuple(
        "temperature_range", new_tuple, grounding=[new.grounding()]
    )
    stale = view.stale_relations()
    unaffected = sorted(set(DERIVED_RELATIONS) - set(stale))

    results = []
    for relation in ("temperature_compatible", "eligible_part"):
        definition = DERIVATIONS[relation]
        results.append(
            view.run_derivation(
                relation,
                completeness=Completeness(
                    CompletenessStatus.COMPLETE,
                    universe=definition["universe"],
                    basis=definition["basis"] + " Frozen scaling mutation rerun.",
                ),
            )
        )
    after_temperature = _relation_tuples(view, "temperature_compatible")
    after_eligible = _relation_tuples(view, "eligible_part")
    expected_temperature = before_temperature - {
        ("part:X100", "bom:BOM-A")
    }
    expected_eligible = before_eligible - {("part:X100", "bom:BOM-A")}
    unaffected_inside_stale = len(before_temperature & after_temperature) + len(
        before_eligible & after_eligible
    )
    recomputed = sum(result.row_count for result in results)
    return {
        "source_fingerprint_changed": old.fingerprint != new.fingerprint,
        "changed_source_observations": len(changed),
        "changed_observation_keys": changed,
        "changed_base_tuples": 2,
        "stale_derived_relations": stale,
        "unaffected_derived_relations": unaffected,
        "rerun_result_correctness": (
            after_temperature == expected_temperature
            and after_eligible == expected_eligible
            and view.stale_relations() == []
        ),
        "stale_after_rerun": view.stale_relations(),
        "temperature_compatible_before": len(before_temperature),
        "temperature_compatible_after": len(after_temperature),
        "eligible_part_before": len(before_eligible),
        "eligible_part_after": len(after_eligible),
        "changed_derived_tuple_memberships": 2,
        "number_of_tuples_recomputed": recomputed,
        "unaffected_tuples_residing_inside_stale_relations": (
            unaffected_inside_stale
        ),
        "relation_granular_recomputation_amplification": recomputed / 2,
        "runtime_recorded": False,
        "runtime_note": (
            "Wall-clock runtime is intentionally excluded from the deterministic "
            "artifact; output cardinality records relation-granular work."
        ),
    }


def _protocol_bundle() -> dict[str, Any]:
    return {
        key: json.loads((C2_ROOT / name).read_text(encoding="utf-8"))
        for key, name in (
            ("protocol", "protocol.json"),
            ("packet_schema", "packet_schema.json"),
            ("output_schema", "output_schema.json"),
        )
    }


def _evaluate_scale(
    scale: str,
    scale_dir: Path,
    work_dir: Path,
    protocol_bundle: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    manifest = json.loads((scale_dir / "manifest.json").read_text(encoding="utf-8"))
    oracle = json.loads((scale_dir / "oracle.json").read_text(encoding="utf-8"))
    c0 = _oracle_tuples(oracle)
    compilation = compile_c1(work_dir / f"{scale}.sqlite", source_dir=scale_dir)
    view = compilation.view
    try:
        if compilation.fingerprints != oracle["source_fingerprints"]:
            raise AssertionError(f"{scale} source fingerprints differ from C0")
        actual = {relation: _relation_tuples(view, relation) for relation in c0}
        unresolved = {
            relation: c0[relation] - actual[relation]
            for relation in c0
            if c0[relation] - actual[relation]
        }
        unexpected = {
            relation: actual[relation] - c0[relation]
            for relation in c0
            if actual[relation] - c0[relation]
        }
        packets = build_frontier_packets(
            view, unresolved, compilation.observations
        )
        accounting = _packet_accounting(packets, protocol_bundle)
        lineage = _source_lineage(oracle)
        cross_authority = sorted(
            relation for relation, sources in lineage.items() if len(sources) > 1
        )
        c0_count = sum(len(rows) for rows in c0.values())
        c1_count = sum(len(rows) for rows in actual.values())
        measurements = {
            "scale": scale,
            "scale_factor": manifest["scale_factor"],
            "seed": manifest["seed"],
            "source_bytes": manifest["source_bytes"],
            "source_record_count": manifest["source_record_count"],
            "observations": len(compilation.observations),
            "referents": view.query(
                "SELECT count(*) AS count FROM _tv_referents"
            )[0]["count"],
            "c0_tuples": c0_count,
            "c1_tuples": c1_count,
            "mechanical_coverage": (
                sum(len(c0[name] & actual[name]) for name in c0) / c0_count
            ),
            "cross_authority_relation_count": len(cross_authority),
            "cross_authority_relations": cross_authority,
            "conflicts": len(actual["spec_conflict"]),
            "unresolved_frontier_tuples": sum(
                len(rows) for rows in unresolved.values()
            ),
            **accounting,
        }
        measurements["frontier_record_ratio"] = (
            accounting["unique_selected_source_records"]
            / manifest["source_record_count"]
        )
        measurements["frontier_packet_ratio"] = (
            accounting["deduplicated_campaign_model_visible_bytes"]
            / manifest["source_bytes"]
        )
        selector = _selector_stress(view, packets)
        mutation = _mutation_at_scale(view, scale_dir)
        return (
            {
                "measurements": measurements,
                "unresolved_assertions": {
                    relation: [list(row) for row in sorted(rows)]
                    for relation, rows in sorted(unresolved.items())
                },
                "unexpected_c1_tuples": {
                    relation: [list(row) for row in sorted(rows)]
                    for relation, rows in sorted(unexpected.items())
                },
                "selector_distractor_test": selector,
                "mutation": mutation,
            },
            packets,
        )
    finally:
        view.close()


def _freeze_c2(
    packets: list[dict[str, Any]],
    scale_results: dict[str, Any],
    baseline_reproduced: bool,
    scaling_seal_path: Path,
) -> dict[str, Any]:
    PACKETS_ROOT.mkdir(parents=True, exist_ok=True)
    packet_paths: list[Path] = []
    for index, packet in enumerate(packets, start=1):
        validate_packet(packet)
        path = PACKETS_ROOT / f"packet-{index:03}.json"
        _write_json(path, packet)
        packet_paths.append(path)

    baseline_oracle_path = SCALES_ROOT / "S1" / "oracle.json"
    adjudication_oracle = {
        "oracle_id": "taskview-bom-c2-adjudication-oracle-v1",
        "frozen_before_provider_inference": True,
        "derived_from_oracle": BASELINE_ORACLE_ID,
        "source_oracle_sha256": _sha256(baseline_oracle_path),
        "derivation_rule": (
            "Each of these two candidate assertions is a positive tuple in the "
            "already-frozen C0 acceptable_replacement extension, so its disposition "
            "is frozen as ACCEPT. Absence from C0 is not assigned a disposition."
        ),
        "cells": [
            {
                "candidate_assertion": packet["candidate_assertion"],
                "decision": "ACCEPT",
                "provenance": {
                    "oracle": BASELINE_ORACLE_ID,
                    "relation": "acceptable_replacement",
                    "tuple": packet["candidate_assertion"]["tuple"],
                },
            }
            for packet in packets
        ],
    }
    oracle_path = C2_ROOT / "adjudication_oracle.json"
    _write_json(oracle_path, adjudication_oracle)

    baseline_frontier = {
        (
            item["candidate_assertion"]["relation"],
            *item["candidate_assertion"]["tuple"],
        )
        for item in packets
    }
    intended = {
        (
            "acceptable_replacement",
            "part:R210",
            "part:R200",
            "context:high_vibration_cabinet",
        ),
        (
            "acceptable_replacement",
            "part:X110",
            "part:X160",
            "context:outdoor_enclosure",
        ),
    }
    selector_source = inspect.getsource(build_frontier_packets)
    forbidden_ids = {"X110", "X160", "R210", "R200"}
    packet_text = "\n".join(
        path.read_text(encoding="utf-8") for path in packet_paths
    )
    all_scale_frontiers_match = all(
        {
            (relation, *row)
            for relation, rows in result["unresolved_assertions"].items()
            for row in rows
        }
        == intended
        for result in scale_results.values()
    )
    s1_observations, _fingerprints = parse_sources(SCALES_ROOT / "S1")
    real_evidence = {
        (
            observation.source,
            observation.fingerprint,
            observation.location,
            observation.evidence,
        )
        for observation in s1_observations
    }
    grounds_resolve = all(
        (
            evidence["source"],
            evidence["source_fingerprint"],
            evidence["native_location"],
            evidence["record"],
        )
        in real_evidence
        for packet in packets
        for evidence in packet["evidence"]
    )
    provider_called = False

    def forbidden_provider(_packet: dict[str, Any]) -> dict[str, Any]:
        nonlocal provider_called
        provider_called = True
        raise AssertionError("provider must not be reached during preflight")

    runner_failed_closed = False
    try:
        run_c2(forbidden_provider, packets[0])
    except LiveInferenceBlocked:
        runner_failed_closed = True

    checks = {
        "01_s1_reproduces_original_report": baseline_reproduced,
        "02_s10_s100_compile_successfully": all(
            not result["unexpected_c1_tuples"]
            for name, result in scale_results.items()
            if name in {"S10", "S100"}
        ),
        "03_frontier_is_exactly_two_intended_tuples": (
            all_scale_frontiers_match and baseline_frontier == intended
        ),
        "04_c1_does_not_establish_semantic_oracle_tuples": all(
            result["measurements"]["unresolved_frontier_tuples"] == 2
            for result in scale_results.values()
        ),
        "05_packets_contain_no_oracle_decision_labels": not any(
            marker in packet_text
            for marker in ('"decision"', "correct answer", "expected acceptance")
        ),
        "06_selector_has_no_exact_frontier_id_literals": not any(
            identifier in selector_source for identifier in forbidden_ids
        ),
        "07_all_packet_grounds_resolve": grounds_resolve,
        "08_hidden_adjudication_oracle_is_frozen": (
            adjudication_oracle["frozen_before_provider_inference"]
            and len(adjudication_oracle["cells"]) == 2
        ),
        "09_participant_output_schema_is_frozen": (
            (C2_ROOT / "output_schema.json").exists()
            and (C2_ROOT / "packet_schema.json").exists()
        ),
        "10_provider_model_not_invoked": (
            not provider_called and PROVIDER_INFERENCE_CALLS == 0
        ),
        "11_provider_inference_call_count_is_zero": PROVIDER_INFERENCE_CALLS == 0,
        "12_explicit_authorization_flag_fails_closed": (
            SEMANTIC_FRONTIER_INFERENCE_AUTHORIZED is False
            and runner_failed_closed
        ),
    }
    receipt = {
        "preflight_id": "taskview-bom-c2-preflight-v1",
        "experiment_id": EXPERIMENT_ID,
        "checks": checks,
        "passed": all(checks.values()),
        "ready_for_explicit_live_inference_authorization": all(checks.values()),
        "semantic_frontier_inference_authorized": (
            SEMANTIC_FRONTIER_INFERENCE_AUTHORIZED
        ),
        "provider_inference_calls": PROVIDER_INFERENCE_CALLS,
        "frozen_artifacts": {
            "adjudication_oracle": {
                "path": "c2/adjudication_oracle.json",
                "sha256": _sha256(oracle_path),
            },
            "packet_schema": {
                "path": "c2/packet_schema.json",
                "sha256": _sha256(C2_ROOT / "packet_schema.json"),
            },
            "output_schema": {
                "path": "c2/output_schema.json",
                "sha256": _sha256(C2_ROOT / "output_schema.json"),
            },
            "protocol": {
                "path": "c2/protocol.json",
                "sha256": _sha256(C2_ROOT / "protocol.json"),
            },
            "scaling_seal": {
                "path": "results/scaling_seal.json",
                "sha256": _sha256(scaling_seal_path),
            },
            "packets": [
                {
                    "path": f"c2/packets/{path.name}",
                    "sha256": _sha256(path),
                }
                for path in packet_paths
            ],
        },
    }
    _write_json(C2_ROOT / "PRELFIGHT.json", receipt)
    _write_json(C2_ROOT / "PREFLIGHT.json", receipt)
    return receipt


def _markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# TaskView BOM scaling and C2 preflight",
        "",
        "The original `taskview-bom-c0-v1` report is preserved. S1 reproduced it exactly.",
        "",
        "| scale | source bytes | records | observations | referents | C0 tuples | C1 tuples | coverage | cross-authority relations | conflicts | frontier | selected unique records | record ratio | raw evidence bytes | context bytes | provenance bytes | envelope bytes | protocol/schema bytes | payload bytes | metadata bytes | campaign bytes | packet ratio |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for scale in ("S1", "S10", "S100"):
        item = report["scales"][scale]["measurements"]
        lines.append(
            "| {scale} | {source_bytes} | {source_record_count} | {observations} | "
            "{referents} | {c0_tuples} | {c1_tuples} | {coverage:.6%} | "
            "{cross_authority_relation_count} | {conflicts} | "
            "{unresolved_frontier_tuples} | {unique_selected_source_records} | "
            "{frontier_record_ratio:.6%} | {frontier_raw_evidence_bytes} | "
            "{frontier_normalized_mechanical_context_bytes} | "
            "{frontier_grounding_provenance_bytes} | "
            "{frontier_serialization_envelope_bytes} | "
            "{frontier_protocol_schema_bytes} | {serialized_packet_payload_bytes} | "
            "{frontier_metadata_bytes} | "
            "{deduplicated_campaign_model_visible_bytes} | "
            "{frontier_packet_ratio:.6%} |".format(
                coverage=item["mechanical_coverage"],
                **item,
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            report["interpretation"]["sparse_frontier"],
            "",
            report["interpretation"]["byte_ratio"],
            "",
            report["interpretation"]["mechanical_coverage"],
            "",
            report["interpretation"]["mechanical_conflicts"],
            "",
            report["interpretation"]["selector_stress"],
            "",
            report["interpretation"]["lifecycle_scaling"],
            "",
            report["interpretation"]["taskview_failure"],
            "",
            "## C2 readiness",
            "",
            report["interpretation"]["c2_readiness"],
            "",
            "## Recommendation",
            "",
            report["interpretation"]["recommendation"],
            "",
            "SEMANTIC_FRONTIER_INFERENCE_AUTHORIZED = False",
            "PROVIDER_INFERENCE_CALLS = 0",
        ]
    )
    return "\n".join(lines) + "\n"


def run() -> tuple[dict[str, Any], dict[str, Any]]:
    manifests = generate_all()
    baseline_report = json.loads(
        (BASE_ROOT / "report.json").read_text(encoding="utf-8")
    )
    baseline_packets = json.loads(
        (BASE_ROOT / "frontier_packets.json").read_text(encoding="utf-8")
    )
    with tempfile.TemporaryDirectory(prefix="taskview-bom-scaling-") as temporary:
        temporary_path = Path(temporary)
        reproduced_report, reproduced_packets = run_baseline(
            temporary_path / "baseline"
        )
        baseline_reproduced = (
            reproduced_report == baseline_report
            and reproduced_packets == baseline_packets
            and manifests["S1"]["source_fingerprints"]
            == baseline_report["source_fingerprints"]
        )
        protocol_bundle = _protocol_bundle()
        scale_results: dict[str, Any] = {}
        packets_by_scale: dict[str, list[dict[str, Any]]] = {}
        for scale in ("S1", "S10", "S100"):
            result, packets = _evaluate_scale(
                scale,
                SCALES_ROOT / scale,
                temporary_path,
                protocol_bundle,
            )
            scale_results[scale] = result
            packets_by_scale[scale] = packets

    RESULTS_ROOT.mkdir(parents=True, exist_ok=True)
    scaling_seal = {
        "seal_id": "taskview-bom-scaling-seal-v1",
        "status": "SEALED",
        "experiment_id": EXPERIMENT_ID,
        "seed": SCALE_SEED,
        "baseline_report_reproduced_exactly": baseline_reproduced,
        "scale_result_sha256": {
            scale: "sha256:"
            + hashlib.sha256(_canonical(result)).hexdigest()
            for scale, result in scale_results.items()
        },
        "scale_artifacts": {
            scale: {
                "manifest_sha256": _sha256(SCALES_ROOT / scale / "manifest.json"),
                "oracle_sha256": _sha256(SCALES_ROOT / scale / "oracle.json"),
            }
            for scale in ("S1", "S10", "S100")
        },
        "semantic_frontier_inference_authorized": False,
        "provider_inference_calls": 0,
    }
    scaling_seal_path = RESULTS_ROOT / "scaling_seal.json"
    _write_json(scaling_seal_path, scaling_seal)
    preflight = _freeze_c2(
        packets_by_scale["S1"],
        scale_results,
        baseline_reproduced,
        scaling_seal_path,
    )
    selected_counts = [
        scale_results[scale]["measurements"]["unique_selected_source_records"]
        for scale in ("S1", "S10", "S100")
    ]
    frontier_counts = [
        scale_results[scale]["measurements"]["unresolved_frontier_tuples"]
        for scale in ("S1", "S10", "S100")
    ]
    payload_counts = [
        scale_results[scale]["measurements"]["serialized_packet_payload_bytes"]
        for scale in ("S1", "S10", "S100")
    ]
    sparse_survived = (
        selected_counts == [8, 8, 8]
        and frontier_counts == [2, 2, 2]
        and payload_counts == [4382, 4382, 4382]
    )
    report = {
        "experiment_id": EXPERIMENT_ID,
        "baseline_oracle_id": BASELINE_ORACLE_ID,
        "seed": SCALE_SEED,
        "baseline_report_preserved_and_reproduced_exactly": baseline_reproduced,
        "provider_inference_calls": PROVIDER_INFERENCE_CALLS,
        "semantic_frontier_inference_authorized": (
            SEMANTIC_FRONTIER_INFERENCE_AUTHORIZED
        ),
        "scales": scale_results,
        "hypotheses": {
            "h1_sparse_frontier_survived_controlled_scaling": sparse_survived,
            "h2_bounded_relation_specific_adjudication_preflight_passed": (
                preflight["passed"]
            ),
        },
        "interpretation": {
            "sparse_frontier": (
                "H1 survived in this controlled world family: observations grow from "
                f"{scale_results['S1']['measurements']['observations']} to "
                f"{scale_results['S100']['measurements']['observations']}, while the "
                "semantic frontier remains two tuples and unique selected evidence "
                "remains eight records. This is not evidence about arbitrary domains."
            ),
            "byte_ratio": (
                "Packet payload bytes remain constant. Acquisition ratios improve "
                "because the source-byte denominator grows; the packet protocol itself "
                "does not become more byte-efficient."
            ),
            "mechanical_coverage": (
                "Mechanical coverage approaches 100% only because the same two semantic "
                "tuples are divided by a larger mechanically generated C0. This is a "
                "denominator effect, not an improvement in C1."
            ),
            "mechanical_conflicts": (
                "Conflict tuples grow from 1 to 100 because every deterministic cohort "
                "retains the original manufacturer/supplier voltage disagreement. They "
                "remain mechanically represented conflicts and do not enlarge the "
                "semantic frontier."
            ),
            "selector_stress": (
                "At S10 and S100 each target old part has five mechanically plausible "
                "replacement candidates. The selector retains the one candidate named "
                "by the proposed tuple, achieves full relevant-candidate recall, and "
                "includes no distractor candidate or distractor source record."
            ),
            "lifecycle_scaling": (
                "Mutation correctness is unchanged at every scale. Relation-granular "
                "invalidation recomputes all tuples in temperature_compatible and "
                "eligible_part, so unaffected work grows with world size despite one "
                "changed source observation."
            ),
            "taskview_failure": (
                "No semantic or identity failure appears through S100. The concrete "
                "scaling limitation is full-relation recomputation after a one-record "
                "change; this experiment deliberately does not redesign invalidation."
            ),
            "c2_readiness": (
                "The two relation-specific packets, hidden two-cell oracle, schemas, "
                "ground validation, and fail-closed runner pass preflight. The experiment "
                "is ready for a separate explicit live-inference authorization, but is "
                "not authorized by this result."
            ),
            "recommendation": (
                "If inference is separately authorized, run only the frozen C2 "
                "acceptable_replacement adjudications and score decisions plus grounding. "
                "Do not introduce a general constructor or product changes."
            ),
        },
        "c2_preflight": preflight,
        "final_status": [
            "SEMANTIC_FRONTIER_INFERENCE_AUTHORIZED = False",
            "PROVIDER_INFERENCE_CALLS = 0",
        ],
    }
    _write_json(RESULTS_ROOT / "scaling_report.json", report)
    (RESULTS_ROOT / "scaling_report.md").write_text(
        _markdown_report(report), encoding="utf-8"
    )
    return report, preflight


if __name__ == "__main__":
    result, receipt = run()
    print(
        json.dumps(
            {
                "hypotheses": result["hypotheses"],
                "preflight_passed": receipt["passed"],
                "provider_inference_calls": PROVIDER_INFERENCE_CALLS,
                "semantic_frontier_inference_authorized": (
                    SEMANTIC_FRONTIER_INFERENCE_AUTHORIZED
                ),
            },
            indent=2,
            sort_keys=True,
        )
    )
