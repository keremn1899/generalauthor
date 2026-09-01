"""Frozen-metric analysis of a sealed Stage 1 campaign."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any

from research.taskview_orientation.freeze import MANIFEST_PATH
from research.taskview_orientation.runtime_manifest import DIMENSION_FIELD_MAP, EPISODES
from research.taskview_orientation.telemetry import FrozenSpanClassifier
from research.taskview_orientation.runner import CLASSIFICATION_PATH


def _events(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _dimension_scores(record: dict[str, Any]) -> dict[str, dict[str, Any]]:
    scores = {
        score["phase"]: score["field_scores"] for score in record["oracle_scores"]
    }
    output = {}
    for dimension, fields in DIMENSION_FIELD_MAP.items():
        values = [bool(scores[phase][field]) for phase, field in fields]
        output[dimension] = {
            "correct": sum(values),
            "count": len(values),
            "rate": sum(values) / len(values),
            "all_correct": all(values),
        }
    return output


def _episode_summary(root: Path, episode: dict[str, Any]) -> dict[str, Any]:
    episode_root = root / episode["episode_id"]
    record = json.loads((episode_root / "record.json").read_text(encoding="utf-8"))
    events = _events(episode_root / "telemetry.jsonl")
    classifier = FrozenSpanClassifier.load(CLASSIFICATION_PATH)
    local_by_phase = {}
    for phase in range(1, 6):
        phase_events = [
            event
            for event in events
            if event["phase"] == phase
            and event["event_type"] in {"SOURCE_READ", "SOURCE_SEARCH"}
        ]
        local_read = False
        local_bytes = 0
        for event in phase_events:
            counts = classifier._event_label_bytes(event)
            local_bytes += counts["LOCAL_ORACLE"]
            if event["event_type"] == "SOURCE_READ" and counts["LOCAL_ORACLE"] > 0:
                local_read = True
        local_by_phase[str(phase)] = {
            "local_oracle_bytes": local_bytes,
            "inspected_local_source": local_read,
        }
    field_correct = sum(score["correct_fields"] for score in record["oracle_scores"])
    field_count = sum(score["field_count"] for score in record["oracle_scores"])
    return {
        "campaign_episode_id": episode["episode_id"],
        "arm": episode["arm"],
        "replicate": episode["replicate"],
        "O_post": record["metrics"]["O_post"],
        "net_orientation_bytes": record["metrics"]["net_orientation_bytes"],
        "LOCAL_ORACLE_bytes": record["metrics"]["label_bytes"]["LOCAL_ORACLE"],
        "focus_ratio": record["metrics"]["focus_ratio"],
        "phase_focus": record["metrics"]["phase_focus"],
        "broad_searches": record["metrics"]["broad_search_calls"],
        "repeated_broad_searches": record["metrics"]["repeated_broad_searches"],
        "orientation_rereads": record["metrics"]["repeated_orientation_source_reads"],
        "reconstruction_events": record["metrics"]["reconstruction_events"],
        "total_visible_bytes": record["metrics"]["total_model_visible_bytes"],
        "provider_input_tokens": record["metrics"]["provider_input_tokens"],
        "provider_output_tokens": record["metrics"]["provider_output_tokens"],
        "wall_time_ms": record["metrics"]["participant_turn_wall_time_ms"],
        "field_correct": field_correct,
        "field_count": field_count,
        "field_correctness_rate": field_correct / field_count,
        "dimensions": _dimension_scores(record),
        "local_source_by_phase": local_by_phase,
        "local_source_inspection_rate": sum(
            item["inspected_local_source"] for item in local_by_phase.values()
        ) / 5,
        "phase4_reaction": record["oracle_scores"][3],
        "taskview_calls": record["metrics"]["taskview_calls"],
        "taskview_calls_by_operation": record["metrics"]["taskview_calls_by_operation"],
        "taskview_calls_by_variant": record["metrics"].get(
            "taskview_calls_by_variant", {}
        ),
        "describe_catalog_calls": record["metrics"].get(
            "taskview_calls_by_variant", {}
        ).get("describe_catalog", 0),
        "describe_relation_calls": record["metrics"].get(
            "taskview_calls_by_variant", {}
        ).get("describe_relation", 0),
        "describe_why_calls": record["metrics"].get(
            "taskview_calls_by_variant", {}
        ).get("describe_why", 0),
        "taskview_visible_bytes": record["metrics"]["taskview_visible_bytes"],
        "taskview_visible_bytes_by_variant": record["metrics"].get(
            "taskview_visible_bytes_by_variant", {}
        ),
        "post_phase1_repository_bytes_by_phase": {
            str(phase): sum(
                int(event.get("model_visible_output_bytes", 0))
                for event in events
                if event["phase"] == phase
                and event["event_type"] in {"SOURCE_READ", "SOURCE_SEARCH"}
            )
            for phase in range(2, 6)
        },
        "unique_files_read": record["metrics"]["unique_files_read"],
        "repeated_file_reads": record["metrics"]["repeated_file_reads"],
        "answers": record["answers"],
    }


def analyze(root: Path) -> dict[str, Any]:
    seal = json.loads((root / "campaign_seal.json").read_text(encoding="utf-8"))
    if not seal.get("valid") or seal.get("status") != "SEALED":
        raise RuntimeError("campaign is not valid and sealed")
    episodes = [_episode_summary(root, episode) for episode in EPISODES]
    by_key = {(item["arm"], item["replicate"]): item for item in episodes}
    pairs = []
    for replicate in range(1, 5):
        raw = by_key[("RAW", replicate)]
        treatment = by_key[("TASKVIEW", replicate)]
        reduction = (
            (raw["O_post"] - treatment["O_post"]) / raw["O_post"]
            if raw["O_post"]
            else None
        )
        pairs.append(
            {
                "replicate": replicate,
                "RAW_O_post": raw["O_post"],
                "TASKVIEW_O_post": treatment["O_post"],
                "paired_O_post_reduction": reduction,
                "RAW_net_orientation": raw["net_orientation_bytes"],
                "TASKVIEW_net_orientation": treatment["net_orientation_bytes"],
                "net_orientation_difference_TASKVIEW_minus_RAW": (
                    treatment["net_orientation_bytes"] - raw["net_orientation_bytes"]
                ),
                "RAW_local_correctness": raw["dimensions"]["local_implementation_semantics"],
                "TASKVIEW_local_correctness": treatment["dimensions"]["local_implementation_semantics"],
                "RAW_local_source_inspection_rate": raw["local_source_inspection_rate"],
                "TASKVIEW_local_source_inspection_rate": treatment["local_source_inspection_rate"],
                "RAW_changed_evidence": raw["dimensions"]["changed_evidence_reaction"],
                "TASKVIEW_changed_evidence": treatment["dimensions"]["changed_evidence_reaction"],
                "TASKVIEW_usage": treatment["taskview_calls_by_operation"],
            }
        )
    reductions = [pair["paired_O_post_reduction"] for pair in pairs]
    net_differences = [pair["net_orientation_difference_TASKVIEW_minus_RAW"] for pair in pairs]
    wins = sum(pair["TASKVIEW_O_post"] < pair["RAW_O_post"] for pair in pairs)
    raw_local = statistics.mean(
        item["dimensions"]["local_implementation_semantics"]["rate"]
        for item in episodes
        if item["arm"] == "RAW"
    )
    treatment_local = statistics.mean(
        item["dimensions"]["local_implementation_semantics"]["rate"]
        for item in episodes
        if item["arm"] == "TASKVIEW"
    )
    treatment_inspection = statistics.mean(
        item["local_source_inspection_rate"]
        for item in episodes
        if item["arm"] == "TASKVIEW"
    )
    raw_overall = statistics.mean(
        item["field_correctness_rate"] for item in episodes if item["arm"] == "RAW"
    )
    treatment_overall = statistics.mean(
        item["field_correctness_rate"]
        for item in episodes
        if item["arm"] == "TASKVIEW"
    )
    stale_worse_pairs = sum(
        pair["TASKVIEW_changed_evidence"]["rate"]
        < pair["RAW_changed_evidence"]["rate"]
        for pair in pairs
    )
    net_consistently_worse = all(value > 0 for value in net_differences)
    median_reduction = statistics.median(reductions)
    compensating_correctness = treatment_overall > raw_overall
    pass_primary = (
        median_reduction >= 0.30
        and wins >= 3
        and treatment_local >= raw_local
        and treatment_inspection >= 0.80
    )
    kill_primary = (
        ((median_reduction < 0.15 or wins <= 2) and not compensating_correctness)
        or (net_consistently_worse and treatment_overall <= raw_overall)
        or stale_worse_pairs >= 2
    )
    if pass_primary:
        threshold = "PASS"
    elif kill_primary:
        threshold = "FAIL"
    else:
        threshold = "INCONCLUSIVE"
    ignored = sum(
        item["taskview_calls"] == 0 for item in episodes if item["arm"] == "TASKVIEW"
    )
    if threshold == "PASS":
        decision = "CONTINUE TO CROSS-FAMILY REPLICATION"
    elif threshold == "INCONCLUSIVE" or ignored > 2 or treatment_inspection < 0.80:
        decision = "REVISE CASE / APPARATUS AND REPEAT STAGE 1"
    else:
        decision = "KILL / RETHINK TASKVIEW ORIENTATION MECHANISM"
    alternative_path = root / "alternative_witness_adjudication.json"
    alternative = (
        json.loads(alternative_path.read_text(encoding="utf-8"))
        if alternative_path.exists()
        else {"accepted": [], "qualitative_conclusion_changed": False}
    )
    return {
        "campaign_valid": True,
        "manifest_sha256": seal["manifest_sha256"],
        "episodes": episodes,
        "matched_pairs": pairs,
        "aggregate": {
            "median_paired_O_post_reduction": median_reduction,
            "directional_wins": wins,
            "median_net_orientation_difference_TASKVIEW_minus_RAW": statistics.median(
                net_differences
            ),
            "RAW_overall_correctness": raw_overall,
            "TASKVIEW_overall_correctness": treatment_overall,
            "RAW_local_correctness": raw_local,
            "TASKVIEW_local_correctness": treatment_local,
            "TASKVIEW_local_source_inspection_rate": treatment_inspection,
            "stale_anchoring_worse_pairs": stale_worse_pairs,
            "TASKVIEW_ignored_episodes": ignored,
        },
        "threshold_result": threshold,
        "decision": decision,
        "alternative_witness_sensitivity": alternative,
        "dimension_field_map": DIMENSION_FIELD_MAP,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = analyze(args.results)
    if args.out:
        args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
