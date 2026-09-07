"""Isolation. Hides the repo, GOLD, prior probe scores, and this probe's expected distinctions."""

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
    PROSE_V1,
    PROSE_V11,
    SPINE_V1,
    V311,
)
from research.semantic_integration.domains.npdes.semantic_refinement_admission_v1.paths import (
    ANATOMY,
    CONVERSATIONAL,
    EVALUATOR_GOLD,
    EVALUATOR_ONLY,
    LIVE_ROOT,
    NPDES,
    OTR,
    PFPS,
    PROPOSAL,
    REPO,
)


def hidden_paths() -> list[Path]:
    paths = [
        REPO,
        LIVE_ROOT,
        Path("/tmp/world-experiment") / "npdes-obligation-targeted-resolution-v1",
        Path("/tmp/world-experiment") / "npdes-purpose-first-python-spine-v1",
        Path("/tmp/world-experiment") / "npdes-semantic-spine-anatomy-v1",
        Path("/tmp/world-experiment") / "npdes-spine-compiler-probe-v1",
        Path("/tmp/world-experiment") / "npdes-prose-probe-v1",
        Path("/tmp/world-experiment") / "npdes-prose-probe-v1-1",
        Path("/tmp/world-experiment") / "npdes-constructor-v3-1-1-untouched",
        Path("/tmp/world-experiment") / "npdes-conversational-semantic-review-v1",
        Path("/tmp/world-experiment") / "npdes-semantic-proposal-scope-v1",
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
        EVALUATOR_GOLD / "gold_m.json",
        EVALUATOR_GOLD / "gold_s.json",
        EVALUATOR_GOLD / "gold_e.json",
        EVALUATOR_GOLD / "purpose_d.md",
        PFPS / "score.py",
        PFPS / "frozen" / "triggerability.json",
        ANATOMY / "reports" / "semantic_spine_anatomy_v1.md",
        CONVERSATIONAL / "evaluator_only" / "packets.json",
        PROPOSAL / "evaluator_only" / "intents.json",
        OTR / "evaluator_only" / "establishability.json",
        OTR / "reports" / "obligation_targeted_resolution_v1.md",
        OTR / "runs" / "score.json",
        EVALUATOR_ONLY / "expected.json",
        SPINE_V1 / "frozen" / "triggerability.json",
        PROSE_V1 / "frozen" / "semantic_cards.json",
        V311 / "reports" / "constructor_report.md",
        NPDES.parent / "diligence" / "hidden" / "expected" / "purpose_a.json",
        PROSE_V11 / "reports" / "attention_funnel_summary.md",
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
    "establishability.json",
    "expected.json",
    "obligation_targeted_resolution_v1.md",
    "evaluator_only",
    "semantic_cards.json",
    "oracle_obligations.json",
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
