# Adjudication review: geometric_mean obligation

## What was investigated

Judgment was limited to the frozen packet in `PACKET.json` and adjudication rules in `PASS_TASK_ADJUDICATE.md`. No searches of `documents/` or `sources/` were performed beyond the retained snippets already in the packet. `construction.py` was read only to understand how the obligation is currently declared unresolved.

The exact semantic question:

> What does a geometric-mean reporting comment require for comparison of individual monitoring-period values?

The relation contract requires that aggregated reporting is not treated as an ordinary single-period numeric comparison.

## What was found

### Established from workspace sources (admissible snippets)

1. **TDS discharge reporting language** (`documents/farmington/final_permit.txt`, footnote *6): total dissolved solids measured at Outfall 001 must be reported as the geometric mean of weekly values. This is a reporting instruction tied to a specific permit footnote, not a structured field.

2. **TDS net-increase limit uses a different statistic** (`documents/farmington/statement_of_basis.txt`): the enforceable TDS net incremental increase limit is described as a **30-day average** (497 mg/L, later revised to 449 mg/L). Footnote *8 in `final_permit.txt` further defines net TDS as a derived quantity (discharge minus flow-weighted influent), not a single raw sample.

3. **Geometric mean appears elsewhere with a different window** (`statement_of_basis.txt`): E. coli limits are stated as a monthly geometric mean plus a single-sample limit. This shows the permit package uses geometric mean with explicit windows in some places, but that window differs from the TDS weekly footnote.

4. **Comment propagation across parameters** (`sources/permit_limits.csv`): the identical DMR comment text naming TDS and geometric mean of weekly values appears on both a BOD row (PARAMETER_CODE 00310, AVG base, 05/WK frequency) and a TDS row (PARAMETER_CODE 70295, AVG base, numeric limit 497). The comment text is TDS-specific but is attached to a non-TDS parameter within the same limit-set schedule.

5. **Structured measurements are monthly singletons** (`sources/dmr_measurements.csv`): for both the BOD and TDS example rows, one value is stored per `MONITORING_PERIOD_END_DATE` with `STATISTICAL_BASE_TYPE_CODE=AVG`. No weekly sub-period values or geometric-mean-specific fields appear in the retained measurement snippets.

### Contradictory or insufficient patterns (not sufficient alone for resolution)

- All 40 structured rows with the geometric-mean comment use `STATISTICAL_BASE_TYPE_CODE` in {AVG, MAX, MIN}; none encode geometric mean as the structured comparison basis.
- DMR measurements are monthly while many paired limits show weekly analysis frequency.
- Permit narrative distinguishes geometric-mean weekly **reporting** for TDS discharge from 30-day-average **enforcement** language for net increase, but no workspace text in the packet links those statistics to how a monthly DMR field should be compared to a numeric limit.
- Non-TDS parameters carry comment text that explicitly names only TDS.

Per adjudication rules, CSV structural correlation and plausible reading of mismatched fields are not enough to establish comparison semantics.

## Evidence supporting disposition

**Disposition: UNRESOLVED**

The packet establishes isolated facts about permit language and limit-set comment carryover, but it does **not** establish a proposition answering how individual monitoring-period values must be compared when the geometric-mean comment is present.

| Candidate interpretation | Packet verdict |
|---|---|
| `aggregate_before_compare` | Not established. Footnote *6 supports weekly geometric-mean reporting for TDS discharge, but weekly sub-period data are absent and no text requires geometric-mean aggregation before numeric limit comparison for all 40 rows. |
| `reporting_only` | Partially suggested for TDS (reporting vs 30-day-average enforcement in narrative sources), but not established as a general comparison rule for monthly DMR values in structured data. |
| `limit_set_metadata_artifact` | Established that the comment propagates to non-TDS rows (BOD example), but not established that this leaves comparison semantics unchanged for those rows—only that the comment text is mismatched. |
| `unresolved` | Best fit for the obligation as posed. |

**Epistemic basis:** UNRESOLVED at WORLD scope. Individual snippet facts are SOURCE_ESTABLISHED or MECHANICALLY_DERIVED, but no candidate interpretation is sufficiently grounded to resolve the comparison question.

**Failure mode:** EVIDENCE_INSUFFICIENT — missing codebook for statistical bases, absent weekly sub-period measurements, and no workspace text binding reporting language to structured monthly comparison behavior.

## What remains uncertain

- Whether monthly reported values are already geometric means of weekly samples or raw/end-of-period values.
- Which aggregation window applies when comparing a stored monthly DMR value to a numeric limit for TDS vs non-TDS parameters.
- Whether the geometric-mean comment alters enforcement comparison, reporting obligation only, or is inert metadata on non-TDS rows.
- How footnote *6 reporting requirements relate to the structured `numeric_comparison_candidate` path in `construction.py`.

## Proposal and construction impact

**Admit: UNRESOLVED**

No disposable construction edit is proposed. A WORLD-scope rule would require SOURCE_ESTABLISHED grounding for comparison semantics; the packet provides only partial, context-specific permit narrative plus structural mismatch evidence.

`construction.py` already marks rows whose `DMR_COMMENT_TEXT` contains "GEOMETRIC MEAN" as `aggregated_reporting_requirement` unresolved (purpose B and C). That posture remains correct.

## What would change if admitted

If a future packet established SOURCE_ESTABLISHED comparison semantics at narrower scope, admission might:

- **ONE_OCCURRENCE / ONE_SOURCE_VALUE (TDS discharge reporting):** add a derived relation distinguishing report-only geometric-mean obligations from numeric limit comparison rows, without changing non-TDS rows.
- **ONE_RELATION_OR_VOCABULARY (comment carryover):** tag limit rows whose comment text references a different parameter as metadata artifacts, resolving `aggregated_reporting_requirement` only for those rows.
- **WORLD (aggregate before compare):** replace direct monthly `numeric_comparison_candidate` pairing with an aggregation step requiring weekly sub-period inputs not present in current sources.

None of these are admissible from the current packet alone.
