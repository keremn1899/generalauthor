"""Frozen pass prompts. Same text for every trial. No gold ontology, no hidden pairs."""

from __future__ import annotations

PASS_ORDER = ("p0", "p1", "p2", "p3", "p4", "p5", "p6", "p7", "p8")

TIMEOUTS = {
    "p0": 600,
    "p1": 900,
    "p2": 1800,
    "p3": 900,
    "p4": 900,
    "p5": 1800,
    "p6": 900,
    "p7": 900,
    "p8": 1200,
    "p7_certified": 1200,
    "d_world_only": 1200,
}

COMMON = """You are one pass of a multi-pass semantic constructor.

The semantic calculus is frozen (KERNEL.md): Referent, named typed n-ary Relation, Derivation, plus grounding, origin, revision, stale/current, scope/completeness, and explicit unresolved state.

Do not add a primitive. Do not read files outside this workspace. Do not look for hidden expected outputs. They are not here.

PYTHONPATH=. so `import taskview` works. Use view_id="diligence-world" when opening world.sqlite.

Do not repair earlier passes. Prior pass artifacts are inputs. If they are incomplete, record the limitation in your output and continue.

Do not write purpose D. Do not reread sibling trials.
"""

P0 = COMMON + """
# Pass P0 — Intention compiler

Read purposes/visible_a.md, purposes/visible_b.md, purposes/visible_c.md.

Do not author domain relations yet. Do not compile the World.

Write 00_intention_contract.json with key "purposes" mapping "A","B","C" to objects, each with:

- objective
- universe_scope
- required_output_shape
- required_semantic_distinctions
- epistemic_requirements
- allowed_unresolved_states
- completeness_expectations
- purpose_specific_policies

Distinguish purpose policy/thresholds from world-true propositions.
"""

P1 = COMMON + """
# Pass P1 — Semantic vocabulary / admission design

Read sources/, 00_intention_contract.json, KERNEL.md.

Write 01_vocabulary.json with key "relations": a list of objects each with:

- name
- roles (ordered; each {name, type})
- role_types (same order, RoleType names)
- meaning (one sentence)
- admission: WORLD | PURPOSE
- construction_class: MECHANICAL | SEMANTIC | DERIVED
- required_by (purpose letters and/or computations)
- grounding_contract
- construction_rule
- candidate_generation_rule (if applicable)
- if SEMANTIC: unresolved_judgment, allowed_dispositions

Minimum sufficient vocabulary for A/B/C. Classify WORLD vs PURPOSE with the purpose-independence test. Do not persist purpose answers as World relations.
"""

P2 = COMMON + """
# Pass P2 — Mechanical compiler

Read sources/ and 01_vocabulary.json.

Compile only deterministic facts: parsing, explicit IDs, exact joins, normalized deterministic joins, dates, amounts, explicit clause wording when extraction is deterministic, candidate relations.

No semantic adjudication. Do not assert SAME_ENTITY, DISTINCT, or equivalent identity closures.

Write:
- 02_mechanical_world/world.sqlite (TaskView)
- 02_mechanical_report.json with counts: referents, base_tuples, candidate_tuples, notes

Every BASE tuple must be grounded to exact source locations.
"""

P3 = COMMON + """
# Pass P3 — Semantic-obligation generator

Read 00_intention_contract.json, 01_vocabulary.json, and 02_mechanical_world/world.sqlite.

Write 03_obligations.json as a list of objects:

- obligation_id
- relation
- values (role-value map)
- why_demanded
- required_by (purposes/computations)
- current_epistemic_state

Frontier = unresolved semantic judgments required by the declared purposes and not mechanically established.

Do not invent obligations from a hidden oracle. You have none.
"""

P4 = COMMON + """
# Pass P4 — Evidence selector

For each obligation in 03_obligations.json, write 04_packets/<obligation_id>.json with:

- obligation_id
- selected_observations (list of {source_path, location, excerpt})
- selection_rationale
- known_missing_information

Select a small packet. Do not copy the entire data room into each packet.
"""

P5 = COMMON + """
# Pass P5 — Semantic adjudicator

For each obligation, read its 04_packets/<obligation_id>.json.

Write 05_dispositions.json as a list of:

- obligation_id
- relation
- values
- disposition: SAME_ENTITY | DISTINCT | UNRESOLVED | ACCEPT | REJECT
- grounding (exact packet locations)
- rationale

Prefer unsupported uncertainty to unsupported semantic closure. No closed-world DISTINCT from absence. Ground every non-UNRESOLVED disposition.
"""

P6 = COMMON + """
# Pass P6 — World/Purpose admission

Read 01_vocabulary.json and 05_dispositions.json. Start from 02_mechanical_world/world.sqlite.

Persist admitted semantic commitments. Write:

- 06_admission.json listing each persistent relation/assertion class with admission WORLD|PURPOSE, reason, purpose_independence_test
- 06_world/world.sqlite

Do not automatically promote purpose outputs into World.
"""

P7 = COMMON + """
# Pass P7 — Derivation compiler

Read 00_intention_contract.json, 01_vocabulary.json, 06_world/world.sqlite.

Write 07_derivations.json listing each derived/output relation:

- output_relation
- required_input_relations
- optional_enrichment_relations
- epistemic_behavior
- completeness_assumptions
- deterministic_computation
- required_premise
- optional_enrichment
- blocking_unresolved_state
- non_blocking_unresolved_state

Also write construction/derivations/derive_purposes.py that can be run as:

python construction/derivations/derive_purposes.py

It must read 06_world/world.sqlite (or world/world.sqlite) and write purpose_ir/a/output.json, purpose_ir/b/output.json, purpose_ir/c/output.json in the schemas from the purpose files.

Ordinary Python/SQL only. Explicitly distinguish required vs optional premises and which unresolved states block vs do not block.
"""

P8 = COMMON + """
# Pass P8 — Purpose execution

Compute A/B/C by running construction/derivations/derive_purposes.py over the compiled World.

Do not read sources/ (crm.csv, invoices.json, company_registry.csv, contracts, commercial_notes.md). World must suffice.

Write copies:

- 08_outputs/a.json
- 08_outputs/b.json
- 08_outputs/c.json

matching purpose_ir/a/output.json, purpose_ir/b/output.json, purpose_ir/c/output.json.
"""

P7_CERTIFIED = COMMON + """
# Diagnostic P7 only — certified World provided

This workspace contains a compiled World and purposes A/B/C. Sources are absent.

Do not modify world.sqlite relation meanings. Produce only purpose derivations.

Write 07_derivations.json and construction/derivations/derive_purposes.py as in P7.

Then run the derivation and write 08_outputs/a.json, 08_outputs/b.json, 08_outputs/c.json and purpose_ir/{a,b,c}/output.json.
"""

D_WORLD_ONLY = """You are computing held-out purpose D against a compiled World.

Read D_TASK.md, KERNEL.md, and world/world.sqlite. Use PYTHONPATH=. and view_id="diligence-world".

Sources are not present. Do not search for crm.csv, invoices.json, contracts, or commercial_notes.

Write purpose_ir/d/output.json and 08_outputs/d.json in the schema in D_TASK.md.

Do not modify existing World relation meanings. Ordinary Python/SQL over World only.
"""

PROMPTS = {
    "p0": P0,
    "p1": P1,
    "p2": P2,
    "p3": P3,
    "p4": P4,
    "p5": P5,
    "p6": P6,
    "p7": P7,
    "p8": P8,
    "p7_certified": P7_CERTIFIED,
    "d_world_only": D_WORLD_ONLY,
}

FORBIDDEN_PROMPT_TOKENS = (
    "3840192",
    "2019-0008841",
    "Northbridge Analytics LLC",
    "Helion Industrial",
    "purpose_d",
    "INV-1001",
    "eligible_part",
    "acceptable_replacement",
)
