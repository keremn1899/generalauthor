from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from mcp.server.fastmcp import Context
from mcp.types import RequestParams

from research.taskview_orientation.freeze import sha256_file
from research.taskview_orientation.runtime_accounting import (
    AccountingInvariantError,
    SdkObservation,
    observations_from_trajectory,
    reconcile_turn,
    timeline_rows,
    trajectory_event_taxonomy,
)
from research.taskview_orientation.runtime_sdk import CursorSdkParticipantSession
from research.taskview_orientation.telemetry import TelemetryRecorder
from research.taskview_orientation.v01_authorize import AUTHORIZED_MANIFEST_PATH
from research.taskview_orientation.v01_harness_manifest import (
    HARNESS_AUTHORIZED_MANIFEST_PATH,
    HARNESS_MANIFEST_PATH,
    HARNESS_SIDECAR_PATH,
    build_manifest,
)


ALLOWED = {
    "search_source",
    "read_source",
    "write_scratch",
    "describe",
    "query_sql",
    "assertion",
    "rerun",
}
SESSION = "agent-test"


def _message(
    call_id: str,
    tool: str,
    arguments: dict,
    status: str,
    *,
    text: str = '{"ok":true}',
    is_error: bool = False,
    run_id: str = "run-1",
) -> dict:
    return {
        "type": "tool_call",
        "agent_id": SESSION,
        "run_id": run_id,
        "call_id": call_id,
        "name": "mcp",
        "args": {
            "providerIdentifier": "taskview-orientation",
            "toolName": tool,
            "args": arguments,
        },
        "status": status,
        "result": (
            {
                "status": "success",
                "value": {
                    "content": [{"text": {"text": text}}],
                    "isError": is_error,
                },
            }
            if status != "running"
            else None
        ),
    }


def _observations(
    call_id: str,
    tool: str,
    arguments: dict,
    *,
    text: str = '{"ok":true}',
    is_error: bool = False,
    phase: int = 1,
    run_id: str = "run-1",
) -> list[SdkObservation]:
    return [
        SdkObservation(
            phase, f"{run_id}:{call_id}:start", 10,
            _message(call_id, tool, arguments, "running", run_id=run_id),
        ),
        SdkObservation(
            phase, f"{run_id}:{call_id}:complete", 30,
            _message(
                call_id, tool, arguments, "completed",
                text=text, is_error=is_error, run_id=run_id,
            ),
        ),
    ]


def _bridge(
    execution_id: str,
    tool: str,
    arguments: dict,
    *,
    outcome: str = "success",
    phase: int = 1,
    provider_call_id: str | None = None,
    bridge_session_id: str | None = None,
) -> list[dict]:
    common = {
        "bridge_execution_id": execution_id,
        "bridge_request_id": execution_id.replace("execution", "request"),
        "tool_name": tool,
        "tool_arguments": arguments,
    }
    if provider_call_id is not None:
        common["provider_call_id"] = provider_call_id
    if bridge_session_id is not None:
        common["bridge_session_id"] = bridge_session_id
    records = [
        {"timestamp_ns": 20, "phase": phase, "event_type": "BRIDGE_REQUEST", "payload": common},
    ]
    if outcome == "success":
        terminal = {
            "search_source": "SOURCE_SEARCH",
            "read_source": "SOURCE_READ",
            "write_scratch": "SCRATCH_WRITE",
        }.get(tool, "TASKVIEW_TOOL")
        records.append(
            {"timestamp_ns": 25, "phase": phase, "event_type": terminal, "payload": common}
        )
    records.append(
        {
            "timestamp_ns": 28,
            "phase": phase,
            "event_type": "BRIDGE_RESPONSE",
            "payload": {**common, "outcome": outcome},
        }
    )
    return records


def _reconcile(observations: list[SdkObservation], bridge: list[dict]):
    return reconcile_turn(
        observations,
        bridge,
        expected_session_id=SESSION,
        allowed_tool_names=ALLOWED,
    )


def test_normal_single_native_call_uses_provider_identity_and_exact_payload_bytes():
    text = '{\n  "path": "x"\n}'
    report = _reconcile(
        _observations("call-1", "read_source", {"path": "x"}, text=text),
        _bridge(
            "execution-1",
            "read_source",
            {"path": "x", "start_line": 1, "end_line": 10_000},
        ),
    )
    assert report.logical_call_count == 1
    assert len(report.bridge_executions) == 1
    assert report.logical_calls[0].identity == (SESSION, "call-1")
    assert report.model_visible_tool_result_bytes == len(text.encode("utf-8"))
    assert report.per_operation_response_bytes == {"read_source": len(text.encode("utf-8"))}


def test_multiple_sequential_and_identical_repeated_calls_remain_distinct():
    observations = []
    bridge = []
    for index in range(3):
        observations.extend(_observations(f"call-{index}", "describe", {}))
        bridge.extend(_bridge(f"execution-{index}", "describe", {"relation": None, "why": None}))
    report = _reconcile(observations, bridge)
    assert report.logical_call_count == 3
    assert len({call.identity for call in report.logical_calls}) == 3
    assert len(report.call_to_execution) == 3


def test_propagated_provider_id_disambiguates_reversed_identical_executions():
    observations = _observations("call-0", "describe", {})
    observations += _observations("call-1", "describe", {})
    bridge = _bridge(
        "execution-0", "describe", {"relation": None, "why": None},
        provider_call_id="call-1",
    )
    bridge += _bridge(
        "execution-1", "describe", {"relation": None, "why": None},
        provider_call_id="call-0",
    )
    report = _reconcile(observations, bridge)
    assert report.call_to_execution[(SESSION, "call-0")] == "execution-1"
    assert report.call_to_execution[(SESSION, "call-1")] == "execution-0"


def test_stream_fragments_and_same_event_replays_do_not_create_calls():
    observations = _observations("call-1", "query_sql", {"sql": "SELECT 1"})
    observations += [observations[0], observations[1]]
    report = _reconcile(
        observations,
        _bridge(
            "execution-1",
            "query_sql",
            {"sql": "SELECT 1", "parameters": []},
        ),
    )
    assert report.sdk_tool_observations == 4
    assert report.replay_observations == 2
    assert report.logical_call_count == 1

    records = [
        {"event": {"sdk_message": {"type": "thinking"}}},
        {"event": {"sdk_message": {"type": "assistant"}}},
        {"event": {"sdk_message": observations[0].message}},
        {"event": {"sdk_message": observations[1].message}},
    ]
    assert trajectory_event_taxonomy(records) == {
        "MODEL_TOOL_INTENT": None,
        "SDK_TOOL_CALL_START": 1,
        "SDK_TOOL_CALL_COMPLETE": 1,
        "STREAM_FRAGMENT": 2,
    }


def test_executed_tool_error_is_not_a_provider_validation_rejection():
    text = "Error executing tool query_sql: no such table: missing"
    report = _reconcile(
        _observations(
            "call-error", "query_sql", {"sql": "SELECT * FROM missing"},
            text=text, is_error=True,
        ),
        _bridge(
            "execution-error",
            "query_sql",
            {"sql": "SELECT * FROM missing", "parameters": []},
            outcome="error",
        ),
    )
    assert report.provider_errors == 1
    assert report.provider_validation_rejections == 0
    assert len(report.bridge_executions) == 1


def test_pre_handler_validation_error_is_a_logical_attempt_without_execution():
    text = (
        "Error executing tool read_source: 1 validation error for read_sourceArguments\n"
        "path\n  Field required [type=missing]\nhttps://errors.pydantic.dev/2.13/v/missing"
    )
    report = _reconcile(
        _observations(
            "call-invalid", "read_source", {"query": "x"}, text=text, is_error=True
        ),
        [],
    )
    assert report.logical_call_count == 1
    assert report.provider_validation_rejections == 1
    assert len(report.bridge_executions) == 0


def test_native_and_taskview_bytes_reconcile_by_operation():
    observations = _observations("call-native", "search_source", {"query": "x"}, text="abc")
    observations += _observations("call-taskview", "describe", {}, text="12345")
    bridge = _bridge(
        "execution-native", "search_source", {"query": "x", "scope": "."}
    )
    bridge += _bridge(
        "execution-taskview", "describe", {"relation": None, "why": None}
    )
    report = _reconcile(observations, bridge)
    assert report.per_operation_response_bytes == {"describe": 5, "search_source": 3}
    assert report.model_visible_tool_result_bytes == 8


def test_adapter_records_one_logical_call_and_one_exact_visible_result():
    text = '{\n  "rows": []\n}'
    observations = _observations(
        "call-taskview", "query_sql", {"sql": "SELECT 1"}, text=text
    )
    bridge = _bridge(
        "execution-taskview",
        "query_sql",
        {"sql": "SELECT 1", "parameters": []},
    )
    bridge[1]["payload"]["model_visible_output_bytes"] = 1
    report = _reconcile(observations, bridge)
    recorder = TelemetryRecorder(episode_id="test", arm="TASKVIEW", replicate=0)
    CursorSdkParticipantSession._record_reconciled_telemetry(
        SimpleNamespace(telemetry=recorder), bridge, report, phase=1
    )
    assert sum(event["event_type"] == "LOGICAL_TOOL_CALL" for event in recorder.events) == 1
    assert sum(
        event["event_type"] == "TOOL_RESULT_DELIVERED_TO_MODEL"
        for event in recorder.events
    ) == 1
    terminal = next(event for event in recorder.events if event["event_type"] == "TASKVIEW_TOOL")
    assert terminal["bridge_serialized_payload_bytes"] == 1
    assert terminal["model_visible_output_bytes"] == len(text.encode("utf-8"))
    reconciliation = recorder.events[-1]
    assert reconciliation["event_type"] == "ACCOUNTING_RECONCILIATION"
    assert reconciliation["unique_logical_calls"] == 1
    assert reconciliation["bridge_executions"] == 1


def test_bridge_instrumentation_emits_one_request_execution_and_response(
    tmp_path, monkeypatch
):
    from research.taskview_orientation import cursor_tool_server

    source = tmp_path / "source"
    scratch = tmp_path / "scratch"
    source.mkdir()
    scratch.mkdir()
    (source / "x.txt").write_text("needle\n", encoding="utf-8")
    phase = tmp_path / "phase.json"
    phase.write_text('{"phase": 1, "source_version": "initial"}\n', encoding="utf-8")
    bridge_path = tmp_path / "bridge.jsonl"
    monkeypatch.setenv("TASKVIEW_ARM", "RAW")
    monkeypatch.setenv("TASKVIEW_SOURCE_ROOT", str(source))
    monkeypatch.setenv("TASKVIEW_SCRATCH_ROOT", str(scratch))
    monkeypatch.setenv("TASKVIEW_DB_PATH", "RAW_ARM_NO_TASKVIEW")
    monkeypatch.setenv("TASKVIEW_PHASE_STATE", str(phase))
    monkeypatch.setenv("TASKVIEW_BRIDGE_TELEMETRY", str(bridge_path))
    monkeypatch.setenv("TASKVIEW_BRIDGE_SESSION_ID", "bridge-test")
    meta = RequestParams.Meta.model_validate({"toolCallId": "call-bridge"})
    ctx = Context(request_context=SimpleNamespace(request_id="request-7", meta=meta))

    result = cursor_tool_server.search_source("needle", ".", ctx)
    assert result["result_count"] == 1
    records = _jsonl(bridge_path)
    assert [record["event_type"] for record in records] == [
        "BRIDGE_REQUEST",
        "TOOL_CALL",
        "SOURCE_SEARCH",
        "BRIDGE_RESPONSE",
    ]
    identities = {record["payload"]["bridge_execution_id"] for record in records}
    assert len(identities) == 1
    assert all(record["payload"]["provider_call_id"] == "call-bridge" for record in records)
    assert records[-1]["payload"]["outcome"] == "success"


@pytest.mark.parametrize(
    "mutator,match",
    [
        (lambda obs, bridge: bridge.extend(_bridge("execution-extra", "describe", {})), "unattributable"),
        (lambda obs, bridge: bridge.pop(), "missing bridge response"),
        (lambda obs, bridge: bridge.clear(), "missing executions"),
        (
            lambda obs, bridge: obs.append(
                SdkObservation(1, "different-complete-event", 31, obs[1].message)
            ),
            "2 completions",
        ),
    ],
)
def test_real_accounting_failures_abort(mutator, match):
    observations = _observations("call-1", "describe", {})
    bridge = _bridge("execution-1", "describe", {"relation": None, "why": None})
    mutator(observations, bridge)
    with pytest.raises(AccountingInvariantError, match=match):
        _reconcile(observations, bridge)


def test_duplicate_bridge_execution_and_cross_session_contamination_abort():
    observations = _observations("call-1", "describe", {})
    bridge = _bridge("execution-1", "describe", {"relation": None, "why": None})
    bridge += _bridge("execution-1", "describe", {"relation": None, "why": None})
    with pytest.raises(AccountingInvariantError, match="duplicate"):
        _reconcile(observations, bridge)

    contaminated = list(observations)
    contaminated[0] = SdkObservation(
        1, contaminated[0].sdk_event_id, 10,
        {**contaminated[0].message, "agent_id": "agent-other"},
    )
    with pytest.raises(AccountingInvariantError, match="cross-session"):
        _reconcile(contaminated, _bridge("execution-1", "describe", {}))

    with pytest.raises(AccountingInvariantError, match="cross-session bridge"):
        reconcile_turn(
            observations,
            _bridge(
                "execution-1", "describe", {}, bridge_session_id="bridge-other"
            ),
            expected_session_id=SESSION,
            allowed_tool_names=ALLOWED,
            expected_bridge_session_id="bridge-expected",
        )


def test_provider_retry_that_changes_run_identity_aborts():
    observations = _observations("call-1", "describe", {})
    observations[1] = SdkObservation(
        1,
        "run-2:call-1:complete",
        30,
        _message("call-1", "describe", {}, "completed", run_id="run-2"),
    )
    with pytest.raises(AccountingInvariantError, match="provider retry"):
        _reconcile(observations, _bridge("execution-1", "describe", {}))


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


@pytest.mark.requires_path(
    "research/taskview_orientation/results/stage1-cursor-v01/"
    "taskview-orientation-v01-e01-taskview-r2/provider_trajectory.jsonl"
)
def test_preserved_365_608_failure_reconciles_exactly():
    root = Path(
        "research/taskview_orientation/results/stage1-cursor-v01/"
        "taskview-orientation-v01-e01-taskview-r2"
    )
    trajectory = _jsonl(root / "provider_trajectory.jsonl")
    bridge = _jsonl(root / "provider_workspace/logical_tool_telemetry.jsonl")
    observations = observations_from_trajectory(trajectory)
    session = observations[0].message["agent_id"]
    report = reconcile_turn(
        observations,
        bridge,
        expected_session_id=session,
        allowed_tool_names=ALLOWED,
    )
    assert trajectory_event_taxonomy(trajectory)["SDK_TOOL_CALL_START"] == 365
    assert trajectory_event_taxonomy(trajectory)["SDK_TOOL_CALL_COMPLETE"] == 365
    assert report.sdk_tool_observations == 730
    assert report.logical_call_count == 365
    assert len(report.bridge_executions) == 365
    assert report.provider_errors == 243
    assert report.provider_validation_rejections == 0
    assert report.model_visible_tool_result_bytes == 42_790
    assert report.per_operation_response_bytes == {
        "assertion": 74,
        "describe": 5_858,
        "query_sql": 3_373,
        "read_source": 20_669,
        "rerun": 177,
        "search_source": 12_639,
    }
    assert 365 + report.provider_errors == 608
    rows = timeline_rows(report)
    assert len(rows) == 365
    assert all(row["provider_call_id"] and row["bridge_execution_id"] for row in rows)


@pytest.mark.requires_path(
    "research/taskview_orientation/results/stage1-cursor-v10/campaign_seal.json"
)
def test_sealed_v10_discrepancies_are_executed_errors_not_boundary_calls():
    root = Path("research/taskview_orientation/results/stage1-cursor-v10")
    discrepancy_by_episode_phase: dict[tuple[str, int], int] = {}
    for telemetry_path in root.glob("*/telemetry.jsonl"):
        episode = telemetry_path.parent.name
        for event in _jsonl(telemetry_path):
            if event["event_type"] == "ACCOUNTING_DISCREPANCY":
                discrepancy_by_episode_phase[(episode, event["phase"])] = event["overage"]

    observed: dict[tuple[str, int], int] = {}
    for trajectory_path in root.glob("*/provider_trajectory.jsonl"):
        episode_root = trajectory_path.parent
        trajectory = _jsonl(trajectory_path)
        observations = observations_from_trajectory(trajectory)
        session = observations[0].message["agent_id"]
        report = reconcile_turn(
            observations,
            _jsonl(episode_root / "provider_workspace/logical_tool_telemetry.jsonl"),
            expected_session_id=session,
            allowed_tool_names=ALLOWED,
        )
        for call in report.logical_calls:
            if call.is_error and not call.provider_validation_rejected:
                key = (episode_root.name, call.phase)
                observed[key] = observed.get(key, 0) + 1

    assert discrepancy_by_episode_phase == observed
    assert len(observed) == 11
    assert sum(observed.values()) == 19


@pytest.mark.requires_path(
    "research/taskview_orientation/results/stage1-cursor-v01/campaign_invalid.json"
)
def test_harness_v4_manifest_changes_only_runtime_identity_and_is_unauthorized():
    manifest = json.loads(HARNESS_MANIFEST_PATH.read_text(encoding="utf-8"))
    parent = json.loads(AUTHORIZED_MANIFEST_PATH.read_text(encoding="utf-8"))
    assert manifest == build_manifest()
    assert sha256_file(HARNESS_MANIFEST_PATH) == (
        HARNESS_SIDECAR_PATH.read_text(encoding="utf-8").split()[0]
    )
    assert manifest["runtime_binding"]["adapter"] == "taskview-cursor-sdk-v4"
    assert manifest["accounting"]["model"] == "cursor-mcp-identity-v1"
    assert manifest["participant_execution_authorized"] is False
    assert manifest["fresh_authorization_required"] is True
    assert not HARNESS_AUTHORIZED_MANIFEST_PATH.exists()
    assert manifest["semantic_changes"] == []
    for field in (
        "scientific_world",
        "all_frozen_input_hashes",
        "source_snapshot",
        "phase4_replacement_sha256",
        "prompt_hashes",
        "oracle",
        "span_classification",
        "taskview",
        "stage1",
        "arm_policy",
        "prospective_criteria",
    ):
        assert manifest[field] == parent[field]


@pytest.mark.requires_path(
    "research/taskview_orientation/results/stage1-cursor-v01/"
    "taskview-orientation-v01-e01-taskview-r2/provider_trajectory.jsonl",
    "research/taskview_orientation/results/stage1-cursor-v10/campaign_seal.json",
)
def test_v10_exact_byte_counterfactual_does_not_change_sealed_decision():
    from research.taskview_orientation.accounting_diagnosis import build_report

    counterfactual = build_report()["sealed_v10_retrospective"][
        "exact_delivered_byte_counterfactual"
    ]
    assert counterfactual["historical_files_rewritten"] is False
    assert counterfactual["median_paired_O_post_reduction"] == pytest.approx(
        0.2658546924085131
    )
    assert counterfactual["taskview_lower_O_post_pairs"] == 3
    assert counterfactual["net_orientation_deltas"] == [17646, 21934, -1410, 16409]
    assert counterfactual["primary_threshold_still_passes"] is False
    assert counterfactual["sealed_decision_remains"] == "INCONCLUSIVE"
