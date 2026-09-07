"""Frozen prompts. Do not tune between trials of the same microprobe."""

from __future__ import annotations

PASS_TASK = """You are an isolated research probe. You are not the product constructor.

A draft semantic construction already exists in this workspace (`construction.py` if present). Do not regenerate the ontology from scratch. Do not look for hidden gold answers. They are not here.

You may read purposes/, PRINCIPLES.md, WORLD_API.md, ISSUES.md, DRAFT_NOTES.md, sources, and construction.py.

You converse with a domain expert in ordinary language. Do not require them to use ontology terminology, checkboxes, or formal rule syntax. Alternatives may narrow your search; they must never constrain what the expert is allowed to say.

Human feedback is not automatically source truth:
- a policy for this analysis may govern the purpose;
- a claim about the outside world must not be written as if the CSV asserted it;
- a correction to your representation may change the draft construction;
- "I don't know" stays unresolved. It is not false, not rejected, and not "not applicable".

Do not read files outside this workspace.
"""

MP1_PROMPT = (
    "Read PASS_TASK.md, purposes/, ISSUES.md, and construction.py as needed. "
    "For each issue in ISSUES.md: (1) write records/<issue_id>.json as a decision record with keys "
    "current_interpretation, status, why_it_matters, supporting_evidence_used, evidence_snippets_used, "
    "contracts_involved, alternatives_considered, affected_computations, remaining_uncertainty; "
    "(2) write conversation/<issue_id>.md explaining the issue to an ordinary domain expert in whatever "
    "conversational form you think is clearest so they could confirm, reject, qualify, or correct you. "
    "No required headings. No multiple choice. Do not invent evidence you did not use. "
    "Do not ask them to decide something the draft already established mechanically unless you say so. Stop when all four issues are written."
)

MP2_OPEN_PROMPT = (
    "Read PASS_TASK.md, ISSUES.md, and the draft notes. Focus only on the issue named in FOCUS.md. "
    "Write USER_MESSAGE.md: ask the domain expert about this issue so they can explain how they understand it. "
    "Do not offer your proposed interpretation. Do not give A/B/C choices. One message. Stop."
)

MP2_NEAR_PROMPT = (
    "Read PASS_TASK.md, ISSUES.md, construction.py as needed, and FOCUS.md. "
    "Write USER_MESSAGE.md to the domain expert giving: your current best interpretation, the evidence/reason you reached it, "
    "why the distinction matters, and one or more plausible alternatives if you genuinely considered them. "
    "Invite unrestricted correction. Do not ask them to pick A/B/C. One message. Stop."
)

PROXY_PROMPT = (
    "Read EXPERT_STANCE.md (your private notes on how you understand this). Read HOST_MESSAGE.md. "
    "Write REPLY.md: respond as that domain expert in ordinary conversation, 1-3 short paragraphs. "
    "Do not use ontology, API, or table-name jargon unless the host already used it. "
    "You may introduce distinctions the host did not list. Stay within your stance notes; do not invent a legal treatise. Stop."
)

MP3_EXPLAIN_PROMPT = (
    "Read PASS_TASK.md, ISSUES.md, FOCUS.md, and construction.py as needed. "
    "Write USER_MESSAGE.md explaining this one issue to an ordinary domain expert so they can confirm, reject, qualify, or correct you. "
    "Conversational form of your choosing. No multiple choice. Stop."
)

MP3_REVISE_PROMPT = (
    "Read USER_REPLY.md. That is the domain expert's response to USER_MESSAGE.md. "
    "Write INTERPRETATION.json with keys: utterance_understood, epistemic_kind "
    "(one of MODEL_CORRECTION, USER_CERTIFIED_POLICY, USER_ASSERTED_DOMAIN_FACT, USER_UNCERTAINTY, AMBIGUOUS), "
    "scope (one of one_occurrence, one_source_value, one_relation, one_purpose, general_world, unknown), "
    "change_planned, remaining_uncertainty. "
    "If the reply is too ambiguous to edit safely, write CLARIFY.md with one ordinary-language clarifying question and do not change construction.py. "
    "If the reply is clear enough, revise construction.py accordingly. Do not invent source facts. "
    "If they said they do not know, keep the issue unresolved; do not convert that into false or not-applicable. "
    "Then write CONSEQUENCE.md explaining in ordinary language what you changed and what you did not. Stop."
)

MP3_AFTER_CLARIFY_PROMPT = (
    "Read USER_REPLY.md (their answer to your clarifying question). "
    "Update INTERPRETATION.json. If now clear enough, revise construction.py and write CONSEQUENCE.md. "
    "If still ambiguous, leave construction.py unchanged and say so in CONSEQUENCE.md. Stop."
)
