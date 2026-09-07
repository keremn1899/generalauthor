Reading the task files and exploring the database structure.

Writing ANSWERS.md from the query results.

`ANSWERS.md` is complete. Summary of findings from `accepted/world.sqlite`:

**Q1 — Determinacy:** 535 `_hole` rows block determination across three purposes. Main blockers: `nodi_code_semantics` (186 cases, codes `C`/`9` uninterpreted), 296 measurement pairs with reported values but no numeric limit, `pass_fail_reporting_semantics` (48 measurements), monitoring-code interpretation gaps on all 105 requirements, plus `aggregated_reporting_requirement` (40) and `conditional_discharge_dependent_monitoring` (17).

**Q2 — Numeric separation:** 342 measurements in `numeric_comparison_candidate` are mechanically computable; 482 are not (186 `no_numeric_result_case` + 296 with non-numeric limit types). The two sets are disjoint.

**Q3 — Discharge sharpening:** The World explicitly models discharge-conditioned monitoring via `conditional_discharge_dependent_monitoring` on 17 `monitoring_requirement_fy2025` rows (permit NM0028762, comment `WHEN DISCHARGING.`). Condition meaning is established; discharge occurrence is not. 140 related measurements exist, but uncertainty is registered at the requirement level, not on individual measurements.

Reading the task files and exploring the database structure.
Writing ANSWERS.md from the query results.
`ANSWERS.md` is complete. Summary of findings from `accepted/world.sqlite`:

**Q1 — Determinacy:** 535 `_hole` rows block determination across three purposes. Main blockers: `nodi_code_semantics` (186 cases, codes `C`/`9` uninterpreted), 296 measurement pairs with reported values but no numeric limit, `pass_fail_reporting_semantics` (48 measurements), monitoring-code interpretation gaps on all 105 requirements, plus `aggregated_reporting_requirement` (40) and `conditional_discharge_dependent_monitoring` (17).

**Q2 — Numeric separation:** 342 measurements in `numeric_comparison_candidate` are mechanically computable; 482 are not (186 `no_numeric_result_case` + 296 with non-numeric limit types). The two sets are disjoint.

**Q3 — Discharge sharpening:** The World explicitly models discharge-conditioned monitoring via `conditional_discharge_dependent_monitoring` on 17 `monitoring_requirement_fy2025` rows (permit NM0028762, comment `WHEN DISCHARGING.`). Condition meaning is established; discharge occurrence is not. 140 related measurements exist, but uncertainty is registered at the requirement level, not on individual measurements.