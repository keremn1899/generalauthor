"""Constructor v2 pass prompts. P0–P4/P6/P7 match localization; P5 consumes R1–R3."""

from __future__ import annotations

from research.semantic_integration.domains.diligence.pass_localization.prompts import (
    COMMON,
    P0,
    P1,
    P2,
    P3,
    P4,
    P6,
    P7,
)

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
    "p8": 0,
}

P1_V2 = P1 + """
Also read contracts/*.json. Every SEMANTIC relation in 01_vocabulary.json must include the RelationContract fields: roles, role_types, meaning, dispositions, scope, algebra, epistemic_contract, grounding_contract. semantic_family_hint is optional metadata with no behavioral effect.
"""

P5_V2 = COMMON + """
# Pass P5 — Bounded semantic adjudicator (Constructor v2)

For each obligation in 03_obligations.json, read only that obligation and 04_packets/<obligation_id>.json. Also read contracts/identity_judgment.json when the obligation is an identity judgment.

You receive one relation contract, one candidate proposition, and one bounded evidence packet. Do not invent candidates, relations, or purposes. Do not canonicalize referents. Do not search files outside 04_packets/.

For identity-like propositions (SAME_ENTITY / DISTINCT / UNRESOLVED):
- SAME_ENTITY requires evidence that establishes identity. Name similarity, compatibility, address similarity, or lack of contradiction is insufficient.
- DISTINCT requires evidence that establishes distinctness. Absence of identity evidence is insufficient.
- If neither burden is met, UNRESOLVED is the correct successful output.
- If the packet preserves multiple live candidates or says identity cannot be established, do not close SAME/DISTINCT.

Clause-presence and other non-identity obligations may use ACCEPT / REJECT / UNRESOLVED as before.

Write 05_dispositions.json as a JSON list of:
{
  "obligation_id": "...",
  "relation": "...",
  "values": {},
  "disposition": "SAME_ENTITY" | "DISTINCT" | "UNRESOLVED" | "ACCEPT" | "REJECT",
  "supporting_evidence": [{"source_path": "...", "location": "..."}],
  "support_claim": "one sentence: what the cited evidence establishes",
  "grounding": [],
  "rationale": "..."
}

Judge every obligation. Prefer unsupported uncertainty to unsupported semantic closure.
"""

PROMPTS = {
    "p0": P0,
    "p1": P1_V2,
    "p2": P2,
    "p3": P3,
    "p4": P4,
    "p5": P5_V2,
    "p6": P6,
    "p7": P7,
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
