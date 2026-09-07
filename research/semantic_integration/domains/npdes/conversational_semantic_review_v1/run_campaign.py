"""Resumable campaign. Composer 2.5 only."""

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

from research.semantic_integration.domains.npdes.conversational_semantic_review_v1.agent import run_probe_agent
from research.semantic_integration.domains.npdes.conversational_semantic_review_v1.hidden import (
    FOLLOWUP_AFTER_BARE_NO,
    INTERVENTIONS,
    PACKETS,
)
from research.semantic_integration.domains.npdes.conversational_semantic_review_v1.isolation import (
    isolation_leaks_from_events,
    new_live_workspace,
    preflight_isolation,
    remove_live_workspace,
)
from research.semantic_integration.domains.npdes.conversational_semantic_review_v1.issues import ISSUES
from research.semantic_integration.domains.npdes.conversational_semantic_review_v1.paths import (
    DRAFT_TRIAL,
    EVALUATOR_ONLY,
    EXPERIMENT_ID,
    FROZEN,
    N_MP1_TRIALS,
    N_MP3_TRIALS,
    REPORTS,
    RUNS,
    TIMEOUT_SECONDS,
)
from research.semantic_integration.domains.npdes.conversational_semantic_review_v1.prompts import (
    MP1_PROMPT,
    MP2_NEAR_PROMPT,
    MP2_OPEN_PROMPT,
    MP3_AFTER_CLARIFY_PROMPT,
    MP3_EXPLAIN_PROMPT,
    MP3_REVISE_PROMPT,
    PROXY_PROMPT,
)
from research.semantic_integration.domains.npdes.conversational_semantic_review_v1.workspaces import (
    seed_host_workspace,
    seed_proxy_workspace,
)
from research.semantic_integration.domains.npdes.purpose_first_python_spine_v1.runner import (
    prepare_clean_run,
    run_construction,
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
    dump(FROZEN / "obligations.json", {"draft_trial": DRAFT_TRIAL, "issues": ISSUES})
    dump(EVALUATOR_ONLY / "packets.json", PACKETS)
    dump(EVALUATOR_ONLY / "interventions.json", INTERVENTIONS)
    (EVALUATOR_ONLY / "README.md").write_text(
        "Evaluator-only. Never copy into a host workspace. Not GOLD NPDES law.\n",
        encoding="utf-8",
    )


def check_agent(sealed: Path, agent: dict) -> None:
    if agent.get("isolation_leaks"):
        dump(sealed / "LEAK.json", {"leaks": agent["isolation_leaks"]})
        raise RuntimeError(f"isolation leak: {agent['isolation_leaks']}")
    reported = agent.get("reported_model")
    if reported and "composer" not in str(reported).lower():
        dump(sealed / "MODEL_FAIL.json", {"reported_model": reported})
        raise RuntimeError(f"non-Composer model {reported!r}")


def run_host(sealed: Path, live: Path, prompt: str, name: str) -> dict:
    sealed.mkdir(parents=True, exist_ok=True)
    (sealed / f"{name}.prompt.txt").write_text(prompt, encoding="utf-8")
    raw = run_probe_agent(workspace=live, prompt=prompt, timeout_seconds=TIMEOUT_SECONDS)
    agent = slim_agent(raw)
    dump(sealed / f"{name}.agent.json", agent)
    (sealed / f"{name}.stdout.txt").write_text((raw.get("stdout") or "")[-400000:], encoding="utf-8")
    check_agent(sealed, agent)
    return agent


def copy_if(live: Path, sealed: Path, name: str) -> None:
    src = live / name
    if src.exists():
        dest = sealed / name
        if src.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(src, dest)
        else:
            shutil.copy2(src, dest)


def proxy_stance_for_packet(packet: dict) -> str:
    lines = [
        "These are your private notes. They are experimental, not a statute book.",
        f"Issue: {packet['issue_id']}",
        packet["stance_summary"],
        "Distinctions you care about:",
    ]
    lines.extend(f"- {d}" for d in packet["distinctions"])
    if packet.get("must_not_accept"):
        lines.append("You will reject:")
        lines.extend(f"- {d}" for d in packet["must_not_accept"])
    if packet.get("uncertain_about"):
        lines.append("You are genuinely uncertain about: " + "; ".join(packet["uncertain_about"]))
    return "\n".join(lines) + "\n"


def proxy_stance_for_intervention(item: dict) -> str:
    if item.get("exact_utterance"):
        return (
            "Reply with exactly this sentence and nothing else:\n\n"
            + item["exact_utterance"]
            + "\n"
        )
    return (
        f"Kind of response: {item['kind']}\n"
        f"Epistemic intent: {item['epistemic']}\n"
        "Say this stance in your own words, naturally, without ontology jargon:\n\n"
        + item["stance"]
        + "\n"
    )


def run_proxy(sealed: Path, stance: str, host_message: str, name: str) -> dict:
    live = new_live_workspace()
    try:
        seed_proxy_workspace(live, stance=stance, host_message=host_message)
        preflight_isolation(live)
        agent = run_host(sealed, live, PROXY_PROMPT, name)
        copy_if(live, sealed, "REPLY.md")
        reply = (live / "REPLY.md").read_text(encoding="utf-8") if (live / "REPLY.md").exists() else agent.get("assistant_text") or ""
        dump(sealed / f"{name}.reply.json", {"reply": reply})
        return {"agent": agent, "reply": reply}
    finally:
        remove_live_workspace(live)


def rerun_construction(live: Path, sealed: Path) -> dict:
    clean = sealed / "clean_run"
    prepare_clean_run(live, clean)
    result = run_construction(clean)
    public = {
        "ok": result.get("ok"),
        "errors": result.get("errors"),
        "n_hole_groups": result.get("n_hole_groups"),
        "n_hole_instances": result.get("n_hole_instances"),
        "relation_row_counts": result.get("relation_row_counts"),
        "requirement_names": result.get("requirement_names"),
        "hole_groups": result.get("hole_groups"),
    }
    dump(sealed / "rerun_public.json", public)
    if (clean / "spine.json").exists():
        shutil.copy2(clean / "spine.json", sealed / "spine.json")
    if (clean / "holes.json").exists():
        shutil.copy2(clean / "holes.json", sealed / "holes.json")
    return public


def mp1_trial(index: int) -> dict:
    sealed = RUNS / "mp1" / f"T{index}"
    summary = sealed / "trial.json"
    if summary.exists():
        return json.loads(summary.read_text(encoding="utf-8"))
    live = new_live_workspace()
    try:
        seed_host_workspace(live)
        preflight = preflight_isolation(live)
        dump(sealed / "isolation_preflight.json", preflight)
        agent = run_host(sealed, live, MP1_PROMPT, "host")
        copy_if(live, sealed, "records")
        copy_if(live, sealed, "conversation")
        payload = {"trial": f"T{index}", "ok": True, "agent": {k: agent[k] for k in ("reported_model", "usage", "timed_out")}}
        dump(summary, payload)
        return payload
    finally:
        remove_live_workspace(live)


def mp2_cell(issue_id: str, condition: str) -> dict:
    sealed = RUNS / "mp2" / issue_id / condition
    summary = sealed / "cell.json"
    if summary.exists():
        return json.loads(summary.read_text(encoding="utf-8"))
    live = new_live_workspace()
    try:
        seed_host_workspace(live, issue_ids=[issue_id])
        (live / "FOCUS.md").write_text(f"Focus issue: {issue_id}\n", encoding="utf-8")
        preflight_isolation(live)
        prompt = MP2_OPEN_PROMPT if condition == "OPEN" else MP2_NEAR_PROMPT
        agent = run_host(sealed, live, prompt, "host")
        copy_if(live, sealed, "USER_MESSAGE.md")
        host_msg = (
            (live / "USER_MESSAGE.md").read_text(encoding="utf-8")
            if (live / "USER_MESSAGE.md").exists()
            else agent.get("assistant_text") or ""
        )
        dump(sealed / "host_message.json", {"text": host_msg})
        packet = PACKETS[issue_id]
        dump(sealed / "packet_id.json", {"issue_id": issue_id, "note": "packet body not copied to host"})
        proxy = run_proxy(sealed, proxy_stance_for_packet(packet), host_msg, "proxy")
        payload = {
            "issue_id": issue_id,
            "condition": condition,
            "host_message": host_msg,
            "proxy_reply": proxy["reply"],
            "reported_model": agent.get("reported_model"),
        }
        dump(summary, payload)
        return payload
    finally:
        remove_live_workspace(live)


def mp3_trial(name: str) -> dict:
    sealed = RUNS / "mp3" / name
    summary = sealed / "trial.json"
    if summary.exists():
        return json.loads(summary.read_text(encoding="utf-8"))
    live = new_live_workspace()
    history: list[dict] = []
    try:
        seed_host_workspace(live)
        preflight_isolation(live)
        baseline = rerun_construction(live, sealed / "baseline")
        original_construction = (live / "construction.py").read_text(encoding="utf-8")
        (sealed / "construction.original.py").write_text(original_construction, encoding="utf-8")
        for item in INTERVENTIONS[name]:
            step = sealed / item["id"]
            step.mkdir(parents=True, exist_ok=True)
            (live / "FOCUS.md").write_text(f"Focus issue: {item['issue_id']}\nKind expected from user is unknown to you.\n", encoding="utf-8")
            explain = run_host(step, live, MP3_EXPLAIN_PROMPT, "explain")
            copy_if(live, step, "USER_MESSAGE.md")
            host_msg = (
                (live / "USER_MESSAGE.md").read_text(encoding="utf-8")
                if (live / "USER_MESSAGE.md").exists()
                else explain.get("assistant_text") or ""
            )
            proxy = run_proxy(step, proxy_stance_for_intervention(item), host_msg, "proxy1")
            (live / "USER_REPLY.md").write_text(proxy["reply"], encoding="utf-8")
            shutil.copy2(live / "USER_REPLY.md", step / "USER_REPLY.md")
            revise = run_host(step, live, MP3_REVISE_PROMPT, "revise")
            copy_if(live, step, "INTERPRETATION.json")
            copy_if(live, step, "CLARIFY.md")
            copy_if(live, step, "CONSEQUENCE.md")
            copy_if(live, step, "construction.py")
            n_turns = 2
            if (live / "CLARIFY.md").exists() and item["id"] == "H3_bare_no":
                follow = run_proxy(step, FOLLOWUP_AFTER_BARE_NO, (live / "CLARIFY.md").read_text(encoding="utf-8"), "proxy2")
                (live / "USER_REPLY.md").write_text(follow["reply"], encoding="utf-8")
                shutil.copy2(live / "USER_REPLY.md", step / "USER_REPLY2.md")
                run_host(step, live, MP3_AFTER_CLARIFY_PROMPT, "after_clarify")
                copy_if(live, step, "INTERPRETATION.json")
                copy_if(live, step, "CONSEQUENCE.md")
                copy_if(live, step, "construction.py")
                n_turns = 3
            elif (live / "CLARIFY.md").exists():
                follow = run_proxy(step, proxy_stance_for_intervention(item), (live / "CLARIFY.md").read_text(encoding="utf-8"), "proxy2")
                (live / "USER_REPLY.md").write_text(follow["reply"], encoding="utf-8")
                run_host(step, live, MP3_AFTER_CLARIFY_PROMPT, "after_clarify")
                copy_if(live, step, "construction.py")
                n_turns = 3
            public = rerun_construction(live, step / "rerun")
            new_code = (live / "construction.py").read_text(encoding="utf-8") if (live / "construction.py").exists() else ""
            interp = {}
            if (step / "INTERPRETATION.json").exists():
                try:
                    interp = json.loads((step / "INTERPRETATION.json").read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    interp = {"raw": (step / "INTERPRETATION.json").read_text(encoding="utf-8")[:4000]}
            history.append(
                {
                    "id": item["id"],
                    "kind": item["kind"],
                    "issue_id": item["issue_id"],
                    "intended_scope": item["intended_scope"],
                    "epistemic": item["epistemic"],
                    "host_message": host_msg,
                    "user_utterance": proxy["reply"],
                    "host_interpretation": interp,
                    "n_turns": n_turns,
                    "construction_changed": new_code != original_construction and new_code != (history[-1].get("construction_after") if history else original_construction),
                    "construction_after": new_code,
                    "rerun": public,
                    "clarify": (step / "CLARIFY.md").exists(),
                }
            )
            original_construction = new_code or original_construction
        payload = {"trial": name, "baseline": baseline, "steps": [{k: v for k, v in s.items() if k != "construction_after"} for s in history]}
        dump(summary, payload)
        (sealed / "construction.final.py").write_text(original_construction, encoding="utf-8")
        return payload
    finally:
        remove_live_workspace(live)


def main() -> None:
    RUNS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    freeze_inputs()
    print("frozen", flush=True)
    mp1 = [mp1_trial(i) for i in range(1, N_MP1_TRIALS + 1)]
    dump(RUNS / "mp1.json", mp1)
    print("mp1 done", flush=True)
    mp2 = []
    for issue_id in ("unique_applicable_limit", "nodi_semantics", "permit_comments_when_discharging"):
        for condition in ("OPEN", "NEAR"):
            cell = mp2_cell(issue_id, condition)
            mp2.append(cell)
            print(f"mp2 {issue_id} {condition}", flush=True)
    dump(RUNS / "mp2.json", mp2)
    mp3 = [mp3_trial(name) for name in ("H1", "H2", "H3")]
    dump(RUNS / "mp3.json", mp3)
    dump(RUNS / "campaign.json", {"experiment_id": EXPERIMENT_ID, "finished_at": now(), "draft_trial": DRAFT_TRIAL})
    print("campaign sealed", flush=True)


if __name__ == "__main__":
    main()
