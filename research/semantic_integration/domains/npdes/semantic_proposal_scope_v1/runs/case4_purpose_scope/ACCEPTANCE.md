# Acceptance: multiple applicable limits for Purpose A

## What you mean

You are confirming the correction we asked about: after duplicate or restated permit-limit catalog rows are collapsed, a single FY2025 measurement may still be compared against **multiple applicable limits**, including cases where those limits share the same limit type code but differ in other fields (such as limit id, numeric value, or statistical base). You are **not** asking us to keep forcing exactly one governing limit per measurement.

You are also drawing a scope line: this multiplicity policy applies **only to Purpose A** (applicable discharge limits for Federal FY2025). It should **not** be generalized to Purposes B or C, and it should **not** be restated as a global WORLD-mode rule.

## Where it applies

- **Purpose A only** — evaluating which enforceable numeric discharge limits apply to FY2025 measurements and whether reported values exceed them.
- **Not** Purposes B or C, and **not** a cross-purpose or WORLD-level applicability cap.

## What rule would change

The Purpose A requirement `unique_applicable_limit_per_measurement` would change from **exactly one** applicable limit per measurement to **at least one** per measurement, with no upper bound after deduplication.

Measurement–limit pairs would be derived by matching each FY2025 measurement to every permit-limit catalog row that shares permit, outfall, parameter, and an effective interval containing the monitoring period, **collapsing restated catalog rows first**, then materializing all surviving pairs.

## Measurable consequences (dry run vs. baseline draft)

| Measure | Baseline draft | Proposed (multi_applicable_limits) |
|---|---:|---:|
| measurement–limit pairs | 824 | **2,812** (+1,988) |
| numeric comparison candidates | 342 | **1,336** (+994) |
| unresolved issue groups | 8 | **8** (unchanged) |
| unresolved items (total) | 535 | **535** (unchanged) |

The expansion reflects measurements now paired with every surviving applicable limit after deduplication, rather than being forced to a single pair. The **692 measurements** that still have multiple collapsed limits sharing the same limit type code are treated as expected under your confirmed reading—they do not create new unresolved multiplicity holes.

All eight existing unresolved groups are unchanged in count:

- aggregated reporting requirements (40)
- conditional discharge-dependent monitoring (17)
- limit sample type codes (105)
- monitoring frequency codes (105)
- NODI code semantics (186)
- pass/fail reporting semantics (12)
- permit document text unavailable (1)
- permit limit comment text (69)

WORLD-mode semantics are unchanged; only Purpose A purpose semantics change.

## What remains unresolved

These were **not** settled by your reply and were **not** what separated the prior dry-run interpretations:

1. **Which catalog fields define a restated duplicate row.** The dry run collapses on limit type code, limit id, standard-unit numeric value, value qualifier, and statistical base. A narrower or broader collapse key could shift pair counts, but you have not specified an alternative.

2. **How downstream comparison fields (numeric value, operator, qualifier, statistical base) should be scoped** when multiple limits survive for one measurement. The dry run materializes comparison candidates at the measurement–limit pair level (1,336 candidates across 2,812 pairs), which is consistent with per-pair scoping, but you have not explicitly confirmed that as policy.

Neither of these produced competing dry-run outcomes in the current results, and neither blocks accepting the core policy you confirmed.
