# Consequence of domain expert reply on applicable limits

## What changed

The construction no longer assumes that each FY2025 measurement has exactly one governing numeric limit.

**Removed:** the purpose-A requirement `unique_applicable_limit_per_measurement` (cardinality ONE per measurement).

**Revised pairing:** `measurement_limit_pair` now lists every deduplicated permit-limit row that is in force for the measurement’s permit, outfall, parameter, and monitoring-period end date. Duplicate-looking catalog rows that share the same numeric value, units, and limit-kind fields are collapsed to one requirement before pairing. The limit identifiers already carried on the DMR row are still included when present, even if a schedule-variant duplicate would otherwise represent the same requirement.

On this fixture the pair count rises from 824 (one per measurement) to 2,768, with 692 measurements having more than one candidate limit and none having zero.

**Added unresolved dependencies (purpose A):**

- `measurement_to_limit_kind_matching` — structured sources do not establish which limit kind (for example grab versus average, mass versus concentration) a reported value should be checked against.
- `superseded_limit_applicability` — overlapping intervals may include superseded rows; structured sources do not identify which rows are no longer in play.

## What did not change

- The raw `dmr_measurement` and `permit_limit` world relations still mirror source rows without deduplication.
- No narrative permit text, comment phrases, NODI codes, or document authority were reinterpreted.
- No source fields were invented and no limits were marked superseded or inapplicable from guesswork.
- Numeric comparison candidates still require both a reported value and a limit numeric value; they now propagate from the expanded pair set.
- Other existing unresolved items (pass/fail comments, geometric-mean reporting, conditional discharge, missing permit text) are untouched.

## What remains open

The expert’s preferred end state—keep in-force limits for the period and limit type, drop catalog duplicates, then decide zero/one/several real comparisons—is only partly implemented. Deduplication and multi-limit pairing are in place; matching measurement reporting kind to limit kind and excluding superseded rows are explicitly left unresolved rather than approximated from incomplete structured evidence.
