"""C4 derive purpose_ir JSON from compiled TaskView."""

from __future__ import annotations

import json
from pathlib import Path

from taskview import TaskView

ROOT = Path(__file__).resolve().parents[2]


def contract_short(contract_ref: str) -> str:
    return contract_ref.removeprefix("contract:")


def invoice_short(invoice_ref: str) -> str:
    return invoice_ref.removeprefix("invoice:")


def export_purpose_a(tv: TaskView, out_path: Path) -> None:
    rows = tv.query_semantic(
        """
        SELECT invoice_id, billed_name, amount, currency, period, status,
               contract_id, association
        FROM purpose_a_invoice
        ORDER BY invoice_id
        """
    )
    payload = {
        "purpose": "contractual_revenue_exposure",
        "invoices": [
            {
                "invoice_id": invoice_short(row["invoice_id"]),
                "billed_name": row["billed_name"],
                "amount": row["amount"],
                "currency": row["currency"],
                "period": row["period"],
                "status": row["status"],
                "contract_id": contract_short(row["contract_id"]),
                "association": row["association"],
            }
            for row in rows
        ],
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2) + "\n")


def export_purpose_b(tv: TaskView, out_path: Path) -> None:
    rows = tv.query_semantic(
        """
        SELECT left, right, epistemic
        FROM purpose_b_link
        ORDER BY left, right
        """
    )
    payload = {
        "purpose": "counterparty_reconciliation",
        "links": [
            {"left": row["left"], "right": row["right"], "epistemic": row["epistemic"]}
            for row in rows
        ],
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2) + "\n")


def export_purpose_c(tv: TaskView, out_path: Path) -> None:
    rows = tv.query_semantic(
        """
        SELECT counterparty, contract_id, open_invoice_ids, obligation_kinds, status
        FROM purpose_c_dependency
        ORDER BY contract_id
        """
    )
    dependencies = []
    for row in rows:
        open_ids = (
            sorted(row["open_invoice_ids"].split(","))
            if row["open_invoice_ids"]
            else []
        )
        open_ids = [item for item in open_ids if item]
        kinds = sorted(row["obligation_kinds"].split(","))
        kinds = [item for item in kinds if item]
        dependencies.append(
            {
                "counterparty": row["counterparty"],
                "contract_id": contract_short(row["contract_id"]),
                "open_invoice_ids": open_ids,
                "obligation_kinds": kinds,
                "status": row["status"],
            }
        )
    payload = {"purpose": "commercial_dependency", "dependencies": dependencies}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2) + "\n")


def export_all(tv: TaskView) -> None:
    export_purpose_a(tv, ROOT / "purpose_ir" / "a" / "output.json")
    export_purpose_b(tv, ROOT / "purpose_ir" / "b" / "output.json")
    export_purpose_c(tv, ROOT / "purpose_ir" / "c" / "output.json")
