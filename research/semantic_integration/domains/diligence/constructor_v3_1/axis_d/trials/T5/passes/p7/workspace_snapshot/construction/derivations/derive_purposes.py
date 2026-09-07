#!/usr/bin/env python3
"""Derive purpose IR outputs from compiled world relations.

Reads 06_world/world.sqlite (or world/world.sqlite) and writes:
  purpose_ir/a/output.json
  purpose_ir/b/output.json
  purpose_ir/c/output.json
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

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

CLASS_RANK = {"crm:": 0, "billing:": 1, "contract:": 2, "registry:": 3}


def find_world_db() -> Path:
    for candidate in (ROOT / "06_world" / "world.sqlite", ROOT / "world" / "world.sqlite"):
        if candidate.exists():
            return candidate
    raise FileNotFoundError("world.sqlite not found under 06_world/ or world/")


def class_rank(identifier: str) -> int:
    for prefix, rank in CLASS_RANK.items():
        if identifier.startswith(prefix):
            return rank
    return 4


def orient_pair(left: str, right: str) -> tuple[str, str]:
    rl, rr = class_rank(left), class_rank(right)
    if rl < rr or (rl == rr and left < right):
        return left, right
    return right, left


def strip_prefix(value: str, prefix: str) -> str:
    token = f"{prefix}:"
    return value[len(token) :] if value.startswith(token) else value


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def fetchall(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
    return list(conn.execute(sql, params))


def build_identity_index(rows: list[sqlite3.Row]) -> dict[tuple[str, str], str]:
    index: dict[tuple[str, str], str] = {}
    for row in rows:
        left, right = orient_pair(row["left"], row["right"])
        index[(left, right)] = row["disposition"]
    return index


def lookup_identity(index: dict[tuple[str, str], str], a: str, b: str) -> str | None:
    left, right = orient_pair(a, b)
    return index.get((left, right))


def derive_open_invoices(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return fetchall(
        conn,
        """
        SELECT invoice, invoice_id, status
        FROM invoice_record
        WHERE status = 'open'
        ORDER BY invoice_id
        """,
    )


def derive_purpose_a(conn: sqlite3.Connection, identity_index: dict[tuple[str, str], str]) -> dict[str, Any]:
    placeholders = ", ".join("?" for _ in ACQUISITION_KINDS)
    rows = fetchall(
        conn,
        f"""
        SELECT
            ir.invoice_id,
            ir.billed_name,
            ir.amount,
            ir.currency,
            ir.period,
            ir.status,
            cd.contract_id AS contract_ref
        FROM invoice_record ir
        JOIN invoice_governing_contract igc ON ir.invoice = igc.invoice_id
        JOIN contract_document cd ON igc.contract_id = cd.contract
        JOIN contract_lifecycle cl ON cd.contract = cl.contract_id
        JOIN clause_occurrence co ON cd.contract = co.contract_id
        WHERE cl.active = 1
          AND co.kind IN ({placeholders})
        ORDER BY ir.invoice_id
        """,
        tuple(ACQUISITION_KINDS),
    )

    invoices: list[dict[str, Any]] = []
    for row in rows:
        billing_id = f"billing:{row['billed_name']}"
        contract_id = f"contract:{row['contract_ref']}"
        disposition = lookup_identity(identity_index, billing_id, contract_id)
        if disposition == "SAME_ENTITY":
            association = "asserted"
        else:
            association = "unresolved"

        invoices.append(
            {
                "invoice_id": strip_prefix(row["invoice_id"], "invoice"),
                "billed_name": row["billed_name"],
                "amount": row["amount"],
                "currency": row["currency"],
                "period": row["period"],
                "status": row["status"],
                "contract_id": strip_prefix(row["contract_ref"], "contract"),
                "association": association,
            }
        )

    return {"purpose": "contractual_revenue_exposure", "invoices": invoices}


def derive_purpose_b(conn: sqlite3.Connection) -> dict[str, Any]:
    rows = fetchall(
        conn,
        "SELECT left, right, disposition FROM identity_judgment ORDER BY left, right",
    )
    links: list[dict[str, str]] = []
    for row in rows:
        left, right = orient_pair(row["left"], row["right"])
        disposition = row["disposition"]
        if disposition == "REJECT":
            disposition = "DISTINCT"
        links.append({"left": left, "right": right, "epistemic": disposition})

    links.sort(key=lambda item: (item["left"], item["right"]))
    return {"purpose": "counterparty_reconciliation", "links": links}


def identity_blocks(index: dict[tuple[str, str], str], a: str, b: str) -> bool:
    disposition = lookup_identity(index, a, b)
    return disposition in (None, "UNRESOLVED")


def pick_counterparty(
    contract_ref: str,
    identity_rows: list[sqlite3.Row],
    index: dict[tuple[str, str], str],
) -> str:
    contract_id = f"contract:{contract_ref}"
    candidates: list[str] = []
    for row in identity_rows:
        for side in (row["left"], row["right"]):
            if side == contract_id:
                other = row["right"] if row["left"] == contract_id else row["left"]
                if row["disposition"] == "SAME_ENTITY" and other != contract_id:
                    candidates.append(other)
    if not candidates:
        return contract_id
    return min(candidates, key=lambda item: (class_rank(item), item))


def has_current_relationship(
    obligation_kinds: list[str],
    open_invoice_refs: set[str],
) -> bool:
    if open_invoice_refs:
        return True
    rolling_or_auto = {"auto_renewal", "rolling_term"}
    return bool(rolling_or_auto & set(obligation_kinds))


def derive_purpose_c(
    conn: sqlite3.Connection,
    identity_index: dict[tuple[str, str], str],
    identity_rows: list[sqlite3.Row],
) -> dict[str, Any]:
    placeholders = ", ".join("?" for _ in OBLIGATION_KINDS)
    contract_rows = fetchall(
        conn,
        f"""
        SELECT cd.contract_id AS contract_ref, co.kind
        FROM contract_document cd
        JOIN contract_lifecycle cl ON cd.contract = cl.contract_id
        JOIN clause_occurrence co ON cd.contract = co.contract_id
        WHERE cl.active = 1
          AND co.kind IN ({placeholders})
        ORDER BY cd.contract_id, co.kind
        """,
        tuple(OBLIGATION_KINDS),
    )

    open_rows = derive_open_invoices(conn)
    open_by_contract: dict[str, list[str]] = {}
    for row in fetchall(
        conn,
        """
        SELECT igc.contract_id AS contract_referent, ir.invoice_id
        FROM invoice_governing_contract igc
        JOIN invoice_record ir ON igc.invoice_id = ir.invoice
        WHERE ir.status = 'open'
        ORDER BY ir.invoice_id
        """,
    ):
        contract_ref = strip_prefix(row["contract_referent"], "contract")
        invoice_id = strip_prefix(row["invoice_id"], "invoice")
        open_by_contract.setdefault(contract_ref, []).append(invoice_id)

    grouped: dict[str, dict[str, Any]] = {}
    for row in contract_rows:
        contract_ref = row["contract_ref"]
        bucket = grouped.setdefault(
            contract_ref,
            {"obligation_kinds": set(), "open_invoice_ids": open_by_contract.get(contract_ref, [])},
        )
        bucket["obligation_kinds"].add(row["kind"])

    dependencies: list[dict[str, Any]] = []
    for contract_ref in sorted(grouped):
        info = grouped[contract_ref]
        obligation_kinds = sorted(info["obligation_kinds"])
        open_invoice_ids = sorted(info["open_invoice_ids"])
        if not has_current_relationship(obligation_kinds, set(open_invoice_ids)):
            continue

        counterparty = pick_counterparty(contract_ref, identity_rows, identity_index)
        contract_id = f"contract:{contract_ref}"
        status = "dependent"

        if identity_blocks(identity_index, counterparty, contract_id):
            status = "unresolved"
        else:
            for invoice_id in open_invoice_ids:
                billed_rows = fetchall(
                    conn,
                    "SELECT billed_name FROM invoice_record WHERE invoice_id = ?",
                    (f"invoice:{invoice_id}",),
                )
                if not billed_rows:
                    continue
                billing_id = f"billing:{billed_rows[0]['billed_name']}"
                if identity_blocks(identity_index, billing_id, contract_id):
                    status = "unresolved"
                    break

        dependencies.append(
            {
                "counterparty": counterparty,
                "contract_id": contract_ref,
                "open_invoice_ids": open_invoice_ids,
                "obligation_kinds": obligation_kinds,
                "status": status,
            }
        )

    return {"purpose": "commercial_dependency", "dependencies": dependencies}


def write_output(rel_path: str, payload: dict[str, Any]) -> Path:
    out_path = ROOT / rel_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return out_path


def main() -> None:
    db_path = find_world_db()
    conn = connect(db_path)
    try:
        identity_rows = fetchall(conn, "SELECT left, right, disposition FROM identity_judgment")
        identity_index = build_identity_index(identity_rows)

        purpose_a = derive_purpose_a(conn, identity_index)
        purpose_b = derive_purpose_b(conn)
        purpose_c = derive_purpose_c(conn, identity_index, identity_rows)

        write_output("purpose_ir/a/output.json", purpose_a)
        write_output("purpose_ir/b/output.json", purpose_b)
        write_output("purpose_ir/c/output.json", purpose_c)

        print(f"Read {db_path}")
        print(f"Wrote {len(purpose_a['invoices'])} purpose A invoices")
        print(f"Wrote {len(purpose_b['links'])} purpose B links")
        print(f"Wrote {len(purpose_c['dependencies'])} purpose C dependencies")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
