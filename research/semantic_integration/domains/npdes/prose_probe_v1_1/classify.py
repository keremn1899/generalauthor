"""Evaluator-only locator classification of sealed B3 R1–R3 candidates.

Never shown to the model. GOLD vs NEGATIVE labels never enter participant workspaces.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from research.semantic_integration.domains.npdes.prose_probe_v1.score import load_frozen, _norm
from research.semantic_integration.domains.npdes.prose_probe_v1_1.paths import FROZEN, V1

GOLD = "GOLD_MATCH"
NEGATIVE = "NEGATIVE_CONTROL_MATCH"
OTHER = "OTHER"
REPS = (1, 2, 3)


def _doc_key(value: str) -> str:
    text = _norm(str(value or "")).replace("\\", "/").replace(".pdf", ".txt")
    return text


def document_matches(candidate: dict, document: str) -> bool:
    """Require the facility-qualified document, not a bare final_permit alias."""
    cand = _doc_key(
        " ".join(
            [
                str(candidate.get("_document") or ""),
                str(candidate.get("source") or ""),
            ]
        )
    )
    span = _doc_key(document)
    stem = span.replace(".txt", "")
    if not stem:
        return False
    return stem in cand


def page_matches(candidate: dict, page: int) -> bool:
    if candidate.get("_page") == page:
        return True
    loc = str(candidate.get("locator") or "")
    if re.search(rf"(?:page|p\.?)\s*{page}\b", loc, re.I):
        return True
    if re.search(rf"#p{page}\b", loc, re.I):
        return True
    return False


def span_overlaps(candidate_span: str, frozen_span: str) -> bool:
    a = _norm(candidate_span or "")
    b = _norm(frozen_span or "")
    if not a or not b:
        return False
    if len(b) <= 48:
        return b in a or (len(a) <= 48 and a in b)
    if b[:80] in a:
        return True
    if len(a) >= 24 and a[:80] in b:
        return True
    tokens = [t for t in b.split() if len(t) >= 5]
    if len(tokens) < 3:
        tokens = [t for t in b.split() if len(t) >= 3]
    if not tokens:
        return False
    hit = sum(1 for t in tokens if t in a)
    need = max(3, int(round(0.5 * len(tokens))))
    return hit >= need


def _spans_for(gold_id: str, pas: dict, *, negative: bool) -> list[dict]:
    if negative:
        return list(pas["negatives"].get(gold_id) or [])
    spec = pas["positives"][gold_id]
    return list(spec.get("spans") or []) + list(spec.get("paired_spans") or [])


def matching_gold_ids(candidate: dict, pas: dict, gold_ids: list[str]) -> list[str]:
    hits = []
    blob = str(candidate.get("exact_span") or "")
    for gid in gold_ids:
        for span in _spans_for(gid, pas, negative=False):
            if document_matches(candidate, span["document"]) and page_matches(candidate, span["page"]):
                if span_overlaps(blob, span.get("exact_span") or ""):
                    hits.append(gid)
                    break
    return hits


def matching_negative_ids(candidate: dict, pas: dict, gold_ids: list[str]) -> list[str]:
    hits = []
    blob = str(candidate.get("exact_span") or "")
    for gid in gold_ids:
        for span in _spans_for(gid, pas, negative=True):
            if document_matches(candidate, span["document"]) and page_matches(candidate, span["page"]):
                if span_overlaps(blob, span.get("exact_span") or ""):
                    hits.append(gid)
                    break
    return hits


def classify_candidate(candidate: dict, pas: dict, gold_ids: list[str]) -> dict[str, Any]:
    golds = matching_gold_ids(candidate, pas, gold_ids)
    negs = matching_negative_ids(candidate, pas, gold_ids)
    if golds:
        label = GOLD
    elif negs:
        label = NEGATIVE
    else:
        label = OTHER
    return {
        "label": label,
        "gold_ids": golds,
        "negative_ids": negs if label != GOLD else [],
    }


def classify_replicates(*, reps: tuple[int, ...] = REPS) -> dict[str, Any]:
    pas = load_frozen("passages.json")
    gold_ids = list(pas["positives"])
    selected: list[dict] = []
    replicate_rows = []
    for rep in reps:
        merged_path = V1 / "runs" / "b3" / f"R{rep}" / "merged.json"
        payload = json.loads(merged_path.read_text(encoding="utf-8"))
        candidates = payload["candidates"]
        gold_hits = {gid: 0 for gid in gold_ids}
        neg_hits = {gid: 0 for gid in gold_ids}
        n_gold = n_neg = n_other = 0
        for i, cand in enumerate(candidates):
            row = classify_candidate(cand, pas, gold_ids)
            if row["label"] == GOLD:
                n_gold += 1
                for gid in row["gold_ids"]:
                    gold_hits[gid] += 1
            elif row["label"] == NEGATIVE:
                n_neg += 1
                for gid in row["negative_ids"]:
                    neg_hits[gid] += 1
            else:
                n_other += 1
            if row["label"] == OTHER:
                continue
            item = {
                "candidate_id": f"R{rep}/c{i:04d}",
                "rep": rep,
                "merged_index": i,
                "label": row["label"],
                "gold_ids": row["gold_ids"],
                "negative_ids": row["negative_ids"],
                "source": cand.get("source"),
                "locator": cand.get("locator"),
                "exact_span": cand.get("exact_span"),
                "affected_purpose": cand.get("affected_purpose"),
                "computation_change_reason": cand.get("computation_change_reason"),
                "_segment_id": cand.get("_segment_id"),
                "_page": cand.get("_page"),
                "_document": cand.get("_document"),
            }
            selected.append(item)
        n_seams = sum(1 for gid in gold_ids if gold_hits[gid] > 0)
        replicate_rows.append(
            {
                "rep": rep,
                "n_merged": len(candidates),
                "n_gold_match": n_gold,
                "n_negative_match": n_neg,
                "n_other": n_other,
                "n_selected": n_gold + n_neg,
                "locator_gold_nomination_recall": n_seams / len(gold_ids),
                "gold_hits": gold_hits,
                "negative_hits": neg_hits,
                "missing_gold_seams": [gid for gid in gold_ids if gold_hits[gid] == 0],
            }
        )
    out = {
        "experiment_id": "npdes-prose-probe-v1-1",
        "classifier": "frozen_source_locator_document_page_span_overlap",
        "note": (
            "GOLD_MATCH requires facility-qualified document + page + span overlap "
            "with frozen positive locators. This is stricter than v1 B3 recall, which "
            "aliased bare final_permit across facilities. v1 12/12 recall is sealed and unaltered."
        ),
        "replicates_used": list(reps),
        "n_selected": len(selected),
        "replicate_metrics": replicate_rows,
        "candidates": selected,
    }
    return out


def dump_selected(payload: dict | None = None) -> dict:
    FROZEN.mkdir(parents=True, exist_ok=True)
    payload = payload or classify_replicates()
    (FROZEN / "selected.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    freeze = {
        "experiment_id": "npdes-prose-probe-v1-1",
        "not": "Constructor v3.2",
        "v1_sealed": True,
        "replicates": [1, 2, 3],
        "model": "composer-2.5",
        "processes_other": False,
        "n_selected": payload["n_selected"],
        "classifier": payload["classifier"],
        "replicate_metrics": payload["replicate_metrics"],
    }
    (FROZEN / "freeze.json").write_text(json.dumps(freeze, indent=2) + "\n", encoding="utf-8")
    return payload


def load_selected() -> dict:
    path = FROZEN / "selected.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return dump_selected()


if __name__ == "__main__":
    payload = dump_selected()
    print(json.dumps({k: payload[k] for k in payload if k != "candidates"}, indent=2))
    print("n_selected", payload["n_selected"])
