"""Attach constructor contracts to physical World tables. No relation-name matching."""

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
        relation = row["relation_name"] if isinstance(row, sqlite3.Row) else row[0]
        role_name = row["role_name"] if isinstance(row, sqlite3.Row) else row[2]
        role_type = row["role_type"] if isinstance(row, sqlite3.Row) else row[3]
        column_name = row["column_name"] if isinstance(row, sqlite3.Row) else row[4]
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


def load_vocabulary(path: Path | None) -> list[dict[str, Any]]:
    if path is None or not path.exists():
        return []
    payload = json.loads(path.read_text())
    if isinstance(payload, dict):
        return list(payload.get("relations") or [])
    if isinstance(payload, list):
        return payload
    return []


def _vocab_roles(item: dict[str, Any]) -> list[dict[str, Any]]:
    roles = item.get("roles") or []
    out = []
    for role in roles:
        if not isinstance(role, dict):
            continue
        name = str(role.get("name") or role.get("role_name") or "")
        out.append(
            {
                "role_name": name,
                "role_type": str(role.get("type") or role.get("role_type") or ""),
                "column_name": str(role.get("column_name") or name),
                "semantic_identity": role.get("semantic_identity") or None,
            }
        )
    return out


def contracts_for_world(world: Path, vocabulary_path: Path | None) -> dict[str, dict[str, Any]]:
    sidecar = world.parent / "attached_contracts.json"
    if sidecar.exists():
        payload = json.loads(sidecar.read_text())
        for contract in payload.values():
            for role in contract.get("physical_roles") or []:
                if not role.get("semantic_identity"):
                    role["semantic_identity"] = role.get("role_name")
        return payload
    vocab = load_vocabulary(vocabulary_path)
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
        vocab_roles = _vocab_roles(contract)
        by_surface = {str(r.get("role_name")): r for r in vocab_roles}
        physical = []
        source_roles = roles.get(table) or vocab_roles
        for item in source_roles:
            surface = str(item.get("role_name") or "")
            extra = by_surface.get(surface) or {}
            physical.append(
                {
                    "role_name": surface,
                    "role_type": item.get("role_type") or extra.get("role_type") or "",
                    "column_name": item.get("column_name") or extra.get("column_name") or surface,
                    "semantic_identity": extra.get("semantic_identity") or item.get("semantic_identity"),
                }
            )
        contract["physical_roles"] = physical
        attached[table] = contract
    return attached
