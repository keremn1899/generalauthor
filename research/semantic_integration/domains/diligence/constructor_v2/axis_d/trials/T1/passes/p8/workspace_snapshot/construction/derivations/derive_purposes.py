#!/usr/bin/env python3
"""C4 purpose derivation compiler.

Reads compiled WORLD relations from world.sqlite and writes purpose_ir/{a,b,c}/output.json.
Ordinary Python/SQL only; distinguishes required vs optional premises and blocking vs
non-blocking unresolved states per 07_derivations.json.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VIEW_ID = "diligence-world"

PURPOSE_A_KINDS = {
    "change_of_control_consent",
    "change_of_control_termination",
    "assignment_notice_or_consent",
    "assignment_consent",
    "assignment_notice",
    "assignment_competitor_prohibition",
    "competitor_assignment_prohibition",
}

PURPOSE_C_KINDS = {"exclusivity", "auto_renewal", "rolling_term"}

CLASS_RANK = ("billing:", "contract:", "crm:", "registry:")


def resolve_world_db() -> Path:
    for candidate in (ROOT / "06_world" / "world.sqlite", ROOT / "world" / "world.sqlite"):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("world.sqlite not found under 06_world/ or world/")


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    view = conn.execute("SELECT view_id FROM _tv_view WHERE singleton = 1").fetchone()
    if view is None or view["view_id"] != VIEW_ID:
        raise RuntimeError(f"expected view_id={VIEW_ID!r}, got {view}")
    return conn


def disposition_from_grounding(conn: sqlite3.Connection, assertion_id: str) -> str | None:
    row = conn.execute(
        """
        SELECT detail FROM _tv_groundings
        WHERE subject_id = ? AND kind = 'WORLD' AND detail LIKE '%:%'
        """,
        (assertion_id,),
    ).fetchone()
    if row is None:
        return None
    return str(row["detail"]).split(":", 1)[1]


def load_identity_judgments(conn: sqlite3.Connection) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in conn.execute("SELECT _assertion_id, left, right FROM identity_judgment"):
        disp = disposition_from_grounding(conn, row["_assertion_id"])
        if disp is None:
            continue
        rows.append({"left": row["left"], "right": row["right"], "disposition": disp})
    return rows


def load_clause_judgments(conn: sqlite3.Connection) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in conn.execute(
        "SELECT _assertion_id, contract_id, kind FROM contract_clause_judgment"
    ):
        disp = disposition_from_grounding(conn, row["_assertion_id"])
        if disp is None:
            continue
        rows.append(
            {
                "contract_id": row["contract_id"],
                "kind": row["kind"],
                "disposition": disp,
            }
        )
    return rows


def class_rank_prefix(identifier: str) -> int:
    for index, prefix in enumerate(CLASS_RANK):
        if identifier.startswith(prefix):
            return index
    return len(CLASS_RANK)


def orient_class_rank(left: str, right: str, disposition: str) -> tuple[str, str, str]:
    """Canonicalize unordered identity pairs to class_rank orientation."""
    if class_rank_prefix(left) < class_rank_prefix(right) or (
        class_rank_prefix(left) == class_rank_prefix(right) and left < right
    ):
        return left, right, disposition
    return right, left, disposition


def strip_prefix(identifier: str, prefix: str) -> str:
    if identifier.startswith(prefix):
        return identifier[len(prefix) :]
    return identifier


def active_contract_ids(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute(
        """
        SELECT cdk.contract_id
        FROM contract_document_kind cdk
        LEFT JOIN contract_stated_expired cse ON cse.contract_id = cdk.contract_id
        WHERE NOT (cdk.kind = 'sow' AND cse.contract_id IS NOT NULL)
        """
    ).fetchall()
    return {row["contract_id"] for row in rows}


def acquisition_relevant_contract_ids(
    conn: sqlite3.Connection, clause_rows: list[dict[str, str]], active: set[str]
) -> set[str]:
    qualifying: set[str] = set()
    for row in clause_rows:
        if row["contract_id"] not in active:
            continue
        if row["kind"] not in PURPOSE_A_KINDS:
            continue
        if row["disposition"] != "PRESENT":
            continue
        qualifying.add(row["contract_id"])
    return qualifying


def identity_lookup(identity_rows: list[dict[str, str]]) -> dict[tuple[str, str], str]:
    table: dict[tuple[str, str], str] = {}
    for row in identity_rows:
        left, right, disp = orient_class_rank(row["left"], row["right"], row["disposition"])
        table[(left, right)] = disp
        table[(right, left)] = disp
    return table


def identity_between(table: dict[tuple[str, str], str], left: str, right: str) -> str | None:
    canonical_left, canonical_right, disp = orient_class_rank(left, right, "")
    return table.get((canonical_left, canonical_right))


def derive_purpose_b(identity_rows: list[dict[str, str]]) -> dict:
    links = []
    seen: set[tuple[str, str]] = set()
    for row in identity_rows:
        left, right, disp = orient_class_rank(row["left"], row["right"], row["disposition"])
        key = (left, right)
        if key in seen:
            continue
        seen.add(key)
        links.append({"left": left, "right": right, "epistemic": disp})
    links.sort(key=lambda item: (item["left"], item["right"]))
    return {"purpose": "counterparty_reconciliation", "links": links}


def derive_purpose_a(
    conn: sqlite3.Connection,
    identity_rows: list[dict[str, str]],
    clause_rows: list[dict[str, str]],
) -> dict:
    active = active_contract_ids(conn)
    acquisition_contracts = acquisition_relevant_contract_ids(conn, clause_rows, active)
    id_table = identity_lookup(identity_rows)

    invoices = []
    for inv in conn.execute(
        """
        SELECT ib.invoice_id, ib.billed_name, ia.amount, ic.currency, ip.period, ist.status
        FROM invoice_billed_name ib
        JOIN invoice_amount ia ON ia.invoice_id = ib.invoice_id
        JOIN invoice_currency ic ON ic.invoice_id = ib.invoice_id
        JOIN invoice_period ip ON ip.invoice_id = ib.invoice_id
        JOIN invoice_status ist ON ist.invoice_id = ib.invoice_id
        ORDER BY ib.invoice_id
        """
    ):
        billing_id = f"billing:{inv['billed_name']}"
        for contract_id in sorted(acquisition_contracts):
            disp = identity_between(id_table, billing_id, contract_id)
            if disp is None:
                continue
            association = "asserted" if disp == "SAME_ENTITY" else "unresolved"
            invoices.append(
                {
                    "invoice_id": strip_prefix(inv["invoice_id"], "invoice:"),
                    "billed_name": inv["billed_name"],
                    "amount": inv["amount"],
                    "currency": inv["currency"],
                    "period": inv["period"],
                    "status": inv["status"],
                    "contract_id": strip_prefix(contract_id, "contract:"),
                    "association": association,
                }
            )
    invoices.sort(key=lambda row: row["invoice_id"])
    return {"purpose": "contractual_revenue_exposure", "invoices": invoices}


def pick_counterparty(
    contract_id: str,
    identity_rows: list[dict[str, str]],
    id_table: dict[tuple[str, str], str],
) -> str:
    """Prefer crm: identifier in the SAME_ENTITY class reachable from the contract."""
    same_class: set[str] = {contract_id}
    changed = True
    while changed:
        changed = False
        for row in identity_rows:
            if row["disposition"] != "SAME_ENTITY":
                continue
            left, right = row["left"], row["right"]
            if left in same_class and right not in same_class:
                same_class.add(right)
                changed = True
            elif right in same_class and left not in same_class:
                same_class.add(left)
                changed = True
    candidates = [item for item in same_class if item.startswith("crm:")]
    if candidates:
        return sorted(candidates)[0]
    for prefix in CLASS_RANK:
        prefixed = sorted(item for item in same_class if item.startswith(prefix))
        if prefixed:
            return prefixed[0]
    return contract_id


def open_invoices_for_contract(
    conn: sqlite3.Connection,
    contract_id: str,
    id_table: dict[tuple[str, str], str],
) -> list[str]:
    open_ids: list[str] = []
    for row in conn.execute(
        """
        SELECT ib.invoice_id, ib.billed_name
        FROM invoice_billed_name ib
        JOIN invoice_open io ON io.invoice_id = ib.invoice_id
        """
    ):
        billing_id = f"billing:{row['billed_name']}"
        disp = identity_between(id_table, billing_id, contract_id)
        if disp == "SAME_ENTITY":
            open_ids.append(strip_prefix(row["invoice_id"], "invoice:"))
    return sorted(open_ids)


def derive_purpose_c(
    conn: sqlite3.Connection,
    identity_rows: list[dict[str, str]],
    clause_rows: list[dict[str, str]],
) -> dict:
    active = active_contract_ids(conn)
    id_table = identity_lookup(identity_rows)
    dependencies = []

    for contract_id in sorted(active):
        present_kinds = sorted(
            {
                row["kind"]
                for row in clause_rows
                if row["contract_id"] == contract_id
                and row["kind"] in PURPOSE_C_KINDS
                and row["disposition"] == "PRESENT"
            }
        )
        if not present_kinds:
            continue

        billing_links = [
            row
            for row in identity_rows
            if row["left"].startswith("billing:") and row["right"] == contract_id
            or row["right"].startswith("billing:") and row["left"] == contract_id
        ]
        billing_dispositions = {row["disposition"] for row in billing_links}
        identity_unresolved = not billing_links or "UNRESOLVED" in billing_dispositions

        open_invoice_ids = [] if identity_unresolved else open_invoices_for_contract(
            conn, contract_id, id_table
        )
        has_open_invoice = bool(open_invoice_ids)
        has_auto_renewal = "auto_renewal" in present_kinds
        has_rolling_term = "rolling_term" in present_kinds
        current_relationship = has_open_invoice or has_auto_renewal or has_rolling_term

        if identity_unresolved:
            status = "unresolved"
            billing_name = next(
                (
                    row["left"].removeprefix("billing:")
                    if row["left"].startswith("billing:")
                    else row["right"].removeprefix("billing:")
                    for row in billing_links
                ),
                None,
            )
            counterparty = (
                f"billing:{billing_name}" if billing_name else pick_counterparty(contract_id, identity_rows, id_table)
            )
        elif current_relationship:
            status = "dependent"
            counterparty = pick_counterparty(contract_id, identity_rows, id_table)
        else:
            continue

        dependencies.append(
            {
                "counterparty": counterparty,
                "contract_id": strip_prefix(contract_id, "contract:"),
                "open_invoice_ids": open_invoice_ids,
                "obligation_kinds": present_kinds,
                "status": status,
            }
        )

    dependencies.sort(key=lambda row: row["contract_id"])
    return {"purpose": "commercial_dependency", "dependencies": dependencies}


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    db_path = resolve_world_db()
    conn = connect(db_path)
    try:
        identity_rows = load_identity_judgments(conn)
        clause_rows = load_clause_judgments(conn)

        write_json(ROOT / "purpose_ir" / "a" / "output.json", derive_purpose_a(conn, identity_rows, clause_rows))
        write_json(ROOT / "purpose_ir" / "b" / "output.json", derive_purpose_b(identity_rows))
        write_json(ROOT / "purpose_ir" / "c" / "output.json", derive_purpose_c(conn, identity_rows, clause_rows))
    finally:
        conn.close()


if __name__ == "__main__":
    main()
