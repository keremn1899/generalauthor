#!/usr/bin/env python3
"""P7 purpose derivations over the certified diligence-world TaskView."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from taskview import TaskView

ROOT = Path(__file__).resolve().parents[2]
WORLD_PATH = ROOT / "world" / "world.sqlite"
DERIVATIONS_PATH = ROOT / "07_derivations.json"
VIEW_ID = "diligence-world"

ACQUISITION_CLAUSE_KINDS = frozenset(
    {
        "assignment_notice_or_consent",
        "change_of_control_consent",
        "change_of_control_termination",
        "competitor_assignment_prohibition",
    }
)
DEPENDENCY_CLAUSE_KINDS = frozenset({"auto_renewal", "exclusivity", "rolling_term"})
CONTINUITY_CLAUSE_KINDS = frozenset({"auto_renewal", "rolling_term"})


def _billing_id(billed_name: str) -> str:
    return f"billing:{billed_name}"


def _identity_lookup(rows: list[dict[str, str]]) -> dict[tuple[str, str], str]:
    out: dict[tuple[str, str], str] = {}
    for row in rows:
        left = row["left"]
        right = row["right"]
        out[(left, right)] = row["disposition"]
        out[(right, left)] = row["disposition"]
    return out



def derive_purpose_a(tv: TaskView) -> dict:
    invoices = tv.query_semantic(
        "SELECT invoice_id, billed_name, amount, currency, period, status "
        "FROM invoice_record"
    )
    active_contracts = {
        row["contract_id"]
        for row in tv.query_semantic(
            "SELECT contract_id FROM contract_active WHERE active = 1"
        )
    }
    acquisition_by_contract: dict[str, set[str]] = defaultdict(set)
    for row in tv.query_semantic(
        "SELECT contract_id, clause_kind FROM contract_clause_kind"
    ):
        if row["clause_kind"] in ACQUISITION_CLAUSE_KINDS:
            acquisition_by_contract[row["contract_id"]].add(row["clause_kind"])
    identity = _identity_lookup(tv.query_semantic("SELECT left, right, disposition FROM identity_judgment"))

    qualifying: list[dict] = []
    for invoice in invoices:
        billed_name = invoice["billed_name"]
        linked_contracts: list[tuple[str, str]] = []
        billing = _billing_id(billed_name)
        for (left, right), disposition in identity.items():
            if left != billing or not right.startswith("contract:"):
                continue
            if disposition not in {"SAME_ENTITY", "UNRESOLVED"}:
                continue
            linked_contracts.append((right.removeprefix("contract:"), disposition))
        for bare_contract, disposition in sorted(linked_contracts):
            if bare_contract not in active_contracts:
                continue
            if not acquisition_by_contract.get(bare_contract):
                continue
            association = (
                "asserted" if disposition == "SAME_ENTITY" else "unresolved"
            )
            qualifying.append(
                {
                    "invoice_id": invoice["invoice_id"],
                    "billed_name": billed_name,
                    "amount": invoice["amount"],
                    "currency": invoice["currency"],
                    "period": invoice["period"],
                    "status": invoice["status"],
                    "contract_id": bare_contract,
                    "association": association,
                }
            )

    qualifying.sort(key=lambda row: row["invoice_id"])
    return {"purpose": "contractual_revenue_exposure", "invoices": qualifying}


def derive_purpose_b(tv: TaskView) -> dict:
    links = [
        {
            "left": row["left"],
            "right": row["right"],
            "epistemic": row["disposition"],
        }
        for row in tv.query_semantic(
            "SELECT left, right, disposition FROM identity_judgment "
            "ORDER BY left, right"
        )
    ]
    return {"purpose": "counterparty_reconciliation", "links": links}


def derive_purpose_c(tv: TaskView) -> dict:
    active_contracts = {
        row["contract_id"]
        for row in tv.query_semantic(
            "SELECT contract_id FROM contract_active WHERE active = 1"
        )
    }
    clauses_by_contract: dict[str, set[str]] = defaultdict(set)
    for row in tv.query_semantic(
        "SELECT contract_id, clause_kind FROM contract_clause_kind"
    ):
        clauses_by_contract[row["contract_id"]].add(row["clause_kind"])

    identity_rows = tv.query_semantic("SELECT left, right, disposition FROM identity_judgment")
    identity = _identity_lookup(identity_rows)

    billing_for_contract: dict[str, tuple[str, str]] = {}
    for left, right in identity:
        if left.startswith("billing:") and right.startswith("contract:"):
            billing_for_contract[right.removeprefix("contract:")] = (left, identity[(left, right)])

    open_invoices_by_billing: dict[str, list[str]] = defaultdict(list)
    for row in tv.query_semantic(
        "SELECT invoice_id, billed_name, status FROM invoice_record WHERE status = 'open'"
    ):
        open_invoices_by_billing[_billing_id(row["billed_name"])].append(row["invoice_id"])
    for billed in open_invoices_by_billing:
        open_invoices_by_billing[billed].sort()

    dependencies: list[dict] = []
    for contract_id in sorted(active_contracts):
        obligation_kinds = sorted(
            clauses_by_contract.get(contract_id, set()) & DEPENDENCY_CLAUSE_KINDS
        )
        if not obligation_kinds:
            continue

        billing_link = billing_for_contract.get(contract_id)
        if billing_link is None:
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

        billing_id, disposition = billing_link
        continuity = bool(clauses_by_contract.get(contract_id, set()) & CONTINUITY_CLAUSE_KINDS)
        open_invoice_ids = open_invoices_by_billing.get(billing_id, [])
        has_current_relationship = bool(open_invoice_ids) or continuity
        if not has_current_relationship:
            continue

        status = "dependent" if disposition == "SAME_ENTITY" else "unresolved"
        dependencies.append(
            {
                "counterparty": billing_id,
                "contract_id": contract_id,
                "open_invoice_ids": open_invoice_ids,
                "obligation_kinds": obligation_kinds,
                "status": status,
            }
        )

    dependencies.sort(key=lambda row: row["contract_id"])
    return {"purpose": "commercial_dependency", "dependencies": dependencies}


DERIVERS = {
    "a": derive_purpose_a,
    "b": derive_purpose_b,
    "c": derive_purpose_c,
}


PURPOSE_ORDER = ("a", "b", "c")


def main() -> None:
    spec = json.loads(DERIVATIONS_PATH.read_text(encoding="utf-8"))
    with TaskView(WORLD_PATH, view_id=VIEW_ID) as tv:
        outputs = {purpose: deriver(tv) for purpose, deriver in DERIVERS.items()}
    for purpose, payload in outputs.items():
        entry = spec["derivations"][PURPOSE_ORDER.index(purpose)]
        for key in ("purpose_ir", "snapshot"):
            path = ROOT / entry["output"][key]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({purpose: entry["output"] for purpose, entry in zip(DERIVERS, spec["derivations"], strict=True)}, indent=2))


if __name__ == "__main__":
    main()
