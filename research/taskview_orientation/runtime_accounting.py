"""Identity-based Cursor SDK/MCP accounting for TaskView participant runs.

The Cursor SDK emits lifecycle observations.  The MCP server emits execution
telemetry.  Neither raw event count is a logical-call count.  This module keeps
the provider call identity authoritative and reconciles it one-to-one with
bridge executions without collapsing legitimate repeated calls.
"""

from __future__ import annotations

import json
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Iterable, Mapping


ACCOUNTING_MODEL_VERSION = "cursor-mcp-identity-v1"
TASKVIEW_OPERATIONS = frozenset({"describe", "query_sql", "assertion", "rerun"})
SUCCESS_TERMINAL_EVENTS = frozenset(
    {"SOURCE_READ", "SOURCE_SEARCH", "TASKVIEW_TOOL", "SCRATCH_WRITE"}
)


class AccountingInvariantError(RuntimeError):
    """A scientifically meaningful provider/bridge invariant failed."""


def _jsonable(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _jsonable(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def _field(value: Any, name: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(name, default)
    return getattr(value, name, default)


def _canonical_json(value: Any) -> str:
    return json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_tool_arguments(tool_name: str, arguments: Any) -> dict[str, Any]:
    """Normalize provider and bridge serialization, never logical occurrences.

    Cursor omits default-valued MCP arguments while EpisodeTools records them.
    The write tool records content length rather than content in bridge telemetry.
    This function only makes those two representations comparable; it is not an
    identity or deduplication function.
    """

    args = dict(_jsonable(arguments) or {})
    if tool_name == "search_source":
        return {"query": args.get("query"), "scope": args.get("scope", ".")}
    if tool_name == "read_source":
        return {
            "path": args.get("path"),
            "start_line": args.get("start_line", 1),
            "end_line": args.get("end_line", 10_000),
        }
    if tool_name == "write_scratch":
        content = args.get("content")
        content_bytes = args.get("content_bytes")
        if content_bytes is None and isinstance(content, str):
            content_bytes = len(content.encode("utf-8"))
        return {"path": args.get("path"), "content_bytes": content_bytes}
    if tool_name == "describe":
        return {"relation": args.get("relation"), "why": args.get("why")}
    if tool_name == "query_sql":
        return {"sql": args.get("sql"), "parameters": args.get("parameters") or []}
    if tool_name == "assertion":
        # Frozen EpisodeTools intentionally omits grounding from its call marker.
        return {
            "action": args.get("action"),
            "relation": args.get("relation"),
            "values": args.get("values"),
        }
    if tool_name == "rerun":
        return {"relation": args.get("relation")}
    return args


def _provider_tool(message: Any) -> tuple[str, dict[str, Any]]:
    name = str(_field(message, "name", ""))
    args = _field(message, "args")
    if name == "mcp" and isinstance(args, Mapping):
        tool_name = args.get("toolName")
        if tool_name:
            name = str(tool_name)
            args = args.get("args")
    return name, canonical_tool_arguments(name, args)


def _content_texts(result: Any) -> list[str]:
    value = _field(result, "value")
    content = _field(value, "content") if value is not None else None
    if not isinstance(content, (list, tuple)):
        return []
    texts: list[str] = []
    for item in content:
        text = _field(item, "text")
        if isinstance(text, str):
            texts.append(text)
        elif isinstance(text, Mapping) and isinstance(text.get("text"), str):
            texts.append(text["text"])
    return texts


def delivered_payload_bytes(result: Any) -> int:
    """Count exact UTF-8 text payload bytes exposed in the MCP result content."""

    texts = _content_texts(result)
    if not texts:
        raise AccountingInvariantError("tool result has no attributable model-visible text payload")
    return sum(len(text.encode("utf-8")) for text in texts)


def _result_is_error(message: Any) -> bool:
    if str(_field(message, "status", "")) == "error":
        return True
    result = _field(message, "result")
    value = _field(result, "value")
    return bool(_field(value, "isError", False))


def _provider_validation_rejected(message: Any) -> bool:
    """Recognize only errors which demonstrably occurred before handler entry."""

    if str(_field(message, "status", "")) == "error":
        return True
    text = "\n".join(_content_texts(_field(message, "result"))).lower()
    return "validation error for " in text and (
        "field required" in text or "pydantic.dev" in text
    )


@dataclass(frozen=True)
class SdkObservation:
    phase: int
    sdk_event_id: str
    timestamp_ns: int | None
    message: Any


@dataclass(frozen=True)
class LogicalCall:
    provider_session_id: str
    provider_call_id: str
    run_id: str
    phase: int
    tool_name: str
    tool_arguments: dict[str, Any]
    start_sdk_event_id: str
    complete_sdk_event_id: str
    start_timestamp_ns: int | None
    complete_timestamp_ns: int | None
    result: Any
    model_visible_output_bytes: int
    is_error: bool
    provider_validation_rejected: bool

    @property
    def identity(self) -> tuple[str, str]:
        return (self.provider_session_id, self.provider_call_id)

    @property
    def signature(self) -> tuple[str, str]:
        return (self.tool_name, _canonical_json(self.tool_arguments))


@dataclass(frozen=True)
class BridgeExecution:
    bridge_execution_id: str
    bridge_request_id: str | None
    bridge_session_id: str | None
    server_instance_id: str | None
    provider_call_id: str | None
    phase: int
    tool_name: str
    tool_arguments: dict[str, Any]
    record_index: int
    timestamp_ns: int | None
    response_record_index: int | None
    outcome: str | None

    @property
    def signature(self) -> tuple[str, str]:
        return (self.tool_name, _canonical_json(self.tool_arguments))


@dataclass(frozen=True)
class AccountingReport:
    logical_calls: tuple[LogicalCall, ...]
    bridge_executions: tuple[BridgeExecution, ...]
    execution_to_call: dict[str, tuple[str, str]]
    call_to_execution: dict[tuple[str, str], str]
    replay_observations: int
    sdk_tool_observations: int
    per_operation_response_bytes: dict[str, int]
    legacy_bridge_telemetry: bool

    @property
    def logical_call_count(self) -> int:
        return len(self.logical_calls)

    @property
    def model_visible_tool_result_bytes(self) -> int:
        return sum(call.model_visible_output_bytes for call in self.logical_calls)

    @property
    def provider_errors(self) -> int:
        return sum(call.is_error for call in self.logical_calls)

    @property
    def provider_validation_rejections(self) -> int:
        return sum(call.provider_validation_rejected for call in self.logical_calls)


def observations_from_trajectory(records: Iterable[dict[str, Any]]) -> list[SdkObservation]:
    observations: list[SdkObservation] = []
    for index, record in enumerate(records):
        event = record.get("event")
        if not isinstance(event, Mapping) or event.get("sdk_message") is None:
            continue
        message = event["sdk_message"]
        if _field(message, "type") != "tool_call":
            continue
        run_id = str(_field(message, "run_id", "unknown-run"))
        offset = event.get("offset")
        sdk_event_id = f"{run_id}:{offset}" if offset is not None else f"record:{index}"
        observations.append(
            SdkObservation(
                phase=int(record.get("phase", 0)),
                sdk_event_id=sdk_event_id,
                timestamp_ns=record.get("timestamp_ns"),
                message=message,
            )
        )
    return observations


def _logical_calls(
    observations: Iterable[SdkObservation],
    *,
    expected_session_id: str,
    allowed_tool_names: set[str],
) -> tuple[list[LogicalCall], int, int]:
    unique_events: dict[str, SdkObservation] = {}
    replay_count = 0
    raw_count = 0
    for observation in observations:
        raw_count += 1
        prior = unique_events.get(observation.sdk_event_id)
        if prior is not None:
            if _canonical_json(prior.message) != _canonical_json(observation.message):
                raise AccountingInvariantError(
                    f"conflicting replay for SDK event {observation.sdk_event_id}"
                )
            replay_count += 1
            continue
        unique_events[observation.sdk_event_id] = observation

    grouped: dict[tuple[str, str], list[SdkObservation]] = defaultdict(list)
    for observation in unique_events.values():
        message = observation.message
        session_id = str(_field(message, "agent_id", ""))
        call_id = str(_field(message, "call_id", ""))
        if not call_id:
            raise AccountingInvariantError("SDK tool lifecycle observation has no call_id")
        if session_id != expected_session_id:
            raise AccountingInvariantError(
                f"cross-session tool observation: {session_id!r} != {expected_session_id!r}"
            )
        grouped[(session_id, call_id)].append(observation)

    calls: list[LogicalCall] = []
    for identity, lifecycle in grouped.items():
        starts = [item for item in lifecycle if str(_field(item.message, "status", "")) == "running"]
        completes = [
            item
            for item in lifecycle
            if str(_field(item.message, "status", "")) in {"completed", "error"}
        ]
        if len(starts) != 1 or len(completes) != 1:
            raise AccountingInvariantError(
                f"logical call {identity} has {len(starts)} starts and {len(completes)} completions"
            )
        start, complete = starts[0], completes[0]
        start_name, start_args = _provider_tool(start.message)
        complete_name, complete_args = _provider_tool(complete.message)
        if (start_name, start_args) != (complete_name, complete_args):
            raise AccountingInvariantError(f"tool identity changed during lifecycle for {identity}")
        if start_name not in allowed_tool_names:
            raise AccountingInvariantError(f"SDK exposed a non-frozen tool: {start_name!r}")
        start_run = str(_field(start.message, "run_id", ""))
        complete_run = str(_field(complete.message, "run_id", ""))
        if start_run != complete_run or start.phase != complete.phase:
            raise AccountingInvariantError(f"provider retry changed call semantics for {identity}")
        result = _field(complete.message, "result")
        calls.append(
            LogicalCall(
                provider_session_id=identity[0],
                provider_call_id=identity[1],
                run_id=start_run,
                phase=start.phase,
                tool_name=start_name,
                tool_arguments=start_args,
                start_sdk_event_id=start.sdk_event_id,
                complete_sdk_event_id=complete.sdk_event_id,
                start_timestamp_ns=start.timestamp_ns,
                complete_timestamp_ns=complete.timestamp_ns,
                result=_jsonable(result),
                model_visible_output_bytes=delivered_payload_bytes(result),
                is_error=_result_is_error(complete.message),
                provider_validation_rejected=_provider_validation_rejected(complete.message),
            )
        )
    order = {event_id: index for index, event_id in enumerate(unique_events)}
    calls.sort(key=lambda call: order[call.start_sdk_event_id])
    return calls, replay_count, raw_count


def _bridge_executions(records: list[dict[str, Any]]) -> tuple[list[BridgeExecution], bool]:
    request_records = [
        (index, record) for index, record in enumerate(records) if record.get("event_type") == "BRIDGE_REQUEST"
    ]
    if not request_records:
        legacy: list[BridgeExecution] = []
        for index, record in enumerate(records):
            if record.get("event_type") not in {"TOOL_CALL", "SCRATCH_WRITE"}:
                continue
            payload = record.get("payload", {})
            name = str(payload.get("tool_name", ""))
            legacy.append(
                BridgeExecution(
                    bridge_execution_id=f"legacy:{index}",
                    bridge_request_id=None,
                    bridge_session_id=None,
                    server_instance_id=None,
                    provider_call_id=None,
                    phase=int(record.get("phase", 0)),
                    tool_name=name,
                    tool_arguments=canonical_tool_arguments(name, payload.get("tool_arguments")),
                    record_index=index,
                    timestamp_ns=record.get("timestamp_ns"),
                    response_record_index=None,
                    outcome=None,
                )
            )
        return legacy, True

    responses: dict[str, tuple[int, dict[str, Any]]] = {}
    for index, record in enumerate(records):
        if record.get("event_type") != "BRIDGE_RESPONSE":
            continue
        execution_id = str(record.get("payload", {}).get("bridge_execution_id", ""))
        if not execution_id or execution_id in responses:
            raise AccountingInvariantError(f"duplicate or missing bridge response identity: {execution_id!r}")
        responses[execution_id] = (index, record)

    executions: list[BridgeExecution] = []
    seen: set[str] = set()
    for index, record in request_records:
        payload = record.get("payload", {})
        execution_id = str(payload.get("bridge_execution_id", ""))
        if not execution_id or execution_id in seen:
            raise AccountingInvariantError(f"duplicate or missing bridge execution identity: {execution_id!r}")
        seen.add(execution_id)
        if execution_id not in responses:
            raise AccountingInvariantError(f"missing bridge response for {execution_id}")
        response_index, response = responses[execution_id]
        name = str(payload.get("tool_name", ""))
        executions.append(
            BridgeExecution(
                bridge_execution_id=execution_id,
                bridge_request_id=str(payload.get("bridge_request_id")),
                bridge_session_id=(
                    str(payload["bridge_session_id"])
                    if payload.get("bridge_session_id") is not None
                    else None
                ),
                server_instance_id=(
                    str(payload["server_instance_id"])
                    if payload.get("server_instance_id") is not None
                    else None
                ),
                provider_call_id=(
                    str(payload["provider_call_id"])
                    if payload.get("provider_call_id") is not None
                    else None
                ),
                phase=int(record.get("phase", 0)),
                tool_name=name,
                tool_arguments=canonical_tool_arguments(name, payload.get("tool_arguments")),
                record_index=index,
                timestamp_ns=record.get("timestamp_ns"),
                response_record_index=response_index,
                outcome=str(response.get("payload", {}).get("outcome", "")),
            )
        )
    extra_responses = set(responses) - seen
    if extra_responses:
        raise AccountingInvariantError(f"bridge responses without executions: {sorted(extra_responses)}")
    return executions, False


def reconcile_turn(
    observations: Iterable[SdkObservation],
    bridge_records: list[dict[str, Any]],
    *,
    expected_session_id: str,
    allowed_tool_names: set[str],
    expected_bridge_session_id: str | None = None,
) -> AccountingReport:
    calls, replay_count, raw_count = _logical_calls(
        observations,
        expected_session_id=expected_session_id,
        allowed_tool_names=allowed_tool_names,
    )
    executions, legacy = _bridge_executions(bridge_records)
    if expected_bridge_session_id is not None:
        contaminated = sorted(
            {
                execution.bridge_session_id
                for execution in executions
                if execution.bridge_session_id != expected_bridge_session_id
            },
            key=str,
        )
        if contaminated:
            raise AccountingInvariantError(
                f"cross-session bridge execution: {contaminated!r} != "
                f"{expected_bridge_session_id!r}"
            )

    execution_to_call: dict[str, tuple[str, str]] = {}
    call_to_execution: dict[tuple[str, str], str] = {}
    calls_by_provider_id = {call.provider_call_id: call for call in calls}

    # Prefer a provider call ID propagated in MCP request metadata when Cursor
    # supplies one. This remains exact even for concurrent identical calls.
    for execution in (item for item in executions if item.provider_call_id is not None):
        call = calls_by_provider_id.get(execution.provider_call_id or "")
        if call is None:
            raise AccountingInvariantError(
                f"bridge execution names unknown provider call {execution.provider_call_id!r}"
            )
        if call.identity in call_to_execution:
            raise AccountingInvariantError(f"duplicate tool execution for {call.identity}")
        if call.provider_validation_rejected:
            raise AccountingInvariantError(
                f"provider-validation rejection unexpectedly executed: {call.identity}"
            )
        if execution.phase != call.phase or execution.signature != call.signature:
            raise AccountingInvariantError(f"bridge/provider call identity mismatch for {call.identity}")
        execution_to_call[execution.bridge_execution_id] = call.identity
        call_to_execution[call.identity] = execution.bridge_execution_id
        if execution.outcome == "error" and not call.is_error:
            raise AccountingInvariantError(f"bridge/provider outcome mismatch for {call.identity}")
        if execution.outcome == "success" and call.is_error:
            raise AccountingInvariantError(f"bridge/provider outcome mismatch for {call.identity}")

    # Cursor SDK 1.0.30 does not promise that metadata field. The smallest
    # fallback preserves multiplicity and pairs by phase + normalized signature
    # + occurrence; it never deduplicates calls by arguments.
    queues: dict[tuple[int, tuple[str, str]], deque[LogicalCall]] = defaultdict(deque)
    for call in calls:
        if not call.provider_validation_rejected and call.identity not in call_to_execution:
            queues[(call.phase, call.signature)].append(call)
    for execution in (item for item in executions if item.provider_call_id is None):
        queue = queues[(execution.phase, execution.signature)]
        if not queue:
            raise AccountingInvariantError(
                "unattributable or duplicate tool execution: "
                f"{execution.tool_name} {execution.tool_arguments}"
            )
        call = queue.popleft()
        execution_to_call[execution.bridge_execution_id] = call.identity
        call_to_execution[call.identity] = execution.bridge_execution_id
        if execution.outcome == "error" and not call.is_error:
            raise AccountingInvariantError(f"bridge/provider outcome mismatch for {call.identity}")
        if execution.outcome == "success" and call.is_error:
            raise AccountingInvariantError(f"bridge/provider outcome mismatch for {call.identity}")

    missing = [call.identity for queue in queues.values() for call in queue]
    if missing:
        raise AccountingInvariantError(f"accepted logical calls missing executions: {missing}")
    rejected_with_execution = [
        call.identity
        for call in calls
        if call.provider_validation_rejected and call.identity in call_to_execution
    ]
    if rejected_with_execution:
        raise AccountingInvariantError(
            f"provider-validation rejections unexpectedly executed: {rejected_with_execution}"
        )

    by_operation: dict[str, int] = defaultdict(int)
    for call in calls:
        by_operation[call.tool_name] += call.model_visible_output_bytes
    if sum(by_operation.values()) != sum(call.model_visible_output_bytes for call in calls):
        raise AccountingInvariantError("per-operation response-byte totals do not reconcile")

    return AccountingReport(
        logical_calls=tuple(calls),
        bridge_executions=tuple(executions),
        execution_to_call=execution_to_call,
        call_to_execution=call_to_execution,
        replay_observations=replay_count,
        sdk_tool_observations=raw_count,
        per_operation_response_bytes=dict(sorted(by_operation.items())),
        legacy_bridge_telemetry=legacy,
    )


def trajectory_event_taxonomy(records: Iterable[dict[str, Any]]) -> dict[str, int | None]:
    """Summarize actual Cursor SDK event types without treating fragments as calls."""

    counts: dict[str, int | None] = {
        "MODEL_TOOL_INTENT": None,  # Cursor SDK 1.0.30 does not expose this separately.
        "SDK_TOOL_CALL_START": 0,
        "SDK_TOOL_CALL_COMPLETE": 0,
        "STREAM_FRAGMENT": 0,
    }
    for record in records:
        event = record.get("event")
        if not isinstance(event, Mapping) or event.get("sdk_message") is None:
            continue
        message = event["sdk_message"]
        if _field(message, "type") == "tool_call":
            status = str(_field(message, "status", ""))
            if status == "running":
                counts["SDK_TOOL_CALL_START"] = int(counts["SDK_TOOL_CALL_START"] or 0) + 1
            elif status in {"completed", "error"}:
                counts["SDK_TOOL_CALL_COMPLETE"] = int(counts["SDK_TOOL_CALL_COMPLETE"] or 0) + 1
        else:
            counts["STREAM_FRAGMENT"] = int(counts["STREAM_FRAGMENT"] or 0) + 1
    return counts


def timeline_rows(report: AccountingReport) -> list[dict[str, Any]]:
    """Return one mechanically attributable row per provider logical call."""

    executions = {item.bridge_execution_id: item for item in report.bridge_executions}
    rows: list[dict[str, Any]] = []
    for sequence, call in enumerate(report.logical_calls, start=1):
        execution_id = report.call_to_execution.get(call.identity)
        execution = executions.get(execution_id) if execution_id is not None else None
        rows.append(
            {
                "logical_sequence": sequence,
                "provider_session_id": call.provider_session_id,
                "provider_call_id": call.provider_call_id,
                "provider_run_id": call.run_id,
                "sdk_start_event_id": call.start_sdk_event_id,
                "sdk_complete_event_id": call.complete_sdk_event_id,
                "sdk_start_timestamp_ns": call.start_timestamp_ns,
                "sdk_complete_timestamp_ns": call.complete_timestamp_ns,
                "bridge_execution_id": execution_id,
                "bridge_request_id": execution.bridge_request_id if execution else None,
                "bridge_record_index": execution.record_index if execution else None,
                "bridge_timestamp_ns": execution.timestamp_ns if execution else None,
                "phase": call.phase,
                "operation": call.tool_name,
                "arguments": call.tool_arguments,
                "outcome": "error" if call.is_error else "success",
                "provider_validation_rejected": call.provider_validation_rejected,
                "model_visible_output_bytes": call.model_visible_output_bytes,
            }
        )
    return rows
