"""Frozen cases. Utterances are injected exactly. Intents stay evaluator-only."""

from __future__ import annotations

SCOPES = (
    "ONE_OCCURRENCE",
    "ONE_SOURCE_VALUE",
    "ONE_RELATION_OR_VOCABULARY",
    "ONE_PURPOSE",
    "WORLD",
    "UNKNOWN",
)

EPISTEMIC = (
    "MODEL_CORRECTION",
    "USER_CERTIFIED_POLICY",
    "USER_ASSERTED_EXTERNAL_FACT",
    "USER_UNCERTAINTY",
    "AMBIGUOUS",
)

CASES = [
    {
        "id": "case1_bare_rejection",
        "n": 1,
        "issue_id": "unique_applicable_limit",
        "utterance": "No, that's wrong.",
        "stage": "baseline",
        "previous_case": None,
        "accept_if_ready": None,
    },
    {
        "id": "case2_underspecified",
        "n": 2,
        "issue_id": "unique_applicable_limit",
        "utterance": "No, multiple limits can apply.",
        "stage": "baseline",
        "previous_case": None,
        "accept_if_ready": None,
    },
    {
        "id": "case3_substantive",
        "n": 3,
        "issue_id": "unique_applicable_limit",
        "utterance": (
            "No. A measurement may need to be compared against multiple genuinely different "
            "limit types, but duplicate or restated catalog rows should still collapse."
        ),
        "stage": "baseline",
        "previous_case": None,
        "accept_if_ready": "Yes, that's what I mean.",
    },
    {
        "id": "case4_purpose_scope",
        "n": 4,
        "issue_id": "unique_applicable_limit",
        "utterance": "Yes, but only for Purpose A. Don't make that a general rule.",
        "stage": "after_proposal",
        "previous_case": "case3_substantive",
        "accept_if_ready": "Yes, that's what I mean.",
    },
    {
        "id": "case5_world_generalization",
        "n": 5,
        "issue_id": "unique_applicable_limit",
        "utterance": "That's generally true, not just for this analysis.",
        "stage": "after_proposal",
        "previous_case": "case4_purpose_scope",
        "accept_if_ready": "Yes, that's what I mean.",
    },
    {
        "id": "case6_uncertainty",
        "n": 6,
        "issue_id": "nodi_semantics",
        "utterance": "I don't know what 9 means. Don't infer it from the pattern in the data.",
        "stage": "baseline",
        "previous_case": None,
        "accept_if_ready": "Yes, that's what I mean.",
    },
    {
        "id": "case7_policy",
        "n": 7,
        "issue_id": "document_authority",
        "utterance": "For this analysis, if the final permit and fact sheet disagree, use the final permit.",
        "stage": "baseline",
        "previous_case": None,
        "accept_if_ready": "Yes, that's what I mean.",
    },
    {
        "id": "case8_external_fact",
        "n": 8,
        "issue_id": "document_authority",
        "utterance": "The final permit legally overrides the fact sheet.",
        "stage": "baseline",
        "previous_case": None,
        "accept_if_ready": "Yes, that's what I mean.",
    },
]

# Hidden from host workspaces. Not NPDES law. Evaluator scoring only.
INTENTS = {
    "case1_bare_rejection": {
        "preferred_disposition": "NEEDS_CLARIFICATION",
        "intended_scope": "UNKNOWN",
        "epistemic": "AMBIGUOUS",
        "durable_mutation_before_accept": False,
        "allow_unnecessary_clarification": True,
        "notes": "Bare rejection; localize disagreement; no durable mutation.",
    },
    "case2_underspecified": {
        "preferred_disposition": "NEEDS_CLARIFICATION",
        "intended_scope": "UNKNOWN",
        "epistemic": "AMBIGUOUS",
        "durable_mutation_before_accept": False,
        "allow_unnecessary_clarification": True,
        "notes": "Multiple plausible readings of 'multiple limits' with different blast radii.",
    },
    "case3_substantive": {
        "preferred_disposition": "READY_FOR_ACCEPTANCE",
        "intended_scope": "ONE_PURPOSE",
        "epistemic": "MODEL_CORRECTION",
        "durable_mutation_before_accept": False,
        "allow_unnecessary_clarification": False,
        "notes": "Meaning resolved; infer Purpose A rather than WORLD; expose consequences.",
    },
    "case4_purpose_scope": {
        "preferred_disposition": "READY_FOR_ACCEPTANCE",
        "intended_scope": "ONE_PURPOSE",
        "epistemic": "USER_CERTIFIED_POLICY",
        "durable_mutation_before_accept": False,
        "allow_unnecessary_clarification": False,
        "notes": "Narrow Case 3 proposal to Purpose A; no accidental WORLD broadening.",
    },
    "case5_world_generalization": {
        "preferred_disposition": "READY_FOR_ACCEPTANCE",
        "intended_scope": "WORLD",
        "epistemic": "USER_CERTIFIED_POLICY",
        "durable_mutation_before_accept": False,
        "allow_unnecessary_clarification": False,
        "notes": "Promote the referred proposition only; do not drag Purpose B/C machinery.",
    },
    "case6_uncertainty": {
        "preferred_disposition": "READY_FOR_ACCEPTANCE",
        "intended_scope": "ONE_SOURCE_VALUE",
        "epistemic": "USER_UNCERTAINTY",
        "durable_mutation_before_accept": False,
        "allow_unnecessary_clarification": False,
        "notes": "Code 9 stays uninterpreted; do not close from structural correlation.",
    },
    "case7_policy": {
        "preferred_disposition": "READY_FOR_ACCEPTANCE",
        "intended_scope": "ONE_PURPOSE",
        "epistemic": "USER_CERTIFIED_POLICY",
        "durable_mutation_before_accept": False,
        "allow_unnecessary_clarification": False,
        "notes": "Analysis policy; not filename-derived fact; human/policy provenance.",
    },
    "case8_external_fact": {
        "preferred_disposition": "READY_FOR_ACCEPTANCE",
        "intended_scope": "ONE_PURPOSE",
        "epistemic": "USER_ASSERTED_EXTERNAL_FACT",
        "durable_mutation_before_accept": False,
        "allow_unnecessary_clarification": True,
        "notes": "Unverified external claim; must not become source-established World truth.",
    },
}
