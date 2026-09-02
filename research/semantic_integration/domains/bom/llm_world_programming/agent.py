"""Isolated cursor-agent invocation for one programming trial."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

MODEL = "gpt-5.6-sol-high"  # frozen v1 campaign only; do not use for new tests
ADAPTER = "cursor-agent-isolated-workspace-agent-v1"
TIMEOUT_SECONDS = 600


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


def usage_from_events(events: list[dict[str, Any]]) -> dict[str, Any]:
    terminal = next(
        (event for event in reversed(events) if event.get("type") == "result"),
        {},
    )
    usage = terminal.get("usage") if isinstance(terminal.get("usage"), dict) else {}
    input_tokens = usage.get("inputTokens", usage.get("input_tokens"))
    output_tokens = usage.get("outputTokens", usage.get("output_tokens"))
    total = None
    if isinstance(input_tokens, int) and isinstance(output_tokens, int):
        total = input_tokens + output_tokens
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total,
        "is_error": bool(terminal.get("is_error")),
        "model": next(
            (
                event.get("model")
                for event in events
                if event.get("type") == "system" and event.get("subtype") == "init"
            ),
            None,
        ),
    }


def tool_metrics(events: list[dict[str, Any]]) -> dict[str, Any]:
    started = [
        event
        for event in events
        if event.get("type") == "tool_call" and event.get("subtype") == "started"
    ]
    shell = 0
    reads = 0
    writes = 0
    python_execs = 0
    paths: list[str] = []
    for event in started:
        call = event.get("tool_call") or {}
        kind = next(iter(call), "unknown")
        payload = call.get(kind) or {}
        args = payload.get("args") if isinstance(payload, dict) else {}
        if not isinstance(args, dict):
            args = {}
        name = kind.lower()
        command = str(args.get("command") or args.get("cmd") or "")
        path = str(args.get("path") or args.get("file") or args.get("target") or "")
        if "shell" in name or command:
            shell += 1
        if "read" in name:
            reads += 1
        if "write" in name:
            writes += 1
        if "python" in command.lower() or command.strip().startswith("python"):
            python_execs += 1
        if path:
            paths.append(path)
        if command:
            for token in command.replace("=", " ").split():
                if "/" in token or token.endswith((".csv", ".json", ".md", ".py", ".sqlite")):
                    paths.append(token)
    return {
        "tool_calls_started": len(started),
        "shell_calls": shell,
        "read_calls": reads,
        "write_calls": writes,
        "python_executions_guess": python_execs,
        "mentioned_paths": paths,
    }


def run_agent(*, workspace: Path, prompt: str) -> dict[str, Any]:
    command = [
        "cursor-agent",
        "--print",
        "--output-format",
        "stream-json",
        "--force",
        "--trust",
        "--sandbox",
        "enabled",
        "--workspace",
        str(workspace),
        "--model",
        MODEL,
        prompt,
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=workspace,
            text=True,
            capture_output=True,
            check=False,
            timeout=TIMEOUT_SECONDS,
        )
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
        "model": MODEL,
        "timeout_seconds": TIMEOUT_SECONDS,
    }
