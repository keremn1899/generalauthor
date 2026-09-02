"""R1 relation/purpose contracts. semantic_family_hint has no v2 behavior."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

Scope = Literal["WORLD", "PURPOSE"]


@dataclass
class RoleSpec:
    name: str
    type: str


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
    relation: str
    role: str
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


IDENTITY_CONTRACT = RelationContract(
    name="identity_judgment",
    roles=[RoleSpec("left", "TEXT"), RoleSpec("right", "TEXT")],
    role_types=["TEXT", "TEXT"],
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
    row_inclusion="active_contract_and_acquisition_clause",
    orientation="native",
)

PURPOSE_B = PurposeProjectionContract(
    purpose_id="B",
    output_fields=["left", "right", "epistemic"],
    identifier_rendering={},
    disposition_mapping={
        "SAME_ENTITY": "SAME_ENTITY",
        "DISTINCT": "DISTINCT",
        "UNRESOLVED": "UNRESOLVED",
        "REJECT": "DISTINCT",
    },
    orientation="class_rank",
    completeness="required identity links connecting crm, billing, contract, registry candidates",
)

PURPOSE_C = PurposeProjectionContract(
    purpose_id="C",
    output_fields=["counterparty", "contract_id", "open_invoice_ids", "obligation_kinds", "status"],
    identifier_rendering={"contract_id": "strip_contract_prefix", "open_invoice_ids": "strip_invoice_prefix"},
    allowed_kinds=["exclusivity", "auto_renewal", "rolling_term"],
    row_inclusion="active_and_declared_obligation_kind",
    disposition_mapping={"UNRESOLVED": "unresolved", "SAME_ENTITY": "dependent"},
)

PURPOSE_D = PurposeProjectionContract(
    purpose_id="D",
    output_fields=["invoice_id", "contract_id", "status"],
    identifier_rendering={"invoice_id": "strip_invoice_prefix", "contract_id": "strip_contract_prefix"},
    allowed_kinds=["assignment_notice_or_consent", "assignment_consent", "assignment_notice"],
    row_inclusion="open_invoice_and_assignment_notice_or_consent",
)


def contract_to_dict(contract: RelationContract) -> dict[str, Any]:
    return asdict(contract)
