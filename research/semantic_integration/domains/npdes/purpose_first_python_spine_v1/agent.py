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
from research.semantic_integration.domains.npdes.purpose_first_python_spine_v1.isolation import run_isolated
from research.semantic_integration.domains.npdes.purpose_first_python_spine_v1.paths import ADAPTER, MODEL


def _as_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def exploration_from_events(events: list) -> dict[str, Any]:
    reads: list[str] = []
    shells: list[str] = []
    writes: list[str] = []
    for event in events:
        if event.get("type") != "tool_call" or event.get("subtype") != "started":
            continue
        call = event.get("tool_call") or {}
        kind = next(iter(call), "")
        payload = call.get(kind) or {}
        args = payload.get("args") if isinstance(payload, dict) else {}
        if not isinstance(args, dict):
            args = {}
        path = str(args.get("path") or args.get("file") or args.get("target_directory") or "")
        command = str(args.get("command") or args.get("cmd") or "")
        name = kind.lower()
        if "read" in name and path:
            reads.append(path)
        if "write" in name and path:
            writes.append(path)
        if command:
            shells.append(command[:500])
    def uniq(items: list[str]) -> list[str]:
        out, seen = [], set()
        for item in items:
            if item not in seen:
                seen.add(item)
                out.append(item)
        return out
    return {
        "reads": uniq(reads)[:80],
        "writes": uniq(writes)[:40],
        "shells": uniq(shells)[:40],
        "n_reads": len(reads),
        "n_writes": len(writes),
        "n_shells": len(shells),
    }


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
        "adapter": ADAPTER,
        "model": MODEL,
        "reported_model": reported,
        "timeout_seconds": timeout_seconds,
    }
