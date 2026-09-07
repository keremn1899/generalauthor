# Failure analysis

Primary bucket per failed hidden-question instance. Domain-specific families are not used.

## MEASURED

Failed WORLD answers (7 unique question×consumer cells; RAW had 0):

| domain | consumer | Q | score class | primary bucket | why this bucket |
| --- | --- | --- | --- | --- | --- |
| harbor_towing | C1, C2, C3 | Q3 | INCORRECT (value 3; gold 1) | CONSUMER_REASONING_FAILURE | Needed state is in `tow_job.billed_hours` (blank on J6 only). Consumers counted missing PURPOSE `billable_hours` rows (J5, J6, J7). They cited both grains and chose the wrong one. Not ABI-name instability; not absent semantics. |
| harbor_towing | C1, C2, C3 | Q6 | UNSUPPORTED_CLOSURE (`false`) | CONSUMER_REASONING_FAILURE | World records `insufficient_evidence` / `EXPLICIT_UNRESOLVED` for B12 after-hours emergency documentation. Consumers closed absence as a negative fact. Not durable World closure. |
| seed_grants | C3 | Q4 | UNRESOLVED_INCORRECTLY | CONSUMER_REASONING_FAILURE | Same T1 World from which C1/C2 computed 10000. C3 over-applied `seed_core_waiver_unknown` (the Q6 overlay on `award_match_obligation`) to the match **amount**. Semantics present; interface found. |

Construction-side (no consumer):

| item | bucket | note |
| --- | --- | --- |
| 6/6 accepted Worlds | — | No `RUNTIME_FAILURE`. |
| `construction.py` vs hidden questions | — | No hardcoded question strings. |
| Fuel surcharge / emergency authorized / status-S meaning / waiver granted / PENDING meaning / insurance rider | CORRECT_EVIDENCE_INSUFFICIENCY | Worlds left these unresolved. Target. |
| Harbor PURPOSE `billable_hours` omitting J5/J7 | COLLAPSED grain (not a failure-taxonomy family) | Chargeability mixed with billed-hours quantity. Contributes to Q3 consumer miss; World still has the quantity column. |
| Seed waiver failure attached to `award_match_obligation` | COLLAPSED overlay | Invites C3’s Q4 miss; C1/C2 still computed the amount. |

Unused buckets on this pack: `RUNTIME_FAILURE`, `SOURCE_DISCOVERY_FAILURE`, `REPRESENTATION_MISSING`, `GROUNDING_FAILURE`, `SEMANTIC_UNDERCOVERAGE` (as primary), `CONSUMER_INTERFACE_FAILURE` (as primary).

## OBSERVED

- Failures are **not** dominated by constructor-authored vocabulary. Harbor T1 vs T2 names differ widely; consumers only saw T1 and found `effective_rate`, `job_charge`, `award_match_obligation`, `checkout_fee`.
- The safety miss is **consumer** fail-open: answering `false` for an undocumented emergency. The World stayed unresolved.
- The accuracy miss that RAW wins cleanly is harbor cardinality Q3, where two honest grains coexist.

## HYPOTHESIS

If a follow-up changes anything, it should be consumer discipline around PURPOSE vs WORLD grains and “unresolved is not false,” not a generic ABI layer. ABI remains motivated by T1/T2 name divergence, but this probe did not observe consumers failing to *find* needed relations.
