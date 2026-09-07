#!/usr/bin/env python3
"""Derive Purpose A/B/C output JSON from compiled world relations."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

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

C_OBLIGATION_KINDS = ("exclusivity", "auto_renewal", "rolling_term")
C_CURRENT_RELATIONSHIP_KINDS = ("auto_renewal", "rolling_term")


def find_world_db() -> Path:
    for candidate in (Path("06_world/world.sqlite"), Path("world/world.sqlite")):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("world.sqlite not found under 06_world/ or world/")


def connect_world(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT view_id FROM _tv_view WHERE singleton = 1"
    ).fetchone()
    if row is None or row["view_id"] != VIEW_ID:
        raise RuntimeError(
            f"{db_path} is not a diligence-world TaskView (view_id={row and row['view_id']!r})"
        )
    return conn


def strip_prefix(value: str, prefix: str) -> str:
    text = str(value)
    if text.startswith(prefix):
        return text[len(prefix) :]
    return text


def identity_lookup(
    conn: sqlite3.Connection, left: str, right: str
) -> str | None:
    row = conn.execute(
        "SELECT disposition FROM identity_judgment WHERE left = ? AND right = ?",
        (left, right),
    ).fetchone()
    if row is None:
        row = conn.execute(
            "SELECT disposition FROM identity_judgment WHERE left = ? AND right = ?",
            (right, left),
        ).fetchone()
    return None if row is None else str(row["disposition"])


def contract_has_clause(
    conn: sqlite3.Connection, contract_ref: str, kinds: tuple[str, ...]
) -> bool:
    placeholders = ",".join("?" for _ in kinds)
    row = conn.execute(
        f"""
        SELECT 1
        FROM contract_clause
        WHERE contract_id = ?
          AND clause_kind IN ({placeholders})
        LIMIT 1
        """,
        (contract_ref, *kinds),
    ).fetchone()
    return row is not None


def contract_clause_kinds(
    conn: sqlite3.Connection, contract_ref: str, kinds: tuple[str, ...]
) -> list[str]:
    placeholders = ",".join("?" for _ in kinds)
    rows = conn.execute(
        f"""
        SELECT clause_kind
        FROM contract_clause
        WHERE contract_id = ?
          AND clause_kind IN ({placeholders})
        ORDER BY clause_kind
        """,
        (contract_ref, *kinds),
    ).fetchall()
    return [str(row["clause_kind"]) for row in rows]


def derive_invoice_contract_associations(conn: sqlite3.Connection) -> list[dict[str, str]]:
    """Purpose A intermediate: asserted vs unresolved invoice-to-contract links."""
    rows = conn.execute(
        """
        SELECT
            si.invoice_id AS invoice_ref,
            si.invoice_id_text,
            si.billed_name,
            sc.contract_id AS contract_ref,
            sc.contract_id_text,
            sc.counterparty_text,
            cas.active
        FROM source_invoice si
        JOIN identity_judgment ij
          ON ij.left = 'billing:' || si.billed_name
         AND ij.right LIKE 'contract:%'
        JOIN source_contract sc ON sc.contract_id = ij.right
        JOIN contract_active_status cas ON cas.contract_id = sc.contract_id
        WHERE cas.active = 1
          AND EXISTS (
            SELECT 1
            FROM contract_clause cc
            WHERE cc.contract_id = sc.contract_id
              AND cc.clause_kind IN (
                'change_of_control_consent',
                'change_of_control_termination',
                'assignment_notice_or_consent',
                'assignment_consent',
                'assignment_notice',
                'assignment_competitor_prohibition',
                'competitor_assignment_prohibition'
              )
          )
        ORDER BY si.invoice_id_text, sc.contract_id_text
        """
    ).fetchall()

    associations: list[dict[str, str]] = []
    for row in rows:
        identity = identity_lookup(
            conn,
            f"billing:{row['billed_name']}",
            str(row["contract_ref"]),
        )
        if identity == "SAME_ENTITY" and row["billed_name"] == row["counterparty_text"]:
            disposition = "asserted"
        else:
            disposition = "unresolved"
        associations.append(
            {
                "invoice": str(row["invoice_ref"]),
                "contract": str(row["contract_ref"]),
                "disposition": disposition,
            }
        )
    return associations


def derive_purpose_a(conn: sqlite3.Connection) -> dict:
    associations = derive_invoice_contract_associations(conn)
    by_invoice: dict[str, dict[str, str]] = {}
    for assoc in associations:
        invoice_ref = assoc["invoice"]
        existing = by_invoice.get(invoice_ref)
        if existing is None or assoc["disposition"] == "asserted":
            by_invoice[invoice_ref] = assoc

    invoices: list[dict] = []
    for invoice_ref, assoc in sorted(
        by_invoice.items(), key=lambda item: strip_prefix(item[0], "billing:")
    ):
        row = conn.execute(
            """
            SELECT invoice_id_text, billed_name, amount, currency, period, status
            FROM source_invoice
            WHERE invoice_id = ?
            """,
            (invoice_ref,),
        ).fetchone()
        if row is None:
            continue
        contract_row = conn.execute(
            "SELECT contract_id_text FROM source_contract WHERE contract_id = ?",
            (assoc["contract"],),
        ).fetchone()
        invoices.append(
            {
                "invoice_id": row["invoice_id_text"],
                "billed_name": row["billed_name"],
                "amount": row["amount"],
                "currency": row["currency"],
                "period": row["period"],
                "status": row["status"],
                "contract_id": contract_row["contract_id_text"],
                "association": assoc["disposition"],
            }
        )

    return {"purpose": "contractual_revenue_exposure", "invoices": invoices}


def derive_purpose_b(conn: sqlite3.Connection) -> dict:
    links: list[dict[str, str]] = []
    candidates = conn.execute(
        """
        SELECT left, right
        FROM identity_link_candidate
        ORDER BY left, right
        """
    ).fetchall()
    for candidate in candidates:
        left = str(candidate["left"])
        right = str(candidate["right"])
        row = conn.execute(
            """
            SELECT disposition
            FROM identity_judgment
            WHERE left = ? AND right = ?
            """,
            (left, right),
        ).fetchone()
        epistemic = "UNRESOLVED" if row is None else str(row["disposition"])
        links.append({"left": left, "right": right, "epistemic": epistemic})
    return {"purpose": "counterparty_reconciliation", "links": links}


def derive_commercial_dependency_judgments(
    conn: sqlite3.Connection,
) -> list[dict]:
    contracts = conn.execute(
        """
        SELECT sc.contract_id AS contract_ref, sc.contract_id_text
        FROM source_contract sc
        JOIN contract_active_status cas
          ON cas.contract_id = sc.contract_id
         AND cas.active = 1
        WHERE EXISTS (
            SELECT 1
            FROM contract_clause cc
            WHERE cc.contract_id = sc.contract_id
              AND cc.clause_kind IN ('exclusivity', 'auto_renewal', 'rolling_term')
        )
        ORDER BY sc.contract_id_text
        """
    ).fetchall()

    judgments: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for contract in contracts:
        contract_ref = str(contract["contract_ref"])
        obligation_kinds = contract_clause_kinds(
            conn, contract_ref, C_OBLIGATION_KINDS
        )
        identity_rows = conn.execute(
            """
            SELECT left, disposition
            FROM identity_judgment
            WHERE right = ?
              AND left LIKE 'billing:%'
            ORDER BY left
            """,
            (contract_ref,),
        ).fetchall()
        for identity_row in identity_rows:
            counterparty = str(identity_row["left"])
            key = (counterparty, contract_ref)
            if key in seen:
                continue
            seen.add(key)
            billed_name = strip_prefix(counterparty, "billing:")
            identity = str(identity_row["disposition"])
            open_rows = conn.execute(
                """
                SELECT oi.invoice_id_text
                FROM open_invoice oi
                JOIN source_invoice si ON si.invoice_id = oi.invoice_id
                WHERE si.billed_name = ?
                ORDER BY oi.invoice_id_text
                """,
                (billed_name,),
            ).fetchall()
            open_invoice_ids = [str(item["invoice_id_text"]) for item in open_rows]
            has_current_relationship = bool(open_invoice_ids) or bool(
                contract_clause_kinds(conn, contract_ref, C_CURRENT_RELATIONSHIP_KINDS)
            )
            if identity != "SAME_ENTITY":
                status = "unresolved"
            elif has_current_relationship and obligation_kinds:
                status = "dependent"
            else:
                continue
            judgments.append(
                {
                    "counterparty": counterparty,
                    "contract": contract_ref,
                    "contract_id": str(contract["contract_id_text"]),
                    "open_invoice_ids": open_invoice_ids,
                    "obligation_kinds": obligation_kinds,
                    "status": status,
                }
            )
    return judgments


def derive_purpose_c(conn: sqlite3.Connection) -> dict:
    dependencies: list[dict] = []
    for judgment in derive_commercial_dependency_judgments(conn):
        dependencies.append(
            {
                "counterparty": judgment["counterparty"],
                "contract_id": judgment["contract_id"],
                "open_invoice_ids": judgment["open_invoice_ids"],
                "obligation_kinds": judgment["obligation_kinds"],
                "status": judgment["status"],
            }
        )
    dependencies.sort(key=lambda row: row["contract_id"])
    return {"purpose": "commercial_dependency", "dependencies": dependencies}


def write_output(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    db_path = find_world_db()
    conn = connect_world(db_path)
    try:
        write_output(Path("purpose_ir/a/output.json"), derive_purpose_a(conn))
        write_output(Path("purpose_ir/b/output.json"), derive_purpose_b(conn))
        write_output(Path("purpose_ir/c/output.json"), derive_purpose_c(conn))
    finally:
        conn.close()


if __name__ == "__main__":
    main()
