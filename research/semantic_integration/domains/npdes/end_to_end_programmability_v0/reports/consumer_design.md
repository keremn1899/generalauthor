# Consumer design

## MEASURED

SQL `consumers/sql/monitoring_analysis.sql` joins `measurement_limit_pair`, `dmr_measurement`, `numeric_comparison_candidate`, `no_numeric_result_case`, and `_hole`.

Python discovers optional `monitoring_condition` and `pass_fail_outcome_reporting` via sqlite_master. It does not parse comments or map NODI legends.

## OBSERVED

The same bytes ran on A, B, and C. Schema expansion is consumed only when present.

## HYPOTHESIS

Ordinary SQL/Python against constructor-authored relation names is enough for v0; semantic ABI is out of scope.
