"""Score ablation runs with the frozen E1/E2 functions plus tighter coverage."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from research.semantic_integration.domains.npdes.purpose_first_python_spine_v1.score import (
    SEAM_SIGNATURES,
    hardcode_flags,
    seam_hit,
    spine_distinctions,
)

PRIMARY = [
    "S-FARM-TDS-STAGE",
    "S-FARM-REPORT-ONLY",
    "S-AZTEC-WHEN-DISCHARGING",
    "S-AZTEC-REPORT-ONLY",
    "S-GCC-EVENT-DISCHARGE",
    "S-GCC-REPORT-ONLY",
    "S-SOURCE-AUTHORITY",
]


def _blob(code: str, holes: list, spine: dict, public: dict) -> str:
    parts = [code, json.dumps(public), json.dumps(spine)[:200000], json.dumps(holes)[:400000]]
    return "\n".join(parts).lower()


def _trial_view(public: dict, spine: dict) -> dict[str, Any]:
    groups = public.get("hole_groups") or spine.get("hole_groups") or []
    return {
        "final": {
            "ok": bool(public.get("ok")),
            "errors": public.get("errors") or [],
            "relations": public.get("relations") or spine.get("relations") or {},
            "relation_row_counts": public.get("relation_row_counts") or spine.get("relation_row_counts") or {},
            "hole_groups": groups,
            "n_hole_groups": public.get("n_hole_groups") or spine.get("n_hole_groups") or len(groups),
            "n_hole_instances": public.get("n_hole_instances") or spine.get("n_hole_instances") or 0,
        }
    }


def precise_coverage(code: str, holes: list, groups: list) -> dict[str, bool]:
    reqs = " ".join(str(g.get("requirement") or "") for g in groups).lower()
    kinds = {str(g.get("failure_kind") or "") for g in groups}
    hole_blob = json.dumps(groups).lower() + json.dumps(holes[:80]).lower()
    code_l = code.lower()
    uniqueness_hole = bool(kinds & {"CARDINALITY_OVERSATISFIED", "MULTIPLE_CANDIDATES", "CARDINALITY_UNDERSATISFIED"})
    uniqueness_req = "require_unique" in code_l
    interval = any(tok in code_l for tok in ("interval_contains", "begin_date", "limit_begin", "parse_date"))
    when = any(tok in (reqs + hole_blob) for tok in ("discharg", "when discharging")) or (
        "comment" in reqs and bool(kinds & {"UNINTERPRETED", "EXPLICIT_UNRESOLVED"})
    )
    report = "COMPARISON_OPERATOR_REQUIRED" in kinds or any(
        tok in reqs for tok in ("non_numeric", "without_numeric", "report_only", "comparability")
    )
    if not report and "require_numeric" in code_l and bool(
        kinds & {"COMPARISON_OPERATOR_REQUIRED", "UNINTERPRETED", "EXPLICIT_UNRESOLVED"}
    ):
        report = True
    nodi = "nodi" in reqs
    authority_hole = any(
        tok in reqs
        for tok in (
            "document_text",
            "document_inventory",
            "not_materialized",
            "not_available",
            "permit_document",
        )
    )
    return {
        "tds_interval": interval,
        "tds_uniqueness_authored": uniqueness_req,
        "tds_cardinality_hole": uniqueness_hole,
        "tds_precise": interval and (uniqueness_hole or uniqueness_req),
        "when_precise": when,
        "report_precise": report,
        "nodi_precise": nodi,
        "authority_inventoried": "document_inventory" in code_l or "permit_document" in code_l,
        "authority_precise": authority_hole,
    }


def score_run(code: str, public: dict, holes: list, spine: dict | None = None) -> dict[str, Any]:
    spine = spine or {}
    trial = _trial_view(public, spine)
    text = _blob(code, holes, spine, public)
    per_seam = {gid: seam_hit(gid, trial, text) for gid in PRIMARY}
    e1 = sum(1 for gid in PRIMARY if per_seam[gid])
    distinctions = spine_distinctions(trial, text)
    groups = trial["final"]["hole_groups"]
    return {
        "ok": trial["final"]["ok"],
        "errors": trial["final"]["errors"],
        "e1_hits": e1,
        "e1_n": len(PRIMARY),
        "e1_recall": e1 / len(PRIMARY),
        "per_seam": per_seam,
        "e2_distinctions": distinctions,
        "e2_n_true": sum(1 for v in distinctions.values() if v),
        "n_hole_groups": trial["final"]["n_hole_groups"],
        "n_hole_instances": trial["final"]["n_hole_instances"],
        "relation_row_counts": trial["final"]["relation_row_counts"],
        "hardcode_flags": hardcode_flags(code),
        "precise": precise_coverage(code, holes, groups),
    }


def classify_ablation(baseline: dict, ablated: dict) -> str:
    if not ablated.get("ok"):
        return "COUPLED_OR_INDETERMINATE"
    degraded = False
    if (ablated.get("e1_hits") or 0) < (baseline.get("e1_hits") or 0):
        degraded = True
    if (ablated.get("e2_n_true") or 0) < (baseline.get("e2_n_true") or 0):
        degraded = True
    b_p = baseline.get("precise") or {}
    a_p = ablated.get("precise") or {}
    for key in (
        "tds_precise",
        "tds_cardinality_hole",
        "tds_uniqueness_authored",
        "when_precise",
        "report_precise",
        "nodi_precise",
        "authority_precise",
    ):
        if b_p.get(key) and not a_p.get(key):
            degraded = True
    if ablated.get("n_hole_groups") == 0 and (baseline.get("n_hole_groups") or 0) > 0:
        degraded = True
    b_rows = baseline.get("relation_row_counts") or {}
    a_rows = ablated.get("relation_row_counts") or {}
    if sum(b_rows.values() or [0]) > 0 and sum(a_rows.values() or [0]) == 0:
        degraded = True
    if degraded:
        return "REQUIRED_FOR_PURPOSE"
    return "LOCALLY_REDUNDANT_FOR_PURPOSE"
