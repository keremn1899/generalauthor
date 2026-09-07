#!/usr/bin/env python3
"""Derive purpose IR outputs A/B/C from world.sqlite and adjudicated dispositions."""

from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DISPOSITIONS_PATH = ROOT / "05_dispositions.json"
PURPOSE_CONTRACTS = {
    "a": ROOT / "contracts" / "purpose_a.json",
    "b": ROOT / "contracts" / "purpose_b.json",
    "c": ROOT / "contracts" / "purpose_c.json",
}
WORLD_PATHS = [ROOT / "06_world" / "world.sqlite", ROOT / "world" / "world.sqlite"]
VIEW_ID = "diligence-world"


def find_world() -> Path:
    for path in WORLD_PATHS:
        if path.exists():
            return path
    raise FileNotFoundError(
        "world.sqlite not found; expected 06_world/world.sqlite or world/world.sqlite"
    )


def connect_world(path: Path) -> sqlite3.Connection:
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    view = db.execute("SELECT view_id FROM _tv_view WHERE singleton = 1").fetchone()
    if view is None or view["view_id"] != VIEW_ID:
        raise ValueError(f"{path} is not TaskView {VIEW_ID!r}")
    return db


def load_purpose_contract(purpose_key: str) -> dict:
    with PURPOSE_CONTRACTS[purpose_key].open(encoding="utf-8") as handle:
        return json.load(handle)


def load_dispositions() -> list[dict]:
    with DISPOSITIONS_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def strip_prefix(value: str, prefix: str) -> str:
    token = f"{prefix}:"
    return value[len(token) :] if value.startswith(token) else value


def index_dispositions(dispositions: list[dict]) -> dict[tuple[str, str], dict]:
    by_relation: dict[str, list[dict]] = defaultdict(list)
    for item in dispositions:
        by_relation[item["relation"]].append(item)
    return by_relation


def clause_accepts(
    by_relation: dict[str, list[dict]], contract_id: str, allowed_kinds: set[str]
) -> set[str]:
    accepted: set[str] = set()
    for item in by_relation.get("clause_kind_judgment", []):
        values = item["values"]
        if values.get("contract") != contract_id:
            continue
        if item["disposition"] != "ACCEPT":
            continue
        kind = values.get("clause_kind", "")
        if kind in allowed_kinds:
            accepted.add(kind)
    return accepted


def contract_is_mechanically_inactive(db: sqlite3.Connection, contract_id: str) -> bool:
    row = db.execute(
        "SELECT expiry_date FROM contract_term WHERE contract_id = ?",
        (contract_id,),
    ).fetchone()
    if row is None:
        return False
    expiry = str(row["expiry_date"] or "").strip()
    return bool(expiry)


def billing_contract_disposition(
    db: sqlite3.Connection, billed_name: str, contract_id: str
) -> str | None:
    left = f"billing:{billed_name}"
    row = db.execute(
        "SELECT disposition FROM identity_judgment WHERE left = ? AND right = ?",
        (left, contract_id),
    ).fetchone()
    if row is not None:
        return str(row["disposition"])
    row = db.execute(
        "SELECT disposition FROM identity_judgment WHERE left = ? AND right = ?",
        (contract_id, left),
    ).fetchone()
    if row is not None:
        return str(row["disposition"])
    return None


def candidate_contract_for_billing(
    db: sqlite3.Connection, billed_name: str
) -> str | None:
    left = f"billing:{billed_name}"
    rows = db.execute(
        "SELECT right FROM reconciliation_link WHERE left = ? AND right LIKE 'contract:%'",
        (left,),
    ).fetchall()
    if len(rows) == 1:
        return str(rows[0]["right"])
    return None


def derive_purpose_a(db: sqlite3.Connection, by_relation: dict[str, list[dict]]) -> dict:
    contract = load_purpose_contract("a")
    allowed_kinds = set(contract["allowed_kinds"])
    disposition_map = contract["disposition_mapping"]

    invoices: list[dict] = []
    for row in db.execute(
        "SELECT invoice_id, billed_name, amount, currency, period, status "
        "FROM invoice_record ORDER BY invoice_id"
    ):
        contract_id = candidate_contract_for_billing(db, str(row["billed_name"]))
        if contract_id is None:
            continue
        if contract_is_mechanically_inactive(db, contract_id):
            continue
        if not clause_accepts(by_relation, contract_id, allowed_kinds):
            continue

        identity = billing_contract_disposition(db, str(row["billed_name"]), contract_id)
        if identity == "DISTINCT":
            continue
        if identity not in disposition_map:
            continue

        invoices.append(
            {
                "invoice_id": strip_prefix(str(row["invoice_id"]), "invoice"),
                "billed_name": str(row["billed_name"]),
                "amount": float(row["amount"]),
                "currency": str(row["currency"]),
                "period": str(row["period"]),
                "status": str(row["status"]),
                "contract_id": strip_prefix(contract_id, "contract"),
                "association": disposition_map[identity],
            }
        )

    return {"purpose": "contractual_revenue_exposure", "invoices": invoices}


def derive_purpose_b(db: sqlite3.Connection) -> dict:
    contract = load_purpose_contract("b")
    disposition_map = contract["disposition_mapping"]

    links: list[dict] = []
    for row in db.execute(
        "SELECT rl.left, rl.right, ij.disposition "
        "FROM reconciliation_link rl "
        "JOIN identity_judgment ij "
        "ON rl.left = ij.left AND rl.right = ij.right "
        "ORDER BY rl.left, rl.right"
    ):
        disposition = str(row["disposition"])
        epistemic = disposition_map.get(disposition, disposition)
        links.append(
            {
                "left": str(row["left"]),
                "right": str(row["right"]),
                "epistemic": epistemic,
            }
        )

    return {"purpose": "counterparty_reconciliation", "links": links}


def open_invoices_for_contract(
    db: sqlite3.Connection, contract_id: str
) -> list[tuple[str, str, str]]:
    """Return (invoice_id, billed_name, identity_disposition) for open invoices."""
    results: list[tuple[str, str, str]] = []
    for row in db.execute(
        "SELECT ir.invoice_id, ir.billed_name "
        "FROM invoice_record ir "
        "JOIN open_invoice oi ON ir.invoice_id = oi.invoice_id"
    ):
        billed_name = str(row["billed_name"])
        identity = billing_contract_disposition(db, billed_name, contract_id)
        results.append((str(row["invoice_id"]), billed_name, identity or "UNRESOLVED"))
    return results


def derive_purpose_c(db: sqlite3.Connection, by_relation: dict[str, list[dict]]) -> dict:
    contract = load_purpose_contract("c")
    allowed_kinds = set(contract["allowed_kinds"])

    candidate_contracts: set[str] = set()
    for row in db.execute("SELECT contract_id FROM contract_record"):
        contract_id = str(row["contract_id"])
        if contract_is_mechanically_inactive(db, contract_id):
            continue
        obligations = clause_accepts(by_relation, contract_id, allowed_kinds)
        open_rows = open_invoices_for_contract(db, contract_id)
        linked_open = [
            item
            for item in open_rows
            if candidate_contract_for_billing(db, item[1]) == contract_id
        ]
        if obligations or linked_open:
            candidate_contracts.add(contract_id)

    dependencies: list[dict] = []
    for contract_id in sorted(candidate_contracts):
        obligations = sorted(clause_accepts(by_relation, contract_id, allowed_kinds))
        open_rows = [
            item
            for item in open_invoices_for_contract(db, contract_id)
            if candidate_contract_for_billing(db, item[1]) == contract_id
        ]

        same_entity_opens = [
            invoice_id
            for invoice_id, billed_name, identity in open_rows
            if identity == "SAME_ENTITY"
        ]
        has_unresolved_identity = any(
            identity == "UNRESOLVED"
            for _invoice_id, _billed_name, identity in open_rows
        )

        open_ids = sorted(
            strip_prefix(invoice_id, "invoice") for invoice_id, _billed_name, _identity in open_rows
        )
        if obligations and same_entity_opens and not has_unresolved_identity:
            counterparty = f"billing:{open_rows[0][1]}"
            status = "dependent"
        else:
            counterparty = (
                f"billing:{open_rows[0][1]}"
                if open_rows
                else f"contract:{strip_prefix(contract_id, 'contract')}"
            )
            status = "unresolved"

        dependencies.append(
            {
                "counterparty": counterparty,
                "contract_id": strip_prefix(contract_id, "contract"),
                "open_invoice_ids": open_ids,
                "obligation_kinds": obligations,
                "status": status,
            }
        )

    return {"purpose": "commercial_dependency", "dependencies": dependencies}


def write_output(purpose_key: str, payload: dict) -> Path:
    output_path = ROOT / "purpose_ir" / purpose_key / "output.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    return output_path


def main() -> None:
    world_path = find_world()
    db = connect_world(world_path)
    try:
        by_relation = index_dispositions(load_dispositions())

        outputs = {
            "a": derive_purpose_a(db, by_relation),
            "b": derive_purpose_b(db),
            "c": derive_purpose_c(db, by_relation),
        }
        for key, payload in outputs.items():
            path = write_output(key, payload)
            print(f"wrote {path.relative_to(ROOT)} ({len(list(payload.values())[1])} rows)")
    finally:
        db.close()


if __name__ == "__main__":
    main()
