"""D_WORLD_ONLY and certified-P7 diagnostics. Separate from ordinary constructor success."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from research.semantic_integration.domains.diligence.evaluator import load_json, score_purpose_d
from research.semantic_integration.domains.diligence.pass_localization.agent import run_pass_agent
from research.semantic_integration.domains.diligence.pass_localization.campaign import (
    abort,
    isolation_leaks_from_events,
)
from research.semantic_integration.domains.diligence.pass_localization.certified_world import (
    build_certified_world,
)
from research.semantic_integration.domains.diligence.pass_localization.isolation import (
    new_live_workspace,
    preflight_isolation,
    remove_live_workspace,
)
from research.semantic_integration.domains.diligence.pass_localization.prompts import (
    D_WORLD_ONLY,
    P7_CERTIFIED,
    TIMEOUTS,
)
from research.semantic_integration.domains.diligence.pass_localization.workspaces import (
    DILIGENCE,
    FROZEN_ABC_WORLD,
    KERNEL,
    PURPOSES,
    copy_taskview,
)

ROOT = Path(__file__).resolve().parent
HIDDEN = DILIGENCE / "hidden"


def run_d_world_only() -> dict:
    dest = ROOT / "d_world_only"
    if (dest / "score.json").exists() and (dest / "agent.json").exists():
        return json.loads((dest / "score.json").read_text())
    if not FROZEN_ABC_WORLD.exists():
        raise RuntimeError("frozen A/B/C world missing")
    dest.mkdir(parents=True, exist_ok=True)
    live = new_live_workspace()
    try:
        (live / "world").mkdir()
        shutil.copy2(FROZEN_ABC_WORLD, live / "world" / "world.sqlite")
        shutil.copy2(KERNEL, live / "KERNEL.md")
        copy_taskview(live)
        d_text = (HIDDEN / "purpose_d.md").read_text(encoding="utf-8")
        visible = "\n".join(
            line
            for line in d_text.splitlines()
            if "constructor workspace" not in line.lower()
            and "held out from the constructor" not in line.lower()
        )
        (live / "D_TASK.md").write_text(visible.strip() + "\n", encoding="utf-8")
        (live / "purpose_ir" / "d").mkdir(parents=True)
        (live / "08_outputs").mkdir()
        (live / "README.md").write_text(
            "D_WORLD_ONLY diagnostic. Compiled World plus purpose D. Sources are absent.\n",
            encoding="utf-8",
        )
        if (live / "sources").exists():
            shutil.rmtree(live / "sources")
        preflight = preflight_isolation(live)
        agent = run_pass_agent(
            workspace=live, prompt=D_WORLD_ONLY, timeout_seconds=TIMEOUTS["d_world_only"]
        )
        leaks = isolation_leaks_from_events(agent.get("events") or [])
        saved = dest / "workspace"
        if saved.exists():
            shutil.rmtree(saved)
        shutil.copytree(live, saved)
        (dest / "transcript.stdout.txt").write_text(agent["stdout"] or "", encoding="utf-8")
        (dest / "agent.json").write_text(
            json.dumps(
                {
                    "model": agent["model"],
                    "reported_model": agent.get("reported_model"),
                    "isolation_leaks": leaks,
                    "isolation_preflight": preflight,
                    "timed_out": agent["timed_out"],
                    "tools": agent["tools"],
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        if leaks:
            abort(f"isolation failed D_WORLD_ONLY: {leaks}")
        actual = load_json(saved / "purpose_ir" / "d" / "output.json") or load_json(
            saved / "08_outputs" / "d.json"
        )
        expected = load_json(HIDDEN / "expected" / "purpose_d.json")
        score = score_purpose_d(actual, expected)
        source_rereads = [
            path
            for path in (agent.get("tools") or {}).get("mentioned_paths") or []
            if any(
                name in str(path)
                for name in ("crm.csv", "invoices.json", "/contracts/", "commercial_notes")
            )
        ]
        payload = {
            "score": score,
            "source_rereads": source_rereads,
            "sources_present": bool(list(saved.rglob("crm.csv"))),
            "world_fingerprint_source": str(FROZEN_ABC_WORLD),
        }
        (dest / "score.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        return payload
    finally:
        remove_live_workspace(live)


def run_p7_certified(trial: int) -> dict:
    dest = ROOT / "p7_certified" / f"T{trial}"
    score_path = dest / "score.json"
    if score_path.exists() and (dest / "agent.json").exists():
        return json.loads(score_path.read_text())
    dest.mkdir(parents=True, exist_ok=True)
    live = new_live_workspace()
    try:
        (live / "world").mkdir()
        build_certified_world(live / "world" / "world.sqlite")
        shutil.copy2(KERNEL, live / "KERNEL.md")
        copy_taskview(live)
        purposes = live / "purposes"
        purposes.mkdir()
        for name in ("visible_a.md", "visible_b.md", "visible_c.md"):
            shutil.copy2(PURPOSES / name, purposes / name)
        (live / "construction" / "derivations").mkdir(parents=True)
        (live / "purpose_ir" / "a").mkdir(parents=True)
        (live / "purpose_ir" / "b").mkdir(parents=True)
        (live / "purpose_ir" / "c").mkdir(parents=True)
        (live / "08_outputs").mkdir()
        (live / "PASS_TASK.md").write_text(P7_CERTIFIED, encoding="utf-8")
        (live / "README.md").write_text(
            "P7-certified diagnostic. Evaluator World plus purposes A/B/C. Sources are absent.\n",
            encoding="utf-8",
        )
        if (live / "sources").exists():
            shutil.rmtree(live / "sources")
        preflight = preflight_isolation(live)
        agent = run_pass_agent(
            workspace=live, prompt=P7_CERTIFIED, timeout_seconds=TIMEOUTS["p7_certified"]
        )
        leaks = isolation_leaks_from_events(agent.get("events") or [])
        saved = dest / "workspace"
        if saved.exists():
            shutil.rmtree(saved)
        shutil.copytree(live, saved)
        (dest / "transcript.stdout.txt").write_text(agent["stdout"] or "", encoding="utf-8")
        (dest / "agent.json").write_text(
            json.dumps(
                {
                    "trial": trial,
                    "model": agent["model"],
                    "reported_model": agent.get("reported_model"),
                    "isolation_leaks": leaks,
                    "isolation_preflight": preflight,
                    "timed_out": agent["timed_out"],
                    "tools": agent["tools"],
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        if leaks:
            abort(f"isolation failed P7_CERTIFIED T{trial}: {leaks}")
        from research.semantic_integration.domains.diligence.evaluator import (
            score_purpose_a,
            score_purpose_b,
            score_purpose_c,
        )

        actual_a = load_json(saved / "08_outputs" / "a.json") or load_json(
            saved / "purpose_ir" / "a" / "output.json"
        )
        actual_b = load_json(saved / "08_outputs" / "b.json") or load_json(
            saved / "purpose_ir" / "b" / "output.json"
        )
        actual_c = load_json(saved / "08_outputs" / "c.json") or load_json(
            saved / "purpose_ir" / "c" / "output.json"
        )
        payload = {
            "A": score_purpose_a(actual_a, load_json(HIDDEN / "expected" / "purpose_a.json")),
            "B": score_purpose_b(actual_b, load_json(HIDDEN / "expected" / "purpose_b.json")),
            "C": score_purpose_c(actual_c, load_json(HIDDEN / "expected" / "purpose_c.json")),
            "sources_present": bool(list(saved.rglob("crm.csv"))),
        }
        (dest / "score.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        return payload
    finally:
        remove_live_workspace(live)


def run_all_p7_certified() -> dict:
    results = {f"T{i}": run_p7_certified(i) for i in range(1, 6)}
    (ROOT / "p7_certified" / "results.json").write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n"
    )
    return results
