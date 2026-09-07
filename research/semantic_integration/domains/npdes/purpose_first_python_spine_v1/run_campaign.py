"""Resumable 5-trial campaign. Composer 2.5 only. Host runs construction.py from scratch."""

from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from research.semantic_integration.domains.npdes.purpose_first_python_spine_v1.agent import run_probe_agent
from research.semantic_integration.domains.npdes.purpose_first_python_spine_v1.isolation import (
    isolation_leaks_from_events,
    new_live_workspace,
    preflight_isolation,
    remove_live_workspace,
)
from research.semantic_integration.domains.npdes.purpose_first_python_spine_v1.paths import (
    FROZEN,
    MAX_CONSTRUCT_ITERS,
    MODEL,
    N_TRIALS,
    REPORTS,
    RUNS,
    SPINE_V1,
    TIMEOUT_SECONDS,
)
from research.semantic_integration.domains.npdes.purpose_first_python_spine_v1.prompts import (
    FIRST_PROMPT,
    REPAIR_PROMPT,
)
from research.semantic_integration.domains.npdes.purpose_first_python_spine_v1.runner import (
    prepare_clean_run,
    public_feedback,
    run_construction,
)
from research.semantic_integration.domains.npdes.purpose_first_python_spine_v1.workspaces import (
    freeze_input_manifest,
    seed_workspace,
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def dump(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")


def slim_agent(record: dict) -> dict:
    stdout = record.get("stdout") or ""
    return {
        "adapter": record.get("adapter"),
        "model": record.get("model"),
        "reported_model": record.get("reported_model"),
        "returncode": record.get("returncode"),
        "timed_out": record.get("timed_out"),
        "usage": record.get("usage"),
        "tools": record.get("tools"),
        "exploration": record.get("exploration"),
        "timeout_seconds": record.get("timeout_seconds"),
        "stdout_tail": stdout[-20000:],
        "stderr_tail": (record.get("stderr") or "")[-4000:],
        "isolation_leaks": isolation_leaks_from_events(record.get("events") or []),
        "finished_at": now(),
    }


def run_trial(index: int) -> dict:
    sealed = RUNS / f"T{index}"
    sealed.mkdir(parents=True, exist_ok=True)
    summary_path = sealed / "trial.json"
    if summary_path.exists():
        return json.loads(summary_path.read_text(encoding="utf-8"))

    live = new_live_workspace()
    iterations: list[dict] = []
    last_run: dict | None = None
    try:
        seed_workspace(live)
        preflight = preflight_isolation(live)
        dump(sealed / "isolation_preflight.json", preflight)
        for iteration in range(1, MAX_CONSTRUCT_ITERS + 1):
            iter_dir = sealed / f"iter{iteration}"
            iter_dir.mkdir(parents=True, exist_ok=True)
            prompt = FIRST_PROMPT if iteration == 1 else REPAIR_PROMPT
            (iter_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
            raw = run_probe_agent(workspace=live, prompt=prompt, timeout_seconds=TIMEOUT_SECONDS)
            agent = slim_agent(raw)
            dump(iter_dir / "agent.json", agent)
            (iter_dir / "transcript.stdout.txt").write_text((raw.get("stdout") or "")[-400000:], encoding="utf-8")
            (iter_dir / "transcript.stderr.txt").write_text((raw.get("stderr") or "")[-80000:], encoding="utf-8")
            if agent["isolation_leaks"]:
                dump(sealed / "LEAK.json", {"leaks": agent["isolation_leaks"]})
                raise RuntimeError(f"isolation leak: {agent['isolation_leaks']}")
            reported = agent.get("reported_model")
            if reported and "composer" not in str(reported).lower():
                dump(sealed / "MODEL_FAIL.json", {"reported_model": reported})
                raise RuntimeError(f"non-Composer model {reported!r}")
            if (live / "construction.py").exists():
                shutil.copy2(live / "construction.py", iter_dir / "construction.py")
            clean = iter_dir / "clean_run"
            prepare_clean_run(live, clean)
            result = run_construction(clean)
            dump(iter_dir / "run.json", {k: v for k, v in result.items() if k != "hole_instances"})
            public = public_feedback(result)
            dump(iter_dir / "diagnostics_public.json", public)
            dump(live / "diagnostics.json", public)
            if (clean / "spine.json").exists():
                shutil.copy2(clean / "spine.json", iter_dir / "spine.json")
            if (clean / "holes.json").exists():
                shutil.copy2(clean / "holes.json", iter_dir / "holes.json")
            last_run = result
            iterations.append(
                {
                    "iteration": iteration,
                    "ok": bool(result.get("ok")),
                    "errors": result.get("errors") or [],
                    "n_hole_groups": result.get("n_hole_groups") or 0,
                    "n_hole_instances": result.get("n_hole_instances") or 0,
                    "relation_row_counts": result.get("relation_row_counts") or {},
                    "timed_out": agent.get("timed_out"),
                    "reported_model": agent.get("reported_model"),
                    "usage": agent.get("usage"),
                    "exploration": agent.get("exploration"),
                }
            )
            if result.get("ok"):
                break
        accepted = next((row for row in reversed(iterations) if row["ok"]), None)
        trial = {
            "trial": f"T{index}",
            "model": MODEL,
            "n_iterations": len(iterations),
            "accepted": bool(accepted),
            "iterations": iterations,
            "final": {
                "ok": bool((last_run or {}).get("ok")),
                "errors": (last_run or {}).get("errors") or [],
                "relation_row_counts": (last_run or {}).get("relation_row_counts") or {},
                "referent_kinds": (last_run or {}).get("referent_kinds") or {},
                "relations": (last_run or {}).get("relations") or {},
                "n_hole_groups": (last_run or {}).get("n_hole_groups") or 0,
                "n_hole_instances": (last_run or {}).get("n_hole_instances") or 0,
                "hole_groups": (last_run or {}).get("hole_groups") or [],
                "requirement_names": (last_run or {}).get("requirement_names") or [],
            },
            "finished_at": now(),
        }
        dump(summary_path, trial)
        dump(sealed / "final_run.json", trial["final"])
        return trial
    finally:
        remove_live_workspace(live)


def freeze_if_needed() -> None:
    FROZEN.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    src = SPINE_V1 / "frozen" / "triggerability.json"
    dest = FROZEN / "triggerability.json"
    if not dest.exists():
        payload = json.loads(src.read_text(encoding="utf-8"))
        payload = dict(payload)
        payload["reused_from"] = "npdes-spine-compiler-probe-v1"
        payload["reused_unchanged"] = True
        payload["this_experiment_id"] = "npdes-purpose-first-python-spine-v1"
        dest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    md_src = SPINE_V1 / "frozen" / "triggerability.md"
    if not (FROZEN / "triggerability.md").exists():
        shutil.copy2(md_src, FROZEN / "triggerability.md")
    if not (FROZEN / "input_manifest.json").exists():
        dump(FROZEN / "input_manifest.json", freeze_input_manifest())
    if not (REPORTS / "experiment_freeze.md").exists() and (FROZEN / "experiment_freeze.md").exists():
        shutil.copy2(FROZEN / "experiment_freeze.md", REPORTS / "experiment_freeze.md")
    if not (REPORTS / "python_authoring_surface.md").exists():
        shutil.copy2(FROZEN / "WORLD_API.md", REPORTS / "python_authoring_surface.md")


def main() -> None:
    freeze_if_needed()
    for index in range(1, N_TRIALS + 1):
        print(f"=== T{index} ===", flush=True)
        trial = run_trial(index)
        print(
            f"T{index} ok={trial['final']['ok']} iters={trial['n_iterations']} "
            f"groups={trial['final']['n_hole_groups']}",
            flush=True,
        )
    from research.semantic_integration.domains.npdes.purpose_first_python_spine_v1.report import write_reports
    from research.semantic_integration.domains.npdes.purpose_first_python_spine_v1.score import score_campaign

    scored = score_campaign()
    dump(RUNS / "score.json", scored)
    write_reports(scored)
    print("sealed reports written", flush=True)


if __name__ == "__main__":
    main()
