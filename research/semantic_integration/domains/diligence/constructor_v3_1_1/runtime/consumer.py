"""Stable consumer semantic interface. IMPLEMENTATION_DETAIL for diligence A/B/C/D.

FOUNDATIONAL: consumer programs depend on these field identities, not constructor table names.
DOMAIN_POLICY: the field set is the diligence purpose ABI, not a kernel primitive.
"""

from __future__ import annotations

IDENTITY_DISPOSITIONS = frozenset({"SAME_ENTITY", "DISTINCT", "UNRESOLVED"})
CLAUSE_POSITIVE = frozenset({"PRESENT", "ACCEPT", "TRUE", "YES"})
CLAUSE_NEGATIVE = frozenset({"ABSENT", "REJECT", "FALSE", "NO"})

CONSUMER_FIELDS = frozenset(
    {
        "invoice_id",
        "billed_name",
        "amount",
        "currency",
        "period",
        "status",
        "contract_id",
        "counterparty_text",
        "active",
        "clause_kind",
        "left",
        "right",
        "disposition",
        "account",
        "account_name",
        "company_number",
        "legal_name",
    }
)

JOIN_IDENTITIES = frozenset({"invoice", "contract", "account", "entity"})

CANONICAL_RELATIONS = (
    "invoice_record",
    "contract_record",
    "contract_active",
    "contract_clause_kind",
    "identity_judgment",
    "crm_record",
    "registry_record",
)

INVOICE_FIELDS = (
    "invoice_id",
    "billed_name",
    "amount",
    "currency",
    "period",
    "status",
)

REQUIRED_IDENTITY_TO_RELATION = {
    "invoice_id": "invoice_record",
    "billed_name": "invoice_record",
    "amount": "invoice_record",
    "currency": "invoice_record",
    "period": "invoice_record",
    "status": "invoice_record",
    "contract_id": "contract_record",
    "counterparty_text": "contract_record",
    "active": "contract_active",
    "clause_kind": "contract_clause_kind",
    "left": "identity_judgment",
    "right": "identity_judgment",
    "disposition": "identity_judgment",
}

CONSUMER_FIELD_TO_RELATION = {
    **REQUIRED_IDENTITY_TO_RELATION,
    "account": "crm_record",
    "account_name": "crm_record",
    "company_number": "registry_record",
    "legal_name": "registry_record",
}
