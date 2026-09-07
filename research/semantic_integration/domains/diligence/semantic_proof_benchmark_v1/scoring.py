"""Probe A metrics. Oracle is evaluator-only and never copied into workspaces."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from statistics import median
from typing import Any

from research.semantic_integration.domains.diligence.pass_localization.pairs import pair_key
from research.semantic_integration.domains.diligence.semantic_proof_benchmark_v1.paths import HIDDEN
from research.semantic_integration.domains.diligence.semantic_proof_benchmark_v1.parse import (
    evidence_in_packet,
)

COMMITTED = {"SAME_ENTITY", "DISTINCT"}


def oracle_pairs() -> dict[tuple[str, str], str]:
    payload = json.loads((HIDDEN / "annotations" / "identity_dispositions.json").read_text())
    out: dict[tuple[str, str], str] = {}
    mapping = {
        "SAME_ENTITY": "same_entity",
        "DISTINCT": "distinct",
        "UNRESOLVED": "unresolved",
    }
    for kind, key in mapping.items():
        for left, right in payload[key]:
            out[pair_key(left, right)] = kind
    return out


def score_row(row: dict[str, Any], packet: dict[str, Any], oracle: dict[tuple[str, str], str]) -> dict[str, Any]:
    cand = row.get("candidate") or {}
    key = pair_key(str(cand.get("left") or ""), str(cand.get("right") or ""))
    want = oracle.get(key)
    got = str(row.get("final_disposition") or "UNRESOLVED").upper()
    proposed = str(row.get("proposed_disposition") or got).upper()
    grounding_ok = evidence_in_packet(row.get("supporting_evidence"), packet)
    proof_valid = bool(row.get("proof_valid", True))
    proof_size = int(row.get("proof_size") or 0)
    return {
        **row,
        "oracle": want,
        "in_oracle": want is not None,
        "exact": want == got if want else False,
        "unsupported_closure": bool(want == "UNRESOLVED" and got in COMMITTED),
        "under_closure": bool(want in COMMITTED and got == "UNRESOLVED"),
        "polarity": {want, got} == {"SAME_ENTITY", "DISTINCT"},
        "grounding_valid": grounding_ok,
        "proof_valid": proof_valid,
        "proof_size": proof_size,
        "proposed_wrong_caught": bool(
            proposed != want and proposed in COMMITTED and got == "UNRESOLVED" and want != proposed
        ),
        "correct_downgraded": bool(proposed == want and want in COMMITTED and got == "UNRESOLVED"),
        "correct_same_never_proposed": bool(want == "SAME_ENTITY" and proposed != "SAME_ENTITY"),
    }


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    scored = [r for r in rows if r.get("in_oracle")]
    n = len(scored)
    committed = [r for r in scored if r.get("final_disposition") in COMMITTED]
    unsupported = [r for r in scored if r.get("unsupported_closure")]
    confusion: dict[str, dict[str, int]] = {"SAME_ENTITY": {}, "DISTINCT": {}, "UNRESOLVED": {}}
    for row in scored:
        want = row["oracle"]
        got = row["final_disposition"]
        confusion.setdefault(want, {})
        confusion[want][got] = confusion[want].get(got, 0) + 1

    def recall(kind: str) -> float | None:
        gold = [r for r in scored if r["oracle"] == kind]
        if not gold:
            return None
        return sum(1 for r in gold if r["final_disposition"] == kind) / len(gold)

    sizes = [int(r.get("proof_size") or 0) for r in scored]
    return {
        "compared": n,
        "exact": sum(1 for r in scored if r.get("exact")),
        "exact_accuracy": (sum(1 for r in scored if r.get("exact")) / n) if n else None,
        "unsupported_closures": len(unsupported),
        "semantic_risk": (len(unsupported) / len(committed)) if committed else 0.0,
        "semantic_coverage": (len(committed) / n) if n else None,
        "committed": len(committed),
        "SAME_recall": recall("SAME_ENTITY"),
        "DISTINCT_recall": recall("DISTINCT"),
        "UNRESOLVED_recall": recall("UNRESOLVED"),
        "under_closure": sum(1 for r in scored if r.get("under_closure")),
        "polarity_errors": sum(1 for r in scored if r.get("polarity")),
        "grounding_validity": (sum(1 for r in scored if r.get("grounding_valid")) / n) if n else None,
        "proof_validity": (sum(1 for r in scored if r.get("proof_valid")) / n) if n else None,
        "mean_proof_size": (sum(sizes) / len(sizes)) if sizes else None,
        "median_proof_size": (float(median(sizes)) if sizes else None),
        "adjudicator_proposed_wrong_caught": sum(1 for r in scored if r.get("proposed_wrong_caught")),
        "correct_closure_incorrectly_downgraded": sum(1 for r in scored if r.get("correct_downgraded")),
        "correct_SAME_never_proposed": sum(1 for r in scored if r.get("correct_same_never_proposed")),
        "confusion": confusion,
        "isolation_leaks": sum(len(r.get("isolation_leaks") or []) for r in rows),
    }


def write_strategy_scores(strategy: str, rows: list[dict[str, Any]], dest: Path) -> dict[str, Any]:
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "judgments.json").write_text(json.dumps(rows, indent=2) + "\n")
    payload = aggregate(rows)
    payload["strategy"] = strategy
    (dest / "risk_coverage.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return payload
