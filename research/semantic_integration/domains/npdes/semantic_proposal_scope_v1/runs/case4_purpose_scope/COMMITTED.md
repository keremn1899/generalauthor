# Committed: multi_applicable_limits

## Expert acceptance

The expert accepted the proposal with: **"Yes, that's what I mean."** (`ACCEPT.md`)

The chosen dry run was **`multi_applicable_limits`** (`CHOSEN_DRY_RUN.txt`).

## What was committed

`construction.py` was overwritten with `dry_run/multi_applicable_limits/construction.py`.

### Purpose A: how measurements are paired with limits

Previously, each FY2025 measurement was paired with at most one permit-limit row—the one whose `LIMIT_VALUE_ID` and `LIMIT_SET_SCHEDULE_ID` matched the measurement row directly.

Now, each FY2025 measurement is matched to **every** permit-limit catalog row that shares permit, outfall (feature), and parameter, and whose effective interval contains the monitoring period. Restated catalog rows are collapsed before materialization, using limit type code, limit id, standard-unit value, value qualifier, and statistical base as the deduplication key. All surviving pairs are kept.

### Purpose A: uniqueness requirement

The requirement `unique_applicable_limit_per_measurement` changed from **exactly one** applicable limit per measurement (`cardinality="ONE"`) to **at least one** (`cardinality="AT_LEAST_ONE"`), with no upper bound after deduplication.

### Scope

This multiplicity policy applies **only to Purpose A**. It was not generalized to Purposes B or C, and it was not restated as a WORLD-mode rule.

### Measurable effect on this dataset (from dry run)

| Relation | Before | After |
|---|---:|---:|
| `measurement_limit_pair` | 824 | 2,812 |
| `numeric_comparison_candidate` | 342 | 1,336 |

Unresolved issue groups (8) and total unresolved items (535) are unchanged from the baseline draft.

## What did not change

- **`source.py`**, **`world_api.py`**, purpose definitions (`purposes/`), and source data (`sources/`) were not modified.
- **WORLD-mode semantics** are unchanged (`WORLD_semantics_changed: false` in the dry-run delta).
- **Purposes B and C** requirements and derivations (`monitoring_requirement_fy2025`, `no_numeric_result_case`, and their purpose requirements) were not altered by this commit.
- Base mapped relations (`dmr_measurement`, `permit_limit`, `permit_document`) and the `fy2025_measurement` derivation are structurally the same.
- The eight existing unresolved issue groups and their instance counts are the same as before.
- The **`dry_run/`** directory and other proposal artifacts were left in place; only `construction.py` was updated.

## What remains unresolved

The expert did not settle:

1. **Which catalog fields define a restated duplicate row** beyond the collapse key used in the dry run (limit type code, limit id, standard-unit value, value qualifier, statistical base).
2. **Whether downstream comparison requirements** (numeric value, operator, qualifier, statistical base) should stay scoped per measurement or be re-scoped per measurement–limit pair when multiple limits survive.

These ambiguities were noted in `PROPOSAL.json` and `ACCEPTANCE.md` and were not part of what the expert confirmed.
