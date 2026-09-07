# Adjudication Review: `empty_numeric_limit`

## What was investigated

The frozen packet `PACKET.json` for obligation `empty_numeric_limit` (Purpose A) was adjudicated against `PASS_TASK_ADJUDICATE.md` constraints. Only retained snippets whose `source_id` is a workspace path (`documents/` or `sources/`) were treated as admissible evidence. No corpus search beyond the packet was performed.

The exact semantic question is: **When LIMIT_VALUE_NMBR is empty, is the row a numeric limit, report-only monitoring, or something else?** The relation contract requires that empty limits be **classified before comparison** and that **absence is not a denial**.

## What was found

### Heterogeneous semantics, not one class

The packet presents five candidate interpretations. Workspace evidence supports several of them for **distinct subsets** of the 57 empty-limit rows, but none covers all rows and no structured field alone disambiguates them.

| Subset | Supported interpretation | Evidence |
|--------|-------------------------|----------|
| Matched Report/N/A permit columns (TSS avg, dissolved copper, flow, cyanide, TDS, cadmium avg) | Report-only monitoring in that limit slot | `documents/gcc/final_permit.txt`, `documents/gcc/fact_sheet.txt`, `documents/aztec/final_permit.txt`, `documents/farmington/final_permit.txt` |
| Same parameter, different limit-type row | Numeric limit may exist on a sibling populated row | Permit tables + contradictory evidence (e.g., NM0020583 TSS Q1/Q2 empty while C2/C3 carry 20/30 mg/L) |
| 12 WET retest rows with PASS/FAIL comment | Pass/fail (0/1) reporting, not concentration limit | `sources/permit_limits.csv` DMR_COMMENT_TEXT |
| Rows with "WHEN DISCHARGING." comment | Conditionally applicable monitoring | `documents/aztec/final_permit.txt` footnote *1; csv comment text |
| Rows with geometric-mean comment | Aggregated reporting obligation | `documents/farmington/final_permit.txt` footnotes *6-*7; csv comment text |
| 18/57 blank-comment rows | Unestablished—may be missing encoding | Known limitations in packet |

### Structured fields are insufficient classifiers

- **LIMIT_TYPE_CODE**: All 57 empty rows are `ENF`, yet permit text and comments show report-only, pass/fail, and conditional rows (`sources/permit_limits.csv` aggregate snippet). ENF does not establish a numeric concentration limit in the empty slot.
- **LIMIT_VALUE_TYPE_CODE**: No workspace codebook; Q1/Q2/C2/C3 patterns are inconsistent (packet contradictory evidence).
- **CSV correlation alone**: The packet explicitly warns against inferring semantics only from structural correlation; permit-text and comment-text grounding is required for several categories.

### What construction already does

`construction.py` already excludes empty `LIMIT_VALUE_NMBR` rows from `numeric_comparison_candidate` via `has_limit_value_nmbr`. It flags pass/fail, WHEN DISCHARGING, and geometric-mean rows as `purpose.unresolved(...)`. It does **not** positively classify empty rows into report-only vs pass/fail vs conditional vs gap.

## Evidence supporting partial conclusions

**Established from workspace sources (not admissible as a complete WORLD rule):**

1. Empty `LIMIT_VALUE_NMBR` on a row does **not** by itself mean the parameter lacks any numeric limit elsewhere (gcc fact sheet + aztec/farmington sibling-row patterns).
2. Permit tables marked "Report" or "N/A" for a column correspond to report-only monitoring in that slot, not a numeric concentration limit there (gcc, aztec, farmington permit tables).
3. WET retest rows with PASS=0/FAIL=1 comments encode non-concentration pass/fail reporting (`sources/permit_limits.csv`).
4. "WHEN DISCHARGING" and geometric-mean footnotes denote conditional or aggregated obligations whose per-period applicability is not established from structured sources alone.

## What remains uncertain

- **18/57 rows** with blank `DMR_COMMENT_TEXT` and no permit-text match in the packet.
- **Report-only classification** is established in permit documents but cannot be mechanically linked to all structured rows without document parsing beyond inventory.
- **Discharge occurrence** for WHEN DISCHARGING rows is not in structured sources.
- **FY2025 measurements**: No `dmr_measurements.csv` rows with empty `LIMIT_VALUE_NMBR`, so Purpose A comparison applicability cannot be empirically tested in this slice.
- **Positive taxonomy**: The obligation asks for classification before comparison; negative exclusion from numeric comparison is insufficient, and no reusable mapping covers all 57 rows.

## Judgment

**Disposition: UNRESOLVED**

The packet establishes multiple row-level semantics from workspace sources but does not establish a single classificatory resolution for all empty `LIMIT_VALUE_NMBR` occurrences. The obligation bundles heterogeneous cases under one question (`OBLIGATION_TOO_BROAD`). Partial SOURCE_ESTABLISHED evidence does not yield a complete ONE_RELATION_OR_VOCABULARY or WORLD resolution.

## Proposal status

**Admit: UNRESOLVED** — no `dry_run/construction.py` was written.

A comment-pattern-only mapping (`PASS/FAIL`, `WHEN DISCHARGING`, `GEOMETRIC MEAN`) would be MECHANICALLY_DERIVED and would leave 18 rows plus all report-only rows (permit-text-established but not structurally linkable) unresolved. A WORLD-scope rule equating empty limits to report-only monitoring would lack SOURCE_ESTABLISHED grounding for all occurrences and must not be admitted as World truth.

## What would change if admitted

If a disposable edit were admitted at **ONE_RELATION_OR_VOCABULARY** scope with **MECHANICALLY_DERIVED** grounding only:

- `permit_limit` rows with empty `LIMIT_VALUE_NMBR` would gain an `empty_limit_semantics` field from comment-pattern rules.
- ~39 rows with non-blank comments could receive pass_fail, conditional, or aggregated labels; ~18 blank-comment rows would remain explicitly unresolved.
- Report-only rows identified only via permit text would **not** be classified without new document-ingestion logic.
- `numeric_comparison_candidate` behavior would be unchanged (already gated on `has_limit_value_nmbr`).
- Purpose A obligations `limit_type_code_for_enforceability` and the existing `purpose.unresolved` entries would still require adjudication for rows outside comment-pattern coverage.

Admission would require demonstrating that comment-pattern rules alone satisfy the relation contract ("classified before comparison") for all affected rows; the frozen packet does not support that.
