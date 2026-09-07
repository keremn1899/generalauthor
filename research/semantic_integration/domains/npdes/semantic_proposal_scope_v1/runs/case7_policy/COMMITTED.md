# Committed

The expert accepted the proposal with: "Yes, that's what I mean."

The chosen dry-run construction was `final_permit_over_fact_sheet` (from `CHOSEN_DRY_RUN.txt`). That dry-run file existed, so `construction.py` was overwritten with `dry_run/final_permit_over_fact_sheet/construction.py`.

## What is now in construction.py

`construction.py` now records the user-certified analysis policy that, when the final permit and fact sheet disagree, the final permit governs. This appears as a PURPOSE-mode `document_conflict_authority` derivation grounded in the user utterance: "For this analysis, if the final permit and fact sheet disagree, use the final permit."

The existing `permit_document_text_not_available` unresolved item remains, with grounding that now also references the certified conflict policy (`document_conflict_authority`).

A new unresolved item, `document_authority_among_other_kinds`, was added for inventoried document kinds other than `final_permit` and `fact_sheet`. Authority among those other kinds is not established for this analysis.

The rest of the construction—the structured mappings and derivations for DMR measurements, permit limits, permit documents, FY2025 measurements, measurement–limit pairs, numeric comparison candidates, no-numeric-result cases, monitoring requirements, and the other purpose requirements and unresolved items—was already present and is unchanged apart from the additions above.

## What did not change

- `source.py`, `world_api.py`, and all files under `sources/` and `purposes/`
- The dry-run copy at `dry_run/final_permit_over_fact_sheet/construction.py`
- Other project files (`README.md`, `PROPOSAL.json`, `ACCEPT.md`, and so on)
