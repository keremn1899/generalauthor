#!/usr/bin/env python3
"""FY2025 monitoring/compliance analysis over an accepted World sqlite.

Ordinary Python + SQLite. No source CSVs, PDFs, comment parsing, or NODI legends.
Optional enrichment relations are used only if present in the World schema.
"""

from __future__ import annotations

import csv
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path


def _tables(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    return {r[0] for r in rows}


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {r[1] for r in conn.execute(f'PRAGMA table_info("{table}")').fetchall()}


def _parse_key(key_json: str) -> dict:
    try:
        return json.loads(key_json)
    except json.JSONDecodeError:
        return {}


def _finite(value: object) -> float | None:
    text = str(value or "").strip().replace(",", "")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _load_sql(sql_path: Path) -> str:
    return sql_path.read_text(encoding="utf-8")


def classify_row(
    row: dict,
    *,
    limit_holes: dict[str, set[str]],
    limit_id_holes: dict[tuple[str, str], set[str]],
    measurement_holes: dict[str, set[str]],
    monitoring_condition: str,
    pass_fail_value: str | None,
    referent_keys: dict[str, dict],
) -> dict:
    measurement = row["measurement"]
    permit_limit_row = row["permit_limit_row"]
    holes = set(measurement_holes.get(measurement) or [])
    holes |= set(limit_holes.get(permit_limit_row) or [])
    key = referent_keys.get(permit_limit_row) or {}
    pair = (str(key.get("limit_value_id") or ""), str(key.get("limit_set_schedule_id") or ""))
    if pair[0]:
        holes |= set(limit_id_holes.get(pair) or [])

    nodi_code = str(row.get("nodi_code") or "")
    comparison_status = "NOT_ESTABLISHED"
    monitoring_status = "NOT_ESTABLISHED"
    evidence_status = "NOT_ESTABLISHED"
    unresolved_reason = ""

    if "conditional_discharge_dependent_monitoring" in holes:
        monitoring_status = "UNRESOLVED_SEMANTIC"
    elif "discharge_occurrence_in_period" in holes:
        monitoring_status = "UNRESOLVED_FACTUAL"
    elif monitoring_condition == "discharge_occurrence":
        monitoring_status = "CONDITIONAL_ON_DISCHARGE"
    elif "monitoring_frequency_code" in holes:
        monitoring_status = "FREQUENCY_UNINTERPRETED"
    else:
        monitoring_status = "NO_DISCHARGE_CONDITION_ASSERTED"

    if pass_fail_value is not None:
        if str(pass_fail_value).strip() == "0":
            comparison_status = "PASS"
        elif str(pass_fail_value).strip() == "1":
            comparison_status = "FAIL"
        else:
            comparison_status = "UNRESOLVED_SEMANTIC"
            holes.add("wet_pass_fail_outcome_code")
    elif "pass_fail_reporting_semantics" in holes:
        comparison_status = "UNRESOLVED_SEMANTIC"
    elif "nodi_code_semantics" in holes:
        comparison_status = "UNRESOLVED_SEMANTIC"
    elif int(row.get("is_numeric_comparison_candidate") or 0) == 1:
        reported = _finite(row.get("reported_standard_units") or row.get("reported_value"))
        limit = _finite(row.get("limit_standard_units") or row.get("numeric_limit"))
        qualifier = str(row.get("limit_qualifier") or "")
        if "limit_comparison_operator" in holes or "reported_value_qualifier" in holes:
            comparison_status = "UNRESOLVED_SEMANTIC"
        elif reported is None or limit is None:
            comparison_status = "UNRESOLVED_SEMANTIC"
        elif qualifier in {"<=", "<", "C", ""}:
            comparison_status = "EXCEEDANCE" if reported > limit else "WITHIN_LIMIT"
        elif qualifier in {">=", ">"}:
            comparison_status = "EXCEEDANCE" if reported < limit else "WITHIN_LIMIT"
        else:
            comparison_status = "UNRESOLVED_SEMANTIC"
            holes.add("limit_comparison_operator")
    elif int(row.get("is_no_numeric_result_case") or 0) == 1:
        comparison_status = "NO_NUMERIC_RESULT"
    else:
        comparison_status = "NOT_NUMERIC_CANDIDATE"

    blocking = sorted(
        h
        for h in holes
        if h
        in {
            "nodi_code_semantics",
            "conditional_discharge_dependent_monitoring",
            "discharge_occurrence_in_period",
            "pass_fail_reporting_semantics",
            "wet_pass_fail_outcome_code",
            "aggregated_reporting_requirement",
            "permit_document_text_not_available",
        }
    )
    if comparison_status in {"PASS", "FAIL", "EXCEEDANCE", "WITHIN_LIMIT"} and monitoring_status not in {
        "UNRESOLVED_SEMANTIC",
        "UNRESOLVED_FACTUAL",
    }:
        evidence_status = "DETERMINATE"
    elif monitoring_status == "UNRESOLVED_FACTUAL" or "discharge_occurrence_in_period" in holes:
        evidence_status = "UNRESOLVED_FACTUAL"
    elif comparison_status == "UNRESOLVED_SEMANTIC" or monitoring_status == "UNRESOLVED_SEMANTIC" or blocking:
        evidence_status = "UNRESOLVED_SEMANTIC"
    elif comparison_status == "NO_NUMERIC_RESULT":
        evidence_status = "UNRESOLVED_SEMANTIC" if "nodi_code_semantics" in holes else "NOT_ESTABLISHED"
    else:
        evidence_status = "NOT_ESTABLISHED"

    unresolved_reason = ";".join(sorted(holes)) if holes else ""

    permit_key = referent_keys.get(row["permit"]) or {}
    feature_key = referent_keys.get(row["feature"]) or {}
    parameter_key = referent_keys.get(row["parameter"]) or {}
    return {
        "application_key": measurement,
        "facility": permit_key.get("permit_number") or row["permit"],
        "outfall": feature_key.get("feature_number") or row["feature"],
        "parameter": parameter_key.get("parameter_code") or row["parameter"],
        "monitoring_period": row["monitoring_period"],
        "reported_value": row.get("reported_value") or "",
        "numeric_limit": row.get("numeric_limit") or "",
        "applicable_requirement": permit_limit_row,
        "comparison_status": comparison_status,
        "monitoring_status": monitoring_status,
        "unresolved_reason": unresolved_reason,
        "evidence_status": evidence_status,
        "nodi_code": nodi_code,
        "has_reported_value": row.get("has_reported_value"),
        "is_numeric_comparison_candidate": row.get("is_numeric_comparison_candidate"),
        "monitoring_condition": monitoring_condition,
        "pass_fail_reported": "" if pass_fail_value is None else str(pass_fail_value),
    }


def run_analysis(*, world_sqlite: Path, sql_path: Path, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(world_sqlite)
    conn.row_factory = sqlite3.Row
    try:
        tables = _tables(conn)
        if "measurement_limit_pair" not in tables:
            raise RuntimeError("WORLD_ONLY_CONSUMPTION_FAILED: measurement_limit_pair missing")
        sql = _load_sql(sql_path)
        core = [dict(r) for r in conn.execute(sql).fetchall()]
        referent_keys = {
            rid: _parse_key(key_json)
            for rid, key_json in conn.execute("SELECT id, key_json FROM _referent")
        }
        measurement_holes: dict[str, set[str]] = defaultdict(set)
        limit_holes: dict[str, set[str]] = defaultdict(set)
        limit_id_holes: dict[tuple[str, str], set[str]] = defaultdict(set)
        for hole in conn.execute("SELECT requirement, subject_json FROM _hole"):
            req = hole["requirement"]
            subject = _parse_key(hole["subject_json"])
            if subject.get("measurement"):
                measurement_holes[str(subject["measurement"])].add(req)
            if subject.get("permit_limit_row"):
                limit_holes[str(subject["permit_limit_row"])].add(req)
            if subject.get("limit_value_id") and subject.get("limit_set_schedule_id"):
                limit_id_holes[
                    (str(subject["limit_value_id"]), str(subject["limit_set_schedule_id"]))
                ].add(req)

        conditions: dict[str, str] = {}
        if "monitoring_requirement_fy2025" in tables and "monitoring_condition" in _columns(
            conn, "monitoring_requirement_fy2025"
        ):
            for rec in conn.execute(
                "SELECT permit_limit_row, monitoring_condition FROM monitoring_requirement_fy2025"
            ):
                conditions[rec["permit_limit_row"]] = rec["monitoring_condition"] or ""

        pass_fail: dict[str, str] = {}
        if "pass_fail_outcome_reporting" in tables:
            for rec in conn.execute(
                "SELECT measurement, dmr_value_nmbr FROM pass_fail_outcome_reporting"
            ):
                pass_fail[rec["measurement"]] = rec["dmr_value_nmbr"]
        elif "binary_pass_fail_measurement" in tables:
            value_col = "dmr_value_standard_units"
            cols = _columns(conn, "binary_pass_fail_measurement")
            if "dmr_value_nmbr" in cols:
                value_col = "dmr_value_nmbr"
            for rec in conn.execute(
                f"SELECT measurement, {value_col} AS value FROM binary_pass_fail_measurement"
            ):
                pass_fail[rec["measurement"]] = rec["value"]

        rows = []
        for raw in core:
            rows.append(
                classify_row(
                    raw,
                    limit_holes=limit_holes,
                    limit_id_holes=limit_id_holes,
                    measurement_holes=measurement_holes,
                    monitoring_condition=conditions.get(raw["permit_limit_row"], ""),
                    pass_fail_value=pass_fail.get(raw["measurement"]),
                    referent_keys=referent_keys,
                )
            )
        rows.sort(
            key=lambda r: (
                r["facility"],
                r["outfall"],
                r["parameter"],
                r["monitoring_period"],
                r["application_key"],
            )
        )
        hole_counts = dict(
            conn.execute("SELECT requirement, COUNT(*) FROM _hole GROUP BY requirement ORDER BY 1")
        )
        n_nodi_c = conn.execute(
            "SELECT COUNT(*) FROM no_numeric_result_case WHERE nodi_code = 'C'"
        ).fetchone()[0]
        n_nodi_9 = conn.execute(
            "SELECT COUNT(*) FROM no_numeric_result_case WHERE nodi_code = '9'"
        ).fetchone()[0]
    finally:
        conn.close()

    fieldnames = list(rows[0].keys()) if rows else [
        "application_key",
        "facility",
        "outfall",
        "parameter",
        "monitoring_period",
        "reported_value",
        "numeric_limit",
        "applicable_requirement",
        "comparison_status",
        "monitoring_status",
        "unresolved_reason",
        "evidence_status",
        "nodi_code",
    ]
    csv_path = output_dir / "monitoring_analysis.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    json_path = output_dir / "monitoring_analysis.json"
    json_path.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")

    evidence = Counter(r["evidence_status"] for r in rows)
    comparison = Counter(r["comparison_status"] for r in rows)
    monitoring = Counter(r["monitoring_status"] for r in rows)
    nodi_unresolved = sum(
        1
        for r in rows
        if r["nodi_code"] in {"C", "9"} and "nodi_code_semantics" in (r["unresolved_reason"] or "")
    )
    summary = {
        "n_rows": len(rows),
        "evidence_status": dict(evidence),
        "comparison_status": dict(comparison),
        "monitoring_status": dict(monitoring),
        "n_nodi_c_cases": n_nodi_c,
        "n_nodi_9_cases": n_nodi_9,
        "n_nodi_c_or_9_with_unresolved_semantics": nodi_unresolved,
        "n_pass": comparison.get("PASS", 0),
        "n_fail": comparison.get("FAIL", 0),
        "n_exceedance": comparison.get("EXCEEDANCE", 0),
        "n_within_limit": comparison.get("WITHIN_LIMIT", 0),
        "n_unresolved_factual_monitoring": monitoring.get("UNRESOLVED_FACTUAL", 0),
        "n_unresolved_semantic_monitoring": monitoring.get("UNRESOLVED_SEMANTIC", 0),
        "n_conditional_on_discharge": monitoring.get("CONDITIONAL_ON_DISCHARGE", 0),
        "hole_counts": hole_counts,
        "world_sqlite": str(world_sqlite),
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    md = [
        "# Monitoring analysis summary",
        "",
        f"rows: {summary['n_rows']}",
        "",
        "## evidence_status",
        "",
    ]
    for key, n in sorted(evidence.items()):
        md.append(f"- {key}: {n}")
    md.extend(["", "## comparison_status", ""])
    for key, n in sorted(comparison.items()):
        md.append(f"- {key}: {n}")
    md.extend(["", "## monitoring_status", ""])
    for key, n in sorted(monitoring.items()):
        md.append(f"- {key}: {n}")
    md.extend(
        [
            "",
            "## NODI negative control",
            "",
            f"- no_numeric_result_case NODI C: {n_nodi_c}",
            f"- no_numeric_result_case NODI 9: {n_nodi_9}",
            f"- C/9 rows with nodi_code_semantics unresolved: {nodi_unresolved}",
            "",
        ]
    )
    (output_dir / "summary.md").write_text("\n".join(md), encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) < 2:
        print("usage: monitoring_analysis.py WORLD.sqlite OUTPUT_DIR [SQL_PATH]", file=sys.stderr)
        return 2
    world = Path(args[0])
    output = Path(args[1])
    sql = Path(args[2]) if len(args) > 2 else Path(__file__).resolve().parent.parent / "sql" / "monitoring_analysis.sql"
    run_analysis(world_sqlite=world, sql_path=sql, output_dir=output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
