#!/usr/bin/env python3
"""Compile Purpose A/B/C IR outputs from world.sqlite derived relations.

Reads 06_world/world.sqlite (or world/world.sqlite). Purpose semantic judgments
(applicable_limit_judgment, monitoring_obligation_judgment, missing_evidence_judgment)
are not persisted in World; this script applies the P7 derivation rules documented
in 07_derivations.json using only admitted World relations.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
WORLD_CANDIDATES = [ROOT / "06_world" / "world.sqlite", ROOT / "world" / "world.sqlite"]
FY2025_PERIOD = "Federal FY2025"
MISSING_NUMERIC = -999999999.0


def find_world_db() -> Path:
    for path in WORLD_CANDIDATES:
        if path.is_file():
            return path
    raise FileNotFoundError(
        "world.sqlite not found; expected 06_world/world.sqlite or world/world.sqlite"
    )


def ref_suffix(referent: str | None, prefix: str) -> str | None:
    if not referent:
        return None
    marker = f"{prefix}:"
    if referent.startswith(marker):
        return referent[len(marker):]
    return referent


def permit_number(facility_id: str) -> str:
    return ref_suffix(facility_id, "facility") or facility_id


def parameter_code(parameter_id: str) -> str:
    return ref_suffix(parameter_id, "parameter") or parameter_id


def discharge_feature(discharge_point_id: str) -> str:
    text = ref_suffix(discharge_point_id, "discharge_point") or discharge_point_id
    if ":" in text:
        return text.rsplit(":", 1)[-1]
    return text


def connect_world() -> sqlite3.Connection:
    db = sqlite3.connect(find_world_db())
    db.row_factory = sqlite3.Row
    return db


def stated_limits_for_measurement(db: sqlite3.Connection, measurement_id: str) -> list[sqlite3.Row]:
    return db.execute(
        """
        SELECT pl.limit_value_id, pl.statistical_base, lsc.classification
        FROM reported_measurement_stated m
        JOIN permit_limit_value_stated pl
          ON pl.facility_id = m.facility_id
          AND pl.discharge_point_id = m.discharge_point_id
          AND pl.parameter_id = m.parameter_id
        LEFT JOIN limit_source_classification lsc ON lsc.limit_value_id = pl.limit_value_id
        WHERE m.measurement_id = ?
          AND m.period_end >= pl.begin_date
          AND m.period_end <= pl.end_date
        """,
        (measurement_id,),
    ).fetchall()


def eligible_limits(db: sqlite3.Connection, measurement_id: str) -> list[str]:
    rows = db.execute(
        """
        SELECT c.limit_value_id
        FROM candidate_limit_for_measurement c
        JOIN numeric_comparison_eligible e
          ON e.measurement_id = c.measurement_id
          AND e.limit_value_id = c.limit_value_id
          AND e.eligible = 1
        WHERE c.measurement_id = ?
        """,
        (measurement_id,),
    ).fetchall()
    return [row["limit_value_id"] for row in rows]


def candidate_limits(db: sqlite3.Connection, measurement_id: str) -> list[str]:
    rows = db.execute(
        "SELECT limit_value_id FROM candidate_limit_for_measurement WHERE measurement_id = ?",
        (measurement_id,),
    ).fetchall()
    return [row["limit_value_id"] for row in rows]


def classify_applicable_limit(
    db: sqlite3.Connection, measurement_id: str
) -> tuple[str, str | None, str | None]:
    """Return (disposition, selected_limit_value_id, unresolved_reason)."""
    measurement = db.execute(
        "SELECT * FROM reported_measurement_stated WHERE measurement_id = ?",
        (measurement_id,),
    ).fetchone()
    if measurement is None:
        return "UNRESOLVED", None, "measurement_context_not_found"

    eligible = eligible_limits(db, measurement_id)
    candidates = candidate_limits(db, measurement_id)
    stated = stated_limits_for_measurement(db, measurement_id)

    if len(eligible) == 1:
        return "ACCEPT", eligible[0], None
    if len(eligible) > 1:
        return "UNRESOLVED", None, "multiple_eligible_enforceable_limits"

    if candidates and not eligible:
        stat_match = [
            row for row in stated if row["statistical_base"] == measurement["statistical_base"]
        ]
        if stat_match and not any(row["classification"] == "enforceable-numeric" for row in stat_match):
            return "REJECT", None, None
        return "UNRESOLVED", None, "numeric_comparison_ineligible"

    if not candidates:
        if stated and not any(row["classification"] == "enforceable-numeric" for row in stated):
            return "REJECT", None, None
        stat_match = [
            row for row in stated if row["statistical_base"] == measurement["statistical_base"]
        ]
        if stat_match and not any(row["classification"] == "enforceable-numeric" for row in stat_match):
            return "REJECT", None, None
        if not stated:
            return "UNRESOLVED", None, "no_stated_limit_for_measurement_context"
        return "UNRESOLVED", None, "no_enforceable_numeric_limit_candidate"

    return "UNRESOLVED", None, "applicability_indeterminate"


def measurement_identity(db: sqlite3.Connection, measurement_id: str) -> dict[str, Any]:
    row = db.execute(
        """
        SELECT m.measurement_id, m.facility_id, m.discharge_point_id, m.parameter_id, m.period_end
        FROM reported_measurement_stated m
        WHERE m.measurement_id = ?
        """,
        (measurement_id,),
    ).fetchone()
    if row is None:
        return {"measurement": measurement_id}
    return {
        "facility_permit_number": permit_number(row["facility_id"]),
        "discharge_point": discharge_feature(row["discharge_point_id"]),
        "parameter_code": parameter_code(row["parameter_id"]),
        "monitoring_period_end": row["period_end"],
        "measurement": row["measurement_id"],
    }


def expectation_identity(db: sqlite3.Connection, expectation_id: str) -> dict[str, Any]:
    row = db.execute(
        """
        SELECT expectation_id, facility_id, discharge_point_id, parameter_id, period_end, source_measurement_id
        FROM monitoring_expectation_without_numeric_result
        WHERE expectation_id = ?
        """,
        (expectation_id,),
    ).fetchone()
    if row is None:
        return {"monitoring_expectation": expectation_id}
    return {
        "facility_permit_number": permit_number(row["facility_id"]),
        "discharge_point": discharge_feature(row["discharge_point_id"]),
        "parameter_code": parameter_code(row["parameter_id"]),
        "monitoring_period_end": row["period_end"],
        "monitoring_expectation": row["expectation_id"],
        "source_measurement": row["source_measurement_id"],
    }


def requirement_identity(db: sqlite3.Connection, requirement_id: str) -> dict[str, Any]:
    row = db.execute(
        """
        SELECT r.requirement_id, r.facility_id, r.discharge_point_id, r.parameter_id
        FROM monitoring_requirement_stated r
        WHERE r.requirement_id = ?
        """,
        (requirement_id,),
    ).fetchone()
    if row is None:
        return {"monitoring_requirement": requirement_id}
    return {
        "facility_permit_number": permit_number(row["facility_id"]),
        "discharge_point": discharge_feature(row["discharge_point_id"]),
        "parameter_code": parameter_code(row["parameter_id"]),
        "monitoring_requirement": row["requirement_id"],
        "fy2025_period": FY2025_PERIOD,
    }


def derive_purpose_a(db: sqlite3.Connection) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []

    universe = db.execute(
        """
        SELECT fy.measurement_id
        FROM fy2025_in_scope_measurement fy
        JOIN measurement_has_ordinary_numeric_value h
          ON h.measurement_id = fy.measurement_id
          AND h.has_numeric_value = 1
        ORDER BY fy.measurement_id
        """
    ).fetchall()

    for unit in universe:
        measurement_id = unit["measurement_id"]
        disposition, limit_id, reason = classify_applicable_limit(db, measurement_id)
        identity = measurement_identity(db, measurement_id)

        if disposition == "ACCEPT":
            exceed = db.execute(
                """
                SELECT exceeds, comparison_performed
                FROM numeric_exceedance_result
                WHERE measurement_id = ? AND limit_value_id = ?
                """,
                (measurement_id, limit_id),
            ).fetchone()
            rows.append(
                {
                    **identity,
                    "applicable_limit_value": limit_id,
                    "comparison_performed": bool(exceed and exceed["comparison_performed"]),
                    "exceeds_limit": bool(exceed and exceed["exceeds"]),
                }
            )
        elif disposition == "REJECT":
            rows.append(
                {
                    **identity,
                    "applicable_limit_value": None,
                    "comparison_performed": False,
                    "exceeds_limit": None,
                }
            )
        else:
            unresolved.append(
                {
                    **identity,
                    "applicability_unresolved_reason": reason or "applicability_indeterminate",
                }
            )

    return {
        "purpose": "applicable_discharge_limits",
        "rows": rows,
        "unresolved": unresolved,
    }


def derive_purpose_b(db: sqlite3.Connection) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []

    universe = db.execute(
        """
        SELECT requirement_id, facility_id, evaluation_period
        FROM fy2025_candidate_monitoring_requirement
        ORDER BY requirement_id
        """
    ).fetchall()

    for unit in universe:
        requirement_id = unit["requirement_id"]
        identity = requirement_identity(db, requirement_id)
        condition = db.execute(
            """
            SELECT condition_text
            FROM permit_condition_language_stated
            WHERE requirement_id = ?
            LIMIT 1
            """,
            (requirement_id,),
        ).fetchone()

        # Without FY2025 discharge/season/event facts, required vs not-required cannot be established.
        if condition and condition["condition_text"]:
            reason = "condition_precedent_not_established"
        else:
            reason = "insufficient_fy2025_applicability_evidence"

        unresolved.append(
            {
                **identity,
                "obligation_outcome": None,
                "applicability_unresolved_reason": reason,
            }
        )

    return {
        "purpose": "monitoring_obligations",
        "rows": rows,
        "unresolved": unresolved,
    }


def derive_purpose_c(db: sqlite3.Connection) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []

    universe = db.execute(
        """
        SELECT expectation_id
        FROM monitoring_expectation_without_numeric_result
        ORDER BY expectation_id
        """
    ).fetchall()

    for unit in universe:
        expectation_id = unit["expectation_id"]
        identity = expectation_identity(db, expectation_id)
        expectation = db.execute(
            """
            SELECT e.*, m.nodi_code
            FROM monitoring_expectation_without_numeric_result e
            JOIN reported_measurement_stated m ON m.measurement_id = e.source_measurement_id
            WHERE e.expectation_id = ?
            """,
            (expectation_id,),
        ).fetchone()
        if expectation is None:
            unresolved.append(
                {
                    **identity,
                    "established_missing_evidence_state": None,
                    "unresolved_reason": "expectation_context_not_found",
                }
            )
            continue

        notation = db.execute(
            """
            SELECT notation_id, notation_text
            FROM documented_no_discharge_notation
            WHERE facility_id = ?
              AND discharge_point_id = ?
              AND parameter_id = ?
              AND period_end = ?
            LIMIT 1
            """,
            (
                expectation["facility_id"],
                expectation["discharge_point_id"],
                expectation["parameter_id"],
                expectation["period_end"],
            ),
        ).fetchone()

        if notation is not None:
            rows.append(
                {
                    **identity,
                    "established_missing_evidence_state": "documented_no_discharge",
                    "notation_referent": notation["notation_id"],
                    "notation_text": notation["notation_text"],
                }
            )
            continue

        if expectation["nodi_code"]:
            unresolved.append(
                {
                    **identity,
                    "established_missing_evidence_state": None,
                    "unresolved_reason": "nodi_semantics_not_established",
                    "nodi_code": expectation["nodi_code"],
                }
            )
            continue

        unresolved.append(
            {
                **identity,
                "established_missing_evidence_state": None,
                "unresolved_reason": "missing_evidence_state_not_established",
            }
        )

    return {
        "purpose": "missing_evidence_semantics",
        "rows": rows,
        "unresolved": unresolved,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def main() -> None:
    db = connect_world()
    outputs = {
        ROOT / "purpose_ir" / "a" / "output.json": derive_purpose_a(db),
        ROOT / "purpose_ir" / "b" / "output.json": derive_purpose_b(db),
        ROOT / "purpose_ir" / "c" / "output.json": derive_purpose_c(db),
    }
    for path, payload in outputs.items():
        write_json(path, payload)
        print(f"Wrote {path} ({len(payload['rows'])} rows, {len(payload['unresolved'])} unresolved)")
    db.close()


if __name__ == "__main__":
    main()
