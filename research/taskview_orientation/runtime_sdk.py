"""Cursor SDK adapter exposing only the frozen TaskView MCP tool surface."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import sys
import time
import uuid
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Mapping

from cursor_sdk import (
    Agent,
    AgentOptions,
    CursorClient,
    LocalAgentOptions,
    StdioMcpServerConfig,
)

from research.taskview_orientation.fixture import semantic_rows
from research.taskview_orientation.runner import ParticipantTurn
from research.taskview_orientation.runtime_accounting import (
    ACCOUNTING_MODEL_VERSION,
    SUCCESS_TERMINAL_EVENTS,
    TASKVIEW_OPERATIONS,
    AccountingInvariantError,
    AccountingReport,
    SdkObservation,
    reconcile_turn,
)
from research.taskview_orientation.runtime import (
    MAX_STRUCTURED_ANSWER_TOKENS,
    MCP_SERVER_NAME,
    MODEL,
    MODEL_CONTEXT_WINDOW,
    MODEL_DISPLAY_NAME,
    MODEL_PROVIDER,
    PROVIDER_TOOL_SCHEMAS,
    REASONING_EFFORT,
    SERVICE_TIER,
    TURN_TIMEOUT_SECONDS,
    CursorRuntimeError,
    _strip_json_fence,
    answer_schema,
    provider_tools,
    sha256_json,
)
from research.taskview_orientation.telemetry import visible_bytes
from research.taskview_orientation.tools import EpisodeTools


ADAPTER_VERSION = "taskview-cursor-sdk-v4"
CURSOR_SDK_VERSION = importlib.metadata.version("cursor-sdk")
BUILTIN_TOOL_ALLOWLIST: tuple[str, ...] = ("mcp",)


def runtime_binding() -> dict[str, Any]:
    schemas = json.loads(
        (Path(__file__).parent / "frozen" / "tool_schemas.json").read_text(encoding="utf-8")
    )
    native = provider_tools(schemas["native"])
    treatment = provider_tools(schemas["native"] + schemas["taskview"])
    return {
        "provider": MODEL_PROVIDER,
        "model": MODEL,
        "model_display_name": MODEL_DISPLAY_NAME,
        "exact_model_version_identifier": MODEL,
        "adapter": ADAPTER_VERSION,
        "accounting_model": ACCOUNTING_MODEL_VERSION,
        "cursor_sdk_version": CURSOR_SDK_VERSION,
        "service_tier": SERVICE_TIER,
        "reasoning_effort": REASONING_EFFORT,
        "sampling": {
            "seed": "not supported by Cursor SDK",
            "temperature": "not exposed by Cursor SDK",
            "top_p": "not exposed by Cursor SDK",
        },
        "immutable_backend_revision_exposed": False,
        "context_limit_tokens": MODEL_CONTEXT_WINDOW,
        "context_limit_source": "not exposed by Cursor SDK",
        "context_policy": "one Cursor SDK Agent and five sequential runs; no summaries or retries",
        "timeout_policy": (
            f"{TURN_TIMEOUT_SECONDS} seconds requested per turn; no retry or restart after timeout"
        ),
        "budgets": {
            "structured_answer_max_tokens": MAX_STRUCTURED_ANSWER_TOKENS,
            "turn_timeout_seconds": TURN_TIMEOUT_SECONDS,
            "hard_provider_output_budget": (
                "not exposed; exact JSON contract and harness byte ceiling applied"
            ),
            "hard_provider_reasoning_budget": "not exposed",
        },
        "builtin_tool_allowlist": list(BUILTIN_TOOL_ALLOWLIST),
        "tool_policy": (
            "Cursor SDK built-ins are restricted to the MCP capability; only the inline "
            "taskview-orientation server is loaded"
        ),
        "provider_tool_serialization_sha256": {
            "RAW": sha256_json(native),
            "TASKVIEW": sha256_json(treatment),
            "schema_map": sha256_json(PROVIDER_TOOL_SCHEMAS),
        },
    }


def _jsonable(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _jsonable(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def _tool_name(name: str, allowed: set[str]) -> str | None:
    if name in allowed:
        return name
    for candidate in allowed:
        if name.endswith(f"-{candidate}") or name.endswith(f"_{candidate}"):
            return candidate
    return None


def _mcp_call_name_and_arguments(message: Any) -> tuple[str, Any]:
    """Resolve the concrete tool name and arguments for an SDK tool_call message.

    Per the Cursor SDK's documented McpToolCallSchema, every allowed MCP call
    is reported under the generic ``name`` "mcp"; the concrete server/tool
    identifier and the tool's own arguments are nested at ``args["toolName"]``
    and ``args["args"]``. A non-MCP (built-in) tool call keeps its own name
    and arguments unchanged, so it still fails the allowlist check below.
    """
    name = str(getattr(message, "name", ""))
    args = getattr(message, "args", None)
    if name == "mcp" and isinstance(args, Mapping):
        tool_name = args.get("toolName")
        if tool_name:
            return str(tool_name), args.get("args")
    return name, args


def _mcp_call_failed(message: Any) -> bool:
    """True if this tool call never reached (or errored inside) our tool logic.

    A provider-side rejection (e.g. a disallowed tool) surfaces as SDK status
    "error". A malformed call to an allowed MCP tool instead surfaces as a
    "completed" SDK status carrying a successful MCP envelope whose payload
    sets ``isError``: FastMCP rejects bad arguments (e.g. a missing required
    field) before our tool function's own body — and its telemetry logging —
    ever runs, so the bridge never records it. Both cases need a synthesized
    telemetry record here instead.
    """
    if getattr(message, "status", "") == "error":
        return True
    result = getattr(message, "result", None)
    if isinstance(result, Mapping) and result.get("status") == "success":
        value = result.get("value")
        if isinstance(value, Mapping) and value.get("isError"):
            return True
    return False


class CursorSdkParticipantSession:
    """One SDK Agent retained for all five episode turns."""

    def __init__(
        self,
        system_prompt: str,
        frozen_schemas: list[dict[str, Any]],
        arm: str,
        *,
        raw_path: Path,
        state_path: Path,
        workspace: Path,
        source_root: Path,
        scratch_root: Path,
        taskview_path: Path | None,
    ) -> None:
        if not os.environ.get("CURSOR_API_KEY"):
            raise CursorRuntimeError("CURSOR_API_KEY is required by the Cursor SDK adapter")
        self.arm = arm
        self.system_prompt = system_prompt
        self.visible_tools = provider_tools(frozen_schemas)
        self.allowed_tool_names = {record["name"] for record in frozen_schemas}
        self.workspace = workspace.resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.raw_path = raw_path
        self.raw_path.parent.mkdir(parents=True, exist_ok=True)
        self._raw = self.raw_path.open("x", encoding="utf-8")
        self._state_path = state_path
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        self._state_file = self._state_path.open("x", encoding="utf-8")
        self._phase_state_path = self.workspace / "phase_state.json"
        self._bridge_telemetry_path = self.workspace / "logical_tool_telemetry.jsonl"
        self._bridge_session_id = f"bridge-{uuid.uuid4()}"
        self._bridge_offset = 0
        self._first_turn = True

        repository_root = Path(__file__).resolve().parents[2]
        python_path = os.environ.get("PYTHONPATH", "")
        server_env = {
            "PYTHONPATH": str(repository_root) + (os.pathsep + python_path if python_path else ""),
            "TASKVIEW_ARM": arm,
            "TASKVIEW_SOURCE_ROOT": str(source_root.resolve()),
            "TASKVIEW_SCRATCH_ROOT": str(scratch_root.resolve()),
            "TASKVIEW_DB_PATH": (
                str(taskview_path.resolve()) if taskview_path is not None else "RAW_ARM_NO_TASKVIEW"
            ),
            "TASKVIEW_PHASE_STATE": str(self._phase_state_path),
            "TASKVIEW_BRIDGE_TELEMETRY": str(self._bridge_telemetry_path),
            "TASKVIEW_BRIDGE_SESSION_ID": self._bridge_session_id,
        }
        mcp_servers = {
            MCP_SERVER_NAME: StdioMcpServerConfig(
                command=sys.executable,
                args=["-m", "research.taskview_orientation.cursor_tool_server"],
                env=server_env,
                cwd=str(repository_root),
            )
        }
        local_options = LocalAgentOptions(cwd=self.workspace, setting_sources=[])
        self._client = CursorClient.launch_bridge(
            workspace=self.workspace,
            local=local_options,
            client_timeout=TURN_TIMEOUT_SECONDS,
            max_retries=0,
        )
        self._agent = Agent.create(
            AgentOptions(
                model=MODEL,
                mode="agent",
                tools=BUILTIN_TOOL_ALLOWLIST,
                local=local_options,
                mcp_servers=mcp_servers,
            ),
            client=self._client,
        )
        self.session_id = self._agent.agent_id
        self.provider_session_id = self.session_id
        self.sdk_version = CURSOR_SDK_VERSION

    def _participant_prompt(self, phase: int, prompt: str) -> str:
        contract = (
            "Use only tools from the taskview-orientation MCP server. Return only one JSON "
            "object, without Markdown fences, conforming exactly to this schema: "
            + json.dumps(answer_schema(phase), sort_keys=True)
        )
        if self._first_turn:
            return self.system_prompt + "\n\n" + contract + "\n\n" + prompt
        return contract + "\n\n" + prompt

    def _fresh_bridge_telemetry(self) -> list[dict[str, Any]]:
        if not self._bridge_telemetry_path.exists():
            return []
        lines = self._bridge_telemetry_path.read_text(encoding="utf-8").splitlines()
        fresh = lines[self._bridge_offset :]
        self._bridge_offset = len(lines)
        return [json.loads(line) for line in fresh]

    @staticmethod
    def _record_reconciled_telemetry(
        tools: EpisodeTools,
        bridge_records: list[dict[str, Any]],
        accounting: AccountingReport,
        *,
        phase: int,
    ) -> None:
        calls = {call.identity: call for call in accounting.logical_calls}
        terminal_counts: dict[tuple[str, str], int] = {identity: 0 for identity in calls}

        for call in accounting.logical_calls:
            tools.telemetry.record(
                "LOGICAL_TOOL_CALL",
                phase=call.phase,
                provider_session_id=call.provider_session_id,
                provider_call_id=call.provider_call_id,
                provider_run_id=call.run_id,
                tool_name=call.tool_name,
                tool_arguments=call.tool_arguments,
                taskview_operation=(
                    call.tool_name if call.tool_name in TASKVIEW_OPERATIONS else None
                ),
                provider_validation_rejected=call.provider_validation_rejected,
            )

        for record in bridge_records:
            payload = dict(record["payload"])
            execution_id = payload.get("bridge_execution_id")
            identity = accounting.execution_to_call.get(str(execution_id))
            call = calls.get(identity) if identity is not None else None
            if call is not None:
                payload.update(
                    {
                        "provider_session_id": call.provider_session_id,
                        "provider_call_id": call.provider_call_id,
                        "provider_run_id": call.run_id,
                    }
                )
            if record["event_type"] in SUCCESS_TERMINAL_EVENTS:
                if call is None:
                    raise AccountingInvariantError(
                        f"successful terminal telemetry is unattributable: {record['event_type']}"
                    )
                terminal_counts[call.identity] += 1
                measured = payload.pop("model_visible_output_bytes", None)
                if measured is not None:
                    payload["bridge_serialized_payload_bytes"] = measured
                payload["model_visible_output_bytes"] = call.model_visible_output_bytes
            tools.telemetry.record(
                record["event_type"], phase=int(record["phase"]), **payload
            )

        for call in accounting.logical_calls:
            execution_id = accounting.call_to_execution.get(call.identity)
            if call.provider_validation_rejected:
                if execution_id is not None:
                    raise AccountingInvariantError(
                        f"validation-rejected call executed: {call.identity}"
                    )
            elif execution_id is None:
                raise AccountingInvariantError(f"accepted call was not executed: {call.identity}")

            expected_terminals = 0 if call.is_error else 1
            if terminal_counts[call.identity] != expected_terminals:
                raise AccountingInvariantError(
                    f"call {call.identity} has {terminal_counts[call.identity]} successful "
                    f"terminal events, expected {expected_terminals}"
                )
            if call.is_error:
                tools.telemetry.record(
                    "TOOL_ERROR",
                    phase=call.phase,
                    provider_session_id=call.provider_session_id,
                    provider_call_id=call.provider_call_id,
                    provider_run_id=call.run_id,
                    bridge_execution_id=execution_id,
                    tool_name=call.tool_name,
                    tool_arguments=call.tool_arguments,
                    taskview_operation=(
                        call.tool_name if call.tool_name in TASKVIEW_OPERATIONS else None
                    ),
                    provider_validation_rejected=call.provider_validation_rejected,
                    model_visible_output_bytes=call.model_visible_output_bytes,
                )
            tools.telemetry.record(
                "TOOL_RESULT_DELIVERED_TO_MODEL",
                phase=call.phase,
                provider_session_id=call.provider_session_id,
                provider_call_id=call.provider_call_id,
                provider_run_id=call.run_id,
                bridge_execution_id=execution_id,
                tool_name=call.tool_name,
                tool_arguments=call.tool_arguments,
                outcome="error" if call.is_error else "success",
                delivered_payload_bytes=call.model_visible_output_bytes,
            )

        delivered = sum(call.model_visible_output_bytes for call in accounting.logical_calls)
        canonical = sum(
            int(event.get("model_visible_output_bytes", 0))
            for event in tools.telemetry.events
            if event["phase"] == phase
            and event["event_type"] in SUCCESS_TERMINAL_EVENTS | {"TOOL_ERROR"}
        )
        if canonical != delivered:
            raise AccountingInvariantError(
                f"model-visible tool bytes do not reconcile: canonical={canonical}, delivered={delivered}"
            )
        tools.telemetry.record(
            "ACCOUNTING_RECONCILIATION",
            phase=phase,
            accounting_model=ACCOUNTING_MODEL_VERSION,
            sdk_tool_lifecycle_observations=accounting.sdk_tool_observations,
            sdk_replay_observations=accounting.replay_observations,
            unique_logical_calls=accounting.logical_call_count,
            bridge_executions=len(accounting.bridge_executions),
            provider_validation_rejections=accounting.provider_validation_rejections,
            model_visible_tool_results=accounting.logical_call_count,
            model_visible_tool_result_bytes=accounting.model_visible_tool_result_bytes,
            per_operation_response_bytes=accounting.per_operation_response_bytes,
        )

    def _record_state(self, boundary: str, phase: int, tools: EpisodeTools) -> None:
        if tools.taskview is None:
            state: dict[str, Any] | None = None
        else:
            view = tools.taskview.view
            semantic = semantic_rows(view)
            state = {
                "view_revision": view.revision,
                "description": view.describe(),
                "semantic_rows": semantic,
                "semantic_sha256": sha256_json(semantic),
            }
        self._state_file.write(
            json.dumps(
                {
                    "timestamp_ns": time.time_ns(),
                    "phase": phase,
                    "boundary": boundary,
                    "arm": self.arm,
                    "taskview_state": state,
                },
                sort_keys=True,
            )
            + "\n"
        )
        self._state_file.flush()

    def turn(
        self, *, phase: int, prompt: str, answer_fields: list[str], tools: EpisodeTools
    ) -> ParticipantTurn:
        del answer_fields
        if phase == 4:
            self._record_state("immediately_after_phase4_source_mutation", phase, tools)
        self._phase_state_path.write_text(
            json.dumps({"phase": phase, "source_version": tools.source_version}) + "\n",
            encoding="utf-8",
        )
        run = self._agent.send(self._participant_prompt(phase, prompt))
        sdk_observations: list[SdkObservation] = []
        for event in run.events():
            self._raw.write(
                json.dumps(
                    {"phase": phase, "timestamp_ns": time.time_ns(), "event": _jsonable(event)},
                    sort_keys=True,
                )
                + "\n"
            )
            if event.sdk_message is not None and event.sdk_message.type == "tool_call":
                run_id = str(event.sdk_message.run_id)
                offset = str(event.offset)
                sdk_observations.append(
                    SdkObservation(
                        phase=phase,
                        sdk_event_id=f"{run_id}:{offset}",
                        timestamp_ns=time.time_ns(),
                        message=event.sdk_message,
                    )
                )
        result = run.wait()
        self._raw.write(
            json.dumps(
                {"phase": phase, "timestamp_ns": time.time_ns(), "result": _jsonable(result)},
                sort_keys=True,
            )
            + "\n"
        )
        self._raw.flush()
        if result.status != "finished":
            raise CursorRuntimeError(f"Cursor SDK participant failed in phase {phase}: {result}")
        if result.agent_id != self.session_id:
            raise CursorRuntimeError("Cursor SDK agent changed within the episode")
        if result.model is None or result.model.id != MODEL:
            raise CursorRuntimeError(f"Cursor SDK model binding mismatch: {result.model}")

        bridge_records = self._fresh_bridge_telemetry()
        try:
            accounting = reconcile_turn(
                sdk_observations,
                bridge_records,
                expected_session_id=self.session_id,
                allowed_tool_names=self.allowed_tool_names,
                expected_bridge_session_id=self._bridge_session_id,
            )
            self._record_reconciled_telemetry(
                tools, bridge_records, accounting, phase=phase
            )
        except AccountingInvariantError as exc:
            raise CursorRuntimeError(f"tool accounting invariant failed: {exc}") from exc

        final_text = result.result
        try:
            answer = json.loads(_strip_json_fence(final_text))
        except json.JSONDecodeError as exc:
            raise CursorRuntimeError(f"final answer is not JSON: {final_text!r}") from exc
        if visible_bytes(answer) > MAX_STRUCTURED_ANSWER_TOKENS * 4:
            raise CursorRuntimeError("structured answer exceeded the frozen approximate token budget")
        if phase == 3:
            self._record_state("immediately_before_phase4_source_mutation", phase, tools)
        self._first_turn = False
        usage = result.usage
        return ParticipantTurn(
            answer=answer,
            session_id=self.session_id,
            provider_input_tokens=usage.input_tokens if usage is not None else None,
            provider_output_tokens=usage.output_tokens if usage is not None else None,
        )

    def close(self) -> None:
        try:
            self._agent.close()
        finally:
            try:
                self._client.close()
            finally:
                self._state_file.close()
                self._raw.close()


class CursorSdkSessionFactory:
    def __init__(self, output_root: Path) -> None:
        self.output_root = output_root
        self.session: CursorSdkParticipantSession | None = None

    def __call__(
        self, system: str, schemas: list[dict[str, Any]], arm: str
    ) -> CursorSdkParticipantSession:
        if self.session is not None:
            raise RuntimeError("episode factory may create exactly one participant session")
        self.session = CursorSdkParticipantSession(
            system,
            schemas,
            arm,
            raw_path=self.output_root / "provider_trajectory.jsonl",
            state_path=self.output_root / "runtime_state.jsonl",
            workspace=self.output_root / "provider_workspace",
            source_root=self.output_root / "source",
            scratch_root=self.output_root / "scratch",
            taskview_path=(self.output_root / "taskview.sqlite") if arm == "TASKVIEW" else None,
        )
        return self.session

    def close(self) -> None:
        if self.session is not None:
            self.session.close()


DefaultSessionFactory = CursorSdkSessionFactory
