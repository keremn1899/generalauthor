# Selected obligations

## MEASURED

Prefer the eight fixture evidence-shapes listed in the probe brief. Split NODI by code (C vs 9). Include empty LIMIT_VALUE_NMBR even though T5 emitted no named hole. Replace nothing as unresolved leftovers: all preferred fixtures are present except a dedicated report-only named hole, which is covered by empty_numeric_limit. Add monitoring_frequency as the extra purpose-reachable codebook obligation. Do not select only easy/establishable cases.

| id | question | n | purpose | why included |
| --- | --- | --- | --- | --- |
| nodi_c | What does NODI code C mean for a FY2025 DMR row with no numeric result? | 150 | ['C'] | Preferred fixture: NODI C; codebook-shaped evidence problem; 150 occurrences |
| nodi_9 | What does NODI code 9 mean for a FY2025 DMR row with no numeric result? | 36 | ['C'] | Preferred fixture: NODI 9; sibling of C; 36 occurrences; leakage control |
| when_discharging | What does the permit-limit comment 'WHEN DISCHARGING' do to monitoring/limit applicability? | 17 | ['B', 'C'] | Preferred fixture: discharge-conditioned applicability; permit-clause evidence |
| geometric_mean | What does a geometric-mean reporting comment require for comparison of individual monitoring-period values? | 40 | ['A', 'B', 'C'] | Preferred fixture: aggregation semantics; Farmington permit footnotes exist in corpus |
| pass_fail | What does PASS=0 / FAIL=1 reporting mean, and is it a numeric concentration comparison? | 12 | ['A', 'B', 'C'] | Preferred fixture: binary coding; sibling leakage control vs WHEN DISCHARGING / geometric mean |
| empty_numeric_limit | When LIMIT_VALUE_NMBR is empty, is the row a numeric limit, report-only monitoring, or something else? | 57 | ['A'] | Preferred fixture #6: empty numeric / report-only; present in structured sources though T5 did not emit a hole |
| document_authority | Without ranking from filenames, what do inventoried permit documents establish, and which document governs if they disagree? | 1 | ['B', 'C'] | Preferred fixture: document authority; text is in the frozen corpus, legal hierarchy may not be |
| monitoring_frequency | What monitoring frequencies do opaque LIMIT_FREQ_OF_ANALYSIS_CODE values (e.g. 05/WK, 01/07, 01/01) establish? | 105 | ['B'] | Additional purpose-reachable codebook-shaped obligation (empty-numeric is included separately; sample-type is a sibling leftover) |

## OBSERVED

Selection frozen before host resolution. Varied evidence shapes, not only establishable cases.

## HYPOTHESIS

A small reusable obligation set can cover hundreds of T5 hole instances without sending raw rows to the resolver.
