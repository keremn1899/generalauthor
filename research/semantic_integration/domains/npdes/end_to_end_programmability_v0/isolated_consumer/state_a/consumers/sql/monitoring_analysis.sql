-- FY2025 monitoring/compliance extract against the accepted World.
-- Works on States A/B/C: uses only baseline T5 relation names and columns.
-- Optional enrichment relations are discovered by the Python consumer, not this file.
-- Do not open CSVs, PDFs, or permit-package text.

WITH holes_by_measurement AS (
  SELECT
    json_extract(subject_json, '$.measurement') AS measurement,
    requirement,
    failure_kind,
    json_extract(observed_json, '$.value') AS observed_value
  FROM _hole
  WHERE json_extract(subject_json, '$.measurement') IS NOT NULL
),
holes_by_limit AS (
  SELECT
    json_extract(subject_json, '$.permit_limit_row') AS permit_limit_row,
    json_extract(subject_json, '$.limit_value_id') AS limit_value_id,
    json_extract(subject_json, '$.limit_set_schedule_id') AS limit_set_schedule_id,
    requirement,
    failure_kind
  FROM _hole
  WHERE json_extract(subject_json, '$.permit_limit_row') IS NOT NULL
     OR json_extract(subject_json, '$.limit_value_id') IS NOT NULL
)
SELECT
  mlp.measurement AS measurement,
  mlp.permit_limit_row AS permit_limit_row,
  mlp.permit AS permit,
  mlp.feature AS feature,
  mlp.parameter AS parameter,
  mlp.limit_value AS limit_value,
  mlp.monitoring_period_end AS monitoring_period,
  dmr.dmr_value_nmbr AS reported_value,
  dmr.limit_value_nmbr AS numeric_limit,
  dmr.has_reported_value AS has_reported_value,
  dmr.has_limit_value_nmbr AS has_limit_value_nmbr,
  dmr.nodi_code AS nodi_code,
  dmr.dmr_value_qualifier_code AS reported_qualifier,
  dmr.limit_value_qualifier_code AS limit_qualifier,
  dmr.dmr_value_standard_units AS reported_standard_units,
  dmr.limit_value_standard_units AS limit_standard_units,
  dmr.optional_monitoring_flag AS optional_monitoring_flag,
  dmr.limit_type_code AS limit_type_code,
  dmr.statistical_base_type_code AS statistical_base_type_code,
  CASE WHEN ncc.measurement IS NOT NULL THEN 1 ELSE 0 END AS is_numeric_comparison_candidate,
  CASE WHEN nnr.measurement IS NOT NULL THEN 1 ELSE 0 END AS is_no_numeric_result_case,
  COALESCE(h_nodi.requirement, '') AS nodi_hole_requirement,
  COALESCE(h_nodi.observed_value, '') AS nodi_hole_value,
  COALESCE(h_freq.requirement, '') AS frequency_hole_requirement
FROM measurement_limit_pair AS mlp
JOIN dmr_measurement AS dmr ON dmr.measurement = mlp.measurement
LEFT JOIN numeric_comparison_candidate AS ncc ON ncc.measurement = mlp.measurement
LEFT JOIN no_numeric_result_case AS nnr ON nnr.measurement = mlp.measurement
LEFT JOIN holes_by_measurement AS h_nodi
  ON h_nodi.measurement = mlp.measurement
 AND h_nodi.requirement = 'nodi_code_semantics'
LEFT JOIN holes_by_measurement AS h_freq
  ON h_freq.measurement = mlp.measurement
 AND h_freq.requirement = 'monitoring_frequency_code'
ORDER BY mlp.permit, mlp.feature, mlp.parameter, mlp.monitoring_period_end, mlp.measurement;
