"""Composer 2.5 isolated invocation for Probe A. Does not use constructor v2 isolation roots."""

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
from research.semantic_integration.domains.diligence.semantic_proof_benchmark_v1.isolation import (
    run_isolated,
)

ADAPTER = "cursor-agent-bwrap-isolated-semantic-proof-v1"
MODEL = "composer-2.5"


def _as_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def isolation_leaks(events: list, repo: Path) -> list[str]:
    leaks = []
    repo_s = str(repo)
    for event in events:
        if event.get("type") != "tool_call" or event.get("subtype") != "completed":
            continue
        call = event.get("tool_call") or {}
        kind = next(iter(call), "")
        if kind != "readToolCall":
            continue
        payload = call.get(kind) or {}
        path = str((payload.get("args") or {}).get("path") or "")
        result = payload.get("result") or {}
        if path.startswith(repo_s) and isinstance(result, dict) and "success" in result:
            leaks.append(path)
    return leaks


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
        "adapter": ADAPTER,
        "model": MODEL,
        "reported_model": reported,
        "timeout_seconds": timeout_seconds,
    }
