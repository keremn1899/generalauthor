# Committed

## Expert acceptance

The expert accepted with: "Yes, that's what I mean."

The chosen dry run was `world_multi_applicable_limits` (from `CHOSEN_DRY_RUN.txt`).

## What is now committed

`construction.py` was overwritten with the dry-run construction from `dry_run/world_multi_applicable_limits/construction.py`.

That construction changes how measurement–limit applicability is modeled:

- **Multiple applicable limits per measurement.** After collapsing duplicate or restated permit-limit catalog rows, each FY2025 measurement is matched to every permit-limit row that shares permit, outfall, parameter, and an effective interval containing the monitoring period. All surviving pairs are materialized.
- **Catalog collapse key.** Restated rows are collapsed on limit type code, limit id, limit value standard units, limit value qualifier code, and statistical base type code.
- **`measurement_limit_pair` is now WORLD mode** (previously PURPOSE mode).
- **`unique_applicable_limit_per_measurement` now requires at least one pair per measurement** (previously exactly one).

Per the dry-run results, this raises `measurement_limit_pair` from 824 to 2,812 rows and `numeric_comparison_candidate` from 342 to 1,336 rows. The eight unresolved issue groups and 535 unresolved items are unchanged.

## What did not change

- `source.py`, `world_api.py`, source data under `sources/`, and purpose definitions under `purposes/` were not modified.
- Base mapped relations (`dmr_measurement`, `permit_limit`, `permit_document`) and other derived relations (`fy2025_measurement`, `no_numeric_result_case`, `monitoring_requirement_fy2025`) are unchanged except through the new measurement–limit pairing logic.
- Purpose requirements other than the cardinality change on `unique_applicable_limit_per_measurement` were not altered.
- The dry-run copy under `dry_run/world_multi_applicable_limits/` was left in place.

## What remains unresolved

From `PROPOSAL.json`, these were not settled by the expert’s acceptance:

1. Which structured fields define duplicate or restated catalog rows (the dry run uses the collapse key listed above).
2. Whether downstream per-measurement comparison requirements (numeric value, operator, qualifier, statistical base) should stay scoped per measurement or be re-scoped per measurement–limit pair when multiple limits survive.
