"""Compile T5 holes into candidate/selected obligations. Evaluator freeze."""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from research.semantic_integration.domains.npdes.obligation_targeted_resolution_v1.paths import (
    DRAFT_TRIAL,
    EVALUATOR_GOLD,
    EVALUATOR_ONLY,
    FROZEN,
    PARTICIPANT,
    PERMIT_TEXT,
    PFPS,
)
from research.semantic_integration.domains.npdes.purpose_first_python_spine_v1.workspaces import (
    document_inventory,
)

HOLES = PFPS / "runs" / DRAFT_TRIAL / "iter1" / "holes.json"
PUBLIC = PFPS / "runs" / DRAFT_TRIAL / "iter1" / "run.json"
LIMITS = PARTICIPANT / "sources" / "structured" / "permit_limits.csv"
DMR = PARTICIPANT / "sources" / "structured" / "dmr_measurements.csv"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def occ_id(hole: dict, i: int) -> str:
    subj = hole.get("subject") or {}
    if subj.get("measurement"):
        return str(subj["measurement"])
    if subj.get("limit_value_id") and subj.get("limit_set_schedule_id"):
        return f"{subj['limit_value_id']}|{subj['limit_set_schedule_id']}"
    if subj.get("permit_limit_row"):
        return str(subj["permit_limit_row"])
    if subj.get("source"):
        return str(subj["source"])
    return f"{hole.get('requirement')}:{i}"


def compile_candidates() -> list[dict]:
    holes = _load(HOLES)
    buckets: dict[tuple, list[dict]] = defaultdict(list)
    for i, hole in enumerate(holes):
        req = str(hole.get("requirement") or "")
        observed = hole.get("observed") or {}
        if isinstance(observed, dict):
            obs = observed.get("value") or observed.get("field") or ""
        else:
            obs = str(observed)
        kind = str(hole.get("failure_kind") or "")
        if req == "nodi_code_semantics":
            key = (req, str((hole.get("subject") or {}).get("nodi_code") or obs), kind)
        elif req in {"conditional_discharge_dependent_monitoring", "aggregated_reporting_requirement", "pass_fail_reporting_semantics", "permit_document_text_not_available"}:
            key = (req, "", kind)
        elif req in {"monitoring_frequency_code", "limit_sample_type_code", "permit_limit_comment_text"}:
            key = (req, str(obs), kind)
        else:
            key = (req, str(obs), kind)
        buckets[key].append({**hole, "_i": i})

    candidates = []
    for (req, value, kind), members in sorted(buckets.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        ids = [occ_id(h, h["_i"]) for h in members]
        candidates.append(
            {
                "candidate_id": f"{req}:{value or '_'}".strip(":"),
                "requirement_schema": req,
                "source_value": value,
                "failure_kind": kind,
                "n_occurrences": len(members),
                "occurrence_ids": ids,
                "purpose": members[0].get("purpose"),
                "relation": members[0].get("relation"),
            }
        )
    return candidates


def empty_limit_rows() -> list[dict]:
    rows = []
    with LIMITS.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if not str(row.get("LIMIT_VALUE_NMBR") or "").strip():
                rows.append(
                    {
                        "limit_value_id": row.get("LIMIT_VALUE_ID"),
                        "limit_set_schedule_id": row.get("LIMIT_SET_SCHEDULE_ID"),
                        "permit": row.get("EXTERNAL_PERMIT_NMBR"),
                        "parameter": row.get("PARAMETER_CODE"),
                        "comment": (row.get("DMR_COMMENT_TEXT") or "")[:180],
                    }
                )
    return rows


def selected_specs(candidates: list[dict], empty_rows: list[dict]) -> list[dict]:
    by_req_val = {(c["requirement_schema"], c["source_value"]): c for c in candidates}
    by_req = defaultdict(list)
    for c in candidates:
        by_req[c["requirement_schema"]].append(c)

    def take(req: str, value: str = "") -> dict:
        if value:
            return by_req_val[(req, value)]
        group = by_req[req]
        if len(group) == 1:
            return group[0]
        merged_ids = []
        n = 0
        for g in group:
            merged_ids.extend(g["occurrence_ids"])
            n += g["n_occurrences"]
        base = dict(group[0])
        base["occurrence_ids"] = merged_ids
        base["n_occurrences"] = n
        base["source_value"] = ""
        return base

    nodi_c = take("nodi_code_semantics", "C")
    nodi_9 = take("nodi_code_semantics", "9")
    when = take("conditional_discharge_dependent_monitoring")
    geom = take("aggregated_reporting_requirement")
    pf = take("pass_fail_reporting_semantics")
    doc = take("permit_document_text_not_available")
    freq = take("monitoring_frequency_code")  # fallback extra; empty limits added separately

    empty_ids = [f"{r['limit_value_id']}|{r['limit_set_schedule_id']}" for r in empty_rows]
    empty = {
        "candidate_id": "empty_numeric_limit",
        "requirement_schema": "empty_numeric_limit_classification",
        "source_value": "",
        "failure_kind": "UNCLASSIFIED_EMPTY_LIMIT",
        "n_occurrences": len(empty_ids),
        "occurrence_ids": empty_ids,
        "purpose": ["A"],
        "relation": "permit_limit",
        "note": "Empty LIMIT_VALUE_NMBR rows exist in structured sources. T5 excluded them from numeric comparison without a named hole. Included as preferred fixture #6.",
    }

    specs = [
        {
            "obligation_id": "nodi_c",
            "requirement_schema": "nodi_code_semantics",
            "exact_semantic_question": "What does NODI code C mean for a FY2025 DMR row with no numeric result?",
            "declared_purposes": ["C"],
            "relation_contract": "no_numeric_result_case.nodi_code must be interpreted before missing-evidence classification",
            "source_field_value": "NODI_CODE='C'",
            "why_blocked": "T5 require_interpreted(nodi_code_semantics, known=['']) leaves C UNINTERPRETED",
            "include_reason": "Preferred fixture: NODI C; codebook-shaped evidence problem; 150 occurrences",
            **{k: nodi_c[k] for k in ("n_occurrences", "occurrence_ids", "failure_kind", "relation")},
        },
        {
            "obligation_id": "nodi_9",
            "requirement_schema": "nodi_code_semantics",
            "exact_semantic_question": "What does NODI code 9 mean for a FY2025 DMR row with no numeric result?",
            "declared_purposes": ["C"],
            "relation_contract": "no_numeric_result_case.nodi_code must be interpreted; C and 9 must not inherit each other",
            "source_field_value": "NODI_CODE='9'",
            "why_blocked": "T5 leaves nonempty NODI codes UNINTERPRETED",
            "include_reason": "Preferred fixture: NODI 9; sibling of C; 36 occurrences; leakage control",
            **{k: nodi_9[k] for k in ("n_occurrences", "occurrence_ids", "failure_kind", "relation")},
        },
        {
            "obligation_id": "when_discharging",
            "requirement_schema": "conditional_discharge_dependent_monitoring",
            "exact_semantic_question": "What does the permit-limit comment 'WHEN DISCHARGING' do to monitoring/limit applicability?",
            "declared_purposes": ["B", "C"],
            "relation_contract": "comment conditions monitoring; discharge occurrence in a period is a separate factual question",
            "source_field_value": "DMR_COMMENT_TEXT contains 'WHEN DISCHARGING'",
            "why_blocked": "T5 names an EXPLICIT_UNRESOLVED family for this phrase without converting it to a World rule",
            "include_reason": "Preferred fixture: discharge-conditioned applicability; permit-clause evidence",
            **{k: when[k] for k in ("n_occurrences", "occurrence_ids", "failure_kind", "relation")},
        },
        {
            "obligation_id": "geometric_mean",
            "requirement_schema": "aggregated_reporting_requirement",
            "exact_semantic_question": "What does a geometric-mean reporting comment require for comparison of individual monitoring-period values?",
            "declared_purposes": ["A", "B", "C"],
            "relation_contract": "aggregated reporting is not an ordinary single-period numeric comparison",
            "source_field_value": "DMR_COMMENT_TEXT contains 'GEOMETRIC MEAN'",
            "why_blocked": "T5 leaves geometric-mean comments as EXPLICIT_UNRESOLVED",
            "include_reason": "Preferred fixture: aggregation semantics; Farmington permit footnotes exist in corpus",
            **{k: geom[k] for k in ("n_occurrences", "occurrence_ids", "failure_kind", "relation")},
        },
        {
            "obligation_id": "pass_fail",
            "requirement_schema": "pass_fail_reporting_semantics",
            "exact_semantic_question": "What does PASS=0 / FAIL=1 reporting mean, and is it a numeric concentration comparison?",
            "declared_purposes": ["A", "B", "C"],
            "relation_contract": "binary pass/fail coding is not ordinary concentration comparison",
            "source_field_value": "DMR_COMMENT_TEXT contains 'PASS = 0' and 'FAIL = 1'",
            "why_blocked": "T5 leaves pass/fail comments EXPLICIT_UNRESOLVED",
            "include_reason": "Preferred fixture: binary coding; sibling leakage control vs WHEN DISCHARGING / geometric mean",
            **{k: pf[k] for k in ("n_occurrences", "occurrence_ids", "failure_kind", "relation")},
        },
        {
            "obligation_id": "empty_numeric_limit",
            "requirement_schema": empty["requirement_schema"],
            "exact_semantic_question": "When LIMIT_VALUE_NMBR is empty, is the row a numeric limit, report-only monitoring, or something else?",
            "declared_purposes": ["A"],
            "relation_contract": "empty numeric limit must be classified before comparison; absence is not a denial",
            "source_field_value": "LIMIT_VALUE_NMBR empty",
            "why_blocked": "T5 drops empty-limit rows from numeric_comparison_candidate without a named classification hole",
            "include_reason": "Preferred fixture #6: empty numeric / report-only; present in structured sources though T5 did not emit a hole",
            "n_occurrences": empty["n_occurrences"],
            "occurrence_ids": empty["occurrence_ids"],
            "failure_kind": empty["failure_kind"],
            "relation": empty["relation"],
        },
        {
            "obligation_id": "document_authority",
            "requirement_schema": "permit_document_text_not_available",
            "exact_semantic_question": "Without ranking from filenames, what do inventoried permit documents establish, and which document governs if they disagree?",
            "declared_purposes": ["B", "C"],
            "relation_contract": "narrative conditions require document text; filename kind is not hierarchy",
            "source_field_value": "document_inventory.json kinds (final_permit, fact_sheet, ...)",
            "why_blocked": "T5 inventories 12 documents and leaves narrative text EXPLICIT_UNRESOLVED",
            "include_reason": "Preferred fixture: document authority; text is in the frozen corpus, legal hierarchy may not be",
            **{k: doc[k] for k in ("n_occurrences", "occurrence_ids", "failure_kind", "relation")},
        },
        {
            "obligation_id": "monitoring_frequency",
            "requirement_schema": "monitoring_frequency_code",
            "exact_semantic_question": "What monitoring frequencies do opaque LIMIT_FREQ_OF_ANALYSIS_CODE values (e.g. 05/WK, 01/07, 01/01) establish?",
            "declared_purposes": ["B"],
            "relation_contract": "frequency codes must be interpreted for monitoring obligations",
            "source_field_value": "LIMIT_FREQ_OF_ANALYSIS_CODE nonempty",
            "why_blocked": "T5 require_interpreted with known=[''] leaves all codes UNINTERPRETED",
            "include_reason": "Additional purpose-reachable codebook-shaped obligation (empty-numeric is included separately; sample-type is a sibling leftover)",
            **{k: freq[k] for k in ("n_occurrences", "occurrence_ids", "failure_kind", "relation")},
        },
    ]
    for spec in specs:
        spec["current_epistemic_status"] = "UNRESOLVED"
        spec["known_structured_evidence"] = "structured CSVs + document inventory; no codebook table in structured sources"
        spec["examples"] = spec["occurrence_ids"][:4]
    return specs


def _trim_row(row: dict, keys: tuple[str, ...]) -> dict:
    return {k: row.get(k) for k in keys if k in row}


def local_structured_context(occurrence_id: str) -> dict:
    """Row-local context for Arm A. Not a factorized sibling obligation."""
    dmr_keys = (
        "EXTERNAL_PERMIT_NMBR",
        "PARAMETER_CODE",
        "PARAMETER_DESC",
        "MONITORING_PERIOD_END_DATE",
        "DMR_FORM_VALUE_ID",
        "DMR_VALUE_NMBR",
        "NODI_CODE",
        "LIMIT_VALUE_ID",
        "LIMIT_SET_SCHEDULE_ID",
        "LIMIT_VALUE_NMBR",
        "LIMIT_FREQ_OF_ANALYSIS_CODE",
        "LIMIT_SAMPLE_TYPE_CODE",
        "LIMIT_UNIT_DESC",
    )
    limit_keys = (
        "EXTERNAL_PERMIT_NMBR",
        "PARAMETER_CODE",
        "PARAMETER_DESC",
        "LIMIT_VALUE_ID",
        "LIMIT_SET_SCHEDULE_ID",
        "LIMIT_VALUE_NMBR",
        "LIMIT_FREQ_OF_ANALYSIS_CODE",
        "LIMIT_SAMPLE_TYPE_CODE",
        "DMR_COMMENT_TEXT",
        "LIMIT_UNIT_DESC",
        "STATISTICAL_BASE_CODE",
    )
    if occurrence_id.startswith("measurement:dmr_form_value_id="):
        vid = occurrence_id.split("=", 1)[1]
        with DMR.open(encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                if str(row.get("DMR_FORM_VALUE_ID") or "") == vid:
                    return {"table": "dmr_measurements.csv", "row": _trim_row(row, dmr_keys)}
        return {"table": "dmr_measurements.csv", "row": None, "lookup": vid}
    lid = sid = None
    if occurrence_id.startswith("permit_limit_row:"):
        rest = occurrence_id.split(":", 1)[1]
        parts = dict(p.split("=", 1) for p in rest.split("|") if "=" in p)
        lid = parts.get("limit_value_id")
        sid = parts.get("limit_set_schedule_id")
    elif "|" in occurrence_id and not occurrence_id.startswith("measurement:"):
        lid, sid = occurrence_id.split("|", 1)
    if lid and sid:
        with LIMITS.open(encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                if str(row.get("LIMIT_VALUE_ID") or "") == lid and str(row.get("LIMIT_SET_SCHEDULE_ID") or "") == sid:
                    return {"table": "permit_limits.csv", "row": _trim_row(row, limit_keys)}
        return {"table": "permit_limits.csv", "row": None, "lookup": f"{lid}|{sid}"}
    if occurrence_id == "document_inventory.json":
        return {"table": "document_inventory.json", "row": {"n_documents": len(document_inventory())}}
    return {"table": None, "occurrence_id": occurrence_id}


def host_visible_obligation(spec: dict) -> dict:
    return {
        "obligation_id": spec["obligation_id"],
        "requirement_schema": spec["requirement_schema"],
        "exact_semantic_question": spec["exact_semantic_question"],
        "declared_purposes": spec["declared_purposes"],
        "relation_contract": spec["relation_contract"],
        "source_field_value": spec["source_field_value"],
        "affected_occurrence_count": spec["n_occurrences"],
        "representative_examples": spec["examples"],
        "why_computation_is_blocked": spec["why_blocked"],
        "known_structured_evidence": spec["known_structured_evidence"],
        "current_epistemic_status": spec["current_epistemic_status"],
    }


def host_visible_occurrence(case: dict) -> dict:
    """Arm A host payload: one occurrence, no factorized sibling obligation id."""
    return {
        "occurrence_id": case["occurrence_id"],
        "purpose": case["purpose"],
        "requirement": case["requirement_schema"],
        "local_structured_context": case.get("local_structured_context") or local_structured_context(case["occurrence_id"]),
        "task": "Determine the semantic issue needed for THIS ONE occurrence. You are not given sibling rows or a reusable obligation covering them.",
    }


def establishability() -> dict:
    return {
        "nodi_c": {
            "label": "NOT_ESTABLISHABLE_IN_CORPUS",
            "note": "No NODI legend/codebook in permit packages or structured CSVs. Gold is hidden and is not corpus evidence.",
        },
        "nodi_9": {
            "label": "NOT_ESTABLISHABLE_IN_CORPUS",
            "note": "Same as C: no official code-9 definition in the frozen permit text or CSVs.",
        },
        "when_discharging": {
            "label": "ESTABLISHABLE_IN_CORPUS",
            "note": "Aztec statement of basis: flow/TRC/pH monitored when discharging. CSV comment WHEN DISCHARGING on NM0028762 limits. Period-level discharge occurrence is a separate factual question.",
        },
        "geometric_mean": {
            "label": "ESTABLISHABLE_IN_CORPUS",
            "note": "Farmington final permit footnotes *6/*7: report geometric mean of weekly TDS values; matches CSV comment language. Does not by itself reassign BOD rows that inherited a TDS comment.",
        },
        "pass_fail": {
            "label": "ESTABLISHABLE_IN_CORPUS",
            "note": "Structured DMR_COMMENT_TEXT itself states PASS=0 FAIL=1 reporting for WET; Farmington permit footnote *9 points to Part II WET conditions. Encoding is in the structured comment.",
        },
        "empty_numeric_limit": {
            "label": "UNCERTAIN_ESTABLISHABILITY",
            "note": "Empty LIMIT_VALUE_NMBR is visible in CSV; some WET/pass-fail rows are empty by design. Permit text may classify WET as report-only, but not every empty cell has a matching clause.",
        },
        "document_authority": {
            "label": "UNCERTAIN_ESTABLISHABILITY",
            "note": "Document bodies exist, so some narrative conditions are readable. A general final-permit-over-fact-sheet legal hierarchy is not clearly established as a single corpus sentence covering all facilities.",
        },
        "monitoring_frequency": {
            "label": "NOT_ESTABLISHABLE_IN_CORPUS",
            "note": "No frequency codebook mapping 05/WK etc. in the frozen permit packages. NMIP is referenced but not included as a source file.",
        },
    }


def arm_a_sample(specs: list[dict]) -> list[dict]:
    # ~20 occurrence-level cases. Varied obligations, not only easy ones.
    plan = [
        ("nodi_c", 3),
        ("nodi_9", 3),
        ("when_discharging", 3),
        ("geometric_mean", 2),
        ("pass_fail", 2),
        ("empty_numeric_limit", 2),
        ("document_authority", 1),
        ("monitoring_frequency", 4),
    ]
    by_id = {s["obligation_id"]: s for s in specs}
    samples = []
    n = 0
    for oid, k in plan:
        spec = by_id[oid]
        ids = spec["occurrence_ids"][:k]
        for occ in ids:
            n += 1
            samples.append(
                {
                    "case_id": f"A{n:02d}",
                    "obligation_id": oid,
                    "occurrence_id": occ,
                    "question": spec["exact_semantic_question"],
                    "purpose": spec["declared_purposes"],
                    "requirement_schema": spec["requirement_schema"],
                    "source_field_value": spec["source_field_value"],
                    "local_structured_context": local_structured_context(occ),
                }
            )
    return samples


def dump(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")


def freeze() -> dict:
    FROZEN.mkdir(parents=True, exist_ok=True)
    EVALUATOR_ONLY.mkdir(parents=True, exist_ok=True)
    public = _load(PUBLIC)
    candidates = compile_candidates()
    empty_rows = empty_limit_rows()
    specs = selected_specs(candidates, empty_rows)
    samples = arm_a_sample(specs)
    baseline = {
        "draft_trial": DRAFT_TRIAL,
        "n_hole_groups": public.get("n_hole_groups"),
        "n_hole_instances": public.get("n_hole_instances"),
        "relation_row_counts": public.get("relation_row_counts"),
        "requirement_names_unique": sorted({n for n in public.get("requirement_names") or []}),
        "n_documents": len(document_inventory()),
        "n_permit_text_files": len(list(PERMIT_TEXT.glob("*/*.txt"))),
    }
    dump(FROZEN / "baseline.json", baseline)
    dump(FROZEN / "candidate_obligations.json", candidates)
    dump(
        FROZEN / "selected_obligations.json",
        {
            "selection_rule": (
                "Prefer the eight fixture evidence-shapes listed in the probe brief. "
                "Split NODI by code (C vs 9). Include empty LIMIT_VALUE_NMBR even though T5 emitted no named hole. "
                "Replace nothing as unresolved leftovers: all preferred fixtures are present except a dedicated report-only named hole, "
                "which is covered by empty_numeric_limit. Add monitoring_frequency as the extra purpose-reachable codebook obligation. "
                "Do not select only easy/establishable cases."
            ),
            "obligations": specs,
            "host_visible": [host_visible_obligation(s) for s in specs],
        },
    )
    dump(FROZEN / "arm_a_sample.json", samples)
    dump(EVALUATOR_ONLY / "establishability.json", establishability())
    dump(EVALUATOR_ONLY / "empty_limit_rows.json", empty_rows)
    dump(
        FROZEN / "negative_controls.json",
        {
            "nodi_9_must_not_apply_to": "nodi_c",
            "nodi_c_must_not_apply_to": "nodi_9",
            "when_discharging_must_not_apply_to": ["geometric_mean", "pass_fail"],
            "document_authority_must_not_rank": "every other document kind from filename alone",
        },
    )
    (EVALUATOR_ONLY / "README.md").write_text(
        "Evaluator-only establishability audit. Never copy into a host workspace. Not GOLD answers.\n",
        encoding="utf-8",
    )
    (FROZEN / "experiment_freeze.md").write_text(
        "\n".join(
            [
                "# Obligation-targeted resolution v1 — freeze",
                "",
                f"Draft spine: sealed {DRAFT_TRIAL}",
                f"Candidates: {len(candidates)}",
                f"Selected: {len(specs)}",
                f"Arm A samples: {len(samples)}",
                "Host may read permit document text copies. Host must not see GOLD or establishability.json.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return {"n_candidates": len(candidates), "n_selected": len(specs), "n_arm_a": len(samples)}


if __name__ == "__main__":
    print(json.dumps(freeze(), indent=2))
