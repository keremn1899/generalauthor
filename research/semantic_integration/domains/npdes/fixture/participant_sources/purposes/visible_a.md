# Purpose A — applicable discharge limits

For Federal FY2025 (2024-10-01 through 2025-09-30 inclusive), determine which enforceable numeric discharge limit applies to each relevant facility, discharge point, parameter, and monitoring period for which we have reported measurements. Determine whether each available reported measurement exceeds the applicable limit. Distinguish enforceable numeric limits from report-only monitoring or monitoring for which no numeric compliance comparison is applicable. Preserve uncertainty where applicability cannot be established from the available evidence.

Write purpose_ir/a/output.json as a JSON object with:
- purpose: applicable_discharge_limits
- rows: list of objects describing the evaluated measurement/limit pairs
- unresolved: list of cases whose applicability cannot be established
