"""Canonical consumer interface = certified World slots. Not constructor relation names."""

from __future__ import annotations

IDENTITY_DISPOSITIONS = frozenset({"SAME_ENTITY", "DISTINCT", "UNRESOLVED"})
CLAUSE_POSITIVE = frozenset({"PRESENT", "ACCEPT", "TRUE", "YES"})
CLAUSE_NEGATIVE = frozenset({"ABSENT", "REJECT", "FALSE", "NO"})
CLAUSE_DISPOSITIONS = IDENTITY_DISPOSITIONS | CLAUSE_POSITIVE | CLAUSE_NEGATIVE | {"UNRESOLVED"}

INVOICE_ROLE_FIELDS = {
    "billed_name": "billed_name",
    "amount": "amount",
    "currency": "currency",
    "period": "period",
    "status": "status",
    "invoice_id": "invoice_id",
}
CONTRACT_ROLE_FIELDS = {
    "counterparty_text": "counterparty_text",
    "counterparty": "counterparty_text",
    "counterparty_name": "counterparty_text",
}
CRM_NAME_ROLES = {"account_name", "name"}
REGISTRY_NAME_ROLES = {"legal_name"}
ACTIVE_ROLES = {"active"}
CLAUSE_KIND_ROLES = {"clause_kind", "kind"}

CANONICAL_RELATIONS = (
    "invoice_record",
    "contract_record",
    "contract_active",
    "contract_clause_kind",
    "identity_judgment",
    "crm_record",
    "registry_record",
)
