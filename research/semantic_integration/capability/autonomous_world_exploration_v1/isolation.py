"""Isolation for autonomous exploration probe."""

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
from research.semantic_integration.capability.autonomous_world_exploration_v1.paths import (
    EVALUATOR_ONLY,
    LIVE_ROOT,
    REPO,
    ROOT,
)


def hidden_paths() -> list[Path]:
    extra = [
        Path("/tmp/world-experiment") / "e2e-semantic-compilation-v1",
        Path("/tmp/world-experiment") / "world-read-programming-v1",
        Path("/tmp/world-experiment") / "npdes-purpose-first-python-spine-v1",
        Path("/tmp/world-experiment") / "npdes-obligation-targeted-resolution-v1",
        Path("/tmp/world-experiment") / "npdes-semantic-refinement-admission-v1",
        Path("/tmp/world-experiment") / "npdes-semantic-proposal-scope-v1",
        Path("/tmp/world-experiment") / "diligence-constructor-v3-1-1",
    ]
    paths = [REPO, LIVE_ROOT, *extra, *cursor_project_dirs()]
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
        EVALUATOR_ONLY / "gold.json",
        EVALUATOR_ONLY / "discovery_targets.json",
        EVALUATOR_ONLY / "downstream_tasks.json",
        EVALUATOR_ONLY / "freeze.json",
        ROOT / "score.py",
        ROOT.parent / "end_to_end_v1" / "evaluator_only" / "competency_questions.json",
        ROOT.parent / "world_read_programming_v1" / "evaluator_only" / "gold.json",
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
    merged = isolated_env(env)
    merged["PYTHONPATH"] = str(workspace)
    return subprocess.run(
        bwrap_command(workspace, argv),
        cwd=workspace,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
        env=merged,
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
    "evaluator_only",
    "gold.json",
    "discovery_targets.json",
    "downstream_tasks.json",
    "grain_wrong",
    "competency_questions.json",
)


def isolation_leaks_from_events(events: list) -> list[str]:
    blob = json.dumps(events)[:200000].lower()
    return [marker for marker in LEAK_MARKERS if marker.lower() in blob]
