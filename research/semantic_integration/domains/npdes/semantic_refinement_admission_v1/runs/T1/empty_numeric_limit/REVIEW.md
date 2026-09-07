# Review: empty_numeric_limit

## Parent disposition

**REFINED** — the parent question ("when LIMIT_VALUE_NMBR is empty, numeric limit, report-only, or something else?") is too coarse. Fifty-seven rows partition into four mechanically distinct classes with different supported answers. The parent is not independently admitted or unresolved.

## Evidence summary

Structured analysis of `sources/permit_limits.csv` confirms 57/105 rows have empty `LIMIT_VALUE_NMBR`. All carry `LIMIT_TYPE_CODE=ENF` but none have populated `LIMIT_VALUE_STANDARD_UNITS`. Partition by `DMR_COMMENT_TEXT` (priority-ordered, case-insensitive):

| Partition | Count | Permits | Supported answer |
|-----------|-------|---------|------------------|
| blank comment | 18 | NM0000116, NM0020583 | Report-only monitoring (SUPPORTED_NEGATIVE for numeric limit) |
| WHEN DISCHARGING | 12 | NM0028762 | Non-applicable mass-load column (SUPPORTED_NEGATIVE) |
| PASS=0/FAIL=1 | 12 | NM0020583 | Special pass/fail WET reporting (SUPPORTED_NEGATIVE) |
| geometric mean | 15 | NM0020583 | Aggregated reporting without per-period numeric limit (SUPPORTED_NEGATIVE) |

Partitions are complete (57/57), non-overlapping, and mechanically computable from structured fields.

## Permit grounding inspected

- **GCC (NM0000116):** Part I table maps TSS AVG and dissolved-metal concentration cells to "Report" while Daily Max carries numeric limits (50 mg/L TSS). Grounds blank-comment rows.
- **Aztec (NM0028762):** N/A lbs/day columns with numeric mg/L limits; footnote *1 "When discharging." Grounds WHEN DISCHARGING rows.
- **Farmington (NM0020583):** Report cells for legacy pollutants; TDS geometric-mean footnote *6; WET pass/fail encoding in structured DMR comment. Grounds blank-comment, geometric-mean, and pass/fail partitions.

## Withheld generalizations

- `LIMIT_TYPE_CODE=ENF` alone does not establish numeric limit semantics (all 57 are ENF).
- Sibling numeric limits on same `LIMIT_ID` (8 rows) do not classify the empty row without partition context.
- No workspace codebook defines `LIMIT_VALUE_NMBR` emptiness directly.

## Construction impact

Trial T5 (`construction.py`) filters `numeric_comparison_candidate` on `has_limit_value_nmbr`, dropping all 57 rows without a named classification hole. Four child partitions each admit a disposable semantic delta via `dry_run/<child_id>/construction.py`, adding a purpose derive relation with partition-rule grounding.

## Residual

Zero residual occurrences in this corpus. Pass/fail and geometric-mean children resolve classification for Purpose A blocking but leave period-level compliance semantics unresolved (existing `purpose.unresolved` entries in construction.py).

## Not produced

`ADMISSION.json` — obligation is not `document_authority` schema.
