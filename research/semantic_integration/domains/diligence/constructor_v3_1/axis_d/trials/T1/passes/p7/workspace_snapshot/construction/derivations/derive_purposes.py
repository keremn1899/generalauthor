#!/usr/bin/env python3
"""Derive purpose IR outputs from compiled world.sqlite relations.

Reads only world.sqlite (06_world/world.sqlite or world/world.sqlite).
Purpose-scoped semantic relations (clause_presence, identity_judgment,
invoice_contract_association) are not persisted in world per 06_admission;
when absent, derivations degrade per 07_derivations.json blocking rules.
"""

from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORLD_CANDIDATES = (ROOT / "06_world" / "world.sqlite", ROOT / "world" / "world.sqlite")

PURPOSE_A_CLAUSE_KINDS = (
    "change_of_control_consent",
    "change_of_control_termination",
    "assignment_notice_or_consent",
    "assignment_consent",
    "assignment_notice",
    "assignment_competitor_prohibition",
    "competitor_assignment_prohibition",
)

PURPOSE_C_OBLIGATION_KINDS = ("exclusivity", "auto_renewal", "rolling_term")


def find_world_db() -> Path:
    for path in WORLD_CANDIDATES:
        if path.exists():
            return path
    raise FileNotFoundError(
        "world.sqlite not found; expected 06_world/world.sqlite or world/world.sqlite"
    )


def strip_prefix(value: str, prefix: str) -> str:
    needle = f"{prefix}:"
    if value.startswith(needle):
        return value[len(needle) :]
    return value


def table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone()
    return row is not None


def table_count(conn: sqlite3.Connection, name: str) -> int:
    if not table_exists(conn, name):
        return 0
    return int(conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0])


def build_thread_index(
    conn: sqlite3.Connection,
) -> tuple[dict[str, set[str]], dict[str, str]]:
    """Map thread_id -> identifier set, and identifier -> thread_id."""
    threads: dict[str, set[str]] = defaultdict(set)
    identifier_thread: dict[str, str] = {}
    if not table_exists(conn, "identity_candidate_pair"):
        return threads, identifier_thread
    for left, right, thread_id in conn.execute(
        "SELECT left, right, thread_id FROM identity_candidate_pair"
    ):
        threads[thread_id].update((left, right))
        identifier_thread[left] = thread_id
        identifier_thread[right] = thread_id
    return threads, identifier_thread


def identifiers_in_thread(threads: dict[str, set[str]], thread_id: str, prefix: str) -> list[str]:
    return sorted(i for i in threads.get(thread_id, ()) if i.startswith(f"{prefix}:"))


def contract_in_force_map(conn: sqlite3.Connection) -> dict[str, str]:
    if not table_exists(conn, "contract_in_force"):
        return {}
    return {
        contract: disposition
        for contract, disposition in conn.execute(
            "SELECT contract, disposition FROM contract_in_force"
        )
    }


def active_contracts_for_purpose_a(
    conn: sqlite3.Connection, in_force: dict[str, str]
) -> set[str]:
    """Active for purpose A: IN_FORCE, or resolved active=true; never expired SOW."""
    active: set[str] = set()
    if table_exists(conn, "contract_in_force_active"):
        for contract, active_flag in conn.execute(
            "SELECT contract, active FROM contract_in_force_active"
        ):
            if int(active_flag) == 1:
                active.add(contract)
    for contract, disposition in in_force.items():
        if disposition == "IN_FORCE":
            active.add(contract)
    return active


def present_clause_kinds(
    conn: sqlite3.Connection, contract: str, kinds: tuple[str, ...]
) -> list[str]:
    if table_count(conn, "clause_presence") == 0:
        return []
    rows = conn.execute(
        """
        SELECT clause_kind
        FROM clause_presence
        WHERE contract = ? AND clause_kind IN ({})
          AND disposition = 'PRESENT'
        """.format(",".join("?" * len(kinds))),
        (contract, *kinds),
    ).fetchall()
    return sorted({row[0] for row in rows})


def association_for_pair(
    conn: sqlite3.Connection, invoice: str, contract: str
) -> str | None:
    if table_count(conn, "invoice_contract_association") == 0:
        return None
    row = conn.execute(
        """
        SELECT disposition
        FROM invoice_contract_association
        WHERE invoice = ? AND contract = ?
        """,
        (invoice, contract),
    ).fetchone()
    return row[0] if row else None


def derive_association(
    conn: sqlite3.Connection,
    invoice: str,
    contract: str,
    billing_id: str,
    contract_id: str,
) -> str:
    stored = association_for_pair(conn, invoice, contract)
    if stored in ("asserted", "unresolved"):
        return stored
    if table_count(conn, "identity_judgment") == 0:
        return "unresolved"
    row = conn.execute(
        """
        SELECT disposition
        FROM identity_judgment
        WHERE (left = ? AND right = ?) OR (left = ? AND right = ?)
        """,
        (billing_id, contract_id, contract_id, billing_id),
    ).fetchone()
    if row is None:
        return "unresolved"
    if row[0] == "SAME_ENTITY":
        return "asserted"
    return "unresolved"


def derive_purpose_a(conn: sqlite3.Connection) -> dict:
    threads, identifier_thread = build_thread_index(conn)
    in_force = contract_in_force_map(conn)
    active_contracts = active_contracts_for_purpose_a(conn, in_force)

    invoices_out: list[dict] = []
    if not table_exists(conn, "invoice"):
        return {"purpose": "contractual_revenue_exposure", "invoices": invoices_out}

    for invoice_ref, invoice_id, billed_name, amount, currency, period, status in conn.execute(
        """
        SELECT invoice, invoice_id, billed_name, amount, currency, period, status
        FROM invoice
        """
    ):
        billing_id = f"billing:{billed_name}"
        thread_id = identifier_thread.get(billing_id)
        if not thread_id:
            continue

        contract_refs = identifiers_in_thread(threads, thread_id, "contract")
        for contract_ref in contract_refs:
            acquisition_kinds = present_clause_kinds(
                conn, contract_ref, PURPOSE_A_CLAUSE_KINDS
            )
            if not acquisition_kinds:
                continue

            disposition = in_force.get(contract_ref)
            if disposition == "EXPIRED":
                continue
            if contract_ref not in active_contracts:
                continue

            association = derive_association(
                conn,
                invoice_ref,
                contract_ref,
                billing_id,
                contract_ref,
            )
            invoices_out.append(
                {
                    "invoice_id": invoice_id,
                    "billed_name": billed_name,
                    "amount": amount,
                    "currency": currency,
                    "period": period,
                    "status": status,
                    "contract_id": strip_prefix(contract_ref, "contract"),
                    "association": association,
                }
            )

    invoices_out.sort(key=lambda row: row["invoice_id"])
    return {"purpose": "contractual_revenue_exposure", "invoices": invoices_out}


def derive_purpose_b(conn: sqlite3.Connection) -> dict:
    links: list[dict] = []
    if not table_exists(conn, "identity_candidate_pair"):
        return {"purpose": "counterparty_reconciliation", "links": links}

    has_judgments = table_count(conn, "identity_judgment") > 0
    for left, right in conn.execute(
        """
        SELECT left, right
        FROM identity_candidate_pair
        ORDER BY left, right
        """
    ):
        epistemic = "UNRESOLVED"
        if has_judgments:
            row = conn.execute(
                """
                SELECT disposition
                FROM identity_judgment
                WHERE left = ? AND right = ?
                """,
                (left, right),
            ).fetchone()
            if row is not None:
                epistemic = row[0]
                if epistemic == "REJECT":
                    epistemic = "DISTINCT"
        links.append({"left": left, "right": right, "epistemic": epistemic})

    return {"purpose": "counterparty_reconciliation", "links": links}


def current_relationship(
    conn: sqlite3.Connection,
    contract_ref: str,
    thread_id: str,
    threads: dict[str, set[str]],
    in_force: dict[str, str],
) -> tuple[bool, bool]:
    """Return (has_open_invoice, has_active_renewing_contract). Second bool is blocking unresolved."""
    has_open = False
    if table_exists(conn, "open_invoice") and table_exists(conn, "invoice"):
        billing_ids = identifiers_in_thread(threads, thread_id, "billing")
        if billing_ids:
            placeholders = ",".join("?" * len(billing_ids))
            names = [strip_prefix(b, "billing") for b in billing_ids]
            row = conn.execute(
                f"""
                SELECT 1
                FROM open_invoice oi
                JOIN invoice i ON i.invoice = oi.invoice
                WHERE i.billed_name IN ({placeholders})
                LIMIT 1
                """,
                tuple(names),
            ).fetchone()
            has_open = row is not None

    disposition = in_force.get(contract_ref)
    if disposition == "UNRESOLVED":
        return has_open, True

    active = disposition == "IN_FORCE"
    if table_exists(conn, "contract_in_force_active"):
        row = conn.execute(
            "SELECT active FROM contract_in_force_active WHERE contract = ?",
            (contract_ref,),
        ).fetchone()
        if row is not None:
            active = bool(row[0])

    renewing = False
    if active:
        kinds = present_clause_kinds(conn, contract_ref, ("auto_renewal", "rolling_term"))
        renewing = bool(kinds)

    return has_open or renewing, False


def pick_counterparty(threads: dict[str, set[str]], thread_id: str) -> str:
    for prefix in ("billing", "crm", "registry", "contract"):
        ids = identifiers_in_thread(threads, thread_id, prefix)
        if ids:
            return ids[0]
    return ""


def open_invoice_ids_for_thread(
    conn: sqlite3.Connection, threads: dict[str, set[str]], thread_id: str
) -> list[str]:
    if not table_exists(conn, "open_invoice") or not table_exists(conn, "invoice"):
        return []
    billing_ids = identifiers_in_thread(threads, thread_id, "billing")
    names = [strip_prefix(b, "billing") for b in billing_ids]
    if not names:
        return []
    placeholders = ",".join("?" * len(names))
    rows = conn.execute(
        f"""
        SELECT oi.invoice_id
        FROM open_invoice oi
        JOIN invoice i ON i.invoice = oi.invoice
        WHERE i.billed_name IN ({placeholders})
        ORDER BY oi.invoice_id
        """,
        tuple(names),
    ).fetchall()
    return [row[0] for row in rows]


def identity_blocks_thread(conn: sqlite3.Connection, thread_id: str) -> bool:
    if table_count(conn, "identity_judgment") == 0:
        return True
    if not table_exists(conn, "identity_candidate_pair"):
        return True
    pairs = conn.execute(
        "SELECT left, right FROM identity_candidate_pair WHERE thread_id = ?",
        (thread_id,),
    ).fetchall()
    for left, right in pairs:
        row = conn.execute(
            """
            SELECT disposition
            FROM identity_judgment
            WHERE left = ? AND right = ?
            """,
            (left, right),
        ).fetchone()
        if row is None or row[0] == "UNRESOLVED":
            return True
    return False


def derive_purpose_c(conn: sqlite3.Connection) -> dict:
    threads, identifier_thread = build_thread_index(conn)
    in_force = contract_in_force_map(conn)
    dependencies: list[dict] = []

    if table_count(conn, "commercial_dependency") > 0:
        for contract_ref, contract_id, counterparty, status in conn.execute(
            """
            SELECT contract, contract_id, counterparty, status
            FROM commercial_dependency
            ORDER BY contract_id
            """
        ):
            obligation_kinds = present_clause_kinds(
                conn, contract_ref, PURPOSE_C_OBLIGATION_KINDS
            )
            thread_id = identifier_thread.get(f"contract:{contract_id}")
            open_ids: list[str] = []
            if thread_id:
                open_ids = open_invoice_ids_for_thread(conn, threads, thread_id)
            dependencies.append(
                {
                    "counterparty": counterparty,
                    "contract_id": contract_id,
                    "open_invoice_ids": open_ids,
                    "obligation_kinds": obligation_kinds,
                    "status": status,
                }
            )
        return {"purpose": "commercial_dependency", "dependencies": dependencies}

    if not table_exists(conn, "contract"):
        return {"purpose": "commercial_dependency", "dependencies": dependencies}

    seen_contracts: set[str] = set()
    for contract_ref, contract_id in conn.execute(
        "SELECT contract, contract_id FROM contract ORDER BY contract_id"
    ):
        if contract_ref in seen_contracts:
            continue
        seen_contracts.add(contract_ref)

        contract_identifier = f"contract:{contract_id}"
        thread_id = identifier_thread.get(contract_identifier)
        if not thread_id:
            continue

        obligation_kinds = present_clause_kinds(
            conn, contract_ref, PURPOSE_C_OBLIGATION_KINDS
        )
        has_current, lifecycle_unresolved = current_relationship(
            conn, contract_ref, thread_id, threads, in_force
        )
        identity_unresolved = identity_blocks_thread(conn, thread_id)
        open_ids = open_invoice_ids_for_thread(conn, threads, thread_id)

        qualifies = has_current and bool(obligation_kinds)
        must_report_unresolved = (
            identity_unresolved
            or lifecycle_unresolved
            or (has_current and not obligation_kinds and table_count(conn, "clause_presence") == 0)
        )

        if not qualifies and not must_report_unresolved:
            continue
        if not has_current and not open_ids:
            continue

        status = "unresolved"
        if qualifies and not identity_unresolved and not lifecycle_unresolved:
            status = "dependent"

        dependencies.append(
            {
                "counterparty": pick_counterparty(threads, thread_id),
                "contract_id": contract_id,
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
    world_path = find_world_db()
    conn = sqlite3.connect(world_path)
    try:
        write_json(ROOT / "purpose_ir" / "a" / "output.json", derive_purpose_a(conn))
        write_json(ROOT / "purpose_ir" / "b" / "output.json", derive_purpose_b(conn))
        write_json(ROOT / "purpose_ir" / "c" / "output.json", derive_purpose_c(conn))
    finally:
        conn.close()


if __name__ == "__main__":
    main()
