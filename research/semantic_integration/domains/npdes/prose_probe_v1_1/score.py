"""Evaluator scoring for B4-lite and negative-control selectivity. Not shown to models."""

from __future__ import annotations

from typing import Any

from research.semantic_integration.domains.npdes.prose_probe_v1.score import (
    FULL,
    MISS,
    PARTIAL,
    score_obligation_output,
)

NO_RELEVANT = "NO_RELEVANT_OBLIGATION"
FULL_SPURIOUS = "FULL_SPURIOUS_OBLIGATION"
WEAK_SPURIOUS = "PARTIAL_WEAK_OBLIGATION"
PARSE_FAIL = "PARSE_FAIL"


def normalize_obligation(payload: Any) -> dict | None:
    if payload is None:
        return None
    if isinstance(payload, list):
        if not payload:
            return None
        payload = payload[0]
    if not isinstance(payload, dict):
        return None
    if "payload" in payload and isinstance(payload["payload"], dict):
        payload = payload["payload"]
    kind = str(payload.get("kind") or "")
    question = payload.get("question_or_proposition")
    if question is None:
        question = payload.get("question")
    required = payload.get("required_context")
    if required is None:
        required = payload.get("semantic_arguments")
    return {
        "kind": kind or ("OBLIGATION" if question else ""),
        "affected_purpose": payload.get("affected_purpose"),
        "question_or_proposition": question,
        "required_context": required,
        "source_locator": payload.get("source_locator"),
        "notes": payload.get("notes"),
        "raw": payload,
    }


def is_no_relevant(payload: Any) -> bool:
    row = normalize_obligation(payload)
    if not row:
        return False
    kind = str(row.get("kind") or "").upper().replace(" ", "_")
    return "NO_RELEVANT" in kind


def is_obligation(payload: Any) -> bool:
    row = normalize_obligation(payload)
    if not row:
        return False
    if is_no_relevant(payload):
        return False
    kind = str(row.get("kind") or "").upper()
    if "OBLIGATION" in kind:
        return True
    q = str(row.get("question_or_proposition") or "").strip()
    return bool(q)


def score_gold_payload(payload: Any, card: dict) -> str:
    if payload is None:
        return MISS
    if is_no_relevant(payload):
        return MISS
    # reuse v1 B1 rubric (walks all strings, including question_or_proposition)
    return score_obligation_output(payload, card)


def score_negative_payload(payload: Any) -> str:
    if payload is None:
        return PARSE_FAIL
    if is_no_relevant(payload):
        return NO_RELEVANT
    if not is_obligation(payload):
        return PARSE_FAIL
    row = normalize_obligation(payload) or {}
    question = str(row.get("question_or_proposition") or "").strip()
    purpose = str(row.get("affected_purpose") or "").strip()
    if len(question) >= 40 and purpose:
        return FULL_SPURIOUS
    return WEAK_SPURIOUS


def best_grade(grades: list[str]) -> str:
    rank = {MISS: 0, PARTIAL: 1, FULL: 2}
    best = MISS
    for g in grades:
        if rank.get(g, 0) > rank[best]:
            best = g
    return best


def p5_negative_row(parsed: dict) -> dict:
    disp = parsed.get("disposition")
    grounding = parsed.get("grounding")
    has_grounding = bool(grounding)
    unsupported = bool(disp in {"ACCEPT", "REJECT"} and not has_grounding)
    propagated = disp == "ACCEPT"
    return {
        "disposition": disp,
        "grounding_present": has_grounding,
        "unsupported_closure": unsupported,
        "negative_propagated_closure": propagated,
        "safe": disp == "UNRESOLVED" or (disp == "REJECT" and has_grounding and not unsupported),
    }
