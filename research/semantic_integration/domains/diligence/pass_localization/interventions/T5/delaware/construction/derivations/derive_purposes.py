#!/usr/bin/env python3
"""Derive purpose A/B/C outputs from world.sqlite and semantic dispositions.

Reads compiled world relations via taskview and purpose-semantic judgments from
05_dispositions.json (purpose-admitted relations are not persisted in world.sqlite).
"""

from __future__ import annotations

import json
from pathlib import Path

from taskview import TaskView

ROOT = Path(__file__).resolve().parents[2]
DISPOSITIONS_PATH = ROOT / "05_dispositions.json"
VIEW_ID = "diligence-world"


def find_world_db() -> Path:
    for candidate in (ROOT / "06_world" / "world.sqlite", ROOT / "world" / "world.sqlite"):
        if candidate.exists():
            return candidate
    raise FileNotFoundError("world.sqlite not found under 06_world/ or world/")


def load_dispositions() -> dict[str, list[dict]]:
    entries = json.loads(DISPOSITIONS_PATH.read_text(encoding="utf-8"))
    grouped: dict[str, list[dict]] = {}
    for entry in entries:
        grouped.setdefault(entry["relation"], []).append(entry)
    return grouped


def strip_invoice_id(referent: str) -> str:
    prefix = "billing:invoice:"
    if referent.startswith(prefix):
        return referent[len(prefix) :]
    return referent


def strip_contract_id(referent: str) -> str:
    prefix = "contract:"
    if referent.startswith(prefix):
        return referent[len(prefix) :]
    return referent


def active_contracts(dispositions: dict[str, list[dict]], relation: str) -> set[str]:
    active: set[str] = set()
    for entry in dispositions.get(relation, []):
        contract = entry["values"]["contract"]
        if entry["disposition"] == "ACCEPT":
            active.add(contract)
    return active


def association_map(dispositions: dict[str, list[dict]]) -> dict[tuple[str, str], str]:
    mapping: dict[tuple[str, str], str] = {}
    for entry in dispositions.get("invoice_contract_association", []):
        invoice = entry["values"]["invoice"]
        contract = entry["values"]["contract"]
        if entry["disposition"] == "ACCEPT":
            mapping[(invoice, contract)] = "asserted"
        elif entry["disposition"] == "UNRESOLVED":
            mapping[(invoice, contract)] = "unresolved"
    return mapping


def identity_links(dispositions: dict[str, list[dict]]) -> list[dict]:
    links = []
    for entry in dispositions.get("identity_link_epistemic", []):
        links.append(
            {
                "left": entry["values"]["left"],
                "right": entry["values"]["right"],
                "epistemic": entry["disposition"],
            }
        )
    links.sort(key=lambda item: (item["left"], item["right"]))
    return links


def identity_status(left: str, right: str, link_index: dict[tuple[str, str], str]) -> str | None:
    if (left, right) in link_index:
        return link_index[(left, right)]
    if (right, left) in link_index:
        return link_index[(right, left)]
    return None


def billing_contract_identity_resolved(
    billed_name: str,
    contract: str,
    link_index: dict[tuple[str, str], str],
) -> bool:
    billing_id = f"billing:{billed_name}"
    status = identity_status(billing_id, contract, link_index)
    return status == "SAME_ENTITY"


def current_relationships(dispositions: dict[str, list[dict]]) -> set[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    for entry in dispositions.get("current_commercial_relationship", []):
        if entry["disposition"] == "ACCEPT":
            pairs.add((entry["values"]["counterparty"], entry["values"]["contract"]))
    return pairs


def derive_purpose_a(tv: TaskView, dispositions: dict[str, list[dict]]) -> dict:
    active = active_contracts(dispositions, "purpose_a_contract_active")
    associations = association_map(dispositions)

    acquisition_contracts = {
        row["contract_id"]
        for row in tv.query_semantic(
            "SELECT contract_id FROM contract_has_acquisition_relevant_term WHERE has_term = 1"
        )
    }

    invoices_by_id = {
        row["invoice_id"]: row
        for row in tv.query_semantic(
            """
            SELECT ib.invoice_id, ib.billed_name, ia.amount, ic.currency,
                   ip.period, ist.status
            FROM invoice_billed_name ib
            JOIN invoice_amount ia ON ia.invoice_id = ib.invoice_id
            JOIN invoice_currency ic ON ic.invoice_id = ib.invoice_id
            JOIN invoice_period ip ON ip.invoice_id = ib.invoice_id
            JOIN invoice_status ist ON ist.invoice_id = ib.invoice_id
            """
        )
    }

    output_rows = []
    for (invoice_ref, contract_ref), association in sorted(associations.items()):
        if contract_ref not in active:
            continue
        if contract_ref not in acquisition_contracts:
            continue
        inv = invoices_by_id[invoice_ref]
        output_rows.append(
            {
                "invoice_id": strip_invoice_id(invoice_ref),
                "billed_name": inv["billed_name"],
                "amount": inv["amount"],
                "currency": inv["currency"],
                "period": inv["period"],
                "status": inv["status"],
                "contract_id": strip_contract_id(contract_ref),
                "association": association,
            }
        )

    output_rows.sort(key=lambda row: row["invoice_id"])
    return {"purpose": "contractual_revenue_exposure", "invoices": output_rows}


def derive_purpose_b(dispositions: dict[str, list[dict]]) -> dict:
    return {"purpose": "counterparty_reconciliation", "links": identity_links(dispositions)}


def derive_purpose_c(tv: TaskView, dispositions: dict[str, list[dict]]) -> dict:
    active = active_contracts(dispositions, "purpose_c_contract_active")
    relationships = current_relationships(dispositions)
    link_index = {
        (entry["values"]["left"], entry["values"]["right"]): entry["disposition"]
        for entry in dispositions.get("identity_link_epistemic", [])
    }

    obligations_by_contract: dict[str, list[str]] = {}
    for row in tv.query_semantic(
        """
        SELECT contract_id, obligation_kind
        FROM contract_has_qualifying_obligation
        WHERE present = 1
        ORDER BY contract_id, obligation_kind
        """
    ):
        obligations_by_contract.setdefault(row["contract_id"], []).append(row["obligation_kind"])

    open_invoices_by_contract: dict[str, list[str]] = {}
    for row in tv.query_semantic(
        """
        SELECT io.invoice_id, ib.billed_name
        FROM invoice_is_open io
        JOIN invoice_billed_name ib ON ib.invoice_id = io.invoice_id
        WHERE io.is_open = 1
        """
    ):
        invoice_ref = row["invoice_id"]
        billed_name = row["billed_name"]
        for entry in dispositions.get("invoice_contract_association", []):
            if entry["disposition"] != "ACCEPT":
                continue
            if entry["values"]["invoice"] != invoice_ref:
                continue
            contract_ref = entry["values"]["contract"]
            billing_id = f"billing:{billed_name}"
            if identity_status(billing_id, contract_ref, link_index) != "SAME_ENTITY":
                continue
            open_invoices_by_contract.setdefault(contract_ref, []).append(
                strip_invoice_id(invoice_ref)
            )

    for contract_ref in open_invoices_by_contract:
        open_invoices_by_contract[contract_ref] = sorted(
            set(open_invoices_by_contract[contract_ref])
        )

    dependencies = []
    for counterparty, contract_ref in sorted(relationships, key=lambda item: strip_contract_id(item[1])):
        if contract_ref not in active:
            continue
        kinds = obligations_by_contract.get(contract_ref, [])
        if not kinds:
            continue
        identity_ok = billing_contract_identity_resolved(
            counterparty.removeprefix("billing:"), contract_ref, link_index
        )
        status = "dependent" if identity_ok else "unresolved"
        dependencies.append(
            {
                "counterparty": counterparty,
                "contract_id": strip_contract_id(contract_ref),
                "open_invoice_ids": open_invoices_by_contract.get(contract_ref, []),
                "obligation_kinds": sorted(kinds),
                "status": status,
            }
        )

    dependencies.sort(key=lambda row: row["contract_id"])
    return {"purpose": "commercial_dependency", "dependencies": dependencies}


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    world_path = find_world_db()
    dispositions = load_dispositions()

    with TaskView(world_path, view_id=VIEW_ID) as tv:
        purpose_a = derive_purpose_a(tv, dispositions)
        purpose_b = derive_purpose_b(dispositions)
        purpose_c = derive_purpose_c(tv, dispositions)

    write_json(ROOT / "purpose_ir" / "a" / "output.json", purpose_a)
    write_json(ROOT / "purpose_ir" / "b" / "output.json", purpose_b)
    write_json(ROOT / "purpose_ir" / "c" / "output.json", purpose_c)

    print(f"Wrote purpose_ir/a/output.json ({len(purpose_a['invoices'])} invoices)")
    print(f"Wrote purpose_ir/b/output.json ({len(purpose_b['links'])} links)")
    print(f"Wrote purpose_ir/c/output.json ({len(purpose_c['dependencies'])} dependencies)")


if __name__ == "__main__":
    main()
