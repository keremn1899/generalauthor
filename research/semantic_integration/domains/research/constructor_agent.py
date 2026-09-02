"""Isolated composer-2.5 constructor invocation."""

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
from research.semantic_integration.domains.research.isolation import run_isolated

ADAPTER = "cursor-agent-bwrap-isolated-constructor-research-v1"
MODEL = "composer-2.5"
TIMEOUT_SECONDS = 2400


def run_constructor(*, workspace: Path, prompt: str) -> dict[str, Any]:
    refuse_non_cursor_model(MODEL, action="run")
    refuse_expensive_model(MODEL, action="run")
    if MODEL != "composer-2.5" or "fast" in MODEL:
        raise RuntimeError("refusing composer-2.5-fast")
    command = [
        "cursor-agent",
        "--print",
        "--output-format",
        "stream-json",
        "--force",
        "--trust",
        "--sandbox",
        "disabled",
        "--workspace",
        str(workspace),
        "--model",
        MODEL,
        prompt,
    ]
    try:
        completed = run_isolated(workspace, command, timeout=TIMEOUT_SECONDS)
        timed_out = False
        returncode = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        returncode = -1
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + "\nTIMEOUT"
    events = stream_events(stdout or "", stderr or "")
    usage = usage_from_events(events)
    reported = usage.get("model")
    if events and not reported_model_is_composer(reported if isinstance(reported, str) else None):
        raise RuntimeError(
            f"refusing non-Cursor reported model {reported!r}; required Composer 2.5"
        )
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
        "timeout_seconds": TIMEOUT_SECONDS,
    }
