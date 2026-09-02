"""Inspect participant TaskView sqlite without depending on relation names."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any

ID_TOKEN = re.compile(
    r"(crm:[A-Za-z0-9-]+|billing:[^|]+|registry:[A-Za-z0-9 -]+|contract:[A-Za-z0-9-]+|INV-[0-9]+|MSA-[A-Z0-9-]+|SOW-[A-Z0-9-]+)"
)
DISPOSITIONS = {"SAME_ENTITY", "DISTINCT", "UNRESOLVED", "ACCEPT", "REJECT"}


def connect(path: Path) -> sqlite3.Connection | None:
    if not path.exists():
        return None
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def table_names(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    return [row[0] for row in rows]


def grounding_rate(path: Path) -> dict[str, Any]:
    conn = connect(path)
    if conn is None:
        return {"sqlite": False, "base_assertions": 0, "grounded": 0, "rate": None}
    try:
        assertions = conn.execute(
            "SELECT assertion_id FROM _tv_assertions"
        ).fetchall()
        ids = [row[0] for row in assertions]
        grounded = 0
        for assertion_id in ids:
            n = conn.execute(
                "SELECT COUNT(*) AS n FROM _tv_groundings "
                "WHERE subject_type='ASSERTION' AND subject_id=?",
                (assertion_id,),
            ).fetchone()["n"]
            if n:
                grounded += 1
        total = len(ids)
        return {
            "sqlite": True,
            "base_assertions": total,
            "grounded": grounded,
            "ungrounded": total - grounded,
            "rate": (grounded / total) if total else None,
        }
    except sqlite3.Error as exc:
        return {"sqlite": True, "error": str(exc), "base_assertions": 0, "grounded": 0, "rate": None}
    finally:
        conn.close()


def all_text_values(path: Path) -> list[str]:
    conn = connect(path)
    if conn is None:
        return []
    values: list[str] = []
    try:
        for table in table_names(conn):
            if table.startswith("_tv_"):
                continue
            try:
                rows = conn.execute(f'SELECT * FROM "{table}"').fetchall()
            except sqlite3.Error:
                continue
            for row in rows:
                for item in row:
                    if isinstance(item, str):
                        values.append(item)
    finally:
        conn.close()
    return values


def contains_token(path: Path, token: str) -> bool:
    return any(token in value for value in all_text_values(path))


def disposition_rows(path: Path) -> list[dict[str, Any]]:
    conn = connect(path)
    if conn is None:
        return []
    found: list[dict[str, Any]] = []
    try:
        for table in table_names(conn):
            if table.startswith("_tv_"):
                continue
            try:
                rows = conn.execute(f'SELECT * FROM "{table}"').fetchall()
            except sqlite3.Error:
                continue
            if not rows:
                continue
            keys = rows[0].keys()
            disp_col = next((k for k in keys if "disp" in k.lower() or k.lower() in ("epistemic", "judgment")), None)
            if disp_col is None:
                sample = [str(rows[0][k]) for k in keys]
                if not any(val in DISPOSITIONS for val in sample):
                    continue
                disp_col = next(k for k in keys if str(rows[0][k]) in DISPOSITIONS)
            id_cols = [k for k in keys if k != disp_col]
            for row in rows:
                disp = str(row[disp_col])
                if disp not in DISPOSITIONS:
                    continue
                tokens = []
                for key in id_cols:
                    val = row[key]
                    if isinstance(val, str):
                        tokens.extend(ID_TOKEN.findall(val) or ([val] if ":" in val else []))
                if len(tokens) >= 2:
                    found.append(
                        {
                            "table": table,
                            "left": tokens[0],
                            "right": tokens[1],
                            "disposition": disp,
                        }
                    )
    finally:
        conn.close()
    return found
