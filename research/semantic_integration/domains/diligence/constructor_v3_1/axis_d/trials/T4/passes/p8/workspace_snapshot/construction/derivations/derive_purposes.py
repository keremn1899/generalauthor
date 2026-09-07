#!/usr/bin/env python3
"""Derive purpose IR outputs A/B/C from compiled world.sqlite (Pass P7)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VIEW_ID = "diligence-world"

PURPOSE_A_KINDS = (
    "change_of_control_consent",
    "change_of_control_termination",
    "assignment_notice_or_consent",
    "assignment_consent",
    "assignment_notice",
    "assignment_competitor_prohibition",
    "competitor_assignment_prohibition",
)

PURPOSE_C_KINDS = ("exclusivity", "auto_renewal", "rolling_term")

CLASS_RANK = {"billing": 0, "contract": 1, "crm": 2, "registry": 3}


def resolve_world_path() -> Path:
    for candidate in (ROOT / "06_world" / "world.sqlite", ROOT / "world" / "world.sqlite"):
        if candidate.exists():
            return candidate
    raise FileNotFoundError("world.sqlite not found under 06_world/ or world/")


def connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    view = conn.execute("SELECT view_id FROM _tv_view WHERE singleton = 1").fetchone()
    if view is None or view["view_id"] != VIEW_ID:
        raise ValueError(f"expected TaskView {VIEW_ID!r}, got {view and view['view_id']!r}")
    return conn


def strip_prefix(value: str, prefix: str) -> str:
    token = f"{prefix}:"
    return value[len(token) :] if value.startswith(token) else value


def orient_pair(left: str, right: str) -> tuple[str, str]:
    left_rank = CLASS_RANK.get(left.split(":", 1)[0], 99)
    right_rank = CLASS_RANK.get(right.split(":", 1)[0], 99)
    if left_rank <= right_rank:
        return left, right
    return right, left


def load_effective_identity(conn: sqlite3.Connection) -> dict[tuple[str, str], str]:
    """Merge required identity_judgment with optional mechanical_identity_allowance."""

    effective: dict[tuple[str, str], str] = {}

    for row in conn.execute(
        "SELECT left, right, disposition FROM identity_judgment ORDER BY left, right"
    ):
        left, right = orient_pair(row["left"], row["right"])
        effective[(left, right)] = row["disposition"]

    for row in conn.execute(
        "SELECT left, right, disposition FROM mechanical_identity_allowance "
        "WHERE disposition = 'SAME_ENTITY' ORDER BY left, right"
    ):
        left, right = orient_pair(row["left"], row["right"])
        key = (left, right)
        if key not in effective or effective[key] == "UNRESOLVED":
            effective[key] = "SAME_ENTITY"

    return effective


def identity_between(effective: dict[tuple[str, str], str], left: str, right: str) -> str | None:
    oriented = orient_pair(left, right)
    return effective.get(oriented)


def map_purpose_a_association(effective: dict[tuple[str, str], str], billed_name: str, contract_id: str) -> str:
    billing_id = f"billing:{billed_name}"
    contract_ref = f"contract:{contract_id}"
    disposition = identity_between(effective, billing_id, contract_ref)
    if disposition == "SAME_ENTITY":
        return "asserted"
    return "unresolved"


def derive_purpose_a(conn: sqlite3.Connection, effective: dict[tuple[str, str], str]) -> dict:
    placeholders = ",".join("?" for _ in PURPOSE_A_KINDS)
    rows = conn.execute(
        f"""
        SELECT DISTINCT
            ir.invoice_id,
            ir.billed_name,
            ir.amount,
            ir.currency,
            ir.period,
            ir.status,
            cr.contract_id
        FROM invoice_record ir
        JOIN governing_contract_link gcl ON gcl.invoice = ir.invoice
        JOIN contract_record cr ON cr.contract = gcl.contract
        JOIN contract_lifecycle cl ON cl.contract = gcl.contract AND cl.active = 1
        WHERE EXISTS (
            SELECT 1
            FROM clause_kind_present ckp
            WHERE ckp.contract = gcl.contract
              AND ckp.disposition = 'ACCEPT'
              AND ckp.clause_kind IN ({placeholders})
        )
        ORDER BY ir.invoice_id
        """,
        PURPOSE_A_KINDS,
    ).fetchall()

    invoices = []
    for row in rows:
        invoices.append(
            {
                "invoice_id": strip_prefix(row["invoice_id"], "invoice"),
                "billed_name": row["billed_name"],
                "amount": row["amount"],
                "currency": row["currency"],
                "period": row["period"],
                "status": row["status"],
                "contract_id": strip_prefix(row["contract_id"], "contract"),
                "association": map_purpose_a_association(
                    effective, row["billed_name"], row["contract_id"]
                ),
            }
        )

    return {"purpose": "contractual_revenue_exposure", "invoices": invoices}


def map_purpose_b_epistemic(disposition: str) -> str:
    mapping = {
        "SAME_ENTITY": "SAME_ENTITY",
        "DISTINCT": "DISTINCT",
        "UNRESOLVED": "UNRESOLVED",
        "REJECT": "DISTINCT",
    }
    return mapping.get(disposition, "UNRESOLVED")


def derive_purpose_b(conn: sqlite3.Connection, effective: dict[tuple[str, str], str]) -> dict:
    links = []
    for (left, right), disposition in sorted(effective.items()):
        links.append(
            {
                "left": left,
                "right": right,
                "epistemic": map_purpose_b_epistemic(disposition),
            }
        )
    return {"purpose": "counterparty_reconciliation", "links": links}


def contract_has_current_relationship(conn: sqlite3.Connection, contract: str) -> bool:
    open_row = conn.execute(
        """
        SELECT 1
        FROM open_invoice oi
        JOIN governing_contract_link gcl ON gcl.invoice = oi.invoice_id
        WHERE gcl.contract = ?
        LIMIT 1
        """,
        (contract,),
    ).fetchone()
    if open_row is not None:
        return True

    term_row = conn.execute(
        """
        SELECT 1
        FROM clause_kind_present ckp
        WHERE ckp.contract = ?
          AND ckp.disposition = 'ACCEPT'
          AND ckp.clause_kind IN ('auto_renewal', 'rolling_term')
        LIMIT 1
        """,
        (contract,),
    ).fetchone()
    return term_row is not None


def obligation_kinds_for_contract(conn: sqlite3.Connection, contract: str) -> list[str]:
    placeholders = ",".join("?" for _ in PURPOSE_C_KINDS)
    rows = conn.execute(
        f"""
        SELECT clause_kind
        FROM clause_kind_present
        WHERE contract = ?
          AND disposition = 'ACCEPT'
          AND clause_kind IN ({placeholders})
        ORDER BY clause_kind
        """,
        (contract, *PURPOSE_C_KINDS),
    ).fetchall()
    return [row["clause_kind"] for row in rows]


def dependency_status(
    conn: sqlite3.Connection,
    effective: dict[tuple[str, str], str],
    contract: str,
    contract_id: str,
    counterparty: str,
) -> str:
    billing_id = None
    billed_rows = conn.execute(
        """
        SELECT DISTINCT ir.billed_name
        FROM invoice_record ir
        JOIN governing_contract_link gcl ON gcl.invoice = ir.invoice
        WHERE gcl.contract = ?
        """,
        (contract,),
    ).fetchall()
    if billed_rows:
        billing_id = f"billing:{billed_rows[0]['billed_name']}"
    else:
        billing_id = f"billing:{counterparty.rstrip('.')}"

    contract_ref = f"contract:{contract_id}"
    billing_to_contract = identity_between(effective, billing_id, contract_ref)
    if billing_to_contract != "SAME_ENTITY":
        return "unresolved"

    for row in conn.execute(
        """
        SELECT ir.billed_name
        FROM open_invoice oi
        JOIN invoice_record ir ON ir.invoice = oi.invoice_id
        JOIN governing_contract_link gcl ON gcl.invoice = oi.invoice_id
        WHERE gcl.contract = ?
        """,
        (contract,),
    ):
        invoice_billing = f"billing:{row['billed_name']}"
        if identity_between(effective, invoice_billing, billing_id) not in (None, "SAME_ENTITY"):
            if identity_between(effective, invoice_billing, billing_id) == "DISTINCT":
                return "unresolved"
        if identity_between(effective, invoice_billing, contract_ref) != "SAME_ENTITY":
            return "unresolved"

    return "dependent"


def open_invoice_ids_for_contract(conn: sqlite3.Connection, contract: str) -> list[str]:
    rows = conn.execute(
        """
        SELECT ir.invoice_id
        FROM open_invoice oi
        JOIN invoice_record ir ON ir.invoice = oi.invoice_id
        JOIN governing_contract_link gcl ON gcl.invoice = oi.invoice_id
        WHERE gcl.contract = ?
        ORDER BY ir.invoice_id
        """,
        (contract,),
    ).fetchall()
    return [strip_prefix(row["invoice_id"], "invoice") for row in rows]


def derive_purpose_c(conn: sqlite3.Connection, effective: dict[tuple[str, str], str]) -> dict:
    placeholders = ",".join("?" for _ in PURPOSE_C_KINDS)
    contracts = conn.execute(
        f"""
        SELECT DISTINCT cr.contract, cr.contract_id, cr.counterparty
        FROM contract_record cr
        JOIN contract_lifecycle cl ON cl.contract = cr.contract AND cl.active = 1
        WHERE EXISTS (
            SELECT 1
            FROM clause_kind_present ckp
            WHERE ckp.contract = cr.contract
              AND ckp.disposition = 'ACCEPT'
              AND ckp.clause_kind IN ({placeholders})
        )
        ORDER BY cr.contract_id
        """,
        PURPOSE_C_KINDS,
    ).fetchall()

    dependencies = []
    for row in contracts:
        contract = row["contract"]
        if not contract_has_current_relationship(conn, contract):
            continue

        obligation_kinds = obligation_kinds_for_contract(conn, contract)
        if not obligation_kinds:
            continue

        billed_rows = conn.execute(
            """
            SELECT DISTINCT ir.billed_name
            FROM invoice_record ir
            JOIN governing_contract_link gcl ON gcl.invoice = ir.invoice
            WHERE gcl.contract = ?
            ORDER BY ir.billed_name
            LIMIT 1
            """,
            (contract,),
        ).fetchall()
        counterparty = (
            f"billing:{billed_rows[0]['billed_name']}"
            if billed_rows
            else f"contract:{row['contract_id']}"
        )

        dependencies.append(
            {
                "counterparty": counterparty,
                "contract_id": strip_prefix(row["contract_id"], "contract"),
                "open_invoice_ids": open_invoice_ids_for_contract(conn, contract),
                "obligation_kinds": obligation_kinds,
                "status": dependency_status(
                    conn,
                    effective,
                    contract,
                    row["contract_id"],
                    row["counterparty"],
                ),
            }
        )

    return {"purpose": "commercial_dependency", "dependencies": dependencies}


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def main() -> None:
    world_path = resolve_world_path()
    conn = connect(world_path)
    try:
        effective = load_effective_identity(conn)
        write_json(ROOT / "purpose_ir" / "a" / "output.json", derive_purpose_a(conn, effective))
        write_json(ROOT / "purpose_ir" / "b" / "output.json", derive_purpose_b(conn, effective))
        write_json(ROOT / "purpose_ir" / "c" / "output.json", derive_purpose_c(conn, effective))
    finally:
        conn.close()


if __name__ == "__main__":
    main()
