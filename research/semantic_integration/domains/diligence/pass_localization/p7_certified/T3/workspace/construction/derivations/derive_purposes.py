#!/usr/bin/env python3
"""P7 purpose derivations over certified world/world.sqlite (read-only)."""

from __future__ import annotations

import json
from pathlib import Path

from taskview import TaskView

ROOT = Path(__file__).resolve().parents[2]
WORLD = ROOT / "world" / "world.sqlite"
VIEW_ID = "diligence-world"

ACQUISITION_CLAUSE_KINDS = (
    "change_of_control_consent",
    "change_of_control_termination",
    "assignment_notice_or_consent",
    "competitor_assignment_prohibition",
)

DEPENDENCY_OBLIGATION_KINDS = ("auto_renewal", "exclusivity", "rolling_term")
CONTINUING_CLAUSE_KINDS = ("auto_renewal", "rolling_term")


def _open_world() -> TaskView:
    return TaskView(WORLD, view_id=VIEW_ID)


def _contract_id_from_ref(ref: str) -> str:
    prefix = "contract:"
    if not ref.startswith(prefix):
        raise ValueError(f"expected contract ref, got {ref!r}")
    return ref[len(prefix) :]


def derive_purpose_a(tv: TaskView) -> dict:
    acquisition = set(ACQUISITION_CLAUSE_KINDS)
    active_with_acquisition: set[str] = set()
    for row in tv.query_semantic("SELECT contract_id, clause_kind FROM contract_clause_kind"):
        if row["clause_kind"] in acquisition:
            active = tv.query_semantic(
                "SELECT active FROM contract_active WHERE contract_id = ?",
                (row["contract_id"],),
            )
            if active and active[0]["active"]:
                active_with_acquisition.add(row["contract_id"])

    billing_to_contract: dict[str, tuple[str, str]] = {}
    for row in tv.query_semantic(
        "SELECT left, right, disposition FROM identity_judgment "
        "WHERE left LIKE 'billing:%' AND right LIKE 'contract:%'"
    ):
        billed = row["left"][len("billing:") :]
        contract_id = _contract_id_from_ref(row["right"])
        billing_to_contract[billed] = (contract_id, row["disposition"])

    invoices: list[dict] = []
    for row in tv.query_semantic(
        "SELECT invoice_id, billed_name, amount, currency, period, status "
        "FROM invoice_record ORDER BY invoice_id"
    ):
        link = billing_to_contract.get(row["billed_name"])
        if link is None:
            continue
        contract_id, disposition = link
        if contract_id not in active_with_acquisition:
            continue
        if disposition == "DISTINCT":
            continue
        association = "asserted" if disposition == "SAME_ENTITY" else "unresolved"
        invoices.append(
            {
                "invoice_id": row["invoice_id"],
                "billed_name": row["billed_name"],
                "amount": row["amount"],
                "currency": row["currency"],
                "period": row["period"],
                "status": row["status"],
                "contract_id": contract_id,
                "association": association,
            }
        )

    return {"purpose": "contractual_revenue_exposure", "invoices": invoices}


def derive_purpose_b(tv: TaskView) -> dict:
    links = []
    for row in tv.query_semantic(
        "SELECT left, right, disposition FROM identity_judgment "
        "ORDER BY left, right"
    ):
        disposition = row["disposition"]
        if disposition not in {"SAME_ENTITY", "DISTINCT", "UNRESOLVED"}:
            disposition = "UNRESOLVED"
        links.append(
            {
                "left": row["left"],
                "right": row["right"],
                "epistemic": disposition,
            }
        )
    return {"purpose": "counterparty_reconciliation", "links": links}


def derive_purpose_c(tv: TaskView) -> dict:
    active_contracts = {
        row["contract_id"]
        for row in tv.query_semantic("SELECT contract_id FROM contract_active WHERE active = 1")
    }

    obligations_by_contract: dict[str, set[str]] = {}
    for row in tv.query_semantic("SELECT contract_id, clause_kind FROM contract_clause_kind"):
        if row["contract_id"] not in active_contracts:
            continue
        if row["clause_kind"] in DEPENDENCY_OBLIGATION_KINDS:
            obligations_by_contract.setdefault(row["contract_id"], set()).add(row["clause_kind"])

    continuing_contracts = {
        row["contract_id"]
        for row in tv.query_semantic("SELECT contract_id, clause_kind FROM contract_clause_kind")
        if row["contract_id"] in active_contracts
        and row["clause_kind"] in CONTINUING_CLAUSE_KINDS
    }

    open_invoices_by_billed: dict[str, list[str]] = {}
    for row in tv.query_semantic(
        "SELECT invoice_id, billed_name, status FROM invoice_record WHERE status = 'open'"
    ):
        open_invoices_by_billed.setdefault(row["billed_name"], []).append(row["invoice_id"])

    contract_counterparty: dict[str, tuple[str, str]] = {}
    for row in tv.query_semantic(
        "SELECT left, right, disposition FROM identity_judgment "
        "WHERE left LIKE 'billing:%' AND right LIKE 'contract:%'"
    ):
        contract_id = _contract_id_from_ref(row["right"])
        contract_counterparty[contract_id] = (row["left"], row["disposition"])

    dependencies: list[dict] = []
    for contract_id in sorted(obligations_by_contract):
        obligation_kinds = sorted(obligations_by_contract[contract_id])
        counterparty_info = contract_counterparty.get(contract_id)
        if counterparty_info is None:
            dependencies.append(
                {
                    "counterparty": f"contract:{contract_id}",
                    "contract_id": contract_id,
                    "open_invoice_ids": [],
                    "obligation_kinds": obligation_kinds,
                    "status": "unresolved",
                }
            )
            continue

        counterparty, disposition = counterparty_info
        billed_name = counterparty[len("billing:") :]
        open_ids = sorted(open_invoices_by_billed.get(billed_name, []))
        has_open_invoice = bool(open_ids)
        has_continuing_term = contract_id in continuing_contracts
        if not (has_open_invoice or has_continuing_term):
            continue

        status = "dependent" if disposition == "SAME_ENTITY" else "unresolved"
        dependencies.append(
            {
                "counterparty": counterparty,
                "contract_id": contract_id,
                "open_invoice_ids": open_ids,
                "obligation_kinds": obligation_kinds,
                "status": status,
            }
        )

    return {"purpose": "commercial_dependency", "dependencies": dependencies}


def write_outputs(outputs: dict[str, dict]) -> None:
    for key, payload in outputs.items():
        text = json.dumps(payload, indent=2, sort_keys=False) + "\n"
        for rel_path in (f"08_outputs/{key}.json", f"purpose_ir/{key}/output.json"):
            path = ROOT / rel_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")


def main() -> None:
    tv = _open_world()
    try:
        outputs = {
            "a": derive_purpose_a(tv),
            "b": derive_purpose_b(tv),
            "c": derive_purpose_c(tv),
        }
    finally:
        tv.close()
    write_outputs(outputs)
    for key, payload in outputs.items():
        print(f"purpose {key}: {json.dumps(payload, sort_keys=True)}")


if __name__ == "__main__":
    main()
