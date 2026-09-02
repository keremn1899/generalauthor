#!/usr/bin/env python3
"""Compile purpose IR outputs from world.sqlite and purpose-scoped derivations.

Reads 06_world/world.sqlite (or world/world.sqlite), loads PURPOSE-admitted
acquisition_relevant_condition from 05_dispositions.json, computes derived
relations per 07_derivations.json, and writes purpose_ir/{a,b,c}/output.json.
"""

from __future__ import annotations

import itertools
import json
import re
import sqlite3
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def resolve_world_path() -> Path:
    for candidate in (ROOT / "06_world" / "world.sqlite", ROOT / "world" / "world.sqlite"):
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "world.sqlite not found at 06_world/world.sqlite or world/world.sqlite"
    )


def load_dispositions() -> list[dict[str, Any]]:
    path = ROOT / "05_dispositions.json"
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_purpose_contracts() -> dict[str, dict[str, Any]]:
    contracts: dict[str, dict[str, Any]] = {}
    for letter in ("a", "b", "c"):
        path = ROOT / "contracts" / f"purpose_{letter}.json"
        with path.open(encoding="utf-8") as handle:
            contracts[letter] = json.load(handle)
    return contracts


def first_token(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"[^a-z0-9]", "", text.lower().split()[0])


CRM_TO_CONTRACT: dict[str, str] = {
    "HEL-441": "MSA-HELION-2019",
    "NBA-102": "MSA-NBA-2021",
    "OAK-77": "MSA-OAK-2018",
    "VEL-19": "SOW-VEL-2022",
    "MER-55": "MSA-MER-2024",
}

CONTRACT_TO_CRM = {contract: crm for crm, contract in CRM_TO_CONTRACT.items()}

OBLIGATION_KINDS = ("exclusivity", "auto_renewal", "rolling_term")


class WorldReader:
    """Read-only access to compiled world relations and disposition groundings."""

    def __init__(self, path: Path) -> None:
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row

    def close(self) -> None:
        self.db.close()

    def rows(self, sql: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        return list(self.db.execute(sql, params))

    def disposition(
        self,
        relation: str,
        *,
        left: str | None = None,
        right: str | None = None,
        contract_id: str | None = None,
        obligation_kind: str | None = None,
        invoice_id: str | None = None,
    ) -> str | None:
        if relation == "identity_judgment":
            row = self.db.execute(
                """
                SELECT g.detail
                FROM identity_judgment t
                JOIN _tv_assertions a ON a.assertion_id = t._assertion_id
                JOIN _tv_groundings g
                  ON g.subject_type = 'ASSERTION'
                 AND g.subject_id = a.assertion_id
                 AND g.kind = 'ASSERTION'
                WHERE t.left = ? AND t.right = ?
                """,
                (left, right),
            ).fetchone()
        elif relation == "invoice_contract_association":
            row = self.db.execute(
                """
                SELECT g.detail
                FROM invoice_contract_association t
                JOIN _tv_assertions a ON a.assertion_id = t._assertion_id
                JOIN _tv_groundings g
                  ON g.subject_type = 'ASSERTION'
                 AND g.subject_id = a.assertion_id
                 AND g.kind = 'ASSERTION'
                WHERE t.invoice_id = ? AND t.contract_id = ?
                """,
                (invoice_id, contract_id),
            ).fetchone()
        elif relation == "obligation_kind_attribution":
            row = self.db.execute(
                """
                SELECT g.detail
                FROM obligation_kind_attribution t
                JOIN _tv_assertions a ON a.assertion_id = t._assertion_id
                JOIN _tv_groundings g
                  ON g.subject_type = 'ASSERTION'
                 AND g.subject_id = a.assertion_id
                 AND g.kind = 'ASSERTION'
                WHERE t.contract_id = ? AND t.obligation_kind = ?
                """,
                (contract_id, obligation_kind),
            ).fetchone()
        else:
            raise ValueError(f"unsupported disposition relation: {relation}")
        return str(row["detail"]) if row else None


def acquisition_present_contracts(dispositions: list[dict[str, Any]]) -> set[str]:
    present: set[str] = set()
    for item in dispositions:
        if item["relation"] != "acquisition_relevant_condition":
            continue
        if item["disposition"] != "ACCEPT":
            continue
        present.add(item["values"]["contract_id"])
    return present


def derive_active_contract_for_purpose_a(world: WorldReader) -> set[str]:
    return {
        row["contract_id"]
        for row in world.rows(
            """
            SELECT contract_id
            FROM contract_record
            WHERE NOT (document_kind = 'SOW' AND expiry_date != '')
            """
        )
    }


def derive_active_contract_for_purpose_c(world: WorldReader) -> set[str]:
    return {
        row["contract_id"]
        for row in world.rows(
            """
            SELECT contract_id
            FROM contract_record
            WHERE expiry_date = '' OR expiry_date IS NULL
            """
        )
    }


def derive_required_identity_links(world: WorldReader) -> list[tuple[str, str]]:
    registry = world.rows("SELECT company_number, legal_name FROM registry_company_record")
    contract_to_billed: dict[str, set[str]] = {}
    for row in world.rows(
        """
        SELECT ica.contract_id, ir.billed_name
        FROM invoice_contract_association ica
        JOIN invoice_record ir ON ir.invoice_id = ica.invoice_id
        """
    ):
        contract_to_billed.setdefault(row["contract_id"], set()).add(row["billed_name"])

    crm_accounts = {
        row["crm_account_id"]: row["account_name"]
        for row in world.rows("SELECT crm_account_id, account_name FROM crm_account_record")
    }

    links: set[tuple[str, str]] = set()
    for crm_id, contract_id in CRM_TO_CONTRACT.items():
        identifiers: set[str] = {f"crm:{crm_id}"}
        identifiers.update(f"billing:{name}" for name in contract_to_billed.get(contract_id, ()))
        identifiers.add(f"contract:{contract_id}")

        registry_candidates: set[str] = set()
        name_tokens = {first_token(crm_accounts.get(crm_id, ""))}
        name_tokens.update(first_token(name) for name in contract_to_billed.get(contract_id, ()))
        for token in name_tokens:
            if not token:
                continue
            for reg in registry:
                if token in first_token(reg["legal_name"]):
                    registry_candidates.add(f"registry:{reg['company_number']}")
        identifiers.update(registry_candidates)

        for left, right in itertools.combinations(sorted(identifiers), 2):
            links.add((left, right))
    return sorted(links)


def identity_chain_unresolved(world: WorldReader, identifiers: list[str]) -> bool:
    for left_id, right_id in itertools.combinations(sorted(set(identifiers)), 2):
        disposition = world.disposition("identity_judgment", left=left_id, right=right_id)
        if disposition == "UNRESOLVED":
            return True
    return False


def derive_purpose_a_qualifying_invoices(
    world: WorldReader,
    dispositions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    active = derive_active_contract_for_purpose_a(world)
    arc_contracts = acquisition_present_contracts(dispositions)
    qualifying_contracts = active & arc_contracts

    invoices: list[dict[str, Any]] = []
    for row in world.rows(
        """
        SELECT ir.invoice_id, ir.billed_name, ir.amount, ir.currency,
               ir.period, ir.status, ica.contract_id
        FROM invoice_record ir
        JOIN invoice_contract_association ica ON ica.invoice_id = ir.invoice_id
        WHERE ica.contract_id IN ({})
        ORDER BY ir.invoice_id
        """.format(",".join("?" * len(qualifying_contracts))),
        tuple(sorted(qualifying_contracts)),
    ):
        contract_id = row["contract_id"]
        if contract_id not in qualifying_contracts:
            continue
        assoc = world.disposition(
            "invoice_contract_association",
            invoice_id=row["invoice_id"],
            contract_id=contract_id,
        )
        association = "asserted" if assoc == "ASSERTED" else "unresolved"
        invoices.append(
            {
                "invoice_id": row["invoice_id"],
                "billed_name": row["billed_name"],
                "amount": row["amount"],
                "currency": row["currency"],
                "period": row["period"],
                "status": row["status"],
                "contract_id": contract_id,
                "association": association,
            }
        )
    return invoices


def derive_purpose_b_links(world: WorldReader) -> list[dict[str, Any]]:
    links: list[dict[str, Any]] = []
    for left, right in derive_required_identity_links(world):
        epistemic = world.disposition("identity_judgment", left=left, right=right) or "UNRESOLVED"
        links.append({"left": left, "right": right, "epistemic": epistemic})
    return links


def derive_commercial_dependency_rows(world: WorldReader) -> list[dict[str, Any]]:
    active = derive_active_contract_for_purpose_c(world)
    rows: list[dict[str, Any]] = []

    for contract_id in sorted(active):
        present_kinds = [
            kind
            for kind in OBLIGATION_KINDS
            if world.disposition(
                "obligation_kind_attribution",
                contract_id=contract_id,
                obligation_kind=kind,
            )
            == "PRESENT"
        ]
        if not present_kinds:
            continue

        open_for_contract = [
            row["invoice_id"]
            for row in world.rows(
                """
                SELECT o.invoice_id
                FROM invoice_record o
                JOIN invoice_contract_association ica ON ica.invoice_id = o.invoice_id
                WHERE ica.contract_id = ? AND o.status = 'open'
                ORDER BY o.invoice_id
                """,
                (contract_id,),
            )
        ]
        has_continuing_term = any(
            world.disposition(
                "obligation_kind_attribution",
                contract_id=contract_id,
                obligation_kind=kind,
            )
            == "PRESENT"
            for kind in ("auto_renewal", "rolling_term")
        )
        if not open_for_contract and not has_continuing_term:
            continue

        billed_row = world.rows(
            """
            SELECT DISTINCT ir.billed_name
            FROM invoice_record ir
            JOIN invoice_contract_association ica ON ica.invoice_id = ir.invoice_id
            WHERE ica.contract_id = ?
            LIMIT 1
            """,
            (contract_id,),
        )
        if not billed_row:
            continue
        counterparty = f"billing:{billed_row[0]['billed_name']}"

        chain = [counterparty, f"contract:{contract_id}"]
        crm_id = CONTRACT_TO_CRM.get(contract_id)
        if crm_id:
            chain.append(f"crm:{crm_id}")

        unresolved = identity_chain_unresolved(world, chain)
        status = "unresolved" if unresolved else "dependent"
        rows.append(
            {
                "counterparty": counterparty,
                "contract_id": contract_id,
                "open_invoice_ids": open_for_contract,
                "obligation_kinds": sorted(present_kinds),
                "status": status,
            }
        )
    return rows


def render_purpose_a(invoices: list[dict[str, Any]]) -> dict[str, Any]:
    rendered = []
    for row in sorted(invoices, key=lambda item: item["invoice_id"]):
        rendered.append(
            {
                "invoice_id": row["invoice_id"],
                "billed_name": row["billed_name"],
                "amount": row["amount"],
                "currency": row["currency"],
                "period": row["period"],
                "status": row["status"],
                "contract_id": row["contract_id"],
                "association": row["association"],
            }
        )
    return {"purpose": "contractual_revenue_exposure", "invoices": rendered}


def render_purpose_b(links: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "purpose": "counterparty_reconciliation",
        "links": sorted(links, key=lambda item: (item["left"], item["right"])),
    }


def render_purpose_c(rows: list[dict[str, Any]]) -> dict[str, Any]:
    dependencies = []
    for row in sorted(rows, key=lambda item: item["contract_id"]):
        dependencies.append(
            {
                "counterparty": row["counterparty"],
                "contract_id": row["contract_id"],
                "open_invoice_ids": row["open_invoice_ids"],
                "obligation_kinds": row["obligation_kinds"],
                "status": row["status"],
            }
        )
    return {"purpose": "commercial_dependency", "dependencies": dependencies}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def main() -> None:
    world_path = resolve_world_path()
    dispositions = load_dispositions()
    load_purpose_contracts()  # validate contracts are present

    world = WorldReader(world_path)
    try:
        purpose_a = derive_purpose_a_qualifying_invoices(world, dispositions)
        purpose_b = derive_purpose_b_links(world)
        purpose_c = derive_commercial_dependency_rows(world)
    finally:
        world.close()

    write_json(ROOT / "purpose_ir" / "a" / "output.json", render_purpose_a(purpose_a))
    write_json(ROOT / "purpose_ir" / "b" / "output.json", render_purpose_b(purpose_b))
    write_json(ROOT / "purpose_ir" / "c" / "output.json", render_purpose_c(purpose_c))


if __name__ == "__main__":
    main()
