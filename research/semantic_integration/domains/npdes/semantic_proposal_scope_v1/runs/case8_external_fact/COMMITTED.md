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

- **`permit_document_text_not_available` remains unresolved.** Structured sources still provide only filenames and hashes; narrative permit text is not available as structured evidence.

- **All existing mapped and derived relations are unchanged** in row counts on this dataset: `dmr_measurement` (824), `permit_limit` (105), `permit_document` (12), `fy2025_measurement` (824), `measurement_limit_pair` (824), `numeric_comparison_candidate` (342), `no_numeric_result_case` (186), `monitoring_requirement_fy2025` (105).

- **The alternative dry run `purpose_policy_bc` was not committed.** That encoding would have treated the override rule as an analysis policy for purposes B and C only.

- **Source files, `source.py`, `world_api.py`, and purpose definitions were not modified.**

## Dry-run outcome for the committed construction

On this dataset, `legal_hierarchy_world` ran without errors. Compared to the baseline, it added one `document_kind_precedence` row and increased unresolved holes by one group and one instance (the new `permit_document_authority_other_kinds` item). All other hole counts were unchanged.
