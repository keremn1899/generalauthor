# Review: geometric_mean obligation

## Parent disposition

**REFINED** — not independently admitted, not independently unresolved.

The parent question ("What does a geometric-mean reporting comment require for comparison of individual monitoring-period values?") is too coarse for the 40 triggered rows. All rows share one identical `DMR_COMMENT_TEXT` string naming TDS at Outfall 001, but `PARAMETER_CODE` spans ten distinct parameters. Permit documents ground three distinct semantic regimes; treating them as one answer would either over-block or under-specify comparison logic.

## Evidence summary

| Source | Finding |
|--------|---------|
| `sources/permit_limits.csv` | 40 rows, one comment, 10 parameters; all `STATISTICAL_BASE_TYPE_CODE` in {AVG, MAX, MIN}; no geometric-mean code |
| `documents/farmington/final_permit.txt` | Footnote *6/*7: geometric mean of weekly values for TDS discharge/intake **Report** rows; footnote *8: net TDS derived quantity; net-increase limit in 30-DAY AVG column |
| `documents/farmington/statement_of_basis.txt` | TDS net incremental increase limit is **30-day average** (497 → 449 mg/L) |
| `sources/dmr_measurements.csv` | Monthly single values per period; no weekly sub-sample rows |

Aztec and GCC documents contain unrelated geometric-mean mentions (metals RP, fecal coliform) not tied to this obligation's `DMR_COMMENT_TEXT` trigger.

## Refinement partitions

| Child | Rule | Count | Disposition |
|-------|------|-------|-------------|
| `geom_mean_non_tds_carryover` | `PARAMETER_CODE != '70295'` | 24 | SUPPORTED_NEGATIVE — comment non-operative |
| `geom_mean_tds_report_only` | `70295` + no `LIMIT_VALUE_NMBR` | 12 | SUPPORTED_RESOLUTION — report geometric mean of weekly values; no numeric comparison |
| `geom_mean_tds_net_increase_comparison` | `70295` + has `LIMIT_VALUE_NMBR` | 4 | SUPPORTED_NEGATIVE — 30-day average governs comparison, not geometric-mean comment |

Partition is complete (24+12+4=40), non-overlapping, and mechanically computable from structured fields.

## Proposals admitted

Three partition-specific proposals admitted as `ADMIT_DISPOSABLE` with matching `dry_run/<child_id>/construction.py` deltas that skip `aggregated_reporting_requirement` unresolved only for the admitted partition.

Rejected: uniform aggregate-before-compare (no grounding for non-TDS rows), global reporting-only without partition (too coarse), parent-level UNRESOLVED (partition differences are not global insufficiency).

## ADMISSION.json

Not written. `OBLIGATION.md` declares `requirement_schema: aggregated_reporting_requirement`, not `document_authority`. Document text was used as source-established grounding for child dispositions but through the refinement/admission proposal workflow rather than a separate document-authority admission ledger.

## Residual uncertainty (outside refined children)

- Whether monthly DMR values are pre-aggregated geometric means of weekly samples (weekly sub-period data absent from `dmr_measurements.csv`).
- Whether a single monthly reported value satisfies the 30-day average for TDS net-increase limits (measurement-window mapping not established).
- These are measurement-aggregation questions, not geometric-mean-comment semantics; they remain outside the three admitted children.
