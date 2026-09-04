# Semantic inventory

Normalized by meaning. Original Python/table names are preserved alongside evaluator labels. Normalized labels were not fed back into programs.

## MEASURED schema counts

| trial | referent kinds | relations | unique require names | factorized req schemas | spine requirement rows | hole groups | hole instances |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T1 | 4 | 13 | 22 | 14 | 48 | 14 | 3414 |
| T2 | 11 | 25 | 28 | 11 | 547 | 16 | 1891 |
| T3 | 12 | 9 | 30 | 16 | 1273 | 31 | 6116 |
| T4 | 8 | 11 | 19 | 13 | 565 | 11 | 2904 |
| T5 | 10 | 8 | 24 | 16 | 90 | 8 | 535 |

## T1

### Referents (original → normalized)

- `document` → **Document**
- `limit_value` → **LimitValue**
- `measurement` → **Measurement**
- `monitoring_requirement` → **MonitoringRequirement**

### Relations

| original | normalized | derived | mode | n_rows |
| --- | --- | --- | --- | --- |
| measurement_context | MeasurementBase | False | WORLD | 824 |
| measurement_result | MeasurementBase | False | WORLD | 824 |
| measurement_limit_snapshot | CandidateCorrespondence | False | WORLD | 824 |
| monitoring_requirement_spec | MonitoringObligation | False | WORLD | 105 |
| requirement_season_month | SeasonalMonth | False | WORLD | 1260 |
| document_catalog | DocumentInventory | False | WORLD | 12 |
| limit_catalog_variant | LimitBase | False | WORLD | 105 |
| measurement_in_fy2025 | Fy2025Scope | True | WORLD | 824 |
| limit_active_on_measurement_date | CandidateCorrespondence | True | WORLD | 824 |
| measurement_schedule_match | CandidateCorrespondence | True | WORLD | 824 |
| numeric_comparison_candidate | NumericComparison | True | PURPOSE | 342 |
| measurement_no_result | MissingEvidence | True | PURPOSE | 186 |
| non_numeric_limit_candidate | NumericComparison | True | PURPOSE | 380 |

### Requirement call sites (original → normalized)

| kind | original | normalized | field |
| --- | --- | --- | --- |
| require_materializable | fy2025_measurements_materializable | materializable_fy2025_measurements |  |
| require_materializable | monitoring_requirements_materializable | materializable_monitoring |  |
| require_materializable | no_result_cases_materializable | materializable_no_result |  |
| require_materializable | comparison_candidates_materializable | materializable_candidates |  |
| require_materializable | non_numeric_limit_candidates_materializable | materializable_candidates |  |
| require_unique | unique_schedule_match_per_measurement | unique_applicable_limit |  |
| require_unique | unique_catalog_variant_per_limit_value | unique_applicable_limit |  |
| require_numeric | comparison_limit_value_numeric | numeric_limit | limit_value_nmbr |
| require_numeric | comparison_reported_value_numeric | numeric_measurement | dmr_value_nmbr |
| require_interpreted | comparison_limit_qualifier | interpret_qualifier | limit_value_qualifier |
| require_interpreted | comparison_reported_qualifier | interpret_qualifier | dmr_value_qualifier |
| require_interpreted | non_numeric_limit_classification | numeric_limit | limit_type_code |
| require_interpreted | non_numeric_limit_optional_flag | interpret_optional_monitoring | optional_monitoring_flag |
| require_interpreted | requirement_comment_semantics | interpret_comment | dmr_comment_text |
| require_interpreted | optional_monitoring_flag_semantics | interpret_optional_monitoring | optional_monitoring_flag |
| require_interpreted | limit_freq_semantics | interpret_frequency | limit_freq_of_analysis_code |
| require_interpreted | season_month_flag_semantics | interpret_seasonal_month | active_flag |
| require_interpreted | nodi_code_semantics | interpret_nodi | nodi_code |
| require_interpreted | no_result_optional_monitoring_flag | interpret_optional_monitoring | optional_monitoring_flag |
| unresolved | discharge_condition_not_in_structured_evidence | interpret_comment |  |
| unresolved | permit_year_condition_requires_document_text | document_text_unavailable |  |
| unresolved | numeric_limit_without_reported_value_or_nodi | interpret_nodi |  |

Grain: schemas=22, candidate obligations=30, occurrences=3414.

## T2

### Referents (original → normalized)

- `discharge_point` → **Outfall**
- `dmr_report` → **Measurement**
- `document` → **Document**
- `facility` → **Facility**
- `limit` → **Limit**
- `limit_set_schedule` → **LimitSchedule**
- `limit_value` → **LimitValue**
- `monitoring_event` → **MonitoringEvent**
- `monitoring_requirement` → **MonitoringRequirement**
- `parameter` → **Parameter**
- `permit` → **Permit**

### Relations

| original | normalized | derived | mode | n_rows |
| --- | --- | --- | --- | --- |
| facility_permit | OtherRelation | False | WORLD | 3 |
| discharge_point_identity | OtherRelation | False | WORLD | 4 |
| parameter_identity | OtherRelation | False | WORLD | 33 |
| limit_identity | LimitBase | False | WORLD | 44 |
| limit_value_identity | LimitBase | False | WORLD | 90 |
| limit_effective_interval | EffectiveInterval | False | WORLD | 44 |
| limit_value_magnitude | LimitBase | False | WORLD | 90 |
| limit_value_qualifier_code | LimitBase | False | WORLD | 90 |
| limit_type_code | LimitBase | False | WORLD | 44 |
| optional_monitoring_flag | CodePayload | False | WORLD | 44 |
| monitoring_schedule | OtherRelation | False | WORLD | 51 |
| seasonal_month_flag | SeasonalMonth | False | WORLD | 84 |
| permit_limit_comment | LimitBase | False | WORLD | 4 |
| dmr_measurement | MeasurementBase | False | WORLD | 824 |
| measurement_value | MeasurementBase | False | WORLD | 824 |
| measurement_qualifier_code | MeasurementBase | False | WORLD | 824 |
| measurement_nodi_code | MeasurementBase | False | WORLD | 824 |
| document_inventory | DocumentInventory | False | WORLD | 12 |
| fy2025_dmr_measurement | Fy2025Scope | True | WORLD | 824 |
| dmr_permit_link | CandidateCorrespondence | True | WORLD | 824 |
| permit_monitoring_requirement | MonitoringObligation | True | WORLD | 51 |
| requirement_fy2025_dmr_evidence | Fy2025Scope | True | WORLD | 51 |
| numeric_comparison_pair | NumericComparison | False | PURPOSE | 342 |
| no_numeric_result_case | MissingEvidence | False | PURPOSE | 186 |
| monitoring_obligation_subject | MonitoringObligation | False | PURPOSE | 51 |

### Requirement call sites (original → normalized)

| kind | original | normalized | field |
| --- | --- | --- | --- |
| require_materializable | fy2025_reported_measurements | other_requirement |  |
| require_materializable | dmr_permit_links | other_requirement |  |
| require_materializable | numeric_comparison_pairs | other_requirement |  |
| require_unique | unique_limit_value_per_numeric_measurement | unique_applicable_limit |  |
| require_interpreted | interpret_limit_type_code | interpret_limit_type | limit_type_code |
| require_interpreted | interpret_limit_value_qualifier | interpret_qualifier | qualifier_code |
| require_interpreted | interpret_optional_monitoring_for_limits | interpret_optional_monitoring | optional_monitoring_flag |
| require_interpreted | interpret_measurement_qualifier | interpret_qualifier | dmr_value_qualifier_code |
| require_interpreted | interpret_nodi_for_limit_applicability | interpret_nodi | nodi_code |
| require_numeric | numeric_limit_for_comparison | numeric_limit | limit_value_nmbr |
| require_numeric | numeric_measurement_for_comparison | numeric_measurement | dmr_value_nmbr |
| require_materializable | permit_monitoring_requirements | other_requirement |  |
| require_materializable | monitoring_obligation_subjects | other_requirement |  |
| require_interpreted | interpret_monitoring_frequency_code | interpret_frequency | limit_freq_of_analysis_code |
| require_interpreted | interpret_seasonal_month_flag | interpret_seasonal_month | active_flag |
| require_interpreted | interpret_permit_dmr_comment | interpret_comment | dmr_comment_text |
| require_interpreted | interpret_optional_monitoring_for_obligations | interpret_optional_monitoring | optional_monitoring_flag |
| require_materializable | no_numeric_result_cases | other_requirement |  |
| require_interpreted | interpret_nodi_semantics | interpret_nodi | nodi_code |
| require_interpreted | interpret_optional_monitoring_for_no_result | interpret_optional_monitoring | optional_monitoring_flag |
| unresolved | reported_value_without_numeric_limit | numeric_limit |  |
| unresolved | numeric_limit_without_reported_value_or_nodi | interpret_nodi |  |
| unresolved | numeric_limit_without_qualifier | interpret_qualifier |  |
| unresolved | conditional_permit_comment_present | interpret_comment |  |
| unresolved | nodi_without_interpretation | interpret_nodi |  |
| unresolved | permit_requirement_without_fy2025_dmr | other_requirement |  |
| unresolved | multiple_permit_schedules_for_limit | other_requirement |  |
| unresolved | missing_measurement_for_numeric_limit | numeric_limit |  |

Grain: schemas=28, candidate obligations=33, occurrences=1891.

## T3

### Referents (original → normalized)

- `discharge_point` → **Outfall**
- `limit` → **Limit**
- `limit_schedule` → **LimitSchedule**
- `limit_set` → **LimitSet**
- `limit_value` → **LimitValue**
- `measurement` → **Measurement**
- `monitoring_event` → **MonitoringEvent**
- `monitoring_period` → **MonitoringPeriod**
- `parameter` → **Parameter**
- `permit` → **Permit**
- `permit_limit_row` → **LimitRow**
- `source_document` → **Document**

### Relations

| original | normalized | derived | mode | n_rows |
| --- | --- | --- | --- | --- |
| document_catalog | DocumentInventory | False | WORLD | 12 |
| measurement_record | MeasurementBase | False | WORLD | 824 |
| permit_limit_record | LimitBase | False | WORLD | 105 |
| fy2025_measurement | Fy2025Scope | True | WORLD | 824 |
| measurement_permit_link | CandidateCorrespondence | True | WORLD | 824 |
| fy25_limit_evaluation | Fy2025Scope | False | PURPOSE | 824 |
| fy25_monitoring_obligation | Fy2025Scope | False | PURPOSE | 105 |
| fy25_no_result_case | Fy2025Scope | False | PURPOSE | 186 |
| numeric_comparison_candidate | NumericComparison | True | PURPOSE | 342 |

### Requirement call sites (original → normalized)

| kind | original | normalized | field |
| --- | --- | --- | --- |
| require_materializable | fy25_measurements_materializable | materializable_fy2025_measurements |  |
| require_materializable | fy25_limit_evaluations_materializable | materializable_fy2025_measurements |  |
| require_unique | unique_permit_limit_per_measurement | unique_applicable_limit |  |
| require_unique | unique_source_limit_value_per_measurement | unique_applicable_limit |  |
| require_interpreted | limit_qualifier_for_comparison | interpret_qualifier | limit_value_qualifier_code |
| require_interpreted | dmr_qualifier_for_comparison | interpret_qualifier | dmr_value_qualifier_code |
| require_interpreted | limit_unit_for_comparison | interpret_unit | limit_unit_code |
| require_interpreted | value_type_for_limit_selection | interpret_value_type | value_type_code |
| require_interpreted | optional_flag_for_limit_applicability | interpret_optional_monitoring | optional_monitoring_flag |
| require_interpreted | nodi_affects_limit_applicability | interpret_nodi | nodi_code |
| require_numeric | limit_value_numeric_for_comparison | numeric_limit | limit_value_nmbr |
| require_numeric | dmr_value_numeric_for_comparison | numeric_measurement | dmr_value_nmbr |
| require_materializable | document_catalog_materializable | materializable_documents |  |
| unresolved | permit_document_text_not_materialized | document_text_unavailable |  |
| require_materializable | fy25_monitoring_obligations_materializable | materializable_fy2025_measurements |  |
| require_interpreted | permit_comment_for_monitoring_applicability | interpret_comment | dmr_comment_text |
| require_interpreted | optional_flag_for_monitoring_applicability | interpret_optional_monitoring | optional_monitoring_flag |
| require_interpreted | frequency_code_for_monitoring_applicability | interpret_frequency | limit_freq_of_analysis_code |
| require_interpreted | sample_type_for_monitoring_applicability | interpret_sample_type | limit_sample_type_code |
| require_materializable | fy25_no_result_cases_materializable | materializable_fy2025_measurements |  |
| require_interpreted | nodi_code_semantics | interpret_nodi | nodi_code |
| require_interpreted | optional_flag_for_no_result_semantics | interpret_optional_monitoring | optional_monitoring_flag |
| require_interpreted | seasonal_{month}_for_monitoring_applicability | interpret_seasonal_month |  |
| unresolved | permit_comment_affects_limit_applicability | interpret_comment |  |
| unresolved | report_only_limit_with_numeric_measurement | numeric_limit |  |
| unresolved | pass_fail_limit_comparison_semantics | pass_fail_semantics |  |
| unresolved | conditional_monitoring_requirement | interpret_comment |  |
| unresolved | nodi_establishes_no_result_state | interpret_nodi |  |
| unresolved | permit_comment_affects_no_result_semantics | interpret_comment |  |
| unresolved | missing_result_with_numeric_limit | numeric_limit |  |

Grain: schemas=30, candidate obligations=63, occurrences=6116.

## T4

### Referents (original → normalized)

- `discharge_point` → **Outfall**
- `dmr_measurement` → **Measurement**
- `document` → **Document**
- `limit` → **Limit**
- `limit_value` → **LimitValue**
- `monitoring_period` → **MonitoringPeriod**
- `parameter` → **Parameter**
- `permit` → **Permit**

### Relations

| original | normalized | derived | mode | n_rows |
| --- | --- | --- | --- | --- |
| permit_feature | OtherRelation | False | WORLD | 4 |
| limit_value_specification | LimitBase | False | WORLD | 105 |
| limit_effective_interval | EffectiveInterval | False | WORLD | 44 |
| measurement_reported | MeasurementBase | False | WORLD | 824 |
| document_inventory_entry | DocumentInventory | False | WORLD | 12 |
| fy2025_measurement | Fy2025Scope | True | WORLD | 824 |
| measurement_permit_match | CandidateCorrespondence | True | WORLD | 824 |
| applicable_limit_candidate | CandidateCorrespondence | False | PURPOSE | 824 |
| numeric_limit_comparison_candidate | NumericComparison | False | PURPOSE | 342 |
| monitoring_obligation_candidate | CandidateCorrespondence | False | PURPOSE | 105 |
| missing_result_case | MissingEvidence | False | PURPOSE | 186 |

### Requirement call sites (original → normalized)

| kind | original | normalized | field |
| --- | --- | --- | --- |
| require_unique | unique_applicable_limit_per_measurement | unique_applicable_limit |  |
| require_materializable | applicable_limit_candidates_materializable | materializable_candidates |  |
| require_interpreted | limit_value_qualifier_for_comparison | interpret_qualifier | limit_value_qualifier_code |
| require_interpreted | dmr_value_qualifier_for_comparison | interpret_qualifier | dmr_value_qualifier_code |
| require_numeric | limit_value_numeric_for_comparison | numeric_limit | limit_value_nmbr |
| require_numeric | dmr_value_numeric_for_comparison | numeric_measurement | dmr_value_nmbr |
| require_interpreted | limit_value_nmbr_comparability | report_only_gap | limit_value_nmbr |
| require_interpreted | limit_type_code_comparability | interpret_limit_type | limit_type_code |
| require_materializable | monitoring_obligation_candidates_materializable | materializable_candidates |  |
| require_interpreted | optional_monitoring_flag_obligation | interpret_optional_monitoring | optional_monitoring_flag |
| require_interpreted | dmr_comment_obligation | interpret_comment | dmr_comment_text |
| require_interpreted | limit_freq_obligation | interpret_frequency | limit_freq_of_analysis_code |
| require_materializable | missing_result_cases_materializable | materializable_no_result |  |
| require_interpreted | nodi_code_semantics | interpret_nodi | nodi_code |
| unresolved | measurement_permit_spec_unmatched | other_requirement |  |
| unresolved | limit_applicability_without_numeric_limit | numeric_limit |  |
| unresolved | conditional_monitoring_applicability | interpret_comment |  |
| unresolved | missing_result_without_nodi | interpret_nodi |  |
| unresolved | nodi_with_limit_but_no_measurement | interpret_nodi |  |

Grain: schemas=19, candidate obligations=25, occurrences=2904.

## T5

### Referents (original → normalized)

- `document` → **Document**
- `feature` → **Outfall**
- `limit` → **Limit**
- `limit_set` → **LimitSet**
- `limit_set_schedule` → **LimitSchedule**
- `limit_value` → **LimitValue**
- `measurement` → **Measurement**
- `parameter` → **Parameter**
- `permit` → **Permit**
- `permit_limit_row` → **LimitRow**

### Relations

| original | normalized | derived | mode | n_rows |
| --- | --- | --- | --- | --- |
| dmr_measurement | MeasurementBase | False | WORLD | 824 |
| permit_limit | LimitBase | False | WORLD | 105 |
| permit_document | DocumentInventory | False | WORLD | 12 |
| fy2025_measurement | Fy2025Scope | True | PURPOSE | 824 |
| measurement_limit_pair | CandidateCorrespondence | True | PURPOSE | 824 |
| numeric_comparison_candidate | NumericComparison | True | PURPOSE | 342 |
| no_numeric_result_case | MissingEvidence | True | PURPOSE | 186 |
| monitoring_requirement_fy2025 | Fy2025Scope | True | PURPOSE | 105 |

### Requirement call sites (original → normalized)

| kind | original | normalized | field |
| --- | --- | --- | --- |
| require_materializable | fy2025_measurements_materializable | materializable_fy2025_measurements |  |
| require_materializable | measurement_limit_pairs_materializable | materializable_fy2025_measurements |  |
| require_unique | unique_applicable_limit_per_measurement | unique_applicable_limit |  |
| require_materializable | numeric_comparison_candidates_materializable | materializable_candidates |  |
| require_numeric | limit_value_for_comparison | other_requirement | limit_value_standard_units |
| require_numeric | reported_value_for_comparison | other_requirement | dmr_value_standard_units |
| require_interpreted | limit_comparison_operator | other_requirement | limit_value_qualifier_code |
| require_interpreted | reported_value_qualifier | interpret_qualifier | dmr_value_qualifier_code |
| require_interpreted | optional_monitoring_flag_for_limit_applicability | interpret_optional_monitoring | optional_monitoring_flag |
| require_interpreted | limit_type_code_for_enforceability | interpret_limit_type | limit_type_code |
| require_interpreted | statistical_base_for_limit_comparison | interpret_statistical_base | statistical_base_type_code |
| require_materializable | monitoring_requirements_materializable | materializable_monitoring |  |
| require_interpreted | monitoring_frequency_code | interpret_frequency | limit_freq_of_analysis_code |
| require_interpreted | limit_sample_type_code | interpret_limit_type | limit_sample_type_code |
| require_interpreted | optional_monitoring_flag_for_obligation | interpret_optional_monitoring | optional_monitoring_flag |
| require_interpreted | permit_limit_comment_text | interpret_comment | dmr_comment_text |
| require_interpreted | limit_set_designator_for_schedule | other_requirement | limit_set_designator |
| require_materializable | no_numeric_result_cases_materializable | materializable_no_result |  |
| require_interpreted | nodi_code_semantics | interpret_nodi | nodi_code |
| require_interpreted | optional_monitoring_flag_for_missing_evidence | interpret_optional_monitoring | optional_monitoring_flag |
| unresolved | permit_document_text_not_available | document_text_unavailable |  |
| unresolved | conditional_discharge_dependent_monitoring | interpret_comment |  |
| unresolved | pass_fail_reporting_semantics | pass_fail_semantics |  |
| unresolved | aggregated_reporting_requirement | aggregated_reporting |  |

Grain: schemas=24, candidate obligations=23, occurrences=535.

## OBSERVED

Independently named relations that both express Measurement ↔ candidate applicable Limit are labeled `CandidateCorrespondence`. Document inventory relations are `DocumentInventory` whether named `document_catalog` or `permit_document`.

## HYPOTHESIS

The five programs share a small schema vocabulary. Apparent requirement-name diversity is mostly field-level `require_interpreted` plus per-row `unresolved` instantiation.
