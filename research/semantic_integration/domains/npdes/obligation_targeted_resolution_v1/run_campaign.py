"""Resumable campaign. Composer 2.5. Arm A once; Arm B three isolated trials."""

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

from research.semantic_integration.domains.npdes.obligation_targeted_resolution_v1.agent import run_probe_agent
from research.semantic_integration.domains.npdes.obligation_targeted_resolution_v1.freeze import freeze, host_visible_obligation
from research.semantic_integration.domains.npdes.obligation_targeted_resolution_v1.isolation import (
    isolation_leaks_from_events,
    new_live_workspace,
    preflight_isolation,
    remove_live_workspace,
)
from research.semantic_integration.domains.npdes.obligation_targeted_resolution_v1.paths import (
    EXPERIMENT_ID,
    FROZEN,
    N_ARM_B_TRIALS,
    REPORTS,
    RUNS,
    TIMEOUT_SECONDS,
)
from research.semantic_integration.domains.npdes.obligation_targeted_resolution_v1.prompts import (
    ADJUDICATE_PROMPT,
    OCCURRENCE_PROMPT,
    RETRIEVE_PROMPT,
)
from research.semantic_integration.domains.npdes.obligation_targeted_resolution_v1.workspaces import (
    seed_adjudicate_workspace,
    seed_occurrence_workspace,
    seed_retrieve_workspace,
    seed_sources,
)
from research.semantic_integration.domains.npdes.purpose_first_python_spine_v1.runner import (
    prepare_clean_run,
    run_construction,
)
from research.semantic_integration.domains.npdes.semantic_proposal_scope_v1.diffs import (
    delta,
    digest_from_run,
    sha256_file,
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


def run_host(sealed: Path, live: Path, prompt: str, name: str) -> dict:
    sealed.mkdir(parents=True, exist_ok=True)
    (sealed / f"{name}.prompt.txt").write_text(prompt, encoding="utf-8")
    last: dict | None = None
    for attempt in range(1, 7):
        try:
            raw = run_probe_agent(workspace=live, prompt=prompt, timeout_seconds=TIMEOUT_SECONDS)
            agent = slim_agent(raw)
            agent["attempt"] = attempt
            last = agent
            fail = agent_failure(agent)
            dump(sealed / f"{name}.agent.json", agent)
            (sealed / f"{name}.stdout.txt").write_text((raw.get("stdout") or "")[-400000:], encoding="utf-8")
        except RuntimeError as exc:
            msg = str(exc)
            agent = {
                "attempt": attempt,
                "reported_model": None,
                "timed_out": False,
                "stderr_tail": msg,
                "stdout_tail": "",
            }
            last = agent
            lowered = msg.lower()
            if "cannot use this model" in lowered or "[unavailable]" in lowered or "none" in lowered:
                fail = "model_unavailable"
            elif "non-cursor" in lowered:
                fail = f"non_composer:{msg}"
            else:
                fail = f"agent_error:{msg[:240]}"
            dump(sealed / f"{name}.attempt{attempt}.json", {"failure": fail, "error": msg})
        if not fail:
            return agent
        dump(sealed / f"{name}.attempt{attempt}.json", {"failure": fail, "stderr_tail": agent.get("stderr_tail")})
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


def selected() -> list[dict]:
    payload = loadj(FROZEN / "selected_obligations.json")
    return payload.get("obligations") or []


def run_arm_a_case(case: dict) -> dict:
    sealed = RUNS / "arm_a" / case["case_id"]
    summary = sealed / "case.json"
    if summary.exists():
        return json.loads(summary.read_text(encoding="utf-8"))
    live = new_live_workspace()
    try:
        seed_occurrence_workspace(live, case)
        preflight_isolation(live)
        agent = run_host(sealed, live, OCCURRENCE_PROMPT, "host")
        copy_if(live, sealed, "JUDGMENT.json")
        payload = {
            **case,
            "reported_model": agent.get("reported_model"),
            "retrieval": agent.get("retrieval"),
            "judgment": loadj(sealed / "JUDGMENT.json"),
            "finished_at": now(),
        }
        dump(summary, payload)
        return payload
    finally:
        remove_live_workspace(live)


def run_arm_b_obligation(trial: str, spec: dict) -> dict:
    sealed = RUNS / "arm_b" / trial / spec["obligation_id"]
    summary = sealed / "cell.json"
    if summary.exists():
        return json.loads(summary.read_text(encoding="utf-8"))
    visible = host_visible_obligation(spec)
    live = new_live_workspace()
    try:
        seed_retrieve_workspace(live, visible)
        preflight_isolation(live)
        baseline_hash = sha256_file(live / "construction.py")
        retrieve = run_host(sealed, live, RETRIEVE_PROMPT, "retrieve")
        copy_if(live, sealed, "EVIDENCE_PLAN.json")
        copy_if(live, sealed, "RETRIEVAL_LOG.json")
        copy_if(live, sealed, "PACKET.json")
        copy_if(live, sealed, "REFINEMENT.json")
        copy_if(live, sealed, "BUDGET_EXCEPTION.md")
        mutated = sha256_file(live / "construction.py") != baseline_hash
        dump(sealed / "mutation_retrieve.json", {"mutated": mutated})
        if mutated:
            shutil.copy2(PFPS_CONSTRUCTION(), live / "construction.py")
        packet = loadj(sealed / "PACKET.json")
        adj_live = new_live_workspace()
        try:
            seed_adjudicate_workspace(adj_live, packet or {"obligation_id": spec["obligation_id"], "retained_snippets": []}, live / "construction.py")
            adjudicate = run_host(sealed, adj_live, ADJUDICATE_PROMPT, "adjudicate")
            copy_if(adj_live, sealed, "JUDGMENT.json")
            copy_if(adj_live, sealed, "PROPOSAL.json")
            copy_if(adj_live, sealed, "REVIEW.md")
            copy_if(adj_live, sealed, "dry_run")
            proposed = adj_live / "dry_run" / "construction.py"
            dry = None
            if proposed.exists():
                seed_sources(adj_live)
                public = execute_construction(adj_live, proposed, sealed / "dry_run_run")
                base_dir = RUNS / "baseline_run"
                if not (base_dir / "spine.json").exists():
                    execute_construction(adj_live, live / "construction.py", base_dir)
                dlt = delta(digest_from_run(base_dir), digest_from_run(sealed / "dry_run_run"))
                dump(sealed / "dry_run_delta.json", dlt)
                dry = {"public": public, "delta": dlt}
            payload = {
                "trial": trial,
                "obligation_id": spec["obligation_id"],
                "n_occurrences": spec["n_occurrences"],
                "reported_model_retrieve": retrieve.get("reported_model"),
                "reported_model_adjudicate": adjudicate.get("reported_model"),
                "retrieval": retrieve.get("retrieval"),
                "plan": loadj(sealed / "EVIDENCE_PLAN.json"),
                "packet": packet,
                "judgment": loadj(sealed / "JUDGMENT.json"),
                "proposal": loadj(sealed / "PROPOSAL.json"),
                "refinement": loadj(sealed / "REFINEMENT.json") or None,
                "mutated_before_evidence": mutated,
                "dry_run": dry,
                "finished_at": now(),
            }
            dump(summary, payload)
            return payload
        finally:
            remove_live_workspace(adj_live)
    finally:
        remove_live_workspace(live)


def PFPS_CONSTRUCTION() -> Path:
    from research.semantic_integration.domains.npdes.obligation_targeted_resolution_v1.paths import DRAFT_TRIAL, PFPS

    return PFPS / "runs" / DRAFT_TRIAL / "iter1" / "construction.py"


def ensure_baseline() -> None:
    dest = RUNS / "baseline_run"
    if dest.exists() and (dest / "run_public.json").exists():
        return
    live = new_live_workspace()
    try:
        seed_retrieve_workspace(live, {"obligation_id": "baseline"})
        execute_construction(live, live / "construction.py", dest)
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
    samples = json.loads((FROZEN / "arm_a_sample.json").read_text(encoding="utf-8"))
    arm_a = []
    for case in samples:
        print(f"arm_a {case['case_id']}", flush=True)
        try:
            arm_a.append(run_arm_a_case(case))
        except Exception as exc:
            failures.append({"arm": "A", "id": case["case_id"], "error": str(exc)})
            dump(RUNS / "arm_a" / case["case_id"] / "FAIL.json", {"error": str(exc), "at": now()})
            print(f"FAIL arm_a {case['case_id']}: {exc}", flush=True)
        dump(RUNS / "progress.json", {"last": f"arm_a:{case['case_id']}", "failures": failures, "at": now()})
    dump(RUNS / "arm_a.json", [{k: v for k, v in r.items() if k != "judgment"} | {"disposition": (r.get("judgment") or {}).get("disposition")} for r in arm_a])
    specs = selected()
    arm_b = []
    for i in range(1, N_ARM_B_TRIALS + 1):
        trial = f"T{i}"
        for spec in specs:
            print(f"arm_b {trial} {spec['obligation_id']}", flush=True)
            try:
                arm_b.append(run_arm_b_obligation(trial, spec))
            except Exception as exc:
                failures.append({"arm": "B", "id": f"{trial}/{spec['obligation_id']}", "error": str(exc)})
                dump(RUNS / "arm_b" / trial / spec["obligation_id"] / "FAIL.json", {"error": str(exc), "at": now()})
                print(f"FAIL arm_b {trial} {spec['obligation_id']}: {exc}", flush=True)
            dump(RUNS / "progress.json", {"last": f"arm_b:{trial}:{spec['obligation_id']}", "failures": failures, "at": now()})
    dump(RUNS / "arm_b.json", [{"trial": r.get("trial"), "obligation_id": r.get("obligation_id"), "disposition": (r.get("judgment") or {}).get("disposition"), "admit": (r.get("proposal") or {}).get("admit")} for r in arm_b])
    dump(RUNS / "campaign.json", {"experiment_id": EXPERIMENT_ID, "finished_at": now(), "freeze": stats, "failures": failures})
    print("campaign sealed", flush=True)
    if failures:
        raise SystemExit(f"campaign completed with {len(failures)} failures")


if __name__ == "__main__":
    main()
