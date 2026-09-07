# Manual Inspection

Experiment root:
`research/semantic_integration/domains/npdes/end_to_end_programmability_v0/`

Open first:
`research/semantic_integration/domains/npdes/end_to_end_programmability_v0/manual_inspection/index.html`

## Paths

- Baseline output: `outputs/state_a/`
- WHEN DISCHARGING enriched output: `outputs/state_b/`
- pass/fail enriched output: `outputs/state_c/`
- Row diffs: `diffs/a_to_b_rows.csv`, `diffs/b_to_c_rows.csv`
- Trace samples: `manual_inspection/traces/`
- SQL consumer: `consumers/sql/monitoring_analysis.sql`
- Python consumer: `consumers/python/monitoring_analysis.py`
- Fresh-agent transcripts: `fresh_agent/state_a/ANSWERS.md`, `fresh_agent/state_c/ANSWERS.md`
- Compact headers: `states/state_a/compact_header.md`, `states/state_b/compact_header.md`, `states/state_c/compact_header.md`
- Accepted World sqlite: `states/state_a/accepted/world.sqlite`, `states/state_b/accepted/world.sqlite`, `states/state_c/accepted/world.sqlite`
- Isolated source-free copies: `isolated_consumer/state_a/`, `isolated_consumer/state_b/`, `isolated_consumer/state_c/`
- Failure-path evidence: `failure_path/result.json`
- Final report: `reports/end_to_end_programmability_v0.md`

## SQLite

```bash
sqlite3 "research/semantic_integration/domains/npdes/end_to_end_programmability_v0/states/state_c/accepted/world.sqlite"
```

```sql
.tables
.schema measurement_limit_pair
.schema monitoring_requirement_fy2025
.schema pass_fail_outcome_reporting
.schema _hole
SELECT name, mode, derived FROM _relation_meta ORDER BY name;
SELECT requirement, COUNT(*) FROM _hole GROUP BY requirement ORDER BY 2 DESC;
SELECT monitoring_condition, COUNT(*) FROM monitoring_requirement_fy2025 GROUP BY 1;
SELECT nodi_code, COUNT(*) FROM no_numeric_result_case GROUP BY 1;
SELECT dmr_value_nmbr, COUNT(*) FROM pass_fail_outcome_reporting GROUP BY 1;
```

State C tables: _hole, _referent, _relation_meta, _requirement, dmr_measurement, fy2025_measurement, measurement_limit_pair, monitoring_requirement_fy2025, no_numeric_result_case, numeric_comparison_candidate, pass_fail_outcome_reporting, permit_document, permit_limit

Consumer hashes (must match frozen): see `frozen/consumer_hashes.json`.
