#!/usr/bin/env python3
"""P7 purpose derivations over the certified World (read-only)."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from taskview import TaskView

ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = ROOT / "07_derivations.json"


def load_spec() -> dict:
    return json.loads(SPEC_PATH.read_text())


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def billing_id(billed_name: str) -> str:
    return f"billing:{billed_name}"


def contract_ref(contract_id: str) -> str:
    return f"contract:{contract_id}"


def judgment_lookup(judgments: list[dict]) -> dict[tuple[str, str], str]:
    out: dict[tuple[str, str], str] = {}
    for row in judgments:
        left, right, disposition = row["left"], row["right"], row["disposition"]
        out[(left, right)] = disposition
        out[(right, left)] = disposition
    return out


def disposition_between(lookup: dict[tuple[str, str], str], left: str, right: str) -> str | None:
    return lookup.get((left, right))


def derive_purpose_a(tv: TaskView, spec: dict) -> dict:
    rows = tv.query_semantic(spec["sql"])
    invoices = [
        {
            "invoice_id": row["invoice_id"],
            "billed_name": row["billed_name"],
            "amount": row["amount"],
            "currency": row["currency"],
            "period": row["period"],
            "status": row["status"],
            "contract_id": row["contract_id"],
            "association": row["association"],
        }
        for row in rows
    ]
    return {"purpose": spec["purpose"], "invoices": invoices}


def derive_purpose_b(tv: TaskView, spec: dict) -> dict:
    rows = tv.query_semantic(spec["sql"])
    links = [
        {"left": row["left"], "right": row["right"], "epistemic": row["epistemic"]}
        for row in rows
    ]
    return {"purpose": spec["purpose"], "links": links}


def derive_purpose_c(tv: TaskView, spec: dict) -> dict:
    judgments = tv.query_semantic("SELECT left, right, disposition FROM identity_judgment")
    lookup = judgment_lookup(judgments)

    active = {
        row["contract_id"]
        for row in tv.query_semantic(
            "SELECT contract_id FROM contract_active WHERE active = 1"
        )
    }
    clauses_by_contract: dict[str, set[str]] = defaultdict(set)
    for row in tv.query_semantic(
        "SELECT contract_id, clause_kind FROM contract_clause_kind"
    ):
        if row["clause_kind"] in spec["obligation_kinds"]:
            clauses_by_contract[row["contract_id"]].add(row["clause_kind"])

    invoices = tv.query_semantic(
        "SELECT invoice_id, billed_name, status FROM invoice_record"
    )
    open_by_billing: dict[str, list[str]] = defaultdict(list)
    for inv in invoices:
        if inv["status"] == "open":
            open_by_billing[billing_id(inv["billed_name"])].append(inv["invoice_id"])

    contracts_by_billing: dict[str, set[str]] = defaultdict(set)
    for row in judgments:
        left, right, disposition = row["left"], row["right"], row["disposition"]
        if disposition != "SAME_ENTITY":
            continue
        if left.startswith("billing:") and right.startswith("contract:"):
            contracts_by_billing[left].add(right.removeprefix("contract:"))
        elif right.startswith("billing:") and left.startswith("contract:"):
            contracts_by_billing[right].add(left.removeprefix("contract:"))

    crm_by_billing: dict[str, str] = {}
    for row in judgments:
        left, right, disposition = row["left"], row["right"], row["disposition"]
        if disposition != "SAME_ENTITY":
            continue
        if left.startswith("crm:") and right.startswith("billing:"):
            crm_by_billing[right] = left
        elif right.startswith("crm:") and left.startswith("billing:"):
            crm_by_billing[left] = right

    renewal_kinds = {"auto_renewal", "rolling_term"}
    dependencies: list[dict] = []

    for contract_id in sorted(active):
        obligation_kinds = sorted(clauses_by_contract.get(contract_id, set()))
        if not obligation_kinds:
            continue

        billings = [
            billing
            for billing, contracts in contracts_by_billing.items()
            if contract_id in contracts
        ]
        if not billings:
            dependencies.append(
                {
                    "counterparty": contract_ref(contract_id),
                    "contract_id": contract_id,
                    "open_invoice_ids": [],
                    "obligation_kinds": obligation_kinds,
                    "status": "unresolved",
                }
            )
            continue

        for billing in sorted(billings):
            open_ids = sorted(open_by_billing.get(billing, []))
            has_renewal = bool(set(obligation_kinds) & renewal_kinds)
            has_current = bool(open_ids) or has_renewal
            identity_ok = (
                disposition_between(lookup, billing, contract_ref(contract_id))
                == "SAME_ENTITY"
            )
            counterparty = crm_by_billing.get(billing, billing)
            if has_current and identity_ok:
                status = "dependent"
            else:
                status = "unresolved"

            dependencies.append(
                {
                    "counterparty": counterparty,
                    "contract_id": contract_id,
                    "open_invoice_ids": open_ids,
                    "obligation_kinds": obligation_kinds,
                    "status": status,
                }
            )

    dependencies.sort(key=lambda item: item["contract_id"])
    return {"purpose": spec["purpose"], "dependencies": dependencies}


DERIVERS = {
    "a": derive_purpose_a,
    "b": derive_purpose_b,
    "c": derive_purpose_c,
}


def main() -> None:
    spec_doc = load_spec()
    world = spec_doc["world"]
    tv = TaskView(ROOT / world["path"], view_id=world["view_id"])
    try:
        for purpose_id, purpose_spec in spec_doc["purposes"].items():
            payload = DERIVERS[purpose_id](tv, purpose_spec)
            for output_path in purpose_spec["outputs"]:
                write_json(ROOT / output_path, payload)
            print(f"derived purpose {purpose_id} -> {purpose_spec['outputs']}")
    finally:
        tv.close()


if __name__ == "__main__":
    main()
