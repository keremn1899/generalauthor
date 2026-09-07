"""Read participant World catalogs without depending on constructor relation names."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


def connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def table_names(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE '_tv_%'"
    ).fetchall()
    return [row[0] for row in rows]


def roles_from_tv(conn: sqlite3.Connection) -> dict[str, list[dict[str, str]]]:
    try:
        rows = conn.execute(
            "SELECT relation_name, ordinal, role_name, role_type, column_name FROM _tv_roles ORDER BY relation_name, ordinal"
        ).fetchall()
    except sqlite3.Error:
        return {}
    out: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        if isinstance(row, sqlite3.Row):
            relation, _ordinal, role_name, role_type, column_name = (
                row["relation_name"],
                row["ordinal"],
                row["role_name"],
                row["role_type"],
                row["column_name"],
            )
        else:
            relation, _ordinal, role_name, role_type, column_name = row[0], row[1], row[2], row[3], row[4]
        out.setdefault(relation, []).append(
            {
                "role_name": role_name,
                "role_type": role_type,
                "column_name": column_name,
            }
        )
    return out


def dict_tables(path: Path) -> dict[str, list[dict[str, Any]]]:
    conn = connect(path)
    out: dict[str, list[dict[str, Any]]] = {}
    try:
        for table in table_names(conn):
            try:
                rows = conn.execute(f'SELECT * FROM "{table}"').fetchall()
            except sqlite3.Error:
                continue
            out[table] = [{k: row[k] for k in row.keys() if k != "_assertion_id"} for row in rows]
    finally:
        conn.close()
    return out


def load_vocabulary(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text())
    if isinstance(payload, dict):
        return list(payload.get("relations") or [])
    if isinstance(payload, list):
        return payload
    return []


def contracts_for_world(world: Path, vocabulary_path: Path | None) -> dict[str, dict[str, Any]]:
    sidecar = world.parent / "attached_contracts.json"
    if sidecar.exists():
        return json.loads(sidecar.read_text())
    vocab = load_vocabulary(vocabulary_path) if vocabulary_path else []
    by_name = {str(item.get("name")): item for item in vocab if isinstance(item, dict) and item.get("name")}
    conn = connect(world)
    try:
        roles = roles_from_tv(conn)
        tables = table_names(conn)
    finally:
        conn.close()
    attached: dict[str, dict[str, Any]] = {}
    for table in tables:
        contract = dict(by_name.get(table) or {})
        contract["physical_table"] = table
        if roles.get(table):
            contract["physical_roles"] = roles[table]
        elif contract.get("roles"):
            contract["physical_roles"] = [
                {
                    "role_name": r.get("name"),
                    "role_type": r.get("type"),
                    "column_name": r.get("name"),
                }
                for r in contract["roles"]
                if isinstance(r, dict)
            ]
        attached[table] = contract
    return attached
