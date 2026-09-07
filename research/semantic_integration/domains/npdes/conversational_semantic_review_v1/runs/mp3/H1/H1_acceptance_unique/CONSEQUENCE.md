# Consequence of domain expert reply

## What changed

The expert confirmed our core assumption: each FY2025 measurement should have exactly one governing numeric limit for compliance, not two parallel obligations. That matches the existing uniqueness requirement on `measurement_limit_pair`.

I recorded that certified policy explicitly in `construction.py`:

- Added a purpose-A requirement note (`governing_limit_uniqueness_policy`) stating that overlapping or staged limit rows and duplicate-looking schedule rows should be treated as one governing limit (history or restatement), not as multiple applicable limits, and that more than one candidate pair for the same measurement is a data conflict to flag—not valid multi-limit applicability.
- Added policy grounding on the `measurement_limit_pair` derivation so the join is documented as representing the single governing limit per measurement.

The existing `unique_applicable_limit_per_measurement` requirement with cardinality `ONE` was left in place. It already enforces what the expert described: if the data ever produced two candidate pairs for one measurement, the construction would emit a conflict hole rather than accepting both.

## What did not change

I did not change how measurement–limit pairs are built from the CSV. The join still follows the limit row already linked on each DMR measurement (`LIMIT_VALUE_ID`, `LIMIT_SET_SCHEDULE_ID`). I did not invent supersession rules, deduplication heuristics, or date-range searches across all permit-limit rows—the expert affirmed the conceptual model but did not give structured-field rules for picking the current row among overlaps or collapsing duplicates.

No other issues (NODI codes, permit-limit comments, document authority) were addressed in this reply and were left unchanged.

On this dataset the uniqueness requirement still passes: 824 FY2025 measurements, 824 pairs, one per measurement.
