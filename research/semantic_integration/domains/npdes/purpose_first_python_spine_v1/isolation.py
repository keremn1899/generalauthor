"""Isolation for Purpose-First Python Spine Probe v1."""

from __future__ import annotations

import json
import os
import secrets
import shutil
import subprocess
from pathlib import Path
from typing import Any

from research.semantic_integration.domains.bom.llm_world_programming_v2.isolation import (
    PREFLIGHT_SOURCE,
    cursor_project_dirs,
    host_python,
    isolated_env,
)
from research.semantic_integration.domains.npdes.purpose_first_python_spine_v1.paths import (
    EVALUATOR,
    FROZEN,
    LIVE_ROOT,
    NPDES,
    PROSE_V1,
    PROSE_V11,
    REPO,
    ROOT,
    SPINE_V1,
    V311,
)


def hidden_paths() -> list[Path]:
    paths = [
        REPO,
        LIVE_ROOT,
        Path("/tmp/world-experiment") / "npdes-spine-compiler-probe-v1",
        Path("/tmp/world-experiment") / "npdes-prose-probe-v1",
        Path("/tmp/world-experiment") / "npdes-prose-probe-v1-1",
        Path("/tmp/world-experiment") / "npdes-constructor-v3-1-1-untouched",
        Path("/tmp/world-experiment") / "diligence-constructor-v3-1",
        Path("/tmp/world-experiment") / "diligence-constructor-v3",
        *cursor_project_dirs(),
    ]
    out: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        key = str(path)
        if key not in seen:
            seen.add(key)
            out.append(path)
    return out


def canary_paths() -> list[Path]:
    return [
        REPO / "CLAUDE.md",
        EVALUATOR / "gold_m.json",
        EVALUATOR / "gold_s.json",
        EVALUATOR / "gold_e.json",
        EVALUATOR / "purpose_d.md",
        EVALUATOR / "permit_text" / "farmington" / "final_permit.txt",
        FROZEN / "triggerability.json",
        SPINE_V1 / "frozen" / "triggerability.json",
        SPINE_V1 / "reports" / "spine_compiler_probe_v1.md",
        SPINE_V1 / "score.py",
        ROOT / "score.py",
        PROSE_V1 / "frozen" / "semantic_cards.json",
        PROSE_V1 / "frozen" / "oracle_obligations.json",
        PROSE_V11 / "reports" / "attention_funnel_summary.md",
        V311 / "reports" / "constructor_report.md",
        NPDES.parent / "diligence" / "hidden" / "expected" / "purpose_a.json",
    ]


def new_live_workspace() -> Path:
    LIVE_ROOT.mkdir(parents=True, exist_ok=True)
    destination = LIVE_ROOT / secrets.token_hex(16)
    destination.mkdir(parents=True)
    return destination


def bwrap_command(workspace: Path, argv: list[str]) -> list[str]:
    command = [
        "bwrap",
        "--die-with-parent",
        "--bind", "/", "/",
        "--dev-bind", "/dev", "/dev",
        "--proc", "/proc",
    ]
    for path in hidden_paths():
        command.extend(["--tmpfs", str(path)])
    command.extend(["--bind", str(workspace), str(workspace), "--chdir", str(workspace), "--", *argv])
    return command


def run_isolated(workspace: Path, argv: list[str], *, timeout: int | None, env: dict[str, str] | None = None):
    return subprocess.run(
        bwrap_command(workspace, argv),
        cwd=workspace,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
        env=isolated_env(env),
    )


def preflight_isolation(workspace: Path) -> dict[str, Any]:
    sibling = LIVE_ROOT / "sibling-canary" / "secret.json"
    sibling.parent.mkdir(parents=True, exist_ok=True)
    if not sibling.exists():
        sibling.write_text('{"leak": true}\n', encoding="utf-8")
    env = os.environ.copy()
    env["ISOLATION_WORKSPACE"] = str(workspace)
    env["ISOLATION_REPO"] = str(REPO)
    env["ISOLATION_CANARIES"] = json.dumps([str(path) for path in canary_paths()])
    env["ISOLATION_SIBLING"] = str(sibling)
    completed = run_isolated(workspace, [host_python(), "-c", PREFLIGHT_SOURCE], timeout=30, env=env)
    try:
        payload = json.loads(completed.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError, ValueError):
        payload = {"ok": False, "failures": [completed.stdout[-1000:], completed.stderr[-1000:]]}
    if completed.returncode != 0 or not payload.get("ok"):
        raise RuntimeError(f"isolation preflight failed: {payload}")
    return payload


def remove_live_workspace(workspace: Path) -> None:
    if workspace.exists() and LIVE_ROOT in workspace.parents:
        shutil.rmtree(workspace)


LEAK_MARKERS = (
    "gold_s.json",
    "gold_m.json",
    "gold_e.json",
    "purpose_d.md",
    "triggerability.json",
    "semantic_cards.json",
    "oracle_obligations.json",
    "constructor_report.md",
    "spine_compiler_probe_v1",
    "permit_text",
    "evaluator_only",
)


def isolation_leaks_from_events(events: list) -> list[str]:
    leaks: list[str] = []
    repo = str(REPO)
    for event in events:
        if event.get("type") != "tool_call" or event.get("subtype") != "completed":
            continue
        call = event.get("tool_call") or {}
        kind = next(iter(call), "")
        payload = call.get(kind) or {}
        args = payload.get("args") or {}
        result = payload.get("result") or {}
        path = str(args.get("path") or args.get("target_directory") or "")
        if path.startswith(repo) and isinstance(result, dict) and "success" in result:
            leaks.append(path)
        lowered = path.lower()
        if any(marker in lowered for marker in LEAK_MARKERS):
            leaks.append(path)
    return leaks
