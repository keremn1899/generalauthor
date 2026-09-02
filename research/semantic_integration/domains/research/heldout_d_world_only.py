"""D_WORLD_ONLY: frozen World plus purpose D. Sources absent. World must not mutate."""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from research.semantic_integration.domains.research.constructor_agent import run_constructor
from research.semantic_integration.domains.research.heldout_d import (
    isolation_leaks_from_events,
    visible_d_text,
)
from research.semantic_integration.domains.research.isolation import (
    REPO,
    new_live_workspace,
    preflight_isolation,
    remove_live_workspace,
)
from research.semantic_integration.domains.research.workspaces import KERNEL, ROOT, TASKVIEW_SRC

ABC = ROOT / "constructor_run" / "abc" / "workspace"
OUT = ROOT / "constructor_run" / "d_world_only"

D_WORLD_ONLY_TASK = """Held-out purpose D, WORLD-ONLY condition.

The environment contains a frozen compiled World, purpose D, and a Python/SQL interface.
Raw source evidence is physically absent. Do not mutate world/world.sqlite.

Read purposes/visible_d.md. Compute purpose_ir/d/output.json from World using Python/SQL.

If World is insufficient, write purpose_ir/d/output.json with
{"purpose": "traceable_result_with_dataset", "insufficient_world": true, "reason": "...", "cases": []}
and do not invent source facts.

Do not read files outside this workspace.
"""

README = """# D_WORLD_ONLY

Frozen World from purposes A/B/C. Purpose D is visible. Sources are absent.
Do not mutate world/world.sqlite.
PYTHONPATH=. so `import taskview` works.
"""


def sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def build_workspace(destination: Path) -> str:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    world_src = ABC / "world" / "world.sqlite"
    if not world_src.exists():
        raise RuntimeError("A/B/C world is not frozen")
    world_dir = destination / "world"
    world_dir.mkdir()
    shutil.copy2(world_src, world_dir / "world.sqlite")
    obligations = ABC / "world" / "obligations.json"
    if obligations.exists():
        shutil.copy2(obligations, world_dir / "obligations.json")
    vocab = ABC / "construction" / "vocabulary.json"
    if vocab.exists():
        construction = destination / "construction"
        construction.mkdir()
        shutil.copy2(vocab, construction / "vocabulary.json")
    dest_tv = destination / "taskview"
    dest_tv.mkdir()
    for name in ("__init__.py", "model.py", "store.py", "agent_surface.py"):
        shutil.copy2(TASKVIEW_SRC / name, dest_tv / name)
    shutil.copy2(KERNEL, destination / "KERNEL.md")
    purposes = destination / "purposes"
    purposes.mkdir()
    (purposes / "visible_d.md").write_text(visible_d_text(), encoding="utf-8")
    (destination / "purpose_ir" / "d").mkdir(parents=True)
    (destination / "D_TASK.md").write_text(D_WORLD_ONLY_TASK, encoding="utf-8")
    (destination / "README.md").write_text(README, encoding="utf-8")
    if (destination / "sources").exists():
        raise RuntimeError("sources must be absent from D_WORLD_ONLY")
    return sha256_file(world_dir / "world.sqlite")


def run_d_world_only() -> dict:
    live = new_live_workspace()
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        before = build_workspace(live)
        preflight = preflight_isolation(live)
        if (live / "sources").exists() or list(live.rglob("study_registry.csv")):
            raise RuntimeError("D_WORLD_ONLY workspace contains source files")
        agent = run_constructor(workspace=live, prompt=D_WORLD_ONLY_TASK)
        leaks = isolation_leaks_from_events(agent.get("events") or [])
        after = sha256_file(live / "world" / "world.sqlite")
        (OUT / "transcript.stdout.txt").write_text(agent["stdout"] or "", encoding="utf-8")
        (OUT / "transcript.stderr.txt").write_text(agent["stderr"] or "", encoding="utf-8")
        (OUT / "agent.json").write_text(
            json.dumps(
                {
                    "returncode": agent["returncode"],
                    "timed_out": agent["timed_out"],
                    "tools": agent["tools"],
                    "model": agent["model"],
                    "reported_model": agent.get("reported_model"),
                    "isolation_leaks": leaks,
                    "isolation_preflight": preflight,
                    "world_fingerprint_before": before,
                    "world_fingerprint_after": after,
                    "world_mutated": before != after,
                    "label": "PRE_REPAIR_CONSTRUCTOR_BASELINE",
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        saved = OUT / "workspace"
        if saved.exists():
            shutil.rmtree(saved)
        shutil.copytree(live, saved)
    finally:
        remove_live_workspace(live)
    if leaks:
        raise RuntimeError(f"isolation failed on D_WORLD_ONLY: {leaks}")
    return {
        "isolation_leaks": leaks,
        "world_fingerprint_before": before,
        "world_fingerprint_after": after,
        "world_mutated": before != after,
    }


if __name__ == "__main__":
    print(json.dumps(run_d_world_only(), indent=2, sort_keys=True))
