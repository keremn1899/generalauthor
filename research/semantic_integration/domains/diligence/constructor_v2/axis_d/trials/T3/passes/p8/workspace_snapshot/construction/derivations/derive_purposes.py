#!/usr/bin/env python3
"""Compile purpose IR artifacts A/B/C from world.sqlite."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = ROOT / "contracts"

ACQUISITION_KINDS = [
    "change_of_control_consent",
    "change_of_control_termination",
    "assignment_notice_or_consent",
    "assignment_consent",
    "assignment_notice",
    "assignment_competitor_prohibition",
    "competitor_assignment_prohibition",
]

OBLIGATION_KINDS = ["exclusivity", "auto_renewal", "rolling_term"]


def resolve_world_db() -> Path:
    for candidate in (ROOT / "06_world" / "world.sqlite", ROOT / "world" / "world.sqlite"):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("world.sqlite not found under 06_world/ or world/")


def load_purpose_contract(purpose_id: str) -> dict:
    path = CONTRACTS / f"purpose_{purpose_id.lower()}.json"
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def map_disposition(disposition: str | None, mapping: dict[str, str], default: str) -> str:
    if disposition is None:
        return default
    return mapping.get(disposition, default)


def identity_lookup(conn: sqlite3.Connection) -> dict[tuple[str, str], str]:
    rows = conn.execute(
        "SELECT left, right, disposition FROM identity_judgment"
    ).fetchall()
    lookup: dict[tuple[str, str], str] = {}
    for left, right, disposition in rows:
        lookup[(left, right)] = disposition
        lookup[(right, left)] = disposition
    return lookup


def clause_present_by_contract(
    conn: sqlite3.Connection, kinds: list[str]
) -> dict[str, set[str]]:
    placeholders = ",".join("?" for _ in kinds)
    rows = conn.execute(
        f"""
        SELECT cr.contract_id, cpj.clause_kind
        FROM clause_presence_judgment cpj
        JOIN contract_record cr ON cpj.contract_id = cr.contract
        WHERE cpj.disposition = 'PRESENT'
          AND cpj.clause_kind IN ({placeholders})
        """,
        kinds,
    ).fetchall()
    result: dict[str, set[str]] = {}
    for contract_id, clause_kind in rows:
        result.setdefault(contract_id, set()).add(clause_kind)
    return result


def derive_purpose_a(conn: sqlite3.Connection, contract: dict) -> dict:
    identity = identity_lookup(conn)
    acquisition = clause_present_by_contract(conn, ACQUISITION_KINDS)
    expired = {
        row[0]
        for row in conn.execute(
            """
            SELECT cr.contract_id
            FROM contract_is_expired cie
            JOIN contract_record cr ON cie.contract_id = cr.contract
            WHERE cie.is_expired = 1
            """
        )
    }
    mapping = contract["disposition_mapping"]
    invoices: list[dict] = []
    rows = conn.execute(
        """
        SELECT ir.invoice_id,
               ir.billed_name,
               ir.amount,
               ir.currency,
               ir.period,
               ir.status,
               cr.contract_id
        FROM invoice_contract_link_candidate iclc
        JOIN invoice_record ir ON iclc.invoice_id = ir.invoice
        JOIN contract_record cr ON iclc.contract_id = cr.contract
        ORDER BY ir.invoice_id
        """
    ).fetchall()
    for invoice_id, billed_name, amount, currency, period, status, contract_id in rows:
        if contract_id in expired:
            continue
        if contract_id not in acquisition:
            continue
        billing_id = f"billing:{billed_name}"
        contract_ref = f"contract:{contract_id}"
        disposition = identity.get((billing_id, contract_ref))
        association = map_disposition(disposition, mapping, "unresolved")
        invoices.append(
            {
                "invoice_id": invoice_id,
                "billed_name": billed_name,
                "amount": amount,
                "currency": currency,
                "period": period,
                "status": status,
                "contract_id": contract_id,
                "association": association,
            }
        )
    invoices.sort(key=lambda row: row["invoice_id"])
    return {"purpose": "contractual_revenue_exposure", "invoices": invoices}


def derive_purpose_b(conn: sqlite3.Connection, contract: dict) -> dict:
    mapping = contract["disposition_mapping"]
    links: list[dict] = []
    rows = conn.execute(
        """
        SELECT ijc.left,
               ijc.right,
               ij.disposition
        FROM identity_judgment_candidate ijc
        LEFT JOIN identity_judgment ij
          ON ijc.left = ij.left AND ijc.right = ij.right
        ORDER BY ijc.left, ijc.right
        """
    ).fetchall()
    for left, right, disposition in rows:
        epistemic = map_disposition(disposition, mapping, "UNRESOLVED")
        links.append({"left": left, "right": right, "epistemic": epistemic})
    return {"purpose": "counterparty_reconciliation", "links": links}


def open_invoices_for_contract(
    conn: sqlite3.Connection, contract_id: str, billed_name: str | None
) -> list[str]:
    rows = conn.execute(
        """
        SELECT DISTINCT ir.invoice_id
        FROM invoice_contract_link_candidate iclc
        JOIN invoice_record ir ON iclc.invoice_id = ir.invoice
        JOIN contract_record cr ON iclc.contract_id = cr.contract
        JOIN invoice_is_open iio ON ir.invoice = iio.invoice_id
        WHERE cr.contract_id = ?
          AND iio.is_open = 1
        ORDER BY ir.invoice_id
        """,
        (contract_id,),
    ).fetchall()
    invoice_ids = [row[0] for row in rows]
    if invoice_ids or billed_name is None:
        return invoice_ids
    rows = conn.execute(
        """
        SELECT ir.invoice_id
        FROM invoice_record ir
        JOIN invoice_is_open iio ON ir.invoice = iio.invoice_id
        WHERE ir.billed_name = ?
          AND iio.is_open = 1
        ORDER BY ir.invoice_id
        """,
        (billed_name,),
    ).fetchall()
    return [row[0] for row in rows]


def billing_thread_for_contract(
    conn: sqlite3.Connection, contract_id: str
) -> str | None:
    """Return billed_name when a mechanical invoice-contract candidate exists."""
    row = conn.execute(
        """
        SELECT ir.billed_name
        FROM invoice_contract_link_candidate iclc
        JOIN invoice_record ir ON iclc.invoice_id = ir.invoice
        JOIN contract_record cr ON iclc.contract_id = cr.contract
        WHERE cr.contract_id = ?
        ORDER BY ir.invoice_id
        LIMIT 1
        """,
        (contract_id,),
    ).fetchone()
    return row[0] if row else None


def has_current_relationship(
    conn: sqlite3.Connection,
    contract_id: str,
    obligation_kinds: set[str],
    open_invoice_ids: list[str],
    is_expired: bool,
) -> bool:
    if open_invoice_ids:
        return True
    if is_expired:
        return False
    return bool(obligation_kinds & {"auto_renewal", "rolling_term"})


def derive_purpose_c(conn: sqlite3.Connection, contract: dict) -> dict:
    identity = identity_lookup(conn)
    obligations = clause_present_by_contract(conn, OBLIGATION_KINDS)
    expired = {
        row[0]
        for row in conn.execute(
            """
            SELECT cr.contract_id
            FROM contract_is_expired cie
            JOIN contract_record cr ON cie.contract_id = cr.contract
            WHERE cie.is_expired = 1
            """
        )
    }
    dependencies: list[dict] = []
    for contract_id in sorted(obligations):
        if contract_id in expired:
            continue
        kinds = sorted(obligations[contract_id] & set(OBLIGATION_KINDS))
        if not kinds:
            continue
        billed_name = billing_thread_for_contract(conn, contract_id)
        if billed_name is not None:
            counterparty = f"billing:{billed_name}"
            billing_id = counterparty
        else:
            counterparty = f"contract:{contract_id}"
            billing_id = None
        open_invoice_ids = open_invoices_for_contract(conn, contract_id, billed_name)
        contract_ref = f"contract:{contract_id}"
        identity_disposition = (
            identity.get((billing_id, contract_ref)) if billing_id is not None else None
        )
        current = has_current_relationship(
            conn, contract_id, set(kinds), open_invoice_ids, contract_id in expired
        )
        if (
            current
            and identity_disposition == "SAME_ENTITY"
            and kinds
        ):
            status = "dependent"
        else:
            status = "unresolved"
        dependencies.append(
            {
                "counterparty": counterparty,
                "contract_id": contract_id,
                "open_invoice_ids": open_invoice_ids,
                "obligation_kinds": kinds,
                "status": status,
            }
        )
    dependencies.sort(key=lambda row: row["contract_id"])
    return {"purpose": "commercial_dependency", "dependencies": dependencies}


def write_output(relative_path: str, payload: dict) -> None:
    out_path = ROOT / relative_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def main() -> None:
    db_path = resolve_world_db()
    conn = sqlite3.connect(db_path)
    try:
        purpose_a = derive_purpose_a(conn, load_purpose_contract("a"))
        purpose_b = derive_purpose_b(conn, load_purpose_contract("b"))
        purpose_c = derive_purpose_c(conn, load_purpose_contract("c"))
    finally:
        conn.close()
    write_output("purpose_ir/a/output.json", purpose_a)
    write_output("purpose_ir/b/output.json", purpose_b)
    write_output("purpose_ir/c/output.json", purpose_c)


if __name__ == "__main__":
    main()
