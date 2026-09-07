"""Host-visible obligation briefs copied from the sealed conversational freeze. No GOLD."""

from __future__ import annotations

ISSUES = [
    {
        "id": "unique_applicable_limit",
        "title": "How many governing numeric limits apply to one measurement?",
        "purpose": "A — applicable discharge limits for Federal FY2025",
        "requirement_contract": {
            "name": "unique_applicable_limit_per_measurement",
            "kind": "UNIQUE",
            "per": "measurement",
            "candidates": "measurement_limit_pair",
            "cardinality": "ONE",
        },
        "relations": [
            "dmr_measurement (824 rows)",
            "permit_limit (105 rows)",
            "fy2025_measurement (824)",
            "measurement_limit_pair (824) — derived by matching permit, outfall, parameter, and whether the monitoring period falls in the limit begin/end dates",
            "numeric_comparison_candidate (342)",
        ],
        "affected_scope": "824 FY2025 measurement–limit pairs; uniqueness currently SATISFIED (no cardinality hole)",
        "structured_evidence": [
            "permit_limits.csv fields LIMIT_BEGIN_DATE, LIMIT_END_DATE, LIMIT_VALUE_ID, LIMIT_SET_SCHEDULE_ID",
            "dmr_measurements.csv MONITORING_PERIOD_END_DATE, PARAMETER_CODE, PERM_FEATURE_NMBR",
            "FY2025 window 2024-10-01 through 2025-09-30",
        ],
        "evidence_snippets": [],
        "current_interpretation": (
            "The draft treats each FY2025 measurement as needing exactly one applicable numeric limit after "
            "intersecting the monitoring period with the limit's effective interval. It does not currently emit "
            "a uniqueness hole — the join produced one pair per measurement."
        ),
        "remaining_uncertainty": (
            "Whether overlapping or staged interval rows should remain separate identities rather than being "
            "forced to a single governing limit; whether catalog restatements of the same limit should count as multiples."
        ),
        "status": "requirement authored; currently satisfied on this fixture",
    },
    {
        "id": "nodi_semantics",
        "title": "What do missing-result / NODI codes mean?",
        "purpose": "C — missing-evidence semantics",
        "requirement_contract": {
            "name": "nodi_code_semantics",
            "kind": "INTERPRETED",
            "relation": "no_numeric_result_case",
            "field": "nodi_code",
            "known": [""],
        },
        "relations": ["no_numeric_result_case (186 rows)", "dmr_measurement"],
        "affected_scope": "186 uninterpreted NODI cases: code C on 150 rows, code 9 on 36 rows",
        "structured_evidence": [
            "dmr_measurements.csv NODI_CODE",
            "empty DMR_VALUE_NMBR on these rows",
        ],
        "evidence_snippets": [
            "NODI_CODE='C' (150 cases)",
            "NODI_CODE='9' (36 cases)",
        ],
        "current_interpretation": (
            "The draft refuses to treat NODI codes as self-explaining. It requires interpretation and leaves "
            "all nonempty codes unresolved. It does not assign 'no discharge' or 'not required' to either code."
        ),
        "remaining_uncertainty": "What C vs 9 establish for missing-evidence classification; whether they are interchangeable.",
        "status": "UNINTERPRETED hole",
    },
    {
        "id": "document_authority",
        "title": "What do inventoried permit documents establish without their text?",
        "purpose": "B/C — narrative conditions and source authority",
        "requirement_contract": {
            "name": "permit_document_text_not_available",
            "kind": "UNRESOLVED",
            "relation": "permit_document",
        },
        "relations": ["permit_document (12 rows)"],
        "affected_scope": "12 inventoried documents; 1 explicit unresolved (narrative text not in structured sources)",
        "structured_evidence": [
            "document_inventory.json: filename, document_kind, bytes, sha256 — no body text",
        ],
        "evidence_snippets": [
            "document_kind=final_permit",
            "document_kind=fact_sheet",
            "document_kind=statement_of_basis",
            "document_kind=reasonable_potential",
            "document_kind=minor_modification",
        ],
        "current_interpretation": (
            "Documents are inventoried by kind and hash only. The draft leaves narrative permit conditions unresolved "
            "rather than ranking fact sheet vs final permit from filenames."
        ),
        "remaining_uncertainty": "Which document would be authoritative if text were present; whether filename kinds imply hierarchy.",
        "status": "EXPLICIT_UNRESOLVED",
    },
]
