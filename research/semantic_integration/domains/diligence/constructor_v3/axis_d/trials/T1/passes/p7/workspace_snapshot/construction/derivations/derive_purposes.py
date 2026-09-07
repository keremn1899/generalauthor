"""Derive purpose A/B/C JSON outputs from compiled world.sqlite relations."""

from __future__ import annotations

import json
from pathlib import Path

from taskview import TaskView

ROOT = Path(__file__).resolve().parents[2]
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
CURRENT_RELATIONSHIP_KINDS = {"auto_renewal", "rolling_term"}


def resolve_world_path() -> Path:
    for candidate in (ROOT / "06_world" / "world.sqlite", ROOT / "world" / "world.sqlite"):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("world.sqlite not found under 06_world/ or world/")


def load_identity_judgments(tv: TaskView) -> dict[tuple[str, str], str]:
    rows = tv.query_semantic(
        "SELECT left, right, disposition FROM identity_judgment ORDER BY left, right"
    )
    out: dict[tuple[str, str], str] = {}
    for row in rows:
        out[(row["left"], row["right"])] = row["disposition"]
        out[(row["right"], row["left"])] = row["disposition"]
    return out


def disposition_for_pair(
    left: str, right: str, judgments: dict[tuple[str, str], str]
) -> str | None:
    return judgments.get((left, right))


def map_invoice_association(
  disposition: str | None,
  table_disposition: str | None,
) -> str | None:
    if table_disposition:
        if table_disposition in ("asserted", "ACCEPT"):
            return "asserted"
        if table_disposition == "unresolved":
            return "unresolved"
    if disposition == "SAME_ENTITY":
        return "asserted"
    if disposition == "UNRESOLVED":
        return "unresolved"
    if disposition == "DISTINCT":
        return None
    return "unresolved"


def identity_linkage_confident(
    billing_id: str,
    crm_id: str,
    contract_id: str,
    judgments: dict[tuple[str, str], str],
) -> bool:
    """Direct SAME_ENTITY only; no transitive closure."""
    pairs = [
        (billing_id, crm_id),
        (billing_id, f"contract:{contract_id}"),
    ]
    for left, right in pairs:
        disposition = disposition_for_pair(left, right, judgments)
        if disposition == "DISTINCT":
            return False
        if disposition != "SAME_ENTITY":
            return False
    return True


def billed_names_for_crm(tv: TaskView, crm_account: str) -> list[str]:
    rows = tv.query_semantic(
        """
        SELECT DISTINCT i.billed_name
        FROM invoice_record i
        JOIN identity_judgment j
          ON j.left = 'billing:' || i.billed_name OR j.right = 'billing:' || i.billed_name
        WHERE (
            j.left = 'crm:' || ? AND j.right = 'billing:' || i.billed_name
            OR j.right = 'crm:' || ? AND j.left = 'billing:' || i.billed_name
        )
        """,
        (crm_account, crm_account),
    )
    if rows:
        return [row["billed_name"] for row in rows]
    # Fallback: unique billed names appearing in identity packets for this CRM's contract path.
    contract_rows = tv.query_semantic(
        """
        SELECT DISTINCT c.contract_id
        FROM contract_record c
        JOIN identity_judgment j
          ON j.left = 'contract:' || c.contract_id OR j.right = 'contract:' || c.contract_id
        WHERE (
            j.left = 'crm:' || ? AND j.right = 'contract:' || c.contract_id
            OR j.right = 'crm:' || ? AND j.left = 'contract:' || c.contract_id
        )
        """,
        (crm_account, crm_account),
    )
    names: list[str] = []
    for contract_row in contract_rows:
        contract_id = contract_row["contract_id"]
        for row in tv.query_semantic(
            """
            SELECT DISTINCT i.billed_name
            FROM invoice_record i
            JOIN identity_judgment j
              ON j.left = 'billing:' || i.billed_name OR j.right = 'billing:' || i.billed_name
            WHERE (
                j.left = 'billing:' || i.billed_name AND j.right = 'contract:' || ?
                OR j.right = 'billing:' || i.billed_name AND j.left = 'contract:' || ?
            )
            """,
            (contract_id, contract_id),
        ):
            names.append(row["billed_name"])
    return sorted(set(names))


def derive_purpose_a(tv: TaskView, judgments: dict[tuple[str, str], str]) -> dict:
    acquisition_clauses = tv.query_semantic(
        """
        SELECT contract, clause_kind
        FROM contract_clause_kind
        WHERE clause_kind IN ({})
        """.format(",".join("?" for _ in PURPOSE_A_KINDS)),
        tuple(PURPOSE_A_KINDS),
    )
    contracts_with_acquisition = {row["contract"] for row in acquisition_clauses}

    active_contracts = {
        row["contract_id"]
        for row in tv.query_semantic(
            "SELECT contract_id, active FROM contract_record WHERE active = 1"
        )
    }
    qualifying_contracts = contracts_with_acquisition & active_contracts

    association_rows = tv.query_semantic(
        "SELECT invoice, contract, disposition FROM invoice_contract_association"
    )
    association_by_pair = {
        (row["invoice"], row["contract"]): row["disposition"] for row in association_rows
    }

    invoices_out: list[dict] = []
    for invoice in tv.query_semantic(
        "SELECT invoice_id, billed_name, amount, currency, period, status FROM invoice_record"
    ):
        billing_id = f"billing:{invoice['billed_name']}"
        candidate_contracts = [
            row["contract_id"]
            for row in tv.query_semantic(
                """
                SELECT DISTINCT c.contract_id
                FROM contract_record c
                WHERE EXISTS (
                    SELECT 1 FROM identity_judgment j
                    WHERE (
                        j.left = ? AND j.right = 'contract:' || c.contract_id
                        OR j.right = ? AND j.left = 'contract:' || c.contract_id
                    )
                )
                """,
                (billing_id, billing_id),
            )
        ]
        for contract_id in candidate_contracts:
            if contract_id not in qualifying_contracts:
                continue
            table_disp = association_by_pair.get((invoice["invoice_id"], contract_id))
            identity_disp = disposition_for_pair(
                billing_id, f"contract:{contract_id}", judgments
            )
            association = map_invoice_association(identity_disp, table_disp)
            if association is None:
                continue
            invoices_out.append(
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

    invoices_out.sort(key=lambda row: row["invoice_id"])
    return {"purpose": "contractual_revenue_exposure", "invoices": invoices_out}


def derive_purpose_b(tv: TaskView) -> dict:
    links = []
    for row in tv.query_semantic(
        "SELECT left, right, disposition FROM identity_judgment ORDER BY left, right"
    ):
        disposition = row["disposition"]
        if disposition == "REJECT":
            epistemic = "DISTINCT"
        else:
            epistemic = disposition
        links.append(
            {
                "left": row["left"],
                "right": row["right"],
                "epistemic": epistemic,
            }
        )
    links.sort(key=lambda row: (row["left"], row["right"]))
    return {"purpose": "counterparty_reconciliation", "links": links}


def derive_purpose_c(tv: TaskView, judgments: dict[tuple[str, str], str]) -> dict:
    obligation_by_contract: dict[str, list[str]] = {}
    for row in tv.query_semantic(
        """
        SELECT contract, clause_kind
        FROM contract_clause_kind
        WHERE clause_kind IN ({})
        """.format(",".join("?" for _ in PURPOSE_C_KINDS)),
        tuple(PURPOSE_C_KINDS),
    ):
        obligation_by_contract.setdefault(row["contract"], []).append(row["clause_kind"])
    for kinds in obligation_by_contract.values():
        kinds.sort()

    active_contracts = {
        row["contract_id"]: row
        for row in tv.query_semantic(
            "SELECT contract_id, active FROM contract_record WHERE active = 1"
        )
    }
    current_relationship_contracts = set()
    for contract_id, row in active_contracts.items():
        kinds = set(obligation_by_contract.get(contract_id, []))
        if kinds & CURRENT_RELATIONSHIP_KINDS:
            current_relationship_contracts.add(contract_id)

    open_invoices_by_name: dict[str, list[str]] = {}
    for row in tv.query_semantic(
        "SELECT invoice_id, billed_name, status FROM invoice_record WHERE status = 'open'"
    ):
        open_invoices_by_name.setdefault(row["billed_name"], []).append(row["invoice_id"])

    crm_accounts = tv.query_semantic("SELECT account FROM crm_account_record")
    dependencies: list[dict] = []

    for crm_row in crm_accounts:
        crm_account = crm_row["account"]
        crm_id = f"crm:{crm_account}"
        contract_ids = [
            row["contract_id"]
            for row in tv.query_semantic(
                """
                SELECT DISTINCT c.contract_id
                FROM contract_record c
                WHERE EXISTS (
                    SELECT 1 FROM identity_judgment j
                    WHERE (
                        j.left = ? AND j.right = 'contract:' || c.contract_id
                        OR j.right = ? AND j.left = 'contract:' || c.contract_id
                    )
                )
                """,
                (crm_id, crm_id),
            )
        ]
        billed_names = billed_names_for_crm(tv, crm_account)
        for contract_id in contract_ids:
            if contract_id not in active_contracts:
                continue
            obligation_kinds = obligation_by_contract.get(contract_id, [])
            if not obligation_kinds:
                continue
            has_open = any(
                open_invoices_by_name.get(name) for name in billed_names
            )
            has_current_contract = contract_id in current_relationship_contracts
            if not has_open and not has_current_contract:
                continue

            open_ids: list[str] = []
            for name in billed_names:
                open_ids.extend(open_invoices_by_name.get(name, []))
            open_ids = sorted(set(open_ids))

            confident = False
            for name in billed_names:
                if identity_linkage_confident(
                    f"billing:{name}", crm_id, contract_id, judgments
                ):
                    confident = True
                    break

            dependencies.append(
                {
                    "counterparty": crm_id,
                    "contract_id": contract_id,
                    "open_invoice_ids": open_ids,
                    "obligation_kinds": obligation_kinds,
                    "status": "dependent" if confident else "unresolved",
                }
            )

    dependencies.sort(key=lambda row: row["contract_id"])
    return {"purpose": "commercial_dependency", "dependencies": dependencies}


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    world_path = resolve_world_path()
    with TaskView(world_path, view_id="diligence-world") as tv:
        judgments = load_identity_judgments(tv)
        write_json(ROOT / "purpose_ir" / "a" / "output.json", derive_purpose_a(tv, judgments))
        write_json(ROOT / "purpose_ir" / "b" / "output.json", derive_purpose_b(tv))
        write_json(ROOT / "purpose_ir" / "c" / "output.json", derive_purpose_c(tv, judgments))


if __name__ == "__main__":
    main()
