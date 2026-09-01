"""Runtime-bound v0.1 preflight; never runs the eight-episode campaign."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from research.taskview_orientation.fixture import SOURCE_ROOT, copy_frozen_task_view
from research.taskview_orientation.freeze import REPOSITORY_ROOT, sha256_file
from research.taskview_orientation.runtime import cursor_version
from research.taskview_orientation.runtime_preflight import _statefulness_probe
from research.taskview_orientation.runtime_sdk import CURSOR_SDK_VERSION, runtime_binding
from research.taskview_orientation.runtime_sdk import CursorSdkParticipantSession
from research.taskview_orientation.surface import ExperimentTaskViewSurface
from research.taskview_orientation.telemetry import TelemetryRecorder, taskview_variant
from research.taskview_orientation.tools import EpisodeTools
from research.taskview_orientation.v01_manifest import V01_MANIFEST_PATH
from research.taskview_orientation.v01_preflight import run_preflight as run_deterministic
from research.taskview_orientation.v01_runtime_manifest import (
    RANDOMIZATION_SEED,
    RUNTIME_FILES,
    RUNTIME_MANIFEST_PATH,
    RUNTIME_PREFLIGHT_RECEIPT,
    RUNTIME_SIDECAR_PATH,
    randomized_order,
)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _runtime_binding() -> dict[str, Any]:
    binding = runtime_binding()
    binding["cursor_agent_version"] = cursor_version()
    return binding


def _check_manifest(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if sha256_file(RUNTIME_MANIFEST_PATH) != RUNTIME_SIDECAR_PATH.read_text().split()[0]:
        errors.append("runtime manifest sidecar drift")
    if manifest["participant_execution_authorized"] is not False:
        errors.append("runtime manifest is participant-authorized")
    if sha256_file(V01_MANIFEST_PATH) != manifest["lineage"]["parent_manifest_sha256"]:
        errors.append("v0.1 parent manifest drift")
    if manifest["randomization"]["randomization_seed"] != RANDOMIZATION_SEED:
        errors.append("randomization seed drift")
    if manifest["randomization"]["arm_order"] != randomized_order():
        errors.append("randomized arm order drift")
    if manifest["randomization"]["old_stage1_order_reused"]:
        errors.append("old Stage 1 arm order was reused")
    if manifest["stage1"]["arm_order"] != manifest["randomization"]["arm_order"]:
        errors.append("stage1 arm order differs from randomization record")
    actual_binding = _runtime_binding()
    if manifest["runtime_binding"] != actual_binding:
        errors.append("runtime binding drift")
    for relative, expected in manifest["runtime_code_hashes"].items():
        if sha256_file(REPOSITORY_ROOT / relative) != expected:
            errors.append(f"runtime code drift: {relative}")
    missing = [relative for relative in RUNTIME_FILES if relative not in manifest["runtime_code_hashes"]]
    if missing:
        errors.append(f"runtime hash inventory missing: {missing}")
    if manifest["prospective_criteria"]["orientation_mechanism"]["rule"][
        "median_paired_O_post_reduction"
    ] != {"operator": ">=", "value": 0.30}:
        errors.append("frozen orientation mechanism criterion changed")
    if manifest["prospective_criteria"]["net_economics"]["success"][
        "median_paired_net_orientation_delta"
    ] != {"operator": "<", "value": 0}:
        errors.append("prospective economic criterion changed")
    return errors


def _live_probe(output_root: Path) -> dict[str, Any]:
    if not os.environ.get("CURSOR_API_KEY"):
        return {
            "status": "BLOCKED",
            "reason": "CURSOR_API_KEY is absent; no provider probe was attempted",
            "provider_calls": 0,
            "statefulness_probe": {"status": "BLOCKED"},
            "dynamic_tool_probe": {"status": "BLOCKED"},
        }
    output_root.mkdir(parents=True, exist_ok=False)
    state = _statefulness_probe(output_root / "statefulness")
    dynamic = _dynamic_tool_probe_v01(output_root / "dynamic")
    return {
        "status": "PASS" if state["status"] == dynamic["status"] == "PASS" else "FAIL",
        "provider_calls": state["turn_count"] + 1,
        "statefulness_probe": state,
        "dynamic_tool_probe": dynamic,
    }


def _dynamic_tool_probe_v01(output_root: Path) -> dict[str, Any]:
    """Exercise the v0.1 MCP surface through one real Cursor SDK turn."""

    workspace = output_root / "workspace"
    workspace.mkdir(parents=True)
    schemas = json.loads(
        (RUNTIME_MANIFEST_PATH.parent.parent / "frozen" / "tool_schemas.json").read_text(
            encoding="utf-8"
        )
    )
    telemetry = TelemetryRecorder(
        episode_id="cursor-v01-dynamic-tool-probe", arm="TASKVIEW", replicate=0
    )
    view = copy_frozen_task_view(output_root / "taskview.sqlite")
    tools = EpisodeTools(
        source_root=SOURCE_ROOT,
        scratch_root=output_root / "scratch",
        telemetry=telemetry,
        taskview=ExperimentTaskViewSurface(view),
    )
    tools.scratch_root.mkdir()
    tools.set_phase(1)
    session = CursorSdkParticipantSession(
        "v0.1 dynamic tool transport preflight only.",
        schemas["native"] + schemas["taskview"],
        "TASKVIEW",
        raw_path=output_root / "provider_trajectory.jsonl",
        state_path=output_root / "provider_state.jsonl",
        workspace=workspace,
        source_root=SOURCE_ROOT,
        scratch_root=tools.scratch_root,
        taskview_path=view.path,
    )
    try:
        turn = session.turn(
            phase=1,
            prompt=(
                "Call exactly these v0.1 MCP operations once each, in this order: "
                "read_source(path='tasks/migrate-jsonlib-v3.md', start_line=1, end_line=2); "
                "describe() with no narrowing; describe(relation='protected_by'); "
                "describe(why={relation:'protected_by', tuple:{service:'service:reporting', "
                "adapter:'adapter:reporting-json-v3'}}); "
                "query_sql(sql='SELECT * FROM protected_by'); "
                "assertion(action='ASSERT', relation='protected_by', values={service: "
                "'service:reporting', adapter:'adapter:reporting-json-v3'}); "
                "rerun(relation='verification_gap'). Then return one JSON object with "
                "direct_change_services:['service:checkout'], decoding_invariants:[], "
                "v3_call_shape:'probe', and citations:[]. Do not call any other tool."
            ),
            answer_fields=[],
            tools=tools,
        )
    finally:
        session.close()
        view.close()
    calls = [
        event for event in telemetry.events if event["event_type"] == "TOOL_CALL"
    ]
    names = [event["tool_name"] for event in calls]
    variants = [
        taskview_variant(event)
        for event in telemetry.events
        if event["event_type"] == "TASKVIEW_TOOL"
    ]
    expected_variants = {
        "describe_catalog",
        "describe_relation",
        "describe_why",
        "query_sql",
        "assertion",
        "rerun",
    }
    expected_names = {"read_source", "describe", "query_sql", "assertion", "rerun"}
    if set(names) != expected_names or set(variants) != expected_variants:
        raise RuntimeError(
            f"v0.1 dynamic tool probe mismatch: names={names}, variants={variants}"
        )
    return {
        "status": "PASS",
        "session_id": turn.session_id,
        "tool_names": names,
        "taskview_variants": variants,
        "logical_tool_call_count": len(calls),
        "answer": turn.answer,
    }


def run_preflight() -> dict[str, Any]:
    manifest = _load(RUNTIME_MANIFEST_PATH)
    errors = _check_manifest(manifest)
    deterministic = run_deterministic()
    if deterministic["status"] != "PASS":
        errors.extend(f"deterministic: {error}" for error in deterministic["errors"])
    live_root = RUNTIME_MANIFEST_PATH.parent.parent / "runtime_preflight" / "taskview-orientation-v01-runtime"
    live = _live_probe(live_root)
    if live["status"] != "PASS":
        errors.append("live provider preflight did not pass")
    return {
        "status": "PASS" if not errors else "BLOCKED" if live["status"] == "BLOCKED" else "FAIL",
        "errors": errors,
        "apparatus_only": True,
        "participant_campaign_calls": 0,
        "provider_preflight_calls": live["provider_calls"],
        "runtime_manifest": str(RUNTIME_MANIFEST_PATH),
        "runtime_manifest_sha256": sha256_file(RUNTIME_MANIFEST_PATH),
        "parent_v01_manifest_sha256": sha256_file(V01_MANIFEST_PATH),
        "cursor_sdk_version": CURSOR_SDK_VERSION,
        "cursor_agent_version": cursor_version(),
        "runtime_binding": _runtime_binding(),
        "deterministic_preflight": deterministic,
        "live_provider_preflight": live,
        "criteria_frozen": True,
        "randomization_seed": RANDOMIZATION_SEED,
        "arm_order": manifest["randomization"]["arm_order"],
        "receipt_path": str(RUNTIME_PREFLIGHT_RECEIPT),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result = run_preflight()
    if args.write:
        RUNTIME_PREFLIGHT_RECEIPT.parent.mkdir(parents=True, exist_ok=True)
        RUNTIME_PREFLIGHT_RECEIPT.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
