#!/usr/bin/env python3
"""P7 derivation compiler: project world.sqlite and admitted dispositions to purpose_ir."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from taskview import TaskView

ROOT = Path(__file__).resolve().parents[2]
DISPOSITIONS_PATH = ROOT / "05_dispositions.json"
VIEW_ID = "diligence-world"
FY2025_CONTEXT = "FY2025 overlap 2024-10-01 to 2025-09-30"


def resolve_world_db() -> Path:
    for relative in ("06_world/world.sqlite", "world/world.sqlite"):
        candidate = ROOT / relative
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "world.sqlite not found at 06_world/world.sqlite or world/world.sqlite"
    )


def load_dispositions() -> list[dict[str, Any]]:
    with DISPOSITIONS_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def index_dispositions(
    dispositions: list[dict[str, Any]],
) -> dict[str, dict[Any, dict[str, Any]]]:
    by_relation: dict[str, dict[Any, dict[str, Any]]] = {}
    for entry in dispositions:
        relation = entry["relation"]
        values = entry.get("values", {})
        if relation == "limit_applicability_resolution":
            key = values["measurement"]
        elif relation == "limit_kind_resolution":
            key = (values["measurement"], values["limit_value"])
        elif relation == "monitoring_obligation_resolution":
            key = (values["requirement"], values["applicability_context"])
        elif relation == "missing_evidence_resolution":
            key = values["case"]
        else:
            continue
        by_relation.setdefault(relation, {})[key] = entry
    return by_relation


def extract_limit_ref(disposition: dict[str, Any]) -> str | None:
    for ground in disposition.get("grounding", []):
        location = str(ground.get("location", ""))
        if location.startswith("compiled_limit_value/"):
            return location.split("/", 1)[1]
    match = re.search(r"limit_val:[^\s,;]+", disposition.get("rationale", ""))
    return match.group(0) if match else None


def grounding_refs(disposition: dict[str, Any] | None, *extra: str) -> list[str]:
    refs: list[str] = []
    if disposition:
        for ground in disposition.get("grounding", []):
            source = ground.get("source_path", "")
            location = ground.get("location", "")
            refs.append(f"{source}:{location}" if source else location)
        rationale = disposition.get("rationale", "").strip()
        if rationale:
            refs.append(f"rationale:{rationale}")
    refs.extend(extra)
    return refs


def limit_category_from_disposition(disposition: dict[str, Any]) -> str:
    disp = disposition.get("final_admitted_disposition", disposition.get("disposition"))
    rationale = disposition.get("rationale", "").lower()
    if disp == "ACCEPT":
        return "enforceable_numeric"
    if disp == "UNRESOLVED":
        return "unresolved"
    if "optional_monitoring_flag=y" in rationale or "report-only" in rationale:
        return "report_only"
    return "no_numeric_comparison"


def applicability_status(
    applicability: dict[str, Any] | None,
    limit_kind: dict[str, Any] | None,
) -> str:
    if applicability is None:
        return "unresolved"
    applic_disp = applicability.get(
        "final_admitted_disposition", applicability.get("disposition")
    )
    if applic_disp == "UNRESOLVED":
        return "unresolved"
    if applic_disp != "ACCEPT":
        return "unresolved"
    if limit_kind is None:
        return "unresolved"
    category = limit_category_from_disposition(limit_kind)
    if category == "enforceable_numeric":
        return "single_enforceable_limit_established"
    if category in {"report_only", "no_numeric_comparison"}:
        return "no_enforceable_numeric_limit_applies"
    return "unresolved"


def compare_exceedance(
    reported_value: float,
    limit_value: float,
    qualifier: str,
) -> str:
    if qualifier in {">=", ""}:
        return "exceeds" if reported_value > limit_value else "does_not_exceed"
    if qualifier == ">":
        return "exceeds" if reported_value > limit_value else "does_not_exceed"
    if qualifier == "<=":
        return "exceeds" if reported_value < limit_value else "does_not_exceed"
    if qualifier == "<":
        return "exceeds" if reported_value < limit_value else "does_not_exceed"
    return "unresolved"


def exceedance_determination(
    measurement: dict[str, Any],
    limit_row: dict[str, Any] | None,
    limit_kind: dict[str, Any] | None,
) -> str:
    if limit_kind is None or limit_row is None:
        return "unresolved"
    category = limit_category_from_disposition(limit_kind)
    if category == "unresolved":
        return "unresolved"
    if category != "enforceable_numeric":
        return "comparison_not_applicable"
    threshold = float(limit_row["limit_value_number"])
    if threshold == 0.0 and not str(limit_row.get("limit_value_qualifier", "")).strip():
        return "unresolved"
    return compare_exceedance(
        float(measurement["reported_value_number"]),
        threshold,
        str(limit_row.get("limit_value_qualifier", "")).strip(),
    )


def condition_dependencies(requirement: dict[str, Any]) -> str:
    anchor = str(requirement.get("condition_anchor_text", "")).strip()
    optional_flag = str(requirement.get("optional_monitoring_flag", "")).strip().upper()
    if not anchor and optional_flag != "Y":
        return "unconditional schedule-based requirement"
    if "when discharg" in anchor.lower():
        return "discharge-occurrence-dependent"
    if anchor:
        return "other permit-condition-gated requirement"
    if optional_flag == "Y":
        return "other permit-condition-gated requirement"
    return "unconditional schedule-based requirement"


def verdict_from_disposition(disposition: dict[str, Any]) -> str:
    disp = disposition.get("final_admitted_disposition", disposition.get("disposition"))
    if disp == "UNRESOLVED":
        return "unresolved"
    rationale = disposition.get("rationale", "").lower()
    if "not required" in rationale:
        return "not_required"
    if disp == "ACCEPT":
        return "required"
    return "unresolved"


def established_state_from_disposition(disposition: dict[str, Any]) -> str:
    disp = disposition.get("final_admitted_disposition", disposition.get("disposition"))
    if disp == "UNRESOLVED":
        return "unresolved"
    rationale = disposition.get("rationale", "").lower()
    if "no-discharge" in rationale or "no discharge" in rationale:
        return "documented_no_discharge"
    if "not required" in rationale or "conditional monitoring not required" in rationale:
        return "conditional_monitoring_not_required"
    if "nodi" in rationale or "documented no-data" in rationale:
        return "other_documented_no_data"
    if "lacks adequate evidence" in rationale or "insufficient" in rationale:
        return "required_monitoring_lacks_adequate_evidence"
    if disp == "ACCEPT":
        return "other_documented_no_data"
    return "unresolved"


def fetch_measurement_context(tv: TaskView) -> dict[str, dict[str, Any]]:
    rows = tv.query_semantic(
        """
        SELECT
            d.measurement_id,
            d.facility_id,
            d.feature_id,
            d.parameter_id,
            d.period_id,
            d.reported_value_number,
            d.reported_unit_code,
            d.value_qualifier,
            d.nodi_code,
            d.dmr_value_id,
            d.linked_limit_value_id,
            wf.permit_number AS facility_identifier,
            pdf.feature_number,
            mp.parameter_code,
            mp.parameter_description,
            per.period_end_date
        FROM compiled_dmr_measurement d
        JOIN workspace_facility wf ON d.facility_id = wf.facility_id
        JOIN permit_discharge_feature pdf ON d.feature_id = pdf.feature_id
        JOIN monitored_parameter mp ON d.parameter_id = mp.parameter_id
        JOIN monitoring_period per ON d.period_id = per.period_id
        """
    )
    return {row["measurement_id"]: row for row in rows}


def fetch_limit_values(tv: TaskView) -> dict[str, dict[str, Any]]:
    rows = tv.query_semantic("SELECT * FROM compiled_limit_value")
    return {row["limit_value_ref_id"]: row for row in rows}


def fetch_requirements(tv: TaskView) -> dict[str, dict[str, Any]]:
    rows = tv.query_semantic(
        """
        SELECT
            mrs.requirement_id,
            mrs.facility_id,
            mrs.feature_id,
            mrs.parameter_id,
            mrs.limit_set_designator,
            mrs.frequency_code,
            mrs.limit_begin_date,
            mrs.limit_end_date,
            mrs.optional_monitoring_flag,
            mrs.condition_anchor_text,
            wf.permit_number AS facility_identifier,
            pdf.feature_number,
            mp.parameter_code,
            mp.parameter_description
        FROM monitoring_requirement_schedule mrs
        JOIN workspace_facility wf ON mrs.facility_id = wf.facility_id
        JOIN permit_discharge_feature pdf ON mrs.feature_id = pdf.feature_id
        JOIN monitored_parameter mp ON mrs.parameter_id = mp.parameter_id
        """
    )
    return {row["requirement_id"]: row for row in rows}


def derive_purpose_a(
    tv: TaskView,
    indexed: dict[str, dict[Any, dict[str, Any]]],
) -> dict[str, Any]:
    measurements = fetch_measurement_context(tv)
    limits = fetch_limit_values(tv)
    applicability = indexed.get("limit_applicability_resolution", {})
    limit_kinds = indexed.get("limit_kind_resolution", {})

    scope = tv.query_semantic(
        """
        SELECT d.measurement_id
        FROM dmr_in_fy2025_scope d
        JOIN measurement_has_ordinary_numeric_result o
          ON d.measurement_id = o.measurement_id
        WHERE o.has_ordinary_numeric = 1
        ORDER BY d.measurement_id
        """
    )

    rows: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []

    for item in scope:
        measurement_id = item["measurement_id"]
        measurement = measurements[measurement_id]
        applic = applicability.get(measurement_id)
        applic_disp = None
        if applic:
            applic_disp = applic.get(
                "final_admitted_disposition", applic.get("disposition")
            )

        if applic is None or applic_disp == "UNRESOLVED":
            unresolved.append(
                {
                    "facility": measurement["facility_identifier"],
                    "feature": measurement["feature_number"],
                    "parameter": measurement["parameter_code"],
                    "monitoring_period": measurement["period_end_date"],
                    "measurement": measurement_id,
                    "reason": (
                        applic.get("rationale", "limit applicability unresolved")
                        if applic
                        else "no admitted limit_applicability_resolution"
                    ),
                    "grounding": grounding_refs(applic),
                }
            )
            continue

        selected_limit = extract_limit_ref(applic)
        limit_kind = (
            limit_kinds.get((measurement_id, selected_limit))
            if selected_limit
            else None
        )
        limit_row = limits.get(selected_limit) if selected_limit else None
        status = applicability_status(applic, limit_kind)
        category = (
            limit_category_from_disposition(limit_kind)
            if limit_kind
            else "unresolved"
        )
        exceedance = exceedance_determination(measurement, limit_row, limit_kind)

        rows.append(
            {
                "facility": measurement["facility_identifier"],
                "feature": measurement["feature_number"],
                "parameter": measurement["parameter_code"],
                "monitoring_period": measurement["period_end_date"],
                "measurement": measurement_id,
                "measurement_summary": (
                    f"dmr_value_id={measurement['dmr_value_id']}; "
                    f"value={measurement['reported_value_number']}; "
                    f"unit={measurement['reported_unit_code']}; "
                    f"qualifier={measurement['value_qualifier'] or '='}"
                ),
                "applicable_limit": selected_limit,
                "limit_applicability_status": status,
                "limit_category": category,
                "exceedance": exceedance,
                "grounding": grounding_refs(applic, *(grounding_refs(limit_kind))),
            }
        )

    return {
        "purpose": "applicable_discharge_limits",
        "rows": rows,
        "unresolved": unresolved,
    }


def derive_purpose_b(
    tv: TaskView,
    indexed: dict[str, dict[Any, dict[str, Any]]],
) -> dict[str, Any]:
    requirements = fetch_requirements(tv)
    obligations = indexed.get("monitoring_obligation_resolution", {})
    scope = tv.query_semantic(
        "SELECT requirement_id FROM monitoring_requirement_in_fy2025 ORDER BY requirement_id"
    )

    rows: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []

    for item in scope:
        requirement_id = item["requirement_id"]
        requirement = requirements[requirement_id]
        disposition = obligations.get((requirement_id, FY2025_CONTEXT))
        verdict = (
            verdict_from_disposition(disposition) if disposition else "unresolved"
        )
        requirement_label = (
            f"req={requirement_id}; param={requirement['parameter_code']}; "
            f"feature={requirement['feature_number']}; "
            f"frequency={requirement['frequency_code']}; "
            f"limit_set={requirement['limit_set_designator']}"
        )
        payload = {
            "facility": requirement["facility_identifier"],
            "requirement": requirement_label,
            "requirement_id": requirement_id,
            "applicability_context": FY2025_CONTEXT,
            "applicability_verdict": verdict,
            "condition_dependencies": condition_dependencies(requirement),
            "grounding": grounding_refs(disposition),
        }
        if verdict == "unresolved":
            unresolved.append(
                {
                    **payload,
                    "reason": (
                        disposition.get("rationale", "applicability unresolved")
                        if disposition
                        else "no admitted monitoring_obligation_resolution"
                    ),
                }
            )
        else:
            rows.append(payload)

    return {
        "purpose": "monitoring_obligations",
        "rows": rows,
        "unresolved": unresolved,
    }


def derive_purpose_c(
    tv: TaskView,
    indexed: dict[str, dict[Any, dict[str, Any]]],
) -> dict[str, Any]:
    measurements = fetch_measurement_context(tv)
    requirements = fetch_requirements(tv)
    resolutions = indexed.get("missing_evidence_resolution", {})
    scope = tv.query_semantic(
        "SELECT * FROM missing_evidence_case_universe ORDER BY case_id"
    )

    rows: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []

    for case in scope:
        case_id = case["case_id"]
        measurement_id = case["measurement_id"]
        measurement = measurements.get(measurement_id, {})
        requirement = requirements.get(case["requirement_id"], {})
        disposition = resolutions.get(case_id)
        observed_form = disposition["values"]["observed_form"] if disposition else ""
        if not observed_form:
            nodi = str(measurement.get("nodi_code", "")).strip()
            qualifier = str(measurement.get("value_qualifier", "")).strip()
            if nodi:
                observed_form = f"nodi:{nodi}"
            elif qualifier and not measurement.get("has_ordinary_numeric"):
                observed_form = f"qualifier:{qualifier}"
            elif measurement_id:
                observed_form = "non_ordinary_submission"
            else:
                observed_form = "absent_submission"

        established = (
            established_state_from_disposition(disposition)
            if disposition
            else "unresolved"
        )
        facility = measurement.get("facility_identifier") or requirement.get(
            "facility_identifier", case["facility_id"]
        )
        feature = measurement.get("feature_number") or requirement.get(
            "feature_number", case["feature_id"]
        )
        parameter = measurement.get("parameter_code") or requirement.get(
            "parameter_code", case["parameter_id"]
        )
        period = measurement.get("period_end_date") or case["period_id"]

        payload = {
            "facility": facility,
            "feature": feature,
            "parameter": parameter,
            "monitoring_period": period,
            "case": case_id,
            "observed_result_form": observed_form,
            "established_state": established,
            "grounding": grounding_refs(disposition),
        }
        if established == "unresolved":
            unresolved.append(
                {
                    **payload,
                    "reason": (
                        disposition.get("rationale", "missing-evidence semantics unresolved")
                        if disposition
                        else "no admitted missing_evidence_resolution"
                    ),
                }
            )
        else:
            rows.append(payload)

    return {
        "purpose": "missing_evidence_semantics",
        "rows": rows,
        "unresolved": unresolved,
    }


def write_output(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def main() -> int:
    world_db = resolve_world_db()
    if not DISPOSITIONS_PATH.exists():
        print(f"Missing required dispositions file: {DISPOSITIONS_PATH}", file=sys.stderr)
        return 1

    dispositions = load_dispositions()
    indexed = index_dispositions(dispositions)

    with TaskView(world_db, view_id=VIEW_ID) as tv:
        purpose_a = derive_purpose_a(tv, indexed)
        purpose_b = derive_purpose_b(tv, indexed)
        purpose_c = derive_purpose_c(tv, indexed)

    write_output(ROOT / "purpose_ir/a/output.json", purpose_a)
    write_output(ROOT / "purpose_ir/b/output.json", purpose_b)
    write_output(ROOT / "purpose_ir/c/output.json", purpose_c)

    print(
        "Wrote purpose_ir outputs: "
        f"A rows={len(purpose_a['rows'])} unresolved={len(purpose_a['unresolved'])}; "
        f"B rows={len(purpose_b['rows'])} unresolved={len(purpose_b['unresolved'])}; "
        f"C rows={len(purpose_c['rows'])} unresolved={len(purpose_c['unresolved'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
