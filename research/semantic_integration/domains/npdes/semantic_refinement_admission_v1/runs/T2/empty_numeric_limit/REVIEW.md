# Review: empty_numeric_limit

## Parent disposition

**REFINED** — not independently admitted or unresolved.

The parent question ("numeric limit, report-only, or something else?") is too coarse. All 57 empty `LIMIT_VALUE_NMBR` rows partition mechanically into four mutually exclusive classes via structured `DMR_COMMENT_TEXT` patterns (blank 18, WHEN DISCHARGING 12, PASS=0/FAIL=1 12, geometric mean 15). Each class has distinct permit-grounded meaning.

## Evidence summary

| Partition | Count | Grounding | Child disposition |
|-----------|-------|-----------|-------------------|
| blank_comment | 18 | gcc/farmington permit Report cells | SUPPORTED_NEGATIVE (not numeric limit) |
| when_discharging | 12 | aztec N/A columns + footnote *1 | SUPPORTED_NEGATIVE (non-applicable column) |
| pass_fail_wet | 12 | structured DMR comment + pass=0;fail=1 units | SUPPORTED_NEGATIVE (pass/fail encoding) |
| geometric_mean | 15 | farmington footnote *6 + structured comment | SUPPORTED_NEGATIVE (aggregated reporting) |

Common structural facts: all 57 rows have `LIMIT_TYPE_CODE=ENF` and empty `LIMIT_VALUE_STANDARD_UNITS`, so emptiness alone does not yield a numeric comparison value. `LIMIT_TYPE_CODE=ENF` was not treated as a single-class answer because permit text and comment partitions override that reading.

## Admission

Four children admitted as **ADMIT_DISPOSABLE** with dry-run `construction.py` copies under `dry_run/<child_id>/`. Each adds one partition-specific derived relation and a Purpose A materialization requirement naming the classification hole that T5 previously left implicit.

Withheld proposals:
- **numeric_limit_via_enf**: ENF typing without value recovery path or permit support.
- **parent_single_class_report_only**: overgeneralizes Report-only evidence across heterogeneous partitions.

## Residual uncertainty

- **pass_fail_wet_encoding**: classification admitted; full pass/fail comparison semantics remain UNRESOLVED.
- **geometric_mean_aggregated_reporting**: classification admitted; per-period aggregation applicability remains UNRESOLVED.
- **when_discharging_non_applicable**: classification admitted; whether discharge occurred in evaluated periods remains UNRESOLVED.
- No ICIS field legend in workspace defines empty `LIMIT_VALUE_NMBR` semantics globally.

## Outputs written

- `EVIDENCE_PLAN.json`, `PACKET.json`, `PARENT.json`, `REFINEMENT.json`
- `PROPOSALS.json`, `RETRIEVAL_LOG.json`
- `dry_run/*/construction.py` for each ADMIT_DISPOSABLE child
- No `ADMISSION.json` (obligation is not `document_authority`)
