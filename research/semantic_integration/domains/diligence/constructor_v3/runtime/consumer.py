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
