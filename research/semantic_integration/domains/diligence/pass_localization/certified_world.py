"""Evaluator-certified World for the optional P7-only diagnostic. Not a constructor artifact."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from taskview import Grounding, GroundingKind, RelationMode, Role, RoleType, TaskView

from research.semantic_integration.domains.diligence.freeze_apparatus import HIDDEN, SOURCES

VIEW_ID = "diligence-world"


def _src(reference: str, detail: str = "") -> list[Grounding]:
    return [Grounding(GroundingKind.SOURCE, reference, detail)]


def build_certified_world(destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        destination.unlink()
    tv = TaskView(str(destination), view_id=VIEW_ID)

    tv.declare_relation(
        "crm_record",
        [Role("account", RoleType.REFERENT), Role("account_name", RoleType.TEXT)],
        mode=RelationMode.BASE,
        description="CRM account observation",
    )
    tv.declare_relation(
        "invoice_record",
        [
            Role("invoice_id", RoleType.TEXT),
            Role("billed_name", RoleType.TEXT),
            Role("amount", RoleType.REAL),
            Role("currency", RoleType.TEXT),
            Role("period", RoleType.TEXT),
            Role("status", RoleType.TEXT),
        ],
        mode=RelationMode.BASE,
        description="Invoice observation",
    )
    tv.declare_relation(
        "registry_record",
        [
            Role("company_number", RoleType.TEXT),
            Role("legal_name", RoleType.TEXT),
            Role("status", RoleType.TEXT),
        ],
        mode=RelationMode.BASE,
        description="Registry observation",
    )
    tv.declare_relation(
        "contract_record",
        [Role("contract_id", RoleType.TEXT), Role("counterparty_text", RoleType.TEXT)],
        mode=RelationMode.BASE,
        description="Contract header observation",
    )
    tv.declare_relation(
        "contract_active",
        [Role("contract_id", RoleType.TEXT), Role("active", RoleType.BOOLEAN)],
        mode=RelationMode.BASE,
        description="Whether contract is active on evaluation date",
    )
    tv.declare_relation(
        "contract_clause_kind",
        [Role("contract_id", RoleType.TEXT), Role("clause_kind", RoleType.TEXT)],
        mode=RelationMode.BASE,
        description="Deterministic/hidden-certified clause kind present on a contract",
    )
    tv.declare_relation(
        "identity_judgment",
        [
            Role("left", RoleType.TEXT),
            Role("right", RoleType.TEXT),
            Role("disposition", RoleType.TEXT),
        ],
        mode=RelationMode.BASE,
        description="Identity disposition",
    )

    with (SOURCES / "crm.csv").open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            ident = f"crm:{row['crm_account_id']}"
            tv.add_referent(ident, label=row["account_name"], grounding=_src("crm.csv", row["crm_account_id"]))
            tv.assert_tuple(
                "crm_record",
                {"account": ident, "account_name": row["account_name"]},
                grounding=_src("crm.csv", row["crm_account_id"]),
            )

    invoices = json.loads((SOURCES / "billing" / "invoices.json").read_text())
    for row in invoices:
        billed = f"billing:{row['billed_name']}"
        tv.add_referent(billed, label=row["billed_name"], grounding=_src("billing/invoices.json", row["invoice_id"]))
        tv.assert_tuple(
            "invoice_record",
            {
                "invoice_id": row["invoice_id"],
                "billed_name": row["billed_name"],
                "amount": float(row["amount"]),
                "currency": row["currency"],
                "period": row["period"],
                "status": row["status"],
            },
            grounding=_src("billing/invoices.json", row["invoice_id"]),
        )

    with (SOURCES / "company_registry.csv").open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            ident = f"registry:{row['company_number']}"
            tv.add_referent(ident, label=row["legal_name"], grounding=_src("company_registry.csv", row["company_number"]))
            tv.assert_tuple(
                "registry_record",
                {
                    "company_number": row["company_number"],
                    "legal_name": row["legal_name"],
                    "status": row["status"],
                },
                grounding=_src("company_registry.csv", row["company_number"]),
            )

    contracts = {
        "MSA-HELION-2019": "Helion Robotics Limited",
        "MSA-NBA-2021": "Northbridge Analytics, Inc.",
        "MSA-OAK-2018": "Oakfield Logistik GmbH",
        "SOW-VEL-2022": "Vellum Print Co Ltd",
        "MSA-MER-2024": "Meridian Energy Partners LLC",
    }
    for contract_id, counterparty in contracts.items():
        ident = f"contract:{contract_id}"
        tv.add_referent(ident, label=contract_id, grounding=_src(f"contracts/{contract_id}.md", "header"))
        tv.assert_tuple(
            "contract_record",
            {"contract_id": contract_id, "counterparty_text": counterparty},
            grounding=_src(f"contracts/{contract_id}.md", "header"),
        )

    clauses = json.loads((HIDDEN / "annotations" / "clause_dispositions.json").read_text())["contracts"]
    kind_map = {
        "change_of_control_consent": "change_of_control_consent",
        "change_of_control_termination": "change_of_control_termination",
        "assignment_notice_or_consent": "assignment_notice_or_consent",
        "competitor_assignment_prohibition": "competitor_assignment_prohibition",
        "exclusivity": "exclusivity",
        "auto_renewal": "auto_renewal",
        "rolling_term": "rolling_term",
    }
    for contract_id, flags in clauses.items():
        tv.assert_tuple(
            "contract_active",
            {"contract_id": contract_id, "active": bool(flags["active"])},
            grounding=_src(f"contracts/{contract_id}.md", "term"),
        )
        for flag, kind in kind_map.items():
            if flags.get(flag):
                tv.assert_tuple(
                    "contract_clause_kind",
                    {"contract_id": contract_id, "clause_kind": kind},
                    grounding=_src(f"contracts/{contract_id}.md", kind),
                )

    identity = json.loads((HIDDEN / "annotations" / "identity_dispositions.json").read_text())
    mapping = {"same_entity": "SAME_ENTITY", "distinct": "DISTINCT", "unresolved": "UNRESOLVED"}
    for key, disp in mapping.items():
        for left, right in identity[key]:
            tv.assert_tuple(
                "identity_judgment",
                {"left": left, "right": right, "disposition": disp},
                grounding=_src("commercial_notes.md", f"{left}|{right}"),
            )
    tv.close()
    return destination
