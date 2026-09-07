# Adjudication Review: `empty_numeric_limit`

## What I Investigated

I read `PASS_TASK_ADJUDICATE.md` and the frozen `PACKET.json` only. I did not search `documents/` or `sources/` beyond what the packet cites. I read `construction.py` to understand how Purpose A currently handles empty `LIMIT_VALUE_NMBR` rows, but made no edits because the adjudication does not admit a disposable proposal.

The semantic question: when `LIMIT_VALUE_NMBR` is empty, is the row a numeric limit, report-only monitoring, or something else? Purpose A requires classifying empty numeric limits before comparison; absence of a value is not a denial.

## What I Found

**Uniform interpretations are refuted.** The packet refutes both `uniform_numeric_limit` (empty field still denotes a recoverable numeric concentration limit) and `uniform_report_only` (empty field uniformly means report-only with no numeric comparison). `LIMIT_TYPE_CODE = ENF` applies to all 57 empty-limit rows but also to many nonempty-limit rows, so it does not imply numeric concentration limits. `LIMIT_VALUE_TYPE_CODE` values (C1, C2, C3, Q1, Q2) appear on both empty and nonempty rows and do not discriminate.

**Heterogeneous non-numeric obligations are source-established for a majority of rows.** The retained `sources/permit_limits.csv` aggregate shows 57 empty-limit rows split by `DMR_COMMENT_TEXT`: 15 geometric-mean TDS, 12 when-discharging, 12 pass/fail WET, and 18 blank. Workspace permit text corroborates each comment-defined subclass:

- **Report-only monitoring:** `documents/gcc/final_permit.txt` PART I lists parameters (e.g., Dissolved Copper, Total Suspended) with "Report" as the effluent limitation where structured rows have empty `LIMIT_VALUE_NMBR`. `documents/aztec/final_permit.txt` and `documents/farmington/final_permit.txt` show the same pattern.
- **Pass/fail WET coding:** `documents/gcc/final_permit.txt` and `documents/farmington/final_permit.txt` PART II WET tables instruct entering "1" or "0" based on NOEC vs critical dilution. `sources/permit_limits.csv` row `LIMIT_VALUE_ID=22415` links this explicitly via `DMR_COMMENT_TEXT` with empty `LIMIT_VALUE_NMBR`.
- **Geometric-mean reporting:** `documents/farmington/final_permit.txt` footnote *6 directs reporting the geometric mean of weekly TDS values, matching 15 empty-limit TDS rows.
- **Conditional when-discharging monitoring:** `documents/aztec/final_permit.txt` footnote *1 ("When discharging") matches 12 empty-limit rows with `DMR_COMMENT_TEXT` "WHEN DISCHARGING."

**Purpose A cannot be resolved end-to-end.** Zero FY2025 DMR measurement rows in this workspace have empty `LIMIT_VALUE_NMBR`, so comparison behavior for these permit limits is unobservable from DMR data. `construction.py` already excludes rows without `has_limit_value_nmbr` from `numeric_comparison_candidate` and marks comment-pattern rows as `purpose.unresolved`, but does not assign obligation types to blank-comment rows.

## Evidence Supporting the Judgment

| Claim | Admissible grounding |
|-------|---------------------|
| Empty-limit rows are not uniformly numeric | CSV aggregate; `LIMIT_VALUE_TYPE_CODE` non-discrimination; permit "Report" language |
| Empty-limit rows are not uniformly report-only | CSV partition into WET pass/fail, geometric mean, when-discharging subclasses |
| Multiple distinct non-numeric obligation types exist | CSV comment partitions + matching permit narrative in gcc, aztec, farmington final permits |
| Structured fields alone do not fully classify all 57 rows | 18 blank `DMR_COMMENT_TEXT` rows; no field legend in workspace structured sources |

All cited snippets use workspace paths (`sources/` or `documents/`). No non-workspace `source_id` snippets were present in the packet.

## What Remains Uncertain

1. **18 blank-comment rows** — no `DMR_COMMENT_TEXT` subclass; permit-text matching is asserted in packet limitations but not individually grounded per row in the frozen packet.
2. **When-discharging applicability** — structured sources do not establish whether discharge occurred for evaluated periods.
3. **Geometric-mean TDS rows** — packet notes numeric limits may exist on separate permit schedule rows not under inspection.
4. **Purpose A execution** — no FY2025 DMR rows with empty `LIMIT_VALUE_NMBR` to observe comparison behavior.

## Disposition and Admission

**Disposition: UNRESOLVED.** The packet's `allowed_dispositions` permits only `UNRESOLVED`. Although workspace sources establish heterogeneous non-numeric obligation types for 39 of 57 rows and refute uniform interpretations, the relation contract requires classification before comparison for all empty-limit rows. Eighteen rows lack structured subclass assignment, and Purpose A behavior is unobservable. Failure mode: `EVIDENCE_INSUFFICIENT`.

**Proposal admission: UNRESOLVED.** A reusable comment-pattern classifier (as partially implemented in `construction.py` via `purpose.unresolved` calls) would not resolve blank-comment rows or discharge-condition applicability. WORLD-scope truth is not fully `SOURCE_ESTABLISHED`. No `dry_run/construction.py` was written; `construction.py` was not modified.

## What Would Change If Admitted

If a future packet admitted `ADMIT_DISPOSABLE` with complete `SOURCE_ESTABLISHED` grounding, `construction.py` would gain a reusable `empty_limit_obligation_type` (or similar) field on `permit_limit` rows derived from `DMR_COMMENT_TEXT` pattern rules—not per-row model judgments—with explicit `UNCLASSIFIED` for blank-comment rows. Purpose A would route classified non-numeric rows out of `numeric_comparison_candidate` and into purpose-specific unresolved or monitoring relations. That change is not warranted on the current packet.
