# Acceptance: multiple applicable limits as a general policy

## What you mean

You are affirming the multi-limit reading we previously clarified—after duplicate or restated permit-limit catalog rows are collapsed, a single measurement may still be governed by **multiple applicable limits**, including cases where those limits share the same limit type code but differ in other fields (such as limit id, numeric value, or statistical base). You are **not** asking us to force exactly one governing limit per measurement.

You are also withdrawing the earlier scope restriction. In your prior reply you said this policy should apply only to Purpose A and not be generalized. Your latest reply—“that’s generally true, not just for this analysis”—means the multiplicity policy is **general**, not limited to Purpose A or to this Federal FY2025 discharge-limit evaluation.

## Where it applies

- **WORLD level** — limit applicability is modeled as a general fact about how measurements relate to permit limits, not as a Purpose-A-only overlay.
- **All analyses** that depend on measurement–limit pairing and numeric comparison, including Purposes B and C and any future work beyond this dataset.
- The change is semantic scope (WORLD mode), not a one-off adjustment to a single purpose output.

## What rule would change

1. **`measurement_limit_pair`** would be derived at **WORLD** mode (not PURPOSE mode): match each FY2025 measurement to every permit-limit catalog row sharing permit, outfall, parameter, and an effective interval containing the monitoring period, collapse restated rows, and materialize all surviving pairs.

2. **`unique_applicable_limit_per_measurement`** would change from **exactly one** applicable limit per measurement to **at least one** per measurement, with no upper bound after deduplication.

## Measurable consequences (dry run vs. baseline draft)

| Measure | Baseline draft | Proposed (world_multi_applicable_limits) |
|---|---:|---:|
| measurement–limit pairs | 824 | **2,812** (+1,988) |
| numeric comparison candidates | 342 | **1,336** (+994) |
| unresolved issue groups | 8 | **8** (unchanged) |
| unresolved items (total) | 535 | **535** (unchanged) |

The expansion reflects measurements now paired with every surviving applicable limit after deduplication, rather than being forced to a single pair. Measurements that still have multiple collapsed limits sharing the same limit type code are treated as expected under your confirmed reading—they do not create new unresolved multiplicity holes.

All eight existing unresolved groups are unchanged in count:

- aggregated reporting requirements (40)
- conditional discharge-dependent monitoring (17)
- limit sample type codes (105)
- monitoring frequency codes (105)
- NODI code semantics (186)
- pass/fail reporting semantics (12)
- permit document text unavailable (1)
- permit limit comment text (69)

WORLD-mode semantics change (measurement_limit_pair moves from PURPOSE to WORLD). Purpose semantics also change for the cardinality relaxation.

On the current dataset, the row counts match what the prior Purpose-A-only dry run would have produced. The material difference from that prior round is **scope**: this policy now governs all purposes, not just Purpose A, even though Purposes B and C do not yet surface additional pair or comparison rows in this particular run.

## What remains unresolved

These were **not** settled by your reply and were **not** what separated competing dry-run interpretations in the current results:

1. **Which catalog fields define a restated duplicate row.** The dry run collapses on limit type code, limit id, standard-unit numeric value, value qualifier, and statistical base. A narrower or broader collapse key could shift pair counts, but you have not specified an alternative.

2. **How downstream comparison fields (numeric value, operator, qualifier, statistical base) should be scoped** when multiple limits survive for one measurement. The dry run materializes comparison candidates at the measurement–limit pair level (1,336 candidates across 2,812 pairs), which is consistent with per-pair scoping, but you have not explicitly confirmed that as policy.

Neither of these produced competing dry-run outcomes in the current results, and neither blocks accepting the core policy you confirmed.
