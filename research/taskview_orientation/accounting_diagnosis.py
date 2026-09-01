"""Zero-cost mechanical replay report for Cursor participant accounting evidence."""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any

from research.taskview_orientation.freeze import REPOSITORY_ROOT, sha256_file
from research.taskview_orientation.runtime_accounting import (
    canonical_tool_arguments,
    observations_from_trajectory,
    reconcile_turn,
    timeline_rows,
    trajectory_event_taxonomy,
)
from research.taskview_orientation.telemetry import FrozenSpanClassifier


ALLOWED_TOOLS = {
    "search_source",
    "read_source",
    "write_scratch",
    "describe",
    "query_sql",
    "assertion",
    "rerun",
}
INVALID_ROOT = (
    REPOSITORY_ROOT
    / "research/taskview_orientation/results/stage1-cursor-v01/"
    "taskview-orientation-v01-e01-taskview-r2"
)
V10_ROOT = REPOSITORY_ROOT / "research/taskview_orientation/results/stage1-cursor-v10"
REPORT_PATH = (
    REPOSITORY_ROOT
    / "research/taskview_orientation/diagnostics/stage1-cursor-v01-accounting-v4.json"
)
SPAN_CLASSIFICATION_PATH = (
    REPOSITORY_ROOT / "research/taskview_orientation/frozen/span_classification.json"
)


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _replay(trajectory_path: Path, bridge_path: Path):
    trajectory = _jsonl(trajectory_path)
    observations = observations_from_trajectory(trajectory)
    session = observations[0].message["agent_id"]
    report = reconcile_turn(
        observations,
        _jsonl(bridge_path),
        expected_session_id=session,
        allowed_tool_names=ALLOWED_TOOLS,
    )
    return trajectory, report


def _signature(tool_name: str, arguments: Any) -> tuple[str, str]:
    return (
        tool_name,
        json.dumps(
            canonical_tool_arguments(tool_name, arguments),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ),
    )


def _corrected_v10_metrics(
    episode_root: Path, report, bridge: list[dict[str, Any]]
) -> dict[str, Any]:
    """Counterfactual metrics only; never rewrites the sealed v10 record."""

    record = json.loads((episode_root / "record.json").read_text(encoding="utf-8"))
    calls = {call.identity: call for call in report.logical_calls}
    successful: dict[tuple[int, tuple[str, str]], deque] = defaultdict(deque)
    for execution in sorted(report.bridge_executions, key=lambda item: item.record_index):
        call = calls[report.execution_to_call[execution.bridge_execution_id]]
        if not call.is_error and call.tool_name != "write_scratch":
            successful[(call.phase, call.signature)].append(call)

    source_events: list[dict[str, Any]] = []
    for bridge_record in bridge:
        if bridge_record["event_type"] not in {"SOURCE_READ", "SOURCE_SEARCH"}:
            continue
        payload = dict(bridge_record["payload"])
        phase = int(bridge_record["phase"])
        call = successful[(phase, _signature(payload["tool_name"], payload["tool_arguments"]))].popleft()
        source_events.append(
            {
                **payload,
                "event_type": bridge_record["event_type"],
                "phase": phase,
                "model_visible_output_bytes": call.model_visible_output_bytes,
            }
        )
    for call in report.logical_calls:
        if call.is_error and call.tool_name in {"read_source", "search_source"}:
            source_events.append(
                {
                    "event_type": "TOOL_ERROR",
                    "phase": call.phase,
                    "tool_name": call.tool_name,
                    "model_visible_output_bytes": call.model_visible_output_bytes,
                }
            )

    classifier = FrozenSpanClassifier.load(SPAN_CLASSIFICATION_PATH)
    post = {"LOCAL_ORACLE": 0, "ORIENTATION_SUPPORT": 0, "IRRELEVANT": 0}
    for event in source_events:
        if event["phase"] >= 2:
            for label, byte_count in classifier._event_label_bytes(event).items():
                post[label] += byte_count
    corrected_o_post = post["ORIENTATION_SUPPORT"] + post["IRRELEVANT"]
    corrected_taskview_post = sum(
        call.model_visible_output_bytes
        for call in report.logical_calls
        if call.phase >= 2 and call.tool_name in {"describe", "query_sql", "assertion", "rerun"}
    )
    return {
        "episode": episode_root.name,
        "replicate": record["replicate"],
        "arm": record["arm"],
        "sealed_O_post": record["metrics"]["O_post"],
        "exact_byte_O_post": corrected_o_post,
        "sealed_taskview_post_bytes": record["metrics"]["taskview_post_bytes"],
        "exact_byte_taskview_post_bytes": corrected_taskview_post,
        "sealed_net_orientation_bytes": record["metrics"]["net_orientation_bytes"],
        "exact_byte_net_orientation_bytes": corrected_o_post + corrected_taskview_post,
    }


def build_report() -> dict[str, Any]:
    trajectory_path = INVALID_ROOT / "provider_trajectory.jsonl"
    bridge_path = INVALID_ROOT / "provider_workspace/logical_tool_telemetry.jsonl"
    trajectory, replay = _replay(trajectory_path, bridge_path)
    bridge = _jsonl(bridge_path)
    bridge_types = Counter(record["event_type"] for record in bridge)

    v10_discrepancies: dict[tuple[str, int], int] = {}
    for telemetry_path in V10_ROOT.glob("*/telemetry.jsonl"):
        for event in _jsonl(telemetry_path):
            if event["event_type"] == "ACCOUNTING_DISCREPANCY":
                v10_discrepancies[(telemetry_path.parent.name, event["phase"])] = event[
                    "overage"
                ]
    v10_executed_errors: dict[tuple[str, int], int] = defaultdict(int)
    v10_episode_summaries = []
    corrected_v10 = []
    for trajectory_file in sorted(V10_ROOT.glob("*/provider_trajectory.jsonl")):
        episode_root = trajectory_file.parent
        bridge_records = _jsonl(
            episode_root / "provider_workspace/logical_tool_telemetry.jsonl"
        )
        trajectory_records = _jsonl(trajectory_file)
        observations = observations_from_trajectory(trajectory_records)
        report = reconcile_turn(
            observations,
            bridge_records,
            expected_session_id=observations[0].message["agent_id"],
            allowed_tool_names=ALLOWED_TOOLS,
        )
        for call in report.logical_calls:
            if call.is_error and not call.provider_validation_rejected:
                v10_executed_errors[(episode_root.name, call.phase)] += 1
        v10_episode_summaries.append(
            {
                "episode": episode_root.name,
                "logical_calls": report.logical_call_count,
                "bridge_executions": len(report.bridge_executions),
                "provider_errors": report.provider_errors,
                "provider_validation_rejections": report.provider_validation_rejections,
            }
        )
        corrected_v10.append(_corrected_v10_metrics(episode_root, report, bridge_records))

    corrected_by_pair = {
        (item["replicate"], item["arm"]): item for item in corrected_v10
    }
    reductions = []
    net_deltas = []
    corrected_wins = 0
    for replicate in range(1, 5):
        raw = corrected_by_pair[(replicate, "RAW")]
        treatment = corrected_by_pair[(replicate, "TASKVIEW")]
        reductions.append(
            (raw["exact_byte_O_post"] - treatment["exact_byte_O_post"])
            / raw["exact_byte_O_post"]
        )
        corrected_wins += treatment["exact_byte_O_post"] < raw["exact_byte_O_post"]
        net_deltas.append(
            treatment["exact_byte_net_orientation_bytes"] - raw["exact_byte_O_post"]
        )
    corrected_median = statistics.median(reductions)

    timeline = timeline_rows(replay)
    return {
        "status": "RECONCILED",
        "participant_calls": 0,
        "source_artifacts": {
            str(trajectory_path.relative_to(REPOSITORY_ROOT)): sha256_file(trajectory_path),
            str(bridge_path.relative_to(REPOSITORY_ROOT)): sha256_file(bridge_path),
        },
        "event_taxonomy": {
            **trajectory_event_taxonomy(trajectory),
            "BRIDGE_REQUEST": 0,
            "BRIDGE_RESPONSE": 0,
            "TOOL_EXECUTION": len(replay.bridge_executions),
            "TOOL_RESULT_DELIVERED_TO_MODEL": replay.logical_call_count,
            "RETRY_REPLAY_DUPLICATE_EVENT": replay.replay_observations,
        },
        "failed_episode": {
            "sdk_tool_lifecycle_observations": replay.sdk_tool_observations,
            "unique_logical_calls": replay.logical_call_count,
            "bridge_raw_records": len(bridge),
            "bridge_raw_event_types": dict(sorted(bridge_types.items())),
            "bridge_executions": len(replay.bridge_executions),
            "successful_results": replay.logical_call_count - replay.provider_errors,
            "executed_error_results": replay.provider_errors,
            "provider_validation_rejections": replay.provider_validation_rejections,
            "model_visible_tool_result_bytes": replay.model_visible_tool_result_bytes,
            "per_operation_response_bytes": replay.per_operation_response_bytes,
            "buggy_v3_decomposition": {
                "bridge_execution_markers": len(replay.bridge_executions),
                "isError_results_misclassified_and_synthesized_again": replay.provider_errors,
                "reported_bridge_count": len(replay.bridge_executions) + replay.provider_errors,
                "reported_sdk_unique_call_ids": replay.logical_call_count,
                "delta": replay.provider_errors,
                "residual": 0,
            },
            "timeline": timeline,
        },
        "retained_telemetry_limits": [
            "Cursor SDK 1.0.30 exposes no separate model-tool-intent event.",
            "The v3 bridge log predates MCP request and bridge response identities; legacy "
            "execution mapping therefore uses phase plus canonical tool signature plus "
            "occurrence, preserving multiplicity.",
            "runtime_state.jsonl is empty because the episode aborted during phase 1.",
            "No canonical telemetry or partial answer record was written before abort.",
        ],
        "sealed_v10_retrospective": {
            "recorded_discrepancy_events": len(v10_discrepancies),
            "recorded_overage_total": sum(v10_discrepancies.values()),
            "executed_error_phase_events": len(v10_executed_errors),
            "executed_error_total": sum(v10_executed_errors.values()),
            "exact_phase_match": dict(v10_discrepancies) == dict(v10_executed_errors),
            "episodes": v10_episode_summaries,
            "assessment": (
                "same isError/pre-handler-rejection classification bug; not boundary timing"
            ),
            "exact_delivered_byte_counterfactual": {
                "historical_files_rewritten": False,
                "episodes": sorted(corrected_v10, key=lambda item: (item["replicate"], item["arm"])),
                "paired_O_post_reductions": reductions,
                "median_paired_O_post_reduction": corrected_median,
                "taskview_lower_O_post_pairs": corrected_wins,
                "net_orientation_deltas": net_deltas,
                "primary_threshold_still_passes": (
                    corrected_median >= 0.30 and corrected_wins >= 3
                ),
                "sealed_decision_remains": "INCONCLUSIVE",
            },
        },
        "scientific_impact": (
            "runtime/accounting only; exact-byte restatement changes historical byte "
            "magnitudes but not the sealed INCONCLUSIVE decision or any TaskView answer"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    report = build_report()
    if args.write:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    print(json.dumps({key: value for key, value in report.items() if key != "failed_episode"}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
