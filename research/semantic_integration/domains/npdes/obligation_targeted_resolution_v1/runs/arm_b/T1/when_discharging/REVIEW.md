# Adjudication Review: `when_discharging`

## What I investigated

I read only `PASS_TASK_ADJUDICATE.md`, `PACKET.json`, and `construction.py`. I did not search `documents/` or `sources/` beyond the frozen snippets already retained in the packet. All retained snippets use admissible workspace paths (`documents/aztec/*.txt`, `sources/permit_limits.csv`).

The obligation asks: **What does the permit-limit comment `WHEN DISCHARGING` do to monitoring/limit applicability?** Purposes B and C are in scope. The relation contract states that the comment conditions monitoring while discharge occurrence in a period is a separate factual question.

## What I found

The packet contains convergent permit-package evidence for three supported candidate interpretations and one refuted interpretation:

1. **Monitoring is discharge-conditioned.** Footnote *1 in `documents/aztec/final_permit.txt` attaches "When discharging." to MEASUREMENT FREQUENCY entries for (*1)-marked parameters (pH, flow, TSS, TRC, cyanide, TDS), not to numeric limit values. The statement of basis repeats the same parameter-specific "when discharging" frequencies.

2. **Numeric limits are not waived by the comment.** Part I.A.1 states that authorized intermittent backwash discharges "shall be limited and monitored as specified below." The comment scopes monitoring frequency, not suspension of effluent limits.

3. **No discharge exempts discharge-conditioned monitoring for that month.** Part I.C.5 requires marking NO DISCHARGE on the DMR when there is no discharge during the sampling month.

4. **Optional-monitoring semantics are refuted by structured data.** The representative `permit_limits.csv` row shows `DMR_COMMENT_TEXT=WHEN DISCHARGING.` with `OPTIONAL_MONITORING_FLAG=N`.

5. **Structured discharge occurrence is not established.** The packet's known limitations state that CSV sources do not record whether discharge occurred in FY2025 periods and that no NODI_CODE values appear for NM0028762 DMR rows.

## Evidence supporting resolution

| Claim | Supporting source |
| --- | --- |
| Comment attaches to monitoring frequency, not limits | `documents/aztec/final_permit.txt` Part I.A footnote *1 |
| Monitoring frequencies apply when discharging | `documents/aztec/final_permit.txt`, `documents/aztec/statement_of_basis.txt` Section 5 |
| No-discharge months use NO DISCHARGE reporting | `documents/aztec/final_permit.txt` Part I.C.5 |
| Not optional-monitoring encoding | `sources/permit_limits.csv` (OPTIONAL_MONITORING_FLAG=N) |
| Intermittent/episodic discharge context | `documents/aztec/final_permit.txt` Part I.A.1; `documents/aztec/statement_of_basis.txt` Sections II and VIII |

This is **SOURCE_ESTABLISHED** evidence, not CSV correlation alone and not model hypothesis.

## What remains uncertain

Even with comment semantics resolved, the packet does **not** establish:

- Whether discharge occurred in any specific FY2025 monitoring period.
- How partial discharge within a month or quarter satisfies weekly/quarterly frequency obligations.
- How no-discharge months were actually reported in structured DMR data (no NODI_CODE observations).

These are factual/compliance questions downstream of comment meaning, consistent with the relation contract.

## Disposition

**SUPPORTED_RESOLUTION** at scope **ONE_RELATION_OR_VOCABULARY**: the permit comment's operative effect on monitoring vs. limit applicability is established from workspace permit documents for the NM0028762 Aztec package (17 structured occurrences).

## Proposal and what would change if admitted

**Admit: ADMIT_DISPOSABLE**

The disposable edit in `dry_run/construction.py` adds a reusable comment-to-condition mapping:

- Normalize `DMR_COMMENT_TEXT` matching `WHEN DISCHARGING` → `monitoring_condition=discharge_occurrence`.
- Register `WHEN DISCHARGING.` as a known interpreted comment value.
- Replace the blanket semantic unresolved on all 17 rows with a narrower factual unresolved (`discharge_occurrence_in_period`) whose reason cites missing structured discharge-occurrence evidence, not unknown comment meaning.

If admitted, Purpose B can treat monitoring requirements as discharge-conditioned by vocabulary rather than leaving comment semantics open. Purpose C can distinguish "monitoring not required because no discharge" from "monitoring required but unobserved," but still cannot resolve period-specific discharge facts from CSV alone. Purpose A numeric comparison behavior is unchanged because limits remain applicable when discharge occurs.

If not admitted, `construction.py` continues to mark all 17 `WHEN DISCHARGING` rows unresolved under `conditional_discharge_dependent_monitoring`, conflating unresolved comment semantics with unresolved discharge-occurrence facts.
