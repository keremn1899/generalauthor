"""Cursor MCP bridge for the frozen TaskView orientation tools.

The server is launched inside an episode workspace.  All mutable paths and
the visible arm are supplied by the parent runtime; no participant chooses
them.  Logical tool telemetry is written to a bridge log and merged into the
episode's canonical telemetry by the parent after each participant turn.
"""

from __future__ import annotations

import fcntl
import json
import os
import time
import uuid
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from research.taskview_orientation.fixture import TASK_SPEC_REF, VIEW_ID
from research.taskview_orientation.surface import ExperimentTaskViewSurface
from research.taskview_orientation.tools import EpisodeTools
from taskview import TaskView


SERVER_NAME = "taskview-orientation"
SERVER_INSTANCE_ID = uuid.uuid4().hex
mcp = FastMCP(
    SERVER_NAME,
    instructions=(
        "Frozen TaskView orientation experiment tools. Use only the tools "
        "declared by this server for repository evidence and TaskView access."
    ),
    log_level="ERROR",
)


def _required_path(name: str) -> Path:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"missing frozen runtime environment variable: {name}")
    return Path(value).resolve()


class _BridgeTelemetry:
    """Minimal EpisodeTools-compatible append-only telemetry sink."""

    def __init__(
        self,
        *,
        bridge_request_id: str,
        bridge_execution_id: str,
        provider_call_id: str | None,
    ) -> None:
        self.path = _required_path("TASKVIEW_BRIDGE_TELEMETRY")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.bridge_request_id = bridge_request_id
        self.bridge_execution_id = bridge_execution_id
        self.provider_call_id = provider_call_id

    def record(self, event_type: str, *, phase: int, **payload: Any) -> dict[str, Any]:
        payload.setdefault("bridge_request_id", self.bridge_request_id)
        payload.setdefault("bridge_execution_id", self.bridge_execution_id)
        if self.provider_call_id is not None:
            payload.setdefault("provider_call_id", self.provider_call_id)
        record = {
            "timestamp_ns": time.time_ns(),
            "event_type": event_type,
            "phase": phase,
            "payload": payload,
        }
        with self.path.open("a", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            handle.write(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n")
            handle.flush()
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        return {"tool_arguments": payload.get("tool_arguments")}


def _phase() -> int:
    state = json.loads(_required_path("TASKVIEW_PHASE_STATE").read_text(encoding="utf-8"))
    return int(state["phase"])


def _episode_tools(telemetry: _BridgeTelemetry) -> tuple[EpisodeTools, TaskView | None]:
    phase = _phase()
    view: TaskView | None = None
    surface = None
    if os.environ.get("TASKVIEW_ARM") == "TASKVIEW":
        view = TaskView(
            _required_path("TASKVIEW_DB_PATH"),
            view_id=VIEW_ID,
            task_spec_ref=TASK_SPEC_REF,
        )
        surface = ExperimentTaskViewSurface(view)
    tools = EpisodeTools(
        source_root=_required_path("TASKVIEW_SOURCE_ROOT"),
        scratch_root=_required_path("TASKVIEW_SCRATCH_ROOT"),
        telemetry=telemetry,
        taskview=surface,
    )
    tools.set_phase(phase)
    if phase >= 4:
        tools.mark_phase4_source()
    return tools, view


def _context_provider_call_id(ctx: Context) -> str | None:
    """Read Cursor's tool identity if it is propagated through MCP metadata."""

    meta = ctx.request_context.meta
    if meta is None:
        return None
    value = meta.model_dump(by_alias=True)
    stack: list[Any] = [value]
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            for key, candidate in item.items():
                if key in {"toolCallId", "tool_call_id", "providerCallId"} and isinstance(
                    candidate, str
                ):
                    return candidate
                stack.append(candidate)
        elif isinstance(item, list):
            stack.extend(item)
    return None


def _call(callback, *, ctx: Context, tool_name: str, tool_arguments: dict[str, Any]):
    bridge_request_id = ctx.request_id
    bridge_session_id = os.environ["TASKVIEW_BRIDGE_SESSION_ID"]
    bridge_execution_id = f"{bridge_session_id}:{SERVER_INSTANCE_ID}:{bridge_request_id}"
    provider_call_id = _context_provider_call_id(ctx)
    telemetry = _BridgeTelemetry(
        bridge_request_id=bridge_request_id,
        bridge_execution_id=bridge_execution_id,
        provider_call_id=provider_call_id,
    )
    phase = _phase()
    telemetry.record(
        "BRIDGE_REQUEST",
        phase=phase,
        tool_name=tool_name,
        tool_arguments=tool_arguments,
        bridge_session_id=bridge_session_id,
        server_instance_id=SERVER_INSTANCE_ID,
    )
    tools, view = _episode_tools(telemetry)
    try:
        result = callback(tools)
        telemetry.record(
            "BRIDGE_RESPONSE",
            phase=phase,
            tool_name=tool_name,
            tool_arguments=tool_arguments,
            outcome="success",
        )
        return result
    except Exception as exc:
        telemetry.record(
            "BRIDGE_RESPONSE",
            phase=phase,
            tool_name=tool_name,
            tool_arguments=tool_arguments,
            outcome="error",
            error_type=type(exc).__name__,
        )
        raise
    finally:
        if view is not None:
            view.close()


@mcp.tool(description="Search participant-visible source text under a relative scope.")
def search_source(query: str, scope: str = ".", ctx: Context = None) -> dict[str, Any]:
    return _call(
        lambda tools: tools.search_source(query, scope),
        ctx=ctx,
        tool_name="search_source",
        tool_arguments={"query": query, "scope": scope},
    )


@mcp.tool(description="Read an inclusive line range from one participant-visible source file.")
def read_source(
    path: str, start_line: int = 1, end_line: int = 10_000, ctx: Context = None
) -> dict[str, Any]:
    return _call(
        lambda tools: tools.read_source(path, start_line, end_line),
        ctx=ctx,
        tool_name="read_source",
        tool_arguments={"path": path, "start_line": start_line, "end_line": end_line},
    )


@mcp.tool(
    description=(
        "Write a UTF-8 scratch artifact outside the read-only source tree. Scratch "
        "paths are never valid citations: cite only source paths returned by "
        "read_source or search_source."
    )
)
def write_scratch(path: str, content: str, ctx: Context = None) -> dict[str, Any]:
    return _call(
        lambda tools: tools.write_scratch(path, content),
        ctx=ctx,
        tool_name="write_scratch",
        tool_arguments={"path": path, "content_bytes": len(content.encode("utf-8"))},
    )


if os.environ.get("TASKVIEW_ARM") == "TASKVIEW":

    @mcp.tool(
        description=(
            "Describe the compact relation catalog, one named relation, or one "
            "tuple's grounding. Supply at most one of relation and why. Bare "
            "catalog role names are REFERENT roles; targeted relation detail "
            "shows physical SQL columns."
        )
    )
    def describe(
        relation: str | None = None,
        why: dict[str, Any] | None = None,
        ctx: Context = None,
    ) -> dict[str, Any]:
        return _call(
            lambda tools: tools.describe(relation=relation, why=why),
            ctx=ctx,
            tool_name="describe",
            tool_arguments={"relation": relation, "why": why},
        )

    @mcp.tool(description="Run read-only SQL over declared semantic relation tables.")
    def query_sql(
        sql: str, parameters: list[Any] | None = None, ctx: Context = None
    ) -> dict[str, Any]:
        return _call(
            lambda tools: tools.query_sql(sql, tuple(parameters or ())),
            ctx=ctx,
            tool_name="query_sql",
            tool_arguments={"sql": sql, "parameters": list(parameters or ())},
        )

    @mcp.tool(description="Assert or retract one BASE semantic tuple.")
    def assertion(
        action: str,
        relation: str,
        values: dict[str, Any],
        grounding: list[dict[str, Any]] | None = None,
        ctx: Context = None,
    ) -> dict[str, Any]:
        return _call(
            lambda tools: tools.assertion(
                action=action,
                relation=relation,
                values=values,
                grounding=tuple(grounding or ()),
            ),
            ctx=ctx,
            tool_name="assertion",
            tool_arguments={"action": action, "relation": relation, "values": values},
        )

    @mcp.tool(description="Rerun a registered derivation under its fixture-owned contract.")
    def rerun(relation: str, ctx: Context = None) -> dict[str, Any]:
        return _call(
            lambda tools: tools.rerun(relation),
            ctx=ctx,
            tool_name="rerun",
            tool_arguments={"relation": relation},
        )


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
