#!/usr/bin/env python3
"""Derive purpose A/B/C outputs from compiled world relations.

Reads 06_world/world.sqlite (or world/world.sqlite) and writes
purpose_ir/{a,b,c}/output.json per contracts/purpose_*.json schemas.
"""

from __future__ import annotations

import json
import re
import sqlite3
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVAL_AS_OF = date(2026, 9, 2)

PURPOSE_A_ALLOWED_CLAUSES = {
    "change_of_control_consent",
    "change_of_control_termination",
    "assignment_notice_or_consent",
    "assignment_consent",
    "assignment_notice",
    "assignment_competitor_prohibition",
    "competitor_assignment_prohibition",
}

PURPOSE_C_OBLIGATION_KINDS = {"exclusivity", "auto_renewal", "rolling_term"}

CRM_CONTRACT_PAIRS = [
    ("crm:HEL-441", "contract:MSA-HELION-2019"),
    ("crm:NBA-102", "contract:MSA-NBA-2021"),
    ("crm:OAK-77", "contract:MSA-OAK-2018"),
    ("crm:VEL-19", "contract:SOW-VEL-2022"),
    ("crm:MER-55", "contract:MSA-MER-2024"),
]

BILLING_CONTRACT_PAIRS = [
    ("billing:Helion Robotics Limited", "contract:MSA-HELION-2019"),
    ("billing:Northbridge Analytics Inc.", "contract:MSA-NBA-2021"),
    ("billing:Oakfield Logistik GmbH", "contract:MSA-OAK-2018"),
    ("billing:Vellum Print Co Ltd", "contract:SOW-VEL-2022"),
    ("billing:Meridian Energy Partners LLC", "contract:MSA-MER-2024"),
]


def resolve_world_path() -> Path:
    for candidate in (ROOT / "06_world" / "world.sqlite", ROOT / "world" / "world.sqlite"):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("world.sqlite not found under 06_world/ or world/")


def strip_contract_prefix(identifier: str) -> str:
    return identifier.removeprefix("contract:")


def strip_invoice_prefix(identifier: str) -> str:
    return identifier.removeprefix("invoice:")


def parse_expiry_date(text: str) -> date | None:
    match = re.search(r"(\d{1,2})\s+(\w+)\s+(\d{4})", text)
    if not match:
        return None
    day, month_name, year = match.groups()
    months = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
    }
    month = months.get(month_name.lower())
    if month is None:
        return None
    return date(int(year), month, int(day))


def load_rows(conn: sqlite3.Connection, relation: str) -> list[sqlite3.Row]:
    conn.row_factory = sqlite3.Row
    return list(conn.execute(f'SELECT * FROM "{relation}"'))


def identity_lookup(
    judgments: dict[tuple[str, str], str], left: str, right: str
) -> str | None:
    if left == right:
        return "SAME_ENTITY"
    key = (left, right) if left < right else (right, left)
    return judgments.get(key)


def contract_active_status(
    contract_id: str,
    doc_type: str | None,
    expiry_date: str | None,
    term_text: str | None,
    clause_kinds: set[str],
) -> str:
    if expiry_date:
        parsed = parse_expiry_date(expiry_date)
        if parsed is not None and parsed < EVAL_AS_OF:
            return "INACTIVE"

    if doc_type == "SOW" and expiry_date:
        return "INACTIVE"

    renewal_signals = clause_kinds & {"auto_renewal", "rolling_term"}
    term_lower = (term_text or "").lower()
    if renewal_signals:
        return "ACTIVE"
    if "month-to-month" in term_lower:
        return "ACTIVE"
    if "successive" in term_lower and "period" in term_lower:
        return "ACTIVE"
    if "rolling" in term_lower:
        return "ACTIVE"

    return "UNRESOLVED"


def build_world_state(conn: sqlite3.Connection) -> dict:
    judgments: dict[tuple[str, str], str] = {}
    for row in load_rows(conn, "identity_judgment"):
        left, right = row["left"], row["right"]
        key = (left, right) if left < right else (right, left)
        judgments[key] = row["disposition"]

    clauses_by_contract: dict[str, set[str]] = {}
    for row in load_rows(conn, "observed_clause"):
        clauses_by_contract.setdefault(row["contract_id"], set()).add(row["clause_kind"])

    doc_type = {row["contract_id"]: row["doc_type"] for row in load_rows(conn, "contract_doc_type")}
    expiry = {
        row["contract_id"]: row["expiry_date"]
        for row in load_rows(conn, "contract_expiry_date")
    }
    term_text = {
        row["contract_id"]: row["term_text"]
        for row in load_rows(conn, "contract_term_text")
    }

    contract_active: dict[str, str] = {}
    for contract_id in doc_type:
        contract_active[contract_id] = contract_active_status(
            contract_id,
            doc_type.get(contract_id),
            expiry.get(contract_id),
            term_text.get(contract_id),
            clauses_by_contract.get(contract_id, set()),
        )

    acquisition_relevant = {
        contract_id
        for contract_id, status in contract_active.items()
        if status == "ACTIVE"
        and clauses_by_contract.get(contract_id, set()) & PURPOSE_A_ALLOWED_CLAUSES
    }

    invoices: dict[str, dict] = {}
    for row in load_rows(conn, "invoice_billed_name"):
        invoice_id = row["invoice_id"]
        invoices[invoice_id] = {"billed_name": row["billed_name"]}
    for relation, field in (
        ("invoice_amount", "amount"),
        ("invoice_currency", "currency"),
        ("invoice_period", "period"),
        ("invoice_status", "status"),
    ):
        for row in load_rows(conn, relation):
            invoices[row["invoice_id"]][field] = row[field]

    open_invoices = {row["invoice_id"] for row in load_rows(conn, "open_invoice")}

    billing_by_invoice = {
        invoice_id: f"billing:{data['billed_name']}"
        for invoice_id, data in invoices.items()
    }

    return {
        "judgments": judgments,
        "clauses_by_contract": clauses_by_contract,
        "contract_active": contract_active,
        "acquisition_relevant": acquisition_relevant,
        "invoices": invoices,
        "open_invoices": open_invoices,
        "billing_by_invoice": billing_by_invoice,
        "identity_link_candidates": [
            (row["left"], row["right"]) for row in load_rows(conn, "identity_link_candidate")
        ],
    }


def derive_purpose_a(state: dict) -> dict:
    rows = []
    for invoice_id in sorted(state["invoices"]):
        billing_id = state["billing_by_invoice"][invoice_id]
        invoice = state["invoices"][invoice_id]
        for billing_name, contract_id in BILLING_CONTRACT_PAIRS:
            if billing_name != billing_id:
                continue
            if contract_id not in state["acquisition_relevant"]:
                continue
            disposition = identity_lookup(state["judgments"], billing_id, contract_id)
            if disposition == "SAME_ENTITY":
                association = "asserted"
            elif disposition == "UNRESOLVED":
                association = "unresolved"
            else:
                continue
            rows.append(
                {
                    "invoice_id": strip_invoice_prefix(invoice_id),
                    "billed_name": invoice["billed_name"],
                    "amount": invoice["amount"],
                    "currency": invoice["currency"],
                    "period": invoice["period"],
                    "status": invoice["status"],
                    "contract_id": strip_contract_prefix(contract_id),
                    "association": association,
                }
            )
    return {"purpose": "contractual_revenue_exposure", "invoices": rows}


def derive_purpose_b(state: dict) -> dict:
    links = []
    for left, right in sorted(state["identity_link_candidates"]):
        disposition = identity_lookup(state["judgments"], left, right)
        if disposition is None:
            epistemic = "UNRESOLVED"
        elif disposition == "DISTINCT":
            epistemic = "DISTINCT"
        elif disposition == "SAME_ENTITY":
            epistemic = "SAME_ENTITY"
        else:
            epistemic = "UNRESOLVED"
        links.append({"left": left, "right": right, "epistemic": epistemic})
    return {"purpose": "counterparty_reconciliation", "links": links}


def open_invoices_for_contract(state: dict, contract_id: str) -> list[str]:
    billing_ids = {
        billing
        for billing, contract in BILLING_CONTRACT_PAIRS
        if contract == contract_id
    }
    return sorted(
        strip_invoice_prefix(invoice_id)
        for invoice_id, billing_id in state["billing_by_invoice"].items()
        if billing_id in billing_ids and invoice_id in state["open_invoices"]
    )


def derive_purpose_c(state: dict) -> dict:
    dependencies = []
    for crm_id, contract_id in CRM_CONTRACT_PAIRS:
        active = state["contract_active"].get(contract_id, "UNRESOLVED")
        obligation_kinds = sorted(
            state["clauses_by_contract"].get(contract_id, set()) & PURPOSE_C_OBLIGATION_KINDS
        )
        if active != "ACTIVE" or not obligation_kinds:
            continue

        billing_ids = {
            billing
            for billing, contract in BILLING_CONTRACT_PAIRS
            if contract == contract_id
        }
        billing_id = next(iter(billing_ids))
        billing_contract = identity_lookup(state["judgments"], billing_id, contract_id)
        billing_crm = identity_lookup(state["judgments"], billing_id, crm_id)
        if billing_contract == "SAME_ENTITY" and billing_crm == "SAME_ENTITY":
            status = "dependent"
        else:
            status = "unresolved"

        open_invoice_ids = open_invoices_for_contract(state, contract_id)
        current_relationship = bool(open_invoice_ids) or (
            active == "ACTIVE"
            and state["clauses_by_contract"].get(contract_id, set())
            & {"auto_renewal", "rolling_term"}
        )
        if not current_relationship:
            continue

        dependencies.append(
            {
                "counterparty": crm_id,
                "contract_id": strip_contract_prefix(contract_id),
                "open_invoice_ids": open_invoice_ids,
                "obligation_kinds": obligation_kinds,
                "status": status,
            }
        )

    dependencies.sort(key=lambda row: row["contract_id"])
    return {"purpose": "commercial_dependency", "dependencies": dependencies}


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    world_path = resolve_world_path()
    conn = sqlite3.connect(world_path)
    try:
        state = build_world_state(conn)
    finally:
        conn.close()

    write_json(ROOT / "purpose_ir" / "a" / "output.json", derive_purpose_a(state))
    write_json(ROOT / "purpose_ir" / "b" / "output.json", derive_purpose_b(state))
    write_json(ROOT / "purpose_ir" / "c" / "output.json", derive_purpose_c(state))


if __name__ == "__main__":
    main()
