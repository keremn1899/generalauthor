"""cursor-agent invocation inside a bwrap that hides the repository."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

from research.semantic_integration.domains.bom.llm_world_programming.agent import (
    ADAPTER as V1_ADAPTER,
    TIMEOUT_SECONDS,
    stream_events,
    tool_metrics,
    usage_from_events,
)
from research.semantic_integration.domains.bom.llm_world_programming_v2.isolation import (
    run_isolated,
)

ADAPTER = "cursor-agent-bwrap-isolated-workspace-agent-v3"
# Default for new campaigns. Frozen v3 stays on gpt-5.6-sol-high until that run ends.
DEFAULT_MODEL = "composer-2.5"
CURSOR_NEW_WORK_SLUGS = frozenset({"composer-2.5"})
CURSOR_REPORTED_COMPOSER = frozenset({"composer 2.5", "composer-2.5"})
EXPENSIVE_MODEL_MARKERS = ("sol-high", "sol-medium", "sol-low", "gpt-5.6-sol")
NON_CURSOR_MODEL_MARKERS = (
    "gpt",
    "claude",
    "gemini",
    "sonnet",
    "opus",
    "anthropic",
    "openai",
    "sol-high",
    "sol-medium",
    "sol-low",
)


def model_is_expensive(model: str) -> bool:
    lowered = model.lower()
    return any(marker in lowered for marker in EXPENSIVE_MODEL_MARKERS)


def model_is_non_cursor(model: str) -> bool:
    lowered = model.lower().replace("_", "-")
    return any(marker in lowered for marker in NON_CURSOR_MODEL_MARKERS)


def reported_model_is_composer(model: str | None) -> bool:
    if not model:
        return False
    return model.lower().replace("_", "-") in CURSOR_REPORTED_COMPOSER


def refuse_expensive_model(model: str, *, action: str) -> None:
    if not model_is_expensive(model):
        return
    if os.environ.get("ALLOW_EXPENSIVE_MODEL") == "1":
        return
    raise RuntimeError(
        f"refusing to {action} with expensive model {model!r}. "
        "New programming tests use composer-2.5. Set ALLOW_EXPENSIVE_MODEL=1 "
        "only to finish a campaign already frozen on that model."
    )


def refuse_non_cursor_model(model: str, *, action: str) -> None:
    if os.environ.get("ALLOW_EXPENSIVE_MODEL") == "1" and model_is_expensive(model):
        return
    if not model_is_non_cursor(model) and model.lower() in CURSOR_NEW_WORK_SLUGS:
        return
    raise RuntimeError(
        f"refusing to {action} with non-Cursor model {model!r}. "
        "New inference uses composer-2.5 only."
    )


def run_agent(
    *,
    workspace: Path,
    prompt: str,
    model: str,
    allow_expensive: bool = False,
) -> dict[str, Any]:
    if not allow_expensive:
        refuse_non_cursor_model(model, action="run")
        refuse_expensive_model(model, action="run")
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
        model,
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
    return {
        "command": command,
        "bwrap_adapter": ADAPTER,
        "v1_adapter": V1_ADAPTER,
        "returncode": returncode,
        "timed_out": timed_out,
        "stdout": stdout,
        "stderr": stderr,
        "events": events,
        "usage": usage_from_events(events),
        "tools": tool_metrics(events),
        "adapter": ADAPTER,
        "model": model,
        "timeout_seconds": TIMEOUT_SECONDS,
    }
