"""Evaluator scoring for B0/B1/B3/B4 against frozen semantic cards. Not shown to models."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from research.semantic_integration.domains.npdes.constructor_v3_1_1_untouched.score import (
    load_json,
    snapshot,
    walk_strings,
)
from research.semantic_integration.domains.npdes.prose_probe_v1.paths import FROZEN, V311

FULL = "FULL_OBLIGATION"
PARTIAL = "PARTIAL_OBLIGATION"
MISS = "MISS"


def load_frozen(name: str) -> Any:
    return json.loads((FROZEN / name).read_text(encoding="utf-8"))


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower())


def _has_any(blob: str, needles: list[str]) -> bool:
    return any(_norm(n) in blob for n in needles if n.strip())


def _has_all_groups(blob: str, groups: list[list[str]]) -> bool:
    for group in groups:
        if not _has_any(blob, group):
            return False
    return True


def score_text_against_card(text: str, card: dict) -> str:
    blob = _norm(text)
    markers = card.get("full_markers") or {}
    groups = markers.get("all_groups") or []
    any_needles = markers.get("any") or []
    if groups and _has_all_groups(blob, groups):
        if any_needles and not _has_any(blob, any_needles):
            # groups matched; optional any-needles are boosters, not required if groups already full
            return FULL
        return FULL
    # partial: any single required group matched, or partial_condition keywords
    if groups:
        matched = sum(1 for g in groups if _has_any(blob, g))
        if matched:
            return PARTIAL
    gid = card["gold_id"]
    weak = {
        "S-FARM-TDS-STAGE": ["tds", "net increase", "70295"],
        "S-FARM-CN-SCHEDULE": ["cyanide"],
        "S-FARM-TRC-CONDITIONAL": ["trc", "chlorine", "uv"],
        "S-FARM-REPORT-ONLY": ["report"],
        "S-AZTEC-WHEN-DISCHARGING": ["discharg"],
        "S-AZTEC-REPORT-ONLY": ["report"],
        "S-AZTEC-WET-SEASONAL": ["wet"],
        "S-AZTEC-DELTA-BHC": ["bhc"],
        "S-GCC-EVENT-DISCHARGE": ["storm", "artesian"],
        "S-GCC-REPORT-ONLY": ["report"],
        "S-GCC-WET-FIRST-DISCHARGE": ["wet"],
        "S-SOURCE-AUTHORITY": ["fact sheet", "statement of basis"],
    }
    if _has_any(blob, weak.get(gid, [])):
        return PARTIAL
    return MISS


def obligation_blob(item: Any) -> str:
    if isinstance(item, dict):
        return walk_strings(item)
    return str(item or "")


def score_b0_trial(trial: int, cards: list[dict]) -> dict:
    obligations = load_json(snapshot(trial, "p3") / "03_obligations.json")
    if isinstance(obligations, dict):
        items = obligations.get("obligations") or obligations.get("items") or []
    else:
        items = obligations or []
    rows = []
    for card in cards:
        best = MISS
        examples = []
        for item in items:
            grade = score_text_against_card(obligation_blob(item), card)
            rank = {MISS: 0, PARTIAL: 1, FULL: 2}
            if rank[grade] > rank[best]:
                best = grade
            if grade != MISS and len(examples) < 3:
                if isinstance(item, dict):
                    examples.append(
                        {
                            "obligation_id": item.get("obligation_id"),
                            "relation": item.get("relation"),
                            "why_demanded": str(item.get("why_demanded") or "")[:400],
                            "grade": grade,
                        }
                    )
        rows.append(
            {
                "gold_id": card["gold_id"],
                "grade": best,
                "hit": best in {FULL, PARTIAL},
                "full": best == FULL,
                "examples": examples,
            }
        )
    n = len(cards)
    full_n = sum(1 for r in rows if r["full"])
    rec_n = sum(1 for r in rows if r["hit"])
    return {
        "trial": trial,
        "n_obligations": len(items),
        "per_seam": rows,
        "full_recall": full_n / n if n else None,
        "full_or_partial_recall": rec_n / n if n else None,
        "n_full": full_n,
        "n_partial_or_full": rec_n,
    }


def score_b0() -> dict:
    cards = load_frozen("semantic_cards.json")
    trials = [score_b0_trial(i, cards) for i in range(1, 6)]
    fulls = [t["full_recall"] for t in trials]
    mean_full = sum(fulls) / len(fulls)
    per_seam = {}
    for card in cards:
        gid = card["gold_id"]
        grades = []
        for t in trials:
            row = next(r for r in t["per_seam"] if r["gold_id"] == gid)
            grades.append(row["grade"])
        per_seam[gid] = {
            "grades": grades,
            "full_recall": sum(g == FULL for g in grades) / 5,
            "full_or_partial_recall": sum(g != MISS for g in grades) / 5,
            "stability": dict(Counter(grades)),
        }
    return {
        "condition": "B0",
        "trials": trials,
        "per_seam": per_seam,
        "mean_full_recall": mean_full,
        "mean_full_or_partial_recall": sum(t["full_or_partial_recall"] for t in trials) / 5,
        "stability_across_trials": {
            "full_recalls": fulls,
            "range": [min(fulls), max(fulls)],
        },
    }


def score_obligation_output(payload: Any, card: dict) -> str:
    if payload is None:
        return MISS
    if isinstance(payload, list):
        text = walk_strings(payload)
        kinds = [p.get("kind") for p in payload if isinstance(p, dict)]
        if kinds and all(k == "NO_RELEVANT_OBLIGATION" for k in kinds):
            return MISS
        return score_text_against_card(text, card)
    if isinstance(payload, dict):
        kind = str(payload.get("kind") or "")
        if kind == "NO_RELEVANT_OBLIGATION":
            return MISS
        if "candidates" in payload and not payload.get("question"):
            return score_text_against_card(walk_strings(payload), card)
        return score_text_against_card(walk_strings(payload), card)
    return score_text_against_card(str(payload), card)


def nomination_needles() -> dict[str, list[str]]:
    pas = load_frozen("passages.json")
    out: dict[str, list[str]] = {}
    for gid, spec in pas["positives"].items():
        needles = []
        for span in spec.get("spans") or []:
            excerpt = _norm(span.get("exact_span") or "")
            if excerpt:
                needles.append(excerpt[:180])
        for span in spec.get("paired_spans") or []:
            excerpt = _norm(span.get("exact_span") or "")
            if excerpt:
                needles.append(excerpt[:180])
        out[gid] = needles
    return out


def _doc_aliases(document: str) -> set[str]:
    base = document.replace(".txt", "").replace(".pdf", "")
    return {document, base, base + ".pdf", base + ".txt", document.replace("farmington/", "").replace("aztec/", "").replace("gcc/", "")}


def candidate_matches_gold(candidate: dict, gold_id: str, pas: dict) -> bool:
    spec = pas["positives"][gold_id]
    cand_src = _norm(str(candidate.get("source") or "") + " " + str(candidate.get("locator") or ""))
    cand_span = _norm(str(candidate.get("exact_span") or "") + " " + str(candidate.get("computation_change_reason") or ""))
    blob = cand_src + " " + cand_span
    docs = [spec["document"]] + [s["document"] for s in spec.get("paired_spans") or []]
    page_hit = False
    for span in (spec.get("spans") or []) + (spec.get("paired_spans") or []):
        doc = span["document"]
        aliases = _doc_aliases(doc)
        loc_ok = any(_norm(a) in cand_src or _norm(a).split("/")[-1] in cand_src for a in aliases)
        if loc_ok and candidate.get("locator") and str(span["page"]) in str(candidate.get("locator")):
            page_hit = True
        excerpt = _norm(span.get("exact_span") or "")
        if excerpt and excerpt[:80] in blob:
            return True
        # distinctive tokens from excerpt
        if loc_ok and excerpt:
            tokens = [t for t in excerpt.split() if len(t) > 6][:4]
            if tokens and all(t in blob for t in tokens[:2]):
                return True
    if page_hit and any(tok in blob for tok in ["*10", "*11", "when discharging", "delta-bhc", "first discharge", "report", "chlorine", "springtime"]):
        return True
    return False


def candidate_matches_negative(candidate: dict, gold_id: str, pas: dict) -> bool:
    blob = _norm(
        str(candidate.get("source") or "")
        + " "
        + str(candidate.get("locator") or "")
        + " "
        + str(candidate.get("exact_span") or "")
    )
    for span in pas["negatives"].get(gold_id) or []:
        excerpt = _norm(span.get("exact_span") or "")
        if excerpt and excerpt[:60] in blob:
            return True
        aliases = _doc_aliases(span["document"])
        loc_ok = any(_norm(a).split("/")[-1] in blob for a in aliases)
        if loc_ok and str(span["page"]) in str(candidate.get("locator") or "") and excerpt:
            tokens = [t for t in excerpt.split() if len(t) > 5][:3]
            if tokens and all(t in blob for t in tokens[:2]):
                return True
    return False


def parse_disposition(payload: Any) -> dict:
    row = None
    if isinstance(payload, list) and payload:
        row = payload[0] if isinstance(payload[0], dict) else None
    elif isinstance(payload, dict):
        if "disposition" in payload:
            row = payload
        elif isinstance(payload.get("dispositions"), list) and payload["dispositions"]:
            row = payload["dispositions"][0]
    if not row:
        return {"disposition": None, "grounding": None, "rationale": None, "raw": payload}
    disp = str(row.get("disposition") or "").upper()
    if "UNRESOLVED" in disp:
        disp = "UNRESOLVED"
    elif "ACCEPT" in disp or "SAME" in disp:
        disp = "ACCEPT"
    elif "REJECT" in disp or "DISTINCT" in disp:
        disp = "REJECT"
    return {
        "disposition": disp or None,
        "grounding": row.get("grounding"),
        "rationale": row.get("rationale"),
        "raw": row,
    }


def score_b2_row(gold_id: str, parsed: dict, expected: dict) -> dict:
    spec = expected[gold_id]
    disp = parsed.get("disposition")
    grounding = parsed.get("grounding")
    has_grounding = bool(grounding)
    safe = disp in spec["safe"] if disp else False
    unsupported = False
    if disp in {"ACCEPT", "REJECT"} and not has_grounding:
        unsupported = True
    # heuristic: closing with ACCEPT/REJECT contrary to listed unsupported pattern is flagged in report, not auto
    return {
        "gold_id": gold_id,
        "disposition": disp,
        "safe": safe and not unsupported,
        "correct_or_legitimate_unresolved": safe and not unsupported,
        "unsupported_closure": unsupported,
        "grounding_present": has_grounding,
        "correct_under_closure": disp == "UNRESOLVED" and "UNRESOLVED" in spec["safe"],
    }
