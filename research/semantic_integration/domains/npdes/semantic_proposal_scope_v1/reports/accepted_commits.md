# Accepted commits

## MEASURED

| case | committed | matches dry-run | revert ok | unrelated damage |
| --- | --- | --- | --- | --- |
| case1_bare_rejection | N | — | — | N |
| case2_underspecified | N | — | — | N |
| case3_substantive | N | — | — | N |
| case4_purpose_scope | Y | Y | Y | N |
| case5_world_generalization | Y | Y | Y | N |
| case6_uncertainty | N | — | Y | N |
| case7_policy | Y | Y | Y | Y |
| case8_external_fact | Y | Y | Y | Y |

## OBSERVED

### case4_purpose_scope

commit_delta: `{"relation_count_changes": {"measurement_limit_pair": {"baseline": 824, "proposed": 2812}, "numeric_comparison_candidate": {"baseline": 342, "proposed": 1336}}, "requirements_added": [], "requirements_removed": [], "requirements_changed": [{"name": "unique_applicable_limit_per_measurement", "baseline": {"name": "unique_applicable_limit_per_measurement", "kind": "UNIQUE", "purpose": ["A"], "cardinality": "ONE", "relation": "measurement_limit_pair", "field": null, "known": null}, "proposed": {"name": "unique_applicable_limit_per_measurement", "kind": "UNIQUE", "purpose": ["A"], "cardinality": "AT_LEAST_ONE", "relation": "measurement_limit_pair", "field": null, "known": null}}], "relation_mode_changes": {}, "n_hole_groups": {"baseline": 8, "proposed": 8}, "n_hole_instances": {"baseline": 535, "proposed": 535}, "hole_requirements_added": [], "hole_requirements_removed": [], "WORLD_semantics_changed": false, "PURPOSE_semantics_changed": true, "ok": {"baseline": true, "proposed": true}}`

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

The requirement `unique_applicable_limit_per_measurement` changed from **exactly one** applicable limit per measurement (`cardinality="ONE"`) to **at least one** (`cardinality="AT_LEAST_O

revert: `{"construction_restored": true, "sources_unchanged": true, "rerun_matches_baseline": true}`

### case5_world_generalization

commit_delta: `{"relation_count_changes": {"measurement_limit_pair": {"baseline": 824, "proposed": 2812}, "numeric_comparison_candidate": {"baseline": 342, "proposed": 1336}}, "requirements_added": [], "requirements_removed": [], "requirements_changed": [{"name": "unique_applicable_limit_per_measurement", "baseline": {"name": "unique_applicable_limit_per_measurement", "kind": "UNIQUE", "purpose": ["A"], "cardinality": "ONE", "relation": "measurement_limit_pair", "field": null, "known": null}, "proposed": {"name": "unique_applicable_limit_per_measurement", "kind": "UNIQUE", "purpose": ["A"], "cardinality": "AT_LEAST_ONE", "relation": "measurement_limit_pair", "field": null, "known": null}}], "relation_mode_changes": {"measurement_limit_pair": {"baseline": "PURPOSE", "proposed": "WORLD"}}, "n_hole_groups": {"baseline": 8, "proposed": 8}, "n_hole_instances": {"baseline": 535, "proposed": 535}, "hole_requirements_added": [], "hole_requirements_removed": [], "WORLD_semantics_changed": true, "PURPOSE_semantics_changed": true, "ok": {"baseline": true, "proposed": true}}`

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

Per the dry-run results, this raises `measurement_limit_pair` from 824 to 2,812 rows and `numeric_comparison_ca

revert: `{"construction_restored": true, "sources_unchanged": true, "rerun_matches_baseline": true}`

### case7_policy

commit_delta: `{"relation_count_changes": {"document_conflict_authority": {"baseline": null, "proposed": 1}}, "requirements_added": ["document_authority_among_other_kinds"], "requirements_removed": [], "requirements_changed": [], "relation_mode_changes": {"document_conflict_authority": {"baseline": null, "proposed": "PURPOSE"}}, "n_hole_groups": {"baseline": 8, "proposed": 9}, "n_hole_instances": {"baseline": 535, "proposed": 536}, "hole_requirements_added": ["document_authority_among_other_kinds"], "hole_requirements_removed": [], "WORLD_semantics_changed": true, "PURPOSE_semantics_changed": true, "ok": {"baseline": true, "proposed": true}}`

# Committed

The expert accepted the proposal with: "Yes, that's what I mean."

The chosen dry-run construction was `final_permit_over_fact_sheet` (from `CHOSEN_DRY_RUN.txt`). That dry-run file existed, so `construction.py` was overwritten with `dry_run/final_permit_over_fact_sheet/construction.py`.

## What is now in construction.py

`construction.py` now records the user-certified analysis policy that, when the final permit and fact sheet disagree, the final permit governs. This appears as a PURPOSE-mode `document_conflict_authority` derivation grounded in the user utterance: "For this analysis, if the final permit and fact sheet disagree, use the final permit."

The existing `permit_document_text_not_available` unresolved item remains, with grounding that now also references the certified conflict policy (`document_conflict_authority`).

A new unresolved item, `document_authority_among_other_kinds`, was added for inventoried document kinds other than `final_permit` and `fact_sheet`. Authority among those other kinds is not established for this analysis.

The rest of the construction—the structured mappings and derivations for DMR measurements, permit limits, permit documents, FY

revert: `{"construction_restored": true, "sources_unchanged": true, "rerun_matches_baseline": true}`

### case8_external_fact

commit_delta: `{"relation_count_changes": {"document_kind_precedence": {"baseline": null, "proposed": 1}}, "requirements_added": ["permit_document_authority_other_kinds"], "requirements_removed": [], "requirements_changed": [], "relation_mode_changes": {"document_kind_precedence": {"baseline": null, "proposed": "WORLD"}}, "n_hole_groups": {"baseline": 8, "proposed": 9}, "n_hole_instances": {"baseline": 535, "proposed": 536}, "hole_requirements_added": ["permit_document_authority_other_kinds"], "hole_requirements_removed": [], "WORLD_semantics_changed": true, "PURPOSE_semantics_changed": true, "ok": {"baseline": true, "proposed": true}}`

# Committed

## Expert acceptance

The expert said: "Yes, that's what I mean."

## What was committed

`construction.py` was overwritten with the dry-run construction `legal_hierarchy_world` (as named in `CHOSEN_DRY_RUN.txt`).

That construction encodes the user's statement — "The final permit legally overrides the fact sheet." — as a general legal fact in the world, not as a purpose-specific analysis policy.

Concrete additions in `construction.py`:

1. **New relation `document_kind_precedence`** — records legal precedence between permit package document kinds when narrative conditions conflict. It has two text fields: `superior_document_kind` and `subordinate_document_kind`.

2. **One mapped row** — `final_permit` takes precedence over `fact_sheet`, grounded as a user-asserted external fact.

3. **New unresolved item `permit_document_authority_other_kinds`** — legal precedence among other inventoried document kinds (for example `statement_of_basis`, `reasonable_potential`, `minor_modification`, `appendices`) is still not established. The dry run listed these other kinds from the document inventory.

## What did not change

- **`permit_document_text_not_available` remains unresolv

revert: `{"construction_restored": true, "sources_unchanged": true, "rerun_matches_baseline": true}`

## HYPOTHESIS

Acceptance after a dry-run can keep proposed and committed deltas aligned, and commits can revert without source mutation.
