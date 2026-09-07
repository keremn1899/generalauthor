"""Isolation for the NPDES prose probe. Hides repo, gold, frozen cards, and constructor trials."""

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
from research.semantic_integration.domains.npdes.prose_probe_v1.paths import (
    EVALUATOR,
    EXPERIMENT_ID,
    LIVE_ROOT,
    NPDES,
    REPO,
    ROOT,
    V311,
)


def hidden_paths() -> list[Path]:
    paths = [
        REPO,
        LIVE_ROOT,
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
        ROOT / "frozen" / "semantic_cards.json",
        ROOT / "frozen" / "evidence_sufficiency.json",
        ROOT / "frozen" / "oracle_obligations.json",
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
