# Semantic coverage

Behavioral scoring of accepted Worlds against hidden competency questions. Relation names are not scored. Auto-scorer tags in `runs/score.json` are substring heuristics; the evaluator notes below override them where the dump heuristic is too coarse.

WORLD consumers used **T1** only (frozen selection rule).

## MEASURED

### harbor_towing T1 (WORLD consumer World)

| Q | auto-scorer | behavioral | note |
| --- | --- | --- | --- |
| Q1 | PRESENT | PRESENT | `effective_rate` / `job_charge` establish J1 at 240 (TOW). |
| Q2 | PRESENT | PRESENT | ASST billed as ESCORT 180; not the ASST rate-card row. |
| Q3 | PRESENT | PRESENT at WORLD grain; COLLAPSED at PURPOSE grain | `tow_job.billed_hours` is blank **only** on J6. PURPOSE `billable_hours` has four rows (J1–J4); J5 and J7 are omitted because berth restriction, not because billed_hours is blank. Gold Q3 is the WORLD column (count = 1). |
| Q4 | PRESENT | PRESENT | J2 charge 2280 (8×240 + 1×360). |
| Q5 | EXPLICITLY_UNRESOLVED | EXPLICITLY_UNRESOLVED | No fuel-surcharge tuple. |
| Q6 | EXPLICITLY_UNRESOLVED | EXPLICITLY_UNRESOLVED | J7 `billing_outcome = insufficient_evidence`; purpose failure `berth_b12_after_hours`. The World does **not** assert “J7 was not an emergency.” |

relations=9 assertions=40 source_groundings=25 failures=6

### harbor_towing T2

Same auto-scorer tags. Different vocabulary (`job`, `job_billable_hours`, `service_rate`, …). Not used by WORLD consumers.

relations=7 assertions=31 source_groundings=14 failures=5

### seed_grants T1 (WORLD consumer World)

| Q | auto-scorer | behavioral | note |
| --- | --- | --- | --- |
| Q1 | PRESENT | PRESENT | A-101 remaining 15000. |
| Q2 | PRESENT | PRESENT | SEED-FAST match 0. |
| Q3 | PRESENT | PRESENT | Status A established for two awards; S/H uninterpreted. |
| Q4 | PRESENT | PRESENT | `match_rate` 0.20 on A-101 (50000 → 10000). Waiver-unknown failures sit on the same relation and can be over-read as blocking the amount. |
| Q5 | EXPLICITLY_UNRESOLVED | EXPLICITLY_UNRESOLVED | Status S not in legend. |
| Q6 | EXPLICITLY_UNRESOLVED | EXPLICITLY_UNRESOLVED | Waiver letters absent. |

relations=9 assertions=38 source_groundings=30 failures=8

### seed_grants T2

Same auto-scorer tags. Names differ (`remaining_balance`, `program_cash_match`, `status_legend`, …).

relations=9 assertions=38 source_groundings=38 failures=8

### makerspace_checkout T1 (WORLD consumer World)

| Q | auto-scorer | behavioral | note |
| --- | --- | --- | --- |
| Q1 | PRESENT | PRESENT | C6 L1→LASER-A fee 12. |
| Q2 | PRESENT | PRESENT | C7 after-hours 18. |
| Q3 | PRESENT | PRESENT | One unauthorized checkout (missing cert). |
| Q4 | PRESENT | PRESENT | C1 daytime 24. |
| Q5 | EXPLICITLY_UNRESOLVED | EXPLICITLY_UNRESOLVED | PENDING undefined. |
| Q6 | EXPLICITLY_UNRESOLVED | EXPLICITLY_UNRESOLVED | No insurance rider in corpus. |

relations=7 assertions=29 source_groundings=27 failures=1

### makerspace_checkout T2

Same auto-scorer tags. Larger ontology (11 relations). Not used by WORLD consumers.

relations=11 assertions=44 source_groundings=16 failures=5

## OBSERVED

- Establishable hidden computations are **source-independent** in the accepted sqlite: WORLD consumers were given no raw files and still recovered Q1/Q2/Q4 in every domain, plus Q3 in seed and makerspace.
- Harbor Q3 is the only establishable distinction that is easy to mis-query: WORLD column vs PURPOSE table. That is not absence of the blank-hours fact.
- No World admitted the unsupported-closure markers (fuel surcharge amount, J7 emergency authorized, status S means …, waiver granted, PENDING means …, insurance rider covers).

## HYPOTHESIS

H2 (semantic sufficiency) holds for the large majority of establishable questions. The remaining miss pattern is grain (harbor Q3) and overlay coupling (seed waiver vs match amount), not empty Worlds.
