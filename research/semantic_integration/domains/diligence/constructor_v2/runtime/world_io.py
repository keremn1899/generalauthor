"""Flexible World table extraction for certified and participant schemas."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from research.semantic_integration.domains.diligence.pass_localization.inspect_world import (
    table_names,
)
from research.semantic_integration.domains.diligence.pass_localization.pairs import (
    load_dispositions,
    pair_from_obj,
)


IDENTITY_DISPOSITIONS = {"SAME_ENTITY", "DISTINCT", "UNRESOLVED"}
IDENTITY_MAP = {
    "SAME_ENTITY": "SAME_ENTITY",
    "DISTINCT": "DISTINCT",
    "UNRESOLVED": "UNRESOLVED",
    "REJECT": "DISTINCT",
}
REF_PREFIXES = ("crm:", "billing:", "registry:", "contract:")


def _is_ref(value: str) -> bool:
    text = str(value)
    return any(text.startswith(prefix) for prefix in REF_PREFIXES)


def dict_rows(path: Path) -> dict[str, list[dict[str, Any]]]:
    if not path.exists():
        return {}
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    out: dict[str, list[dict[str, Any]]] = {}
    try:
        for table in table_names(conn):
            if table.startswith("_tv_"):
                continue
            try:
                rows = conn.execute(f'SELECT * FROM "{table}"').fetchall()
            except sqlite3.Error:
                continue
            out[table] = [{k: row[k] for k in row.keys() if k != "_assertion_id"} for row in rows]
    finally:
        conn.close()
    return out


def _has_cols(row: dict[str, Any], *names: str) -> bool:
    keys = {k.lower() for k in row}
    return all(name.lower() in keys for name in names)


def _col(row: dict[str, Any], *names: str) -> Any:
    lower = {k.lower(): k for k in row}
    for name in names:
        if name.lower() in lower:
            return row[lower[name.lower()]]
    return None


def invoices(tables: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    for rows in tables.values():
        if rows and _has_cols(rows[0], "invoice_id", "billed_name"):
            return rows
    return []


def contracts(tables: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    found = []
    for rows in tables.values():
        if not rows:
            continue
        if _has_cols(rows[0], "contract_id") and (
            _has_cols(rows[0], "counterparty_text")
            or _has_cols(rows[0], "counterparty_name")
            or _has_cols(rows[0], "counterparty")
        ):
            for row in rows:
                found.append(
                    {
                        "contract_id": _col(row, "contract_id"),
                        "counterparty_text": str(
                            _col(row, "counterparty_text", "counterparty_name", "counterparty") or ""
                        ),
                    }
                )
            return found
    return found


def clause_kinds(tables: dict[str, list[dict[str, Any]]]) -> dict[str, set[str]]:
    kinds: dict[str, set[str]] = {}
    for rows in tables.values():
        if not rows or not _has_cols(rows[0], "contract_id", "clause_kind"):
            continue
        for row in rows:
            present = _col(row, "present")
            if present is False or present == 0 or str(present).lower() == "false":
                continue
            cid = str(_col(row, "contract_id"))
            kinds.setdefault(cid, set()).add(str(_col(row, "clause_kind")))
    return kinds


def active_contracts(tables: dict[str, list[dict[str, Any]]]) -> dict[str, bool]:
    active: dict[str, bool] = {}
    for name, rows in tables.items():
        if not rows or not _has_cols(rows[0], "contract_id"):
            continue
        if _has_cols(rows[0], "active"):
            for row in rows:
                active[str(_col(row, "contract_id"))] = bool(_col(row, "active"))
            if active:
                return active
        if "lifecycle" in name.lower() or _has_cols(rows[0], "status") and "clause" not in name.lower():
            if "invoice" in name.lower():
                continue
            for row in rows:
                status = str(_col(row, "status") or "").lower()
                if status:
                    active[str(_col(row, "contract_id"))] = status in {"active", "in_force", "current"}
    return active


def identity_from_tables(tables: dict[str, list[dict[str, Any]]]) -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    for rows in tables.values():
        if not rows:
            continue
        sample = rows[0]
        disp_key = next(
            (k for k in sample if k.lower() in {"disposition", "epistemic", "judgment"}),
            None,
        )
        if disp_key is None:
            continue
        for row in rows:
            disp = str(row.get(disp_key) or "")
            mapped = IDENTITY_MAP.get(disp, disp)
            if mapped not in IDENTITY_DISPOSITIONS:
                continue
            left = _col(row, "left")
            right = _col(row, "right")
            if not left or not right:
                ids = [
                    str(v)
                    for k, v in row.items()
                    if k != disp_key and isinstance(v, str) and _is_ref(str(v))
                ]
                if len(ids) < 2:
                    continue
                left, right = ids[0], ids[1]
            if not (_is_ref(str(left)) and _is_ref(str(right))):
                continue
            found.append({"left": str(left), "right": str(right), "disposition": mapped})
    return found


def identity_from_dispositions(path: Path) -> list[dict[str, str]]:
    rows = load_dispositions(path)
    found: list[dict[str, str]] = []
    for row in rows:
        disp = str(row.get("disposition") or "").upper()
        mapped = IDENTITY_MAP.get(disp, disp)
        if mapped not in IDENTITY_DISPOSITIONS:
            continue
        values = row.get("values") if isinstance(row.get("values"), dict) else row
        left = values.get("left") if isinstance(values, dict) else None
        right = values.get("right") if isinstance(values, dict) else None
        if left and right and _is_ref(str(left)) and _is_ref(str(right)):
            found.append({"left": str(left), "right": str(right), "disposition": mapped})
            continue
        relation = str(row.get("relation") or "").lower()
        if "identity" not in relation and disp in {"ACCEPT", "REJECT"}:
            continue
        pair = pair_from_obj(row)
        if pair and _is_ref(pair[0]) and _is_ref(pair[1]):
            found.append({"left": pair[0], "right": pair[1], "disposition": mapped})
    return found
