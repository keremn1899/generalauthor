#!/usr/bin/env python3
"""C4 derivation compiler: materialize purpose_ir outputs from world.sqlite."""

from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VIEW_ID = "diligence-world"
REFERENCE_DATE = date(2026, 9, 2)
OBLIGATION_KINDS = ("auto_renewal", "exclusivity", "rolling_term")
ACQUISITION_KINDS = (
    "change_of_control_consent",
    "change_of_control_termination",
    "assignment_notice_or_consent",
    "assignment_consent",
    "assignment_notice",
    "assignment_competitor_prohibition",
    "competitor_assignment_prohibition",
)


def resolve_world_path() -> Path:
    for candidate in (ROOT / "06_world" / "world.sqlite", ROOT / "world" / "world.sqlite"):
        if candidate.exists():
            return candidate
    raise FileNotFoundError("world.sqlite not found under 06_world/ or world/")


def connect_world(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    view = conn.execute("SELECT view_id FROM _tv_view WHERE singleton = 1").fetchone()
    if view is None or view["view_id"] != VIEW_ID:
        raise RuntimeError(f"expected TaskView {VIEW_ID!r}, got {view}")
    return conn


def fetch_rows(conn: sqlite3.Connection, relation: str) -> list[sqlite3.Row]:
    return list(conn.execute(f'SELECT * FROM "{relation}"'))


def strip_prefix(value: str, prefix: str) -> str:
    token = f"{prefix}:"
    return value[len(token) :] if value.startswith(token) else value


def parse_expiry(raw: str) -> date | None:
    text = (raw or "").strip()
    if not text:
        return None
    for fmt in ("%d %B %Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def contract_is_expired(document_kind: str, expiry_date: str) -> bool:
    expiry = parse_expiry(expiry_date)
    if expiry is None:
        return False
    return expiry < REFERENCE_DATE


def purpose_a_active(contract: sqlite3.Row) -> bool:
    if contract["document_kind"] == "SOW" and contract_is_expired(
        contract["document_kind"], contract["expiry_date"]
    ):
        return False
    return True


def purpose_c_active(contract: sqlite3.Row) -> bool:
    return not contract_is_expired(contract["document_kind"], contract["expiry_date"])


def load_acquisition_presence() -> dict[tuple[str, str], str]:
    """Prior-pass artifact: acquisition_clause_presence is PURPOSE-scoped and not in world.sqlite."""
    path = ROOT / "05_dispositions.json"
    if not path.exists():
        return {}
    present: dict[tuple[str, str], str] = {}
    for item in json.loads(path.read_text(encoding="utf-8")):
        if item.get("relation") != "acquisition_clause_presence":
            continue
        values = item["values"]
        key = (values["contract"], values["clause_kind"])
        disposition = item.get("final_admitted_disposition") or item.get("disposition")
        if disposition == "ACCEPT":
            present[key] = "PRESENT"
        else:
            present[key] = "UNRESOLVED"
    return present


def identity_lookup(rows: list[sqlite3.Row]) -> dict[tuple[str, str], str]:
    table: dict[tuple[str, str], str] = {}
    for row in rows:
        left, right, disposition = row["left"], row["right"], row["disposition"]
        table[(left, right)] = disposition
        table[(right, left)] = disposition
    return table


def identity_between(table: dict[tuple[str, str], str], left: str, right: str) -> str | None:
    return table.get((left, right))


def derive_open_invoices(invoices: list[sqlite3.Row]) -> list[sqlite3.Row]:
    return [row for row in invoices if row["status"] == "open"]


def contract_has_acquisition_clause(
    contract_key: str, acquisition: dict[tuple[str, str], str]
) -> bool:
    return any(acquisition.get((contract_key, kind)) == "PRESENT" for kind in ACQUISITION_KINDS)


def contract_obligation_kinds(
    contract_key: str, obligations: list[sqlite3.Row]
) -> list[str]:
    kinds = [
        row["clause_kind"]
        for row in obligations
        if row["contract"] == contract_key and row["disposition"] == "PRESENT"
    ]
    return sorted(kinds)


def has_current_relationship(
    contract_key: str,
    contract: sqlite3.Row,
    open_invoice_ids: list[str],
    obligations: list[sqlite3.Row],
) -> bool:
    if open_invoice_ids:
        return True
    if not purpose_c_active(contract):
        return False
    for row in obligations:
        if row["contract"] != contract_key:
            continue
        if row["disposition"] == "PRESENT" and row["clause_kind"] in ("auto_renewal", "rolling_term"):
            return True
    return False


def derive_purpose_a(
    invoices: list[sqlite3.Row],
    contracts: list[sqlite3.Row],
    identity_rows: list[sqlite3.Row],
    acquisition: dict[tuple[str, str], str],
) -> dict:
    contract_by_key = {row["contract"]: row for row in contracts}
    identity = identity_lookup(identity_rows)
    exposure: list[dict] = []

    for invoice in sorted(invoices, key=lambda row: row["invoice_id"]):
        billing_ref = f"billing:{invoice['billed_name']}"
        for contract_key, contract in contract_by_key.items():
            link = identity_between(identity, billing_ref, contract_key)
            if link is None:
                continue
            if not purpose_a_active(contract):
                continue
            if not contract_has_acquisition_clause(contract_key, acquisition):
                continue
            association = "asserted" if link == "SAME_ENTITY" else "unresolved"
            exposure.append(
                {
                    "invoice_id": invoice["invoice_id"],
                    "billed_name": invoice["billed_name"],
                    "amount": invoice["amount"],
                    "currency": invoice["currency"],
                    "period": invoice["period"],
                    "status": invoice["status"],
                    "contract_id": contract["contract_id"],
                    "association": association,
                }
            )

    exposure.sort(key=lambda row: row["invoice_id"])
    return {"purpose": "contractual_revenue_exposure", "invoices": exposure}


def derive_purpose_b(identity_rows: list[sqlite3.Row]) -> dict:
    links = [
        {
            "left": row["left"],
            "right": row["right"],
            "epistemic": row["disposition"],
        }
        for row in identity_rows
    ]
    links.sort(key=lambda row: (row["left"], row["right"]))
    return {"purpose": "counterparty_reconciliation", "links": links}


def derive_purpose_c(
    invoices: list[sqlite3.Row],
    contracts: list[sqlite3.Row],
    identity_rows: list[sqlite3.Row],
    obligations: list[sqlite3.Row],
    open_invoices: list[sqlite3.Row],
) -> dict:
    contract_by_key = {row["contract"]: row for row in contracts}
    identity = identity_lookup(identity_rows)
    open_by_billing: dict[str, list[str]] = defaultdict(list)
    for row in open_invoices:
        open_by_billing[row["billed_name"]].append(row["invoice_id"])

    pairs: set[tuple[str, str]] = set()
    for invoice in invoices:
        billing_ref = f"billing:{invoice['billed_name']}"
        for contract_key in contract_by_key:
            if identity_between(identity, billing_ref, contract_key) is not None:
                pairs.add((billing_ref, contract_key))

    dependencies: list[dict] = []
    for billing_ref, contract_key in sorted(pairs, key=lambda item: (item[1], item[0])):
        contract = contract_by_key[contract_key]
        billed_name = strip_prefix(billing_ref, "billing")
        link = identity_between(identity, billing_ref, contract_key)
        obligation_kinds = contract_obligation_kinds(contract_key, obligations)
        open_ids = sorted(open_by_billing.get(billed_name, []))
        current = has_current_relationship(contract_key, contract, open_ids, obligations)
        has_obligation = bool(obligation_kinds)

        would_depend = current and has_obligation
        if link == "UNRESOLVED":
            if not would_depend:
                continue
            status = "unresolved"
        elif would_depend:
            status = "dependent"
        else:
            continue

        dependencies.append(
            {
                "counterparty": billing_ref,
                "contract_id": contract["contract_id"],
                "open_invoice_ids": open_ids,
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
    conn = connect_world(world_path)
    try:
        invoices = fetch_rows(conn, "invoice_record")
        contracts = fetch_rows(conn, "contract_record")
        identity_rows = fetch_rows(conn, "identity_judgment")
        obligations = fetch_rows(conn, "obligation_clause_presence")
    finally:
        conn.close()

    acquisition = load_acquisition_presence()
    open_invoices = derive_open_invoices(invoices)

    write_json(ROOT / "purpose_ir" / "a" / "output.json", derive_purpose_a(
        invoices, contracts, identity_rows, acquisition
    ))
    write_json(ROOT / "purpose_ir" / "b" / "output.json", derive_purpose_b(identity_rows))
    write_json(ROOT / "purpose_ir" / "c" / "output.json", derive_purpose_c(
        invoices, contracts, identity_rows, obligations, open_invoices
    ))


if __name__ == "__main__":
    main()
