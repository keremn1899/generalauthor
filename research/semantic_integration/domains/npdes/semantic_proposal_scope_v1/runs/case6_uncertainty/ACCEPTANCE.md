# Acceptance

## What you mean

You are saying that NODI code **9** has no established missing-evidence meaning that you can affirm, and you do not want anyone to guess its meaning by looking at how code 9 co-occurs with other fields in the measurements data (for example, alongside code C or particular parameter combinations). Your statement is uncertainty plus a prohibition on pattern-based inference—not a claim that 9 means any particular thing.

## Where this applies

This applies to **FY2025 rows with no numeric result** where `NODI_CODE='9'`. In the current data that is **36 cases** out of **186** total no-numeric-result rows (the other **150** carry code C, which you did not address in this utterance).

## What rule would change

**No rule change is needed.** The draft already requires interpretation for NODI codes and treats only the empty code as known. Code 9 therefore stays **UNINTERPRETED** under the `nodi_code_semantics` requirement—it is not assigned "no discharge," "not required," or any other missing-evidence classification, and nothing in the construction infers meaning from distributional patterns in the CSV.

## Measurable consequences from the dry run

The dry run compared the baseline draft against proposed constructions. **No proposals were run** because the baseline already matches your stated intent.

Baseline hole profile (unchanged):

| Metric | Count |
|--------|------:|
| Hole groups | 8 |
| Hole instances | 535 |
| NODI semantics hole (all non-empty codes) | 186 instances |
| — code C | 150 |
| — code 9 | 36 |

The `nodi_code_semantics` hole remains **UNINTERPRETED** for all 186 cases. Your utterance does not reduce that count—it confirms that code 9 should stay in that unresolved bucket rather than be inferred from data patterns.

## What remains unresolved

- **Code 9 itself:** still unknown per your statement; correctly left uninterpreted.
- **Code C (150 cases):** you did not speak to whether C has a known meaning or how it relates to 9. The draft continues to leave C uninterpreted as well.
- **Whether C and 9 are interchangeable:** not addressed; no change implied by this utterance.

These open items do not create competing interpretations of what you said about code 9—they are simply outside the scope of this statement.
