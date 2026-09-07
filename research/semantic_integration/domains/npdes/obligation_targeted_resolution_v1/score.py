"""Score obligation-targeted resolution traces. Evaluator judgment, not usability."""

from __future__ import annotations

import difflib
import json
from pathlib import Path
from typing import Any

from research.semantic_integration.domains.npdes.obligation_targeted_resolution_v1.paths import (
    DRAFT_TRIAL,
    EVALUATOR_ONLY,
    FROZEN,
    PFPS,
    RUNS,
)

SIBLINGS = {
    "nodi_c": "nodi_9",
    "nodi_9": "nodi_c",
    "when_discharging": "geometric_mean",
    "geometric_mean": "pass_fail",
    "pass_fail": "when_discharging",
}

ADDED_LEAKAGE_MARKERS = {
    "nodi_c": ["known=['', 'C', '9']", 'known=["", "C", "9"]', "known=['C', '9']", 'known=["C", "9"]'],
    "nodi_9": ["known=['', 'C', '9']", 'known=["", "C", "9"]', "known=['C', '9']", 'known=["C", "9"]'],
}


def _added_lines(proposed: str, baseline: str) -> str:
    diff = difflib.unified_diff(baseline.splitlines(), proposed.splitlines(), lineterm="")
    return "\n".join(line[1:] for line in diff if line.startswith("+") and not line.startswith("+++"))


def leakage_flags(cell: dict) -> list[str]:
    oid = cell.get("obligation_id")
    flags = []
    sealed = RUNS / "arm_b" / str(cell.get("trial")) / str(oid) / "dry_run" / "construction.py"
    baseline_path = PFPS / "runs" / DRAFT_TRIAL / "iter1" / "construction.py"
    if (cell.get("dry_run") or {}).get("public", {}).get("ok") is False:
        return flags
    if sealed.exists() and baseline_path.exists():
        added = _added_lines(
            sealed.read_text(encoding="utf-8", errors="replace"),
            baseline_path.read_text(encoding="utf-8", errors="replace"),
        )
        for marker in ADDED_LEAKAGE_MARKERS.get(oid) or []:
            if marker in added:
                flags.append(f"added_mentions:{marker}")
    delta = (cell.get("dry_run") or {}).get("delta") or {}
    removed = set(delta.get("hole_requirements_removed") or [])
    if oid in {"nodi_c", "nodi_9"} and "nodi_code_semantics" in removed:
        flags.append("closed_entire_nodi_requirement")
    if oid == "when_discharging" and "aggregated_reporting_requirement" in removed:
        flags.append("closed_geometric_mean_requirement")
    if oid == "when_discharging" and "pass_fail_reporting_semantics" in removed:
        flags.append("closed_pass_fail_requirement")
    if oid == "geometric_mean" and "conditional_discharge_dependent_monitoring" in removed:
        flags.append("closed_when_discharging_requirement")
    if oid == "pass_fail" and "conditional_discharge_dependent_monitoring" in removed:
        flags.append("closed_when_discharging_requirement")
    return flags


def _json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"_parse_error": True}


def selected() -> list[dict]:
    return (_json(FROZEN / "selected_obligations.json") or {}).get("obligations") or []


def establishability() -> dict:
    return _json(EVALUATOR_ONLY / "establishability.json") or {}


def arm_b_cells() -> list[dict]:
    rows = []
    for trial in ("T1", "T2", "T3"):
        for spec in selected():
            cell = _json(RUNS / "arm_b" / trial / spec["obligation_id"] / "cell.json")
            if cell:
                rows.append(cell)
    return rows


def arm_a_cases() -> list[dict]:
    rows = []
    for path in sorted((RUNS / "arm_a").glob("*/case.json")) if (RUNS / "arm_a").exists() else []:
        rows.append(json.loads(path.read_text(encoding="utf-8")))
    return rows


WORKSPACE_SNIPPET_MARKERS = (
    "/documents/",
    "/sources/",
    "documents/",
    "sources/",
    "construction.py",
    "PACKET.json",
    "purposes/",
    "PASS_TASK",
    "PRINCIPLES.md",
    "WORLD_API.md",
    "OBLIGATION.md",
    "OCCURRENCE.md",
    "BUDGET.md",
)


def extra_corpus_snippets(snippets: list) -> list[str]:
    bad = []
    for snip in snippets or []:
        sid = str((snip or {}).get("source_id") or "")
        if not sid:
            continue
        lowered = sid.replace("\\", "/")
        if any(tok in lowered for tok in WORKSPACE_SNIPPET_MARKERS):
            continue
        bad.append(sid)
    return bad


def dry_run_ok(cell: dict) -> bool:
    dry = cell.get("dry_run") or {}
    public = dry.get("public") or {}
    return bool(public.get("ok"))


def protocol_mismatch(cell: dict) -> bool:
    judgment = cell.get("judgment") or {}
    proposal = cell.get("proposal") or {}
    return proposal.get("admit") == "ADMIT_DISPOSABLE" and judgment.get("disposition") not in {
        "SUPPORTED_RESOLUTION",
        "SUPPORTED_NEGATIVE",
    }


def unsupported_closure(cell: dict) -> bool:
    judgment = cell.get("judgment") or {}
    proposal = cell.get("proposal") or {}
    disp = judgment.get("disposition")
    epistemic = judgment.get("epistemic_basis") or proposal.get("epistemic_basis")
    admit = proposal.get("admit")
    if admit != "ADMIT_DISPOSABLE":
        return False
    snippets = ((cell.get("packet") or {}).get("retained_snippets") or [])
    if extra_corpus_snippets(snippets) and epistemic == "SOURCE_ESTABLISHED":
        return True
    if epistemic in {"MODEL_HYPOTHESIS", "USER_ASSERTED_EXTERNAL_FACT"}:
        return True
    if disp in {"SUPPORTED_RESOLUTION", "SUPPORTED_NEGATIVE"}:
        if epistemic == "SOURCE_ESTABLISHED" and not snippets:
            return True
        return False
    # Parent UNRESOLVED + disposable admit of a refined/scoped proposal is a protocol
    # mismatch, not an unsupported codebook closure, when the proposal is source-grounded.
    if proposal.get("epistemic_basis") == "SOURCE_ESTABLISHED" and snippets:
        return False
    return True


def score() -> dict[str, Any]:
    specs = selected()
    est = establishability()
    cells = arm_b_cells()
    a_cases = arm_a_cases()
    n_occ = sum(s.get("n_occurrences") or 0 for s in specs)
    n_obl = len(specs)
    refinements = [c for c in cells if c.get("refinement")]
    dispositions = {}
    for c in cells:
        d = (c.get("judgment") or {}).get("disposition") or "MISSING"
        dispositions[d] = dispositions.get(d, 0) + 1
    closures = [c for c in cells if unsupported_closure(c)]
    establishable_ids = [k for k, v in est.items() if (v or {}).get("label") == "ESTABLISHABLE_IN_CORPUS"]
    resolved_est = []
    for oid in establishable_ids:
        for c in cells:
            if c.get("obligation_id") == oid and (c.get("judgment") or {}).get("disposition") in {"SUPPORTED_RESOLUTION", "SUPPORTED_NEGATIVE"}:
                resolved_est.append(c)
                break
    docs_opened = []
    retained = []
    for c in cells:
        r = c.get("retrieval") or {}
        docs_opened.append(r.get("n_documents_touched") or 0)
        retained.append(len((c.get("packet") or {}).get("retained_snippets") or []))
    judgments_b = len(cells)
    occ_per_judgment = (n_occ / judgments_b) if judgments_b else None
    a_docs = [((c.get("retrieval") or {}).get("n_documents_touched") or 0) for c in a_cases]
    a_disp = {}
    for c in a_cases:
        d = (c.get("judgment") or {}).get("disposition") or "MISSING"
        a_disp[d] = a_disp.get(d, 0) + 1
    by_obl_a: dict[str, set] = {}
    for c in a_cases:
        oid = c.get("obligation_id")
        interp = str(((c.get("judgment") or {}).get("interpretation") or ""))[:200]
        by_obl_a.setdefault(oid, set()).add(interp)
    a_inconsistent = {k: v for k, v in by_obl_a.items() if len(v) > 1}
    extra_b = []
    for c in cells:
        extra_b.extend(extra_corpus_snippets(((c.get("packet") or {}).get("retained_snippets") or [])))
    extra_a = []
    for c in a_cases:
        extra_a.extend(extra_corpus_snippets(((c.get("judgment") or {}).get("snippets") or [])))
    mutated = [c for c in cells if c.get("mutated_before_evidence")]
    mismatches = [f"{c.get('trial')}:{c.get('obligation_id')}" for c in cells if protocol_mismatch(c)]
    failed_dry = [
        f"{c.get('trial')}:{c.get('obligation_id')}"
        for c in cells
        if c.get("dry_run") and (c.get("dry_run") or {}).get("public", {}).get("ok") is False
    ]
    leaks = {f"{c.get('trial')}:{c.get('obligation_id')}": leakage_flags(c) for c in cells if leakage_flags(c)}
    unresolved_by_mode = {}
    for c in cells:
        if (c.get("judgment") or {}).get("disposition") == "UNRESOLVED":
            mode = (c.get("judgment") or {}).get("failure_mode_if_unresolved") or "MISSING"
            unresolved_by_mode[mode] = unresolved_by_mode.get(mode, 0) + 1
    return {
        "n_selected_obligations": n_obl,
        "n_candidate_obligations": len(_json(FROZEN / "candidate_obligations.json") or []),
        "n_affected_occurrences_selected": n_occ,
        "compression": (n_occ / n_obl) if n_obl else None,
        "n_arm_b_cells": len(cells),
        "n_arm_a_cases": len(a_cases),
        "n_refinements": len(refinements),
        "dispositions": dispositions,
        "unsupported_closures": len(closures),
        "establishable_ids": establishable_ids,
        "establishable_resolved_at_least_once": len({c.get("obligation_id") for c in resolved_est}),
        "mean_documents_opened_b": (sum(docs_opened) / len(docs_opened)) if docs_opened else None,
        "mean_retained_snippets_b": (sum(retained) / len(retained)) if retained else None,
        "occurrences_per_arm_b_judgment": occ_per_judgment,
        "arm_a_dispositions": a_disp,
        "arm_a_mean_documents": (sum(a_docs) / len(a_docs)) if a_docs else None,
        "arm_a_inconsistent_obligations": {k: list(v)[:4] for k, v in a_inconsistent.items()},
        "mutated_before_evidence": len(mutated),
        "protocol_mismatches": mismatches,
        "failed_dry_runs": failed_dry,
        "extra_corpus_snippet_ids_arm_b": sorted(set(extra_b))[:20],
        "extra_corpus_snippet_ids_arm_a": sorted(set(extra_a))[:20],
        "leakage_flags": leaks,
        "n_leakage_cells": len(leaks),
        "unresolved_by_mode": unresolved_by_mode,
        "cells": cells,
        "arm_a": a_cases,
    }


def choose_label(summary: dict) -> str:
    cells = summary.get("cells") or []
    if summary.get("unsupported_closures"):
        return "UNSUPPORTED_SEMANTIC_CLOSURE"
    if summary.get("n_leakage_cells"):
        return "PROPAGATION_UNSAFE"
    if summary.get("n_refinements", 0) > 16:
        return "SEMANTIC_COMPRESSION_WEAK"
    docs = summary.get("mean_documents_opened_b") or 0
    if docs > 8:
        return "TARGETED_RETRIEVAL_WEAK"
    n_est = len(summary.get("establishable_ids") or [])
    n_got = summary.get("establishable_resolved_at_least_once") or 0
    if n_est and n_got == 0 and summary.get("n_arm_b_cells", 0) >= 8:
        return "BOUNDED_ADJUDICATION_UNDERCLOSES"
    compact = (summary.get("n_selected_obligations") or 0) <= 12 and (summary.get("n_refinements") or 0) <= 8
    safe = summary.get("unsupported_closures") == 0
    leverage = (summary.get("occurrences_per_arm_b_judgment") or 0) >= 5
    a_n = summary.get("n_arm_a_cases") or 0
    less_dup = a_n >= 8 and (summary.get("arm_a_mean_documents") or 0) >= (summary.get("mean_documents_opened_b") or 0)
    retrieved = n_est == 0 or n_got >= max(1, n_est // 2)
    if compact and safe and leverage and retrieved and summary.get("n_arm_b_cells", 0) >= 8:
        if less_dup or not a_n:
            return "OBLIGATION_DRIVEN_RESOLUTION_SUPPORTED"
    if summary.get("n_arm_b_cells", 0) < 8:
        return "MIXED_OBLIGATION_RESOLUTION_RESULT"
    return "MIXED_OBLIGATION_RESOLUTION_RESULT"
