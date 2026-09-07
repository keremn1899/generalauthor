# Adjudication Review: geometric_mean

## What I investigated

I read `PASS_TASK_ADJUDICATE.md`, `PACKET.json`, and `construction.py` only. I did not search `documents/` or `sources/` beyond the frozen snippets in the packet. All retained snippets use admissible workspace `source_id` paths (`documents/farmington/final_permit.txt`, `sources/permit_limits.csv`, `sources/dmr_measurements.csv`).

The obligation asks: *What does a geometric-mean reporting comment require for comparison of individual monitoring-period values?* The relation contract states that aggregated reporting is not an ordinary single-period numeric comparison.

## What I found

### Source-established (TDS footnote *6 only)

Permit footnote *6 in `documents/farmington/final_permit.txt` authoritatively defines the geometric-mean comment for Total Dissolved Solids at Outfall 001: weekly measurements are inputs, and the permittee must **report the geometric mean value of weekly values**.

Part I reporting requirements items 3–4 in the same document establish that **reported aggregate statistics** (30-day average, monthly average, 7-day average, weekly average, daily maximum) exceeding effluent limitations constitute violations. This links reported aggregates—not raw single samples—to limit comparison.

Footnote *8 shows net TDS limits depend on **aggregated** discharge and influent values (footnotes *6 and *7 also require geometric mean of weekly values), supporting that compliance quantities are derived from aggregates rather than a single raw measurement.

Together, for TDS (PARAMETER_CODE 70295), the supported narrow interpretation is **aggregate_before_compare**: individual monitoring-period DMR values are not the direct compliance comparison quantity; the geometric mean of weekly values (or a net derived from such aggregates) is the reporting and comparison frame.

### Contradicted interpretations

- **applies_to_all_comment_rows**: Contradicted. The packet states that all 40 structured rows—including BOD (00310), E. coli (51040), pH (00400)—carry the identical TDS geometric-mean comment, but the permit assigns those pollutants footnotes *1–*5 with no geometric-mean reporting requirement. CSV correlation alone cannot extend footnote *6 semantics to non-TDS parameters.

- **reporting_only**: Contradicted for TDS. Part I items 3–4 tie reported values to violation evidence; the comment is not merely a display instruction.

- **ordinary_single_period**: Contradicted for TDS footnote *6, where weekly aggregation is required before reporting.

### Why the parent obligation remains UNRESOLVED

The packet's own `known_limitations` state that the parent obligation cannot receive a single disposition without refinement because structured occurrences conflate TDS-specific geometric-mean reporting with misattached limit-set comment rows for other parameters.

Additional unresolved factors:

1. Structured `STATISTICAL_BASE_TYPE_CODE` remains `AVG` (not `GM`) for all comment-bearing rows; no codebook in structured sources defines geometric-mean comparison semantics.
2. DMR structured data provide one value per monitoring period without weekly sample arrays; whether a stored DMR value is already a geometric mean cannot be determined from structured data alone.
3. Footnote *6 uses "Report" but does not explicitly say "compare geometric mean to limit"; the comparison linkage is supported by Part I aggregate-violation language and footnote *8 context, but the exact statistic wording differs ("weekly average" vs "geometric mean").

## Evidence supporting the narrow proposal

| Evidence | Supports |
|----------|----------|
| Footnote *6 (`final_permit.txt`) | Geometric mean of weekly values is the TDS reporting quantity |
| Part I items 3–4 (`final_permit.txt`) | Reported aggregates, not raw samples, are compared to limits |
| Footnote *8 (`final_permit.txt`) | Net TDS limits use aggregated values |
| `permit_limits.csv` row 3610673300 (PARAMETER_CODE 70295) | Structured TDS row whose comment matches footnote *6 |
| `permit_limits.csv` aggregate (40 rows, 10 parameters) | Same comment misattached to non-TDS parameters |

## What remains uncertain

- Uniform semantics across all 40 geometric-mean comment rows (WORLD scope).
- Whether DMR stored numeric values are pre-computed geometric means.
- Whether "weekly average" (Part I) and "geometric mean" (footnote *6) denote the same comparison statistic.
- Full permit cross-check for every parameter in the 40 structured rows.

## What would change if the proposal were admitted

A disposable edit to `construction.py` would apply a reusable parameter-code filter: only `PARAMETER_CODE == "70295"` rows with geometric-mean comment text would retain the `aggregated_reporting_requirement` unresolved flag. The ~36 misattached non-TDS rows would no longer be treated as geometric-mean aggregation obligations. This narrows scope from WORLD to ONE_SOURCE_VALUE (TDS footnote *6) without per-row model judgments.

`construction.py` itself is unchanged; the mapping appears only in `dry_run/construction.py`.
