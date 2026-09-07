#!/usr/bin/env python3
"""P7 purpose derivation compiler.

Reads compiled world relations from world.sqlite and writes Purpose A/B/C
output JSON under purpose_ir/. Distinguishes required vs optional premises
and blocking vs non-blocking unresolved states per 07_derivations.json.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from taskview import TaskView

FY2025_START = "2024-10-01"
FY2025_END = "2025-09-30"
VIEW_ID = "diligence-world"

ROOT = Path(__file__).resolve().parents[2]
WORLD_CANDIDATES = [ROOT / "06_world" / "world.sqlite", ROOT / "world" / "world.sqlite"]


def resolve_world_path() -> Path:
    for candidate in WORLD_CANDIDATES:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        "world.sqlite not found; expected 06_world/world.sqlite or world/world.sqlite"
    )


def referent_suffix(referent_id: str) -> str:
    if ":" in referent_id:
        return referent_id.split(":", 1)[1]
    return referent_id


def grounding_ref(relation: str, **keys: str) -> dict[str, str]:
    location = ", ".join(f"{k}={v}" for k, v in keys.items())
    return {"source_path": f"world.sqlite/{relation}", "location": location}


def compare_values(
    measurement: float, limit: float, qualifier: str
) -> str:
    q = (qualifier or "").strip()
    if q in ("<=", "<"):
        return "exceeds_limit" if measurement > limit else "within_limit"
    if q in (">=", ">"):
        return "exceeds_limit" if measurement < limit else "within_limit"
    return "comparison_not_applicable"


def units_comparable(dmr_unit: str, standard_unit: str) -> bool:
    dmr_unit = (dmr_unit or "").strip()
    standard_unit = (standard_unit or "").strip()
    if not dmr_unit or not standard_unit:
        return False
    return dmr_unit == standard_unit


def load_referent_labels(tv: TaskView) -> dict[str, str]:
    rows = tv.query("SELECT id, label FROM _tv_referents")
    return {row["id"]: row["label"] for row in rows}


def derive_purpose_a(tv: TaskView, labels: dict[str, str]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []

    pairs = tv.query(
        """
        SELECT
            p.measurement_id,
            p.limit_row_id,
            p.facility_id,
            p.feature_id,
            p.parameter_id,
            p.period_id,
            mp.period_end_date,
            pf.feature_number,
            par.parameter_code,
            par.parameter_description,
            d.value_kind,
            d.dmr_value_nmbr,
            d.dmr_unit_code,
            d.nodi_code,
            d.dmr_value_qualifier_code,
            l.has_numeric_value,
            l.limit_value_nmbr,
            l.standard_unit_code,
            l.limit_unit_code,
            l.limit_value_qualifier_code,
            l.statistical_base_code,
            lsf.limit_type_code,
            lsf.optional_monitoring_flag
        FROM measurement_limit_evaluation_pair p
        JOIN fy2025_in_scope_measurement fy ON fy.measurement_id = p.measurement_id
        JOIN dmr_reported_value_kind d ON d.measurement_id = p.measurement_id
        JOIN limit_value_attributes l ON l.limit_row_id = p.limit_row_id
        JOIN limit_source_flags lsf ON lsf.limit_row_id = p.limit_row_id
        JOIN monitoring_period mp ON mp.period_id = p.period_id
        JOIN permit_feature pf ON pf.feature_id = p.feature_id
        JOIN parameter par ON par.parameter_id = p.parameter_id
        WHERE fy.in_fy2025 = 1
        ORDER BY p.facility_id, mp.period_end_date, par.parameter_code
        """
    )

    for pair in pairs:
        facility = referent_suffix(pair["facility_id"])
        evidence = [
            grounding_ref("measurement_limit_evaluation_pair", measurement_id=pair["measurement_id"], limit_row_id=pair["limit_row_id"]),
            grounding_ref("dmr_reported_value_kind", measurement_id=pair["measurement_id"]),
            grounding_ref("limit_value_attributes", limit_row_id=pair["limit_row_id"]),
            grounding_ref("limit_source_flags", limit_row_id=pair["limit_row_id"]),
        ]

        base = {
            "facility": facility,
            "facility_label": labels.get(pair["facility_id"], ""),
            "feature": pair["feature_number"],
            "parameter_code": pair["parameter_code"],
            "parameter_description": pair["parameter_description"],
            "monitoring_period_end": pair["period_end_date"],
            "measurement_id": pair["measurement_id"],
            "limit_row_id": pair["limit_row_id"],
            "grounding": evidence,
        }

        value_kind = pair["value_kind"]
        has_numeric = bool(pair["has_numeric_value"])
        optional_mon = (pair["optional_monitoring_flag"] or "").upper() == "Y"

        if value_kind != "numeric":
            row = {
                **base,
                "limit_category": "no_numeric_comparison",
                "comparison_outcome": "comparison_not_applicable",
                "policy_basis": "non_numeric_dmr_value_kind",
            }
            rows.append(row)
            continue

        if not has_numeric:
            row = {
                **base,
                "limit_category": "no_numeric_comparison",
                "comparison_outcome": "comparison_not_applicable",
                "policy_basis": "limit_has_no_numeric_value",
            }
            rows.append(row)
            continue

        if optional_mon:
            row = {
                **base,
                "limit_category": "report_only",
                "comparison_outcome": "comparison_not_applicable",
                "policy_basis": "optional_monitoring_flag",
            }
            rows.append(row)
            continue

        if (pair["limit_type_code"] or "") != "ENF":
            row = {
                **base,
                "limit_category": "report_only",
                "comparison_outcome": "comparison_not_applicable",
                "policy_basis": "non_enf_limit_type",
            }
            rows.append(row)
            continue

        if not units_comparable(pair["dmr_unit_code"], pair["standard_unit_code"]):
            unresolved.append(
                {
                    **base,
                    "unresolved_state": "limit_measurement_unit_mismatch_unresolved",
                    "reason": (
                        "Numeric measurement and limit are present but dmr_unit_code "
                        f"({pair['dmr_unit_code']!r}) does not match standard_unit_code "
                        f"({pair['standard_unit_code']!r}); numeric comparison blocked."
                    ),
                    "evidence_consulted": evidence,
                    "blocking": True,
                }
            )
            continue

        comparison = compare_values(
            float(pair["dmr_value_nmbr"]),
            float(pair["limit_value_nmbr"]),
            pair["limit_value_qualifier_code"],
        )

        row = {
            **base,
            "limit_category": "enforceable_numeric",
            "comparison_outcome": comparison,
            "limit_value": pair["limit_value_nmbr"],
            "measurement_value": pair["dmr_value_nmbr"],
            "limit_unit_code": pair["standard_unit_code"],
            "limit_qualifier": pair["limit_value_qualifier_code"],
            "statistical_base_code": pair["statistical_base_code"],
            "policy_basis": "enforceability_threshold_enf_numeric_aligned_units",
        }
        rows.append(row)

    return {
        "purpose": "applicable_discharge_limits",
        "rows": rows,
        "unresolved": unresolved,
    }


def derive_purpose_b(tv: TaskView, labels: dict[str, str]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []

    candidates = tv.query(
        """
        SELECT
            m.requirement_id,
            m.facility_id,
            m.feature_id,
            m.parameter_id,
            m.limit_row_id,
            m.frequency_code,
            m.sample_type_code,
            p.period_id,
            p.period_end_date,
            pf.feature_number,
            par.parameter_code,
            par.parameter_description,
            le.overlaps AS limit_effective,
            lsa.active_in_month AS season_active,
            CASE
                WHEN EXISTS (
                    SELECT 1 FROM conditional_trigger_language ctl
                    WHERE ctl.limit_row_id = m.limit_row_id
                ) THEN 1
                ELSE 0
            END AS has_trigger
        FROM monitoring_requirement_candidate m
        JOIN monitoring_period p ON p.facility_id = m.facility_id
        JOIN permit_feature pf ON pf.feature_id = m.feature_id
        JOIN parameter par ON par.parameter_id = m.parameter_id
        LEFT JOIN limit_effective_during_period le
            ON le.limit_row_id = m.limit_row_id AND le.period_id = p.period_id
        LEFT JOIN limit_season_month_active lsa
            ON lsa.limit_row_id = m.limit_row_id
            AND lsa.calendar_month = CAST(substr(p.period_end_date, 6, 2) AS INTEGER)
        WHERE p.period_end_date BETWEEN ? AND ?
        ORDER BY m.facility_id, p.period_end_date, par.parameter_code
        """,
        (FY2025_START, FY2025_END),
    )

    for item in candidates:
        facility = referent_suffix(item["facility_id"])
        evidence = [
            grounding_ref("monitoring_requirement_candidate", requirement_id=item["requirement_id"]),
            grounding_ref("monitoring_period", period_id=item["period_id"]),
        ]

        base = {
            "facility": facility,
            "facility_label": labels.get(item["facility_id"], ""),
            "feature": item["feature_number"],
            "parameter_code": item["parameter_code"],
            "parameter_description": item["parameter_description"],
            "monitoring_period_end": item["period_end_date"],
            "requirement_id": item["requirement_id"],
            "frequency_code": item["frequency_code"],
            "sample_type_code": item["sample_type_code"],
            "grounding": evidence,
        }

        if not item["limit_effective"]:
            rows.append(
                {
                    **base,
                    "applicability_verdict": "not_required",
                    "condition_basis": "limit_not_effective_during_period",
                    "policy_basis": "temporal_scope_excludes_period",
                }
            )
            continue

        if item["season_active"] == 0:
            rows.append(
                {
                    **base,
                    "applicability_verdict": "not_required",
                    "condition_basis": "out_of_season",
                    "policy_basis": "limit_season_month_active",
                }
            )
            continue

        if item["has_trigger"]:
            unresolved.append(
                {
                    **base,
                    "unresolved_state": "conditional_trigger_evidence_insufficient",
                    "reason": (
                        "Conditional trigger language is present for the limit row but "
                        "discharge_occurrence_evidence and conditional_monitoring_relief_evidence "
                        "have no ACCEPT-grounded tuples in world.sqlite."
                    ),
                    "evidence_consulted": evidence
                    + [
                        grounding_ref(
                            "conditional_trigger_language",
                            limit_row_id=item["limit_row_id"],
                        )
                    ],
                    "blocking": True,
                }
            )
            continue

        rows.append(
            {
                **base,
                "applicability_verdict": "required",
                "condition_basis": "schedule_and_temporal_scope",
                "policy_basis": "no_conditional_trigger_mechanical_schedule",
                "grounding": evidence
                + [
                    grounding_ref(
                        "limit_effective_during_period",
                        limit_row_id=item["limit_row_id"],
                        period_id=item["period_id"],
                    ),
                    grounding_ref(
                        "limit_season_month_active",
                        limit_row_id=item["limit_row_id"],
                        calendar_month=str(int(item["period_end_date"][5:7])),
                    ),
                ],
            }
        )

    return {
        "purpose": "monitoring_obligations",
        "rows": rows,
        "unresolved": unresolved,
    }


def derive_purpose_c(
    tv: TaskView,
    labels: dict[str, str],
    purpose_b: dict[str, Any],
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []

    b_required = {
        (row["requirement_id"], row["monitoring_period_end"])
        for row in purpose_b["rows"]
        if row.get("applicability_verdict") == "required"
    }
    b_not_required = {
        (row["requirement_id"], row["monitoring_period_end"])
        for row in purpose_b["rows"]
        if row.get("applicability_verdict") == "not_required"
    }

    nodi_cases = tv.query(
        """
        SELECT
            d.measurement_id,
            m.facility_id,
            m.feature_id,
            m.parameter_id,
            m.period_id,
            mp.period_end_date,
            pf.feature_number,
            par.parameter_code,
            par.parameter_description,
            d.value_kind,
            d.nodi_code,
            d.dmr_value_qualifier_code
        FROM dmr_reported_value_kind d
        JOIN dmr_measurement_extract_row m ON m.measurement_id = d.measurement_id
        JOIN fy2025_in_scope_measurement fy ON fy.measurement_id = d.measurement_id
        JOIN monitoring_period mp ON mp.period_id = m.period_id
        JOIN permit_feature pf ON pf.feature_id = m.feature_id
        JOIN parameter par ON par.parameter_id = m.parameter_id
        WHERE fy.in_fy2025 = 1
          AND d.value_kind IN ('nodi', 'qualifier_only')
        ORDER BY m.facility_id, mp.period_end_date, par.parameter_code
        """
    )

    for case in nodi_cases:
        facility = referent_suffix(case["facility_id"])
        evidence = [
            grounding_ref("dmr_reported_value_kind", measurement_id=case["measurement_id"]),
            grounding_ref("dmr_measurement_extract_row", measurement_id=case["measurement_id"]),
        ]
        base = {
            "facility": facility,
            "facility_label": labels.get(case["facility_id"], ""),
            "feature": case["feature_number"],
            "parameter_code": case["parameter_code"],
            "parameter_description": case["parameter_description"],
            "monitoring_period_end": case["period_end_date"],
            "expectation_id": f"expectation:numeric_absent:{referent_suffix(case['measurement_id'])}",
            "measurement_id": case["measurement_id"],
            "grounding": evidence,
        }

        nodi_code = (case["nodi_code"] or "").strip()
        qualifier = (case["dmr_value_qualifier_code"] or "").strip()
        if nodi_code or qualifier:
            rows.append(
                {
                    **base,
                    "established_state": "other_documented_no_data_state",
                    "evidence_summary": (
                        f"DMR value_kind={case['value_kind']}"
                        + (f", nodi_code={nodi_code}" if nodi_code else "")
                        + (f", qualifier={qualifier}" if qualifier else "")
                    ),
                    "policy_basis": "mechanical_nodata_code_present",
                }
            )
        else:
            unresolved.append(
                {
                    **base,
                    "unresolved_state": "nodata_reason_ambiguous",
                    "reason": "Non-numeric DMR result lacks grounded NODI code or qualifier narrative.",
                    "evidence_consulted": evidence,
                    "blocking": True,
                }
            )

    absent_cases = tv.query(
        """
        SELECT
            e.expectation_id,
            e.requirement_id,
            e.period_id,
            e.facility_id,
            mp.period_end_date,
            m.feature_id,
            m.parameter_id,
            pf.feature_number,
            par.parameter_code,
            par.parameter_description
        FROM expected_monitoring_without_dmr_row e
        JOIN monitoring_requirement_candidate m ON m.requirement_id = e.requirement_id
        JOIN monitoring_period mp ON mp.period_id = e.period_id
        JOIN permit_feature pf ON pf.feature_id = m.feature_id
        JOIN parameter par ON par.parameter_id = m.parameter_id
        WHERE mp.period_end_date BETWEEN ? AND ?
        ORDER BY e.facility_id, mp.period_end_date, par.parameter_code
        """,
        (FY2025_START, FY2025_END),
    )

    for case in absent_cases:
        facility = referent_suffix(case["facility_id"])
        period_end = case["period_end_date"]
        req_id = case["requirement_id"]
        evidence = [
            grounding_ref("expected_monitoring_without_dmr_row", expectation_id=case["expectation_id"]),
            grounding_ref("monitoring_requirement_candidate", requirement_id=req_id),
        ]
        base = {
            "facility": facility,
            "facility_label": labels.get(case["facility_id"], ""),
            "feature": case["feature_number"],
            "parameter_code": case["parameter_code"],
            "parameter_description": case["parameter_description"],
            "monitoring_period_end": period_end,
            "expectation_id": case["expectation_id"],
            "requirement_id": req_id,
            "grounding": evidence,
        }

        key = (req_id, period_end)
        if key in b_not_required:
            rows.append(
                {
                    **base,
                    "established_state": "conditional_monitoring_not_required",
                    "evidence_summary": "Purpose B establishes monitoring not required for this requirement-period.",
                    "policy_basis": "cross_purpose_b_not_required",
                }
            )
        elif key in b_required:
            rows.append(
                {
                    **base,
                    "established_state": "required_monitoring_lacks_adequate_evidence",
                    "evidence_summary": (
                        "Monitoring is required per Purpose B schedule evaluation but no "
                        "corresponding DMR measurement row is present."
                    ),
                    "policy_basis": "absent_dmr_with_required_monitoring",
                }
            )
        else:
            unresolved.append(
                {
                    **base,
                    "unresolved_state": "adequacy_of_evidence_cannot_be_determined",
                    "reason": (
                        "Purpose B applicability for this requirement-period is unresolved; "
                        "cannot classify absent DMR evidence."
                    ),
                    "evidence_consulted": evidence,
                    "blocking": True,
                }
            )

    return {
        "purpose": "missing_evidence_semantics",
        "rows": rows,
        "unresolved": unresolved,
    }


def write_output(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    world_path = resolve_world_path()
    with TaskView(world_path, view_id=VIEW_ID) as tv:
        labels = load_referent_labels(tv)

        purpose_a = derive_purpose_a(tv, labels)
        purpose_b = derive_purpose_b(tv, labels)
        purpose_c = derive_purpose_c(tv, labels, purpose_b)

    write_output(ROOT / "purpose_ir" / "a" / "output.json", purpose_a)
    write_output(ROOT / "purpose_ir" / "b" / "output.json", purpose_b)
    write_output(ROOT / "purpose_ir" / "c" / "output.json", purpose_c)

    print(f"Wrote purpose_ir/a/output.json ({len(purpose_a['rows'])} rows, {len(purpose_a['unresolved'])} unresolved)")
    print(f"Wrote purpose_ir/b/output.json ({len(purpose_b['rows'])} rows, {len(purpose_b['unresolved'])} unresolved)")
    print(f"Wrote purpose_ir/c/output.json ({len(purpose_c['rows'])} rows, {len(purpose_c['unresolved'])} unresolved)")


if __name__ == "__main__":
    main()
