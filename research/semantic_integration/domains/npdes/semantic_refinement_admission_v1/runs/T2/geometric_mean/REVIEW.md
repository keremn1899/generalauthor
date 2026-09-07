# Review: geometric_mean obligation

## Parent disposition

**REFINED** — not independently admitted or unresolved.

The parent question ("What does a geometric-mean reporting comment require for comparison of individual monitoring-period values?") is too coarse. All 40 trigger occurrences belong to NM0020583 (Farmington) limit set schedule 3600891019 and share identical DMR comment text, but retrieved evidence shows three mechanically separable classes with different semantic consequences.

## Evidence summary

1. **Limit-set comment propagation (24 rows).** Non-TDS parameters (BOD, TSS, pH, E. coli, flow, etc.) carry a comment that explicitly names only TDS discharge at Outfall 001. Footnote *6 in `documents/farmington/final_permit.txt` applies to TDS discharge reporting, not to BOD or other pollutants. Structured rows retain ordinary `STATISTICAL_BASE_TYPE_CODE` values (AVG/MAX/MIN).

2. **TDS report-only rows (12 rows).** Permit table shows TDS discharge and intake as "Report" with 1/Week frequency; footnote *6 requires geometric mean of weekly values. These rows have no `LIMIT_VALUE_NMBR` in structured data. The comment governs reporting, not numeric limit comparison.

3. **TDS net-increase numeric rows (4 rows).** Permit table and statement of basis describe the 497/449 mg/L net-increase limit as a 30-day average. Structured fields use `STATISTICAL_BASE_TYPE_CODE=AVG`. DMR measurements store monthly single values compared to the numeric limit. The geometric-mean footnote (*6) targets discharge reporting, not net-increase enforcement.

## Refinement children

| Child | Count | Disposition | Admission |
|-------|-------|-------------|-----------|
| `non_tds_comment_carryover` | 24 | SUPPORTED_NEGATIVE | ADMIT_DISPOSABLE |
| `tds_report_only_weekly_geom_mean` | 12 | SUPPORTED_RESOLUTION | ADMIT_DISPOSABLE |
| `tds_numeric_net_increase_comparison` | 4 | SUPPORTED_NEGATIVE | ADMIT_DISPOSABLE |

Partition is complete (40/40), non-overlapping, and mechanically computable from `PARAMETER_CODE` and `LIMIT_VALUE_NMBR`.

## Rejected interpretations

- **aggregate_before_compare** — Refuted for non-TDS carryover rows and for TDS net-increase rows where permit basis specifies 30-day average enforcement.
- **Parent-level UNRESOLVED** — Inappropriate once documents are consulted; insufficiency was an artifact of treating all 40 rows as one semantic class.

## Remaining uncertainty

Weekly sub-period sample values are not present in `dmr_measurements.csv`. The workspace cannot verify whether monthly reported values are pre-computed geometric means of weekly samples. This does not block partition-specific dispositions about comparison semantics.

## Dry-run construction deltas

Each ADMIT_DISPOSABLE child has a `dry_run/<child_id>/construction.py` that skips `aggregated_reporting_requirement` unresolved emission for its partition:

- `non_tds_comment_carryover`: skip when `PARAMETER_CODE != '70295'`
- `tds_report_only_weekly_geom_mean`: skip when TDS and `LIMIT_VALUE_NMBR` empty
- `tds_numeric_net_increase_comparison`: skip when TDS and `LIMIT_VALUE_NMBR` non-empty

## ADMISSION.json

Not written — obligation `requirement_schema` is `aggregated_reporting_requirement`, not `document_authority`.
