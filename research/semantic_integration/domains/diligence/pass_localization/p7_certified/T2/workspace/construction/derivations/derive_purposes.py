#!/usr/bin/env python3
"""P7 purpose derivations over the certified diligence-world TaskView."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from taskview import TaskView

ROOT = Path(__file__).resolve().parents[2]
DERIVATIONS_PATH = ROOT / "07_derivations.json"

ACQUISITION_CLAUSE_KINDS = (
    "change_of_control_consent",
    "change_of_control_termination",
    "assignment_notice_or_consent",
    "competitor_assignment_prohibition",
)

OBLIGATION_CLAUSE_KINDS = ("exclusivity", "auto_renewal", "rolling_term")
CONTINUING_CLAUSE_KINDS = ("auto_renewal", "rolling_term")


def _association(disposition: str) -> str:
    return "asserted" if disposition == "SAME_ENTITY" else "unresolved"


def derive_purpose_a(tv: TaskView) -> dict[str, Any]:
    clause_list = ", ".join(f"'{kind}'" for kind in ACQUISITION_CLAUSE_KINDS)
    rows = tv.query_semantic(
        f"""
        SELECT DISTINCT
          i.invoice_id,
          i.billed_name,
          i.amount,
          i.currency,
          i.period,
          i.status,
          ca.contract_id,
          ij.disposition
        FROM invoice_record i
        JOIN identity_judgment ij
          ON ij.left = 'billing:' || i.billed_name
          AND ij.right LIKE 'contract:%'
        JOIN contract_active ca
          ON ca.contract_id = replace(ij.right, 'contract:', '')
          AND ca.active = 1
        WHERE EXISTS (
          SELECT 1
          FROM contract_clause_kind cck
          WHERE cck.contract_id = ca.contract_id
            AND cck.clause_kind IN ({clause_list})
        )
        ORDER BY i.invoice_id
        """
    )
    invoices = [
        {
            "invoice_id": row["invoice_id"],
            "billed_name": row["billed_name"],
            "amount": row["amount"],
            "currency": row["currency"],
            "period": row["period"],
            "status": row["status"],
            "contract_id": row["contract_id"],
            "association": _association(row["disposition"]),
        }
        for row in rows
    ]
    return {"purpose": "contractual_revenue_exposure", "invoices": invoices}


def derive_purpose_b(tv: TaskView) -> dict[str, Any]:
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


def derive_purpose_c(tv: TaskView) -> dict[str, Any]:
    obligation_list = ", ".join(f"'{kind}'" for kind in OBLIGATION_CLAUSE_KINDS)
    continuing_list = ", ".join(f"'{kind}'" for kind in CONTINUING_CLAUSE_KINDS)
    candidates = tv.query_semantic(
        f"""
        WITH billing_contract AS (
          SELECT
            ij.left AS counterparty,
            replace(ij.right, 'contract:', '') AS contract_id,
            ij.disposition
          FROM identity_judgment ij
          WHERE ij.left LIKE 'billing:%'
            AND ij.right LIKE 'contract:%'
        ),
        open_invoices AS (
          SELECT invoice_id, 'billing:' || billed_name AS counterparty
          FROM invoice_record
          WHERE status = 'open'
        )
        SELECT DISTINCT
          bc.counterparty,
          bc.contract_id,
          bc.disposition
        FROM billing_contract bc
        JOIN contract_active ca
          ON ca.contract_id = bc.contract_id
          AND ca.active = 1
        WHERE EXISTS (
          SELECT 1
          FROM contract_clause_kind cck
          WHERE cck.contract_id = bc.contract_id
            AND cck.clause_kind IN ({obligation_list})
        )
          AND (
            EXISTS (
              SELECT 1
              FROM open_invoices oi
              WHERE oi.counterparty = bc.counterparty
            )
            OR EXISTS (
              SELECT 1
              FROM contract_clause_kind cck
              WHERE cck.contract_id = bc.contract_id
                AND cck.clause_kind IN ({continuing_list})
            )
          )
        ORDER BY bc.contract_id
        """
    )

    dependencies: list[dict[str, Any]] = []
    for row in candidates:
        obligations = tv.query_semantic(
            f"""
            SELECT clause_kind
            FROM contract_clause_kind
            WHERE contract_id = ?
              AND clause_kind IN ({obligation_list})
            ORDER BY clause_kind
            """,
            (row["contract_id"],),
        )
        open_invoice_rows = tv.query_semantic(
            """
            SELECT invoice_id
            FROM invoice_record
            WHERE status = 'open'
              AND 'billing:' || billed_name = ?
            ORDER BY invoice_id
            """,
            (row["counterparty"],),
        )
        dependencies.append(
            {
                "counterparty": row["counterparty"],
                "contract_id": row["contract_id"],
                "open_invoice_ids": [
                    invoice["invoice_id"] for invoice in open_invoice_rows
                ],
                "obligation_kinds": [item["clause_kind"] for item in obligations],
                "status": (
                    "dependent"
                    if row["disposition"] == "SAME_ENTITY"
                    else "unresolved"
                ),
            }
        )
    return {"purpose": "commercial_dependency", "dependencies": dependencies}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    spec = json.loads(DERIVATIONS_PATH.read_text(encoding="utf-8"))
    world_path = ROOT / spec["world"]
    tv = TaskView(world_path, view_id=spec["view_id"])
    try:
        outputs = {
            "a": derive_purpose_a(tv),
            "b": derive_purpose_b(tv),
            "c": derive_purpose_c(tv),
        }
        for key, payload in outputs.items():
            purpose_paths = spec["purposes"][key]["outputs"]
            write_json(ROOT / purpose_paths["purpose_ir"], payload)
            write_json(ROOT / purpose_paths["artifact"], payload)
    finally:
        tv.close()


if __name__ == "__main__":
    main()
