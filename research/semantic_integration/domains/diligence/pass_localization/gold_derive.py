"""Evaluator gold derivations over a certified-schema World. Intervention use only."""

from __future__ import annotations

import json
from pathlib import Path

from taskview import TaskView

A_CLAUSES = {
    "change_of_control_consent",
    "change_of_control_termination",
    "assignment_notice_or_consent",
    "assignment_consent_required",
    "assignment_notice_required",
    "assignment_competitor_prohibition",
    "competitor_assignment_prohibition",
}
C_KINDS = {"exclusivity", "auto_renewal", "rolling_term"}
D_ASSIGN = {"assignment_notice_or_consent", "assignment_consent_required", "assignment_notice_required"}


def _tv(world: Path) -> TaskView:
    return TaskView(str(world), view_id="diligence-world")


def _has(tv: TaskView, name: str) -> bool:
    return any(rel["name"] == name for rel in tv.describe()["relations"])


def derive_certified(world: Path) -> dict:
    tv = _tv(world)
    invoices = tv.query("SELECT * FROM invoice_record") if _has(tv, "invoice_record") else []
    contracts = {
        row["contract_id"]: row for row in (tv.query("SELECT * FROM contract_record") if _has(tv, "contract_record") else [])
    }
    active = {
        row["contract_id"]: bool(row["active"])
        for row in (tv.query("SELECT * FROM contract_active") if _has(tv, "contract_active") else [])
    }
    clauses: dict[str, set[str]] = {}
    if _has(tv, "contract_clause_kind"):
        for row in tv.query("SELECT * FROM contract_clause_kind"):
            clauses.setdefault(row["contract_id"], set()).add(row["clause_kind"])
    identity = []
    if _has(tv, "identity_judgment"):
        identity = tv.query("SELECT * FROM identity_judgment")

    def same(a: str, b: str) -> bool:
        for row in identity:
            left, right, disp = row["left"], row["right"], row["disposition"]
            if disp == "SAME_ENTITY" and {left, right} == {a, b}:
                return True
        return False

    def unresolved(a: str, b: str) -> bool:
        for row in identity:
            if row["disposition"] == "UNRESOLVED" and {row["left"], row["right"]} == {a, b}:
                return True
        return False

    def contract_for_billed(billed: str) -> tuple[str | None, str]:
        billing = f"billing:{billed}"
        for cid, rec in contracts.items():
            ctext = rec["counterparty_text"].replace(",", "")
            billed_norm = billed.replace(",", "")
            name_match = billed_norm in ctext or ctext in billed_norm
            linked = same(billing, f"contract:{cid}")
            if not name_match and not linked:
                continue
            if unresolved(billing, f"contract:{cid}"):
                return cid, "unresolved"
            return cid, "asserted"
        return None, "unresolved"

    a_rows = []
    for inv in invoices:
        cid, assoc = contract_for_billed(inv["billed_name"])
        if not cid or not active.get(cid):
            continue
        kinds = clauses.get(cid, set())
        if kinds & A_CLAUSES:
            a_rows.append(
                {
                    "invoice_id": inv["invoice_id"],
                    "billed_name": inv["billed_name"],
                    "amount": inv["amount"],
                    "currency": inv["currency"],
                    "period": inv["period"],
                    "status": inv["status"],
                    "contract_id": cid,
                    "association": assoc,
                }
            )
    a_rows.sort(key=lambda row: row["invoice_id"])

    b_links = [
        {"left": row["left"], "right": row["right"], "epistemic": row["disposition"]}
        for row in identity
    ]
    b_links.sort(key=lambda row: (row["left"], row["right"]))

    c_rows = []
    for cid, rec in contracts.items():
        if not active.get(cid):
            continue
        kinds = sorted(clauses.get(cid, set()) & C_KINDS)
        if not kinds:
            continue
        billed_candidates = []
        for inv in invoices:
            found, assoc = contract_for_billed(inv["billed_name"])
            if found == cid:
                billed_candidates.append(inv)
        if not billed_candidates:
            continue
        open_ids = sorted({inv["invoice_id"] for inv in billed_candidates if inv["status"] == "open"})
        crm = None
        billed = billed_candidates[0]["billed_name"]
        billing = f"billing:{billed}"
        for row in identity:
            if row["disposition"] == "SAME_ENTITY" and row["right"] == billing and row["left"].startswith("crm:"):
                crm = row["left"]
            if row["disposition"] == "SAME_ENTITY" and row["left"] == billing and row["right"].startswith("crm:"):
                crm = row["right"]
        registry_unresolved = any(
            row["disposition"] == "UNRESOLVED"
            and billing in {row["left"], row["right"]}
            and "registry:" in row["left"] + row["right"]
            for row in identity
        )
        # Registry unresolved must not block commercial dependency.
        status = "dependent"
        if any(
            row["disposition"] == "UNRESOLVED" and {row["left"], row["right"]} == {billing, f"contract:{cid}"}
            for row in identity
        ):
            status = "unresolved"
        c_rows.append(
            {
                "counterparty": crm or billing,
                "contract_id": cid,
                "open_invoice_ids": open_ids,
                "obligation_kinds": kinds,
                "status": status,
            }
        )
    c_rows.sort(key=lambda row: row["contract_id"])
    tv.close()
    return {
        "a": {"purpose": "contractual_revenue_exposure", "invoices": a_rows},
        "b": {"purpose": "counterparty_reconciliation", "links": b_links},
        "c": {"purpose": "commercial_dependency", "dependencies": c_rows},
    }


def write_outputs(world: Path, dest_dir: Path) -> dict:
    payload = derive_certified(world)
    dest_dir.mkdir(parents=True, exist_ok=True)
    mapping = {"a": payload["a"], "b": payload["b"], "c": payload["c"]}
    for letter, obj in mapping.items():
        (dest_dir / f"{letter}.json").write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")
        purpose = dest_dir.parent / "purpose_ir" / letter / "output.json"
        purpose.parent.mkdir(parents=True, exist_ok=True)
        purpose.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")
    return payload
