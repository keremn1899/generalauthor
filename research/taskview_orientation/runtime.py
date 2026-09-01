"""Pinned Cursor Composer 2.5 adapter for the TaskView Stage 1 campaign.

Each episode owns one Cursor chat ID and resumes it for all five turns. The
participant workspace exposes the frozen logical tools through one project MCP
server; Cursor built-ins and unrelated MCP servers invalidate the turn.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any

from research.taskview_orientation.fixture import semantic_rows
from research.taskview_orientation.oracle import load_oracle
from research.taskview_orientation.runner import ParticipantTurn
from research.taskview_orientation.telemetry import visible_bytes
from research.taskview_orientation.tools import EpisodeTools


ADAPTER_VERSION = "taskview-cursor-agent-v2"
CURSOR_AGENT_VERSION = "2026.08.25-3e8eec8"
MODEL = "composer-2.5"
MODEL_DISPLAY_NAME = "Composer 2.5"
MODEL_PROVIDER = "cursor"
REASONING_EFFORT = "model-default"
SERVICE_TIER = "cursor-default"
TURN_TIMEOUT_SECONDS = 300
MAX_STRUCTURED_ANSWER_TOKENS = 4000
MODEL_CONTEXT_WINDOW: int | None = None
MCP_SERVER_NAME = "taskview-orientation"


def sha256_json(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _schema_for_value(value: Any) -> dict[str, Any]:
    if isinstance(value, bool):
        return {"type": "boolean"}
    if isinstance(value, int):
        return {"type": "integer"}
    if isinstance(value, str):
        return {"type": "string"}
    if isinstance(value, list):
        item = _schema_for_value(value[0]) if value else {"type": "string"}
        return {"type": "array", "items": item}
    raise TypeError(f"unsupported frozen answer value: {value!r}")


def answer_schema(phase: int) -> dict[str, Any]:
    oracle = load_oracle()["phases"][str(phase)]
    properties = {
        name: _schema_for_value(value)
        for name, value in oracle.items()
        if name != "citation_witnesses"
    }
    properties["citations"] = {
        "type": "array",
        "minItems": 1,
        "items": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "start_line": {"type": "integer"},
                "end_line": {"type": "integer"},
            },
            "required": ["path", "start_line", "end_line"],
            "additionalProperties": False,
        },
    }
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }


PROVIDER_TOOL_SCHEMAS: dict[str, dict[str, Any]] = {
    "search_source": {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "scope": {"type": "string", "default": "."},
        },
        "required": ["query"],
        "additionalProperties": False,
    },
    "read_source": {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "start_line": {"type": "integer", "minimum": 1, "default": 1},
            "end_line": {"type": "integer", "minimum": 1, "default": 10000},
        },
        "required": ["path"],
        "additionalProperties": False,
    },
    "write_scratch": {
        "type": "object",
        "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
        "required": ["path", "content"],
        "additionalProperties": False,
    },
    "describe": {
        "type": "object",
        "properties": {
            "relation": {"type": ["string", "null"]},
            "why": {"type": ["object", "null"], "additionalProperties": True},
        },
        "additionalProperties": False,
    },
    "query_sql": {
        "type": "object",
        "properties": {
            "sql": {"type": "string"},
            "parameters": {"type": "array", "default": []},
        },
        "required": ["sql"],
        "additionalProperties": False,
    },
    "assertion": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["ASSERT", "RETRACT"]},
            "relation": {"type": "string"},
            "values": {"type": "object", "additionalProperties": True},
            "grounding": {"type": "array", "default": []},
        },
        "required": ["action", "relation", "values"],
        "additionalProperties": False,
    },
    "rerun": {
        "type": "object",
        "properties": {"relation": {"type": "string"}},
        "required": ["relation"],
        "additionalProperties": False,
    },
}


def provider_tools(frozen_schemas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Canonical Cursor-MCP serialization recorded in the frozen manifest."""
    return [
        {
            "server": MCP_SERVER_NAME,
            "name": record["name"],
            "description": record["description"],
            "inputSchema": PROVIDER_TOOL_SCHEMAS[record["name"]],
        }
        for record in frozen_schemas
    ]


class CursorRuntimeError(RuntimeError):
    pass


def cursor_version() -> str:
    result = subprocess.run(
        ["cursor-agent", "--version"], text=True, capture_output=True, check=False
    )
    if result.returncode != 0:
        raise CursorRuntimeError(f"cursor-agent --version failed: {result.stderr.strip()}")
    return result.stdout.strip()


def isolated_cursor_prefix(workspace: Path) -> list[str]:
    """Hide global MCP/plugin configuration without changing the user's files."""
    workspace = workspace.resolve()
    isolation = workspace / ".cursor_runtime_isolation"
    empty_plugins = isolation / "plugins"
    empty_plugins.mkdir(parents=True, exist_ok=True)
    empty_mcp = isolation / "mcp.json"
    empty_mcp.write_text("{\"mcpServers\":{}}\n", encoding="utf-8")
    user_cursor = Path.home() / ".cursor"
    return [
        "bwrap", "--bind", "/", "/",
        "--bind", str(empty_plugins), str(user_cursor / "plugins"),
        "--ro-bind", str(empty_mcp), str(user_cursor / "mcp.json"),
    ]


def stream_events(stdout: str, stderr: str = "") -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line in (stdout + ("\n" + stderr if stderr else "")).splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def mcp_identity(event: dict[str, Any]) -> tuple[str | None, str | None]:
    call = event.get("tool_call", {}).get("mcpToolCall", {})
    args = call.get("args", {}) if isinstance(call, dict) else {}
    server = (
        args.get("server")
        or args.get("serverName")
        or args.get("serverIdentifier")
        or args.get("providerIdentifier")
        or call.get("server")
    )
    tool = args.get("tool") or args.get("toolName") or call.get("tool") or call.get("name")
    return (
        str(server) if server is not None else None,
        str(tool) if tool is not None else None,
    )


def provider_validation_rejections(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return MCP calls rejected by Cursor before the server handler ran.

    Cursor reports these as completed MCP transport calls even though FastMCP
    validation prevents the logical tool function (and its telemetry hook)
    from running. They are participant tool attempts and must be retained as
    failed canonical tool calls rather than mistaken for telemetry loss.
    """
    rejected: list[dict[str, Any]] = []
    for event in events:
        if event.get("type") != "tool_call" or event.get("subtype") != "completed":
            continue
        call = event.get("tool_call", {}).get("mcpToolCall")
        if not isinstance(call, dict):
            continue
        result_text = json.dumps(call.get("result", {}), sort_keys=True, ensure_ascii=False)
        normalized = result_text.lower()
        if "error executing tool" not in normalized or "validation error" not in normalized:
            continue
        arguments = call.get("args", {})
        rejected.append(
            {
                "call_id": arguments.get("toolCallId") or event.get("call_id"),
                "tool_name": arguments.get("toolName"),
                "tool_arguments": arguments.get("args", {}),
                "provider_result": call.get("result", {}),
            }
        )
    return rejected


def _strip_json_fence(text: str) -> str:
    value = text.strip()
    if value.startswith("```json") and value.endswith("```"):
        return value[7:-3].strip()
    if value.startswith("```") and value.endswith("```"):
        return value[3:-3].strip()
    return value


class CursorParticipantSession:
    """One pinned Cursor chat resumed for all five turns of an episode."""

    def __init__(
        self,
        system_prompt: str,
        frozen_schemas: list[dict[str, Any]],
        arm: str,
        *,
        raw_path: Path,
        state_path: Path,
        workspace: Path,
        condition: str | None = None,
    ) -> None:
        actual_version = cursor_version()
        if actual_version != CURSOR_AGENT_VERSION:
            raise CursorRuntimeError(
                f"Cursor CLI drift: expected {CURSOR_AGENT_VERSION}, got {actual_version}"
            )
        self.arm = arm
        self.condition = condition
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
        self._bridge_session_id = f"bridge-{uuid.uuid4().hex}"
        self._bridge_offset = 0
        self._first_turn = True
        self._configure_mcp()
        created = subprocess.run(
            ["cursor-agent", "create-chat"], cwd=self.workspace, text=True,
            capture_output=True, check=False, timeout=30,
        )
        if created.returncode != 0 or not created.stdout.strip():
            raise CursorRuntimeError(f"cursor-agent create-chat failed: {created.stderr.strip()}")
        self.session_id = created.stdout.strip().splitlines()[-1]
        self.provider_session_id = self.session_id
        self.cli_version = CURSOR_AGENT_VERSION

    def _configure_mcp(self) -> None:
        repository_root = Path(__file__).resolve().parents[2]
        python_path = os.environ.get("PYTHONPATH", "")
        server_env = {
            "PYTHONPATH": str(repository_root) + (os.pathsep + python_path if python_path else ""),
            "TASKVIEW_ARM": self.arm,
            "TASKVIEW_SOURCE_ROOT": "PENDING_FIRST_TURN",
            "TASKVIEW_SCRATCH_ROOT": "PENDING_FIRST_TURN",
            "TASKVIEW_DB_PATH": "PENDING_FIRST_TURN",
            "TASKVIEW_PHASE_STATE": str(self._phase_state_path),
            "TASKVIEW_BRIDGE_TELEMETRY": str(self._bridge_telemetry_path),
            "TASKVIEW_BRIDGE_SESSION_ID": self._bridge_session_id,
        }
        if self.condition:
            server_env["TASKVIEW_CONDITION"] = self.condition
        if self.condition in {"T00", "T10", "T01", "T11"}:
            server_module = (
                "research.taskview_orientation.bounded_reliance.cursor_tool_server"
            )
        elif self.condition in {"ATOMIC", "COMPILED"}:
            server_module = (
                "research.taskview_orientation.compiled_projection.cursor_tool_server"
            )
        else:
            server_module = "research.taskview_orientation.cursor_tool_server"
        config = {"mcpServers": {MCP_SERVER_NAME: {
            "command": sys.executable,
            "args": ["-m", server_module],
            "env": server_env,
        }}}
        config_dir = self.workspace / ".cursor"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "mcp.json").write_text(
            json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    def _bind_turn_paths(self, tools: EpisodeTools, phase: int) -> None:
        config_path = self.workspace / ".cursor" / "mcp.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        env = config["mcpServers"][MCP_SERVER_NAME]["env"]
        env["TASKVIEW_SOURCE_ROOT"] = str(tools.source_root)
        env["TASKVIEW_SCRATCH_ROOT"] = str(tools.scratch_root)
        env["TASKVIEW_DB_PATH"] = (
            str(tools.taskview.view.path) if tools.taskview is not None else "RAW_ARM_NO_TASKVIEW"
        )
        config_path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        self._phase_state_path.write_text(
            json.dumps({"phase": phase, "source_version": tools.source_version}) + "\n",
            encoding="utf-8",
        )

    def _record_raw(
        self, phase: int, command: list[str], result: subprocess.CompletedProcess[str]
    ) -> None:
        self._raw.write(json.dumps({
            "type": "adapter_command", "phase": phase, "timestamp_ns": time.time_ns(),
            "command": command[:-1] + ["<participant-prompt>"], "returncode": result.returncode,
        }, sort_keys=True) + "\n")
        self._raw.write(result.stdout)
        if result.stdout and not result.stdout.endswith("\n"):
            self._raw.write("\n")
        for line in result.stderr.splitlines():
            self._raw.write(json.dumps(
                {"type": "provider_stderr", "phase": phase, "text": line}
            ) + "\n")
        self._raw.flush()

    def _merge_bridge_telemetry(self, tools: EpisodeTools) -> int:
        if not self._bridge_telemetry_path.exists():
            return 0
        lines = self._bridge_telemetry_path.read_text(encoding="utf-8").splitlines()
        fresh = lines[self._bridge_offset:]
        self._bridge_offset = len(lines)
        logical_calls = 0
        for line in fresh:
            record = json.loads(line)
            if record["event_type"] == "TOOL_CALL":
                logical_calls += 1
            tools.telemetry.record(
                record["event_type"], phase=int(record["phase"]), **record["payload"]
            )
        return logical_calls

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
        self._state_file.write(json.dumps({
            "timestamp_ns": time.time_ns(), "phase": phase, "boundary": boundary,
            "arm": self.arm, "taskview_state": state,
        }, sort_keys=True) + "\n")
        self._state_file.flush()

    def _participant_prompt(self, phase: int, prompt: str) -> str:
        contract = (
            "Use only tools from the taskview-orientation MCP server. Do not use Cursor "
            "file, search, shell, web, or other MCP tools. Return only one JSON object, "
            "without Markdown fences, conforming exactly to this schema: "
            + json.dumps(answer_schema(phase), sort_keys=True)
        )
        if self._first_turn:
            return self.system_prompt + "\n\n" + contract + "\n\n" + prompt
        return contract + "\n\n" + prompt

    def turn(
        self, *, phase: int, prompt: str, answer_fields: list[str], tools: EpisodeTools,
    ) -> ParticipantTurn:
        del answer_fields
        if phase == 4:
            self._record_state("immediately_after_phase4_source_mutation", phase, tools)
        self._bind_turn_paths(tools, phase)
        participant_prompt = self._participant_prompt(phase, prompt)
        command = isolated_cursor_prefix(self.workspace) + [
            "cursor-agent", "-p", "--output-format", "stream-json", "--model", MODEL,
            "--mode", "ask", "--trust", "--approve-mcps", "--resume", self.session_id,
            participant_prompt,
        ]
        try:
            result = subprocess.run(
                command, cwd=self.workspace, text=True, capture_output=True,
                check=False, timeout=TURN_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError(f"participant phase {phase} exceeded timeout") from exc
        self._record_raw(phase, command, result)
        events = stream_events(result.stdout, result.stderr)
        init = next((event for event in events
                     if event.get("type") == "system" and event.get("subtype") == "init"), None)
        terminal = next((event for event in reversed(events)
                         if event.get("type") == "result"), None)
        if result.returncode != 0 or terminal is None or terminal.get("is_error"):
            raise CursorRuntimeError(
                f"Cursor participant failed in phase {phase}: "
                f"returncode={result.returncode}, result={terminal}"
            )
        if init is None or init.get("model") != MODEL_DISPLAY_NAME:
            raise CursorRuntimeError(f"Cursor model binding mismatch: {init}")
        if init.get("session_id") != self.session_id or terminal.get("session_id") != self.session_id:
            raise CursorRuntimeError("Cursor session changed within the episode")

        mcp_started = 0
        forbidden: list[str] = []
        for event in events:
            if event.get("type") != "tool_call" or event.get("subtype") != "started":
                continue
            call = event.get("tool_call", {})
            if "getMcpToolsToolCall" in call:
                discovery = call["getMcpToolsToolCall"].get("args", {})
                if (
                    discovery.get("server") != MCP_SERVER_NAME
                    or (
                        discovery.get("toolName") is not None
                        and discovery.get("toolName") not in self.allowed_tool_names
                    )
                ):
                    forbidden.append(
                        f"mcp-discovery:{discovery.get('server')}:"
                        f"{discovery.get('toolName')}"
                    )
                continue
            if "mcpToolCall" not in call:
                forbidden.append(next(iter(call), "unknownCursorTool"))
                continue
            server, name = mcp_identity(event)
            serialized = json.dumps(call.get("mcpToolCall", {}), sort_keys=True)
            if server not in {None, MCP_SERVER_NAME} and MCP_SERVER_NAME not in serialized:
                forbidden.append(f"mcp:{server}:{name}")
            elif name is not None and name not in self.allowed_tool_names:
                forbidden.append(f"mcp:{server}:{name}")
            mcp_started += 1
        logical_calls = self._merge_bridge_telemetry(tools)
        validation_rejections = provider_validation_rejections(events)
        for rejection in validation_rejections:
            tools.telemetry.record(
                "TOOL_CALL",
                phase=phase,
                tool_name=rejection["tool_name"],
                tool_arguments=rejection["tool_arguments"],
                provider_validation_rejected=True,
                provider_call_id=rejection["call_id"],
            )
            tools.telemetry.record(
                "TOOL_ERROR",
                phase=phase,
                tool_name=rejection["tool_name"],
                tool_arguments=rejection["tool_arguments"],
                provider_validation_rejected=True,
                provider_call_id=rejection["call_id"],
                model_visible_output_bytes=visible_bytes(rejection["provider_result"]),
            )
        logical_calls += len(validation_rejections)
        if forbidden:
            raise CursorRuntimeError(f"participant used forbidden Cursor tools: {forbidden}")
        if logical_calls != mcp_started:
            raise CursorRuntimeError(
                f"MCP/logical tool accounting mismatch: Cursor={mcp_started}, bridge={logical_calls}"
            )

        final_message = next(
            (event for event in reversed(events) if event.get("type") == "assistant"),
            None,
        )
        content = (
            final_message.get("message", {}).get("content", [])
            if isinstance(final_message, dict)
            else []
        )
        final_text = "".join(
            item.get("text", "")
            for item in content
            if isinstance(item, dict) and item.get("type") == "text"
        )
        if not isinstance(final_text, str):
            raise CursorRuntimeError("Cursor turn completed without a final text result")
        try:
            answer = json.loads(_strip_json_fence(final_text))
        except json.JSONDecodeError as exc:
            raise CursorRuntimeError(f"final answer is not JSON: {final_text!r}") from exc
        if visible_bytes(answer) > MAX_STRUCTURED_ANSWER_TOKENS * 4:
            raise CursorRuntimeError("structured answer exceeded the frozen approximate token budget")
        if phase == 3:
            self._record_state("immediately_before_phase4_source_mutation", phase, tools)
        self._first_turn = False
        usage = terminal.get("usage") if isinstance(terminal.get("usage"), dict) else {}
        return ParticipantTurn(
            answer=answer, session_id=self.session_id,
            provider_input_tokens=usage.get("inputTokens"),
            provider_output_tokens=usage.get("outputTokens"),
        )

    def close(self) -> None:
        self._state_file.close()
        self._raw.close()


class CursorSessionFactory:
    """Episode-scoped factory retaining exactly one Cursor participant session."""

    def __init__(self, output_root: Path, *, condition: str | None = None) -> None:
        self.output_root = output_root
        self.condition = condition
        self.session: CursorParticipantSession | None = None

    def __call__(
        self, system: str, schemas: list[dict[str, Any]], arm: str
    ) -> CursorParticipantSession:
        if self.session is not None:
            raise RuntimeError("episode factory may create exactly one participant session")
        self.session = CursorParticipantSession(
            system, schemas, arm,
            raw_path=self.output_root / "provider_trajectory.jsonl",
            state_path=self.output_root / "runtime_state.jsonl",
            workspace=self.output_root / "provider_workspace",
            condition=self.condition,
        )
        return self.session

    def close(self) -> None:
        if self.session is not None:
            self.session.close()


DefaultSessionFactory = CursorSessionFactory


def runtime_binding() -> dict[str, Any]:
    from research.taskview_orientation.fixture import FROZEN_ROOT

    schemas = json.loads((FROZEN_ROOT / "tool_schemas.json").read_text(encoding="utf-8"))
    return {
        "adapter": ADAPTER_VERSION,
        "provider": MODEL_PROVIDER,
        "model": MODEL,
        "model_display_name": MODEL_DISPLAY_NAME,
        "exact_model_version_identifier": MODEL,
        "immutable_backend_revision_exposed": False,
        "cursor_agent_version": CURSOR_AGENT_VERSION,
        "reasoning_effort": REASONING_EFFORT,
        "service_tier": SERVICE_TIER,
        "sampling": {
            "temperature": "not exposed by cursor-agent CLI",
            "top_p": "not exposed by cursor-agent CLI",
            "seed": "not supported by cursor-agent CLI",
        },
        "budgets": {
            "turn_timeout_seconds": TURN_TIMEOUT_SECONDS,
            "structured_answer_max_tokens": MAX_STRUCTURED_ANSWER_TOKENS,
            "hard_provider_reasoning_budget": "not exposed",
            "hard_provider_output_budget": (
                "not exposed; exact JSON contract and harness byte ceiling applied"
            ),
        },
        "tool_policy": (
            "only frozen taskview-orientation MCP tools; any Cursor built-in or unrelated "
            "MCP call invalidates the episode"
        ),
        "context_policy": (
            "one Cursor chat ID resumed across five turns; no injected summaries or retries"
        ),
        "context_limit_tokens": MODEL_CONTEXT_WINDOW,
        "context_limit_source": "not exposed by cursor-agent CLI",
        "timeout_policy": "300 seconds per turn; no retry or restart after timeout",
        "provider_tool_serialization_sha256": {
            "RAW": sha256_json(provider_tools(schemas["native"])),
            "TASKVIEW": sha256_json(provider_tools(schemas["native"] + schemas["taskview"])),
            "schema_map": sha256_json(PROVIDER_TOOL_SCHEMAS),
        },
    }
