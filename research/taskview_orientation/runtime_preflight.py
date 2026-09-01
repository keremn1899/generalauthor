"""Deterministic and provider-specific preflight for the Cursor default."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import secrets
import tempfile
import time
from pathlib import Path
from typing import Any

from cursor_sdk import Agent, AgentOptions, CursorClient, LocalAgentOptions

from research.taskview_orientation.fixture import FROZEN_ROOT, SOURCE_ROOT, copy_frozen_task_view
from research.taskview_orientation.freeze import (
    PACKAGE_ROOT,
    REPOSITORY_ROOT,
    deterministic_dry_run_receipt,
    sha256_file,
    source_manifest,
)
from research.taskview_orientation.runtime import provider_tools, sha256_json
from research.taskview_orientation.runtime_sdk import (
    ADAPTER_VERSION,
    BUILTIN_TOOL_ALLOWLIST,
    CURSOR_SDK_VERSION,
    MODEL,
    MODEL_DISPLAY_NAME,
    MODEL_PROVIDER,
    TURN_TIMEOUT_SECONDS,
    CursorSdkParticipantSession,
    CursorRuntimeError,
    runtime_binding,
)
from research.taskview_orientation.surface import ExperimentTaskViewSurface
from research.taskview_orientation.telemetry import TelemetryRecorder
from research.taskview_orientation.tools import EpisodeTools
from taskview import TaskViewError


DEFAULT_MANIFEST = FROZEN_ROOT / "experiment_manifest.next.json"


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _check_hashes(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for relative, expected in manifest["all_frozen_input_hashes"].items():
        path = FROZEN_ROOT / relative
        actual = sha256_file(path) if path.is_file() else None
        if actual != expected:
            errors.append(f"frozen input drift: {relative}: {actual} != {expected}")
    for section in ("apparatus_code_hashes", "taskview_runtime_hashes"):
        for relative, expected in manifest[section].items():
            path = REPOSITORY_ROOT / relative
            actual = sha256_file(path) if path.is_file() else None
            if actual != expected:
                errors.append(f"{section} drift: {relative}: {actual} != {expected}")
    if source_manifest()["tree_sha256"] != manifest["source_snapshot"]["tree_sha256"]:
        errors.append("source-tree hash drift")
    return errors


def _deterministic_checks(manifest: dict[str, Any]) -> dict[str, Any]:
    errors = _check_hashes(manifest)
    schemas = json.loads((FROZEN_ROOT / "tool_schemas.json").read_text(encoding="utf-8"))
    raw_names = [record["name"] for record in schemas["native"]]
    treatment_names = [record["name"] for record in schemas["native"] + schemas["taskview"]]
    provider_raw = provider_tools(schemas["native"])
    provider_treatment = provider_tools(schemas["native"] + schemas["taskview"])
    if provider_treatment[: len(provider_raw)] != provider_raw:
        errors.append("Cursor MCP serialization changed native tools by arm")

    current_dry = deterministic_dry_run_receipt()
    frozen_dry = json.loads((FROZEN_ROOT / "dry_run_receipt.json").read_text(encoding="utf-8"))
    if current_dry != frozen_dry:
        errors.append("deterministic Stage 0 dry-run receipt drift")

    with tempfile.TemporaryDirectory(prefix="taskview-cursor-deterministic-") as directory:
        view = copy_frozen_task_view(Path(directory) / "taskview.sqlite")
        surface = ExperimentTaskViewSurface(view)
        try:
            try:
                surface.rerun("verification_gap", universe="participant-supplied")
                errors.append("completeness wrapper accepted participant contract")
            except TaskViewError:
                pass
            before = sha256_file(Path(directory) / "taskview.sqlite")
            tools = EpisodeTools(
                source_root=SOURCE_ROOT,
                scratch_root=Path(directory) / "scratch",
                telemetry=TelemetryRecorder(
                    episode_id="runtime-preflight", arm="TASKVIEW", replicate=0
                ),
                taskview=surface,
            )
            tools.scratch_root.mkdir()
            tools.set_phase(5)
            try:
                tools.assertion(
                    action="ASSERT",
                    relation="verified_by",
                    values={"service": "service:checkout", "test": "test:checkout-contract"},
                )
                errors.append("Phase 5 proposed repair guard accepted mutation")
            except TaskViewError:
                pass
            if before != sha256_file(Path(directory) / "taskview.sqlite"):
                errors.append("Phase 5 proposed repair mutated scored current state")
        finally:
            view.close()

    expected_order = [
        ["RAW", 1], ["TASKVIEW", 1], ["TASKVIEW", 2], ["RAW", 2],
        ["RAW", 3], ["TASKVIEW", 3], ["TASKVIEW", 4], ["RAW", 4],
    ]
    if manifest["stage1"]["arm_order"] != expected_order:
        errors.append("frozen arm assignment/order drift")
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "source_tree_sha256": source_manifest()["tree_sha256"],
        "taskview_database_sha256": sha256_file(FROZEN_ROOT / "taskview.sqlite"),
        "tool_schema_sha256": sha256_file(FROZEN_ROOT / "tool_schemas.json"),
        "provider_serialization_sha256": {
            "RAW": sha256_json(provider_raw), "TASKVIEW": sha256_json(provider_treatment),
        },
        "raw_native_names": raw_names,
        "taskview_visible_names": treatment_names,
        "completeness_contract_rejection": True,
        "phase5_proposed_repair_guard": "PASS",
        "telemetry_logging": "PASS" if current_dry == frozen_dry else "FAIL",
        "arm_order": expected_order,
    }


def _statefulness_probe(output_root: Path) -> dict[str, Any]:
    workspace = output_root / "statefulness_workspace"
    workspace.mkdir(parents=True)
    markers = [f"marker-{index}-{secrets.token_hex(8)}" for index in range(1, 6)]
    retained: list[list[str]] = []
    usage: list[dict[str, Any] | None] = []
    trajectory = output_root / "statefulness_probe_trajectory.jsonl"
    started = time.time_ns()
    local_options = LocalAgentOptions(cwd=workspace, setting_sources=[])
    with CursorClient.launch_bridge(
        workspace=workspace,
        local=local_options,
        client_timeout=TURN_TIMEOUT_SECONDS,
        max_retries=0,
    ) as client:
        with Agent.create(
            AgentOptions(model=MODEL, mode="agent", tools=[], local=local_options),
            client=client,
        ) as agent:
            session_id = agent.agent_id
            with trajectory.open("x", encoding="utf-8") as raw:
                expected: list[str] = []
                for index, marker in enumerate(markers, start=1):
                    expected.append(marker)
                    instruction = (
                        "State-retention preflight only. Retain every opaque marker from this "
                        f"chat. Add {marker}. Return only JSON "
                        f"{{\"remembered\":{json.dumps(expected)}}}. Do not use tools."
                    )
                    result = agent.send(instruction).wait()
                    raw.write(json.dumps(asdict(result), sort_keys=True, default=str) + "\n")
                    if (
                        result.status != "finished"
                        or result.agent_id != session_id
                        or result.model is None
                        or result.model.id != MODEL
                    ):
                        raise CursorRuntimeError(
                            f"statefulness probe turn {index} invalid: {result}"
                        )
                    answer = json.loads(result.result)
                    if answer.get("remembered") != expected:
                        raise CursorRuntimeError(
                            f"state not retained: expected {expected}, got {answer.get('remembered')}"
                        )
                    retained.append(answer["remembered"])
                    usage.append(
                        result.usage.to_json() if result.usage is not None else None
                    )
    return {
        "status": "PASS", "adapter": ADAPTER_VERSION,
        "binding": {"provider": MODEL_PROVIDER, "model": MODEL, "display": MODEL_DISPLAY_NAME},
        "thread_id": session_id, "provider_session_id": session_id,
        "cursor_sdk_version": CURSOR_SDK_VERSION, "turn_count": 5, "one_thread": True,
        "builtin_tools": [],
        "markers_retained_by_turn": retained, "provider_usage": usage,
        "model_context_window_tokens": None,
        "started_timestamp_ns": started, "completed_timestamp_ns": time.time_ns(),
    }


def _dynamic_tool_probe(output_root: Path) -> dict[str, Any]:
    workspace = output_root / "dynamic_tool_workspace"
    workspace.mkdir(parents=True)
    schemas = json.loads((FROZEN_ROOT / "tool_schemas.json").read_text(encoding="utf-8"))
    telemetry = TelemetryRecorder(
        episode_id="cursor-dynamic-tool-probe", arm="TASKVIEW", replicate=0
    )
    view = copy_frozen_task_view(output_root / "dynamic_tool_taskview.sqlite")
    tools = EpisodeTools(
        source_root=SOURCE_ROOT, scratch_root=output_root / "dynamic_tool_scratch",
        telemetry=telemetry, taskview=ExperimentTaskViewSurface(view),
    )
    tools.scratch_root.mkdir()
    tools.set_phase(1)
    session = CursorSdkParticipantSession(
        "Dynamic-tool transport preflight only.",
        schemas["native"] + schemas["taskview"], "TASKVIEW",
        raw_path=output_root / "dynamic_tool_probe_trajectory.jsonl",
        state_path=output_root / "dynamic_tool_probe_state.jsonl",
        workspace=workspace,
        source_root=SOURCE_ROOT,
        scratch_root=tools.scratch_root,
        taskview_path=view.path,
    )
    try:
        turn = session.turn(
            phase=1,
            prompt=(
                "Call read_source once for tasks/migrate-jsonlib-v3.md lines 1 through 2, "
                "call describe once, and call query_sql once with SELECT service_id FROM "
                "requires_change ORDER BY service_id. Then return direct_change_services as "
                "[], decoding_invariants as [], v3_call_shape as 'probe', and cite the read."
            ),
            answer_fields=[], tools=tools,
        )
    finally:
        session.close()
        view.close()
    names = [
        event["tool_name"] for event in telemetry.events if event["event_type"] == "TOOL_CALL"
    ]
    required = {"read_source", "describe", "query_sql"}
    if set(names) != required or len(names) != 3:
        raise CursorRuntimeError(f"dynamic tool probe mismatch: {names}")
    return {
        "status": "PASS", "session_id": turn.session_id,
        "tool_calls": names, "logical_tool_call_count": len(names),
        "answer": turn.answer,
    }


def run_preflight(output_root: Path, manifest_path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    if output_root.exists():
        raise FileExistsError(f"refusing to replace preflight output: {output_root}")
    output_root.mkdir(parents=True)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    deterministic = _deterministic_checks(manifest)
    if deterministic["status"] != "PASS":
        raise RuntimeError(f"deterministic preflight failed: {deterministic['errors']}")
    state = _statefulness_probe(output_root)
    dynamic = _dynamic_tool_probe(output_root)
    receipt = {
        "status": "PASS", "apparatus_only": True, "participant_campaign_calls": 0,
        "adapter": ADAPTER_VERSION, "runtime_binding": runtime_binding(),
        "manifest_source": str(manifest_path.resolve()),
        "manifest_source_sha256": sha256_file(manifest_path),
        "deterministic_checks": deterministic, "statefulness_probe": state,
        "dynamic_tool_probe": dynamic,
        "probe_trajectory_sha256": sha256_file(
            output_root / "statefulness_probe_trajectory.jsonl"
        ),
        "dynamic_tool_probe_trajectory_sha256": sha256_file(
            output_root / "dynamic_tool_probe_trajectory.jsonl"
        ),
        "adapter_implementation_sha256": sha256_file(PACKAGE_ROOT / "runtime_sdk.py"),
        "tool_server_implementation_sha256": sha256_file(
            PACKAGE_ROOT / "cursor_tool_server.py"
        ),
        "completed_timestamp_ns": time.time_ns(),
    }
    _write_json(output_root / "runtime_preflight.json", receipt)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    print(json.dumps(run_preflight(args.output, args.manifest), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
