"""Compose State C construction from sealed T1 WHEN DISCHARGING + T3 pass/fail deltas.

Does not re-adjudicate. Does not repair T1's empty binary_pass_fail mapping.
T3 is used because it is a supported pass/fail resolution whose disposable
propagation materialized 8 pass_fail_outcome_reporting rows.
"""

from __future__ import annotations

from pathlib import Path

from research.semantic_integration.domains.npdes.end_to_end_programmability_v0.paths import (
    WD_CONSTRUCTION,
)

HELPERS = '''
def _is_pass_fail_unit(unit_desc: object) -> bool:
    normalized = _text(unit_desc).lower().replace(" ", "")
    return "pass=0" in normalized and "fail=1" in normalized


def _is_pass_fail_comment(comment: object) -> bool:
    upper = _text(comment).upper()
    return "PASS = 0" in upper and "FAIL = 1" in upper


def _is_established_pass_fail_reporting(
    limit_unit_desc: object,
    comment: object,
) -> bool:
    return _is_pass_fail_unit(limit_unit_desc) and _is_pass_fail_comment(comment)

'''

OUTCOME_BLOCK = '''
    pass_fail_outcome_rows = [
        {
            "measurement": row["measurement"],
            "permit_limit_row": row["permit_limit_row"],
            "parameter": row["parameter"],
            "monitoring_period_end": row["monitoring_period_end"],
            "dmr_value_nmbr": row["dmr_value_nmbr"],
            "limit_unit_desc": row["limit_unit_desc"],
            "dmr_comment_text": row["dmr_comment_text"],
        }
        for row in measurement_limit_rows
        if row.get("is_pass_fail_outcome_unit") and row["has_reported_value"]
    ]
    world.derive(
        "pass_fail_outcome_reporting",
        pass_fail_outcome_rows,
        roles=[
            ("measurement", "REFERENT"),
            ("permit_limit_row", "REFERENT"),
            ("parameter", "REFERENT"),
            ("monitoring_period_end", "TEXT"),
            ("dmr_value_nmbr", "TEXT"),
            ("limit_unit_desc", "TEXT"),
            ("dmr_comment_text", "TEXT"),
        ],
        inputs=["measurement_limit_pair"],
        grounding={
            "vocabulary": "pass=0;fail=1",
            "outcome_meaning": {"0": "pass", "1": "fail"},
            "prior_proposal": "obligation_targeted_resolution_v1/arm_b/T3/pass_fail",
        },
        mode="PURPOSE",
    )

'''

REQUIREMENT_BLOCK = '''
    purpose.require_interpreted(
        "wet_pass_fail_outcome_code",
        relation="pass_fail_outcome_reporting",
        field="dmr_value_nmbr",
        known=["0", "1"],
        purpose=["A", "B", "C"],
        per="measurement",
    )

'''

OLD_PASS_FAIL_UNRESOLVED = '''        if "PASS = 0" in comment.upper() and "FAIL = 1" in comment.upper():
            purpose.unresolved(
                "pass_fail_reporting_semantics",
                subject=permit_limit_key,
                relation="measurement_limit_pair",
                reason="Permit limit uses pass/fail reporting semantics that require interpretation beyond ordinary numeric concentration comparison.",
                purpose=["A", "B", "C"],
                grounding={"dmr_comment_text": comment},
            )
'''

NEW_PASS_FAIL_UNRESOLVED = '''        if _is_pass_fail_comment(comment) and not _is_established_pass_fail_reporting(
            row.get("LIMIT_UNIT_DESC"), comment
        ):
            purpose.unresolved(
                "pass_fail_reporting_semantics",
                subject=permit_limit_key,
                relation="measurement_limit_pair",
                reason="Permit limit comment references pass/fail reporting but structured unit vocabulary is not established.",
                purpose=["A", "B", "C"],
                grounding={"dmr_comment_text": comment},
            )
'''

EXTRA_FIELDS = '''                "dmr_comment_text": _text(source_row["DMR_COMMENT_TEXT"]),
                "limit_freq_of_analysis_code": row["limit_freq_of_analysis_code"],
                "statistical_base_type_code": row["statistical_base_type_code"],
'''

EXTRA_FIELDS_NEW = '''                "dmr_comment_text": _text(source_row["DMR_COMMENT_TEXT"]),
                "limit_freq_of_analysis_code": row["limit_freq_of_analysis_code"],
                "statistical_base_type_code": row["statistical_base_type_code"],
                "limit_unit_desc": _text(source_row.get("LIMIT_UNIT_DESC")),
                "is_pass_fail_outcome_unit": _is_established_pass_fail_reporting(
                    source_row.get("LIMIT_UNIT_DESC"),
                    source_row["DMR_COMMENT_TEXT"],
                ),
                "dmr_value_nmbr": row["dmr_value_nmbr"],
'''


def compose_state_c_construction() -> str:
    text = WD_CONSTRUCTION.read_text(encoding="utf-8")
    needle = "def construct(source: Source, world: World, purpose: Purpose) -> None:"
    if needle not in text:
        raise RuntimeError("when_discharging construction missing construct()")
    if HELPERS.strip() not in text:
        text = text.replace(needle, HELPERS + needle, 1)
    if EXTRA_FIELDS not in text:
        raise RuntimeError("measurement_limit_rows field block not found")
    text = text.replace(EXTRA_FIELDS, EXTRA_FIELDS_NEW, 1)
    marker = '''    numeric_comparison_rows = [
        row
        for row in measurement_limit_rows
        if row["has_reported_value"] and row["has_limit_value_nmbr"]
    ]
'''
    if marker not in text:
        raise RuntimeError("numeric_comparison_rows block not found")
    if "pass_fail_outcome_reporting" not in text:
        text = text.replace(marker, OUTCOME_BLOCK + marker, 1)
    req_needle = '''    purpose.require_materializable(
        "monitoring_requirements_materializable",
        relation="monitoring_requirement_fy2025",
        purpose="B",
    )
'''
    if req_needle not in text:
        raise RuntimeError("monitoring_requirements_materializable not found")
    if "wet_pass_fail_outcome_code" not in text:
        text = text.replace(req_needle, REQUIREMENT_BLOCK + req_needle, 1)
    if OLD_PASS_FAIL_UNRESOLVED not in text:
        raise RuntimeError("WHEN-DISCHARGING pass_fail unresolved block not found")
    text = text.replace(OLD_PASS_FAIL_UNRESOLVED, NEW_PASS_FAIL_UNRESOLVED, 1)
    if "pass_fail_outcome_reporting" not in text or "wet_pass_fail_outcome_code" not in text:
        raise RuntimeError("State C compose incomplete")
    return text


def write_state_c_construction(dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(compose_state_c_construction(), encoding="utf-8")
    return dest
