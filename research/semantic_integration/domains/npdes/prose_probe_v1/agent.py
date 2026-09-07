"""Isolated composer-2.5 invocation for the NPDES prose probe."""

from __future__ import annotations

import json
import re
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
from research.semantic_integration.domains.npdes.prose_probe_v1.isolation import run_isolated
from research.semantic_integration.domains.npdes.prose_probe_v1.paths import ADAPTER, MODEL


def _as_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


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


def load_result_json(workspace: Path) -> dict[str, Any] | list | None:
    path = workspace / "result.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    dispositions = workspace / "05_dispositions.json"
    if dispositions.exists():
        try:
            return json.loads(dispositions.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return None


_JSON_FENCE = re.compile(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", re.S)


def parse_json_from_stdout(stdout: str) -> dict[str, Any] | list | None:
    for match in _JSON_FENCE.finditer(stdout or ""):
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
    return None
