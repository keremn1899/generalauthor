"""Build purpose-sufficient semantic spine over NPDES structured sources."""

from __future__ import annotations

from source import Source, interval_contains, parse_date
from world_api import Purpose, World

FY_BEGIN = "2024-10-01"
FY_END = "2025-09-30"


def _text(value: object) -> str:
    return "" if value is None else str(value).strip()


def _has_text(value: object) -> bool:
    return bool(_text(value))


def _is_pass_fail_unit_descriptor(unit_desc: str) -> bool:
    normalized = _text(unit_desc).lower().replace(" ", "")
    return "pass=0" in normalized and "fail=1" in normalized


def _is_pass_fail_comment(comment: str) -> bool:
    upper = _text(comment).upper()
    return "PASS = 0" in upper and "FAIL = 1" in upper


def _is_wet_pass_fail_reporting(
    *,
    limit_unit_desc: str = "",
    dmr_unit_desc: str = "",
    dmr_comment_text: str = "",
) -> bool:
    return (
        _is_pass_fail_unit_descriptor(limit_unit_desc)
        or _is_pass_fail_unit_descriptor(dmr_unit_desc)
        or _is_pass_fail_comment(dmr_comment_text)
    )


def construct(source: Source, world: World, purpose: Purpose) -> None:
    dmr_rows = source.rows("dmr_measurements.csv")
    limit_rows = source.rows("permit_limits.csv")
    documents = source.document_inventory()

    permit_ids: dict[str, str] = {}
    feature_ids: dict[str, str] = {}
    parameter_ids: dict[str, str] = {}
    limit_ids: dict[str, str] = {}
    limit_value_ids: dict[str, str] = {}
    measurement_ids: dict[str, str] = {}
    limit_set_ids: dict[str, str] = {}
    schedule_ids: dict[str, str] = {}
    permit_limit_ids: dict[tuple[str, str], str] = {}
    document_ids: dict[str, str] = {}

    def permit_ref(number: str) -> str:
        key = _text(number)
        if key not in permit_ids:
            permit_ids[key] = world.referent("permit", {"permit_number": key})
        return permit_ids[key]

    def feature_ref(feature_id: str, permit_number: str, feature_number: str) -> str:
        key = _text(feature_id)
        if key not in feature_ids:
            feature_ids[key] = world.referent(
                "feature",
                {
                    "feature_id": key,
                    "permit_number": _text(permit_number),
                    "feature_number": _text(feature_number),
                },
            )
        return feature_ids[key]

    def parameter_ref(code: str) -> str:
        key = _text(code)
        if key not in parameter_ids:
            parameter_ids[key] = world.referent("parameter", {"parameter_code": key})
        return parameter_ids[key]

    def limit_ref(limit_id: str) -> str:
        key = _text(limit_id)
        if key not in limit_ids:
            limit_ids[key] = world.referent("limit", {"limit_id": key})
        return limit_ids[key]

    def limit_value_ref(limit_value_id: str) -> str:
        key = _text(limit_value_id)
        if key not in limit_value_ids:
            limit_value_ids[key] = world.referent("limit_value", {"limit_value_id": key})
        return limit_value_ids[key]

    def measurement_ref(form_value_id: str) -> str:
        key = _text(form_value_id)
        if key not in measurement_ids:
            measurement_ids[key] = world.referent("measurement", {"dmr_form_value_id": key})
        return measurement_ids[key]

    def limit_set_ref(limit_set_id: str) -> str:
        key = _text(limit_set_id)
        if key not in limit_set_ids:
            limit_set_ids[key] = world.referent("limit_set", {"limit_set_id": key})
        return limit_set_ids[key]

    def schedule_ref(schedule_id: str) -> str:
        key = _text(schedule_id)
        if key not in schedule_ids:
            schedule_ids[key] = world.referent("limit_set_schedule", {"limit_set_schedule_id": key})
        return schedule_ids[key]

    def permit_limit_ref(limit_value_id: str, schedule_id: str) -> str:
        key = (_text(limit_value_id), _text(schedule_id))
        if key not in permit_limit_ids:
            permit_limit_ids[key] = world.referent(
                "permit_limit_row",
                {"limit_value_id": key[0], "limit_set_schedule_id": key[1]},
            )
        return permit_limit_ids[key]

    def document_ref(sha256: str, path: str) -> str:
        key = _text(sha256)
        if key not in document_ids:
            document_ids[key] = world.referent("document", {"sha256": key, "path": _text(path)})
        return document_ids[key]

    world.relation(
        "dmr_measurement",
        [
            ("measurement", "REFERENT"),
            ("permit", "REFERENT"),
            ("feature", "REFERENT"),
            ("parameter", "REFERENT"),
            ("limit", "REFERENT"),
            ("limit_value", "REFERENT"),
            ("limit_set", "REFERENT"),
            ("limit_set_schedule", "REFERENT"),
            ("monitoring_period_end", "TEXT"),
            ("limit_begin_date", "TEXT"),
            ("limit_end_date", "TEXT"),
            ("dmr_value_nmbr", "TEXT"),
            ("dmr_value_standard_units", "TEXT"),
            ("dmr_value_qualifier_code", "TEXT"),
            ("limit_value_nmbr", "TEXT"),
            ("limit_value_standard_units", "TEXT"),
            ("limit_value_qualifier_code", "TEXT"),
            ("limit_type_code", "TEXT"),
            ("optional_monitoring_flag", "TEXT"),
            ("nodi_code", "TEXT"),
            ("limit_set_designator", "TEXT"),
            ("limit_value_type_code", "TEXT"),
            ("value_type_code", "TEXT"),
            ("statistical_base_type_code", "TEXT"),
            ("dmr_sample_type_code", "TEXT"),
            ("dmr_freq_of_analysis_code", "TEXT"),
            ("limit_freq_of_analysis_code", "TEXT"),
            ("limit_sample_type_code", "TEXT"),
            ("monitoring_location_code", "TEXT"),
            ("has_reported_value", "BOOLEAN"),
            ("has_limit_value_nmbr", "BOOLEAN"),
            ("period_in_limit_interval", "BOOLEAN"),
        ],
        description="Reported DMR measurement rows with structural source fields.",
    )

    world.relation(
        "permit_limit",
        [
            ("permit_limit_row", "REFERENT"),
            ("permit", "REFERENT"),
            ("feature", "REFERENT"),
            ("parameter", "REFERENT"),
            ("limit", "REFERENT"),
            ("limit_value", "REFERENT"),
            ("limit_set", "REFERENT"),
            ("limit_set_schedule", "REFERENT"),
            ("limit_begin_date", "TEXT"),
            ("limit_end_date", "TEXT"),
            ("limit_value_nmbr", "TEXT"),
            ("limit_value_standard_units", "TEXT"),
            ("limit_value_qualifier_code", "TEXT"),
            ("limit_type_code", "TEXT"),
            ("optional_monitoring_flag", "TEXT"),
            ("limit_set_designator", "TEXT"),
            ("limit_set_name", "TEXT"),
            ("limit_freq_of_analysis_code", "TEXT"),
            ("limit_sample_type_code", "TEXT"),
            ("statistical_base_type_code", "TEXT"),
            ("dmr_comment_text", "TEXT"),
            ("monitoring_location_code", "TEXT"),
            ("has_limit_value_nmbr", "BOOLEAN"),
            ("limit_overlaps_fy2025", "BOOLEAN"),
        ],
        description="Permit limit schedule rows with structural source fields.",
    )

    world.relation(
        "permit_document",
        [
            ("permit", "REFERENT"),
            ("document", "REFERENT"),
            ("document_kind", "TEXT"),
            ("filename", "TEXT"),
            ("bytes", "INTEGER"),
        ],
        description="Permit package document inventory entries.",
    )

    limit_index: dict[tuple[str, str], dict[str, str]] = {}
    for row in limit_rows:
        key = (_text(row["LIMIT_VALUE_ID"]), _text(row["LIMIT_SET_SCHEDULE_ID"]))
        limit_index[key] = row

    dmr_measurement_rows: list[dict[str, object]] = []
    for row in dmr_rows:
        period_end = parse_date(row["MONITORING_PERIOD_END_DATE"]) or ""
        limit_begin = parse_date(row["LIMIT_BEGIN_DATE"]) or ""
        limit_end = parse_date(row["LIMIT_END_DATE"]) or ""
        dmr_measurement_rows.append(
            {
                "measurement": measurement_ref(row["DMR_FORM_VALUE_ID"]),
                "permit": permit_ref(row["EXTERNAL_PERMIT_NMBR"]),
                "feature": feature_ref(
                    row["PERM_FEATURE_ID"],
                    row["EXTERNAL_PERMIT_NMBR"],
                    row["PERM_FEATURE_NMBR"],
                ),
                "parameter": parameter_ref(row["PARAMETER_CODE"]),
                "limit": limit_ref(row["LIMIT_ID"]),
                "limit_value": limit_value_ref(row["LIMIT_VALUE_ID"]),
                "limit_set": limit_set_ref(row["LIMIT_SET_ID"]),
                "limit_set_schedule": schedule_ref(row["LIMIT_SET_SCHEDULE_ID"]),
                "monitoring_period_end": period_end,
                "limit_begin_date": limit_begin,
                "limit_end_date": limit_end,
                "dmr_value_nmbr": _text(row["DMR_VALUE_NMBR"]),
                "dmr_value_standard_units": _text(row["DMR_VALUE_STANDARD_UNITS"]),
                "dmr_unit_desc": _text(row.get("DMR_UNIT_DESC")),
                "dmr_value_qualifier_code": _text(row["DMR_VALUE_QUALIFIER_CODE"]),
                "limit_value_nmbr": _text(row["LIMIT_VALUE_NMBR"]),
                "limit_value_standard_units": _text(row["LIMIT_VALUE_STANDARD_UNITS"]),
                "limit_value_qualifier_code": _text(row["LIMIT_VALUE_QUALIFIER_CODE"]),
                "limit_type_code": _text(row["LIMIT_TYPE_CODE"]),
                "optional_monitoring_flag": _text(row["OPTIONAL_MONITORING_FLAG"]),
                "nodi_code": _text(row["NODI_CODE"]),
                "limit_set_designator": _text(row["LIMIT_SET_DESIGNATOR"]),
                "limit_value_type_code": _text(row["LIMIT_VALUE_TYPE_CODE"]),
                "value_type_code": _text(row["VALUE_TYPE_CODE"]),
                "statistical_base_type_code": _text(row["STATISTICAL_BASE_TYPE_CODE"]),
                "dmr_sample_type_code": _text(row["DMR_SAMPLE_TYPE_CODE"]),
                "dmr_freq_of_analysis_code": _text(row["DMR_FREQ_OF_ANALYSIS_CODE"]),
                "limit_freq_of_analysis_code": _text(row["LIMIT_FREQ_OF_ANALYSIS_CODE"]),
                "limit_sample_type_code": _text(row["LIMIT_SAMPLE_TYPE_CODE"]),
                "monitoring_location_code": _text(row["MONITORING_LOCATION_CODE"]),
                "has_reported_value": _has_text(row["DMR_VALUE_NMBR"]),
                "has_limit_value_nmbr": _has_text(row["LIMIT_VALUE_NMBR"]),
                "period_in_limit_interval": interval_contains(period_end, limit_begin, limit_end),
            }
        )
    world.map("dmr_measurement", dmr_measurement_rows, grounding={"source": "dmr_measurements.csv"})

    permit_limit_map_rows: list[dict[str, object]] = []
    for row in limit_rows:
        permit_limit_map_rows.append(
            {
                "permit_limit_row": permit_limit_ref(row["LIMIT_VALUE_ID"], row["LIMIT_SET_SCHEDULE_ID"]),
                "permit": permit_ref(row["EXTERNAL_PERMIT_NMBR"]),
                "feature": feature_ref(
                    row["PERM_FEATURE_ID"],
                    row["EXTERNAL_PERMIT_NMBR"],
                    row["PERM_FEATURE_NMBR"],
                ),
                "parameter": parameter_ref(row["PARAMETER_CODE"]),
                "limit": limit_ref(row["LIMIT_ID"]),
                "limit_value": limit_value_ref(row["LIMIT_VALUE_ID"]),
                "limit_set": limit_set_ref(row["LIMIT_SET_ID"]),
                "limit_set_schedule": schedule_ref(row["LIMIT_SET_SCHEDULE_ID"]),
                "limit_begin_date": parse_date(row["LIMIT_BEGIN_DATE"]) or "",
                "limit_end_date": parse_date(row["LIMIT_END_DATE"]) or "",
                "limit_value_nmbr": _text(row["LIMIT_VALUE_NMBR"]),
                "limit_value_standard_units": _text(row["LIMIT_VALUE_STANDARD_UNITS"]),
                "limit_value_qualifier_code": _text(row["LIMIT_VALUE_QUALIFIER_CODE"]),
                "limit_type_code": _text(row["LIMIT_TYPE_CODE"]),
                "optional_monitoring_flag": _text(row["OPTIONAL_MONITORING_FLAG"]),
                "limit_set_designator": _text(row["LIMIT_SET_DESIGNATOR"]),
                "limit_set_name": _text(row["LIMIT_SET_NAME"]),
                "limit_freq_of_analysis_code": _text(row["LIMIT_FREQ_OF_ANALYSIS_CODE"]),
                "limit_sample_type_code": _text(row["LIMIT_SAMPLE_TYPE_CODE"]),
                "statistical_base_type_code": _text(row["STATISTICAL_BASE_TYPE_CODE"]),
                "dmr_comment_text": _text(row["DMR_COMMENT_TEXT"]),
                "monitoring_location_code": _text(row["MONITORING_LOCATION_CODE"]),
                "has_limit_value_nmbr": _has_text(row["LIMIT_VALUE_NMBR"]),
                "limit_overlaps_fy2025": interval_contains(FY_BEGIN, row["LIMIT_BEGIN_DATE"], row["LIMIT_END_DATE"])
                or interval_contains(FY_END, row["LIMIT_BEGIN_DATE"], row["LIMIT_END_DATE"])
                or (
                    parse_date(row["LIMIT_BEGIN_DATE"]) is not None
                    and parse_date(row["LIMIT_END_DATE"]) is not None
                    and parse_date(row["LIMIT_BEGIN_DATE"]) <= FY_BEGIN
                    and parse_date(row["LIMIT_END_DATE"]) >= FY_END
                ),
            }
        )
    world.map("permit_limit", permit_limit_map_rows, grounding={"source": "permit_limits.csv"})

    document_rows: list[dict[str, object]] = []
    for row in documents:
        document_rows.append(
            {
                "permit": permit_ref(row["permit"]),
                "document": document_ref(row["sha256"], row["path"]),
                "document_kind": _text(row["document_kind"]),
                "filename": _text(row["filename"]),
                "bytes": int(_text(row["bytes"]) or "0"),
            }
        )
    world.map("permit_document", document_rows, grounding={"source": "document_inventory.json"})

    fy_measurement_rows = [
        row
        for row in dmr_measurement_rows
        if interval_contains(row["monitoring_period_end"], FY_BEGIN, FY_END)
    ]
    world.derive(
        "fy2025_measurement",
        fy_measurement_rows,
        roles=[("measurement", "REFERENT"), ("monitoring_period_end", "TEXT")],
        inputs=["dmr_measurement"],
        grounding={"fy_begin": FY_BEGIN, "fy_end": FY_END},
        mode="PURPOSE",
    )

    measurement_limit_rows: list[dict[str, object]] = []
    for row in dmr_measurement_rows:
        if not interval_contains(row["monitoring_period_end"], FY_BEGIN, FY_END):
            continue
        source_row = limit_index.get(
            (
                world.referents[row["limit_value"]]["key"]["limit_value_id"],
                world.referents[row["limit_set_schedule"]]["key"]["limit_set_schedule_id"],
            )
        )
        if source_row is None:
            continue
        measurement_limit_rows.append(
            {
                "measurement": row["measurement"],
                "permit_limit_row": permit_limit_ref(
                    source_row["LIMIT_VALUE_ID"],
                    source_row["LIMIT_SET_SCHEDULE_ID"],
                ),
                "permit": row["permit"],
                "feature": row["feature"],
                "parameter": row["parameter"],
                "limit": row["limit"],
                "limit_value": row["limit_value"],
                "monitoring_period_end": row["monitoring_period_end"],
                "dmr_value_nmbr": row["dmr_value_nmbr"],
                "dmr_value_standard_units": row["dmr_value_standard_units"],
                "dmr_unit_desc": row["dmr_unit_desc"],
                "limit_unit_desc": row["limit_unit_desc"],
                "limit_value_standard_units": row["limit_value_standard_units"],
                "limit_value_qualifier_code": row["limit_value_qualifier_code"],
                "dmr_value_qualifier_code": row["dmr_value_qualifier_code"],
                "optional_monitoring_flag": row["optional_monitoring_flag"],
                "limit_type_code": row["limit_type_code"],
                "has_reported_value": row["has_reported_value"],
                "has_limit_value_nmbr": row["has_limit_value_nmbr"],
                "nodi_code": row["nodi_code"],
                "dmr_comment_text": _text(source_row["DMR_COMMENT_TEXT"]),
                "limit_unit_desc": _text(source_row.get("LIMIT_UNIT_DESC")),
                "limit_freq_of_analysis_code": row["limit_freq_of_analysis_code"],
                "statistical_base_type_code": row["statistical_base_type_code"],
            }
        )
    world.derive(
        "measurement_limit_pair",
        measurement_limit_rows,
        roles=[
            ("measurement", "REFERENT"),
            ("permit_limit_row", "REFERENT"),
            ("permit", "REFERENT"),
            ("feature", "REFERENT"),
            ("parameter", "REFERENT"),
            ("limit", "REFERENT"),
            ("limit_value", "REFERENT"),
            ("monitoring_period_end", "TEXT"),
            ("dmr_value_nmbr", "TEXT"),
            ("dmr_value_standard_units", "TEXT"),
            ("limit_value_standard_units", "TEXT"),
            ("limit_value_qualifier_code", "TEXT"),
            ("dmr_value_qualifier_code", "TEXT"),
            ("optional_monitoring_flag", "TEXT"),
            ("limit_type_code", "TEXT"),
            ("has_reported_value", "BOOLEAN"),
            ("has_limit_value_nmbr", "BOOLEAN"),
            ("nodi_code", "TEXT"),
            ("dmr_comment_text", "TEXT"),
            ("limit_freq_of_analysis_code", "TEXT"),
            ("statistical_base_type_code", "TEXT"),
        ],
        inputs=["dmr_measurement", "permit_limit"],
        grounding={"join": ["LIMIT_VALUE_ID", "LIMIT_SET_SCHEDULE_ID"]},
        mode="PURPOSE",
    )

    wet_pass_fail_rows: list[dict[str, object]] = []
    for row in measurement_limit_rows:
        if not _is_wet_pass_fail_reporting(
            limit_unit_desc=row["limit_unit_desc"],
            dmr_unit_desc=row["dmr_unit_desc"],
            dmr_comment_text=row["dmr_comment_text"],
        ):
            continue
        wet_pass_fail_rows.append(
            {
                "measurement": row["measurement"],
                "permit_limit_row": row["permit_limit_row"],
                "permit": row["permit"],
                "feature": row["feature"],
                "parameter": row["parameter"],
                "limit": row["limit"],
                "limit_value": row["limit_value"],
                "monitoring_period_end": row["monitoring_period_end"],
                "reporting_role": "wet_outcome_code",
                "outcome_code": row["dmr_value_nmbr"],
                "outcome_semantics": "0=pass_noec_not_below_critical_dilution;1=fail_noec_below_critical_dilution",
                "is_numeric_concentration_comparison": False,
                "dmr_comment_text": row["dmr_comment_text"],
            }
        )
    world.derive(
        "wet_pass_fail_reporting",
        wet_pass_fail_rows,
        roles=[
            ("measurement", "REFERENT"),
            ("permit_limit_row", "REFERENT"),
            ("permit", "REFERENT"),
            ("feature", "REFERENT"),
            ("parameter", "REFERENT"),
            ("limit", "REFERENT"),
            ("limit_value", "REFERENT"),
            ("monitoring_period_end", "TEXT"),
            ("reporting_role", "TEXT"),
            ("outcome_code", "TEXT"),
            ("outcome_semantics", "TEXT"),
            ("is_numeric_concentration_comparison", "BOOLEAN"),
            ("dmr_comment_text", "TEXT"),
        ],
        inputs=["measurement_limit_pair"],
        grounding={
            "classifier": [
                "LIMIT_UNIT_DESC or DMR_UNIT_DESC matches pass=0;fail=1",
                "DMR_COMMENT_TEXT contains PASS=0 and FAIL=1 reporting instructions",
            ],
            "sources": [
                "sources/permit_limits.csv",
                "documents/farmington/final_permit.txt",
            ],
        },
        mode="PURPOSE",
    )

    numeric_comparison_rows = [
        row
        for row in measurement_limit_rows
        if row["has_reported_value"] and row["has_limit_value_nmbr"]
    ]
    world.derive(
        "numeric_comparison_candidate",
        numeric_comparison_rows,
        roles=[
            ("measurement", "REFERENT"),
            ("permit_limit_row", "REFERENT"),
            ("dmr_value_standard_units", "TEXT"),
            ("limit_value_standard_units", "TEXT"),
            ("limit_value_qualifier_code", "TEXT"),
            ("dmr_value_qualifier_code", "TEXT"),
            ("statistical_base_type_code", "TEXT"),
        ],
        inputs=["measurement_limit_pair"],
        mode="PURPOSE",
    )

    no_numeric_result_rows = [
        row
        for row in dmr_measurement_rows
        if interval_contains(row["monitoring_period_end"], FY_BEGIN, FY_END)
        and not row["has_reported_value"]
    ]
    world.derive(
        "no_numeric_result_case",
        no_numeric_result_rows,
        roles=[
            ("measurement", "REFERENT"),
            ("permit", "REFERENT"),
            ("feature", "REFERENT"),
            ("parameter", "REFERENT"),
            ("limit", "REFERENT"),
            ("limit_value", "REFERENT"),
            ("monitoring_period_end", "TEXT"),
            ("nodi_code", "TEXT"),
            ("optional_monitoring_flag", "TEXT"),
            ("limit_freq_of_analysis_code", "TEXT"),
            ("dmr_freq_of_analysis_code", "TEXT"),
            ("has_limit_value_nmbr", "BOOLEAN"),
        ],
        inputs=["fy2025_measurement"],
        mode="PURPOSE",
    )

    monitoring_requirement_rows = [
        row
        for row in permit_limit_map_rows
        if row["limit_overlaps_fy2025"]
    ]
    world.derive(
        "monitoring_requirement_fy2025",
        monitoring_requirement_rows,
        roles=[
            ("permit_limit_row", "REFERENT"),
            ("permit", "REFERENT"),
            ("feature", "REFERENT"),
            ("parameter", "REFERENT"),
            ("limit", "REFERENT"),
            ("limit_value", "REFERENT"),
            ("optional_monitoring_flag", "TEXT"),
            ("limit_freq_of_analysis_code", "TEXT"),
            ("limit_sample_type_code", "TEXT"),
            ("dmr_comment_text", "TEXT"),
            ("has_limit_value_nmbr", "BOOLEAN"),
            ("limit_set_designator", "TEXT"),
        ],
        inputs=["permit_limit"],
        grounding={"fy_begin": FY_BEGIN, "fy_end": FY_END},
        mode="PURPOSE",
    )

    _declare_purpose_requirements(purpose, limit_rows, documents)


def _declare_purpose_requirements(
    purpose: Purpose,
    limit_rows: list[dict[str, str]],
    documents: list[dict[str, str]],
) -> None:
    purpose.require_materializable(
        "fy2025_measurements_materializable",
        relation="fy2025_measurement",
        purpose="A",
    )
    purpose.require_materializable(
        "measurement_limit_pairs_materializable",
        relation="measurement_limit_pair",
        purpose="A",
    )
    purpose.require_unique(
        "unique_applicable_limit_per_measurement",
        per="measurement",
        candidates="measurement_limit_pair",
        purpose="A",
        cardinality="ONE",
    )
    purpose.require_materializable(
        "numeric_comparison_candidates_materializable",
        relation="numeric_comparison_candidate",
        purpose="A",
    )
    purpose.require_numeric(
        "limit_value_for_comparison",
        relation="numeric_comparison_candidate",
        field="limit_value_standard_units",
        purpose="A",
        per="measurement",
    )
    purpose.require_numeric(
        "reported_value_for_comparison",
        relation="numeric_comparison_candidate",
        field="dmr_value_standard_units",
        purpose="A",
        per="measurement",
    )
    purpose.require_interpreted(
        "limit_comparison_operator",
        relation="numeric_comparison_candidate",
        field="limit_value_qualifier_code",
        known=["<=", ">="],
        purpose="A",
        per="measurement",
    )
    purpose.require_interpreted(
        "reported_value_qualifier",
        relation="numeric_comparison_candidate",
        field="dmr_value_qualifier_code",
        known=["=", "<", ">"],
        purpose="A",
        per="measurement",
    )
    purpose.require_interpreted(
        "optional_monitoring_flag_for_limit_applicability",
        relation="measurement_limit_pair",
        field="optional_monitoring_flag",
        known=["Y", "N"],
        purpose="A",
    )
    purpose.require_interpreted(
        "limit_type_code_for_enforceability",
        relation="measurement_limit_pair",
        field="limit_type_code",
        known=["ENF"],
        purpose="A",
    )
    purpose.require_interpreted(
        "statistical_base_for_limit_comparison",
        relation="numeric_comparison_candidate",
        field="statistical_base_type_code",
        known=["AVG", "MAX", "MIN"],
        purpose="A",
        per="measurement",
    )
    purpose.require_materializable(
        "wet_pass_fail_reporting_materializable",
        relation="wet_pass_fail_reporting",
        purpose=["A", "B", "C"],
    )
    purpose.require_interpreted(
        "wet_pass_fail_outcome_code",
        relation="wet_pass_fail_reporting",
        field="outcome_code",
        known=["0", "1"],
        purpose=["A", "B", "C"],
        per="measurement",
    )
    purpose.require_interpreted(
        "wet_pass_fail_not_numeric_concentration_comparison",
        relation="wet_pass_fail_reporting",
        field="is_numeric_concentration_comparison",
        known=[False],
        purpose=["A", "B", "C"],
        per="measurement",
    )

    purpose.require_materializable(
        "monitoring_requirements_materializable",
        relation="monitoring_requirement_fy2025",
        purpose="B",
    )
    purpose.require_interpreted(
        "monitoring_frequency_code",
        relation="monitoring_requirement_fy2025",
        field="limit_freq_of_analysis_code",
        purpose="B",
        per="permit_limit_row",
    )
    purpose.require_interpreted(
        "limit_sample_type_code",
        relation="monitoring_requirement_fy2025",
        field="limit_sample_type_code",
        purpose="B",
        per="permit_limit_row",
    )
    purpose.require_interpreted(
        "optional_monitoring_flag_for_obligation",
        relation="monitoring_requirement_fy2025",
        field="optional_monitoring_flag",
        known=["Y", "N"],
        purpose="B",
    )
    purpose.require_interpreted(
        "permit_limit_comment_text",
        relation="permit_limit",
        field="dmr_comment_text",
        known=[""],
        purpose=["B", "C"],
        per="permit_limit_row",
    )
    purpose.require_interpreted(
        "limit_set_designator_for_schedule",
        relation="monitoring_requirement_fy2025",
        field="limit_set_designator",
        known=["A", "Q"],
        purpose="B",
    )

    purpose.require_materializable(
        "no_numeric_result_cases_materializable",
        relation="no_numeric_result_case",
        purpose="C",
    )
    purpose.require_interpreted(
        "nodi_code_semantics",
        relation="no_numeric_result_case",
        field="nodi_code",
        known=[""],
        purpose="C",
        per="measurement",
    )
    purpose.require_interpreted(
        "optional_monitoring_flag_for_missing_evidence",
        relation="no_numeric_result_case",
        field="optional_monitoring_flag",
        known=["Y", "N"],
        purpose="C",
    )

    for row in limit_rows:
        comment = _text(row.get("DMR_COMMENT_TEXT"))
        permit_limit_key = {
            "limit_value_id": _text(row["LIMIT_VALUE_ID"]),
            "limit_set_schedule_id": _text(row["LIMIT_SET_SCHEDULE_ID"]),
        }
        if "WHEN DISCHARGING" in comment.upper():
            purpose.unresolved(
                "conditional_discharge_dependent_monitoring",
                subject=permit_limit_key,
                relation="monitoring_requirement_fy2025",
                reason="Permit limit comment references discharge occurrence; structured sources do not establish whether discharge occurred for the evaluated period.",
                purpose=["B", "C"],
                grounding={"dmr_comment_text": comment},
            )
        if "GEOMETRIC MEAN" in comment.upper():
            purpose.unresolved(
                "aggregated_reporting_requirement",
                subject=permit_limit_key,
                relation="monitoring_requirement_fy2025",
                reason="Permit limit comment describes aggregated reporting (geometric mean) whose applicability to individual monitoring periods is not established from structured sources alone.",
                purpose=["B", "C"],
                grounding={"dmr_comment_text": comment},
            )

    purpose.unresolved(
        "permit_document_text_not_available",
        subject={"source": "document_inventory.json"},
        relation="permit_document",
        reason="Permit package documents are inventoried by filename and hash only; narrative permit conditions are not available as structured evidence.",
        purpose=["B", "C"],
        grounding={"n_documents": len(documents)},
    )


def main() -> None:
    src = Source("sources")
    world = World()
    purpose = world.purpose()
    construct(src, world, purpose)


if __name__ == "__main__":
    main()
