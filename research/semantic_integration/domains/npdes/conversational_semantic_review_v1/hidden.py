"""Evaluator-only expert packets and interventions. Never copied into a host workspace."""

from __future__ import annotations

# Experimental expert stances. Not claims about real NPDES law. Not GOLD.

PACKETS = {
    "unique_applicable_limit": {
        "issue_id": "unique_applicable_limit",
        "stance_summary": "interval-then-one, not raw-catalog uniqueness",
        "distinctions": [
            "After intersecting a measurement period with a limit's effective dates, this analysis wants at most one governing numeric limit.",
            "Two rows that are successive stages with non-overlapping dates are not a conflict; they are the same selection problem solved by dates.",
            "Two rows whose intervals still overlap after that filter are a real conflict, not two valid simultaneous answers.",
            "Seasonal month flags qualify the same limit's applicability; they do not create a second simultaneous governing limit.",
        ],
        "must_not_accept": [
            "collapsing staged dated rows into one identity before date filtering",
            "treating every catalog restatement as a second governing limit after dates already selected one",
        ],
        "uncertain_about": [],
    },
    "nodi_semantics": {
        "issue_id": "nodi_semantics",
        "stance_summary": "C and 9 are different; 9 is unknown; do not infer from glyphs",
        "distinctions": [
            "NODI code C and NODI code 9 are not interchangeable.",
            "The expert does not know what code 9 means in this dataset and forbids inferring meaning from the digit 9 or from the letters of C.",
            "An empty NODI with a missing numeric value is not the same state as a populated NODI code.",
            "The expert would distinguish 'no discharge occurred' from 'monitoring was not required' but will not assign either meaning to these codes without a legend.",
        ],
        "must_not_accept": [
            "code 9 means not required because 9 looks like a special case",
            "all NODI codes share one missing-evidence meaning",
        ],
        "uncertain_about": ["meaning of code 9", "meaning of code C without a legend"],
    },
    "permit_comments_when_discharging": {
        "issue_id": "permit_comments_when_discharging",
        "stance_summary": "WHEN DISCHARGING is discharge-occurrence, not seasonal and not aggregation",
        "distinctions": [
            "WHEN DISCHARGING is about whether a discharge occurred in the period, which may make monitoring applicable or not.",
            "It is not a wet-season vs dry-season schedule and not a geometric-mean aggregation instruction.",
            "Geometric-mean comments are a different question (how to combine numbers).",
            "Pass/fail comments are a different question (how a result is coded).",
            "The expert will not close WHEN DISCHARGING as always-required or never-required from the phrase alone.",
        ],
        "must_not_accept": [
            "all nonempty comments are the same unresolved blob",
            "WHEN DISCHARGING means monitoring is never required",
            "WHEN DISCHARGING is a seasonal month flag",
        ],
        "uncertain_about": ["whether discharge actually occurred in any given FY2025 period"],
    },
}

INTERVENTIONS = {
    "H1": [
        {
            "id": "H1_acceptance_unique",
            "kind": "ACCEPTANCE",
            "issue_id": "unique_applicable_limit",
            "intended_scope": "one purpose requirement (Purpose A uniqueness after interval filter)",
            "epistemic": "USER_CERTIFIED_POLICY",
            "stance": (
                "Yes: for this analysis, after you restrict to the measurement period and the limit's effective dates, "
                "exactly one governing numeric limit is the right rule. If two still overlap, that is a conflict to leave unresolved, "
                "not two valid answers."
            ),
            "speak_naturally": True,
        },
        {
            "id": "H1_uncertainty_nodi",
            "kind": "UNCERTAINTY",
            "issue_id": "nodi_semantics",
            "intended_scope": "one source value family (NODI codes, especially 9)",
            "epistemic": "USER_UNCERTAINTY",
            "stance": (
                "I don't know what NODI code 9 means here. Do not infer it from the digit or treat it as the same as code C. "
                "Leave those cases unresolved until there is a legend. Empty NODI is a different situation."
            ),
            "speak_naturally": True,
        },
    ],
    "H2": [
        {
            "id": "H2_correction_comments",
            "kind": "CORRECTION",
            "issue_id": "permit_comments_when_discharging",
            "intended_scope": "one semantic relation (comment families must stay distinct)",
            "epistemic": "MODEL_CORRECTION",
            "stance": (
                "No. Those comment rows are related because they sit in the same field, but they must remain separate questions. "
                "WHEN DISCHARGING is about whether discharge occurred. Geometric mean is how to aggregate. Pass/fail is how a result is coded. "
                "Do not fold them into one comment-semantics bucket."
            ),
            "speak_naturally": True,
        },
        {
            "id": "H2_qualification_when",
            "kind": "QUALIFICATION",
            "issue_id": "permit_comments_when_discharging",
            "intended_scope": "one source value (WHEN DISCHARGING phrase) under Purpose B",
            "epistemic": "USER_CERTIFIED_POLICY",
            "stance": (
                "Usually WHEN DISCHARGING means monitoring depends on whether there was a discharge. "
                "It does not by itself change the numeric limit. If a row's comment is only about geometric mean or pass/fail, that exception is not a discharge condition."
            ),
            "speak_naturally": True,
        },
    ],
    "H3": [
        {
            "id": "H3_bare_no",
            "kind": "AMBIGUOUS_REJECTION",
            "issue_id": "unique_applicable_limit",
            "intended_scope": "unknown — host must localize",
            "epistemic": "MODEL_CORRECTION",
            "stance": "No, that's wrong.",
            "speak_naturally": False,
            "exact_utterance": "No, that's wrong.",
            "good_localization": [
                "one governing limit vs many",
                "which records were matched",
                "date/interval filter vs catalog identity",
            ],
        },
        {
            "id": "H3_document_policy",
            "kind": "CORRECTION",
            "issue_id": "document_authority",
            "intended_scope": "one purpose policy (authority ranking is policy, not a filename fact)",
            "epistemic": "USER_CERTIFIED_POLICY",
            "stance": (
                "For this analysis, if we had the documents, the final permit would govern over a fact sheet. "
                "We do not have the text. Do not infer that ranking from filenames, and do not treat the inventory as if the narrative conditions were already known. "
                "Keep them unresolved."
            ),
            "speak_naturally": True,
        },
    ],
}

FOLLOWUP_AFTER_BARE_NO = (
    "The problem is not the date matching. The problem is treating uniqueness as a physical identity collapse. "
    "Keep staged dated limits as separate records and select by dates; uniqueness is a purpose rule after that selection, not a reason to merge identities."
)
