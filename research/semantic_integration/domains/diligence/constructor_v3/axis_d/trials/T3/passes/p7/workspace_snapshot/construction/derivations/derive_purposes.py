#!/usr/bin/env python3
"""Pass P7 derivation compiler: world.sqlite -> purpose_ir/{a,b,c}/output.json."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORLD_CANDIDATES = (ROOT / "06_world" / "world.sqlite", ROOT / "world" / "world.sqlite")
OUTPUT_PATHS = {
    "a": ROOT / "purpose_ir" / "a" / "output.json",
    "b": ROOT / "purpose_ir" / "b" / "output.json",
    "c": ROOT / "purpose_ir" / "c" / "output.json",
}

ACQUISITION_KINDS = (
    "change_of_control_consent",
    "change_of_control_termination",
    "assignment_notice_or_consent",
    "assignment_consent",
    "assignment_notice",
    "assignment_competitor_prohibition",
    "competitor_assignment_prohibition",
)
OBLIGATION_KINDS = ("auto_renewal", "exclusivity", "rolling_term")
CONTINUING_OBLIGATION_KINDS = ("auto_renewal", "rolling_term")


def resolve_world_path() -> Path:
    for candidate in WORLD_CANDIDATES:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("world.sqlite not found under 06_world/ or world/")


def connect_world(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def strip_prefix(value: str, prefix: str) -> str:
    text = str(value or "")
    needle = f"{prefix}:"
    return text[len(needle) :] if text.startswith(needle) else text


def contract_is_active(conn: sqlite3.Connection, contract: str) -> bool:
    row = conn.execute(
        """
        SELECT disposition
        FROM contract_liveness_judgment
        WHERE contract = ?
        ORDER BY CASE disposition
            WHEN 'ACTIVE' THEN 0
            WHEN 'INACTIVE' THEN 1
            ELSE 2
        END
        LIMIT 1
        """,
        (contract,),
    ).fetchone()
    if row and row["disposition"] == "ACTIVE":
        return True
    if row and row["disposition"] == "INACTIVE":
        return False

    schedule = conn.execute(
        """
        SELECT expiry_date
        FROM source_contract_schedule
        WHERE contract = ?
        LIMIT 1
        """,
        (contract,),
    ).fetchone()
    expiry = (schedule["expiry_date"] if schedule else "") or ""
    if "not renewed" in expiry.lower():
        return False
    return True


def contract_has_acquisition_clause(conn: sqlite3.Connection, contract: str) -> bool:
    row = conn.execute(
        """
        SELECT 1
        FROM acquisition_clause_judgment
        WHERE contract = ?
          AND clause_kind IN ({})
          AND disposition = 'ACCEPT'
        LIMIT 1
        """.format(",".join("?" * len(ACQUISITION_KINDS))),
        (contract, *ACQUISITION_KINDS),
    ).fetchone()
    return row is not None


def map_association(disposition: str | None) -> str:
    if disposition == "asserted":
        return "asserted"
    return "unresolved"


def identity_disposition(
    conn: sqlite3.Connection, left: str, right: str
) -> str | None:
    row = conn.execute(
        """
        SELECT disposition
        FROM identity_judgment
        WHERE (left = ? AND right = ?)
           OR (left = ? AND right = ?)
        ORDER BY CASE disposition
            WHEN 'SAME_ENTITY' THEN 0
            WHEN 'DISTINCT' THEN 1
            WHEN 'UNRESOLVED' THEN 2
            ELSE 3
        END
        LIMIT 1
        """,
        (left, right, right, left),
    ).fetchone()
    if row is None:
        return None
    return row["disposition"] or None


def derive_purpose_a(conn: sqlite3.Connection) -> dict:
    rows = conn.execute(
        """
        SELECT
            si.invoice_id,
            si.billed_name,
            si.amount,
            si.currency,
            si.period,
            si.status,
            sc.contract_id,
            ica.disposition AS association_disposition
        FROM source_invoice si
        JOIN invoice_contract_association ica ON ica.invoice = si.invoice
        JOIN source_contract sc ON sc.contract = ica.contract
        """
    ).fetchall()

    invoices: list[dict] = []
    for row in rows:
        contract = f"contract:{row['contract_id']}"
        if not contract_is_active(conn, contract):
            continue
        if not contract_has_acquisition_clause(conn, contract):
            continue
        association = map_association(row["association_disposition"])
        invoices.append(
            {
                "invoice_id": row["invoice_id"],
                "billed_name": row["billed_name"],
                "amount": row["amount"],
                "currency": row["currency"],
                "period": row["period"],
                "status": row["status"],
                "contract_id": row["contract_id"],
                "association": association,
            }
        )

    invoices.sort(key=lambda item: item["invoice_id"])
    return {"purpose": "contractual_revenue_exposure", "invoices": invoices}


def derive_purpose_b(conn: sqlite3.Connection) -> dict:
    mapping = {
        "SAME_ENTITY": "SAME_ENTITY",
        "DISTINCT": "DISTINCT",
        "UNRESOLVED": "UNRESOLVED",
        "REJECT": "DISTINCT",
    }
    rows = conn.execute(
        """
        SELECT left, right, disposition
        FROM identity_judgment
        WHERE disposition != ''
        ORDER BY left ASC, right ASC
        """
    ).fetchall()
    links = [
        {
            "left": row["left"],
            "right": row["right"],
            "epistemic": mapping.get(row["disposition"], "UNRESOLVED"),
        }
        for row in rows
    ]
    return {"purpose": "counterparty_reconciliation", "links": links}


def obligation_kinds_for_contract(conn: sqlite3.Connection, contract: str) -> list[str]:
    rows = conn.execute(
        """
        SELECT clause_kind
        FROM obligation_kind_judgment
        WHERE contract = ?
          AND clause_kind IN ('auto_renewal', 'exclusivity', 'rolling_term')
          AND disposition = 'ACCEPT'
        ORDER BY clause_kind ASC
        """,
        (contract,),
    ).fetchall()
    return [row["clause_kind"] for row in rows]


def open_invoices_for_contract(
    conn: sqlite3.Connection, contract: str
) -> list[str]:
    rows = conn.execute(
        """
        SELECT si.invoice_id, si.billed_name, ica.disposition AS association_disposition
        FROM source_invoice si
        JOIN invoice_contract_association ica ON ica.invoice = si.invoice
        WHERE ica.contract = ?
          AND si.status = 'open'
        """,
        (contract,),
    ).fetchall()
    invoice_ids: list[str] = []
    for row in rows:
        billing_id = f"billing:{row['billed_name']}"
        same_entity = identity_disposition(conn, billing_id, contract)
        if same_entity != "SAME_ENTITY":
            continue
        invoice_ids.append(row["invoice_id"])
    invoice_ids.sort()
    return invoice_ids


def association_blocks_dependency(
    conn: sqlite3.Connection, contract: str, open_invoice_ids: list[str]
) -> bool:
    if not open_invoice_ids:
        return False
    rows = conn.execute(
        """
        SELECT ica.disposition
        FROM source_invoice si
        JOIN invoice_contract_association ica ON ica.invoice = si.invoice
        WHERE ica.contract = ?
          AND si.status = 'open'
        """,
        (contract,),
    ).fetchall()
    for row in rows:
        if row["disposition"] not in ("asserted",):
            return True
    return False


def identity_blocks_dependency(
    conn: sqlite3.Connection,
    counterparty: str,
    contract: str,
    billed_names: list[str],
) -> bool:
    if identity_disposition(conn, counterparty, contract) == "UNRESOLVED":
        return True
    for billed_name in billed_names:
        billing_id = f"billing:{billed_name}"
        if identity_disposition(conn, counterparty, billing_id) == "UNRESOLVED":
            return True
        if identity_disposition(conn, billing_id, contract) == "UNRESOLVED":
            return True
    return False


def derive_purpose_c(conn: sqlite3.Connection) -> dict:
    candidates = conn.execute(
        """
        SELECT DISTINCT counterparty, contract
        FROM commercial_dependency_judgment
        """
    ).fetchall()

    dependencies: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for row in candidates:
        counterparty = row["counterparty"]
        contract = row["contract"]
        key = (counterparty, contract)
        if key in seen:
            continue
        seen.add(key)

        if not contract_is_active(conn, contract):
            continue

        kinds = obligation_kinds_for_contract(conn, contract)
        if not kinds:
            continue

        contract_id = strip_prefix(contract, "contract")
        open_invoice_ids = open_invoices_for_contract(conn, contract)
        billed_names = [
            item["billed_name"]
            for item in conn.execute(
                """
                SELECT DISTINCT si.billed_name
                FROM source_invoice si
                JOIN invoice_contract_association ica ON ica.invoice = si.invoice
                WHERE ica.contract = ?
                """,
                (contract,),
            ).fetchall()
        ]

        prong_obligation = bool(kinds)
        prong_current = bool(open_invoice_ids) or (
            any(kind in CONTINUING_OBLIGATION_KINDS for kind in kinds)
        )
        blocked = identity_blocks_dependency(
            conn, counterparty, contract, billed_names
        ) or association_blocks_dependency(conn, contract, open_invoice_ids)

        if prong_obligation and prong_current and not blocked:
            status = "dependent"
        else:
            status = "unresolved"

        dependencies.append(
            {
                "counterparty": counterparty,
                "contract_id": contract_id,
                "open_invoice_ids": open_invoice_ids,
                "obligation_kinds": kinds,
                "status": status,
            }
        )

    dependencies.sort(key=lambda item: item["contract_id"])
    return {"purpose": "commercial_dependency", "dependencies": dependencies}


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    world_path = resolve_world_path()
    conn = connect_world(world_path)
    try:
        outputs = {
            "a": derive_purpose_a(conn),
            "b": derive_purpose_b(conn),
            "c": derive_purpose_c(conn),
        }
    finally:
        conn.close()

    for key, payload in outputs.items():
        write_json(OUTPUT_PATHS[key], payload)
        print(f"wrote {OUTPUT_PATHS[key]}")


if __name__ == "__main__":
    main()
