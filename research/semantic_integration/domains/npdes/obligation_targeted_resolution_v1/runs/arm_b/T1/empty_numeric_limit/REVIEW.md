# Adjudication review: `empty_numeric_limit`

## What was investigated

Judgment was limited to the frozen `PACKET.json`, `PASS_TASK_ADJUDICATE.md`, and `construction.py` (for proposal feasibility only). No searches were run under `documents/` or `sources/`.

The semantic question: when `LIMIT_VALUE_NMBR` is empty, is the row a numeric limit, report-only monitoring, or something else? Purpose A requires classifying empty limits before numeric comparison; absence is not a denial.

## What was found

The packet's own `allowed_dispositions` permits only **UNRESOLVED**, which matches the evidence.

Empty `LIMIT_VALUE_NMBR` is **not one thing**. Retained workspace evidence shows at least four distinct readings across different rows:

| Pattern | Admissible evidence | Reading |
| --- | --- | --- |
| AVG row, empty number, permit says Report | `sources/permit_limits.csv` 3610129901; `documents/gcc/final_permit.txt` TSS table | Report-only monitoring for that statistical base |
| Q1 mass-load row, empty number, WHEN DISCHARGING comment | `sources/permit_limits.csv` 3610840340; `documents/aztec/final_permit.txt` N/A mass columns + footnote | Non-applicable limit column; numeric limit on sibling concentration row |
| Empty number, pass=0;fail=1 units and comment | `sources/permit_limits.csv` 3610839676 | Special pass/fail reporting, not ordinary numeric concentration |
| Report cells, geometric-mean footnote | `documents/farmington/final_permit.txt` TDS table + *6 | Aggregated reporting obligation, not a per-period numeric limit |

The **`numeric_limit`** candidate is not supported. The CSV aggregate states that **zero** of the 57 empty-number rows have a nonempty `LIMIT_VALUE_STANDARD_UNITS`, and permit narrative maps the corresponding cells to **Report** or **N/A**, not to a hidden numeric effluent limit recoverable for comparison.

## What evidence supports it

All citations above use admissible `source_id` paths under `sources/` or `documents/`. The heterogeneous partition (blank 18, WHEN DISCHARGING 12, PASS/FAIL 12, geometric mean 15) is mechanically stated in the packet from `sources/permit_limits.csv`. Permit-text snippets corroborate report-only and N/A readings for representative pollutants.

`construction.py` already treats emptiness structurally (`has_limit_value_nmbr`) and flags comment-driven edge cases (`pass_fail_reporting_semantics`, `aggregated_reporting_requirement`, `conditional_discharge_dependent_monitoring`) as `purpose.unresolved` rather than imposing a single world truth.

## What remains uncertain

- **No field legend**: no ICIS/NPDES codebook in the workspace defines `LIMIT_VALUE_NMBR` emptiness directly.
- **Incomplete permit crosswalk**: only 3 of 12 permit packages were opened; not every empty row was matched to permit-table text.
- **ENF typing contradiction**: all 57 empty rows carry `LIMIT_TYPE_CODE=ENF`, which conflicts with a blanket "monitoring-only" label.
- **Optional monitoring on WET rows**: `OPTIONAL_MONITORING_FLAG=Y` on some schedules blocks a uniform enforceability rule.
- **No FY2025 DMR instances**: zero FY2025 measurement rows have empty `LIMIT_VALUE_NMBR`, so Purpose A impact is structural inference, not observed join failure.

## What would change if admitted

**Nothing is admitted** (`PROPOSAL.json` → `admit: UNRESOLVED`). `construction.py` is unchanged.

Admission would require a **reusable, source-grounded disambiguation rule** (not per-row model judgment) that maps empty `LIMIT_VALUE_NMBR` rows into comparison-eligible vs monitoring-only vs special-encoding classes. The frozen packet does not supply a complete rule set covering all 57 rows and their ENF typing. A WORLD-scope single interpretation would be unsupported because permit and comment context splits the population.

If future evidence supplied a codebook definition or complete permit-table crosswalk for every empty row, a scoped proposal (likely `ONE_RELATION_OR_VOCABULARY` or row-pattern keyed `MECHANICALLY_DERIVED` classes) could add a `limit_comparison_eligibility` field to `permit_limit` and filter `numeric_comparison_candidate` accordingly. Until then, Purpose A correctly blocks comparison on `has_limit_value_nmbr` without treating absence as exceedance.
