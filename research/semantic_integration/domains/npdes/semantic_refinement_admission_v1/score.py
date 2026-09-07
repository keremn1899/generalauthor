"""Score refinement/admission traces. Research metadata, not kernel primitives."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from research.semantic_integration.domains.npdes.semantic_refinement_admission_v1.paths import (
    EVALUATOR_ONLY,
    FROZEN,
    OBLIGATION_IDS,
    RUNS,
)

TDS_MARKERS = ("70295", "total dissolved", "tds")
NONTDS_MARKERS = ("00310", "bod", "non-tds", "carryover", "misattach", "inherited")
SIBLING_HOLES = {
    "geometric_mean": ("conditional_discharge_dependent_monitoring", "pass_fail_reporting_semantics"),
    "empty_numeric_limit": ("conditional_discharge_dependent_monitoring", "pass_fail_reporting_semantics", "aggregated_reporting_requirement"),
}


def _json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"_parse_error": True}


def cells() -> list[dict]:
    rows = []
    for trial in ("T1", "T2", "T3"):
        for oid in OBLIGATION_IDS:
            cell = _json(RUNS / trial / oid / "cell.json")
            if cell:
                rows.append(cell)
    return rows


def children_of(cell: dict) -> list[dict]:
    ref = cell.get("refinement") or {}
    kids = ref.get("children") or []
    if isinstance(kids, list):
        return [k for k in kids if isinstance(k, dict)]
    return []


def mentions_tds_split(cell: dict) -> dict:
    blob = json.dumps(cell.get("refinement") or {}, default=str).lower()
    tds = any(m in blob for m in TDS_MARKERS)
    other = any(m in blob for m in NONTDS_MARKERS) or ("parameter_code" in blob and "70295" in blob)
    return {"tds": tds, "nontds": other, "recovered": tds and other}


def leakage(cell: dict) -> list[str]:
    flags = []
    oid = cell.get("obligation_id")
    siblings = SIBLING_HOLES.get(oid) or ()
    for dry in cell.get("dry_runs") or []:
        if dry.get("ok") is False:
            continue
        removed = set(((dry.get("delta") or {}).get("hole_requirements_removed") or []))
        for sib in siblings:
            if sib in removed and oid == "geometric_mean":
                flags.append(f"{dry.get('child_id')}:removed:{sib}")
            if oid == "empty_numeric_limit" and sib in removed:
                # empty-limit pass/fail child should not drop when-discharging / geometric as families unless intended
                if sib == "conditional_discharge_dependent_monitoring":
                    flags.append(f"{dry.get('child_id')}:removed:{sib}")
    return flags


def unsupported_child(child: dict, cell: dict) -> bool:
    admit = child.get("admission_status")
    if admit != "ADMIT_DISPOSABLE":
        return False
    epi = child.get("epistemic_basis")
    if epi in {"MODEL_GENERALIZATION", "USER_ASSERTED", "UNRESOLVED"}:
        return True
    snippets = ((cell.get("packet") or {}).get("retained_snippets") or [])
    if epi == "SOURCE_ESTABLISHED" and not snippets and not child.get("evidence_grounding"):
        return True
    return False


def _as_items(value) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return [value]
    return [{"value": value}]


def broader_admitted(cell: dict) -> list[str]:
    flags = []
    adm = cell.get("admission") or {}
    for item in _as_items(adm.get("GENERALIZATIONS_ADMITTED")):
        text = json.dumps(item, default=str).lower()
        if any(tok in text for tok in ("outrank", "always", "whenever", "all final", "legally override", "level 3", "level_3")):
            flags.append(str(item)[:240])
        if isinstance(item, dict) and item.get("admission_status") == "ADMIT_DISPOSABLE":
            epi = str(item.get("epistemic_basis") or "")
            if epi in {"MODEL_GENERALIZATION", "UNRESOLVED"}:
                flags.append(f"admitted_generalization:{epi}")
    levels = adm.get("LEVELS") or {}
    for lvl3 in _as_items(levels.get("LEVEL_3_GENERAL")):
        if isinstance(lvl3, dict) and lvl3.get("admission_status") == "ADMIT_DISPOSABLE":
            flags.append("LEVEL_3_GENERAL admitted disposable")
    return flags


def local_underused(cell: dict) -> bool:
    if cell.get("obligation_id") != "document_authority":
        return False
    adm = cell.get("admission") or {}
    established = _as_items(adm.get("ESTABLISHED_PROPOSITIONS"))
    local_admitted = False
    for item in established:
        if isinstance(item, dict) and str(item.get("admission_status") or item.get("admit") or "") == "ADMIT_DISPOSABLE":
            local_admitted = True
    levels = adm.get("LEVELS") or {}
    for lvl1 in _as_items(levels.get("LEVEL_1_DOCUMENT_LOCAL")):
        if isinstance(lvl1, dict) and lvl1.get("admission_status") == "ADMIT_DISPOSABLE":
            local_admitted = True
    if not established and not levels:
        return True
    return not local_admitted


def parent_protocol_drift(cell: dict) -> bool:
    parent = cell.get("parent") or {}
    status = parent.get("parent_status")
    if status not in {"REFINED", "REFINEMENT_REQUIRED"}:
        if status == "UNRESOLVED" and children_of(cell):
            return True
        return False
    # After refinement the parent must not be independently unresolved or admitted.
    if parent.get("independently_admitted"):
        return True
    if parent.get("independently_unresolved"):
        return True
    if status == "UNRESOLVED":
        return True
    return False


def score() -> dict[str, Any]:
    rows = cells()
    specs = (_json(FROZEN / "selected_obligations.json") or {}).get("obligations") or []
    occ = {s["obligation_id"]: s.get("affected_occurrence_count") or len(s.get("occurrence_ids") or []) for s in specs}
    parent_statuses = {}
    drifts = []
    tds = {}
    compact = []
    unsup = []
    leaks = {}
    failed_dry = []
    broader = []
    underused = []
    mutated = 0
    for c in rows:
        oid = c.get("obligation_id")
        trial = c.get("trial")
        key = f"{trial}:{oid}"
        parent = c.get("parent") or {}
        parent_statuses[key] = parent.get("parent_status")
        if parent_protocol_drift(c):
            drifts.append(key)
        if c.get("mutated_durable"):
            mutated += 1
        kids = children_of(c)
        counts = [k.get("affected_count") or 0 for k in kids if isinstance(k.get("affected_count"), (int, float))]
        n_parent = occ.get(oid) or 0
        compact.append(
            {
                "cell": key,
                "n_children": len(kids),
                "largest": max(counts) if counts else None,
                "smallest": min(counts) if counts else None,
                "parent_occurrences": n_parent,
                "residual": (c.get("refinement") or {}).get("residual_occurrences"),
                "mechanically_computable": (c.get("refinement") or {}).get("mechanically_computable"),
                "fragmented": bool(counts) and min(counts) <= 1 and len(kids) >= 8,
            }
        )
        if oid == "geometric_mean":
            tds[key] = mentions_tds_split(c)
        for k in kids:
            if unsupported_child(k, c):
                unsup.append(f"{key}:{k.get('child_id')}")
        lf = leakage(c)
        if lf:
            leaks[key] = lf
        for dry in c.get("dry_runs") or []:
            if dry.get("ok") is False:
                failed_dry.append(f"{key}:{dry.get('child_id')}")
        if oid == "document_authority":
            b = broader_admitted(c)
            if b:
                broader.extend([f"{key}:{x}" for x in b])
            if local_underused(c):
                underused.append(key)
    fragmented = [r["cell"] for r in compact if r.get("fragmented")]
    refined_ok = [
        k
        for k, st in parent_statuses.items()
        if st == "REFINED" and k not in drifts and ("geometric_mean" in k or "empty_numeric_limit" in k)
    ]
    return {
        "n_cells": len(rows),
        "parent_statuses": parent_statuses,
        "protocol_drifts": drifts,
        "n_protocol_drifts": len(drifts),
        "tds_split": tds,
        "n_tds_recovered": sum(1 for v in tds.values() if v.get("recovered")),
        "compactness": compact,
        "fragmented_cells": fragmented,
        "unsupported_child_closures": unsup,
        "leakage_flags": leaks,
        "n_leakage": len(leaks),
        "failed_dry_runs": failed_dry,
        "broader_admissions": broader,
        "local_underused": underused,
        "mutated_durable": mutated,
        "n_refined_protocol_ok": len(refined_ok),
        "cells": rows,
    }


def choose_label(summary: dict) -> str:
    if summary.get("broader_admissions"):
        return "UNSUPPORTED_GENERALIZATION_ADMITTED"
    if summary.get("fragmented_cells"):
        return "OVERFRAGMENTED_REFINEMENT"
    if summary.get("n_protocol_drifts"):
        return "REFINEMENT_PROTOCOL_WEAK"
    if summary.get("local_underused") and len(summary.get("local_underused") or []) >= 2:
        return "LOCAL_EVIDENCE_UNDERUSED"
    if summary.get("failed_dry_runs") and not summary.get("n_protocol_drifts") and not summary.get("broader_admissions"):
        # apply failures are labeled separately if they dominate; still mixed if other things work
        pass
    n = summary.get("n_cells") or 0
    tds_ok = (summary.get("n_tds_recovered") or 0) >= 2
    compact = not summary.get("fragmented_cells")
    no_unsup = not summary.get("unsupported_child_closures")
    no_leak = not summary.get("n_leakage")
    no_drift = not summary.get("n_protocol_drifts")
    no_broader = not summary.get("broader_admissions")
    no_under = not summary.get("local_underused")
    if n >= 9 and tds_ok and compact and no_unsup and no_leak and no_drift and no_broader and no_under:
        if summary.get("failed_dry_runs"):
            return "MIXED_REFINEMENT_ADMISSION_RESULT"
        return "REFINEMENT_ADMISSION_BOUNDARY_SUPPORTED"
    if summary.get("failed_dry_runs") and n >= 9 and no_drift and no_broader:
        return "DISPOSABLE_APPLY_FAILURE"
    if n < 9:
        return "MIXED_REFINEMENT_ADMISSION_RESULT"
    return "MIXED_REFINEMENT_ADMISSION_RESULT"
