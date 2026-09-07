"""Frozen prompts. Do not tune between Arm B trials."""

from __future__ import annotations

PASS_TASK = """You are an isolated research probe. You are not the product constructor.

A draft semantic construction already exists as construction.py. Do not regenerate the ontology from scratch.
Do not overwrite construction.py until a later stage explicitly allows a disposable dry-run copy under dry_run/.

You may read purposes/, PRINCIPLES.md, WORLD_API.md, ISSUES.md, sources/, documents/, and construction.py.

Authoritative sources in this workspace include structured CSVs and permit-package document text under documents/.
There are no hidden gold answers.

Human-style claims are not automatically source truth. Structural correlation in a CSV is not a code legend.
Training-data or web knowledge is not source evidence. If a definition is not in a workspace file, UNRESOLVED is correct.
Do not invent entities, relation families, or purposes.

Do not read files outside this workspace.
Do not run a broad search for “anything semantically useful.”
Do not use web search.
"""

RETRIEVE_PROMPT = (
    "Read PASS_TASK.md, OBLIGATION.md, BUDGET.md, documents/INDEX.md, and construction.py as needed. "
    "Resolve this semantic obligation, not its individual occurrences. "
    "First write EVIDENCE_PLAN.json with keys: proposition, would_establish, would_refute, "
    "likely_authoritative_source_types, insufficient_alone, unknowable_from_structured_data_alone. "
    "Then inspect only evidence bearing on this exact obligation. Soft budget: at most 5 documents opened "
    "and at most 8 retained snippets unless you write BUDGET_EXCEPTION.md explaining why. "
    "Write RETRIEVAL_LOG.json with keys: structured_inspected, documents_opened, sections_inspected, "
    "snippets_inspected, queries_or_actions, n_documents_opened, approx_chars_inspected. "
    "Then write PACKET.json with keys: obligation_id, exact_semantic_question, purpose, relation_contract, "
    "candidate_interpretations, retained_snippets (list of {source_id, location, text, why_retained}), "
    "contradictory_evidence, known_limitations, allowed_dispositions "
    "(SUPPORTED_RESOLUTION, SUPPORTED_NEGATIVE, UNRESOLVED). "
    "Snippets must be exact enough to audit. Each snippet source_id must be a workspace path "
    "(documents/... or sources/...). Do not cite web pages, EPA dictionaries, or training-data legends. "
    "If the workspace does not contain establishing text, retain that limitation in the packet. "
    "If the obligation conflates materially different questions demonstrated by retrieved evidence, "
    "write REFINEMENT.json with parent, children, why_necessary, occurrence_partition, mechanically_computable. "
    "Do not overwrite construction.py. Stop."
)

ADJUDICATE_PROMPT = (
    "Read PASS_TASK_ADJUDICATE.md and PACKET.json only (and construction.py if you need to draft a disposable edit). "
    "You must not search documents/ or sources/. Judge only the frozen packet. "
    "Write JUDGMENT.json with keys: disposition (SUPPORTED_RESOLUTION, SUPPORTED_NEGATIVE, UNRESOLVED), "
    "grounding, interpretation, epistemic_basis "
    "(SOURCE_ESTABLISHED, MECHANICALLY_DERIVED, USER_CERTIFIED_POLICY, USER_ASSERTED_EXTERNAL_FACT, "
    "MODEL_HYPOTHESIS, UNRESOLVED), scope (ONE_OCCURRENCE, ONE_SOURCE_VALUE, ONE_RELATION_OR_VOCABULARY, "
    "ONE_PURPOSE, WORLD), remaining_uncertainty, failure_mode_if_unresolved "
    "(EVIDENCE_INSUFFICIENT, RETRIEVAL_FAILURE, OBLIGATION_TOO_BROAD, CONTRACT_INSUFFICIENT, OTHER, or null). "
    "A plausible interpretation is not enough. CSV correlation is not enough. "
    "Snippets whose source_id is not a workspace path (documents/ or sources/) are not admissible evidence. "
    "If insufficient, disposition UNRESOLVED. "
    "Write PROPOSAL.json with keys: interpretation, scope, epistemic_basis, exact_grounding, semantic_delta, "
    "affected_obligations, affected_occurrence_count, remaining_uncertainty, admit "
    "(ADMIT_DISPOSABLE, UNRESOLVED, UNVERIFIED_PROPOSAL). "
    "WORLD scope without SOURCE_ESTABLISHED grounding must not be admitted as World truth. "
    "If ADMIT_DISPOSABLE, write dry_run/construction.py by copying construction.py and applying a reusable "
    "semantic mapping (not per-row model judgments). If UNRESOLVED or UNVERIFIED_PROPOSAL, do not change construction. "
    "Write REVIEW.md: what you investigated, what you found, what evidence supports it, what remains uncertain, "
    "what would change if admitted. Stop."
)

OCCURRENCE_PROMPT = (
    "Read PASS_TASK.md, OCCURRENCE.md, documents/INDEX.md, and sources as needed. "
    "Determine the semantic issue needed for THIS ONE occurrence only. You are not given a factorized obligation "
    "covering sibling rows. Inspect authoritative evidence if needed. "
    "Write JUDGMENT.json with keys: occurrence_id, semantic_question_used, disposition "
    "(SUPPORTED_RESOLUTION, SUPPORTED_NEGATIVE, UNRESOLVED), interpretation, grounding, "
    "documents_opened, snippets (list of {source_id, text}), remaining_uncertainty. "
    "source_id must be a workspace path. Training-data or web code legends are not evidence. "
    "If this workspace does not establish the meaning, disposition UNRESOLVED. "
    "Do not overwrite construction.py. Stop."
)

PASS_TASK_ADJUDICATE = """You are a bounded adjudicator. The evidence packet is frozen.

Do not search the broader corpus. Do not invent new entities or relation families.
Do not rewrite the ontology or the declared purpose.
Do not infer semantics only from structural correlation.
Do not treat training-data or web knowledge as evidence.
If a retained snippet's source_id is not a workspace path, ignore it.
If the packet does not establish a proposition from workspace sources, return UNRESOLVED.
"""
