#!/usr/bin/env python3
"""Derive Purpose A/B/C JSON outputs from World IR and disposition verdicts."""

from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[2]
DISPOSITIONS_PATH = WORKSPACE / "05_dispositions.json"
VIEW_ID = "diligence-world"


def find_world_db() -> Path:
    for candidate in (
        WORKSPACE / "06_world" / "world.sqlite",
        WORKSPACE / "world" / "world.sqlite",
    ):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("world.sqlite not found under 06_world/ or world/")


def open_world(path: Path) -> sqlite3.Connection:
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    view = db.execute("SELECT view_id FROM _tv_view WHERE singleton = 1").fetchone()
    if view is None or view["view_id"] != VIEW_ID:
        raise RuntimeError(f"{path} is not a {VIEW_ID!r} TaskView database")
    return db


def load_dispositions() -> list[dict]:
    with DISPOSITIONS_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def disposition_rows(dispositions: list[dict], relation: str) -> list[dict]:
    return [row for row in dispositions if row.get("relation") == relation]


def contract_stem(contract_id: str) -> str:
    prefix = "contract:"
    if contract_id.startswith(prefix):
        return contract_id[len(prefix) :]
    return contract_id


def build_purpose_a(db: sqlite3.Connection, dispositions: list[dict]) -> dict:
    invoices = {
        row["invoice_id"]: dict(row)
        for row in db.execute(
            "SELECT invoice_id, billed_name, amount, currency, period, status "
            "FROM source_invoice"
        )
    }

    associations: dict[str, dict[str, str]] = {}
    for row in disposition_rows(dispositions, "invoice_contract_association"):
        values = row["values"]
        inv_id = values["invoice_id"]
        if row["disposition"] == "ACCEPT":
            associations[inv_id] = {
                "contract_id": values["contract_id"],
                "association": "asserted",
            }
        elif row["disposition"] == "UNRESOLVED":
            associations[inv_id] = {
                "contract_id": values.get("contract_id", ""),
                "association": "unresolved",
            }

    active_contracts = {
        row["values"]["contract_id"]
        for row in disposition_rows(dispositions, "contract_active_for_exposure")
        if row["disposition"] == "ACCEPT"
    }
    relevant_contracts = {
        row["values"]["contract_id"]
        for row in disposition_rows(dispositions, "contract_acquisition_relevant_term")
        if row["disposition"] == "ACCEPT"
    }

    output_rows: list[dict] = []
    for inv_id in sorted(invoices):
        assoc = associations.get(inv_id)
        if assoc is None:
            continue
        contract_id = assoc["contract_id"]
        if contract_id not in active_contracts or contract_id not in relevant_contracts:
            continue
        inv = invoices[inv_id]
        output_rows.append(
            {
                "invoice_id": inv_id,
                "billed_name": inv["billed_name"],
                "amount": inv["amount"],
                "currency": inv["currency"],
                "period": inv["period"],
                "status": inv["status"],
                "contract_id": contract_stem(contract_id),
                "association": assoc["association"],
            }
        )

    return {"purpose": "contractual_revenue_exposure", "invoices": output_rows}


def build_purpose_b(dispositions: list[dict]) -> dict:
    links: list[dict] = []
    for row in disposition_rows(dispositions, "counterparty_identity_verdict"):
        values = row["values"]
        links.append(
            {
                "left": values["left"],
                "right": values["right"],
                "epistemic": row["disposition"],
            }
        )
    links.sort(key=lambda item: (item["left"], item["right"]))
    return {"purpose": "counterparty_reconciliation", "links": links}


def identity_lookup(dispositions: list[dict]) -> dict[tuple[str, str], str]:
    lookup: dict[tuple[str, str], str] = {}
    for row in disposition_rows(dispositions, "counterparty_identity_verdict"):
        values = row["values"]
        key = (values["left"], values["right"])
        lookup[key] = row["disposition"]
        reverse = (values["right"], values["left"])
        lookup.setdefault(reverse, row["disposition"])
    return lookup


def build_purpose_c(
    db: sqlite3.Connection, dispositions: list[dict]
) -> dict:
    obligation_kinds: dict[str, list[str]] = defaultdict(list)
    for row in disposition_rows(dispositions, "contract_obligation_kind"):
        if row["disposition"] != "ACCEPT":
            continue
        values = row["values"]
        cid = values["contract_id"]
        kind = values["kind"]
        if kind not in obligation_kinds[cid]:
            obligation_kinds[cid].append(kind)

    associations: dict[tuple[str, str], str] = {}
    for row in disposition_rows(dispositions, "invoice_contract_association"):
        values = row["values"]
        key = (values["invoice_id"], values["contract_id"])
        if row["disposition"] == "ACCEPT":
            associations[key] = "asserted"
        elif row["disposition"] == "UNRESOLVED":
            associations[key] = "unresolved"

    open_invoices = {
        row["invoice_id"]
        for row in db.execute(
            "SELECT invoice_id FROM invoice_is_open WHERE is_open = 1"
        )
    }

    identity = identity_lookup(dispositions)

    dependencies: list[dict] = []
    for row in disposition_rows(dispositions, "commercial_dependency_status"):
        values = row["values"]
        counterparty = values["counterparty"]
        contract_id = values["contract_id"]

        if row["disposition"] == "REJECT":
            continue

        status = "dependent"
        if row["disposition"] != "ACCEPT":
            status = "unresolved"
        elif identity.get((counterparty, contract_id)) == "UNRESOLVED":
            status = "unresolved"
        else:
            for inv_id in open_invoices:
                assoc = associations.get((inv_id, contract_id))
                if assoc == "unresolved":
                    status = "unresolved"
                    break

        kinds = sorted(obligation_kinds.get(contract_id, []))
        invoice_ids: list[str] = []
        if status == "dependent":
            for inv_id in sorted(open_invoices):
                if associations.get((inv_id, contract_id)) == "asserted":
                    invoice_ids.append(inv_id)

        dependencies.append(
            {
                "counterparty": counterparty,
                "contract_id": contract_id,
                "open_invoice_ids": invoice_ids,
                "obligation_kinds": kinds,
                "status": status,
            }
        )

    dependencies.sort(key=lambda item: item["contract_id"])
    return {"purpose": "commercial_dependency", "dependencies": dependencies}


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def main() -> None:
    world_path = find_world_db()
    dispositions = load_dispositions()
    db = open_world(world_path)
    try:
        purpose_a = build_purpose_a(db, dispositions)
        purpose_b = build_purpose_b(dispositions)
        purpose_c = build_purpose_c(db, dispositions)
    finally:
        db.close()

    write_json(WORKSPACE / "purpose_ir" / "a" / "output.json", purpose_a)
    write_json(WORKSPACE / "purpose_ir" / "b" / "output.json", purpose_b)
    write_json(WORKSPACE / "purpose_ir" / "c" / "output.json", purpose_c)


if __name__ == "__main__":
    main()
