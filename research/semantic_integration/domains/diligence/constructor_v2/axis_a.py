"""AXIS A: 10 isolated P5 trials on frozen identity packets."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from research.semantic_integration.domains.diligence.constructor_v2.agent import (
    MODEL,
    run_v2_agent,
)
from research.semantic_integration.domains.diligence.constructor_v2.axis_a_apparatus import (
    APPARATUS,
    oracle_pairs,
    write_apparatus,
)
from research.semantic_integration.domains.diligence.constructor_v2.isolation import (
    EXPERIMENT_ID,
    REPO,
    new_live_workspace,
    preflight_isolation,
    remove_live_workspace,
)
from research.semantic_integration.domains.diligence.constructor_v2.runtime.contracts import (
    contract_to_dict,
    IDENTITY_CONTRACT,
)
from research.semantic_integration.domains.diligence.constructor_v2.runtime.verifier import (
    admit,
    verify_identity_disposition,
)
from research.semantic_integration.domains.diligence.pass_localization.pairs import pair_key

ROOT = Path(__file__).resolve().parent
TRIALS = ROOT / "axis_a" / "trials"
N_TRIALS = 10
TIMEOUT = 1200

P5_PROMPT = """You are the bounded semantic adjudicator (Constructor v2, pass P5).

You receive:
- identity_contract.json
- obligations.json
- packets/<obligation_id>.json

For EACH obligation, read only that obligation and its packet. Do not invent candidates, relations, or purposes. Do not canonicalize referents. Do not search files outside packets/.

SAME_ENTITY requires evidence that establishes identity. Name similarity, compatibility, or lack of contradiction is insufficient.
DISTINCT requires evidence that establishes distinctness. Absence of identity evidence is insufficient.
If neither burden is met, UNRESOLVED is the correct successful output.
If the packet preserves multiple live candidates or says identity cannot be established, do not close SAME/DISTINCT.

Write judgments.json as a JSON list of:
{
  "obligation_id": "...",
  "proposition": {"left": "...", "right": "..."},
  "disposition": "SAME_ENTITY" | "DISTINCT" | "UNRESOLVED",
  "supporting_evidence": [{"source_path": "...", "location": "..."}],
  "support_claim": "one sentence: what the cited evidence establishes"
}

Judge every obligation. Do not read files outside this workspace.
"""


def isolation_leaks(events: list) -> list[str]:
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
        path = str((payload.get("args") or {}).get("path") or "")
        result = payload.get("result") or {}
        if path.startswith(repo) and isinstance(result, dict) and "success" in result:
            leaks.append(path)
    return leaks


def seed_axis_a_workspace(dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    write_apparatus()
    shutil.copytree(APPARATUS / "packets", dest / "packets")
    shutil.copy2(APPARATUS / "obligations.json", dest / "obligations.json")
    shutil.copy2(APPARATUS / "identity_contract.json", dest / "identity_contract.json")
    (dest / "README.md").write_text("AXIS A bounded identity adjudication. Packets only.\n")
    (dest / "P5_TASK.md").write_text(P5_PROMPT)


def load_judgments(path: Path) -> list[dict]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text())
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("judgments", "dispositions"):
            if isinstance(payload.get(key), list):
                return payload[key]
    return []


def apply_verifier(judgments: list[dict], packets_dir: Path) -> list[dict]:
    audit = []
    for row in judgments:
        prop = row.get("proposition") or row.get("values") or {}
        left = str(prop.get("left") or row.get("left") or "")
        right = str(prop.get("right") or row.get("right") or "")
        oid = str(row.get("obligation_id") or "")
        packet = {}
        ppath = packets_dir / f"{oid}.json"
        if ppath.exists():
            packet = json.loads(ppath.read_text())
        proposed = str(row.get("disposition") or "UNRESOLVED").upper()
        claim = str(row.get("support_claim") or "")
        verification = verify_identity_disposition(
            left=left, right=right, proposed=proposed, packet=packet, support_claim=claim
        )
        final = admit(proposed, verification)
        audit.append(
            {
                "candidate": {"left": left, "right": right},
                "packet": oid,
                "initial_disposition": proposed,
                "support_evidence": row.get("supporting_evidence"),
                "support_claim": claim,
                "verifier_result": verification.get("result"),
                "verifier_reason": verification.get("reason"),
                "final_disposition": final,
            }
        )
    return audit


def score_audit(audit: list[dict]) -> dict:
    oracle = {pair_key(a, b): k for a, b, k in oracle_pairs()}
    compared = 0
    exact = 0
    unsupported_closure = 0
    under_closure = 0
    polarity = 0
    verifier_changed = 0
    correct_downgraded = 0
    confusion = {"SAME_ENTITY": {}, "DISTINCT": {}, "UNRESOLVED": {}}
    for row in audit:
        cand = row["candidate"]
        key = pair_key(cand["left"], cand["right"])
        if key not in oracle:
            continue
        want = oracle[key]
        got = row["final_disposition"]
        initial = row["initial_disposition"]
        compared += 1
        confusion.setdefault(want, {})
        confusion[want][got] = confusion[want].get(got, 0) + 1
        if got == want:
            exact += 1
        if want == "UNRESOLVED" and got in {"SAME_ENTITY", "DISTINCT"}:
            unsupported_closure += 1
        if want in {"SAME_ENTITY", "DISTINCT"} and got == "UNRESOLVED":
            under_closure += 1
        if {want, got} == {"SAME_ENTITY", "DISTINCT"}:
            polarity += 1
        if initial != got:
            verifier_changed += 1
            if initial == want and got != want:
                correct_downgraded += 1
    return {
        "compared": compared,
        "exact": exact,
        "accuracy": (exact / compared) if compared else None,
        "unsupported_closure": unsupported_closure,
        "under_closure": under_closure,
        "polarity": polarity,
        "verifier_changed": verifier_changed,
        "correct_downgraded": correct_downgraded,
        "confusion": confusion,
    }


def run_trial(index: int) -> dict:
    sealed = TRIALS / f"T{index:02d}"
    sealed.mkdir(parents=True, exist_ok=True)
    if (sealed / "score.json").exists():
        return json.loads((sealed / "score.json").read_text())
    live = new_live_workspace()
    try:
        seed_axis_a_workspace(live)
        preflight = preflight_isolation(live)
        agent = run_v2_agent(workspace=live, prompt=P5_PROMPT, timeout_seconds=TIMEOUT)
        leaks = isolation_leaks(agent.get("events") or [])
        (sealed / "transcript.stdout.txt").write_text(agent["stdout"] or "")
        (sealed / "agent.json").write_text(
            json.dumps(
                {
                    "trial": index,
                    "model": agent["model"],
                    "reported_model": agent.get("reported_model"),
                    "timed_out": agent["timed_out"],
                    "isolation_leaks": leaks,
                    "isolation_preflight": preflight,
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        saved = sealed / "workspace"
        if saved.exists():
            shutil.rmtree(saved)
        shutil.copytree(live, saved)
        if leaks:
            raise RuntimeError(f"isolation failed AXIS A T{index}: {leaks}")
        judgments = load_judgments(saved / "judgments.json")
        audit = apply_verifier(judgments, saved / "packets")
        (sealed / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
        score = score_audit(audit)
        (sealed / "score.json").write_text(json.dumps(score, indent=2) + "\n")
        return score
    finally:
        remove_live_workspace(live)


def run_all() -> dict:
    write_apparatus()
    scores = {f"T{i:02d}": run_trial(i) for i in range(1, N_TRIALS + 1)}
    unsupported = sum(s.get("unsupported_closure") or 0 for s in scores.values())
    under = sum(s.get("under_closure") or 0 for s in scores.values())
    polarity = sum(s.get("polarity") or 0 for s in scores.values())
    exact = sum(s.get("exact") or 0 for s in scores.values())
    compared = sum(s.get("compared") or 0 for s in scores.values())
    verifier_changed = sum(s.get("verifier_changed") or 0 for s in scores.values())
    downgraded = sum(s.get("correct_downgraded") or 0 for s in scores.values())
    confusion: dict[str, dict[str, int]] = {"SAME_ENTITY": {}, "DISTINCT": {}, "UNRESOLVED": {}}
    for score in scores.values():
        for want, got_map in (score.get("confusion") or {}).items():
            for got, n in got_map.items():
                confusion.setdefault(want, {})
                confusion[want][got] = confusion[want].get(got, 0) + n
    payload = {
        "experiment_id": EXPERIMENT_ID,
        "axis": "A",
        "model": MODEL,
        "trials": scores,
        "aggregate": {
            "n_trials": N_TRIALS,
            "compared": compared,
            "exact": exact,
            "accuracy": (exact / compared) if compared else None,
            "unsupported_closure": unsupported,
            "under_closure": under,
            "polarity": polarity,
            "verifier_changed": verifier_changed,
            "correct_downgraded": downgraded,
            "confusion": confusion,
            "trials_with_unsupported_closure": [
                name for name, score in scores.items() if score.get("unsupported_closure")
            ],
        },
    }
    dest = ROOT / "axis_a"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "results.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return payload


if __name__ == "__main__":
    print(json.dumps(run_all(), indent=2, sort_keys=True)[:4000])
