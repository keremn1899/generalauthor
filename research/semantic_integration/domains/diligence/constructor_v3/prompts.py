"""Constructor v3 pass prompts. P3 unchanged. P5 is the Probe A A1 single adjudicator."""

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

P1_V3 = P1 + """
Also read contracts/*.json and contracts/consumer_interface.json.

Every role that supplies a consumer field must set semantic_identity to that field id. Surface role names may differ from consumer field ids. Example: a role named "counterparty" that holds the contract party string must set semantic_identity to "counterparty_text". The runtime will not guess that mapping.

Join keys for factored relations use semantic_identity invoice, contract, account, or entity.

Include RelationContract fields on SEMANTIC relations: roles, role_types, meaning, dispositions, scope, algebra, epistemic_contract, grounding_contract. semantic_family_hint is optional metadata with no behavioral effect.
"""

P5_V3 = COMMON + """
# Pass P5 — Bounded single semantic adjudicator (Constructor v3)

For each obligation in 03_obligations.json, read only that obligation and 04_packets/<obligation_id>.json. Also read contracts/identity_judgment.json when the obligation is an identity judgment.

Input: one candidate proposition, one relation contract, one bounded evidence packet.
Output: disposition, exact grounding, and a one-sentence support_claim.

Do not invent candidates, relations, or purposes. Do not canonicalize referents. Do not search files outside 04_packets/. Do not run a second critic, proof obligation, pairwise proof, or cue checklist.

For identity (SAME_ENTITY / DISTINCT / UNRESOLVED):
- SAME_ENTITY requires establishing evidence of identity. Name similarity, compatibility, address similarity, or lack of contradiction is insufficient.
- DISTINCT requires establishing contrary evidence of distinctness. Absence of identity evidence is insufficient.
- If neither burden is met, UNRESOLVED is the correct successful output.
- Never convert uncertainty into negative closure.

Clause-presence and other non-identity obligations may use ACCEPT / REJECT / UNRESOLVED.

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
    "p1": P1_V3,
    "p2": P2,
    "p3": P3,
    "p4": P4,
    "p5": P5_V3,
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
