# Acceptance summary

## What you mean

For this analysis, you are certifying a document-authority policy for a specific pair of permit documents: if the **final permit** and **fact sheet** disagree, the **final permit** governs. You are not asserting that narrative permit text is now available, and you are not claiming a universal hierarchy among every document kind in the permit package.

## Where it applies

This policy applies to purposes **B** and **C** (narrative conditions and source authority) for the three permits in the current inventory. Only one permit package (NM0000116) actually contains both a final permit and a fact sheet; the other two permits have final permits but no fact sheet in the inventory.

The policy is scoped to **this analysis** — it is a certified analytical choice, not a claim that the outside world inherently ranks these documents this way.

## What rule changes

Compared with the baseline draft, the construction would add one certified conflict rule:

- **On disagreement between final permit and fact sheet → use the final permit.**

The baseline left all narrative document authority unresolved under a single “permit document text not available” item. The proposed construction keeps that item (because structured sources still carry only filenames and hashes, not narrative body text) and additionally records the certified pair rule above. It also explicitly flags that authority among **other** inventoried document kinds — statement of basis, reasonable potential, minor modification, part II appendix, part IV — remains unsettled for this analysis.

## Measurable consequences from the dry run

Both baseline and proposal run successfully. Counts that matter:

| Measure | Baseline | Proposed |
|---|---:|---:|
| Hole groups | 8 | 9 |
| Hole instances | 535 | 536 |
| Permit documents inventoried | 12 | 12 |
| All other relation row counts | unchanged | unchanged |

What changed:

- **+1 new certified policy row** encoding final-permit-over-fact-sheet on disagreement.
- **+1 new explicit unresolved item** (`document_authority_among_other_kinds`) for the five other document kinds present in the inventory.
- **No change** to the existing unresolved item for unavailable narrative text (still 1 instance covering all 12 documents).
- **No change** to monitoring requirements, limit comparisons, numeric candidates, pass/fail semantics, or any of the other 7 baseline hole groups (same counts: 40 aggregated-reporting, 17 conditional-discharge, 105 sample-type, 105 frequency, 186 nodi-code, 12 pass/fail, 69 permit-limit comments).

In practical terms: accepting this proposal records your authority preference for the final-permit/fact-sheet pair and makes the remaining gaps more explicit, but it does **not** resolve any narrative permit conditions today because the structured sources still cannot detect disagreement.

## What remains unresolved

Even after acceptance, these items stay open:

1. **Narrative text is unavailable** — all 12 inventoried documents are known by kind and hash only; no structured source can yet evaluate whether final permit and fact sheet actually disagree.
2. **Authority among other document kinds** — you did not specify how statement of basis, reasonable potential, minor modification, or appendix documents relate to the final permit when text is present.
3. **What counts as disagreement** — the certified rule applies on disagreement, but disagreement detection awaits narrative text extraction or human review.
4. **All pre-existing semantic gaps** — monitoring frequency codes, sample type codes, nodi semantics, pass/fail reporting, aggregated reporting requirements, conditional discharge monitoring, and permit limit comment interpretation are unchanged and still unresolved at the same counts as before.
