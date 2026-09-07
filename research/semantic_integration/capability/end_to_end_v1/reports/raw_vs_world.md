# RAW vs WORLD

Fresh Composer 2.5 consumers, isolated contexts, no gold. WORLD condition: declared purpose + accepted T1 World + TaskView/SQL. RAW condition: declared purpose + evidence folder. Six hidden questions each. 3×3×2 = 18 runs.

## MEASURED

| condition | CORRECT | INCORRECT | UNRESOLVED_CORRECTLY | UNRESOLVED_INCORRECTLY | UNSUPPORTED_CLOSURE | n |
| --- | --- | --- | --- | --- | --- | --- |
| WORLD | 32 | 3 | 15 | 1 | 3 | 54 |
| RAW | 36 | 0 | 18 | 0 | 0 | 54 |

Establishable slice (Q1–Q4, 36 answers each):

| condition | CORRECT | INCORRECT | UNRESOLVED_INCORRECTLY |
| --- | --- | --- | --- |
| WORLD | 32 | 3 | 1 |
| RAW | 36 | 0 | 0 |

Non-establishable slice (Q5–Q6, 18 answers each):

| condition | UNRESOLVED_CORRECTLY | UNSUPPORTED_CLOSURE |
| --- | --- | --- |
| WORLD | 15 | 3 |
| RAW | 18 | 0 |

### Per domain (do not hide variance)

| domain | WORLD exact (est.) | RAW exact (est.) | WORLD correct unresolved | RAW correct unresolved |
| --- | --- | --- | --- | --- |
| harbor_towing | 9/12 | 12/12 | 3/6 (all Q5; all Q6 closed as `false`) | 6/6 |
| seed_grants | 11/12 | 12/12 | 6/6 | 6/6 |
| makerspace_checkout | 12/12 | 12/12 | 6/6 | 6/6 |

Trial-level WORLD:

| domain | C1 | C2 | C3 |
| --- | --- | --- | --- |
| harbor_towing | Q3 INCORRECT=3; Q6 UNSUPPORTED_CLOSURE=`false` | same | same |
| seed_grants | all target | all target | Q4 UNRESOLVED_INCORRECTLY |
| makerspace_checkout | all target | all target | all target |

Trial-level RAW: all 18 runs hit the target class on every question.

### Reuse (WORLD, one T1 World per domain, no rebuild)

| domain | trial | n_sql_hint | schema/file reads | raw sources read |
| --- | --- | --- | --- | --- |
| harbor_towing | C1 | 5 | 8 | 0 |
| harbor_towing | C2 | 4 | 6 | 0 |
| harbor_towing | C3 | 2 | 6 | 0 |
| seed_grants | C1 | 3 | 6 | 0 |
| seed_grants | C2 | 6 | 6 | 0 |
| seed_grants | C3 | 4 | 5 | 0 |
| makerspace_checkout | C1 | 4 | 7 | 0 |
| makerspace_checkout | C2 | 4 | 9 | 0 |
| makerspace_checkout | C3 | 3 | 7 | 0 |

Held-out questions answered per accepted World without raw-source access or rebuild: **6 / 6** in every WORLD run.

## OBSERVED

Three-way split required by the protocol:

1. **Semantic compilation advantage.** Makerspace WORLD matched RAW exactly. Seed WORLD matched RAW on 17/18 answers. Cross-source rates, remaining balances, ASST→ESCORT, overtime, L1→LASER-A, after-hours multiplier were answered from compiled state, not by re-reading CSV/prose.
2. **Semantic undercoverage.** Not the primary harbor Q3 story: T1 still stores blank `billed_hours` on J6. RAW’s advantage is that the CSV grain is the only grain. WORLD offers a second PURPOSE table that omits J5/J7 for a different reason.
3. **Consumer-interface / reasoning.** Harbor Q3 consumers found both `tow_job.billed_hours` and `billable_hours` and counted PURPOSE absence (3) instead of WORLD blanks (1). Harbor Q6 treated `insufficient_evidence` as `false`. Seed C3 treated waiver-unknown as blocking the 20% match amount that C1/C2 computed from the same World. None of these are “the consumer could not find a table.”

RAW is strictly more exact on this pack. WORLD is competitive in two of three domains and tied in one.

## HYPOTHESIS

H4 (compile once, compute many) is supported. WORLD is not yet a strict accuracy winner versus a fresh agent on the same small corpus. The residual WORLD misses are fail-open denial and grain selection, not missing sqlite.
