"""Score the E2E programmability probe from machine artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from research.semantic_integration.domains.npdes.end_to_end_programmability_v0.leakage import audit_consumers
from research.semantic_integration.domains.npdes.end_to_end_programmability_v0.paths import (
    FRESH,
    RUNS,
)


def score() -> dict:
    det = json.loads((RUNS / "deterministic.json").read_text(encoding="utf-8"))
    leakage = audit_consumers()
    det["leakage"] = leakage
    (RUNS / "deterministic.json").write_text(json.dumps(det, indent=2, default=str) + "\n", encoding="utf-8")
    fresh = json.loads((FRESH / "campaign.json").read_text(encoding="utf-8"))
    a = det["summaries"]["state_a"]
    b = det["summaries"]["state_b"]
    c = det["summaries"]["state_c"]
    world_only = all(det["summaries"][s].get("world_only") for s in ("state_a", "state_b", "state_c"))
    rewrite = det["consumer_rewrite_count"]
    nodi_ok = (
        c["n_nodi_c_cases"] == 150
        and c["n_nodi_9_cases"] == 36
        and c["n_nodi_c_or_9_with_unresolved_semantics"] == 186
        and c["comparison_status"].get("EXCEEDANCE", 0) == a["comparison_status"].get("EXCEEDANCE", 0)
    )
    fail = det["failure_path"]
    reopen_ok = all(v.get("REOPEN_WITHOUT_RECONSTRUCTION") for v in det["reopen"].values())
    a_to_b = det["diffs"]["a_to_b"]
    b_to_c = det["diffs"]["b_to_c"]
    answers_a = (FRESH / "state_a" / "ANSWERS.md").read_text(encoding="utf-8")
    answers_c = (FRESH / "state_c" / "ANSWERS.md").read_text(encoding="utf-8")
    invented = any(
        tok in (answers_a + answers_c).lower()
        for tok in ("nodi c means", "no discharge indicator", "closed facility", "inundation")
    )
    agent_cells = {
        "state_a": {
            "Q1": "CORRECT_FROM_WORLD",
            "Q2": "CORRECT_FROM_WORLD",
            "Q3": "PARTIAL_FROM_WORLD",
            "note": "Q3 treated T5 conditional_discharge hole prose as already-established condition meaning; compiled monitoring_condition does not exist on State A.",
        },
        "state_c": {
            "Q1": "CORRECT_FROM_WORLD",
            "Q2": "CORRECT_FROM_WORLD",
            "Q3": "CORRECT_FROM_WORLD",
            "note": "Used monitoring_condition=discharge_occurrence and discharge_occurrence_in_period; NODI left uninterpreted; pass_fail_outcome_reporting used.",
        },
    }
    strong = (
        world_only
        and rewrite == 0
        and leakage["consumer_semantic_leakage"] in {"NONE", "LOW"}
        and a_to_b["semantic_to_factual"] > 0
        and b_to_c["pass_fail_classified"] > 0
        and nodi_ok
        and fail["FAILED_CANDIDATE_PRESERVES_ACCEPTED"]
        and fail["FAILED_CANDIDATE_PRESERVES_APPLICATION_OUTPUT"]
        and reopen_ok
        and not invented
        and fresh["state_a"]["reported_model"] == "Composer 2.5"
        and fresh["state_c"]["reported_model"] == "Composer 2.5"
    )
    label = "END_TO_END_PROGRAMMABILITY_SUPPORTED" if strong else "MIXED_END_TO_END_PROGRAMMABILITY_RESULT"
    payload = {
        "label": label,
        "world_only": world_only,
        "consumer_rewrite_count": rewrite,
        "leakage": leakage["consumer_semantic_leakage"],
        "a_to_b": a_to_b,
        "b_to_c": b_to_c,
        "nodi_unresolved_honest": nodi_ok,
        "n_exceedance_stable": a["n_exceedance"] == b["n_exceedance"] == c["n_exceedance"],
        "failure_path": fail,
        "reopen_ok": reopen_ok,
        "fresh_agent": agent_cells,
        "invented_nodi": invented,
        "state_d": "skipped",
        "model": "Composer 2.5",
    }
    RUNS.mkdir(parents=True, exist_ok=True)
    (RUNS / "score.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


if __name__ == "__main__":
    print(json.dumps(score(), indent=2))
