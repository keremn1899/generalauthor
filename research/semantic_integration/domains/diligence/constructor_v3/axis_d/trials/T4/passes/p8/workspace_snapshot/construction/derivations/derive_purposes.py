#!/usr/bin/env python3
"""Compile purpose A/B/C output JSON from world.sqlite."""

from __future__ import annotations

import json
from pathlib import Path

from taskview import TaskView

VIEW_ID = "diligence-world"

ACQUISITION_CLAUSE_KINDS = (
    "change_of_control_consent",
    "change_of_control_termination",
    "assignment_notice_or_consent",
    "assignment_consent",
    "assignment_notice",
    "assignment_competitor_prohibition",
    "competitor_assignment_prohibition",
)

OBLIGATION_CLAUSE_KINDS = ("exclusivity", "auto_renewal", "rolling_term")


def resolve_world_path(root: Path) -> Path:
    for candidate in (root / "06_world" / "world.sqlite", root / "world" / "world.sqlite"):
        if candidate.exists():
            return candidate
    raise FileNotFoundError("world.sqlite not found under 06_world/ or world/")


def load_identity_map(tv: TaskView) -> dict[tuple[str, str], str]:
    rows = tv.query("SELECT left, right, disposition FROM identity_judgment")
    mapping: dict[tuple[str, str], str] = {}
    for row in rows:
        left, right = row["left"], row["right"]
        mapping[(left, right)] = row["disposition"]
        mapping[(right, left)] = row["disposition"]
    return mapping


def identity_disposition(identity_map: dict[tuple[str, str], str], left: str, right: str) -> str | None:
    return identity_map.get((left, right))


def same_entity_connected(identity_map: dict[tuple[str, str], str], left: str, right: str) -> bool:
    direct = identity_disposition(identity_map, left, right)
    if direct == "SAME_ENTITY":
        return True
    if direct == "DISTINCT":
        return False

    graph: dict[str, set[str]] = {}
    for (a, b), disposition in identity_map.items():
        if disposition != "SAME_ENTITY":
            continue
        graph.setdefault(a, set()).add(b)
        graph.setdefault(b, set()).add(a)

    seen = {left}
    frontier = [left]
    while frontier:
        node = frontier.pop()
        for neighbor in graph.get(node, ()):
            if neighbor == right:
                return True
            if neighbor not in seen:
                seen.add(neighbor)
                frontier.append(neighbor)
    return False


def contract_has_present_clause(
    tv: TaskView, contract_id: str, clause_kinds: tuple[str, ...]
) -> bool:
    placeholders = ",".join("?" for _ in clause_kinds)
    rows = tv.query(
        f"""
        SELECT 1
        FROM clause_kind_presence
        WHERE contract_id = ?
          AND clause_kind IN ({placeholders})
          AND disposition = 'PRESENT'
        LIMIT 1
        """,
        (contract_id, *clause_kinds),
    )
    return bool(rows)


def present_obligation_kinds(tv: TaskView, contract_id: str) -> list[str]:
    placeholders = ",".join("?" for _ in OBLIGATION_CLAUSE_KINDS)
    rows = tv.query(
        f"""
        SELECT clause_kind
        FROM clause_kind_presence
        WHERE contract_id = ?
          AND clause_kind IN ({placeholders})
          AND disposition = 'PRESENT'
        ORDER BY clause_kind
        """,
        (contract_id, *OBLIGATION_CLAUSE_KINDS),
    )
    return [row["clause_kind"] for row in rows]


def derive_purpose_a(tv: TaskView) -> dict:
    identity_map = load_identity_map(tv)
    invoices = tv.query(
        "SELECT invoice_id, billed_name, amount, currency, period, status FROM invoice_fact"
    )
    governing = {
        row["invoice_id"]: row
        for row in tv.query(
            "SELECT invoice_id, contract_id, disposition FROM invoice_governing_contract"
        )
    }
    active_contracts = {
        row["contract_id"]
        for row in tv.query("SELECT contract_id FROM contract_temporal_fact WHERE active = 1")
    }
    candidates = {
        row["invoice_id"]: row["contract_id"]
        for row in tv.query("SELECT invoice_id, contract_id FROM invoice_governing_contract_candidate")
    }

    output_rows: list[dict] = []
    for invoice in invoices:
        invoice_id = invoice["invoice_id"]
        billing_id = f"billing:{invoice['billed_name']}"
        gov = governing.get(invoice_id)
        contract_id = gov["contract_id"] if gov else candidates.get(invoice_id)
        if not contract_id:
            continue

        has_acquisition = contract_has_present_clause(tv, contract_id, ACQUISITION_CLAUSE_KINDS)
        is_active = contract_id in active_contracts
        if not (is_active and has_acquisition):
            continue

        contract_identifier = f"contract:{contract_id}"
        gov_disposition = gov["disposition"] if gov else "UNRESOLVED"
        identity_resolved = same_entity_connected(identity_map, billing_id, contract_identifier)

        if gov_disposition == "ASSERTED" and identity_resolved:
            association = "asserted"
        else:
            association = "unresolved"

        output_rows.append(
            {
                "invoice_id": invoice_id,
                "billed_name": invoice["billed_name"],
                "amount": invoice["amount"],
                "currency": invoice["currency"],
                "period": invoice["period"],
                "status": invoice["status"],
                "contract_id": contract_id,
                "association": association,
            }
        )

    output_rows.sort(key=lambda row: row["invoice_id"])
    return {"purpose": "contractual_revenue_exposure", "invoices": output_rows}


def derive_purpose_b(tv: TaskView) -> dict:
    disposition_map = {
        "SAME_ENTITY": "SAME_ENTITY",
        "DISTINCT": "DISTINCT",
        "UNRESOLVED": "UNRESOLVED",
        "REJECT": "DISTINCT",
        "ACCEPT": "SAME_ENTITY",
    }
    links = []
    for row in tv.query("SELECT left, right, disposition FROM identity_judgment"):
        epistemic = disposition_map.get(row["disposition"], "UNRESOLVED")
        links.append({"left": row["left"], "right": row["right"], "epistemic": epistemic})
    links.sort(key=lambda row: (row["left"], row["right"]))
    return {"purpose": "counterparty_reconciliation", "links": links}


def derive_purpose_c(tv: TaskView) -> dict:
    identity_map = load_identity_map(tv)
    active_contracts = {
        row["contract_id"]
        for row in tv.query("SELECT contract_id FROM contract_temporal_fact WHERE active = 1")
    }
    governing = tv.query(
        """
        SELECT invoice_id, contract_id, disposition
        FROM invoice_governing_contract
        """
    )
    gov_by_contract: dict[str, list[dict]] = {}
    for row in governing:
        gov_by_contract.setdefault(row["contract_id"], []).append(row)

    open_invoice_ids = {
        row["invoice_id"] for row in tv.query("SELECT invoice_id FROM open_invoice_set")
    }
    billing_by_invoice = {
        row["invoice_id"]: row["billed_name"]
        for row in tv.query("SELECT invoice_id, billed_name FROM invoice_fact")
    }

    dependencies: list[dict] = []
    for contract_id in sorted(active_contracts):
        obligation_kinds = present_obligation_kinds(tv, contract_id)
        if not obligation_kinds:
            continue

        contract_identifier = f"contract:{contract_id}"
        contract_links = gov_by_contract.get(contract_id, [])
        linked_open_invoices: list[str] = []
        linkage_unresolved = False

        for link in contract_links:
            billing_id = f"billing:{billing_by_invoice.get(link['invoice_id'], '')}"
            identity_resolved = same_entity_connected(identity_map, billing_id, contract_identifier)
            if link["disposition"] != "ASSERTED" or not identity_resolved:
                linkage_unresolved = True
            if link["disposition"] == "ASSERTED" and link["invoice_id"] in open_invoice_ids:
                linked_open_invoices.append(link["invoice_id"])

        has_open_invoice = bool(linked_open_invoices)
        has_continuing_term = "auto_renewal" in obligation_kinds or "rolling_term" in obligation_kinds
        current_relationship = has_open_invoice or has_continuing_term

        counterparty = None
        for link in contract_links:
            if link["disposition"] == "ASSERTED":
                billed_name = billing_by_invoice.get(link["invoice_id"])
                if billed_name:
                    counterparty = f"billing:{billed_name}"
                    break
        if counterparty is None:
            counterparty = contract_identifier

        if linkage_unresolved:
            status = "unresolved"
        elif current_relationship:
            status = "dependent"
        else:
            continue

        dependencies.append(
            {
                "counterparty": counterparty,
                "contract_id": contract_id,
                "open_invoice_ids": sorted(set(linked_open_invoices)),
                "obligation_kinds": obligation_kinds,
                "status": status,
            }
        )

    dependencies.sort(key=lambda row: row["contract_id"])
    return {"purpose": "commercial_dependency", "dependencies": dependencies}


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    world_path = resolve_world_path(root)
    tv = TaskView(world_path, view_id=VIEW_ID)

    outputs = {
        root / "purpose_ir" / "a" / "output.json": derive_purpose_a(tv),
        root / "purpose_ir" / "b" / "output.json": derive_purpose_b(tv),
        root / "purpose_ir" / "c" / "output.json": derive_purpose_c(tv),
    }
    for path, payload in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        rows = payload.get("invoices") or payload.get("links") or payload.get("dependencies") or []
        print(f"wrote {path.relative_to(root)} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
