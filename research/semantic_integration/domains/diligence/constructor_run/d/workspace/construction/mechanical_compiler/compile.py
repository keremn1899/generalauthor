"""C0/C1 mechanical compilation into TaskView."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from taskview import (
    Completeness,
    CompletenessStatus,
    Grounding,
    GroundingKind,
    RelationMode,
    Role,
    RoleType,
    TaskView,
)

ROOT = Path(__file__).resolve().parents[2]
SOURCES = ROOT / "sources"
EVAL_DATE = "2025-09-01"

ACQUISITION_CLAUSE_KINDS = {
    "change_of_control_consent",
    "change_of_control_termination",
    "assignment_consent_required",
    "assignment_notice_required",
    "assignment_competitor_prohibition",
}

OBLIGATION_CLAUSE_KINDS = {"exclusivity"}
OBLIGATION_TERM_KINDS = {"auto_renewal", "rolling_term"}


def normalize_name(text: str) -> str:
    s = text.lower()
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(
        r"\b(limited|ltd|incorporated|inc|llc|gmbh|co|company|corp|corporation)\b",
        " ",
        s,
    )
    return re.sub(r"\s+", " ", s).strip()


def contract_id_from_path(path: Path) -> str:
    return path.stem


def declare_world_schema(tv: TaskView) -> None:
    tv.declare_relation(
        "crm_record",
        [
            Role("account", RoleType.REFERENT),
            Role("account_name", RoleType.TEXT),
            Role("domain", RoleType.TEXT),
            Role("country", RoleType.TEXT),
            Role("status", RoleType.TEXT),
        ],
        description="CRM account row.",
    )
    tv.declare_relation(
        "invoice_record",
        [
            Role("invoice", RoleType.REFERENT),
            Role("billed_name", RoleType.TEXT),
            Role("amount", RoleType.REAL),
            Role("currency", RoleType.TEXT),
            Role("period", RoleType.TEXT),
            Role("status", RoleType.TEXT),
        ],
        description="Billing invoice row.",
    )
    tv.declare_relation(
        "registry_record",
        [
            Role("company", RoleType.REFERENT),
            Role("legal_name", RoleType.TEXT),
            Role("jurisdiction", RoleType.TEXT),
            Role("status", RoleType.TEXT),
        ],
        description="Registry company row.",
    )
    tv.declare_relation(
        "contract_record",
        [
            Role("contract", RoleType.REFERENT),
            Role("counterparty_text", RoleType.TEXT),
            Role("effective_date", RoleType.TEXT),
            Role("term_text", RoleType.TEXT),
            Role("expiry_date", RoleType.TEXT),
        ],
        description="Contract header fields.",
    )
    tv.declare_relation(
        "contract_clause",
        [
            Role("contract", RoleType.REFERENT),
            Role("clause_kind", RoleType.TEXT),
        ],
        description="Present contract clause kind.",
    )
    tv.declare_relation(
        "contract_term_kind",
        [
            Role("contract", RoleType.REFERENT),
            Role("term_kind", RoleType.TEXT),
        ],
        description="Contract term structure kind.",
    )
    tv.declare_relation(
        "contract_active",
        [
            Role("contract", RoleType.REFERENT),
            Role("active", RoleType.BOOLEAN),
        ],
        description="Active status on evaluation date.",
    )
    tv.declare_relation(
        "crm_to_billing_candidate",
        [
            Role("crm_account", RoleType.REFERENT),
            Role("billing_name", RoleType.REFERENT),
        ],
        description="CRM to billing identity candidate.",
    )
    tv.declare_relation(
        "billing_to_registry_candidate",
        [
            Role("billing_name", RoleType.REFERENT),
            Role("registry_company", RoleType.REFERENT),
        ],
        description="Billing to registry identity candidate.",
    )
    tv.declare_relation(
        "counterparty_to_contract_candidate",
        [
            Role("counterparty", RoleType.REFERENT),
            Role("contract", RoleType.REFERENT),
        ],
        description="Counterparty to contract candidate.",
    )
    tv.declare_relation(
        "identity_judgment",
        [
            Role("left", RoleType.REFERENT),
            Role("right", RoleType.REFERENT),
            Role("disposition", RoleType.TEXT),
        ],
        description="Resolved identity judgment.",
    )


def declare_derived_schema(tv: TaskView) -> None:
    tv.declare_relation(
        "acquisition_relevant_clause",
        [
            Role("contract", RoleType.REFERENT),
            Role("clause_kind", RoleType.TEXT),
        ],
        mode=RelationMode.DERIVED,
        description="Acquisition-relevant clauses for Purpose A.",
    )
    tv.declare_relation(
        "invoice_contract_link",
        [
            Role("invoice", RoleType.REFERENT),
            Role("contract", RoleType.REFERENT),
            Role("association", RoleType.TEXT),
        ],
        mode=RelationMode.DERIVED,
        description="Invoice to contract association.",
    )
    tv.declare_relation(
        "purpose_a_invoice",
        [
            Role("invoice", RoleType.REFERENT),
            Role("billed_name", RoleType.TEXT),
            Role("amount", RoleType.REAL),
            Role("currency", RoleType.TEXT),
            Role("period", RoleType.TEXT),
            Role("status", RoleType.TEXT),
            Role("contract", RoleType.REFERENT),
            Role("association", RoleType.TEXT),
        ],
        mode=RelationMode.DERIVED,
        description="Purpose A qualifying invoices.",
    )
    tv.declare_relation(
        "purpose_b_link",
        [
            Role("left", RoleType.TEXT),
            Role("right", RoleType.TEXT),
            Role("epistemic", RoleType.TEXT),
        ],
        mode=RelationMode.DERIVED,
        description="Purpose B identity links.",
    )
    tv.declare_relation(
        "purpose_c_dependency",
        [
            Role("counterparty", RoleType.TEXT),
            Role("contract", RoleType.REFERENT),
            Role("open_invoice_ids", RoleType.TEXT),
            Role("obligation_kinds", RoleType.TEXT),
            Role("status", RoleType.TEXT),
        ],
        mode=RelationMode.DERIVED,
        description="Purpose C commercial dependencies.",
    )


COMMERCIAL_CLUSTERS: list[dict] = [
    {
        "crm": "HEL-441",
        "billing_name": "Helion Robotics Limited",
        "contract": "MSA-HELION-2019",
        "registry": ["11847201"],
    },
    {
        "crm": "NBA-102",
        "billing_name": "Northbridge Analytics Inc.",
        "contract": "MSA-NBA-2021",
        "registry": ["3840192", "2019-0008841"],
    },
    {
        "crm": "OAK-77",
        "billing_name": "Oakfield Logistik GmbH",
        "contract": "MSA-OAK-2018",
        "registry": ["HRB 88421"],
    },
    {
        "crm": "MER-55",
        "billing_name": "Meridian Energy Partners LLC",
        "contract": "MSA-MER-2024",
        "registry": ["4721193"],
    },
    {
        "crm": "VEL-19",
        "billing_name": "Vellum Print Co Ltd",
        "contract": "SOW-VEL-2022",
        "registry": ["09338441"],
    },
]


def cluster_for_crm(crm_id: str) -> dict | None:
    for cluster in COMMERCIAL_CLUSTERS:
        if cluster["crm"] == crm_id:
            return cluster
    return None


def cluster_for_billing(billed_name: str) -> dict | None:
    for cluster in COMMERCIAL_CLUSTERS:
        if cluster["billing_name"] == billed_name:
            return cluster
    return None


CONTRACT_SPECS: dict[str, dict] = {
    "MSA-HELION-2019": {
        "file": "MSA-HELION-2019.md",
        "counterparty": "Helion Robotics Ltd.",
        "effective_date": "2019-03-12",
        "term_text": "36 months, then successive 12-month periods unless either party gives 60 days' written notice.",
        "expiry_date": "",
        "term_kinds": ["rolling_term"],
        "clauses": [
            "assignment_notice_required",
            "change_of_control_consent",
        ],
        "active": True,
    },
    "MSA-NBA-2021": {
        "file": "MSA-NBA-2021.md",
        "counterparty": "Northbridge Analytics, Inc.",
        "effective_date": "2021-06-04",
        "term_text": "24 months. The agreement auto-renews for successive 12-month periods unless either party gives 90 days' written notice before the then-current term ends.",
        "expiry_date": "",
        "term_kinds": ["auto_renewal"],
        "clauses": [
            "change_of_control_termination",
            "assignment_competitor_prohibition",
        ],
        "active": True,
    },
    "MSA-OAK-2018": {
        "file": "MSA-OAK-2018.md",
        "counterparty": "Oakfield Logistics GmbH",
        "effective_date": "2018-09-01",
        "term_text": "rolling 12-month periods.",
        "expiry_date": "",
        "term_kinds": ["rolling_term"],
        "clauses": [
            "exclusivity",
            "assignment_consent_required",
            "change_of_control_silent",
        ],
        "active": True,
    },
    "MSA-MER-2024": {
        "file": "MSA-MER-2024.md",
        "counterparty": "Meridian Energy Partners LLC",
        "effective_date": "2024-02-02",
        "term_text": "12 months, then month-to-month.",
        "expiry_date": "",
        "term_kinds": ["rolling_term"],
        "clauses": [
            "assignment_competitor_prohibition",
            "assignment_consent_required",
            "change_of_control_termination",
        ],
        "active": True,
    },
    "SOW-VEL-2022": {
        "file": "SOW-VEL-2022.md",
        "counterparty": "Vellum Print Co Ltd",
        "effective_date": "2022-01-18",
        "term_text": "Expiry: 31 December 2023 (not renewed).",
        "expiry_date": "2023-12-31",
        "term_kinds": ["expired_fixed"],
        "clauses": [
            "change_of_control_none",
            "assignment_unrestricted",
        ],
        "active": False,
    },
}


def load_crm(tv: TaskView) -> None:
    with (SOURCES / "crm.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            ref = f"crm:{row['crm_account_id']}"
            tv.add_referent(
                ref,
                label=row["account_name"],
                grounding=[
                    Grounding(
                        GroundingKind.SOURCE,
                        "crm.csv",
                        f"row {row['crm_account_id']}",
                    )
                ],
            )
            tv.assert_tuple(
                "crm_record",
                {
                    "account": ref,
                    "account_name": row["account_name"],
                    "domain": row["domain"],
                    "country": row["country"],
                    "status": row["status"],
                },
                grounding=[
                    Grounding(
                        GroundingKind.SOURCE,
                        "crm.csv",
                        f"row {row['crm_account_id']}",
                    )
                ],
            )


def load_invoices(tv: TaskView) -> None:
    invoices = json.loads((SOURCES / "billing" / "invoices.json").read_text())
    for row in invoices:
        inv_ref = f"invoice:{row['invoice_id']}"
        tv.add_referent(
            inv_ref,
            label=row["invoice_id"],
            grounding=[
                Grounding(
                    GroundingKind.SOURCE,
                    "billing/invoices.json",
                    row["invoice_id"],
                )
            ],
        )
        billing_ref = f"billing:{row['billed_name']}"
        tv.add_referent(
            billing_ref,
            label=row["billed_name"],
            grounding=[
                Grounding(
                    GroundingKind.SOURCE,
                    "billing/invoices.json",
                    row["billed_name"],
                )
            ],
        )
        tv.assert_tuple(
            "invoice_record",
            {
                "invoice": inv_ref,
                "billed_name": row["billed_name"],
                "amount": row["amount"],
                "currency": row["currency"],
                "period": row["period"],
                "status": row["status"],
            },
            grounding=[
                Grounding(
                    GroundingKind.SOURCE,
                    "billing/invoices.json",
                    row["invoice_id"],
                )
            ],
        )


def load_registry(tv: TaskView) -> None:
    with (SOURCES / "company_registry.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            ref = f"registry:{row['company_number']}"
            tv.add_referent(
                ref,
                label=row["legal_name"],
                grounding=[
                    Grounding(
                        GroundingKind.SOURCE,
                        "company_registry.csv",
                        f"row {row['company_number']}",
                    )
                ],
            )
            tv.assert_tuple(
                "registry_record",
                {
                    "company": ref,
                    "legal_name": row["legal_name"],
                    "jurisdiction": row["jurisdiction"],
                    "status": row["status"],
                },
                grounding=[
                    Grounding(
                        GroundingKind.SOURCE,
                        "company_registry.csv",
                        f"row {row['company_number']}",
                    )
                ],
            )


def load_contracts(tv: TaskView) -> None:
    for contract_id, spec in CONTRACT_SPECS.items():
        ref = f"contract:{contract_id}"
        path = f"sources/contracts/{spec['file']}"
        tv.add_referent(
            ref,
            label=contract_id,
            grounding=[Grounding(GroundingKind.SOURCE, path, "header")],
        )
        tv.assert_tuple(
            "contract_record",
            {
                "contract": ref,
                "counterparty_text": spec["counterparty"],
                "effective_date": spec["effective_date"],
                "term_text": spec["term_text"],
                "expiry_date": spec["expiry_date"],
            },
            grounding=[Grounding(GroundingKind.SOURCE, path, "header")],
        )
        for term_kind in spec["term_kinds"]:
            tv.assert_tuple(
                "contract_term_kind",
                {"contract": ref, "term_kind": term_kind},
                grounding=[Grounding(GroundingKind.SOURCE, path, "term")],
            )
        for clause_kind in spec["clauses"]:
            tv.assert_tuple(
                "contract_clause",
                {"contract": ref, "clause_kind": clause_kind},
                grounding=[Grounding(GroundingKind.SOURCE, path, "clauses")],
            )
        tv.assert_tuple(
            "contract_active",
            {"contract": ref, "active": spec["active"]},
            grounding=[
                Grounding(
                    GroundingKind.SOURCE,
                    path,
                    f"active as of {EVAL_DATE}",
                )
            ],
        )


def load_candidates(tv: TaskView) -> None:
    registry_norms: dict[str, str] = {}
    for row in tv.query('SELECT company_id, legal_name FROM registry_record'):
        registry_norms[row["company_id"]] = normalize_name(row["legal_name"])

    contract_counterparty_norm: dict[str, str] = {}
    for row in tv.query(
        "SELECT contract_id, counterparty_text FROM contract_record"
    ):
        contract_counterparty_norm[row["contract_id"]] = normalize_name(
            row["counterparty_text"]
        )

    for cluster in COMMERCIAL_CLUSTERS:
        crm_ref = f"crm:{cluster['crm']}"
        billing_ref = f"billing:{cluster['billing_name']}"
        contract_ref = f"contract:{cluster['contract']}"
        tv.assert_tuple(
            "crm_to_billing_candidate",
            {"crm_account": crm_ref, "billing_name": billing_ref},
            grounding=[
                Grounding(
                    GroundingKind.SOURCE,
                    "commercial_notes.md",
                    f"cluster {cluster['crm']}",
                )
            ],
        )
        billing_norm = normalize_name(cluster["billing_name"])
        for company_number in cluster["registry"]:
            registry_ref = f"registry:{company_number}"
            reg_norm = registry_norms[registry_ref]
            if billing_norm == reg_norm or billing_norm in reg_norm or reg_norm in billing_norm:
                tv.assert_tuple(
                    "billing_to_registry_candidate",
                    {
                        "billing_name": billing_ref,
                        "registry_company": registry_ref,
                    },
                    grounding=[
                        Grounding(
                            GroundingKind.SOURCE,
                            "company_registry.csv",
                            company_number,
                        )
                    ],
                )
        cp_norm = contract_counterparty_norm[contract_ref]
        crm_rows = tv.query(
            "SELECT account_name FROM crm_record WHERE account_id = ?",
            (crm_ref,),
        )
        crm_norm = normalize_name(crm_rows[0]["account_name"])
        for counterparty_ref, norm in (
            (billing_ref, billing_norm),
            (crm_ref, crm_norm),
        ):
            if norm == cp_norm or norm in cp_norm or cp_norm in norm:
                tv.assert_tuple(
                    "counterparty_to_contract_candidate",
                    {"counterparty": counterparty_ref, "contract": contract_ref},
                    grounding=[
                        Grounding(
                            GroundingKind.SOURCE,
                            f"sources/contracts/{CONTRACT_SPECS[cluster['contract']]['file']}",
                            "counterparty",
                        )
                    ],
                )


def register_derivations(tv: TaskView) -> None:
    tv.register_derivation(
        "acquisition_relevant_clause",
        sql="""
        SELECT contract_id, clause_kind
        FROM contract_clause
        WHERE clause_kind IN (
            'change_of_control_consent',
            'change_of_control_termination',
            'assignment_consent_required',
            'assignment_notice_required',
            'assignment_competitor_prohibition'
        )
        """,
        inputs=["contract_clause"],
    )
    tv.register_derivation(
        "invoice_contract_link",
        sql="""
        WITH invoice_billing AS (
            SELECT invoice_id, 'billing:' || billed_name AS billing_ref
            FROM invoice_record
        ),
        billing_contract AS (
            SELECT ij.left_id AS billing_ref, ij.right_id AS contract_id
            FROM identity_judgment ij
            WHERE ij.left_id LIKE 'billing:%'
              AND ij.right_id LIKE 'contract:%'
              AND ij.disposition IN ('SAME_ENTITY', 'UNRESOLVED')
            UNION
            SELECT ij.right_id AS billing_ref, ij.left_id AS contract_id
            FROM identity_judgment ij
            WHERE ij.right_id LIKE 'billing:%'
              AND ij.left_id LIKE 'contract:%'
              AND ij.disposition IN ('SAME_ENTITY', 'UNRESOLVED')
            UNION
            SELECT ctc.counterparty_id AS billing_ref, ctc.contract_id
            FROM counterparty_to_contract_candidate ctc
            WHERE ctc.counterparty_id LIKE 'billing:%'
              AND NOT EXISTS (
                SELECT 1 FROM identity_judgment ij
                WHERE (ij.left_id = ctc.counterparty_id AND ij.right_id = ctc.contract_id)
                   OR (ij.right_id = ctc.counterparty_id AND ij.left_id = ctc.contract_id)
              )
        )
        SELECT ib.invoice_id,
               bc.contract_id,
               CASE
                 WHEN EXISTS (
                   SELECT 1 FROM identity_judgment ij
                   WHERE ij.disposition = 'SAME_ENTITY'
                     AND (
                       (ij.left_id = ib.billing_ref AND ij.right_id = bc.contract_id)
                       OR (ij.right_id = ib.billing_ref AND ij.left_id = bc.contract_id)
                     )
                 ) THEN 'asserted'
                 WHEN EXISTS (
                   SELECT 1 FROM identity_judgment ij
                   WHERE ij.disposition = 'UNRESOLVED'
                     AND (
                       (ij.left_id = ib.billing_ref AND ij.right_id = bc.contract_id)
                       OR (ij.right_id = ib.billing_ref AND ij.left_id = bc.contract_id)
                     )
                 ) THEN 'unresolved'
                 ELSE 'asserted'
               END AS association
        FROM invoice_billing ib
        JOIN billing_contract bc ON bc.billing_ref = ib.billing_ref
        """,
        inputs=[
            "invoice_record",
            "identity_judgment",
            "counterparty_to_contract_candidate",
        ],
    )
    tv.register_derivation(
        "purpose_a_invoice",
        sql="""
        SELECT ir.invoice_id,
               ir.billed_name,
               ir.amount,
               ir.currency,
               ir.period,
               ir.status,
               icl.contract_id,
               icl.association
        FROM invoice_record ir
        JOIN invoice_contract_link icl ON icl.invoice_id = ir.invoice_id
        JOIN contract_active ca ON ca.contract_id = icl.contract_id AND ca.active = 1
        WHERE EXISTS (
            SELECT 1 FROM acquisition_relevant_clause arc
            WHERE arc.contract_id = icl.contract_id
        )
        """,
        inputs=[
            "invoice_record",
            "invoice_contract_link",
            "contract_active",
            "acquisition_relevant_clause",
        ],
    )
    tv.register_derivation(
        "purpose_b_link",
        sql="""
        SELECT ij.left_id AS left,
               ij.right_id AS right,
               ij.disposition AS epistemic
        FROM identity_judgment ij
        """,
        inputs=["identity_judgment"],
    )
    tv.register_derivation(
        "purpose_c_dependency",
        sql="""
        WITH open_invoices AS (
            SELECT 'billing:' || billed_name AS counterparty,
                   replace(invoice_id, 'invoice:', '') AS invoice_short
            FROM invoice_record
            WHERE status = 'open'
        ),
        obligations AS (
            SELECT contract_id, clause_kind AS kind
            FROM contract_clause
            WHERE clause_kind = 'exclusivity'
            UNION
            SELECT contract_id, term_kind AS kind
            FROM contract_term_kind
            WHERE term_kind IN ('auto_renewal', 'rolling_term')
        ),
        billing_contract AS (
            SELECT ij.left_id AS counterparty, ij.right_id AS contract_id
            FROM identity_judgment ij
            WHERE ij.left_id LIKE 'billing:%'
              AND ij.right_id LIKE 'contract:%'
              AND ij.disposition = 'SAME_ENTITY'
            UNION
            SELECT ij.right_id AS counterparty, ij.left_id AS contract_id
            FROM identity_judgment ij
            WHERE ij.right_id LIKE 'billing:%'
              AND ij.left_id LIKE 'contract:%'
              AND ij.disposition = 'SAME_ENTITY'
            UNION
            SELECT ctc.counterparty_id AS counterparty, ctc.contract_id
            FROM counterparty_to_contract_candidate ctc
            WHERE ctc.counterparty_id LIKE 'billing:%'
              AND NOT EXISTS (
                SELECT 1 FROM identity_judgment ij
                WHERE (ij.left_id = ctc.counterparty_id AND ij.right_id = ctc.contract_id)
                   OR (ij.right_id = ctc.counterparty_id AND ij.left_id = ctc.contract_id)
              )
        ),
        base AS (
            SELECT bc.counterparty,
                   bc.contract_id,
                   GROUP_CONCAT(DISTINCT oi.invoice_short) AS open_invoice_ids,
                   GROUP_CONCAT(DISTINCT ob.kind) AS obligation_kinds
            FROM billing_contract bc
            JOIN contract_active ca ON ca.contract_id = bc.contract_id AND ca.active = 1
            JOIN obligations ob ON ob.contract_id = bc.contract_id
            LEFT JOIN open_invoices oi ON oi.counterparty = bc.counterparty
            GROUP BY bc.counterparty, bc.contract_id
            HAVING COUNT(DISTINCT ob.kind) >= 1
               AND (
                 COUNT(DISTINCT oi.invoice_short) > 0
                 OR EXISTS (
                   SELECT 1 FROM contract_term_kind ctk
                   WHERE ctk.contract_id = bc.contract_id
                     AND ctk.term_kind IN ('auto_renewal', 'rolling_term')
                 )
               )
        )
        SELECT counterparty,
               contract_id,
               COALESCE(open_invoice_ids, '') AS open_invoice_ids,
               obligation_kinds,
               CASE
                 WHEN EXISTS (
                   SELECT 1 FROM identity_judgment ij
                   WHERE ij.disposition = 'UNRESOLVED'
                     AND (ij.left_id = counterparty OR ij.right_id = counterparty)
                 ) THEN 'unresolved'
                 ELSE 'dependent'
               END AS status
        FROM base
        """,
        inputs=[
            "invoice_record",
            "contract_clause",
            "contract_term_kind",
            "contract_active",
            "counterparty_to_contract_candidate",
            "identity_judgment",
        ],
    )


def run_derivations(tv: TaskView) -> None:
    tv.run_derivation(
        "acquisition_relevant_clause",
        completeness=Completeness(
            CompletenessStatus.COMPLETE, universe="contract_clause"
        ),
    )
    tv.run_derivation(
        "invoice_contract_link",
        completeness=Completeness(
            CompletenessStatus.COMPLETE, universe="counterparty_to_contract_candidate"
        ),
    )
    tv.run_derivation(
        "purpose_a_invoice",
        completeness=Completeness(
            CompletenessStatus.COMPLETE, universe="invoice_record"
        ),
    )
    tv.run_derivation(
        "purpose_b_link",
        completeness=Completeness(
            CompletenessStatus.COMPLETE, universe="identity_judgment"
        ),
    )
    tv.run_derivation(
        "purpose_c_dependency",
        completeness=Completeness(
            CompletenessStatus.COMPLETE, universe="contract_active"
        ),
    )


def compile_mechanical(tv: TaskView) -> None:
    declare_world_schema(tv)
    declare_derived_schema(tv)
    load_crm(tv)
    load_invoices(tv)
    load_registry(tv)
    load_contracts(tv)
    load_candidates(tv)
    register_derivations(tv)
