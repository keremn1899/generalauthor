"""Frozen v1.1 prompts. Do not tune between conditions."""

from __future__ import annotations

from research.semantic_integration.domains.npdes.prose_probe_v1.prompts import B2 as FROZEN_P5_OVERLAY

COMMON = """You are an isolated experimental probe, not a World constructor.

Do not write World facts. Do not invent closed-world negation. Do not look for hidden expected outputs. They are not here. Do not read files outside this workspace.
"""

B4_LITE = COMMON + """
# Condition B4-lite — nominated clause to bounded semantic obligation

Read purposes/visible_a.md, purposes/visible_b.md, purposes/visible_c.md, and PASSAGE.md.

PASSAGE.md contains one automatically nominated source passage plus the same kind of local structural context used for oracle-passage obligation formulation.

Determine whether interpretation of this passage could change the result of one or more declared purposes.

If not, return NO_RELEVANT_OBLIGATION.

If yes, formulate the smallest bounded semantic obligation whose resolution would capture the computation-changing distinction.

Do not answer the obligation.
Do not create World facts.

Allowed output:

NO_RELEVANT_OBLIGATION

or

OBLIGATION
affected_purpose:
question_or_proposition:
required_context:
source_locator:

Write exactly one JSON object to result.json with keys:
- kind: "NO_RELEVANT_OBLIGATION" or "OBLIGATION"
- affected_purpose: "A" | "B" | "C" | "A,B" | "A,C" | "B,C" | "A,B,C" | null
- question_or_proposition: string or null
- required_context: string or list of strings or null
- source_locator: string or null
- notes: string

Do not include gold identifiers. Do not include positive/negative labels. Do not determine whether the proposition is true.
"""

C1 = COMMON + """
# Context ablation C1 — target span only

Read purposes/visible_a.md, purposes/visible_b.md, purposes/visible_c.md, and PASSAGE.md.

PASSAGE.md contains only the exact target sentence/span, without heading, adjacent prose, table, or footnote context beyond that span.

Determine whether interpretation of this passage could change the result of one or more declared purposes.

If not, return NO_RELEVANT_OBLIGATION.

If yes, formulate the smallest bounded semantic obligation whose resolution would capture the computation-changing distinction.

Do not answer the obligation.
Do not create World facts.

Write result.json with keys:
- kind: "NO_RELEVANT_OBLIGATION" or "OBLIGATION"
- affected_purpose, question_or_proposition, required_context, source_locator, notes
"""

P5 = FROZEN_P5_OVERLAY

TIMEOUTS = {
    "b4_lite": 300,
    "p5": 600,
    "c1": 300,
}

PROMPTS = {
    "b4_lite": B4_LITE,
    "p5": P5,
    "c1": C1,
}
