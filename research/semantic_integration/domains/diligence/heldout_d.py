"""Held-out purpose D after A/B/C World freeze. Do not change existing relation meanings."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from research.semantic_integration.domains.diligence.constructor_agent import run_constructor
from research.semantic_integration.domains.diligence.isolation import (
    REPO,
    new_live_workspace,
    preflight_isolation,
    remove_live_workspace,
)
from research.semantic_integration.domains.diligence.workspaces import ROOT

ABC = ROOT / "constructor_run" / "abc" / "workspace"
D_OUT = ROOT / "constructor_run" / "d"
HIDDEN_D = ROOT / "hidden" / "purpose_d.md"

D_TASK = """Held-out purpose D is now revealed. The compiled World from purposes A/B/C is in world/world.sqlite.

Do not modify existing relation meanings. Do not retract or rewrite identity_judgment or contract_clause tuples except by adding genuinely new tuples if required.

You may add new relations only if D cannot be computed from existing World state plus ordinary Python/SQL.

Read purposes/visible_d.md. Write purpose_ir/d/output.json in that schema.

Prefer reuse: open invoices, active contracts, assignment notice/consent clauses, and identity links already in World.

Do not read hidden expected outputs. Do not read files outside this workspace.
"""


def isolation_leaks_from_events(events: list) -> list[str]:
    leaks = []
    repo = str(REPO)
    for event in events:
        if event.get("type") != "tool_call" or event.get("subtype") != "completed":
            continue
        call = event.get("tool_call") or {}
        kind = next(iter(call), "")
        if kind != "readToolCall":
            continue
        payload = call.get(kind) or {}
        args = payload.get("args") or {}
        result = payload.get("result") or {}
        path = str(args.get("path") or "")
        if path.startswith(repo) and isinstance(result, dict) and "success" in result:
            leaks.append(path)
    return leaks


def build_d_workspace(destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(ABC, destination)
    purposes = destination / "purposes"
    purposes.mkdir(exist_ok=True)
    text = HIDDEN_D.read_text(encoding="utf-8")
    # Strip designer instruction that names the hidden directory.
    visible = "\n".join(
        line
        for line in text.splitlines()
        if "constructor workspace" not in line.lower()
        and "held out from the constructor" not in line.lower()
    )
    (purposes / "visible_d.md").write_text(visible.strip() + "\n", encoding="utf-8")
    (destination / "purpose_ir" / "d").mkdir(parents=True, exist_ok=True)
    (destination / "D_TASK.md").write_text(D_TASK, encoding="utf-8")
    # Remove any accidental expected files
    for path in destination.rglob("purpose_d.json"):
        path.unlink()


def run_d() -> dict:
    if not (ABC / "world" / "world.sqlite").exists():
        raise RuntimeError("A/B/C world is not frozen")
    live = new_live_workspace()
    D_OUT.mkdir(parents=True, exist_ok=True)
    try:
        build_d_workspace(live)
        preflight = preflight_isolation(live)
        agent = run_constructor(
            workspace=live,
            prompt=D_TASK,
        )
        leaks = isolation_leaks_from_events(agent.get("events") or [])
        (D_OUT / "transcript.stdout.txt").write_text(agent["stdout"] or "", encoding="utf-8")
        (D_OUT / "transcript.stderr.txt").write_text(agent["stderr"] or "", encoding="utf-8")
        (D_OUT / "agent.json").write_text(
            json.dumps(
                {
                    "returncode": agent["returncode"],
                    "timed_out": agent["timed_out"],
                    "tools": agent["tools"],
                    "model": agent["model"],
                    "reported_model": agent.get("reported_model"),
                    "isolation_leaks": leaks,
                    "isolation_preflight": preflight,
                    "abc_world_fingerprint_at_reveal": "sha256:b7ca189ec402e2d178925fccca8255a66a22acc213dbaabaaf2e3f2fb8a8a45b",
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        saved = D_OUT / "workspace"
        if saved.exists():
            shutil.rmtree(saved)
        shutil.copytree(live, saved)
    finally:
        remove_live_workspace(live)
    if leaks:
        raise RuntimeError(f"isolation failed on D: {leaks}")
    return {"isolation_leaks": leaks}


if __name__ == "__main__":
    print(json.dumps(run_d(), indent=2))
