"""Probe A inference runner. One candidate + one packet per isolated call. Resumable."""

from __future__ import annotations

import json
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from research.semantic_integration.domains.diligence.semantic_proof_benchmark_v1.admit import (
    a2_apply_critic,
    a3_admit,
    a4_admit,
    a5_admit,
    a6_admit,
)
from research.semantic_integration.domains.diligence.semantic_proof_benchmark_v1.agent import (
    isolation_leaks,
    run_probe_agent,
)
from research.semantic_integration.domains.diligence.semantic_proof_benchmark_v1.apparatus import (
    freeze_apparatus,
    load_obligations,
    packet_path,
)
from research.semantic_integration.domains.diligence.semantic_proof_benchmark_v1.isolation import (
    new_live_workspace,
    preflight_isolation,
    remove_live_workspace,
)
from research.semantic_integration.domains.diligence.semantic_proof_benchmark_v1.parse import (
    canon_disp,
    evidence_in_packet,
    load_json,
)
from research.semantic_integration.domains.diligence.semantic_proof_benchmark_v1.paths import (
    APPARATUS,
    REPO,
    STRATEGIES,
)
from research.semantic_integration.domains.diligence.semantic_proof_benchmark_v1.prompts import (
    INFERENCE_STRATEGIES,
    PROMPTS,
    TIMEOUT_SECONDS,
)
from research.semantic_integration.domains.diligence.semantic_proof_benchmark_v1.scoring import (
    oracle_pairs,
    score_row,
    write_strategy_scores,
)

N_REPLICATIONS = 5


def sealed_dir(strategy: str, replication: int, obligation_id: str) -> Path:
    return STRATEGIES / strategy / f"R{replication:02d}" / obligation_id


def seed_workspace(dest: Path, obligation: dict, extra: dict[str, Any] | None = None) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    oid = obligation["obligation_id"]
    shutil.copy2(packet_path(oid), dest / "packet.json")
    shutil.copy2(APPARATUS / "relation_contract.json", dest / "relation_contract.json")
    candidate = {
        "obligation_id": oid,
        "left": obligation["values"]["left"],
        "right": obligation["values"]["right"],
        "relation": obligation.get("relation"),
    }
    (dest / "candidate.json").write_text(json.dumps(candidate, indent=2) + "\n")
    (dest / "README.md").write_text("Probe A bounded packet. No other sources.\n")
    if extra:
        for name, payload in extra.items():
            (dest / name).write_text(json.dumps(payload, indent=2) + "\n")


def run_call(workspace: Path, prompt: str) -> dict[str, Any]:
    preflight = preflight_isolation(workspace)
    agent = run_probe_agent(workspace=workspace, prompt=prompt, timeout_seconds=TIMEOUT_SECONDS)
    leaks = isolation_leaks(agent.get("events") or [], REPO)
    return {"agent": agent, "leaks": leaks, "preflight": preflight}


def persist_agent(sealed: Path, name: str, bundle: dict[str, Any]) -> None:
    agent = bundle["agent"]
    stdout = agent.get("stdout") or ""
    if isinstance(stdout, bytes):
        stdout = stdout.decode("utf-8", errors="replace")
    if len(stdout) > 2_000_000:
        stdout = stdout[-2_000_000:]
    try:
        (sealed / f"{name}.stdout.txt").write_text(stdout)
    except OSError:
        (sealed / f"{name}.stdout.txt").write_text("[truncated: write failed]\n")
    (sealed / f"{name}.json").write_text(
        json.dumps(
            {
                "model": agent.get("model"),
                "reported_model": agent.get("reported_model"),
                "timed_out": agent.get("timed_out"),
                "returncode": agent.get("returncode"),
                "usage": agent.get("usage"),
                "tools": agent.get("tools"),
                "isolation_leaks": bundle["leaks"],
                "isolation_preflight": bundle["preflight"],
                "finished_at": datetime.now(timezone.utc).isoformat(),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def finalize_row(
    *,
    strategy: str,
    replication: int,
    obligation: dict,
    proposed: str,
    final: str,
    evidence: Any,
    claim: str,
    packet: dict,
    proof_size: int,
    proof_valid: bool,
    leaks: list[str],
    extra: dict[str, Any],
) -> dict[str, Any]:
    row = {
        "strategy": strategy,
        "trial": f"R{replication:02d}",
        "obligation_id": obligation["obligation_id"],
        "candidate": {"left": obligation["values"]["left"], "right": obligation["values"]["right"]},
        "proposed_disposition": canon_disp(proposed),
        "final_disposition": canon_disp(final),
        "supporting_evidence": evidence,
        "support_claim": claim,
        "proof_size": proof_size,
        "proof_valid": proof_valid,
        "isolation_leaks": leaks,
        **extra,
    }
    return score_row(row, packet, oracle_pairs())


def run_a1(obligation: dict, replication: int) -> dict[str, Any]:
    sealed = sealed_dir("a1_single", replication, obligation["obligation_id"])
    if (sealed / "row.json").exists():
        return json.loads((sealed / "row.json").read_text())
    sealed.mkdir(parents=True, exist_ok=True)
    live = new_live_workspace()
    try:
        seed_workspace(live, obligation)
        bundle = run_call(live, PROMPTS["a1_single"]["adjudicator"])
        persist_agent(sealed, "adjudicator", bundle)
        shutil.copytree(live, sealed / "workspace", dirs_exist_ok=True)
        payload = load_json(live / "judgment.json") or {}
        packet = json.loads(packet_path(obligation["obligation_id"]).read_text())
        proposed = canon_disp(payload.get("disposition"))
        row = finalize_row(
            strategy="a1_single",
            replication=replication,
            obligation=obligation,
            proposed=proposed,
            final=proposed,
            evidence=payload.get("supporting_evidence"),
            claim=str(payload.get("support_claim") or ""),
            packet=packet,
            proof_size=1,
            proof_valid=evidence_in_packet(payload.get("supporting_evidence"), packet),
            leaks=bundle["leaks"],
            extra={"justification": payload.get("justification")},
        )
        (sealed / "row.json").write_text(json.dumps(row, indent=2) + "\n")
        return row
    finally:
        remove_live_workspace(live)


def run_a2(obligation: dict, replication: int) -> dict[str, Any]:
    sealed = sealed_dir("a2_critic", replication, obligation["obligation_id"])
    if (sealed / "row.json").exists():
        return json.loads((sealed / "row.json").read_text())
    sealed.mkdir(parents=True, exist_ok=True)
    packet = json.loads(packet_path(obligation["obligation_id"]).read_text())
    leaks: list[str] = []
    live = new_live_workspace()
    try:
        seed_workspace(live, obligation)
        bundle = run_call(live, PROMPTS["a2_critic"]["adjudicator"])
        persist_agent(sealed, "adjudicator", bundle)
        leaks.extend(bundle["leaks"])
        proposal = load_json(live / "proposal.json") or load_json(live / "judgment.json") or {}
        shutil.copytree(live, sealed / "adjudicator_workspace", dirs_exist_ok=True)
        proposed = canon_disp(proposal.get("disposition"))
    finally:
        remove_live_workspace(live)

    live2 = new_live_workspace()
    try:
        seed_workspace(live2, obligation, extra={"proposal.json": proposal})
        bundle2 = run_call(live2, PROMPTS["a2_critic"]["critic"])
        persist_agent(sealed, "critic", bundle2)
        leaks.extend(bundle2["leaks"])
        critic = load_json(live2 / "critic.json") or {}
        shutil.copytree(live2, sealed / "critic_workspace", dirs_exist_ok=True)
        final, reason = a2_apply_critic(proposed, critic)
        row = finalize_row(
            strategy="a2_critic",
            replication=replication,
            obligation=obligation,
            proposed=proposed,
            final=final,
            evidence=proposal.get("supporting_evidence"),
            claim=str(proposal.get("support_claim") or ""),
            packet=packet,
            proof_size=2,
            proof_valid=evidence_in_packet(proposal.get("supporting_evidence"), packet),
            leaks=leaks,
            extra={"critic": critic, "critic_reason": reason},
        )
        (sealed / "row.json").write_text(json.dumps(row, indent=2) + "\n")
        return row
    finally:
        remove_live_workspace(live2)


def run_a3(obligation: dict, replication: int) -> dict[str, Any]:
    sealed = sealed_dir("a3_entailment", replication, obligation["obligation_id"])
    if (sealed / "row.json").exists():
        return json.loads((sealed / "row.json").read_text())
    sealed.mkdir(parents=True, exist_ok=True)
    live = new_live_workspace()
    try:
        seed_workspace(live, obligation)
        bundle = run_call(live, PROMPTS["a3_entailment"]["adjudicator"])
        persist_agent(sealed, "adjudicator", bundle)
        shutil.copytree(live, sealed / "workspace", dirs_exist_ok=True)
        payload = load_json(live / "judgment.json") or {}
        packet = json.loads(packet_path(obligation["obligation_id"]).read_text())
        proposed = canon_disp(payload.get("disposition"))
        final, rule = a3_admit(payload)
        claims = payload.get("claims") if isinstance(payload.get("claims"), list) else []
        row = finalize_row(
            strategy="a3_entailment",
            replication=replication,
            obligation=obligation,
            proposed=proposed,
            final=final,
            evidence=payload.get("supporting_evidence"),
            claim=str(payload.get("support_claim") or ""),
            packet=packet,
            proof_size=len(claims),
            proof_valid=all(
                evidence_in_packet(c.get("supporting_evidence"), packet)
                for c in claims
                if isinstance(c, dict)
            ),
            leaks=bundle["leaks"],
            extra={"claims": claims, "admit": rule},
        )
        (sealed / "row.json").write_text(json.dumps(row, indent=2) + "\n")
        return row
    finally:
        remove_live_workspace(live)


def run_a4(obligation: dict, replication: int) -> dict[str, Any]:
    sealed = sealed_dir("a4_proof_obligation", replication, obligation["obligation_id"])
    if (sealed / "row.json").exists():
        return json.loads((sealed / "row.json").read_text())
    sealed.mkdir(parents=True, exist_ok=True)
    live = new_live_workspace()
    try:
        seed_workspace(live, obligation)
        bundle = run_call(live, PROMPTS["a4_proof_obligation"]["adjudicator"])
        persist_agent(sealed, "adjudicator", bundle)
        shutil.copytree(live, sealed / "workspace", dirs_exist_ok=True)
        payload = load_json(live / "judgment.json") or {}
        packet = json.loads(packet_path(obligation["obligation_id"]).read_text())
        proposed = canon_disp(payload.get("proposed_disposition") or payload.get("disposition"))
        final, rule = a4_admit(payload)
        obligations = payload.get("proof_obligations") if isinstance(payload.get("proof_obligations"), list) else []
        grounded = True
        for item in obligations:
            if isinstance(item, dict) and item.get("satisfied"):
                if not evidence_in_packet(item.get("evidence"), packet):
                    grounded = False
                    final = "UNRESOLVED"
                    rule = {"rule": "satisfied_obligation_ungrounded"}
        row = finalize_row(
            strategy="a4_proof_obligation",
            replication=replication,
            obligation=obligation,
            proposed=proposed,
            final=final,
            evidence=payload.get("supporting_evidence"),
            claim=str(payload.get("support_claim") or ""),
            packet=packet,
            proof_size=len(obligations),
            proof_valid=grounded,
            leaks=bundle["leaks"],
            extra={"proof_obligations": obligations, "admit": rule, "unsatisfied": payload.get("unsatisfied_obligations")},
        )
        (sealed / "row.json").write_text(json.dumps(row, indent=2) + "\n")
        return row
    finally:
        remove_live_workspace(live)


def run_a5(obligation: dict, replication: int) -> dict[str, Any]:
    sealed = sealed_dir("a5_pairwise", replication, obligation["obligation_id"])
    if (sealed / "row.json").exists():
        return json.loads((sealed / "row.json").read_text())
    sealed.mkdir(parents=True, exist_ok=True)
    packet = json.loads(packet_path(obligation["obligation_id"]).read_text())
    leaks: list[str] = []
    live = new_live_workspace()
    try:
        seed_workspace(live, obligation)
        bundle = run_call(live, PROMPTS["a5_pairwise"]["evidence"])
        persist_agent(sealed, "evidence", bundle)
        leaks.extend(bundle["leaks"])
        evidence_doc = load_json(live / "evidence.json") or {}
        shutil.copytree(live, sealed / "evidence_workspace", dirs_exist_ok=True)
        propositions = evidence_doc.get("propositions") if isinstance(evidence_doc.get("propositions"), list) else []
    finally:
        remove_live_workspace(live)

    live2 = new_live_workspace()
    try:
        seed_workspace(
            live2,
            obligation,
            extra={"evidence.json": {"propositions": propositions}},
        )
        # disposition step must not include packet
        (live2 / "packet.json").unlink(missing_ok=True)
        bundle2 = run_call(live2, PROMPTS["a5_pairwise"]["disposition"])
        persist_agent(sealed, "disposition", bundle2)
        leaks.extend(bundle2["leaks"])
        judgment = load_json(live2 / "judgment.json") or {}
        shutil.copytree(live2, sealed / "disposition_workspace", dirs_exist_ok=True)
        proposed = canon_disp(judgment.get("disposition"))
        final, rule = a5_admit(judgment, propositions)
        proof_valid = all(
            evidence_in_packet(p.get("source_grounding"), packet)
            for p in propositions
            if isinstance(p, dict)
        )
        if not proof_valid:
            final = "UNRESOLVED"
            rule = {"rule": "ungrounded_proposition"}
        row = finalize_row(
            strategy="a5_pairwise",
            replication=replication,
            obligation=obligation,
            proposed=proposed,
            final=final,
            evidence=[p.get("source_grounding") for p in propositions if isinstance(p, dict)],
            claim=str(judgment.get("support_claim") or ""),
            packet=packet,
            proof_size=len(propositions),
            proof_valid=proof_valid,
            leaks=leaks,
            extra={"propositions": propositions, "admit": rule},
        )
        (sealed / "row.json").write_text(json.dumps(row, indent=2) + "\n")
        return row
    finally:
        remove_live_workspace(live2)


def run_a6(obligation: dict, replication: int) -> dict[str, Any]:
    sealed = sealed_dir("a6_multistep", replication, obligation["obligation_id"])
    if (sealed / "row.json").exists():
        return json.loads((sealed / "row.json").read_text())
    sealed.mkdir(parents=True, exist_ok=True)
    live = new_live_workspace()
    try:
        seed_workspace(live, obligation)
        bundle = run_call(live, PROMPTS["a6_multistep"]["adjudicator"])
        persist_agent(sealed, "adjudicator", bundle)
        shutil.copytree(live, sealed / "workspace", dirs_exist_ok=True)
        payload = load_json(live / "judgment.json") or {}
        packet = json.loads(packet_path(obligation["obligation_id"]).read_text())
        proposed = canon_disp(payload.get("disposition"))
        final, rule = a6_admit(payload, packet)
        steps = payload.get("steps") if isinstance(payload.get("steps"), list) else []
        row = finalize_row(
            strategy="a6_multistep",
            replication=replication,
            obligation=obligation,
            proposed=proposed,
            final=final,
            evidence=payload.get("supporting_evidence"),
            claim=str(payload.get("support_claim") or ""),
            packet=packet,
            proof_size=len(steps),
            proof_valid=rule.get("rule") in {"steps_grounded", "unresolved"},
            leaks=bundle["leaks"],
            extra={"steps": steps, "admit": rule},
        )
        (sealed / "row.json").write_text(json.dumps(row, indent=2) + "\n")
        return row
    finally:
        remove_live_workspace(live)


HANDLERS = {
    "a1_single": run_a1,
    "a2_critic": run_a2,
    "a3_entailment": run_a3,
    "a4_proof_obligation": run_a4,
    "a5_pairwise": run_a5,
    "a6_multistep": run_a6,
}


def jobs_for(strategy: str, replications: int) -> list[tuple[str, int, dict]]:
    obligations = load_obligations()
    out = []
    for replication in range(1, replications + 1):
        for obligation in obligations:
            out.append((strategy, replication, obligation))
    return out


def run_strategy(strategy: str, *, replications: int = N_REPLICATIONS, workers: int = 4) -> dict:
    handler = HANDLERS[strategy]
    work = jobs_for(strategy, replications)
    rows: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(handler, obligation, replication): (replication, obligation["obligation_id"])
            for strategy_name, replication, obligation in work
        }
        for fut in as_completed(futures):
            key = futures[fut]
            try:
                rows.append(fut.result())
            except Exception as exc:
                replication, oid = key
                err_path = STRATEGIES / strategy / f"R{replication:02d}" / oid / "error.txt"
                err_path.parent.mkdir(parents=True, exist_ok=True)
                err_path.write_text(repr(exc))
                raise
    rows.sort(key=lambda r: (r.get("trial") or "", r.get("obligation_id") or ""))
    return write_strategy_scores(strategy, rows, STRATEGIES / strategy)


def run_all(*, replications: int = N_REPLICATIONS, workers: int = 4, strategies: tuple[str, ...] | None = None) -> dict:
    freeze_apparatus()
    from research.semantic_integration.domains.diligence.semantic_proof_benchmark_v1.a0 import import_a0

    results = {"a0_v2": import_a0()}
    chosen = strategies or INFERENCE_STRATEGIES
    for strategy in chosen:
        results[strategy] = run_strategy(strategy, replications=replications, workers=workers)
    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", choices=("a0_v2", *INFERENCE_STRATEGIES), default=None)
    parser.add_argument("--replications", type=int, default=N_REPLICATIONS)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    freeze_apparatus()
    if args.strategy == "a0_v2" or args.strategy is None:
        from research.semantic_integration.domains.diligence.semantic_proof_benchmark_v1.a0 import import_a0

        print(json.dumps(import_a0(), indent=2)[:2000])
    if args.strategy in HANDLERS:
        print(json.dumps(run_strategy(args.strategy, replications=args.replications, workers=args.workers), indent=2)[:4000])
    elif args.strategy is None:
        payload = run_all(replications=args.replications, workers=args.workers)
        print(json.dumps({k: v.get("semantic_risk") for k, v in payload.items()}, indent=2))
