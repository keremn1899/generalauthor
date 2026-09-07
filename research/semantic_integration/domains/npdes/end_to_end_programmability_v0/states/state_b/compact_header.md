# Semantic header

## PURPOSE

Declared purposes for this accepted World (Federal FY2025 NPDES monitoring/compliance):

### A — applicable discharge limits

# Purpose A — applicable discharge limits

For Federal FY2025 (2024-10-01 through 2025-09-30 inclusive), determine which enforceable numeric discharge limit applies to each relevant facility, discharge point, parameter, and monitoring period for which we have reported measurements. Determine whether each available reported measurement exceeds the applicable limit. Distinguish enforceable numeric limits from report-only monitoring or monitoring for which no numeric compliance comparison is applicable. Preserve uncertainty where applicability cannot be established from the available evidence.

Write purpose_ir/a/output.json as a JSON object with:
- purpose: applicable_discharge_limits
- rows: list of objects describing the evaluated measurement/limit pairs
- unresolved: list of cases whose applicability cannot be established

### B — monitoring obligations

# Purpose B — monitoring obligations

For Federal FY2025, determine which monitoring requirements were actually applicable for the selected facilities, including requirements that depend on discharge occurrence, season, permit year, special studies, event conditions, or other permit conditions. For each evaluated requirement, determine whether the evidence establishes that monitoring was required, establishes that it was not required, or leaves applicability unresolved.

Write purpose_ir/b/output.json as a JSON object with:
- purpose: monitoring_obligations
- rows: list of evaluated monitoring requirements and their applicability
- unresolved: list of requirements whose applicability cannot be established

### C — missing-evidence semantics

# Purpose C — missing-evidence semantics

For Federal FY2025 monitoring expectations without an ordinary numeric reported result, determine what the available evidence establishes. Distinguish documented no-discharge periods, periods where conditional monitoring was not required, other documented no-data states, required monitoring that appears to lack adequate evidence, and cases that remain unresolved. Do not treat missing data by itself as evidence of compliance or violation.

Write purpose_ir/c/output.json as a JSON object with:
- purpose: missing_evidence_semantics
- rows: list of evaluated no-result / NODI / missing-evidence cases and the established state
- unresolved: list of cases that remain unresolved

## WORLD CONTRACT

No rows are included. Relation names are constructor-authored. Empty description means none was provided.

state: state_b
proposals_admitted_to_this_copy: obligation_v1/T1/when_discharging

### dmr_measurement
meaning: Reported DMR measurement rows with structural source fields.
roles: measurement:REFERENT, permit:REFERENT, feature:REFERENT, parameter:REFERENT, limit:REFERENT, limit_value:REFERENT, limit_set:REFERENT, limit_set_schedule:REFERENT, monitoring_period_end:TEXT, limit_begin_date:TEXT, limit_end_date:TEXT, dmr_value_nmbr:TEXT, dmr_value_standard_units:TEXT, dmr_value_qualifier_code:TEXT, limit_value_nmbr:TEXT, limit_value_standard_units:TEXT, limit_value_qualifier_code:TEXT, limit_type_code:TEXT, optional_monitoring_flag:TEXT, nodi_code:TEXT, limit_set_designator:TEXT, limit_value_type_code:TEXT, value_type_code:TEXT, statistical_base_type_code:TEXT, dmr_sample_type_code:TEXT, dmr_freq_of_analysis_code:TEXT, limit_freq_of_analysis_code:TEXT, limit_sample_type_code:TEXT, monitoring_location_code:TEXT, has_reported_value:BOOLEAN, has_limit_value_nmbr:BOOLEAN, period_in_limit_interval:BOOLEAN
scope: WORLD
mode: WORLD
derived: False

### fy2025_measurement
meaning: (none provided)
roles: measurement:REFERENT, monitoring_period_end:TEXT
scope: PURPOSE
mode: PURPOSE
derived: True

### measurement_limit_pair
meaning: (none provided)
roles: measurement:REFERENT, permit_limit_row:REFERENT, permit:REFERENT, feature:REFERENT, parameter:REFERENT, limit:REFERENT, limit_value:REFERENT, monitoring_period_end:TEXT, dmr_value_standard_units:TEXT, limit_value_standard_units:TEXT, limit_value_qualifier_code:TEXT, dmr_value_qualifier_code:TEXT, optional_monitoring_flag:TEXT, limit_type_code:TEXT, has_reported_value:BOOLEAN, has_limit_value_nmbr:BOOLEAN, nodi_code:TEXT, dmr_comment_text:TEXT, limit_freq_of_analysis_code:TEXT, statistical_base_type_code:TEXT
scope: PURPOSE
mode: PURPOSE
derived: True

### monitoring_requirement_fy2025
meaning: (none provided)
roles: permit_limit_row:REFERENT, permit:REFERENT, feature:REFERENT, parameter:REFERENT, limit:REFERENT, limit_value:REFERENT, optional_monitoring_flag:TEXT, limit_freq_of_analysis_code:TEXT, limit_sample_type_code:TEXT, dmr_comment_text:TEXT, monitoring_condition:TEXT, has_limit_value_nmbr:BOOLEAN, limit_set_designator:TEXT
scope: PURPOSE
mode: PURPOSE
derived: True

### no_numeric_result_case
meaning: (none provided)
roles: measurement:REFERENT, permit:REFERENT, feature:REFERENT, parameter:REFERENT, limit:REFERENT, limit_value:REFERENT, monitoring_period_end:TEXT, nodi_code:TEXT, optional_monitoring_flag:TEXT, limit_freq_of_analysis_code:TEXT, dmr_freq_of_analysis_code:TEXT, has_limit_value_nmbr:BOOLEAN
scope: PURPOSE
mode: PURPOSE
derived: True

### numeric_comparison_candidate
meaning: (none provided)
roles: measurement:REFERENT, permit_limit_row:REFERENT, dmr_value_standard_units:TEXT, limit_value_standard_units:TEXT, limit_value_qualifier_code:TEXT, dmr_value_qualifier_code:TEXT, statistical_base_type_code:TEXT
scope: PURPOSE
mode: PURPOSE
derived: True

### permit_document
meaning: Permit package document inventory entries.
roles: permit:REFERENT, document:REFERENT, document_kind:TEXT, filename:TEXT, bytes:INTEGER
scope: WORLD
mode: WORLD
derived: False

### permit_limit
meaning: Permit limit schedule rows with structural source fields.
roles: permit_limit_row:REFERENT, permit:REFERENT, feature:REFERENT, parameter:REFERENT, limit:REFERENT, limit_value:REFERENT, limit_set:REFERENT, limit_set_schedule:REFERENT, limit_begin_date:TEXT, limit_end_date:TEXT, limit_value_nmbr:TEXT, limit_value_standard_units:TEXT, limit_value_qualifier_code:TEXT, limit_type_code:TEXT, optional_monitoring_flag:TEXT, limit_set_designator:TEXT, limit_set_name:TEXT, limit_freq_of_analysis_code:TEXT, limit_sample_type_code:TEXT, statistical_base_type_code:TEXT, dmr_comment_text:TEXT, monitoring_location_code:TEXT, has_limit_value_nmbr:BOOLEAN, limit_overlaps_fy2025:BOOLEAN
scope: WORLD
mode: WORLD
derived: False

## PURPOSE REQUIREMENTS (names only)

- aggregated_reporting_requirement (UNRESOLVED)
- discharge_occurrence_in_period (UNRESOLVED)
- fy2025_measurements_materializable (MATERIALIZABLE)
- limit_comparison_operator (INTERPRETED)
- limit_sample_type_code (INTERPRETED)
- limit_set_designator_for_schedule (INTERPRETED)
- limit_type_code_for_enforceability (INTERPRETED)
- limit_value_for_comparison (NUMERIC)
- measurement_limit_pairs_materializable (MATERIALIZABLE)
- monitoring_condition_from_comment (INTERPRETED)
- monitoring_frequency_code (INTERPRETED)
- monitoring_requirements_materializable (MATERIALIZABLE)
- no_numeric_result_cases_materializable (MATERIALIZABLE)
- nodi_code_semantics (INTERPRETED)
- numeric_comparison_candidates_materializable (MATERIALIZABLE)
- optional_monitoring_flag_for_limit_applicability (INTERPRETED)
- optional_monitoring_flag_for_missing_evidence (INTERPRETED)
- optional_monitoring_flag_for_obligation (INTERPRETED)
- pass_fail_reporting_semantics (UNRESOLVED)
- permit_document_text_not_available (UNRESOLVED)
- permit_limit_comment_text (INTERPRETED)
- reported_value_for_comparison (NUMERIC)
- reported_value_qualifier (INTERPRETED)
- statistical_base_for_limit_comparison (INTERPRETED)
- unique_applicable_limit_per_measurement (UNIQUE)

## READ RULES

Unresolved / insufficient / unknown / uninterpreted is not false.

A missing positive tuple is not an established negative.

PURPOSE relations are purpose-specific analytical state and do not replace more direct WORLD facts.

Unknown neighboring propositions do not invalidate independently established propositions unless an explicit dependency says so.

Inspect grounding when evidential status matters.

Do not invent NODI code meanings. Do not infer legends from value frequencies.

## REVISION

state_id=state_b; world_sha256=d0d2106f6df5bb989fe27a22026e8fd89a431273b3d00d2a1e1dbc5de25d941a; construction_sha256=8069637ee217a2e523e7764c0e184578c1a0ccca35d81a310a0dd8dba3041352

## ACCESS

The compiled World is `accepted/world.sqlite`. Ordinary SQLite and Python are allowed.
Do not modify the World. There are no raw source files in the consumer workspace.

