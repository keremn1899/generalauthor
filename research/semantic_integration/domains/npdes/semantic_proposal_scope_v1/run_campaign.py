"""Resumable campaign. Inject frozen utterances exactly. Composer 2.5 only."""

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
from research.semantic_integration.domains.npdes.semantic_proposal_scope_v1.agent import run_probe_agent
from research.semantic_integration.domains.npdes.semantic_proposal_scope_v1.cases import CASES, INTENTS
from research.semantic_integration.domains.npdes.semantic_proposal_scope_v1.diffs import (
    delta,
    digest_from_run,
    sha256_file,
    source_fingerprints,
)
from research.semantic_integration.domains.npdes.semantic_proposal_scope_v1.issues import ISSUES
from research.semantic_integration.domains.npdes.semantic_proposal_scope_v1.isolation import (
    isolation_leaks_from_events,
    new_live_workspace,
    preflight_isolation,
    remove_live_workspace,
)
from research.semantic_integration.domains.npdes.semantic_proposal_scope_v1.paths import (
    DRAFT_TRIAL,
    EVALUATOR_ONLY,
    EXPERIMENT_ID,
    FROZEN,
    REPORTS,
    RUNS,
    TIMEOUT_SECONDS,
)
from research.semantic_integration.domains.npdes.semantic_proposal_scope_v1.prompts import (
    COMMIT_PROMPT,
    DECIDE_PROMPT,
    PROPOSE_PROMPT,
)
from research.semantic_integration.domains.npdes.semantic_proposal_scope_v1.workspaces import (
    seed_host_workspace,
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def dump(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")


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
        "assistant_text": (record.get("assistant_text") or "")[-50000:],
        "timeout_seconds": record.get("timeout_seconds"),
        "stdout_tail": (record.get("stdout") or "")[-20000:],
        "stderr_tail": (record.get("stderr") or "")[-4000:],
        "isolation_leaks": isolation_leaks_from_events(record.get("events") or []),
        "finished_at": now(),
    }


def freeze_inputs() -> None:
    FROZEN.mkdir(parents=True, exist_ok=True)
    EVALUATOR_ONLY.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    dump(FROZEN / "cases.json", {"draft_trial": DRAFT_TRIAL, "cases": CASES, "issues": ISSUES})
    dump(EVALUATOR_ONLY / "intents.json", INTENTS)
    (EVALUATOR_ONLY / "README.md").write_text(
        "Evaluator-only intents. Never copy into a host workspace. Not GOLD NPDES law.\n",
        encoding="utf-8",
    )
    (FROZEN / "experiment_freeze.md").write_text(
        "\n".join(
            [
                "# Semantic Proposal & Scope Clarification Microprobe v1 — freeze",
                "",
                f"Draft spine: sealed {DRAFT_TRIAL} construction.py",
                "Utterances injected exactly. No proxy user.",
                "Host never sees evaluator intents or GOLD.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def agent_failure(agent: dict) -> str | None:
    if agent.get("isolation_leaks"):
        return f"leak:{agent['isolation_leaks']}"
    reported = agent.get("reported_model")
    blob = f"{agent.get('stderr_tail') or ''} {agent.get('stdout_tail') or ''} {agent.get('assistant_text') or ''}"
    lowered = blob.lower()
    if "cannot use this model" in lowered or "[unavailable]" in lowered or "error: [unavailable]" in lowered:
        return "model_unavailable"
    if agent.get("timed_out"):
        return "timeout"
    if not reported:
        return "missing_reported_model"
    if "composer" not in str(reported).lower():
        return f"non_composer:{reported}"
    return None


def check_agent(sealed: Path, agent: dict) -> None:
    fail = agent_failure(agent)
    if not fail:
        return
    dump(sealed / "MODEL_FAIL.json", {"failure": fail, "reported_model": agent.get("reported_model"), "stderr_tail": agent.get("stderr_tail")})
    raise RuntimeError(f"host agent failure: {fail}")


def run_host(sealed: Path, live: Path, prompt: str, name: str) -> dict:
    sealed.mkdir(parents=True, exist_ok=True)
    (sealed / f"{name}.prompt.txt").write_text(prompt, encoding="utf-8")
    last: dict | None = None
    for attempt in range(1, 7):
        raw = run_probe_agent(workspace=live, prompt=prompt, timeout_seconds=TIMEOUT_SECONDS)
        agent = slim_agent(raw)
        agent["attempt"] = attempt
        last = agent
        fail = agent_failure(agent)
        dump(sealed / f"{name}.agent.json", agent)
        (sealed / f"{name}.stdout.txt").write_text((raw.get("stdout") or "")[-400000:], encoding="utf-8")
        if not fail:
            return agent
        dump(sealed / f"{name}.attempt{attempt}.json", {"failure": fail, "reported_model": agent.get("reported_model"), "stderr_tail": agent.get("stderr_tail")})
        if fail.startswith("leak:") or fail.startswith("non_composer:"):
            break
        time.sleep(min(120, 25 * attempt))
    check_agent(sealed, last or {})
    return last or {}


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


def construction_hash(live: Path) -> str:
    path = live / "construction.py"
    return sha256_file(path) if path.exists() else ""


def find_dry_runs(live: Path) -> list[tuple[str, Path]]:
    root = live / "dry_run"
    found: list[tuple[str, Path]] = []
    if not root.exists():
        return found
    if (root / "construction.py").exists():
        found.append(("primary", root))
    for child in sorted(root.iterdir()):
        if child.is_dir() and (child / "construction.py").exists():
            found.append((child.name, child))
    return found


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


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"_parse_error": True, "raw": path.read_text(encoding="utf-8")[:8000]}


def previous_proposal_markdown(prev_sealed: Path) -> str:
    parts = [
        "# Uncommitted previous proposal",
        "",
        "This proposal has NOT been committed. Durable construction.py is still the original draft.",
        "The expert is now responding to this proposal.",
        "",
    ]
    for name in ("PROPOSAL.json", "CANDIDATES.json", "DECISION.json", "ACCEPTANCE.md", "CLARIFY.md"):
        path = prev_sealed / name
        if not path.exists():
            continue
        parts.append(f"## {name}")
        parts.append("")
        parts.append(path.read_text(encoding="utf-8")[:20000])
        parts.append("")
    dry = prev_sealed / "DRY_RUN_RESULTS.json"
    if dry.exists():
        parts.append("## DRY_RUN_RESULTS.json")
        parts.append("")
        parts.append(dry.read_text(encoding="utf-8")[:30000])
        parts.append("")
    return "\n".join(parts) + "\n"


def slim_public(public: dict) -> dict:
    groups = []
    for group in public.get("hole_groups") or []:
        groups.append(
            {
                "group_id": group.get("group_id"),
                "requirement": group.get("requirement"),
                "failure_kind": group.get("failure_kind"),
                "relation": group.get("relation"),
                "n_instances": group.get("n_instances"),
            }
        )
    return {
        "ok": public.get("ok"),
        "errors": public.get("errors"),
        "n_hole_groups": public.get("n_hole_groups"),
        "n_hole_instances": public.get("n_hole_instances"),
        "relation_row_counts": public.get("relation_row_counts"),
        "requirement_names": public.get("requirement_names"),
        "hole_groups": groups,
    }


def run_case(case: dict) -> dict:
    sealed = RUNS / case["id"]
    summary = sealed / "case.json"
    if summary.exists():
        return json.loads(summary.read_text(encoding="utf-8"))
    live = new_live_workspace()
    try:
        seed_host_workspace(live, issue_id=case["issue_id"])
        preflight = preflight_isolation(live)
        dump(sealed / "isolation_preflight.json", preflight)
        utterance = case["utterance"]
        (live / "USER_UTTERANCE.md").write_text(utterance + "\n", encoding="utf-8")
        (sealed / "USER_UTTERANCE.md").write_text(utterance + "\n", encoding="utf-8")
        if case.get("previous_case"):
            prev = RUNS / case["previous_case"]
            md = previous_proposal_markdown(prev)
            (live / "PREVIOUS_PROPOSAL.md").write_text(md, encoding="utf-8")
            (sealed / "PREVIOUS_PROPOSAL.md").write_text(md, encoding="utf-8")
        baseline_hash = construction_hash(live)
        (sealed / "construction.baseline.py").write_text(
            (live / "construction.py").read_text(encoding="utf-8"), encoding="utf-8"
        )
        source_before = source_fingerprints(live)
        dump(sealed / "source_fingerprints_before.json", source_before)
        baseline_public = execute_construction(live, live / "construction.py", sealed / "baseline")
        if (sealed / "baseline" / "spine.json").exists():
            shutil.copy2(sealed / "baseline" / "spine.json", sealed / "baseline_spine.json")
        baseline_digest = digest_from_run(sealed / "baseline")

        propose = run_host(sealed, live, PROPOSE_PROMPT, "propose")
        copy_if(live, sealed, "PROPOSAL.json")
        copy_if(live, sealed, "CANDIDATES.json")
        copy_if(live, sealed, "dry_run")
        hash_after_propose = construction_hash(live)
        mutated_after_propose = hash_after_propose != baseline_hash
        if mutated_after_propose:
            shutil.copy2(sealed / "construction.baseline.py", live / "construction.py")
        dump(
            sealed / "mutation_propose.json",
            {
                "baseline_sha256": baseline_hash,
                "after_propose_sha256": hash_after_propose,
                "mutated": mutated_after_propose,
                "restored": mutated_after_propose,
            },
        )

        dry_runs = []
        dry_payload = []
        for run_id, path in find_dry_runs(live):
            dest = sealed / "dry_runs" / run_id
            public = execute_construction(live, path / "construction.py", dest)
            proposed_digest = digest_from_run(dest)
            dlt = delta(baseline_digest, proposed_digest)
            dump(dest / "delta.json", dlt)
            copy_if(path, dest, "construction.py")
            entry = {
                "id": run_id,
                "public": slim_public(public),
                "delta": dlt,
                "construction_sha256": sha256_file(path / "construction.py"),
            }
            dry_runs.append(entry)
            dry_payload.append(entry)
        dump(sealed / "DRY_RUN_RESULTS.json", {"baseline": slim_public(baseline_public), "proposals": dry_payload})
        (live / "DRY_RUN_RESULTS.json").write_text(
            (sealed / "DRY_RUN_RESULTS.json").read_text(encoding="utf-8"), encoding="utf-8"
        )

        decide = run_host(sealed, live, DECIDE_PROMPT, "decide")
        copy_if(live, sealed, "DECISION.json")
        copy_if(live, sealed, "CLARIFY.md")
        copy_if(live, sealed, "ACCEPTANCE.md")
        copy_if(live, sealed, "PROPOSAL.json")
        copy_if(live, sealed, "CANDIDATES.json")
        hash_after_decide = construction_hash(live)
        mutated_after_decide = hash_after_decide != baseline_hash
        if mutated_after_decide:
            shutil.copy2(sealed / "construction.baseline.py", live / "construction.py")
        dump(
            sealed / "mutation_decide.json",
            {
                "after_decide_sha256": hash_after_decide,
                "mutated": mutated_after_decide,
                "restored": mutated_after_decide,
            },
        )

        decision = load_json(sealed / "DECISION.json")
        disposition = decision.get("disposition")
        committed = False
        commit_public = None
        commit_delta = None
        revert = None
        accept_agent = None
        if disposition == "READY_FOR_ACCEPTANCE" and case.get("accept_if_ready"):
            chosen = decision.get("chosen_dry_run_id") or (dry_runs[0]["id"] if dry_runs else "")
            (live / "COMMIT_STAGE.md").write_text(
                "The expert accepted. You may now overwrite construction.py with the chosen dry-run construction.\n",
                encoding="utf-8",
            )
            (live / "ACCEPT.md").write_text(case["accept_if_ready"] + "\n", encoding="utf-8")
            (live / "CHOSEN_DRY_RUN.txt").write_text(str(chosen) + "\n", encoding="utf-8")
            shutil.copy2(live / "ACCEPT.md", sealed / "ACCEPT.md")
            accept_agent = run_host(sealed, live, COMMIT_PROMPT, "commit")
            copy_if(live, sealed, "COMMITTED.md")
            copy_if(live, sealed, "construction.py")
            committed = construction_hash(live) != baseline_hash
            commit_public = execute_construction(live, live / "construction.py", sealed / "committed")
            commit_delta = delta(baseline_digest, digest_from_run(sealed / "committed"))
            dump(sealed / "committed_delta.json", commit_delta)
            shutil.copy2(sealed / "construction.baseline.py", live / "construction.py")
            revert_public = execute_construction(live, live / "construction.py", sealed / "reverted")
            revert_delta = delta(baseline_digest, digest_from_run(sealed / "reverted"))
            source_after = source_fingerprints(live)
            revert = {
                "construction_restored": construction_hash(live) == baseline_hash,
                "sources_unchanged": source_after == source_before,
                "source_fingerprints_after": source_after,
                "rerun_matches_baseline": revert_delta.get("relation_count_changes") == {}
                and revert_delta.get("requirements_added") == []
                and revert_delta.get("requirements_removed") == []
                and revert_public.get("n_hole_groups") == baseline_public.get("n_hole_groups"),
                "revert_delta": revert_delta,
            }
            dump(sealed / "revert.json", revert)

        proposal = load_json(sealed / "PROPOSAL.json")
        payload = {
            "id": case["id"],
            "n": case["n"],
            "issue_id": case["issue_id"],
            "utterance": utterance,
            "stage": case["stage"],
            "previous_case": case.get("previous_case"),
            "reported_model_propose": propose.get("reported_model"),
            "reported_model_decide": decide.get("reported_model"),
            "reported_model_commit": (accept_agent or {}).get("reported_model"),
            "mutated_after_propose": mutated_after_propose,
            "mutated_after_decide": mutated_after_decide,
            "proposal": proposal,
            "decision": decision,
            "disposition": disposition,
            "n_dry_runs": len(dry_runs),
            "dry_run_ids": [d["id"] for d in dry_runs],
            "clarify": (sealed / "CLARIFY.md").exists(),
            "acceptance": (sealed / "ACCEPTANCE.md").exists(),
            "committed": committed,
            "commit_delta": commit_delta,
            "revert": revert,
            "baseline": slim_public(baseline_public),
            "finished_at": now(),
        }
        dump(summary, payload)
        return payload
    finally:
        remove_live_workspace(live)


def main() -> None:
    RUNS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    freeze_inputs()
    print("frozen", flush=True)
    results = []
    for case in CASES:
        print(f"start {case['id']}", flush=True)
        last_err: Exception | None = None
        payload = None
        for attempt in range(1, 4):
            try:
                payload = run_case(case)
                last_err = None
                break
            except RuntimeError as exc:
                last_err = exc
                print(f"retry {case['id']} attempt={attempt} err={exc}", flush=True)
                sealed = RUNS / case["id"]
                if (sealed / "case.json").exists():
                    break
                time.sleep(min(180, 40 * attempt))
        if payload is None:
            raise last_err or RuntimeError(f"{case['id']} failed")
        results.append({k: v for k, v in payload.items() if k != "proposal"})
        print(f"done {case['id']} disposition={payload.get('disposition')}", flush=True)
    dump(RUNS / "campaign.json", {"experiment_id": EXPERIMENT_ID, "finished_at": now(), "cases": [r["id"] for r in results]})
    dump(RUNS / "cases.json", results)
    print("campaign sealed", flush=True)


if __name__ == "__main__":
    main()
