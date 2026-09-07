"""Resumable 9-cell campaign. Composer 2.5. One host run per trial×obligation."""

from __future__ import annotations

import json
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from research.semantic_integration.domains.npdes.purpose_first_python_spine_v1.runner import (
    prepare_clean_run,
    run_construction,
)
from research.semantic_integration.domains.npdes.semantic_proposal_scope_v1.diffs import (
    delta,
    digest_from_run,
    sha256_file,
)
from research.semantic_integration.domains.npdes.semantic_refinement_admission_v1.agent import run_probe_agent
from research.semantic_integration.domains.npdes.semantic_refinement_admission_v1.freeze import freeze
from research.semantic_integration.domains.npdes.semantic_refinement_admission_v1.isolation import (
    isolation_leaks_from_events,
    new_live_workspace,
    preflight_isolation,
    remove_live_workspace,
)
from research.semantic_integration.domains.npdes.semantic_refinement_admission_v1.paths import (
    DRAFT_TRIAL,
    EXPERIMENT_ID,
    FROZEN,
    N_TRIALS,
    OBLIGATION_IDS,
    PFPS,
    REPORTS,
    RUNS,
    TIMEOUT_SECONDS,
)
from research.semantic_integration.domains.npdes.semantic_refinement_admission_v1.prompts import REFINE_PROMPT
from research.semantic_integration.domains.npdes.semantic_refinement_admission_v1.workspaces import (
    seed_sources,
    seed_workspace,
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def dump(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")


def loadj(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"_parse_error": True, "raw": path.read_text(encoding="utf-8")[:8000]}


def slim_agent(record: dict) -> dict:
    return {
        "adapter": record.get("adapter"),
        "model": record.get("model"),
        "reported_model": record.get("reported_model"),
        "returncode": record.get("returncode"),
        "timed_out": record.get("timed_out"),
        "usage": record.get("usage"),
        "tools": record.get("tools"),
        "exploration": record.get("exploration"),
        "retrieval": record.get("retrieval"),
        "assistant_text": (record.get("assistant_text") or "")[-40000:],
        "timeout_seconds": record.get("timeout_seconds"),
        "stdout_tail": (record.get("stdout") or "")[-15000:],
        "stderr_tail": (record.get("stderr") or "")[-4000:],
        "isolation_leaks": isolation_leaks_from_events(record.get("events") or []),
        "finished_at": now(),
    }


def agent_failure(agent: dict) -> str | None:
    if agent.get("isolation_leaks"):
        return f"leak:{agent['isolation_leaks']}"
    reported = agent.get("reported_model")
    blob = f"{agent.get('stderr_tail') or ''} {agent.get('stdout_tail') or ''}"
    lowered = blob.lower()
    if "cannot use this model" in lowered or "[unavailable]" in lowered:
        return "model_unavailable"
    if agent.get("timed_out"):
        return "timeout"
    if not reported:
        return "missing_reported_model"
    if "composer" not in str(reported).lower():
        return f"non_composer:{reported}"
    return None


def run_host(sealed: Path, live: Path, prompt: str) -> dict:
    sealed.mkdir(parents=True, exist_ok=True)
    (sealed / "host.prompt.txt").write_text(prompt, encoding="utf-8")
    last: dict | None = None
    fail = "unknown"
    for attempt in range(1, 7):
        try:
            raw = run_probe_agent(workspace=live, prompt=prompt, timeout_seconds=TIMEOUT_SECONDS)
            agent = slim_agent(raw)
            agent["attempt"] = attempt
            last = agent
            fail = agent_failure(agent)
            dump(sealed / "host.agent.json", agent)
            (sealed / "host.stdout.txt").write_text((raw.get("stdout") or "")[-400000:], encoding="utf-8")
        except RuntimeError as exc:
            msg = str(exc)
            agent = {"attempt": attempt, "reported_model": None, "timed_out": False, "stderr_tail": msg, "stdout_tail": ""}
            last = agent
            lowered = msg.lower()
            if "cannot use this model" in lowered or "[unavailable]" in lowered or "none" in lowered:
                fail = "model_unavailable"
            elif "non-cursor" in lowered:
                fail = f"non_composer:{msg}"
            else:
                fail = f"agent_error:{msg[:240]}"
            dump(sealed / f"host.attempt{attempt}.json", {"failure": fail, "error": msg})
        if not fail:
            return agent
        dump(sealed / f"host.attempt{attempt}.json", {"failure": fail, "stderr_tail": agent.get("stderr_tail")})
        if fail.startswith("leak:") or fail.startswith("non_composer:"):
            break
        time.sleep(min(120, 25 * attempt))
    raise RuntimeError(f"host agent failure: {agent_failure(last or {}) or fail}")


def copy_if(live: Path, sealed: Path, name: str) -> None:
    src = live / name
    if not src.exists():
        return
    dest = sealed / name
    if src.is_dir():
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest)
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)


def execute_construction(live: Path, construction_src: Path, dest: Path) -> dict:
    prepare_clean_run(live, dest)
    shutil.copy2(construction_src, dest / "construction.py")
    result = run_construction(dest)
    public = {
        "ok": result.get("ok"),
        "errors": result.get("errors"),
        "n_hole_groups": result.get("n_hole_groups"),
        "n_hole_instances": result.get("n_hole_instances"),
        "relation_row_counts": result.get("relation_row_counts"),
        "requirement_names": result.get("requirement_names"),
        "hole_groups": result.get("hole_groups"),
    }
    dump(dest / "rerun_public.json", public)
    return public


def ensure_baseline() -> None:
    dest = RUNS / "baseline_run"
    if dest.exists() and (dest / "run_public.json").exists():
        return
    live = new_live_workspace()
    try:
        seed_workspace(live, {"obligation_id": "geometric_mean"})
        execute_construction(live, live / "construction.py", dest)
    finally:
        remove_live_workspace(live)


def find_child_constructions(live: Path) -> list[tuple[str, Path]]:
    found: list[tuple[str, Path]] = []
    root = live / "dry_run"
    if not root.exists():
        return found
    if (root / "construction.py").exists():
        found.append(("parent_or_primary", root / "construction.py"))
    for child in sorted(root.iterdir()):
        if child.is_dir() and (child / "construction.py").exists():
            found.append((child.name, child / "construction.py"))
    return found


def host_visible() -> list[dict]:
    payload = json.loads((FROZEN / "selected_obligations.json").read_text(encoding="utf-8"))
    return payload.get("host_visible") or []


def run_cell(trial: str, spec: dict) -> dict:
    sealed = RUNS / trial / spec["obligation_id"]
    summary = sealed / "cell.json"
    if summary.exists():
        return json.loads(summary.read_text(encoding="utf-8"))
    live = new_live_workspace()
    try:
        seed_workspace(live, spec)
        preflight_isolation(live)
        baseline_hash = sha256_file(live / "construction.py")
        agent = run_host(sealed, live, REFINE_PROMPT)
        mutated = sha256_file(live / "construction.py") != baseline_hash
        dump(sealed / "mutation.json", {"mutated_durable": mutated})
        if mutated:
            shutil.copy2(PFPS / "runs" / DRAFT_TRIAL / "iter1" / "construction.py", live / "construction.py")
        for name in (
            "EVIDENCE_PLAN.json",
            "PACKET.json",
            "PARENT.json",
            "REFINEMENT.json",
            "PROPOSALS.json",
            "ADMISSION.json",
            "RETRIEVAL_LOG.json",
            "REVIEW.md",
            "dry_run",
        ):
            copy_if(live, sealed, name)
        dry_results = []
        seed_sources(live)
        for child_id, construction in find_child_constructions(live):
            dest = sealed / "dry_runs" / child_id
            public = execute_construction(live, construction, dest)
            dlt = delta(digest_from_run(RUNS / "baseline_run"), digest_from_run(dest))
            dump(dest / "delta.json", dlt)
            dry_results.append({"child_id": child_id, "ok": public.get("ok"), "errors": public.get("errors"), "delta": dlt, "public": public})
        payload = {
            "trial": trial,
            "obligation_id": spec["obligation_id"],
            "reported_model": agent.get("reported_model"),
            "retrieval": agent.get("retrieval"),
            "parent": loadj(sealed / "PARENT.json"),
            "refinement": loadj(sealed / "REFINEMENT.json") or None,
            "proposals": loadj(sealed / "PROPOSALS.json") or None,
            "admission": loadj(sealed / "ADMISSION.json") or None,
            "plan": loadj(sealed / "EVIDENCE_PLAN.json"),
            "packet": loadj(sealed / "PACKET.json"),
            "retrieval_log": loadj(sealed / "RETRIEVAL_LOG.json"),
            "mutated_durable": mutated,
            "dry_runs": dry_results,
            "finished_at": now(),
        }
        dump(summary, payload)
        return payload
    finally:
        remove_live_workspace(live)


def main() -> None:
    RUNS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    stats = freeze()
    print("frozen", stats, flush=True)
    ensure_baseline()
    print("baseline rerun", flush=True)
    failures: list[dict] = []
    cells = []
    specs = host_visible()
    for i in range(1, N_TRIALS + 1):
        trial = f"T{i}"
        for spec in specs:
            print(f"{trial} {spec['obligation_id']}", flush=True)
            try:
                cells.append(run_cell(trial, spec))
            except Exception as exc:
                failures.append({"id": f"{trial}/{spec['obligation_id']}", "error": str(exc)})
                dump(RUNS / trial / spec["obligation_id"] / "FAIL.json", {"error": str(exc), "at": now()})
                print(f"FAIL {trial} {spec['obligation_id']}: {exc}", flush=True)
            dump(RUNS / "progress.json", {"last": f"{trial}:{spec['obligation_id']}", "failures": failures, "at": now()})
    dump(
        RUNS / "campaign.json",
        {
            "experiment_id": EXPERIMENT_ID,
            "finished_at": now(),
            "freeze": stats,
            "failures": failures,
            "cells": [{"trial": c.get("trial"), "obligation_id": c.get("obligation_id"), "parent_status": (c.get("parent") or {}).get("parent_status")} for c in cells],
        },
    )
    print("campaign sealed", flush=True)
    if failures:
        raise SystemExit(f"campaign completed with {len(failures)} failures")


if __name__ == "__main__":
    main()
