# Construction results

**Experiment:** End-to-End Semantic Compilation Capability Probe v1  
**Runtime freeze:** Spike 1 `runtime_v0` (`SPIKE1_RUNTIME_LOOP_SUPPORTED`); hashes in `evaluator_only/runtime_freeze.json` still match on-disk files.  
**Model:** Composer 2.5 (all six `system/init.model` reports).  
**World selection for consumers (frozen before scoring):** lowest accepted trial index → **T1** in every domain.

## MEASURED

Accepted Worlds: **6 / 6**

Every trial produced a valid accepted World on **attempt 1** of at most 3. No evaluator gold, no hidden questions, no human semantic correction.

| domain | trial | build | attempts | relations | assertions | SOURCE groundings | derived | purpose reqs | purpose failures | host source reads |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| harbor_towing | T1 | ACCEPTED | 1 | 9 | 40 | 25 | 0 | 8 | 6 | jobs, rate_card, vessels, service_conditions, berth_notice |
| harbor_towing | T2 | ACCEPTED | 1 | 7 | 31 | 14 | 0 | 5 | 5 | same five sources |
| seed_grants | T1 | ACCEPTED | 1 | 9 | 38 | 30 | 0 | 9 | 8 | awards, disbursements, orgs, program_rules, status_fragment |
| seed_grants | T2 | ACCEPTED | 1 | 9 | 38 | 38 | 0 | 10 | 8 | same five sources |
| makerspace_checkout | T1 | ACCEPTED | 1 | 7 | 29 | 27 | 0 | 5 | 1 | checkouts, tools, members, shop_rules, adr |
| makerspace_checkout | T2 | ACCEPTED | 1 | 11 | 44 | 16 | 0 | 5 | 5 | same five sources |

Auto-scorer coverage (substring of allowed values / failure kinds in a World dump):

| domain | trial | coverage | construction.py hidden-question strings | unsupported_closure_hits |
| --- | --- | --- | --- | --- |
| harbor_towing | T1 | Q1–Q4 PRESENT; Q5–Q6 EXPLICITLY_UNRESOLVED | [] | [] |
| harbor_towing | T2 | Q1–Q4 PRESENT; Q5–Q6 EXPLICITLY_UNRESOLVED | [] | [] |
| seed_grants | T1 | Q1–Q4 PRESENT; Q5–Q6 EXPLICITLY_UNRESOLVED | [] | [] |
| seed_grants | T2 | Q1–Q4 PRESENT; Q5–Q6 EXPLICITLY_UNRESOLVED | [] | [] |
| makerspace_checkout | T1 | Q1–Q4 PRESENT; Q5–Q6 EXPLICITLY_UNRESOLVED | [] | [] |
| makerspace_checkout | T2 | Q1–Q4 PRESENT; Q5–Q6 EXPLICITLY_UNRESOLVED | [] | [] |

Establishable PRESENT (auto-scorer): **24/24**  
Non-establishable EXPLICITLY_UNRESOLVED (auto-scorer): **12/12**  
Unsupported-closure marker hits in `construction.py`: **0**

## OBSERVED

- Isolation preflight `ok` on every construction workspace. Host traces report `isolation_leaks: []`.
- Relation **names** differ across the two trials of each domain. Behavior of the auto-scorer coverage tags did not.
- Harbor T1 preserves blank `tow_job.billed_hours` on J6 only, and separately records B12 after-hours jobs J5/J7 as `billing_outcome = insufficient_evidence`. Those are different grains. The auto-scorer cannot see that; see `semantic_coverage.md`.
- Seed T1 stores `award_match_obligation.match_rate = 0.20` for A-101 **and** attaches `seed_core_waiver_unknown` to the same relation. Match amount and waiver status are coupled in the PURPOSE-failure overlay.
- Derived assertion count is 0 in every accepted World. Integration was authored as BASE, not as kernel derivations.

## HYPOTHESIS

H1 (end-to-end construction) is supported on this pack: a Composer 2.5 host with frozen `runtime_v0` can take an untouched folder plus a natural-language purpose and emit an accepted grounded World without evaluator feedback.
