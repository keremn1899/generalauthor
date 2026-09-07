"""Semantic contracts. Expected to evolve. Not the TaskView kernel.

FOUNDATIONAL: RoleSpec.semantic_identity is the ABI key a consumer field binds to.
EXPERIMENTALLY_MOTIVATED: semantic_family_hint is metadata with no runtime behavior.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

Scope = Literal["WORLD", "PURPOSE"]


@dataclass
class RoleSpec:
    name: str
    type: str
    semantic_identity: str | None = None


@dataclass
class Algebra:
    symmetric: bool = False
    transitive: bool = False
    conflicts_with: list[str] = field(default_factory=list)
    closure_policy: str = "no_closed_world"


@dataclass
class EpistemicContract:
    positive_disposition: str = "SAME_ENTITY"
    negative_disposition: str = "DISTINCT"
    unresolved_disposition: str = "UNRESOLVED"


@dataclass
class RelationContract:
    name: str
    roles: list[RoleSpec]
    role_types: list[str]
    meaning: str
    dispositions: list[str]
    scope: Scope
    grounding_contract: str
    algebra: Algebra = field(default_factory=Algebra)
    epistemic_contract: EpistemicContract = field(default_factory=EpistemicContract)
    allowed_value_classes: list[str] = field(default_factory=list)
    semantic_family_hint: str | None = None


@dataclass
class FieldSource:
    """Maps a consumer field to a declared semantic identity. Not a constructor table name."""

    semantic_identity: str
    transform: str = "identity"


@dataclass
class PurposeProjectionContract:
    purpose_id: str
    output_fields: list[str]
    field_sources: dict[str, FieldSource] = field(default_factory=dict)
    identifier_rendering: dict[str, str] = field(default_factory=dict)
    disposition_mapping: dict[str, str] = field(default_factory=dict)
    allowed_kinds: list[str] = field(default_factory=list)
    row_inclusion: str = ""
    orientation: str = "class_rank"
    completeness: str = ""
    allowed_dispositions: list[str] = field(default_factory=list)


def _fields(*names: str) -> dict[str, FieldSource]:
    return {name: FieldSource(semantic_identity=name) for name in names}


IDENTITY_CONTRACT = RelationContract(
    name="identity_judgment",
    roles=[
        RoleSpec("left", "TEXT", semantic_identity="left"),
        RoleSpec("right", "TEXT", semantic_identity="right"),
        RoleSpec("disposition", "TEXT", semantic_identity="disposition"),
    ],
    role_types=["TEXT", "TEXT", "TEXT"],
    meaning="Two referents denote the same legal counterparty, are distinct, or remain unresolved.",
    dispositions=["SAME_ENTITY", "DISTINCT", "UNRESOLVED"],
    scope="WORLD",
    grounding_contract="Bounded packet. SAME_ENTITY and DISTINCT require establishing evidence, not compatibility.",
    algebra=Algebra(symmetric=True, closure_policy="no_closed_world"),
    semantic_family_hint="IDENTITY",
)

PURPOSE_A = PurposeProjectionContract(
    purpose_id="A",
    output_fields=[
        "invoice_id",
        "billed_name",
        "amount",
        "currency",
        "period",
        "status",
        "contract_id",
        "association",
    ],
    field_sources=_fields(
        "invoice_id",
        "billed_name",
        "amount",
        "currency",
        "period",
        "status",
        "contract_id",
    ),
    identifier_rendering={"invoice_id": "strip_invoice_prefix", "contract_id": "strip_contract_prefix"},
    disposition_mapping={"SAME_ENTITY": "asserted", "UNRESOLVED": "unresolved"},
    allowed_kinds=[
        "change_of_control_consent",
        "change_of_control_termination",
        "assignment_notice_or_consent",
        "assignment_consent",
        "assignment_notice",
        "assignment_competitor_prohibition",
        "competitor_assignment_prohibition",
    ],
    allowed_dispositions=["asserted", "unresolved"],
    row_inclusion="active_contract_and_acquisition_clause",
    orientation="native",
)

PURPOSE_B = PurposeProjectionContract(
    purpose_id="B",
    output_fields=["left", "right", "epistemic"],
    field_sources=_fields("left", "right", "disposition"),
    identifier_rendering={},
    disposition_mapping={
        "SAME_ENTITY": "SAME_ENTITY",
        "DISTINCT": "DISTINCT",
        "UNRESOLVED": "UNRESOLVED",
        "REJECT": "DISTINCT",
    },
    allowed_dispositions=["SAME_ENTITY", "DISTINCT", "UNRESOLVED"],
    orientation="class_rank",
    completeness="required identity links connecting crm, billing, contract, registry candidates",
)

PURPOSE_C = PurposeProjectionContract(
    purpose_id="C",
    output_fields=["counterparty", "contract_id", "open_invoice_ids", "obligation_kinds", "status"],
    field_sources=_fields("contract_id", "clause_kind", "status"),
    identifier_rendering={"contract_id": "strip_contract_prefix", "open_invoice_ids": "strip_invoice_prefix"},
    allowed_kinds=["exclusivity", "auto_renewal", "rolling_term"],
    row_inclusion="active_and_declared_obligation_kind",
    disposition_mapping={"UNRESOLVED": "unresolved", "SAME_ENTITY": "dependent"},
)

PURPOSE_D = PurposeProjectionContract(
    purpose_id="D",
    output_fields=["invoice_id", "contract_id", "status"],
    field_sources=_fields("invoice_id", "contract_id"),
    identifier_rendering={"invoice_id": "strip_invoice_prefix", "contract_id": "strip_contract_prefix"},
    allowed_kinds=["assignment_notice_or_consent", "assignment_consent", "assignment_notice"],
    row_inclusion="open_invoice_and_assignment_notice_or_consent",
)


def contract_to_dict(contract: RelationContract) -> dict[str, Any]:
    return asdict(contract)


def purpose_to_dict(contract: PurposeProjectionContract) -> dict[str, Any]:
    payload = asdict(contract)
    payload["field_sources"] = {
        name: {"semantic_identity": src.semantic_identity, "transform": src.transform}
        for name, src in contract.field_sources.items()
    }
    return payload


def consumer_interface_payload() -> dict[str, Any]:
    from research.semantic_integration.domains.diligence.constructor_v3_1.runtime.consumer import (
        CONSUMER_FIELDS,
        JOIN_IDENTITIES,
    )

    return {
        "consumer_fields": sorted(CONSUMER_FIELDS),
        "join_identities": sorted(JOIN_IDENTITIES),
        "field_sources": {
            name: {"semantic_identity": name} for name in sorted(CONSUMER_FIELDS)
        },
        "note": "Programs depend on semantic_identity, not constructor relation or role names.",
    }
