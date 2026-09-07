# Trial results

Labels: **MEASURED** unless marked OBSERVED or HYPOTHESIS.

Model: Composer 2.5. Successful clean runs: 5/5.

| Trial | ok | iters | groups | instances | E1 | E2 | TDS | WHEN DISCHARGING | authority | first failure |
|---|---|---|---|---|---|---|---|---|---|---|
| T1 | yes | 1 | 14 | 3414 | 1.00 | 7/7 | TRIGGER | yes | yes | semantic modeling |
| T2 | yes | 1 | 16 | 1891 | 1.00 | 7/7 | TRIGGER | yes | yes | semantic modeling |
| T3 | yes | 1 | 31 | 6116 | 1.00 | 7/7 | TRIGGER | yes | yes | semantic modeling |
| T4 | yes | 1 | 11 | 2904 | 1.00 | 7/7 | TRIGGER | yes | yes | semantic modeling |
| T5 | yes | 1 | 8 | 535 | 1.00 | 7/7 | TRIGGER | yes | yes | semantic modeling |

## Programs

### T1

- construction.py lines: 695
- requirements: fy2025_measurements_materializable, monitoring_requirements_materializable, no_result_cases_materializable, comparison_candidates_materializable, non_numeric_limit_candidates_materializable, unique_schedule_match_per_measurement, unique_catalog_variant_per_limit_value, comparison_limit_value_numeric, comparison_reported_value_numeric, comparison_limit_qualifier, comparison_reported_qualifier, non_numeric_limit_classification, non_numeric_limit_optional_flag, requirement_comment_semantics, optional_monitoring_flag_semantics, limit_freq_semantics, season_month_flag_semantics, nodi_code_semantics, no_result_optional_monitoring_flag, discharge_condition_not_in_structured_evidence, discharge_condition_not_in_structured_evidence, discharge_condition_not_in_structured_evidence, discharge_condition_not_in_structured_evidence, discharge_condition_not_in_structured_evidence
- row counts: `{"measurement_context": 824, "measurement_result": 824, "measurement_limit_snapshot": 824, "monitoring_requirement_spec": 105, "requirement_season_month": 1260, "document_catalog": 12, "limit_catalog_variant": 105, "measurement_in_fy2025": 824, "limit_active_on_measurement_date": 824, "measurement_schedule_match": 824, "numeric_comparison_candidate": 342, "measurement_no_result": 186, "non_numeric_limit_candidate": 380}`
- hardcode flags: ['if\\s+.*when discharging']
- files read (basenames): ['PASS_TASK.md', 'PRINCIPLES.md', 'README.md', 'WORLD_API.md', 'dmr_measurements.csv', 'document_inventory.json', 'permit_limits.csv', 'source.py', 'visible_a.md', 'visible_b.md', 'visible_c.md', 'world_api.py']

### T2

- construction.py lines: 1015
- requirements: fy2025_reported_measurements, dmr_permit_links, numeric_comparison_pairs, unique_limit_value_per_numeric_measurement, interpret_limit_type_code, interpret_limit_value_qualifier, interpret_optional_monitoring_for_limits, interpret_measurement_qualifier, interpret_nodi_for_limit_applicability, numeric_limit_for_comparison, numeric_measurement_for_comparison, reported_value_without_numeric_limit, reported_value_without_numeric_limit, reported_value_without_numeric_limit, reported_value_without_numeric_limit, reported_value_without_numeric_limit, reported_value_without_numeric_limit, reported_value_without_numeric_limit, reported_value_without_numeric_limit, reported_value_without_numeric_limit, reported_value_without_numeric_limit, reported_value_without_numeric_limit, reported_value_without_numeric_limit, reported_value_without_numeric_limit
- row counts: `{"facility_permit": 3, "discharge_point_identity": 4, "parameter_identity": 33, "limit_identity": 44, "limit_value_identity": 90, "limit_effective_interval": 44, "limit_value_magnitude": 90, "limit_value_qualifier_code": 90, "limit_type_code": 44, "optional_monitoring_flag": 44, "monitoring_schedule": 51, "seasonal_month_flag": 84, "permit_limit_comment": 4, "dmr_measurement": 824, "measurement_value": 824, "measurement_qualifier_code": 824, "measurement_nodi_code": 824, "document_inventory": 12, "fy2025_dmr_measurement": 824, "dmr_permit_link": 824, "permit_monitoring_requirement": 51, "requirement_fy2025_dmr_evidence": 51, "numeric_comparison_pair": 342, "no_numeric_result_case": 186, "monitoring_obligation_subject": 51}`
- hardcode flags: none
- files read (basenames): ['PASS_TASK.md', 'PRINCIPLES.md', 'README.md', 'WORLD_API.md', 'dmr_measurements.csv', 'document_inventory.json', 'permit_limits.csv', 'source.py', 'visible_a.md', 'visible_b.md', 'visible_c.md', 'world_api.py']

### T3

- construction.py lines: 804
- requirements: fy25_measurements_materializable, fy25_limit_evaluations_materializable, unique_permit_limit_per_measurement, unique_source_limit_value_per_measurement, limit_qualifier_for_comparison, dmr_qualifier_for_comparison, limit_unit_for_comparison, value_type_for_limit_selection, optional_flag_for_limit_applicability, nodi_affects_limit_applicability, limit_value_numeric_for_comparison, dmr_value_numeric_for_comparison, permit_comment_affects_limit_applicability, pass_fail_limit_comparison_semantics, permit_comment_affects_limit_applicability, pass_fail_limit_comparison_semantics, permit_comment_affects_limit_applicability, pass_fail_limit_comparison_semantics, permit_comment_affects_limit_applicability, pass_fail_limit_comparison_semantics, permit_comment_affects_limit_applicability, pass_fail_limit_comparison_semantics, permit_comment_affects_limit_applicability, pass_fail_limit_comparison_semantics
- row counts: `{"document_catalog": 12, "measurement_record": 824, "permit_limit_record": 105, "fy2025_measurement": 824, "measurement_permit_link": 824, "fy25_limit_evaluation": 824, "fy25_monitoring_obligation": 105, "fy25_no_result_case": 186, "numeric_comparison_candidate": 342}`
- hardcode flags: none
- files read (basenames): ['PASS_TASK.md', 'PRINCIPLES.md', 'README.md', 'WORLD_API.md', 'construction.py', 'dmr_measurements.csv', 'document_inventory.json', 'permit_limits.csv', 'source.py', 'visible_a.md', 'visible_b.md', 'visible_c.md', 'world_api.py']

### T4

- construction.py lines: 660
- requirements: unique_applicable_limit_per_measurement, applicable_limit_candidates_materializable, limit_value_qualifier_for_comparison, dmr_value_qualifier_for_comparison, limit_value_numeric_for_comparison, dmr_value_numeric_for_comparison, limit_value_nmbr_comparability, limit_type_code_comparability, limit_applicability_without_numeric_limit, limit_applicability_without_numeric_limit, limit_applicability_without_numeric_limit, limit_applicability_without_numeric_limit, limit_applicability_without_numeric_limit, limit_applicability_without_numeric_limit, limit_applicability_without_numeric_limit, limit_applicability_without_numeric_limit, limit_applicability_without_numeric_limit, limit_applicability_without_numeric_limit, limit_applicability_without_numeric_limit, limit_applicability_without_numeric_limit, limit_applicability_without_numeric_limit, limit_applicability_without_numeric_limit, limit_applicability_without_numeric_limit, limit_applicability_without_numeric_limit
- row counts: `{"permit_feature": 4, "limit_value_specification": 105, "limit_effective_interval": 44, "measurement_reported": 824, "document_inventory_entry": 12, "fy2025_measurement": 824, "measurement_permit_match": 824, "applicable_limit_candidate": 824, "numeric_limit_comparison_candidate": 342, "monitoring_obligation_candidate": 105, "missing_result_case": 186}`
- hardcode flags: none
- files read (basenames): ['PASS_TASK.md', 'PRINCIPLES.md', 'README.md', 'WORLD_API.md', 'a9aaba91-56b5-4231-84de-bfcdf8b8ba40.txt', 'construction.py', 'dmr_measurements.csv', 'document_inventory.json', 'permit_limits.csv', 'source.py', 'visible_a.md', 'visible_b.md', 'visible_c.md', 'world_api.py']

### T5

- construction.py lines: 652
- requirements: fy2025_measurements_materializable, measurement_limit_pairs_materializable, unique_applicable_limit_per_measurement, numeric_comparison_candidates_materializable, limit_value_for_comparison, reported_value_for_comparison, limit_comparison_operator, reported_value_qualifier, optional_monitoring_flag_for_limit_applicability, limit_type_code_for_enforceability, statistical_base_for_limit_comparison, monitoring_requirements_materializable, monitoring_frequency_code, limit_sample_type_code, optional_monitoring_flag_for_obligation, permit_limit_comment_text, limit_set_designator_for_schedule, no_numeric_result_cases_materializable, nodi_code_semantics, optional_monitoring_flag_for_missing_evidence, aggregated_reporting_requirement, aggregated_reporting_requirement, aggregated_reporting_requirement, aggregated_reporting_requirement
- row counts: `{"dmr_measurement": 824, "permit_limit": 105, "permit_document": 12, "fy2025_measurement": 824, "measurement_limit_pair": 824, "numeric_comparison_candidate": 342, "no_numeric_result_case": 186, "monitoring_requirement_fy2025": 105}`
- hardcode flags: ['when\\s+discharging.{0,80}(conditional|required|not required)', 'if\\s+.*when discharging']
- files read (basenames): ['PASS_TASK.md', 'PRINCIPLES.md', 'README.md', 'WORLD_API.md', 'source.py', 'visible_a.md', 'visible_b.md', 'visible_c.md', 'world_api.py']

