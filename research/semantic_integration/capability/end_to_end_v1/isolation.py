"""Isolation: hide repo, GOLD, evaluator_only, prior experiments."""

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
from research.semantic_integration.capability.end_to_end_v1.paths import (
    EVALUATOR_ONLY,
    LIVE_ROOT,
    REPO,
    ROOT,
)


def hidden_paths() -> list[Path]:
    extra = [
        Path("/tmp/world-experiment") / "npdes-purpose-first-python-spine-v1",
        Path("/tmp/world-experiment") / "npdes-obligation-targeted-resolution-v1",
        Path("/tmp/world-experiment") / "npdes-semantic-refinement-admission-v1",
        Path("/tmp/world-experiment") / "npdes-semantic-proposal-scope-v1",
        Path("/tmp/world-experiment") / "diligence-constructor-v3-1-1",
    ]
    # EVALUATOR_ONLY lives under REPO; a nested --tmpfs can punch through the repo hide.
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
        EVALUATOR_ONLY / "competency_questions.json",
        EVALUATOR_ONLY / "establishability.json",
        EVALUATOR_ONLY / "domain_selection.md",
        ROOT / "score.py",
        ROOT / "reports" / "end_to_end_semantic_compilation_v1.md",
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
    "competency_questions.json",
    "establishability.json",
    "evaluator_only",
    "gold_s.json",
    "gold_m.json",
    "gold_e.json",
    "domain_selection.md",
    "END_TO_END_SEMANTIC_COMPILATION",
)


def isolation_leaks_from_events(events: list) -> list[str]:
    blob = json.dumps(events)[:200000].lower()
    return [marker for marker in LEAK_MARKERS if marker.lower() in blob]
