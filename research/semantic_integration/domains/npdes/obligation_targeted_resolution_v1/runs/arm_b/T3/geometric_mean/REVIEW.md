# Adjudication review: geometric_mean

## What was investigated

Judgment was limited to `PASS_TASK_ADJUDICATE.md` and the frozen `PACKET.json`. No searches of `documents/` or `sources/` were performed beyond the retained snippet text already in the packet.

The obligation asks: **what does a geometric-mean reporting comment require for comparison of individual monitoring-period values?** The relation contract is that aggregated reporting is not an ordinary single-period numeric comparison. Three candidate interpretations were evaluated against retained and contradictory packet evidence.

## What was found

### Supported (TDS footnote *6–*8 cluster)

Permit narrative snippets in the packet establish TDS-specific semantics:

- Footnotes *6 and *7 require reporting the **geometric mean of weekly values** for TDS discharge and intake measurements.
- Footnote *8 defines net TDS as a **derived difference**, not a direct single-sample reading.
- The TDS effluent table shows discharge/intake as report-only rows and net increase as numeric limits (497 / 449 mg/L).
- Part I.C ties violations to **named aggregate statistics** on the DMR (30-day average, monthly average, weekly average, etc.), not raw individual samples.
- The statement of basis frames the enforceable net-increase limit as a **30-day average**.
- Structured limit rows for parameter **70295** (TDS net increase) combine `STATISTICAL_BASE_TYPE_CODE=AVG`, weekly frequency, and the geometric-mean reporting comment.

Together, these workspace sources support `tds_aggregated_reporting`: for TDS net-increase enforcement, individual weekly monitoring-period values are not the comparison unit; comparison belongs to aggregated reported values aligned with the limit's statistical base.

### Rejected (schedule-wide geometric mean)

Contradictory packet evidence refutes `schedule_wide_geometric_mean`. Twenty-four non-TDS rows on schedule 3600891019 (e.g., BOD, pH) carry the same DMR comment text naming TDS geometric-mean reporting, yet retain ordinary numeric concentration limits at 5/week frequency. Permit footnotes *6–*7 name **only TDS**. CSV co-occurrence alone cannot extend geometric-mean comparison blocking to every parameter on the schedule.

### Rejected for TDS net increase (reporting-only, no comparison block)

`reporting_only_no_comparison_block` is inconsistent with the TDS net-increase evidence above: the permit and basis document frame enforceable net-increase limits as aggregated (30-day average), and Part I.C defines violation evidence in aggregate terms.

For **non-TDS** rows bearing the comment, the permit does not extend footnote semantics; those rows do not gain a geometric-mean comparison block from the comment text alone.

## Evidence supporting the judgment

| Claim | Basis | Epistemic status |
| --- | --- | --- |
| TDS weekly values require geometric-mean reporting | `final_permit.txt` footnotes *6–*7 | SOURCE_ESTABLISHED |
| TDS net-increase limit is aggregated (30-day average) | `final_permit.txt` table + Part I.C; `statement_of_basis.txt` | SOURCE_ESTABLISHED |
| Individual weekly samples are not the net-increase exceedance unit | Part I.C aggregate violation language + AVG limit rows for 70295 | SOURCE_ESTABLISHED |
| Schedule-wide geometric-mean comparison blocking is false | Contradictory non-TDS rows + TDS-only footnotes | SOURCE_ESTABLISHED (negative) |
| Monthly DMR scalar equals geometric mean of weeklies | — | Not established (no weekly sub-period rows) |

## What remains uncertain

1. **Aggregation mechanics**: The workspace has no weekly sub-period measurement rows, so it cannot verify that monthly DMR values equal geometric means of weekly samples.
2. **Formula gap**: The permit does not state an explicit formula mapping weekly geometric means to the 30-day-average net-increase limit.
3. **Discharge/intake TDS rows (*6, *7)**: Report-only in the permit table; the proposed disposable mapping keys on parameter 70295 (net increase) and does not separately encode *6/*7 discharge/intake parameter codes from the packet alone.

## What would change if admitted

`PROPOSAL.json` recommends **ADMIT_DISPOSABLE** with scope **ONE_RELATION_OR_VOCABULARY** (not WORLD truth).

If admitted, `dry_run/construction.py` would:

1. Exclude parameter **70295** rows whose comment contains `GEOMETRIC MEAN` from `numeric_comparison_candidate`, encoding that aggregated TDS net-increase reporting is not ordinary single-period numeric comparison.
2. Stop emitting `aggregated_reporting_requirement` unresolved holes for non-70295 rows that share the schedule-level TDS comment text, because permit footnotes establish TDS-only applicability.

Production `construction.py` is unchanged. The disposable edit is a reusable parameter-code mapping, not per-row adjudication.

## Disposition

**SUPPORTED_RESOLUTION** for the scoped TDS footnote interpretation; **SUPPORTED_NEGATIVE** for schedule-wide and reporting-only readings where contradicted. Overall scope is **ONE_RELATION_OR_VOCABULARY**, not WORLD.
