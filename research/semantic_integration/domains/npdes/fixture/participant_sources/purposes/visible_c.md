# Purpose C — missing-evidence semantics

For Federal FY2025 monitoring expectations without an ordinary numeric reported result, determine what the available evidence establishes. Distinguish documented no-discharge periods, periods where conditional monitoring was not required, other documented no-data states, required monitoring that appears to lack adequate evidence, and cases that remain unresolved. Do not treat missing data by itself as evidence of compliance or violation.

Write purpose_ir/c/output.json as a JSON object with:
- purpose: missing_evidence_semantics
- rows: list of evaluated no-result / NODI / missing-evidence cases and the established state
- unresolved: list of cases that remain unresolved
