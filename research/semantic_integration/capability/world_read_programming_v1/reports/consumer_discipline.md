# Consumer discipline (Part A)

**Arms:** A0 = current WORLD read. A1 = same plus the frozen compact World contract (1176 bytes, domain-neutral).  
**Replication:** 3 fresh Composer 2.5 consumers × 2 arms. Each consumer answered all 12 diagnostic questions across the three frozen T1 Worlds.  
**Worlds:** unmodified T1 hashes; verified after each run.

## MEASURED

| arm | CORRECT | INCORRECT | UNRESOLVED_CORRECTLY | UNRESOLVED_INCORRECTLY | UNSUPPORTED_CLOSURE | n |
| --- | --- | --- | --- | --- | --- | --- |
| A0 | 16 | 3 | 12 | 2 | 3 | 36 |
| A1 | 18 | 1 | 12 | 2 | 3 | 36 |

Establishable (21 cells/arm): A0 **16/21**, A1 **18/21**.  
Non-establishable (15 cells/arm): both **12/15** UNRESOLVED_CORRECTLY. All three misses per arm are harbor Q6.

### Preregistered failure families (3 questions × 3 consumers)

| family | cell | A0 target | A1 target |
| --- | --- | --- | --- |
| WRONG_GRAIN | harbor_towing.Q3 (gold 1) | 0/3 (all answered 3) | **2/3** (C1, C2 = 1; C3 = 3) |
| UNRESOLVED_AS_FALSE | harbor_towing.Q6 | 0/3 (all `false`) | 0/3 (all `false`) |
| PROPOSITION_CONTAMINATION | seed_grants.Q4 (gold 10000) | 1/3 (C1 only) | 1/3 (C2 only) |

### Controls (9 questions × 3 = 27 cells/arm)

All 27 A0 and all 27 A1 control cells hit the target class. No control regression.

Trial-level:

| trial | harbor Q3 | harbor Q6 | seed Q4 | controls |
| --- | --- | --- | --- | --- |
| A0 C1 | 3 INCORRECT | false | 10000 CORRECT | all target |
| A0 C2 | 3 INCORRECT | false | UNRESOLVED | all target |
| A0 C3 | 3 INCORRECT | false | UNRESOLVED | all target |
| A1 C1 | **1 CORRECT** | false | UNRESOLVED | all target |
| A1 C2 | **1 CORRECT** | false | **10000 CORRECT** | all target |
| A1 C3 | 3 INCORRECT | false | UNRESOLVED | all target |

## OBSERVED

A1 C1 rationale for Q3 explicitly used WORLD `tow_job.billed_hours` (only J6 blank) rather than PURPOSE `billable_hours` row absence. That is rule 3 of the contract working.

A1 still answered Q6 `false` while citing `insufficient_evidence` and “no emergency log.” Rule 1 (“unresolved is not false”) did not hold for a yes/no question. The World never asserted “not an emergency.”

Seed Q4 contamination is unchanged in rate: consumers who see `seed_core_waiver_unknown` on `award_match_obligation` still often refuse the established `match_rate` 0.20.

## HYPOTHESIS

The compact contract **materially reduces WORLD/PURPOSE grain errors** and does **not** harm controls. It does **not** eliminate unresolved→false on polar questions and does **not** reliably block proposition contamination. Part A’s success bar (`A1 has 0 unsupported closures`) is **not** met.
