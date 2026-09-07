# Committed

## Expert acceptance

The expert accepted the understanding with these exact words:

> Yes, that's what I mean.

That acceptance applies to the utterance: *"I don't know what 9 means. Don't infer it from the pattern in the data."*

## What was committed to `construction.py`

**Nothing.** `CHOSEN_DRY_RUN.txt` contains no dry-run construction (the file is empty). Per the commit instructions, `construction.py` was left unchanged.

## Why no construction change was needed

The dry run produced no proposals (`DRY_RUN_RESULTS.json` lists `"proposals": []`). The baseline draft already treats all non-empty NODI codes, including code 9, as **UNINTERPRETED** under the `nodi_code_semantics` requirement (only the empty string is listed as known). The expert's statement confirms that code 9 should stay in that unresolved bucket rather than be inferred from data patterns.

## What did not change

- **`construction.py`** — unchanged; the existing semantic spine, relations, derivations, and purpose requirements remain as they were.
- **Hole profile** — unchanged from the baseline dry run: 8 hole groups, 535 hole instances. The `nodi_code_semantics` hole remains UNINTERPRETED for all 186 no-numeric-result cases (150 with code C, 36 with code 9).
- **Other source files** — `source.py`, `world_api.py`, CSV/JSON sources, and purpose files were not modified.

## What remains outside this acceptance

Per the proposal and acceptance notes, the expert did not address NODI code C (150 cases) or whether C and 9 are interchangeable. Those items remain open and were not changed by this commit.
