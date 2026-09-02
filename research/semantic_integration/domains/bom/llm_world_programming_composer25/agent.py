"""cursor-agent invocation inside Composer 2.5 campaign isolation."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from research.semantic_integration.domains.bom.llm_world_programming.agent import (
    TIMEOUT_SECONDS,
    stream_events,
    tool_metrics,
)
from research.semantic_integration.domains.bom.llm_world_programming_composer25.isolation import (
    run_isolated,
)
from research.semantic_integration.domains.bom.llm_world_programming_v2.agent import (
    refuse_expensive_model,
    refuse_non_cursor_model,
)

ADAPTER = "cursor-agent-bwrap-isolated-workspace-agent-composer25"
MODEL = "composer-2.5"
MODEL_FAST_FORBIDDEN = "composer-2.5-fast"


def usage_from_events(events: list[dict[str, Any]]) -> dict[str, Any]:
    terminal = next(
        (event for event in reversed(events) if event.get("type") == "result"),
        {},
    )
    usage = terminal.get("usage") if isinstance(terminal.get("usage"), dict) else {}
    cost_keys = {
        key: value
        for key, value in usage.items()
        if "cost" in key.lower() or "usd" in key.lower() or "price" in key.lower()
    }
    input_tokens = usage.get("inputTokens", usage.get("input_tokens"))
    output_tokens = usage.get("outputTokens", usage.get("output_tokens"))
    total = None
    if isinstance(input_tokens, int) and isinstance(output_tokens, int):
        total = input_tokens + output_tokens
    model = next(
        (
            event.get("model")
            for event in events
            if event.get("type") == "system" and event.get("subtype") == "init"
        ),
        None,
    )
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total,
        "cache_read_tokens": usage.get("cacheReadTokens", usage.get("cache_read_tokens")),
        "cache_write_tokens": usage.get(
            "cacheWriteTokens", usage.get("cache_write_tokens")
        ),
        "duration_ms": terminal.get("duration_ms"),
        "duration_api_ms": terminal.get("duration_api_ms"),
        "is_error": bool(terminal.get("is_error")),
        "model": model,
        "provider_usage": usage,
        "monetary_cost_keys": cost_keys,
        "monetary_cost_exposed": bool(cost_keys),
    }


def refuse_fast_model(model: str) -> None:
    if model.lower() == MODEL_FAST_FORBIDDEN or "fast" in model.lower():
        raise RuntimeError(
            f"refusing model {model!r}; this campaign is frozen on {MODEL}"
        )


def run_agent(*, workspace: Path, prompt: str, model: str) -> dict[str, Any]:
    refuse_non_cursor_model(model, action="run")
    refuse_expensive_model(model, action="run")
    refuse_fast_model(model)
    if model != MODEL:
        raise RuntimeError(f"refusing model {model!r}; frozen campaign uses {MODEL}")
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
