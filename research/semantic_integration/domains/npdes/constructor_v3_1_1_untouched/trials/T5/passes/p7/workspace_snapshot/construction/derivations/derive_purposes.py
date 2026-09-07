#!/usr/bin/env python3
"""Compile Purpose A/B/C IR outputs from world relations and P5 adjudicated dispositions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from taskview import TaskView

ROOT = Path(__file__).resolve().parents[2]
DISPOSITIONS_PATH = ROOT / "05_dispositions.json"
WORLD_CANDIDATES = (ROOT / "06_world" / "world.sqlite", ROOT / "world" / "world.sqlite")

FY2025_START = "2024-10-01"
FY2025_END = "2025-09-30"

SENTINEL_VALUE = -9.999999e99


def find_world_db() -> Path:
    for candidate in WORLD_CANDIDATES:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        "world.sqlite not found; expected 06_world/world.sqlite or world/world.sqlite"
    )


def load_dispositions() -> list[dict[str, Any]]:
    with DISPOSITIONS_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def classify_limit_unresolved(rationale: str) -> str:
    text = rationale.lower()
    if "when discharging" in text or "conditional" in text:
        return "seasonal_conditional_or_event_condition_prevents_limit_selection"
    if "competing" in text or "multiple" in text:
        return "multiple_competing_applicable_limits_without_resolution_rule"
    if "no candidate" in text or "no limit" in text:
        return "measurement_present_but_no_candidate_limit_identified"
    if "insufficient" in text or "not established" in text:
        return "insufficient_permit_or_schedule_evidence_to_bind_limit_to_measurement"
    return "limit_applicability_unknown"


def classify_numeric_regime(rationale: str, disposition: str) -> str | None:
    if disposition == "UNRESOLVED":
        if "unit" in rationale.lower():
            return None
        return "not_numeric_comparable"
    text = rationale.lower()
    if "report-only" in text or "report only" in text:
        return "report_only"
    if "not subject to enforceable" in text or "not comparable" in text:
        return "not_numeric_comparable"
    if "enforceable numeric" in text:
        return "enforceable_numeric_comparison"
    return "enforceable_numeric_comparison"


def classify_numeric_unresolved(rationale: str) -> str:
    if "unit" in rationale.lower():
        return "unit_or_statistical_base_mismatch_precluding_comparison"
    return "limit_established_but_measurement_not_numeric_comparable"


def classify_exceedance_outcome(disposition: str, rationale: str) -> str | None:
    if disposition == "ACCEPT":
        return "exceeds"
    if disposition == "REJECT":
        return "does_not_exceed"
    return None


def classify_monitoring_unresolved(rationale: str) -> str:
    text = rationale.lower()
    if "discharge occurrence" in text or "when discharging" in text:
        return "discharge_occurrence_unknown"
    if "event" in text or "permit-year" in text or "permit year" in text:
        return "special_study_or_event_condition_not_documented"
    if "season" in text or "boundary" in text:
        return "season_or_permit_year_boundary_ambiguous"
    if "conflict" in text:
        return "conflicting_permit_provisions_without_hierarchy_rule"
    if "activation" in text or "schedule" in text:
        return "schedule_activation_status_unknown"
    if "identity" in text or "ambiguous" in text:
        return "requirement_identity_ambiguous_across_limit_sets"
    return "conditional_trigger_evidence_insufficient"


def classify_missing_evidence_unresolved(rationale: str) -> str:
    text = rationale.lower()
    if "nodi" in text:
        return "nodi_or_no_data_code_uninterpretable"
    if "conflict" in text:
        return "conflicting_documentation_of_no_discharge"
    if "identity" in text or "unclear" in text:
        return "monitoring_expectation_identity_unclear"
    if "distinguish" in text or "non-requirement" in text:
        return "insufficient_evidence_to_distinguish_no_requirement_from_missing_report"
    if "obligation" in text:
        return "schedule_present_but_obligation_status_unknown"
    if "partial" in text or "across" in text:
        return "partial_reporting_ambiguity_across_parameters_or_outfalls"
    return "nodi_or_no_data_code_uninterpretable"


def classify_missing_evidence_accept(disposition: str, rationale: str) -> str | None:
    if disposition != "ACCEPT":
        return None
    text = rationale.lower()
    if "no discharge" in text or "no-discharge" in text:
        return "documented_no_discharge_period"
    if "not required" in text or "non-requirement" in text:
        return "conditional_monitoring_not_required"
    if "inadequate" in text or "missing report" in text:
        return "required_monitoring_inadequate_evidence"
    if "no-data" in text or "no data" in text:
        return "other_documented_no_data_state"
    return None


def grounding_refs(grounding: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {"source_path": g["source_path"], "location": g["location"]}
        for g in grounding
    ]


def lookup_map(tv: TaskView, sql: str, key_col: str) -> dict[str, dict[str, Any]]:
    rows = tv.query_semantic(sql)
    return {row[key_col]: row for row in rows}


def derive_purpose_a(
    tv: TaskView, dispositions: list[dict[str, Any]]
) -> dict[str, Any]:
    limit_by_measurement = {
        d["values"]["measurement"]: d
        for d in dispositions
        if d["relation"] == "limit_applicability_judgment"
    }
    numeric_by_measurement = {
        d["values"]["measurement"]: d
        for d in dispositions
        if d["relation"] == "numeric_comparison_regime_judgment"
    }
    exceed_by_measurement = {
        d["values"]["measurement"]: d
        for d in dispositions
        if d["relation"] == "exceedance_judgment"
    }

    measurements = tv.query_semantic(
        """
        SELECT
            fy.measurement_id AS measurement,
            dma.facility_id AS facility,
            dma.discharge_point_id AS discharge_point,
            dma.parameter_id AS parameter,
            dma.monitoring_period_id AS monitoring_period,
            dma.reported_value_nmbr AS reported_value_nmbr,
            dma.reported_unit_code AS reported_unit_code,
            dma.nodi_code AS nodi_code,
            fr.permit_number AS permit_number,
            fr.facility_name AS facility_name,
            dpr.feature_number AS feature_number,
            pr.parameter_code AS parameter_code,
            pr.parameter_desc AS parameter_desc,
            mpr.period_end_date AS period_end_date
        FROM fy2025_in_scope_measurement fy
        JOIN dmr_measurement_assertion dma
          ON fy.measurement_id = dma.measurement_id
        JOIN facility_registry fr ON dma.facility_id = fr.facility_id
        JOIN discharge_point_registry dpr
          ON dma.discharge_point_id = dpr.discharge_point_id
        JOIN parameter_registry pr ON dma.parameter_id = pr.parameter_id
        JOIN monitoring_period_registry mpr
          ON dma.monitoring_period_id = mpr.monitoring_period_id
        ORDER BY fr.permit_number, mpr.period_end_date, pr.parameter_code
        """
    )

    limits = lookup_map(
        tv,
        """
        SELECT
            limit_value_id AS applicable_limit,
            limit_value_nmbr,
            limit_unit_code,
            limit_value_qualifier,
            limit_type_code,
            optional_monitoring_flag,
            statistical_base_code
        FROM permit_limit_assertion
        """,
        "applicable_limit",
    )

    rows: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []

    for meas in measurements:
        mid = meas["measurement"]
        limit_disp = limit_by_measurement.get(mid)
        numeric_disp = numeric_by_measurement.get(mid)
        exceed_disp = exceed_by_measurement.get(mid)

        base = {
            "measurement": mid,
            "facility": meas["facility"],
            "permit_number": meas["permit_number"],
            "facility_name": meas["facility_name"],
            "discharge_point": meas["discharge_point"],
            "feature_number": meas["feature_number"],
            "parameter": meas["parameter"],
            "parameter_code": meas["parameter_code"],
            "parameter_desc": meas["parameter_desc"],
            "monitoring_period": meas["monitoring_period"],
            "period_end_date": meas["period_end_date"],
        }

        if limit_disp is None or limit_disp["disposition"] == "UNRESOLVED":
            rationale = (limit_disp or {}).get("rationale", "No limit applicability adjudication.")
            unresolved.append(
                {
                    **base,
                    "unresolved_state": classify_limit_unresolved(rationale),
                    "rationale": rationale,
                    "grounding": grounding_refs((limit_disp or {}).get("grounding", [])),
                }
            )
            continue

        applicable_limit = limit_disp["values"]["applicable_limit"]
        limit_info = limits.get(applicable_limit, {})
        row: dict[str, Any] = {
            **base,
            "applicable_limit": applicable_limit,
            "limit_value_nmbr": limit_info.get("limit_value_nmbr"),
            "limit_unit_code": limit_info.get("limit_unit_code"),
            "limit_value_qualifier": limit_info.get("limit_value_qualifier"),
            "limit_type_code": limit_info.get("limit_type_code"),
            "reported_value_nmbr": meas["reported_value_nmbr"]
            if meas["reported_value_nmbr"] != SENTINEL_VALUE
            else None,
            "reported_unit_code": meas["reported_unit_code"],
            "nodi_code": meas["nodi_code"],
            "grounding": grounding_refs(limit_disp.get("grounding", [])),
        }

        if numeric_disp and numeric_disp["disposition"] == "UNRESOLVED":
            rationale = numeric_disp["rationale"]
            unresolved.append(
                {
                    **base,
                    "applicable_limit": applicable_limit,
                    "unresolved_state": classify_numeric_unresolved(rationale),
                    "rationale": rationale,
                    "grounding": grounding_refs(numeric_disp.get("grounding", [])),
                }
            )
            continue

        regime = classify_numeric_regime(
            (numeric_disp or {}).get("rationale", ""),
            (numeric_disp or {}).get("disposition", "ACCEPT"),
        )
        row["comparison_regime"] = regime

        if exceed_disp:
            outcome = classify_exceedance_outcome(
                exceed_disp["disposition"], exceed_disp.get("rationale", "")
            )
            if exceed_disp["disposition"] == "UNRESOLVED":
                row["exceedance_outcome"] = None
                row["exceedance_unresolved_state"] = (
                    "limit_established_but_measurement_not_numeric_comparable"
                    if "limit_value_nmbr" in exceed_disp["rationale"].lower()
                    else classify_numeric_unresolved(exceed_disp["rationale"])
                )
                row["exceedance_rationale"] = exceed_disp["rationale"]
            elif outcome:
                row["exceedance_outcome"] = outcome
                row["exceedance_rationale"] = exceed_disp.get("rationale", "")

        rows.append(row)

    return {
        "purpose": "applicable_discharge_limits",
        "temporal_scope": {
            "label": "Federal FY2025",
            "start": FY2025_START,
            "end": FY2025_END,
        },
        "rows": rows,
        "unresolved": unresolved,
        "completeness": {
            "universe_count": len(measurements),
            "rows_count": len(rows),
            "unresolved_count": len(unresolved),
            "partition_ok": len(rows) + len(unresolved) == len(measurements),
        },
    }


def derive_purpose_b(
    tv: TaskView, dispositions: list[dict[str, Any]]
) -> dict[str, Any]:
    applicability = {
        d["values"]["monitoring_requirement"]: d
        for d in dispositions
        if d["relation"] == "monitoring_requirement_applicability_judgment"
    }

    requirements = tv.query_semantic(
        """
        SELECT
            fy.monitoring_requirement_id AS monitoring_requirement,
            lsr.facility_id AS facility,
            lsr.discharge_point_id AS discharge_point,
            lsr.limit_set_id,
            lsr.designator,
            lsr.limit_set_name,
            lsr.schedule_id,
            lsr.status_flag,
            lsr.conditional_comment,
            fr.permit_number,
            fr.facility_name,
            dpr.feature_number
        FROM fy2025_monitoring_requirement fy
        JOIN limit_set_record lsr
          ON fy.monitoring_requirement_id = lsr.monitoring_requirement_id
        JOIN facility_registry fr ON lsr.facility_id = fr.facility_id
        JOIN discharge_point_registry dpr
          ON lsr.discharge_point_id = dpr.discharge_point_id
        ORDER BY fr.permit_number, lsr.limit_set_id
        """
    )

    rows: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []

    for req in requirements:
        rid = req["monitoring_requirement"]
        disp = applicability.get(rid)
        base = {
            "monitoring_requirement": rid,
            "facility": req["facility"],
            "permit_number": req["permit_number"],
            "facility_name": req["facility_name"],
            "discharge_point": req["discharge_point"],
            "feature_number": req["feature_number"],
            "limit_set_id": req["limit_set_id"],
            "limit_set_name": req["limit_set_name"],
            "designator": req["designator"],
            "schedule_id": req["schedule_id"],
            "status_flag": req["status_flag"],
            "triggering_conditions": req["conditional_comment"] or "",
            "applicability_period": f"{FY2025_START}/{FY2025_END}",
        }

        if disp is None:
            unresolved.append(
                {
                    **base,
                    "unresolved_state": "schedule_activation_status_unknown",
                    "rationale": "No applicability adjudication for this requirement.",
                    "grounding": [],
                }
            )
            continue

        disposition = disp["disposition"]
        rationale = disp.get("rationale", "")
        grounding = grounding_refs(disp.get("grounding", []))

        if disposition == "UNRESOLVED":
            unresolved.append(
                {
                    **base,
                    "unresolved_state": classify_monitoring_unresolved(rationale),
                    "rationale": rationale,
                    "grounding": grounding,
                }
            )
            continue

        outcome = disposition
        if disposition == "ACCEPT" and ":" in disp.get("original_disposition", ""):
            outcome = disp["original_disposition"].split(":", 1)[-1]
        rows.append(
            {
                **base,
                "applicability_outcome": outcome.lower()
                if outcome in ("ACCEPT", "REJECT")
                else outcome,
                "rationale": rationale,
                "grounding": grounding,
            }
        )

    return {
        "purpose": "monitoring_obligations",
        "temporal_scope": {
            "label": "Federal FY2025",
            "start": FY2025_START,
            "end": FY2025_END,
        },
        "rows": rows,
        "unresolved": unresolved,
        "completeness": {
            "universe_count": len(requirements),
            "rows_count": len(rows),
            "unresolved_count": len(unresolved),
            "partition_ok": len(rows) + len(unresolved) == len(requirements),
        },
    }


def derive_purpose_c(
    tv: TaskView, dispositions: list[dict[str, Any]]
) -> dict[str, Any]:
    semantic = {
        d["values"]["monitoring_expectation"]: d
        for d in dispositions
        if d["relation"] == "missing_evidence_semantic_judgment"
    }

    expectations = tv.query_semantic(
        """
        SELECT
            me.monitoring_expectation_id AS monitoring_expectation,
            me.facility_id AS facility,
            me.discharge_point_id AS discharge_point,
            me.parameter_id AS parameter,
            me.monitoring_period_id AS monitoring_period,
            me.measurement_id AS measurement,
            dma.nodi_code,
            dma.reported_value_nmbr,
            dma.value_qualifier,
            fr.permit_number,
            fr.facility_name,
            dpr.feature_number,
            pr.parameter_code,
            pr.parameter_desc,
            mpr.period_end_date
        FROM monitoring_expectation_without_numeric_result me
        JOIN dmr_measurement_assertion dma
          ON me.measurement_id = dma.measurement_id
        JOIN facility_registry fr ON me.facility_id = fr.facility_id
        JOIN discharge_point_registry dpr
          ON me.discharge_point_id = dpr.discharge_point_id
        JOIN parameter_registry pr ON me.parameter_id = pr.parameter_id
        JOIN monitoring_period_registry mpr
          ON me.monitoring_period_id = mpr.monitoring_period_id
        ORDER BY fr.permit_number, mpr.period_end_date, pr.parameter_code
        """
    )

    rows: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []

    for exp in expectations:
        eid = exp["monitoring_expectation"]
        disp = semantic.get(eid)
        base = {
            "monitoring_expectation": eid,
            "measurement": exp["measurement"],
            "facility": exp["facility"],
            "permit_number": exp["permit_number"],
            "facility_name": exp["facility_name"],
            "discharge_point": exp["discharge_point"],
            "feature_number": exp["feature_number"],
            "parameter": exp["parameter"],
            "parameter_code": exp["parameter_code"],
            "parameter_desc": exp["parameter_desc"],
            "monitoring_period": exp["monitoring_period"],
            "period_end_date": exp["period_end_date"],
            "nodi_code": exp["nodi_code"],
            "value_qualifier": exp["value_qualifier"],
        }

        if disp is None:
            unresolved.append(
                {
                    **base,
                    "unresolved_state": "monitoring_expectation_identity_unclear",
                    "rationale": "No missing-evidence semantic adjudication.",
                    "grounding": [],
                }
            )
            continue

        disposition = disp["disposition"]
        rationale = disp.get("rationale", "")
        grounding = grounding_refs(disp.get("grounding", []))

        if disposition == "UNRESOLVED":
            unresolved.append(
                {
                    **base,
                    "unresolved_state": classify_missing_evidence_unresolved(rationale),
                    "rationale": rationale,
                    "grounding": grounding,
                }
            )
            continue

        state = classify_missing_evidence_accept(disposition, rationale)
        if state:
            rows.append(
                {
                    **base,
                    "missing_evidence_state": state,
                    "rationale": rationale,
                    "grounding": grounding,
                }
            )
        else:
            unresolved.append(
                {
                    **base,
                    "unresolved_state": "nodi_or_no_data_code_uninterpretable",
                    "rationale": rationale,
                    "grounding": grounding,
                }
            )

    return {
        "purpose": "missing_evidence_semantics",
        "temporal_scope": {
            "label": "Federal FY2025",
            "start": FY2025_START,
            "end": FY2025_END,
        },
        "rows": rows,
        "unresolved": unresolved,
        "completeness": {
            "universe_count": len(expectations),
            "rows_count": len(rows),
            "unresolved_count": len(unresolved),
            "partition_ok": len(rows) + len(unresolved) == len(expectations),
        },
    }


def write_output(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def main() -> None:
    world_path = find_world_db()
    dispositions = load_dispositions()

    with TaskView(world_path, view_id="diligence-world") as tv:
        purpose_a = derive_purpose_a(tv, dispositions)
        purpose_b = derive_purpose_b(tv, dispositions)
        purpose_c = derive_purpose_c(tv, dispositions)

    write_output(ROOT / "purpose_ir" / "a" / "output.json", purpose_a)
    write_output(ROOT / "purpose_ir" / "b" / "output.json", purpose_b)
    write_output(ROOT / "purpose_ir" / "c" / "output.json", purpose_c)

    print(f"Wrote purpose_ir/a/output.json ({purpose_a['completeness']['rows_count']} rows, "
          f"{purpose_a['completeness']['unresolved_count']} unresolved)")
    print(f"Wrote purpose_ir/b/output.json ({purpose_b['completeness']['rows_count']} rows, "
          f"{purpose_b['completeness']['unresolved_count']} unresolved)")
    print(f"Wrote purpose_ir/c/output.json ({purpose_c['completeness']['rows_count']} rows, "
          f"{purpose_c['completeness']['unresolved_count']} unresolved)")


if __name__ == "__main__":
    main()
