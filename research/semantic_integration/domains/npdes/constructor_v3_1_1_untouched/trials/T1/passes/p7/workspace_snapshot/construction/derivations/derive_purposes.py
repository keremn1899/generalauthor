#!/usr/bin/env python3
"""Compile Purpose A/B/C outputs from world.sqlite and admitted dispositions."""

from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
WORLD_PATHS = [ROOT / "06_world" / "world.sqlite", ROOT / "world" / "world.sqlite"]
DISPOSITIONS_PATH = ROOT / "05_dispositions.json"
VIEW_ID = "diligence-world"


def find_world_db() -> Path:
    for path in WORLD_PATHS:
        if path.exists():
            return path
    raise FileNotFoundError(
        "world.sqlite not found; expected 06_world/world.sqlite or world/world.sqlite"
    )


def load_dispositions() -> list[dict[str, Any]]:
    with DISPOSITIONS_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def index_dispositions(
    dispositions: list[dict[str, Any]],
) -> dict[str, dict[str, dict[str, Any]]]:
    by_relation: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for item in dispositions:
        relation = item["relation"]
        values = item.get("values", {})
        key = (
            values.get("measurement")
            or values.get("requirement")
            or values.get("expectation")
            or item["obligation_id"]
        )
        by_relation[relation][key] = item
    return by_relation


def grounding_payload(item: dict[str, Any] | None) -> list[dict[str, str]]:
    if not item:
        return []
    return list(item.get("grounding", []))


def derive_purpose_a(
    conn: sqlite3.Connection,
    disp: dict[str, dict[str, dict[str, Any]]],
) -> dict[str, Any]:
    measurements = conn.execute(
        """
        SELECT
            f.measurement_id,
            f.permit_nbr,
            f.monitoring_period_end,
            m.perm_feature_nbr,
            m.parameter_code
        FROM fy2025_in_scope_measurement f
        INNER JOIN reported_dmr_measurement m ON m.measurement_id = f.measurement_id
        ORDER BY f.permit_nbr, m.perm_feature_nbr, m.parameter_code, f.monitoring_period_end
        """
    ).fetchall()

    selection = disp["applicable_limit_selection"]
    comparison = disp["limit_numeric_comparison_applicability"]
    exceedance = disp["exceedance_determination"]

    rows: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []

    for row in measurements:
        measurement_id = row["measurement_id"]
        base = {
            "facility": row["permit_nbr"],
            "discharge_point": row["perm_feature_nbr"],
            "parameter": row["parameter_code"],
            "monitoring_period": row["monitoring_period_end"],
            "measurement": measurement_id,
        }
        sel = selection.get(measurement_id)
        cmp_ = comparison.get(measurement_id)
        exc = exceedance.get(measurement_id)

        if not sel or sel["disposition"] == "UNRESOLVED":
            unresolved.append(
                {
                    **base,
                    "blocking_state": "limit_applicability_unresolved",
                    "grounding": grounding_payload(sel),
                    "rationale": (sel or {}).get(
                        "rationale",
                        "No admitted applicable_limit_selection disposition.",
                    ),
                }
            )
            continue

        if not cmp_ or cmp_["disposition"] == "UNRESOLVED":
            unresolved.append(
                {
                    **base,
                    "blocking_state": "numeric_comparison_classification_unresolved",
                    "grounding": grounding_payload(cmp_) or grounding_payload(sel),
                    "rationale": (cmp_ or {}).get(
                        "rationale",
                        "Numeric comparison classification blocked pending limit selection.",
                    ),
                }
            )
            continue

        cmp_values = cmp_["values"]
        output_row = {
            **base,
            "applicable_limit": sel["values"].get("selected_limit"),
            "limit_row": sel["values"].get("limit_row"),
            "numeric_comparison_applicable": bool(
                cmp_values.get("comparison_applicable")
            ),
            "comparison_class": cmp_values.get("comparison_class"),
            "exceedance_outcome": None,
            "grounding": (
                grounding_payload(sel)
                + grounding_payload(cmp_)
                + grounding_payload(exc)
            ),
            "rationale": cmp_.get("rationale", ""),
        }

        if cmp_values.get("comparison_applicable"):
            if not exc or exc["disposition"] == "UNRESOLVED":
                unresolved.append(
                    {
                        **base,
                        "blocking_state": "exceedance_unresolved",
                        "applicable_limit": sel["values"].get("selected_limit"),
                        "limit_row": sel["values"].get("limit_row"),
                        "numeric_comparison_applicable": True,
                        "comparison_class": cmp_values.get("comparison_class"),
                        "grounding": grounding_payload(exc)
                        or grounding_payload(cmp_)
                        or grounding_payload(sel),
                        "rationale": (exc or {}).get(
                            "rationale",
                            "Exceedance determination missing for enforceable numeric comparison.",
                        ),
                    }
                )
                continue
            output_row["exceedance_outcome"] = exc["values"].get("exceedance_outcome")
            output_row["rationale"] = exc.get("rationale", output_row["rationale"])

        rows.append(output_row)

    return {
        "purpose": "applicable_discharge_limits",
        "rows": rows,
        "unresolved": unresolved,
        "limitations": [
            "Purpose A rows require admitted applicable_limit_selection and limit_numeric_comparison_applicability ACCEPT dispositions from 05_dispositions.json.",
            "Exceedance outcomes require admitted exceedance_determination ACCEPT when numeric_comparison_applicable is true.",
            "692 limit-applicability cases and 12 enforceable-numeric exceedance gaps remain unresolved in admitted dispositions.",
        ],
    }


def derive_purpose_b(
    conn: sqlite3.Connection,
    disp: dict[str, dict[str, dict[str, Any]]],
) -> dict[str, Any]:
    candidates = conn.execute(
        """
        SELECT
            requirement_id,
            limit_row_id,
            permit_nbr,
            perm_feature_nbr,
            parameter_code,
            limit_freq_of_analysis_code,
            optional_monitoring_flag,
            requirement_kind
        FROM monitoring_requirement_candidate
        ORDER BY permit_nbr, perm_feature_nbr, parameter_code, requirement_id
        """
    ).fetchall()

    applicability = disp["monitoring_obligation_applicability"]
    rows: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []

    for candidate in candidates:
        requirement_id = candidate["requirement_id"]
        base = {
            "facility": candidate["permit_nbr"],
            "discharge_point": candidate["perm_feature_nbr"],
            "parameter": candidate["parameter_code"],
            "requirement": requirement_id,
            "limit_row": candidate["limit_row_id"],
            "requirement_kind": candidate["requirement_kind"],
            "limit_freq_of_analysis_code": candidate["limit_freq_of_analysis_code"],
            "optional_monitoring_flag": candidate["optional_monitoring_flag"],
        }
        item = applicability.get(requirement_id)
        if not item or item["disposition"] == "UNRESOLVED":
            unresolved.append(
                {
                    **base,
                    "blocking_state": "obligation_applicability_unresolved",
                    "grounding": grounding_payload(item),
                    "rationale": (item or {}).get(
                        "rationale",
                        "No admitted monitoring_obligation_applicability disposition.",
                    ),
                }
            )
            continue

        values = item["values"]
        rows.append(
            {
                **base,
                "obligation_applicability": values.get("applicability"),
                "condition_evidence": values.get("condition_evidence"),
                "grounding": grounding_payload(item),
                "rationale": item.get("rationale", ""),
            }
        )

    return {
        "purpose": "monitoring_obligations",
        "rows": rows,
        "unresolved": unresolved,
        "limitations": [
            "Purpose B rows require admitted monitoring_obligation_applicability ACCEPT dispositions from 05_dispositions.json.",
            "Affirmative not-required outcomes require positive evidence; no closed-world negation from missing DMR rows.",
            "23 requirement candidates remain unresolved; all 67 admitted ACCEPT rows are required.",
        ],
    }


def derive_purpose_c(
    conn: sqlite3.Connection,
    disp: dict[str, dict[str, dict[str, Any]]],
) -> dict[str, Any]:
    expectations = conn.execute(
        """
        SELECT
            n.expectation_id,
            n.measurement_id,
            n.permit_nbr,
            n.perm_feature_nbr,
            n.parameter_code,
            n.monitoring_period_end,
            n.nodi_code,
            n.has_numeric_value
        FROM no_ordinary_numeric_result_measurement n
        ORDER BY n.permit_nbr, n.perm_feature_nbr, n.parameter_code, n.monitoring_period_end
        """
    ).fetchall()

    classification = disp["missing_evidence_classification"]
    rows: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []

    for item in expectations:
        expectation_id = item["expectation_id"]
        base = {
            "facility": item["permit_nbr"],
            "discharge_point": item["perm_feature_nbr"],
            "parameter": item["parameter_code"],
            "monitoring_period": item["monitoring_period_end"],
            "expectation": expectation_id,
            "measurement": item["measurement_id"],
            "nodi_code": item["nodi_code"],
            "has_numeric_value": bool(item["has_numeric_value"]),
        }
        cls = classification.get(expectation_id)
        if not cls or cls["disposition"] == "UNRESOLVED":
            unresolved.append(
                {
                    **base,
                    "blocking_state": "missing_evidence_classification_unresolved",
                    "grounding": grounding_payload(cls),
                    "rationale": (cls or {}).get(
                        "rationale",
                        "No admitted missing_evidence_classification disposition.",
                    ),
                }
            )
            continue

        values = cls["values"]
        rows.append(
            {
                **base,
                "established_state": values.get("established_state"),
                "grounding": grounding_payload(cls),
                "rationale": cls.get("rationale", ""),
            }
        )

    return {
        "purpose": "missing_evidence_semantics",
        "rows": rows,
        "unresolved": unresolved,
        "limitations": [
            "Purpose C rows require admitted missing_evidence_classification ACCEPT dispositions from 05_dispositions.json.",
            "documented_no_discharge_assertion has zero ACCEPT tuples in world.sqlite; no documented_no_discharge rows emitted.",
            "All 186 in-scope no-ordinary-numeric-result cases remain unresolved in admitted dispositions.",
        ],
    }


def write_output(name: str, payload: dict[str, Any]) -> Path:
    path = ROOT / "purpose_ir" / name / "output.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    return path


def main() -> None:
    world_path = find_world_db()
    dispositions = load_dispositions()
    disp = index_dispositions(dispositions)

    conn = sqlite3.connect(world_path)
    conn.row_factory = sqlite3.Row
    try:
        outputs = {
            "a": derive_purpose_a(conn, disp),
            "b": derive_purpose_b(conn, disp),
            "c": derive_purpose_c(conn, disp),
        }
    finally:
        conn.close()

    for name, payload in outputs.items():
        path = write_output(name, payload)
        print(
            f"wrote {path.relative_to(ROOT)} "
            f"(rows={len(payload['rows'])}, unresolved={len(payload['unresolved'])})"
        )


if __name__ == "__main__":
    main()
