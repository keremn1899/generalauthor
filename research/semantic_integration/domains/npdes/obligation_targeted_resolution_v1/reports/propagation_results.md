# Propagation results

## MEASURED

### T1 when_discharging

count changes: `{}`
holes groups {'baseline': 8, 'proposed': 8} instances {'baseline': 535, 'proposed': 518}
requirements added/removed: ['discharge_occurrence_in_period', 'monitoring_condition_from_comment'] / ['conditional_discharge_dependent_monitoring']

### T1 pass_fail

count changes: `{"binary_pass_fail_limit": {"baseline": null, "proposed": 0}, "binary_pass_fail_measurement": {"baseline": null, "proposed": 0}}`
holes groups {'baseline': 8, 'proposed': 9} instances {'baseline': 535, 'proposed': 525}
requirements added/removed: ['binary_pass_fail_limits_materializable', 'binary_pass_fail_measurement_unit', 'binary_pass_fail_measurements_materializable', 'binary_pass_fail_reporting_regime', 'binary_pass_fail_reporting_unit'] / ['pass_fail_reporting_semantics']

### T1 document_authority

count changes: `{"permit_document_authority": {"baseline": null, "proposed": 12}}`
holes groups {'baseline': 8, 'proposed': 9} instances {'baseline': 535, 'proposed': 536}
requirements added/removed: ['document_authority_role', 'document_conflict_precedence', 'permit_document_authority_unestablished', 'permit_narrative_conditions_not_structured'] / ['permit_document_text_not_available']

### T2 when_discharging

count changes: `{}`
holes groups {'baseline': 8, 'proposed': 7} instances {'baseline': 535, 'proposed': 501}
requirements added/removed: ['monitoring_applicability_condition'] / ['conditional_discharge_dependent_monitoring']

### T2 geometric_mean

count changes: `{}`
holes groups {'baseline': 8, 'proposed': 8} instances {'baseline': 535, 'proposed': 511}
requirements added/removed: [] / []

### T2 pass_fail

count changes: `{"dmr_measurement": {"baseline": 824, "proposed": null}, "fy2025_measurement": {"baseline": 824, "proposed": null}, "measurement_limit_pair": {"baseline": 824, "proposed": null}, "monitoring_requirement_fy2025": {"baseline": 105, "proposed": null}, "no_numeric_result_case": {"baseline": 186, "proposed": null}, "numeric_comparison_candidate": {"baseline": 342, "proposed": null}, "permit_document": {"baseline": 12, "proposed": null}, "permit_limit": {"baseline": 105, "proposed": null}}`
holes groups {'baseline': 8, 'proposed': None} instances {'baseline': 535, 'proposed': None}
requirements added/removed: [] / ['aggregated_reporting_requirement', 'conditional_discharge_dependent_monitoring', 'fy2025_measurements_materializable', 'limit_comparison_operator', 'limit_sample_type_code', 'limit_set_designator_for_schedule', 'limit_type_code_for_enforceability', 'limit_value_for_comparison', 'measurement_limit_pairs_materializable', 'monitoring_frequency_code', 'monitoring_requirements_materializable', 'no_numeric_result_cases_materializable', 'nodi_code_semantics', 'numeric_comparison_candidates_materializable', 'optional_monitoring_flag_for_limit_applicability', 'optional_monitoring_flag_for_missing_evidence', 'optional_monitoring_flag_for_obligation', 'pass_fail_reporting_semantics', 'permit_document_text_not_available', 'permit_limit_comment_text', 'reported_value_for_comparison', 'reported_value_qualifier', 'statistical_base_for_limit_comparison', 'unique_applicable_limit_per_measurement']

### T2 document_authority

count changes: `{}`
holes groups {'baseline': 8, 'proposed': 8} instances {'baseline': 535, 'proposed': 540}
requirements added/removed: ['document_authority_role_unresolved'] / ['permit_document_text_not_available']

### T3 when_discharging

count changes: `{}`
holes groups {'baseline': 8, 'proposed': 7} instances {'baseline': 535, 'proposed': 501}
requirements added/removed: ['monitoring_condition_from_comment'] / ['conditional_discharge_dependent_monitoring']

### T3 geometric_mean

count changes: `{"numeric_comparison_candidate": {"baseline": 342, "proposed": 318}}`
holes groups {'baseline': 8, 'proposed': 7} instances {'baseline': 535, 'proposed': 495}
requirements added/removed: [] / ['aggregated_reporting_requirement']

### T3 pass_fail

count changes: `{"pass_fail_outcome_reporting": {"baseline": null, "proposed": 8}}`
holes groups {'baseline': 8, 'proposed': 8} instances {'baseline': 535, 'proposed': 527}
requirements added/removed: ['wet_pass_fail_outcome_code'] / []

### T3 document_authority

count changes: `{}`
holes groups {'baseline': 8, 'proposed': 9} instances {'baseline': 535, 'proposed': 541}
requirements added/removed: ['document_authority_role'] / []

## OBSERVED

Intended: one reusable mapping changes all matching occurrences. Leakage: NODI 9 must not close NODI C; WHEN DISCHARGING must not close geometric-mean comments.

## HYPOTHESIS

Deterministic application beats per-row model judgments.
