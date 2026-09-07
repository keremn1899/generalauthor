# Review: geometric_mean obligation

## Parent disposition

**REFINED** — not independently admitted or unresolved.

The parent question asks what a geometric-mean reporting comment requires for comparison of individual monitoring-period values across all 40 triggered rows. Retrieved evidence shows materially different semantics by partition:

| Partition | Count | Disposition |
|-----------|------:|-------------|
| Non-TDS limit-set comment carryover | 24 | SUPPORTED_NEGATIVE |
| TDS discharge reporting (loc=1) | 4 | SUPPORTED_RESOLUTION |
| TDS net-increase enforcement (loc=2, numeric limit) | 4 | SUPPORTED_NEGATIVE |
| Residual TDS report-only / loc=0 | 8 | UNRESOLVED |

Partitions are mechanically computable from `PARAMETER_CODE`, `MONITORING_LOCATION_CODE`, and presence of `LIMIT_VALUE_NMBR`. They are complete and non-overlapping (40/40).

## Key evidence

1. **Limit-set propagation**: All 40 rows share identical TDS-specific `DMR_COMMENT_TEXT` on limit set 3600645646 schedule 3600891019, including BOD, pH, E. coli, and flow parameters (`sources/permit_limits.csv`).

2. **Authoritative TDS footnotes**: Farmington final permit footnote *6 requires reporting the geometric mean of weekly TDS discharge values at Outfall 001; footnote *8 defines net TDS as a derived difference (`documents/farmington/final_permit.txt`).

3. **Enforcement statistic**: Statement of basis describes the TDS net-increase limit as a 30-day average (497 mg/L revised to 449 mg/L), not a geometric mean (`documents/farmington/statement_of_basis.txt`).

4. **Structured data gap**: All 40 rows use `STATISTICAL_BASE_TYPE_CODE` in {AVG, MAX, MIN}. DMR measurements store one monthly value per period; weekly sub-samples are absent from `dmr_measurements.csv`.

## Admitted children (ADMIT_DISPOSABLE)

Three reusable semantic deltas were written under `dry_run/`:

- `non_tds_limit_set_comment_carryover` — skip geometric-mean unresolved when `PARAMETER_CODE != '70295'`
- `tds_discharge_geometric_mean_reporting` — skip unresolved for TDS discharge reporting rows (`70295`, loc `1`)
- `tds_net_increase_avg_enforcement` — skip unresolved for TDS net-increase rows with numeric limits (`70295`, loc `2`, `LIMIT_VALUE_NMBR` present)

## Residual uncertainty

Eight TDS rows (four `MONITORING_LOCATION_CODE=0`, four report-only `MONITORING_LOCATION_CODE=2`) remain UNRESOLVED. Footnote *7 covers intake geometric-mean reporting but workspace structured fields do not map `MONITORING_LOCATION_CODE=0` to that footnote.

## Not written

`ADMISSION.json` was not produced: obligation schema is `aggregated_reporting_requirement`, not `document_authority`.
