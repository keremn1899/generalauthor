#!/usr/bin/env python3
"""P7 derivation compiler: materialize purpose_ir outputs from world.sqlite and P5 dispositions."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DISPOSITIONS_PATH = ROOT / "05_dispositions.json"
VIEW_ID = "diligence-world"

ACQUISITION_CLAUSE_RELATIONS = (
    "contract_coc_consent_required",
    "contract_coc_termination_permitted",
    "contract_assignment_consent_required",
    "contract_assignment_notice_required",
    "contract_assignment_competitor_prohibited",
)

OBLIGATION_KIND_SOURCES = {
    "contract_exclusivity_present": "exclusivity",
    "contract_auto_renewal_present": "auto_renewal",
    "contract_rolling_term_present": "rolling_term",
}


def find_world_db() -> Path:
    for candidate in (ROOT / "06_world" / "world.sqlite", ROOT / "world" / "world.sqlite"):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("world.sqlite not found under 06_world/ or world/")


def load_dispositions() -> list[dict]:
    with DISPOSITIONS_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def disposition_index(dispositions: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for item in dispositions:
        grouped.setdefault(item["relation"], []).append(item)
    return grouped


def contract_id_from_grounding(grounding: list[dict]) -> str | None:
    for entry in grounding:
        path = entry.get("source_path", "")
        if path.startswith("sources/contracts/"):
            return Path(path).stem
    return None


def materialize_invoice_contract_associations(
    dispositions: list[dict],
) -> list[dict[str, str]]:
    """Semantic premise: asserted invoice-to-contract links from P5 dispositions."""
    rows: list[dict[str, str]] = []
    for item in dispositions:
        if item["relation"] != "invoice_contract_association":
            continue
        invoice_ref = item["values"]["invoice"]
        contract_id = contract_id_from_grounding(item.get("grounding", []))
        if contract_id is None:
            raise ValueError(
                f"invoice_contract_association {item['obligation_id']} lacks contract grounding"
            )
        association = "asserted" if item["disposition"] == "ACCEPT" else "unresolved"
        rows.append(
            {
                "invoice": invoice_ref,
                "contract_id": contract_id,
                "association": association,
            }
        )
    return rows


def materialize_counterparty_identity_epistemic(
    dispositions: list[dict],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for item in dispositions:
        if item["relation"] != "counterparty_identity_epistemic":
            continue
        rows.append(
            {
                "left": item["values"]["left"],
                "right": item["values"]["right"],
                "epistemic": item["disposition"],
            }
        )
    return sorted(rows, key=lambda row: (row["left"], row["right"]))


def materialize_commercial_dependency_status(
    dispositions: list[dict],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for item in dispositions:
        if item["relation"] != "commercial_dependency_status":
            continue
        status = "dependent" if item["disposition"] == "ACCEPT" else "unresolved"
        rows.append(
            {
                "counterparty": item["values"]["counterparty"],
                "contract_id": item["values"]["contract_id"],
                "status": status,
            }
        )
    return rows


def query_rows(conn: sqlite3.Connection, sql: str) -> list[sqlite3.Row]:
    conn.row_factory = sqlite3.Row
    return list(conn.execute(sql))


def derive_contract_acquisition_relevant(conn: sqlite3.Connection) -> dict[str, bool]:
    relevant: dict[str, bool] = {}
    for relation in ACQUISITION_CLAUSE_RELATIONS:
        for row in query_rows(
            conn, f"SELECT contract_id FROM {relation} WHERE present = 1"
        ):
            contract_ref = row["contract_id"]
            text_id = conn.execute(
                "SELECT contract_id FROM contract_document WHERE contract_ref_id = ?",
                (contract_ref,),
            ).fetchone()
            if text_id is None:
                continue
            relevant[text_id["contract_id"]] = True
    return relevant


def derive_contract_active_for_diligence(conn: sqlite3.Connection) -> dict[str, bool]:
    active: dict[str, bool] = {}
    contracts = query_rows(
        conn,
        """
        SELECT cd.contract_id, dk.kind
        FROM contract_document cd
        LEFT JOIN contract_document_kind dk ON dk.contract_id = cd.contract_ref_id
        """,
    )
    expired_refs = {
        row["contract_id"]
        for row in query_rows(
            conn, "SELECT contract_id FROM contract_recorded_expired WHERE expired = 1"
        )
    }
    for row in contracts:
        contract_id = row["contract_id"]
        contract_ref = conn.execute(
            "SELECT contract_ref_id FROM contract_document WHERE contract_id = ?",
            (contract_id,),
        ).fetchone()["contract_ref_id"]
        if row["kind"] == "SOW" and contract_ref in expired_refs:
            active[contract_id] = False
        else:
            active[contract_id] = True
    return active


def derive_purpose_a(
    conn: sqlite3.Connection,
    associations: list[dict[str, str]],
) -> dict:
    acquisition_relevant = derive_contract_acquisition_relevant(conn)
    active_for_diligence = derive_contract_active_for_diligence(conn)
    invoices = query_rows(conn, "SELECT * FROM invoice_fields ORDER BY invoice_id")

    assoc_by_invoice = {row["invoice"]: row for row in associations}
    output_rows = []
    for invoice in invoices:
        invoice_ref = invoice["invoice_ref_id"]
        assoc = assoc_by_invoice.get(invoice_ref)
        if assoc is None:
            continue
        contract_id = assoc["contract_id"]
        association = assoc["association"]
        if association == "unresolved":
            include = True
        elif association == "asserted":
            include = (
                acquisition_relevant.get(contract_id, False)
                and active_for_diligence.get(contract_id, False)
            )
        else:
            include = False
        if not include:
            continue
        output_rows.append(
            {
                "invoice_id": invoice["invoice_id"],
                "billed_name": invoice["billed_name"],
                "amount": invoice["amount"],
                "currency": invoice["currency"],
                "period": invoice["period"],
                "status": invoice["status"],
                "contract_id": contract_id,
                "association": association,
            }
        )
    return {"purpose": "contractual_revenue_exposure", "invoices": output_rows}


def derive_purpose_b(identity_links: list[dict[str, str]]) -> dict:
    return {
        "purpose": "counterparty_reconciliation",
        "links": [
            {
                "left": row["left"],
                "right": row["right"],
                "epistemic": row["epistemic"],
            }
            for row in identity_links
        ],
    }


def derive_purpose_c(
    conn: sqlite3.Connection,
    dependency_statuses: list[dict[str, str]],
) -> dict:
    obligation_kinds_by_contract: dict[str, list[str]] = {}
    for row in query_rows(conn, "SELECT contract_id, kind FROM contract_obligation_kind"):
        contract_text_id = conn.execute(
            "SELECT contract_id FROM contract_document WHERE contract_ref_id = ?",
            (row["contract_id"],),
        ).fetchone()["contract_id"]
        obligation_kinds_by_contract.setdefault(contract_text_id, []).append(row["kind"])
    for kinds in obligation_kinds_by_contract.values():
        kinds.sort()

    open_invoices = query_rows(
        conn,
        """
        SELECT io.invoice_id AS invoice_ref, inf.invoice_id, inf.billed_name
        FROM invoice_is_open io
        JOIN invoice_fields inf ON inf.invoice_ref_id = io.invoice_id
        """,
    )
    open_by_billed_name: dict[str, list[str]] = {}
    for row in open_invoices:
        billing_id = f"billing:{row['billed_name']}"
        open_by_billed_name.setdefault(billing_id, []).append(row["invoice_id"])
    for invoice_ids in open_by_billed_name.values():
        invoice_ids.sort()

    dependencies = []
    for status_row in sorted(dependency_statuses, key=lambda row: row["contract_id"]):
        counterparty = status_row["counterparty"]
        contract_id = status_row["contract_id"]
        dependencies.append(
            {
                "counterparty": counterparty,
                "contract_id": contract_id,
                "open_invoice_ids": open_by_billed_name.get(counterparty, []),
                "obligation_kinds": obligation_kinds_by_contract.get(contract_id, []),
                "status": status_row["status"],
            }
        )
    return {"purpose": "commercial_dependency", "dependencies": dependencies}


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def main() -> None:
    world_db = find_world_db()
    dispositions = load_dispositions()

    associations = materialize_invoice_contract_associations(dispositions)
    identity_links = materialize_counterparty_identity_epistemic(dispositions)
    dependency_statuses = materialize_commercial_dependency_status(dispositions)

    conn = sqlite3.connect(world_db)
    try:
        view = conn.execute(
            "SELECT view_id FROM _tv_view WHERE singleton = 1"
        ).fetchone()
        if view is None or view[0] != VIEW_ID:
            raise ValueError(f"{world_db} is not a {VIEW_ID!r} TaskView")

        purpose_a = derive_purpose_a(conn, associations)
        purpose_b = derive_purpose_b(identity_links)
        purpose_c = derive_purpose_c(conn, dependency_statuses)
    finally:
        conn.close()

    write_json(ROOT / "purpose_ir" / "a" / "output.json", purpose_a)
    write_json(ROOT / "purpose_ir" / "b" / "output.json", purpose_b)
    write_json(ROOT / "purpose_ir" / "c" / "output.json", purpose_c)

    print(f"Read {world_db}")
    print(f"Loaded {len(dispositions)} dispositions from {DISPOSITIONS_PATH.name}")
    print(f"Wrote {len(purpose_a['invoices'])} purpose A invoices")
    print(f"Wrote {len(purpose_b['links'])} purpose B links")
    print(f"Wrote {len(purpose_c['dependencies'])} purpose C dependencies")


if __name__ == "__main__":
    main()
