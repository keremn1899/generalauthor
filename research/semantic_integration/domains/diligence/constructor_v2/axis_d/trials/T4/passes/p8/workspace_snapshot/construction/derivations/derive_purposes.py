#!/usr/bin/env python3
"""Compile Purpose A/B/C IR from world.sqlite and purpose-scoped dispositions."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORLD_PATHS = [ROOT / "06_world" / "world.sqlite", ROOT / "world" / "world.sqlite"]
DISPOSITIONS_PATH = ROOT / "05_dispositions.json"
CONTRACTS_DIR = ROOT / "contracts"
OUTPUT_DIR = ROOT / "purpose_ir"

CLASS_RANK = {"crm": 0, "billing": 1, "contract": 2, "registry": 3}


def resolve_world_path() -> Path:
    for path in WORLD_PATHS:
        if path.is_file():
            return path
    raise FileNotFoundError("world.sqlite not found under 06_world/ or world/")


def load_contract(purpose_key: str) -> dict:
    with (CONTRACTS_DIR / f"purpose_{purpose_key}.json").open(encoding="utf-8") as handle:
        return json.load(handle)


def load_dispositions() -> list[dict]:
    with DISPOSITIONS_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def class_rank(identifier: str) -> int:
    prefix = identifier.split(":", 1)[0]
    return CLASS_RANK.get(prefix, 99)


def orient_pair(left: str, right: str) -> tuple[str, str]:
    if class_rank(left) < class_rank(right):
        return left, right
    if class_rank(right) < class_rank(left):
        return right, left
    return (left, right) if left <= right else (right, left)


def strip_invoice(value: str) -> str:
    return value.removeprefix("invoice:")


def strip_contract(value: str) -> str:
    return value.removeprefix("contract:")


def disposition_index(dispositions: list[dict]) -> dict[tuple[str, ...], str]:
    index: dict[tuple[str, ...], str] = {}
    for item in dispositions:
        relation = item["relation"]
        values = item["values"]
        if relation == "identity_judgment":
            left, right = orient_pair(values["left"], values["right"])
            key = (relation, left, right)
        elif relation in {
            "active_contract_judgment",
            "acquisition_clause_judgment",
            "obligation_kind_judgment",
        }:
            parts = [relation]
            for field in sorted(values):
                parts.append(f"{field}={values[field]}")
            key = tuple(parts)
        else:
            continue
        index[key] = item["disposition"]
    return index


def identity_disposition(
    index: dict[tuple[str, ...], str], left: str, right: str
) -> str | None:
    oriented = orient_pair(left, right)
    return index.get(("identity_judgment", oriented[0], oriented[1]))


def active_contract_disposition(index: dict[tuple[str, ...], str], contract_id: str) -> str | None:
    key = ("active_contract_judgment", f"contract={contract_id}")
    disposition = index.get(key)
    if disposition == "ACCEPT":
        return "ACTIVE"
    if disposition == "REJECT":
        return "INACTIVE"
    return disposition


def acquisition_accept_kinds(
    index: dict[tuple[str, ...], str], contract_id: str, allowed_kinds: set[str]
) -> set[str]:
    accepted: set[str] = set()
    for kind in allowed_kinds:
        key = (
            "acquisition_clause_judgment",
            f"contract={contract_id}",
            f"kind={kind}",
        )
        if index.get(key) == "ACCEPT":
            accepted.add(kind)
    return accepted


def obligation_accept_kinds(
    index: dict[tuple[str, ...], str], contract_id: str, allowed_kinds: set[str]
) -> set[str]:
    accepted: set[str] = set()
    for kind in allowed_kinds:
        key = (
            "obligation_kind_judgment",
            f"contract={contract_id}",
            f"kind={kind}",
        )
        if index.get(key) == "ACCEPT":
            accepted.add(kind)
    return accepted


def load_world() -> sqlite3.Connection:
    conn = sqlite3.connect(resolve_world_path())
    conn.row_factory = sqlite3.Row
    view = conn.execute("SELECT view_id FROM _tv_view WHERE singleton = 1").fetchone()
    if view is None or view["view_id"] != "diligence-world":
        raise RuntimeError("world.sqlite is not the diligence-world TaskView")
    return conn


def fetch_rows(conn: sqlite3.Connection, sql: str) -> list[sqlite3.Row]:
    return list(conn.execute(sql))


def legal_name_variants(conn: sqlite3.Connection) -> set[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    for row in fetch_rows(conn, "SELECT left, right FROM legal_name_variant"):
        left, right = row["left"], row["right"]
        pairs.add((left, right))
        pairs.add((right, left))
    return pairs


def names_match(variants: set[tuple[str, str]], left: str, right: str) -> bool:
    return (left, right) in variants or left == right


def invoice_contract_link(
    *,
    billed_name: str,
    contract_ref: str,
    counterparty_name: str,
    variants: set[tuple[str, str]],
    identity_index: dict[tuple[str, ...], str],
) -> bool:
    billing_id = f"billing:{billed_name}"
    contract_id = contract_ref if contract_ref.startswith("contract:") else f"contract:{contract_ref}"
    if identity_disposition(identity_index, billing_id, contract_id) is not None:
        return True
    return names_match(variants, billed_name, counterparty_name)


def association_for_pair(
    *,
    billed_name: str,
    contract_ref: str,
    mapping: dict[str, str],
    identity_index: dict[tuple[str, ...], str],
) -> str:
    billing_id = f"billing:{billed_name}"
    contract_id = contract_ref if contract_ref.startswith("contract:") else f"contract:{contract_ref}"
    disposition = identity_disposition(identity_index, billing_id, contract_id)
    if disposition == "SAME_ENTITY":
        return mapping["SAME_ENTITY"]
    return mapping.get("UNRESOLVED", "unresolved")


def derive_purpose_a(
    conn: sqlite3.Connection,
    index: dict[tuple[str, ...], str],
    contract_spec: dict,
) -> dict:
    variants = legal_name_variants(conn)
    allowed_kinds = set(contract_spec["allowed_kinds"])
    mapping = contract_spec["disposition_mapping"]

    invoices = fetch_rows(
        conn,
        """
        SELECT invoice, invoice_id, billed_name, amount, currency, period, status
        FROM invoice_record
        ORDER BY invoice_id
        """,
    )
    contracts = fetch_rows(
        conn,
        """
        SELECT contract, contract_id, counterparty_name
        FROM contract_record
        ORDER BY contract_id
        """,
    )

    rows: list[dict] = []
    for invoice in invoices:
        for contract in contracts:
            contract_ref = contract["contract"]
            active = active_contract_disposition(index, contract_ref)
            if active != "ACTIVE":
                continue
            if not acquisition_accept_kinds(index, contract_ref, allowed_kinds):
                continue
            if not invoice_contract_link(
                billed_name=invoice["billed_name"],
                contract_ref=contract_ref,
                counterparty_name=contract["counterparty_name"],
                variants=variants,
                identity_index=index,
            ):
                continue
            rows.append(
                {
                    "invoice_id": strip_invoice(invoice["invoice_id"]),
                    "billed_name": invoice["billed_name"],
                    "amount": invoice["amount"],
                    "currency": invoice["currency"],
                    "period": invoice["period"],
                    "status": invoice["status"],
                    "contract_id": contract["contract_id"],
                    "association": association_for_pair(
                        billed_name=invoice["billed_name"],
                        contract_ref=contract_ref,
                        mapping=mapping,
                        identity_index=index,
                    ),
                }
            )

    rows.sort(key=lambda row: row["invoice_id"])
    return {"purpose": "contractual_revenue_exposure", "invoices": rows}


def derive_purpose_b(
    conn: sqlite3.Connection,
    index: dict[tuple[str, ...], str],
    contract_spec: dict,
) -> dict:
    mapping = contract_spec["disposition_mapping"]
    links: list[dict] = []
    for row in fetch_rows(conn, "SELECT left, right FROM identity_judgment ORDER BY left, right"):
        left, right = orient_pair(row["left"], row["right"])
        disposition = identity_disposition(index, left, right)
        if disposition is None:
            disposition = "UNRESOLVED"
        epistemic = mapping.get(disposition, disposition)
        links.append({"left": left, "right": right, "epistemic": epistemic})
    links.sort(key=lambda item: (item["left"], item["right"]))
    return {"purpose": "counterparty_reconciliation", "links": links}


def billing_for_contract(
    conn: sqlite3.Connection,
    *,
    contract_ref: str,
    counterparty_name: str,
    variants: set[tuple[str, str]],
    identity_index: dict[tuple[str, ...], str],
) -> str | None:
    contract_id = (
        contract_ref if contract_ref.startswith("contract:") else f"contract:{contract_ref}"
    )
    for row in fetch_rows(conn, "SELECT billed_name FROM invoice_record ORDER BY invoice_id"):
        billed_name = row["billed_name"]
        if invoice_contract_link(
            billed_name=billed_name,
            contract_ref=contract_id,
            counterparty_name=counterparty_name,
            variants=variants,
            identity_index=identity_index,
        ):
            return f"billing:{billed_name}"

    for row in fetch_rows(conn, "SELECT left, right FROM identity_judgment"):
        if row["left"] == contract_id and row["right"].startswith("billing:"):
            return row["right"]
        if row["right"] == contract_id and row["left"].startswith("billing:"):
            return row["left"]

    for row in fetch_rows(conn, "SELECT DISTINCT billed_name FROM invoice_record"):
        billed_name = row["billed_name"]
        if names_match(variants, billed_name, counterparty_name):
            return f"billing:{billed_name}"
    return None


def open_invoices_for_contract(
    conn: sqlite3.Connection,
    *,
    contract_ref: str,
    counterparty_name: str,
    variants: set[tuple[str, str]],
    identity_index: dict[tuple[str, ...], str],
) -> list[str]:
    open_rows = fetch_rows(
        conn,
        """
        SELECT ir.invoice_id, ir.billed_name
        FROM open_invoice oi
        JOIN invoice_record ir ON ir.invoice = oi.invoice_id
        ORDER BY ir.invoice_id
        """,
    )
    linked: list[str] = []
    for row in open_rows:
        if invoice_contract_link(
            billed_name=row["billed_name"],
            contract_ref=contract_ref,
            counterparty_name=counterparty_name,
            variants=variants,
            identity_index=identity_index,
        ):
            linked.append(strip_invoice(row["invoice_id"]))
    return linked


def current_relationship_holds(
    *,
    open_invoice_ids: list[str],
    obligation_kinds: set[str],
) -> bool:
    if open_invoice_ids:
        return True
    return bool(obligation_kinds & {"auto_renewal", "rolling_term"})


def dependency_status(
    *,
    billed_name: str | None,
    contract_ref: str,
    mapping: dict[str, str],
    identity_index: dict[tuple[str, ...], str],
    current_relationship: bool,
    qualifying_obligations: bool,
) -> str:
    if not current_relationship or not qualifying_obligations:
        return mapping.get("UNRESOLVED", "unresolved")
    if billed_name is None:
        return mapping.get("UNRESOLVED", "unresolved")
    disposition = identity_disposition(
        identity_index, f"billing:{billed_name}", contract_ref
    )
    if disposition == "SAME_ENTITY":
        return mapping.get("SAME_ENTITY", "dependent")
    return mapping.get("UNRESOLVED", "unresolved")


def derive_purpose_c(
    conn: sqlite3.Connection,
    index: dict[tuple[str, ...], str],
    contract_spec: dict,
) -> dict:
    variants = legal_name_variants(conn)
    allowed_kinds = set(contract_spec["allowed_kinds"])
    mapping = contract_spec["disposition_mapping"]

    dependencies: list[dict] = []
    for contract in fetch_rows(
        conn,
        "SELECT contract, contract_id, counterparty_name FROM contract_record ORDER BY contract_id",
    ):
        contract_ref = contract["contract"]
        if active_contract_disposition(index, contract_ref) != "ACTIVE":
            continue
        obligation_kinds = sorted(
            obligation_accept_kinds(index, contract_ref, allowed_kinds)
        )
        if not obligation_kinds:
            continue

        counterparty = billing_for_contract(
            conn,
            contract_ref=contract_ref,
            counterparty_name=contract["counterparty_name"],
            variants=variants,
            identity_index=index,
        )
        billed_name = counterparty.removeprefix("billing:") if counterparty else None
        open_invoice_ids = open_invoices_for_contract(
            conn,
            contract_ref=contract_ref,
            counterparty_name=contract["counterparty_name"],
            variants=variants,
            identity_index=index,
        )
        current_relationship = current_relationship_holds(
            open_invoice_ids=open_invoice_ids,
            obligation_kinds=set(obligation_kinds),
        )
        status = dependency_status(
            billed_name=billed_name,
            contract_ref=contract_ref,
            mapping=mapping,
            identity_index=index,
            current_relationship=current_relationship,
            qualifying_obligations=bool(obligation_kinds),
        )
        if counterparty is None:
            counterparty = contract_ref
        dependencies.append(
            {
                "counterparty": counterparty,
                "contract_id": contract["contract_id"],
                "open_invoice_ids": open_invoice_ids,
                "obligation_kinds": obligation_kinds,
                "status": status,
            }
        )

    dependencies.sort(key=lambda row: row["contract_id"])
    return {"purpose": "commercial_dependency", "dependencies": dependencies}


def write_output(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def main() -> None:
    dispositions = load_dispositions()
    index = disposition_index(dispositions)
    conn = load_world()
    try:
        purpose_a = derive_purpose_a(conn, index, load_contract("a"))
        purpose_b = derive_purpose_b(conn, index, load_contract("b"))
        purpose_c = derive_purpose_c(conn, index, load_contract("c"))
    finally:
        conn.close()

    write_output(OUTPUT_DIR / "a" / "output.json", purpose_a)
    write_output(OUTPUT_DIR / "b" / "output.json", purpose_b)
    write_output(OUTPUT_DIR / "c" / "output.json", purpose_c)


if __name__ == "__main__":
    main()
