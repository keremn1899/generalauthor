#!/usr/bin/env python3
"""Purpose derivations over the certified World (P7)."""

from __future__ import annotations

import json
from pathlib import Path

from taskview import TaskView

ROOT = Path(__file__).resolve().parents[2]
WORLD_PATH = ROOT / "world" / "world.sqlite"
VIEW_ID = "diligence-world"

ACQUISITION_RELEVANT_CLAUSES = (
    "change_of_control_consent",
    "change_of_control_termination",
    "assignment_notice_or_consent",
    "competitor_assignment_prohibition",
)

OBLIGATION_KINDS = ("exclusivity", "auto_renewal", "rolling_term")
CONTINUING_CLAUSES = ("auto_renewal", "rolling_term")


def billing_id(billed_name: str) -> str:
    return f"billing:{billed_name}"


def parse_contract_ref(identifier: str) -> str | None:
    if identifier.startswith("contract:"):
        return identifier[len("contract:") :]
    return None


def derive_purpose_a(tv: TaskView) -> dict:
    clause_placeholders = ", ".join("?" for _ in ACQUISITION_RELEVANT_CLAUSES)
    rows = tv.query_semantic(
        f"""
        WITH acquisition_contracts AS (
            SELECT DISTINCT cc.contract_id
            FROM contract_clause_kind cc
            JOIN contract_active ca
              ON ca.contract_id = cc.contract_id
             AND ca.active = 1
            WHERE cc.clause_kind IN ({clause_placeholders})
        )
        SELECT
            i.invoice_id,
            i.billed_name,
            i.amount,
            i.currency,
            i.period,
            i.status,
            CASE
                WHEN ij.left LIKE 'contract:%' THEN substr(ij.left, 10)
                ELSE substr(ij.right, 10)
            END AS contract_id,
            ij.disposition
        FROM invoice_record i
        JOIN identity_judgment ij
          ON (
            (ij.left = 'billing:' || i.billed_name AND ij.right LIKE 'contract:%')
            OR (ij.right = 'billing:' || i.billed_name AND ij.left LIKE 'contract:%')
          )
        JOIN acquisition_contracts ac
          ON ac.contract_id = CASE
              WHEN ij.left LIKE 'contract:%' THEN substr(ij.left, 10)
              ELSE substr(ij.right, 10)
          END
        ORDER BY i.invoice_id
        """,
        ACQUISITION_RELEVANT_CLAUSES,
    )

    invoices = []
    for row in rows:
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
                    if row["disposition"] == "SAME_ENTITY"
                    else "unresolved"
                ),
            }
        )

    return {"purpose": "contractual_revenue_exposure", "invoices": invoices}


def derive_purpose_b(tv: TaskView) -> dict:
    rows = tv.query_semantic(
        """
        SELECT left, right, disposition
        FROM identity_judgment
        ORDER BY left, right
        """
    )
    links = [
        {
            "left": row["left"],
            "right": row["right"],
            "epistemic": row["disposition"],
        }
        for row in rows
    ]
    return {"purpose": "counterparty_reconciliation", "links": links}


def derive_purpose_c(tv: TaskView) -> dict:
    active_rows = tv.query_semantic(
        "SELECT contract_id FROM contract_active WHERE active = 1"
    )
    active_contracts = {row["contract_id"] for row in active_rows}

    clause_rows = tv.query_semantic(
        f"""
        SELECT contract_id, clause_kind
        FROM contract_clause_kind
        WHERE clause_kind IN ({", ".join("?" for _ in OBLIGATION_KINDS)})
        """,
        OBLIGATION_KINDS,
    )
    clauses_by_contract: dict[str, set[str]] = {}
    for row in clause_rows:
        clauses_by_contract.setdefault(row["contract_id"], set()).add(row["clause_kind"])

    invoice_rows = tv.query_semantic(
        "SELECT invoice_id, billed_name, status FROM invoice_record"
    )
    open_by_billing: dict[str, list[str]] = {}
    for row in invoice_rows:
        if row["status"] == "open":
            open_by_billing.setdefault(billing_id(row["billed_name"]), []).append(
                row["invoice_id"]
            )

    link_rows = tv.query_semantic(
        """
        SELECT left, right, disposition
        FROM identity_judgment
        WHERE (left LIKE 'billing:%' AND right LIKE 'contract:%')
           OR (right LIKE 'billing:%' AND left LIKE 'contract:%')
        """
    )

    dependencies = []
    for row in link_rows:
        if row["left"].startswith("billing:"):
            billing = row["left"]
            contract_id = parse_contract_ref(row["right"])
        else:
            billing = row["right"]
            contract_id = parse_contract_ref(row["left"])
        if contract_id is None:
            continue

        obligation_kinds = sorted(
            kind
            for kind in clauses_by_contract.get(contract_id, set())
            if kind in OBLIGATION_KINDS
        )
        if not obligation_kinds or contract_id not in active_contracts:
            continue

        has_open_invoice = bool(open_by_billing.get(billing))
        has_continuing_term = bool(
            clauses_by_contract.get(contract_id, set()) & set(CONTINUING_CLAUSES)
        )
        current_relationship = has_open_invoice or has_continuing_term
        if not current_relationship:
            continue

        status = (
            "dependent"
            if row["disposition"] == "SAME_ENTITY"
            else "unresolved"
        )
        dependencies.append(
            {
                "counterparty": billing,
                "contract_id": contract_id,
                "open_invoice_ids": sorted(open_by_billing.get(billing, [])),
                "obligation_kinds": obligation_kinds,
                "status": status,
            }
        )

    dependencies.sort(key=lambda item: item["contract_id"])
    return {"purpose": "commercial_dependency", "dependencies": dependencies}


def write_outputs(name: str, payload: dict) -> None:
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    for relative in (f"08_outputs/{name}.json", f"purpose_ir/{name}/output.json"):
        path = ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def main() -> None:
    with TaskView(WORLD_PATH, view_id=VIEW_ID) as tv:
        write_outputs("a", derive_purpose_a(tv))
        write_outputs("b", derive_purpose_b(tv))
        write_outputs("c", derive_purpose_c(tv))


if __name__ == "__main__":
    main()
