"""Frozen probe prompts. Do not tune between conditions."""

from __future__ import annotations

from research.semantic_integration.domains.npdes.constructor_v3_1_1_untouched.prompts import P5 as FROZEN_P5

COMMON_PROBE = """You are an isolated experimental probe, not a World constructor.

Do not write World facts. Do not invent closed-world negation. Do not look for hidden expected outputs. They are not here. Do not read files outside this workspace.
"""

B1 = COMMON_PROBE + """
# Condition B1 — oracle passage to bounded semantic obligation

Read purposes/visible_a.md, purposes/visible_b.md, purposes/visible_c.md, and PASSAGE.md.

Identify any semantic question whose resolution is necessary because a different interpretation of this passage could change the required computation. Formulate the smallest bounded semantic obligation. Do not answer it.

Allowed output:

NO_RELEVANT_OBLIGATION

or

OBLIGATION
- exact question/proposition
- affected purpose
- source locator
- semantic arguments/context required

Write exactly one JSON object to result.json with keys:
- kind: "NO_RELEVANT_OBLIGATION" or "OBLIGATION"
- question: string or null
- affected_purpose: "A" | "B" | "C" | "A,B" | "A,C" | "B,C" | "A,B,C" | null
- source_locator: string or null
- semantic_arguments: list of strings
- notes: string

Do not include gold identifiers. Do not determine whether the proposition is true.
"""

B2 = FROZEN_P5 + """

# Probe overlay — oracle obligation, frozen P5 protocol

This workspace contains exactly one oracle obligation in 03_obligations.json and one evidence packet in 04_packets/.

A labeled ORACLE INTERVENTION relation contract may be present in oracle_relation_contract.json. It is not a World vocabulary change. Use it only to understand the proposition semantics.

Judge that obligation using the P5 rules above.

Write 05_dispositions.json as a list of one object:
- obligation_id
- relation
- values
- disposition: ACCEPT | REJECT | UNRESOLVED
- grounding (exact packet locations)
- rationale

Prefer unsupported uncertainty to unsupported semantic closure. Ground every non-UNRESOLVED disposition. The packet does not include the correct disposition.
"""

B3 = COMMON_PROBE + """
# Condition B3 — purpose-aware clause nomination

Read purposes/visible_a.md, purposes/visible_b.md, purposes/visible_c.md, and SEGMENT.md.

SEGMENT.md is one mechanically bounded source segment. It is not a summary.

Identify passages in this segment whose interpretation could change the result of one or more declared purposes. Do not determine whether the proposition is true. Do not construct World facts. Return only exact source-located candidate passages and why their interpretation can affect computation.

Write result.json as a JSON object:
{
  "candidates": [
    {
      "source": "document path as given in the segment header",
      "locator": "page/section/table/footnote as given",
      "exact_span": "exact quoted text from the segment",
      "affected_purpose": "A" | "B" | "C" | combined,
      "computation_change_reason": "why a different interpretation could change A/B/C computation"
    }
  ]
}

If none, write {"candidates": []}. Do not nominate administrative boilerplate, historical description, or clearly non-operative rationale unless its interpretation could change A/B/C computation.
"""

B4 = B1  # exact B1 obligation-formulation protocol

C1 = COMMON_PROBE + """
# Context ablation C1 — target span only

Read purposes/visible_a.md, purposes/visible_b.md, purposes/visible_c.md, and PASSAGE.md.

PASSAGE.md contains only the exact target sentence/span, without heading, adjacent prose, table, or footnote context beyond that span.

Identify any semantic question whose resolution is necessary because a different interpretation of this passage could change the required computation. Formulate the smallest bounded semantic obligation. Do not answer it.

Write result.json with the same schema as:
- kind: "NO_RELEVANT_OBLIGATION" or "OBLIGATION"
- question, affected_purpose, source_locator, semantic_arguments, notes
"""

C2 = B1  # full local structural context; same B1 instruction

TIMEOUTS = {
    "b1": 300,
    "b2": 600,
    "b3": 240,
    "b4": 300,
    "b4_p5": 600,
    "c1": 300,
    "c2": 300,
}

PROMPTS = {
    "b1": B1,
    "b2": B2,
    "b3": B3,
    "b4": B4,
    "c1": C1,
    "c2": C2,
}
