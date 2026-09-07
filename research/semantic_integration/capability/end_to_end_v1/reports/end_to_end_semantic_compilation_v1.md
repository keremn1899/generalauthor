# End-to-end semantic compilation v1

**Judgment:** `END_TO_END_SEMANTIC_COMPILATION_SUPPORTED`

**Runtime:** frozen Spike 1 `runtime_v0` (`SPIKE1_RUNTIME_LOOP_SUPPORTED`). Files unchanged vs `evaluator_only/runtime_freeze.json`.  
**Model:** Composer 2.5 on all 6 construction runs and all 18 consumer runs.  
**Domains (frozen before any host run):** `harbor_towing`, `seed_grants`, `makerspace_checkout`. Not BOM, diligence, or NPDES.  
**WORLD World per domain:** first accepted trial (**T1**). Not cherry-picked after gold.

This report seals the probe. Do not modify `runtime_v0`, implement ABI, repair Worlds, add conversation, or start a larger benchmark from this result.

Labels used below: **MEASURED** (counts), **OBSERVED** (what the artifacts show), **HYPOTHESIS** (interpretation).

---

## Headline

| Domain | Build success | World semantic coverage | Unsupported durable closure | WORLD exact (est.) | RAW exact (est.) | WORLD correct unresolved | Interface failures (primary) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| harbor_towing | 2/2 ACCEPTED | Q1 Q2 Q4 PRESENT; Q3 PRESENT at WORLD grain; Q5 Q6 unresolved | 0 | 9/12 | 12/12 | 3/6 | 0 |
| seed_grants | 2/2 ACCEPTED | Q1–Q4 PRESENT; Q5 Q6 unresolved | 0 | 11/12 | 12/12 | 6/6 | 0 |
| makerspace_checkout | 2/2 ACCEPTED | Q1–Q4 PRESENT; Q5 Q6 unresolved | 0 | 12/12 | 12/12 | 6/6 | 0 |

**Construction:** 6/6 accepted Worlds; 24/24 establishable auto-coverage PRESENT; 12/12 non-establishable EXPLICITLY_UNRESOLVED; 0 unsupported-closure marker hits in `construction.py`.

**WORLD consumers (54):** 32 CORRECT, 3 INCORRECT, 15 UNRESOLVED_CORRECTLY, 1 UNRESOLVED_INCORRECTLY, 3 UNSUPPORTED_CLOSURE.

**RAW consumers (54):** 36 CORRECT, 18 UNRESOLVED_CORRECTLY.

**Reuse:** 9/9 WORLD runs answered all six questions from the same T1 sqlite, no rebuild, no raw files.

---

## Strong-success checklist

| # | Criterion | Result |
| --- | --- | --- |
| 1 | ≥5/6 construction trials accepted | MEASURED 6/6 |
| 2 | No unsupported durable closure | OBSERVED: no World tuple asserts fuel surcharge, emergency-authorized, status-S meaning, waiver granted, PENDING meaning, or insurance coverage. Consumer `false` on harbor Q6 is not a World assertion. |
| 3 | Large majority of establishable questions computable from World | MEASURED WORLD 32/36 CORRECT; the three harbor Q3 misses are still *queryable* as blank `tow_job.billed_hours`. |
| 4 | Non-establishable usually left correctly unresolved | MEASURED WORLD 15/18 |
| 5 | Fresh WORLD consumers compute repeatedly on one World | MEASURED 6 questions × 9 runs, no sources |
| 6 | WORLD competitive with RAW in most domains | OBSERVED makerspace tied; seed 17/18 vs 18/18; harbor RAW better. 2/3 domains competitive. |
| 7 | Failures not dominated by ABI / missing interface | OBSERVED primary bucket is CONSUMER_REASONING_FAILURE. T1/T2 names differ; consumers still found the T1 relations. |

RAW is strictly more exact on this pack. That does not by itself choose `RAW_REASONING_REMAINS_SUPERIOR`: WORLD is not consistently worse when needed semantics are present. It also does not choose `CONSUMER_ABI_IS_NEXT_BOTTLENECK`: consumers were not lost in vocabulary. `SEMANTIC_CONSTRUCTION_UNDERCOVERS` would require RAW establishing facts the World omitted; harbor Q3’s blank-hours fact is in the World. `UNSUPPORTED_CLOSURE_RISK` would require Worlds admitting unsupported truth; they did not.

---

## Trial-level construction

| domain | trial | build | attempts | relations | assertions | SOURCE groundings | failures |
| --- | --- | --- | --- | --- | --- | --- | --- |
| harbor_towing | T1 | ACCEPTED | 1 | 9 | 40 | 25 | 6 |
| harbor_towing | T2 | ACCEPTED | 1 | 7 | 31 | 14 | 5 |
| seed_grants | T1 | ACCEPTED | 1 | 9 | 38 | 30 | 8 |
| seed_grants | T2 | ACCEPTED | 1 | 9 | 38 | 38 | 8 |
| makerspace_checkout | T1 | ACCEPTED | 1 | 7 | 29 | 27 | 1 |
| makerspace_checkout | T2 | ACCEPTED | 1 | 11 | 44 | 16 | 5 |

T1 vs T2 relation names are mostly disjoint. Auto-scorer coverage tags are identical.

---

## Critical audits

- **No hardcoded evaluation answers.** Search of each sealed `construction.py` for hidden-question strings: none.
- **No raw-source dependency after compilation.** WORLD workspaces had no `sources/` reads. Isolation preflight `ok`.
- **No result laundering.** Harbor J7 is `insufficient_evidence`, not “not an emergency.” Seed status S is `UNINTERPRETED`, not a invented label.
- **No false completeness.** Harbor Q3 was not scored sufficient merely because a consumer guessed 1 — consumers guessed 3, and the report records the WORLD-column vs PURPOSE-table grain.

---

## Required questions

### 1. Can the host autonomously build a valid grounded World from an untouched heterogeneous folder and natural-language purpose?

**MEASURED:** yes, 6/6 trials, one attempt each.

**OBSERVED:** hosts received only the domain folder, `purpose.txt`, frozen `runtime_v0`, TaskView, and ordinary Python.

### 2. How often does construction succeed without evaluator or human semantic feedback?

**MEASURED:** 6/6 accepted; 0 gold files in host workspaces; 0 human corrections; 0 post-build evidence-resolution loops.

### 3. Does the resulting World contain the distinctions necessary for held-out computations the host never saw?

**MEASURED:** auto-scorer PRESENT on 24/24 establishable question×trial cells.

**OBSERVED:** T1 Worlds contain the held-out numbers 240, 180, 2280, 15000, 0, 2, 10000, 12, 18, 1, 24. Harbor blank billed-hours lives on `tow_job`, not only on PURPOSE `billable_hours`.

### 4. Does the World correctly expose genuine evidence insufficiency?

**MEASURED:** 12/12 construction cells Q5–Q6 tagged EXPLICITLY_UNRESOLVED. WORLD consumers: 15/18 UNRESOLVED_CORRECTLY.

**OBSERVED:** fuel surcharge, status S, PENDING, insurance rider, and match waiver remain failures rather than invented facts. Harbor Q6 World-side is correct; three consumers then answered `false`.

### 5. Are there any unsupported durable closures?

**MEASURED:** 0 construction `unsupported_closure_hits`. 0 Worlds asserting the evaluator’s forbidden closures.

**OBSERVED:** 3 consumer answers (harbor Q6) are unsupported closures of the **answer**, not of World tuples.

### 6. Can a fresh consumer answer purpose-relevant questions from World without raw sources?

**MEASURED:** yes. 47/54 WORLD answers in the target class (32 CORRECT + 15 UNRESOLVED_CORRECTLY). 9/9 runs completed without source files.

### 7. How does WORLD compare with RAW on establishable questions?

**MEASURED:** WORLD 32/36 CORRECT; RAW 36/36.

**OBSERVED:** gap is harbor Q3 (3) and seed Q4 C3 (1). Makerspace tied 12/12.

### 8. How does WORLD compare with RAW on non-establishable questions?

**MEASURED:** WORLD 15/18 UNRESOLVED_CORRECTLY; RAW 18/18.

**OBSERVED:** the WORLD miss is systematically harbor Q6 `false`, not invention of a surcharge or a status-S gloss.

### 9. When WORLD fails, is the cause missing semantics or inability to discover the semantic interface?

**OBSERVED:** neither as primary. Harbor Q3: semantics present, two grains, wrong grain chosen. Harbor Q6: unresolved present, closed as denial. Seed Q4 C3: match_rate present, waiver overlay over-read. See `failure_analysis.md`.

### 10. Does one accepted World support multiple computations without rebuild?

**MEASURED:** yes. Six questions per WORLD run against the same T1 sqlite. `n_sql_hint` 2–6 per run.

### 11. Are semantic relation decompositions different across construction trials while behavior remains stable?

**MEASURED:** yes on names (harbor 9 vs 7 relations; makerspace 7 vs 11; largely disjoint identifiers). Auto-scorer coverage tags identical T1/T2.

**HYPOTHESIS:** ontology is not the product; behavior is. This probe did not A/B consumers across T1 vs T2, so stability of *consumer* behavior across decompositions is unmeasured.

### 12. What are the dominant remaining capability failures?

**OBSERVED:**

1. PURPOSE vs WORLD grain (billable vs billed hours).
2. Treating unresolved / insufficient_evidence as `false`.
3. Overlaying one unestablished proposition (waiver) onto a neighboring established one (match rate).

Not: runtime crash, source discovery, grounding refusal of valid SOURCE, or ABI-name hunt.

### 13. Does the experiment support compile-once reusable semantic state rather than “agent answers questions from files”?

**HYPOTHESIS:** yes, with a size caveat. Construction happened once; nine WORLD consumers reused T1 without sources and recovered the purpose-relevant computations in the large majority of cells. RAW’s perfect score shows a capable agent can also answer from files **per question set**. The product claim is reuse without repeating reconciliation. This pack supports that claim. It does not show WORLD beating RAW at one-shot accuracy on a corpus this small.

### 14. Is ABI implementation now justified by observed consumer-interface failures, or can it remain deferred?

**HYPOTHESIS:** **remain deferred.** T1/T2 vocabulary drift is real and is the already-motivated ABI increment. This probe’s **failures** were not “the consumer could not find the relation.” Implementing ABI now would be repairing a failure mode the 18 consumers did not exhibit. Do not treat this sentence as permission to implement it here; the stop rule still holds.

### 15. What capability question should be tested next, if any?

**HYPOTHESIS:** not a bigger domain benchmark and not ABI. Next, if anything:

> Given an accepted World that already records unresolved, can a fresh consumer be required to keep unresolved as unresolved (no `false` from absence), and can PURPOSE-grain tables be kept from shadowing WORLD quantity columns?

That is a consumer-discipline / grain-discipline probe on frozen Worlds, still without runtime changes.

---

## Hypotheses H1–H4

| id | claim | reading |
| --- | --- | --- |
| H1 | End-to-end construction | **Supported.** 6/6 accepted. |
| H2 | Semantic sufficiency | **Mostly supported.** 32/36 WORLD establishable correct; remaining misses are grain/overlay, not empty Worlds. |
| H3 | Fail-closed uncertainty | **Supported on Worlds; mixed on WORLD consumers.** Worlds unresolved; 3/18 consumer cells closed harbor Q6. |
| H4 | Compile once, compute many | **Supported.** Six questions per World, no rebuild, no sources. Not a RAW-accuracy win. |

---

## STOP

Sealed. Do not modify `runtime_v0`, implement ABI, repair failed domains, add host conversation or human semantic correction, run obligation-targeted resolution, modify TaskView or Constructor, promote new primitives, or start a larger benchmark.

The current minimal system can compile a grounded programmable World from purpose plus messy evidence, and a fresh consumer can compute against that World more than once. A fresh agent on the raw folder is still more exact on this pack, mainly by not inventing a second grain and by not turning unresolved into `false`.
