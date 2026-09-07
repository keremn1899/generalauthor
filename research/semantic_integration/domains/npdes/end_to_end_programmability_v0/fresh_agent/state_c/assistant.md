I'll read the task files and inspect the SQLite database to answer Q1–Q3.

I have enough data from the database. Writing `ANSWERS.md`.

`ANSWERS.md` is complete. Summary:

**Q1 — Determinacy:** 342 of 824 FY2025 measurement/limit pairs are determinate for Purpose A numeric exceedance (`numeric_comparison_candidate`). The remaining 510 holes in `_hole` block determination across purposes A/B/C — chiefly `nodi_code_semantics` (186), `monitoring_frequency_code` / `limit_sample_type_code` (105 each), `permit_limit_comment_text` (52), `aggregated_reporting_requirement` (40), `discharge_occurrence_in_period` (17), `pass_fail_reporting_semantics` (4), and `permit_document_text_not_available` (1).

**Q2 — Numeric separation:** 342 rows are mechanically computable via `numeric_comparison_candidate`. The other 482 cannot get an exceedance determination: 186 lack a reported numeric value (`no_numeric_result_case`), 288 have a reported value but no numeric limit (`has_limit_value_nmbr=0`), and 8 use pass/fail reporting semantics.

**Q3 — Semantic sharpening:** The World does model discharge-conditioned monitoring — 17 `monitoring_requirement_fy2025` rows on NM0028762 have `monitoring_condition = 'discharge_occurrence'` established from "WHEN DISCHARGING." comments, with uncertainty only about `discharge_occurrence_in_period`. The other 88 monitoring requirements have empty `monitoring_condition`; their uncertainty is about comment/frequency/sample-type meaning, not discharge occurrence.

I'll read the task files and inspect the SQLite database to answer Q1–Q3.
I have enough data from the database. Writing `ANSWERS.md`.
`ANSWERS.md` is complete. Summary:

**Q1 — Determinacy:** 342 of 824 FY2025 measurement/limit pairs are determinate for Purpose A numeric exceedance (`numeric_comparison_candidate`). The remaining 510 holes in `_hole` block determination across purposes A/B/C — chiefly `nodi_code_semantics` (186), `monitoring_frequency_code` / `limit_sample_type_code` (105 each), `permit_limit_comment_text` (52), `aggregated_reporting_requirement` (40), `discharge_occurrence_in_period` (17), `pass_fail_reporting_semantics` (4), and `permit_document_text_not_available` (1).

**Q2 — Numeric separation:** 342 rows are mechanically computable via `numeric_comparison_candidate`. The other 482 cannot get an exceedance determination: 186 lack a reported numeric value (`no_numeric_result_case`), 288 have a reported value but no numeric limit (`has_limit_value_nmbr=0`), and 8 use pass/fail reporting semantics.

**Q3 — Semantic sharpening:** The World does model discharge-conditioned monitoring — 17 `monitoring_requirement_fy2025` rows on NM0028762 have `monitoring_condition = 'discharge_occurrence'` established from "WHEN DISCHARGING." comments, with uncertainty only about `discharge_occurrence_in_period`. The other 88 monitoring requirements have empty `monitoring_condition`; their uncertainty is about comment/frequency/sample-type meaning, not discharge occurrence.