"""Physical isolation for Probe A inference. Hides repo and hidden oracles."""

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

EXPERIMENT_ID = "diligence-semantic-proof-benchmark-v1"
LIVE_ROOT = Path("/tmp/world-experiment") / EXPERIMENT_ID

from research.semantic_integration.domains.diligence.semantic_proof_benchmark_v1.paths import (
    DILIGENCE,
    HIDDEN,
    REPO,
    ROOT,
    V2,
)


def hidden_paths() -> list[Path]:
    paths = [
        REPO,
        LIVE_ROOT,
        Path("/tmp/world-experiment") / "diligence-constructor-v2-repair",
        Path("/tmp/world-experiment") / "diligence-purpose-driven-construction-v1",
        Path("/tmp/world-experiment") / "diligence-pass-localization-v1",
        *cursor_project_dirs(),
    ]
    unique: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        key = str(path)
        if key not in seen:
            seen.add(key)
            unique.append(path)
    return unique


def canary_paths() -> list[Path]:
    return [
        REPO / "CLAUDE.md",
        HIDDEN / "expected" / "purpose_a.json",
        HIDDEN / "expected" / "purpose_b.json",
        HIDDEN / "expected" / "purpose_c.json",
        HIDDEN / "expected" / "purpose_d.json",
        HIDDEN / "annotations" / "identity_dispositions.json",
        HIDDEN / "designer_notes.md",
        DILIGENCE / "pass_localization" / "reports" / "pass_localization.md",
        DILIGENCE / "reports" / "constructor_v2_repair.md",
        V2 / "reports" / "constructor_v2_repair.md",
        ROOT / "scoring" / "judgments.json",
        ROOT / "reports" / "semantic_proof_benchmark.md",
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
