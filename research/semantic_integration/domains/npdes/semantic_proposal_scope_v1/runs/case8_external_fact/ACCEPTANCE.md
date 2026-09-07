# Acceptance summary

## What I think you mean

When narrative permit conditions in the **final permit** and the **fact sheet** disagree, the **final permit legally wins**. You are stating how NPDES permit-package documents relate in law—not asking us to treat a missing fact sheet as denied, and not claiming we already have the full text of either document in structured form.

## Where this applies

This is treated as a **general legal fact about permit packages**, not as a rule tied only to one analytical purpose. It would still mean the same thing even if we were asking a different compliance question tomorrow.

Document authority only matters in parts of the draft that read narrative permit conditions. The precedence rule is therefore relevant wherever those analyses run, but it does **not** by itself resolve any numeric limit comparison, monitoring schedule code, or pass/fail semantics.

## What rule would change

The construction would record that **final_permit takes precedence over fact_sheet** when their narrative conditions conflict.

The former broad “document authority” uncertainty would be **split**:

- **Still unresolved:** we lack narrative body text for inventoried permit documents (`permit_document_text_not_available`, 1 document).
- **Newly scoped unresolved item:** precedence among **other** inventoried document kinds—statement of basis, reasonable potential determination, minor modification, appendices, and similar—when they might conflict with each other or with the final permit (`permit_document_authority_other_kinds`, 1 document).

## Measurable consequences from the dry run

Compared with the baseline draft on this dataset:

| Measure | Baseline | With your rule |
| --- | ---: | ---: |
| Hole groups | 8 | 9 (+1) |
| Hole instances | 535 | 536 (+1) |
| `document_kind_precedence` rows | 0 | 1 (new) |

**Unchanged** (same counts as baseline):

- 824 FY2025 measurements and measurement–limit pairs
- 342 numeric comparison candidates; 186 no-numeric-result cases
- 105 monitoring requirements
- Existing unresolved groups: aggregated reporting (40), conditional discharge monitoring (17), sample type codes (105), frequency codes (105), NODI semantics (186), pass/fail reporting (12), permit limit comment text (69)

The dry run also checked an alternative reading—that your statement is only an **analysis policy for purposes B and C**—and it produced **the same hole counts and relation counts** on this data. That is why no further clarification is needed to proceed.

## What remains unresolved

Your statement does **not** settle:

1. **Other document kinds.** We still do not know how statement of basis, reasonable potential, minor modification, appendices, etc. rank relative to the final permit or to each other.
2. **Missing text.** Structured sources still do not carry narrative permit/fact-sheet body text, so no actual conflicting conditions can be read or compared yet.
3. **Non-conflicting use of the fact sheet.** You did not say whether fact-sheet text may still inform analysis when it does not conflict with the final permit.
4. **Everything else already open in the draft**—monitoring frequency and sample-type codes, NODI handling, pass/fail semantics, aggregated and conditional monitoring requirements, and permit limit comments—stays open exactly as before.

Accepting this rule adds one precise legal precedence fact and one narrower authority gap; it does not close any of the larger compliance holes above.
