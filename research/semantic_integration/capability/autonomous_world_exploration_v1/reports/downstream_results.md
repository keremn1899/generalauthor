# Downstream results

Same six hidden tasks per domain. E0 sees tasks immediately. E1 orients first, then sees the same tasks. No relation names in the prompts.

## MEASURED

| arm | CORRECT | INCORRECT | UNRESOLVED_CORRECTLY | UNRESOLVED_INCORRECTLY | UNSUPPORTED_CLOSURE | n |
| --- | --- | --- | --- | --- | --- | --- |
| E0 | 39 | 3 | 7 | 3 | 2 | 54 |
| E1 | 40 | 4 | 6 | 1 | 3 | 54 |

Establishable (45 cells/arm): E0 **39/45**, E1 **40/45**.  
Unresolved T5 (9 cells/arm): E0 **7/9**, E1 **6/9**.

| family | E0 | E1 |
| --- | --- | --- |
| GRAIN (harbor T4 gold 1; all answered 3) | 0/3 | 0/3 |
| UNRESOLVED_AS_FALSE (harbor T5) | 1/3 correct unresolved | 0/3 |
| match overlay / amount (seed T4 gold 10000) | 0/3 (all UNRESOLVED) | 1/3 CORRECT, 1 UNRESOLVED, 1 INCORRECT (3000 = 20% of remaining) |
| makerspace all six tasks | 18/18 | 18/18 |

Multi-hop T3: **18/18** correct (both arms). Novel T6: **18/18**. Factual T1/T2: **18/18** except none missed.

E0 ≈ E1 on aggregate (46/54 target-class cells each if CORRECT+UNRESOLVED_CORRECTLY). E1 did not improve the preregistered harbor grain or false-closure cells. E0 was slightly better on harbor T5.

## OBSERVED

Harbor E1 notes already separated J6 blank WORLD `billed_hours` from J5/J7 PURPOSE insufficient billing, then T4 still counted missing PURPOSE `billable_hours` rows (3). Orientation did not bind the later question to the WORLD grain.

Seed T4: E0 treated waiver-unknown as blocking the match amount. E1 R3 computed 10000 from `match_rate` × award amount; E1 R1 applied 20% to remaining 15000.

Makerspace needed no orientation phase.

## HYPOTHESIS

Explicit orientation does not materially improve downstream correctness on this pack. On-demand E0 is enough for factual, multi-hop, and novel analyses. Residual errors are the same consumer-reasoning families as the sealed read-discipline probe, not missed relations.
