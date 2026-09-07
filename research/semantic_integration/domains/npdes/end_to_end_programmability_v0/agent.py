"""Isolated composer-2.5 invocation."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from research.semantic_integration.domains.bom.llm_world_programming.agent import (
    stream_events,
    tool_metrics,
    usage_from_events,
)
from research.semantic_integration.domains.bom.llm_world_programming_v2.agent import (
    refuse_expensive_model,
    refuse_non_cursor_model,
    reported_model_is_composer,
)
from research.semantic_integration.domains.npdes.end_to_end_programmability_v0.isolation import run_isolated
from research.semantic_integration.domains.npdes.end_to_end_programmability_v0.paths import ADAPTER, MODEL
from research.semantic_integration.domains.npdes.purpose_first_python_spine_v1.agent import (
    exploration_from_events,
)


def _as_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def assistant_text(events: list) -> str:
    chunks: list[str] = []
    for event in events:
        if event.get("type") == "assistant":
            message = event.get("message") or event.get("text") or ""
            if isinstance(message, dict):
                content = message.get("content") or []
                if isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict) and part.get("text"):
                            chunks.append(str(part["text"]))
                        elif isinstance(part, str):
                            chunks.append(part)
                elif isinstance(content, str):
                    chunks.append(content)
            elif isinstance(message, str):
                chunks.append(message)
        if event.get("type") == "result" and event.get("result"):
            result = event.get("result")
            if isinstance(result, str):
                chunks.append(result)
    return "\n\n".join(c.strip() for c in chunks if str(c).strip())[-200000:]


def run_probe_agent(*, workspace: Path, prompt: str, timeout_seconds: int) -> dict[str, Any]:
    refuse_non_cursor_model(MODEL, action="run")
    refuse_expensive_model(MODEL, action="run")
    if MODEL != "composer-2.5" or "fast" in MODEL:
        raise RuntimeError("refusing composer-2.5-fast")
    command = [
        "cursor-agent", "--print", "--output-format", "stream-json",
        "--force", "--trust", "--sandbox", "disabled",
        "--workspace", str(workspace), "--model", MODEL, prompt,
    ]
    try:
        completed = run_isolated(workspace, command, timeout=timeout_seconds)
        timed_out = False
        returncode = completed.returncode
        stdout, stderr = _as_text(completed.stdout), _as_text(completed.stderr)
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        returncode = -1
        stdout, stderr = _as_text(exc.stdout), _as_text(exc.stderr) + "\nTIMEOUT"
    events = stream_events(stdout or "", stderr or "")
    usage = usage_from_events(events)
    reported = usage.get("model")
    if events and not reported_model_is_composer(reported if isinstance(reported, str) else None):
        raise RuntimeError(f"refusing non-Cursor reported model {reported!r}")
    return {
        "command": command,
        "returncode": returncode,
        "timed_out": timed_out,
        "stdout": stdout,
        "stderr": stderr,
        "events": events,
        "usage": usage,
        "tools": tool_metrics(events),
        "exploration": exploration_from_events(events),
        "assistant_text": assistant_text(events),
        "adapter": ADAPTER,
        "model": MODEL,
        "reported_model": reported,
        "timeout_seconds": timeout_seconds,
    }
