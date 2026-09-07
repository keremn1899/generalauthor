"""Held-out Purpose D WORLD_ONLY. Sources absent. Frozen Worlds must not change."""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from research.semantic_integration.domains.npdes.constructor_v3_1_1_untouched.agent import (
    MODEL,
    run_v3_agent,
)
from research.semantic_integration.domains.npdes.constructor_v3_1_1_untouched.isolation import (
    REPO,
    new_live_workspace,
    preflight_isolation,
    remove_live_workspace,
)
from research.semantic_integration.domains.npdes.constructor_v3_1_1_untouched.prompts import (
    PROMPTS,
    TIMEOUTS,
)
from research.semantic_integration.domains.npdes.constructor_v3_1_1_untouched.workspaces import (
    KERNEL,
    TASKVIEW_SRC,
    TRIALS,
    copy_taskview,
)

ROOT = Path(__file__).resolve().parent
NPDES = ROOT.parent
PURPOSE_D = NPDES / "fixture" / "evaluator_only" / "purpose_d.md"
REPORTS = ROOT / "reports"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def isolation_leaks_from_events(events: list) -> list[str]:
    leaks: list[str] = []
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


def seed_d_workspace(destination: Path, trial: int) -> Path:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    sealed = TRIALS / f"T{trial}" / "passes" / "p8" / "workspace_snapshot"
    world_src = sealed / "06_world" / "world.sqlite"
    (destination / "world").mkdir()
    (destination / "06_world").mkdir()
    shutil.copy2(world_src, destination / "world" / "world.sqlite")
    shutil.copy2(world_src, destination / "06_world" / "world.sqlite")
    for name in ("01_vocabulary.json", "00_intention_contract.json"):
        src = sealed / name
        if src.exists():
            shutil.copy2(src, destination / name)
    shutil.copy2(KERNEL, destination / "KERNEL.md")
    copy_taskview(destination)
    shutil.copy2(PURPOSE_D, destination / "D_TASK.md")
    for name in (
        "08_outputs",
        "purpose_ir/d",
        "construction/derivations",
        "reports",
    ):
        (destination / name).mkdir(parents=True, exist_ok=True)
    (destination / "README.md").write_text(
        "Held-out Purpose D WORLD_ONLY. Compiled World present. Participant sources absent.\n",
        encoding="utf-8",
    )
    assert not (destination / "sources").exists()
    return world_src


def run_one(trial: int) -> dict:
    sealed_out = TRIALS / f"T{trial}" / "held_out_d"
    if (sealed_out / "agent.json").exists() and (sealed_out / "08_outputs" / "d.json").exists():
        return json.loads((sealed_out / "agent.json").read_text())
    live = new_live_workspace()
    try:
        world_src = seed_d_workspace(live, trial)
        hash_before = sha256_file(world_src)
        hash_live_before = sha256_file(live / "world" / "world.sqlite")
        preflight = preflight_isolation(live)
        agent = run_v3_agent(
            workspace=live,
            prompt=PROMPTS["d_world_only"],
            timeout_seconds=TIMEOUTS["d_world_only"],
        )
        leaks = isolation_leaks_from_events(agent.get("events") or [])
        sealed_out.mkdir(parents=True, exist_ok=True)
        (sealed_out / "transcript.stdout.txt").write_text((agent["stdout"] or "")[:2_000_000])
        (sealed_out / "transcript.stderr.txt").write_text((agent["stderr"] or "")[:500_000])
        hash_after = sha256_file(live / "world" / "world.sqlite")
        hash_src_after = sha256_file(world_src)
        for rel in (
            "purpose_ir/d/output.json",
            "08_outputs/d.json",
        ):
            src = live / rel
            if src.exists():
                dest = sealed_out / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
        source_reads = [
            p
            for p in ((agent.get("tools") or {}).get("mentioned_paths") or [])
            if "sources/" in str(p) or str(p).endswith(".pdf") or "evaluator_only" in str(p)
        ]
        record = {
            "trial": trial,
            "mode": "WORLD_ONLY",
            "returncode": agent["returncode"],
            "timed_out": agent["timed_out"],
            "model": agent["model"],
            "reported_model": agent.get("reported_model"),
            "adapter": agent["adapter"],
            "isolation_leaks": leaks,
            "isolation_preflight": preflight,
            "tools": agent["tools"],
            "source_path_mentions": source_reads,
            "world_hash_before": hash_before,
            "world_hash_live_before": hash_live_before,
            "world_hash_after": hash_after,
            "frozen_world_unchanged": hash_src_after == hash_before,
            "live_world_unchanged": hash_after == hash_live_before,
            "sources_present": (live / "sources").exists(),
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }
        (sealed_out / "agent.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
        return record
    finally:
        remove_live_workspace(live)


def main() -> dict:
    results = [run_one(i) for i in range(1, 6)]
    payload = {
        "experiment_id": "npdes-constructor-v3-1-1-untouched",
        "mode": "WORLD_ONLY",
        "model": MODEL,
        "trials": results,
        "finished_at": datetime.now(timezone.utc).isoformat(),
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "held_out_d.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2)[:4000])
    return payload


if __name__ == "__main__":
    main()
