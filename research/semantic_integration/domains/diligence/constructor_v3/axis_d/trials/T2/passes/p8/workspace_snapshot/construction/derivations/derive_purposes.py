#!/usr/bin/env python3
"""Derive Purpose A/B/C outputs from compiled world relations."""

from __future__ import annotations

import json
from pathlib import Path

from taskview import TaskView

ACQUISITION_RELEVANT_CLAUSES = frozenset(
    {
        "change_of_control_consent",
        "change_of_control_termination",
        "assignment_notice_or_consent",
        "assignment_consent",
        "assignment_notice",
        "assignment_competitor_prohibition",
        "competitor_assignment_prohibition",
    }
)

DEPENDENCY_OBLIGATION_KINDS = frozenset(
    {"exclusivity", "auto_renewal", "rolling_term"}
)

CONTINUING_TERM_CLAUSES = frozenset({"auto_renewal", "rolling_term"})

ROOT = Path(__file__).resolve().parents[2]


def resolve_world_path() -> Path:
    for candidate in (ROOT / "06_world" / "world.sqlite", ROOT / "world" / "world.sqlite"):
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "world.sqlite not found under 06_world/ or world/; prior world construction pass incomplete"
    )


def strip_invoice_prefix(value: str) -> str:
    return value.removeprefix("invoice:")


def strip_contract_prefix(value: str) -> str:
    return value.removeprefix("contract:")


def contract_ref(stem: str) -> str:
    return stem if stem.startswith("contract:") else f"contract:{stem}"


def lookup_judgment(
    judgments: dict[tuple[str, str], str], left: str, right: str
) -> str | None:
    return judgments.get((left, right)) or judgments.get((right, left))


def derive_purpose_a(tv: TaskView) -> dict:
    invoices = tv.query_semantic(
        "SELECT invoice, invoice_id, billed_name, amount, currency, period, status "
        "FROM invoice_observation ORDER BY invoice_id"
    )
    associations = {
        row["invoice"]: row
        for row in tv.query_semantic(
            "SELECT invoice_id AS invoice, contract_id AS contract, disposition "
            "FROM invoice_contract_association"
        )
    }
    active_contracts = {
        contract_ref(row["contract_id"]): row
        for row in tv.query_semantic(
            "SELECT contract, contract_id, active FROM contract_document_observation"
        )
        if row["active"]
    }
    acquisition_contracts: set[str] = set()
    for row in tv.query_semantic(
        "SELECT contract_id AS contract, clause_kind FROM contract_clause_observation"
    ):
        if row["clause_kind"] in ACQUISITION_RELEVANT_CLAUSES:
            acquisition_contracts.add(row["contract"])

    output_rows = []
    for invoice in invoices:
        assoc = associations.get(invoice["invoice"])
        if assoc is None:
            continue
        contract = assoc["contract"]
        if contract not in active_contracts or contract not in acquisition_contracts:
            continue
        output_rows.append(
            {
                "invoice_id": invoice["invoice_id"],
                "billed_name": invoice["billed_name"],
                "amount": invoice["amount"],
                "currency": invoice["currency"],
                "period": invoice["period"],
                "status": invoice["status"],
                "contract_id": strip_contract_prefix(contract),
                "association": assoc["disposition"],
            }
        )

    output_rows.sort(key=lambda row: row["invoice_id"])
    return {"purpose": "contractual_revenue_exposure", "invoices": output_rows}


def derive_purpose_b(tv: TaskView) -> dict:
    candidates = tv.query_semantic(
        "SELECT left, right FROM commercial_relationship_identity_candidate "
        "ORDER BY left, right"
    )
    judgments = {
        (row["left"], row["right"]): row["disposition"]
        for row in tv.query_semantic(
            "SELECT left, right, disposition FROM identity_judgment"
        )
    }

    links = []
    for pair in candidates:
        left = pair["left"]
        right = pair["right"]
        disposition = lookup_judgment(judgments, left, right) or "UNRESOLVED"
        links.append({"left": left, "right": right, "epistemic": disposition})

    links.sort(key=lambda row: (row["left"], row["right"]))
    return {"purpose": "counterparty_reconciliation", "links": links}


def derive_purpose_c(tv: TaskView) -> dict:
    contracts = {
        row["contract"]: row
        for row in tv.query_semantic(
            "SELECT contract, contract_id, active FROM contract_document_observation"
        )
    }
    clauses_by_contract: dict[str, set[str]] = {}
    for row in tv.query_semantic(
        "SELECT contract_id AS contract, clause_kind FROM contract_clause_observation"
    ):
        clauses_by_contract.setdefault(row["contract"], set()).add(row["clause_kind"])

    open_invoices = {
        row["invoice"]
        for row in tv.query_semantic("SELECT invoice FROM open_invoice")
    }
    associations = tv.query_semantic(
        "SELECT invoice_id AS invoice, contract_id AS contract, disposition "
        "FROM invoice_contract_association"
    )
    assoc_by_contract: dict[str, list[dict]] = {}
    for assoc in associations:
        assoc_by_contract.setdefault(assoc["contract"], []).append(assoc)

    invoices = {
        row["invoice"]: row
        for row in tv.query_semantic(
            "SELECT invoice, invoice_id, billed_name FROM invoice_observation"
        )
    }
    judgments = {
        (row["left"], row["right"]): row["disposition"]
        for row in tv.query_semantic(
            "SELECT left, right, disposition FROM identity_judgment"
        )
    }
    account_contract = {
        row["contract_id"]: row["account_id"]
        for row in tv.query_semantic(
            "SELECT account_id, contract_id FROM account_contract_code_correspondence"
        )
    }

    rows = []
    for contract_ref_id, contract in sorted(contracts.items(), key=lambda item: item[1]["contract_id"]):
        obligation_kinds = sorted(
            clauses_by_contract.get(contract_ref_id, set()) & DEPENDENCY_OBLIGATION_KINDS
        )
        if not obligation_kinds or not contract["active"]:
            continue

        contract_assocs = assoc_by_contract.get(contract_ref_id, [])
        open_ids = sorted(
            {
                strip_invoice_prefix(invoices[assoc["invoice"]]["invoice_id"])
                for assoc in contract_assocs
                if assoc["invoice"] in open_invoices
            }
        )
        has_continuing_term = bool(
            clauses_by_contract.get(contract_ref_id, set()) & CONTINUING_TERM_CLAUSES
        )
        current_relationship = bool(open_ids) or (
            contract["active"] and has_continuing_term
        )
        if not current_relationship:
            continue

        billing_refs = sorted(
            {
                f"billing:{invoices[assoc['invoice']]['billed_name']}"
                for assoc in contract_assocs
                if assoc["invoice"] in invoices
            }
        )
        counterparty = billing_refs[0] if billing_refs else account_contract.get(contract_ref_id, contract_ref_id)

        identity_unresolved = any(
            assoc["disposition"] == "unresolved" for assoc in contract_assocs
        )
        if not identity_unresolved and billing_refs:
            for billing_ref in billing_refs:
                disposition = lookup_judgment(judgments, billing_ref, contract_ref_id)
                if disposition != "SAME_ENTITY":
                    identity_unresolved = True
                    break

        status = "unresolved" if identity_unresolved else "dependent"
        rows.append(
            {
                "counterparty": counterparty,
                "contract_id": contract["contract_id"],
                "open_invoice_ids": open_ids,
                "obligation_kinds": obligation_kinds,
                "status": status,
            }
        )

    return {"purpose": "commercial_dependency", "dependencies": rows}


def write_output(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    world_path = resolve_world_path()
    with TaskView(world_path, view_id="diligence-world") as tv:
        outputs = {
            ROOT / "purpose_ir" / "a" / "output.json": derive_purpose_a(tv),
            ROOT / "purpose_ir" / "b" / "output.json": derive_purpose_b(tv),
            ROOT / "purpose_ir" / "c" / "output.json": derive_purpose_c(tv),
        }
    for path, payload in outputs.items():
        write_output(path, payload)
    print(f"Derived purpose outputs from {world_path}")


if __name__ == "__main__":
    main()
