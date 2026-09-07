# T05 nodi_9_unresolved

application_key: `measurement:dmr_form_value_id=3920642644`

## application result

- before comparison/monitoring/evidence: UNRESOLVED_SEMANTIC / FREQUENCY_UNINTERPRETED / UNRESOLVED_SEMANTIC
- after comparison/monitoring/evidence: UNRESOLVED_SEMANTIC / FREQUENCY_UNINTERPRETED / UNRESOLVED_SEMANTIC
- unresolved before: `aggregated_reporting_requirement;limit_sample_type_code;monitoring_frequency_code;nodi_code_semantics;permit_limit_comment_text`
- unresolved after: `aggregated_reporting_requirement;limit_sample_type_code;monitoring_frequency_code;nodi_code_semantics;permit_limit_comment_text`

## World tuple

```json
{
  "measurement": "measurement:dmr_form_value_id=3920642644",
  "permit_limit_row": "permit_limit_row:limit_set_schedule_id=3600891019|limit_value_id=3610673291",
  "permit": "permit:permit_number=NM0020583",
  "feature": "feature:feature_id=3600584104|feature_number=001|permit_number=NM0020583",
  "parameter": "parameter:parameter_code=50060",
  "limit": "limit:limit_id=3606239982",
  "limit_value": "limit_value:limit_value_id=3610673291",
  "monitoring_period_end": "2024-10-31",
  "dmr_value_standard_units": "",
  "limit_value_standard_units": ".019",
  "limit_value_qualifier_code": "<=",
  "dmr_value_qualifier_code": "",
  "optional_monitoring_flag": "N",
  "limit_type_code": "ENF",
  "has_reported_value": 0,
  "has_limit_value_nmbr": 1,
  "nodi_code": "9",
  "dmr_comment_text": "TOTAL DISSOLVED SOLIDS (TDS) MEASURED AT OUTFALL 001.  REPORT THE GEOMETRIC MEAN VALUE OF THE WEEKLY VALUES.",
  "limit_freq_of_analysis_code": "01/01",
  "statistical_base_type_code": "MAX"
}
```

## holes mentioning this measurement

```json
[
  {
    "requirement": "nodi_code_semantics",
    "failure_kind": "UNINTERPRETED",
    "subject_json": "{\"measurement\": \"measurement:dmr_form_value_id=3920642644\", \"nodi_code\": \"9\"}",
    "grounding_json": "{}"
  }
]
```

## construction origin / grounding pointer

proposals on State C: ['obligation_v1/T1/when_discharging', 'obligation_v1/T3/pass_fail']

Source locations live in sealed obligation-resolution packets; this World copy carries relation-level grounding in world.sqlite.origins.json.
