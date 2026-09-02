#!/usr/bin/env python3
"""Derive purpose IR outputs A/B/C from compiled world.sqlite relations.

Reads 06_world/world.sqlite (or world/world.sqlite) and writes:
  purpose_ir/a/output.json
  purpose_ir/b/output.json
  purpose_ir/c/output.json
"""

from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from pathlib import Path

VIEW_ID = "diligence-world"

ACQUISITION_TERM_KINDS = (
    "change_of_control_consent_required",
    "termination_on_change_of_control",
    "assignment_consent_or_notice_required",
    "assignment_affiliate_only",
    "assignment_competitor_prohibited",
)

OBLIGATION_KINDS = ("exclusivity", "auto_renewal", "rolling_term")
CONTINUING_TERM_KINDS = ("auto_renewal", "rolling_term")


def resolve_world_db(root: Path) -> Path:
    for candidate in (root / "06_world" / "world.sqlite", root / "world" / "world.sqlite"):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("world.sqlite not found under 06_world/ or world/")


def connect_world(path: Path) -> sqlite3.Connection:
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    view = db.execute("SELECT view_id FROM _tv_view WHERE singleton = 1").fetchone()
    if view is None or view["view_id"] != VIEW_ID:
        raise RuntimeError(f"{path} is not a {VIEW_ID!r} TaskView database")
    return db


def derive_purpose_a(db: sqlite3.Connection) -> dict:
    """Invoices tied to active contracts with acquisition-relevant PRESENT terms."""
    placeholders = ",".join("?" for _ in ACQUISITION_TERM_KINDS)
    acq_contracts = {
        row["contract_id"]
        for row in db.execute(
            f"""
            SELECT DISTINCT sc.contract_id
            FROM source_contract sc
            JOIN active_contract ac ON ac.contract_id = sc.contract
            JOIN contract_term_reading ctr ON ctr.contract = sc.contract
            WHERE ctr.term_kind IN ({placeholders})
              AND ctr.disposition = 'PRESENT'
            """,
            ACQUISITION_TERM_KINDS,
        )
    }

    invoices = []
    for row in db.execute(
        """
        SELECT
            si.invoice_id,
            si.billed_name,
            si.amount,
            si.currency,
            si.period,
            si.status,
            sc.contract_id,
            icl.disposition AS link_disposition
        FROM source_invoice si
        JOIN invoice_contract_link icl ON icl.invoice = si.invoice
        JOIN source_contract sc ON sc.contract = icl.contract
        WHERE icl.disposition IN ('LINKED', 'UNRESOLVED')
        ORDER BY si.invoice_id
        """
    ):
        if row["contract_id"] not in acq_contracts:
            continue
        invoices.append(
            {
                "invoice_id": row["invoice_id"],
                "billed_name": row["billed_name"],
                "amount": row["amount"],
                "currency": row["currency"],
                "period": row["period"],
                "status": row["status"],
                "contract_id": row["contract_id"],
                "association": (
                    "asserted"
                    if row["link_disposition"] == "LINKED"
                    else "unresolved"
                ),
            }
        )

    return {"purpose": "contractual_revenue_exposure", "invoices": invoices}


def derive_purpose_b(db: sqlite3.Connection) -> dict:
    """Required counterparty identity links with purpose epistemic labels."""
    allowed = {"SAME_ENTITY", "DISTINCT", "UNRESOLVED"}
    links = []
    for row in db.execute(
        """
        SELECT left, right, disposition
        FROM legal_entity_identity
        ORDER BY left ASC, right ASC
        """
    ):
        epistemic = row["disposition"]
        if epistemic not in allowed:
            epistemic = "UNRESOLVED"
        links.append(
            {"left": row["left"], "right": row["right"], "epistemic": epistemic}
        )
    return {"purpose": "counterparty_reconciliation", "links": links}


def _contract_obligation_readings(db: sqlite3.Connection) -> dict[str, dict[str, str]]:
    readings: dict[str, dict[str, str]] = defaultdict(dict)
    placeholders = ",".join("?" for _ in OBLIGATION_KINDS)
    for row in db.execute(
        f"""
        SELECT sc.contract_id, ctr.term_kind, ctr.disposition
        FROM contract_term_reading ctr
        JOIN source_contract sc ON ctr.contract = sc.contract
        WHERE ctr.term_kind IN ({placeholders})
        """,
        OBLIGATION_KINDS,
    ):
        readings[row["contract_id"]][row["term_kind"]] = row["disposition"]
    return readings


def _active_contract_ids(db: sqlite3.Connection) -> set[str]:
    return {
        row["contract_id"]
        for row in db.execute(
            """
            SELECT sc.contract_id
            FROM active_contract ac
            JOIN source_contract sc ON ac.contract_id = sc.contract
            """
        )
    }


def _open_invoices_by_contract(db: sqlite3.Connection) -> dict[str, list[tuple[str, str]]]:
    grouped: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for row in db.execute(
        """
        SELECT sc.contract_id, si.invoice_id, icl.disposition
        FROM invoice_open io
        JOIN source_invoice si ON io.invoice_id = si.invoice
        JOIN invoice_contract_link icl ON icl.invoice = si.invoice
        JOIN source_contract sc ON icl.contract = sc.contract
        WHERE io.is_open = 1
        """
    ):
        grouped[row["contract_id"]].append((row["invoice_id"], row["disposition"]))
    return grouped


def _billing_counterparty_by_contract(db: sqlite3.Connection) -> dict[str, str]:
    counterparty: dict[str, str] = {}
    for row in db.execute(
        """
        SELECT sc.contract_id, si.billed_name
        FROM invoice_contract_link icl
        JOIN source_invoice si ON icl.invoice = si.invoice
        JOIN source_contract sc ON icl.contract = sc.contract
        WHERE icl.disposition = 'LINKED'
        GROUP BY sc.contract_id
        """
    ):
        counterparty[row["contract_id"]] = f"billing:{row['billed_name']}"
    return counterparty


def _crm_counterparty_by_contract(db: sqlite3.Connection) -> dict[str, str]:
    counterparty: dict[str, str] = {}
    for row in db.execute(
        """
        SELECT sc.contract_id, lei.right AS crm_ref
        FROM source_contract sc
        JOIN legal_entity_identity lei
          ON lei.left = sc.contract AND lei.disposition = 'SAME_ENTITY'
        WHERE lei.right LIKE 'crm:%'
        """
    ):
        counterparty[row["contract_id"]] = row["crm_ref"]
    return counterparty


def derive_purpose_c(db: sqlite3.Connection) -> dict:
    """Commercial dependency rows under the conjunctive purpose definition."""
    active = _active_contract_ids(db)
    readings = _contract_obligation_readings(db)
    open_by_contract = _open_invoices_by_contract(db)
    billing_counterparty = _billing_counterparty_by_contract(db)
    crm_counterparty = _crm_counterparty_by_contract(db)

    dependencies = []
    for contract_id in sorted(readings):
        if contract_id not in active:
            continue

        term_map = readings[contract_id]
        present_kinds = sorted(
            kind for kind in OBLIGATION_KINDS if term_map.get(kind) == "PRESENT"
        )
        has_unresolved_kind = any(
            term_map.get(kind) == "UNRESOLVED" for kind in OBLIGATION_KINDS
        )
        has_continuing_contract = any(
            term_map.get(kind) == "PRESENT" for kind in CONTINUING_TERM_KINDS
        )

        open_rows = open_by_contract.get(contract_id, [])
        linked_open_ids = sorted(
            invoice_id for invoice_id, disposition in open_rows if disposition == "LINKED"
        )
        has_unresolved_open_link = any(
            disposition == "UNRESOLVED" for _, disposition in open_rows
        )

        current_relationship = bool(linked_open_ids) or has_continuing_contract
        qualifying_obligation = bool(present_kinds)

        # Candidate universe: plausibly meets conjuncts (PRESENT or UNRESOLVED obligation).
        if not (
            current_relationship or has_unresolved_open_link
        ) or not (qualifying_obligation or has_unresolved_kind):
            continue

        counterparty = billing_counterparty.get(contract_id) or crm_counterparty.get(
            contract_id
        )
        identity_confident = contract_id in billing_counterparty or (
            contract_id in crm_counterparty
            and not has_unresolved_open_link
        )

        if (
            current_relationship
            and qualifying_obligation
            and identity_confident
            and not has_unresolved_open_link
        ):
            status = "dependent"
        else:
            status = "unresolved"

        if counterparty is None:
            status = "unresolved"
            counterparty = f"contract:{contract_id}"

        dependencies.append(
            {
                "counterparty": counterparty,
                "contract_id": contract_id,
                "open_invoice_ids": linked_open_ids if status == "dependent" else [],
                "obligation_kinds": present_kinds if status == "dependent" else [],
                "status": status,
            }
        )

    return {"purpose": "commercial_dependency", "dependencies": dependencies}


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    db_path = resolve_world_db(root)
    db = connect_world(db_path)
    try:
        write_json(root / "purpose_ir" / "a" / "output.json", derive_purpose_a(db))
        write_json(root / "purpose_ir" / "b" / "output.json", derive_purpose_b(db))
        write_json(root / "purpose_ir" / "c" / "output.json", derive_purpose_c(db))
    finally:
        db.close()
    print(f"Derived purpose outputs from {db_path}")


if __name__ == "__main__":
    main()
