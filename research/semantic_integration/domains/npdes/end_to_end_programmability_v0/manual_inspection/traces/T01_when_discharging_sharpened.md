# T01 when_discharging_sharpened

application_key: `measurement:dmr_form_value_id=3920700840`

## application result

- before comparison/monitoring/evidence: WITHIN_LIMIT / UNRESOLVED_SEMANTIC / UNRESOLVED_SEMANTIC
- after comparison/monitoring/evidence: WITHIN_LIMIT / UNRESOLVED_FACTUAL / UNRESOLVED_FACTUAL
- unresolved before: `conditional_discharge_dependent_monitoring;limit_sample_type_code;monitoring_frequency_code;permit_limit_comment_text`
- unresolved after: `discharge_occurrence_in_period;limit_sample_type_code;monitoring_frequency_code`

## World tuple

```json
{
  "measurement": "measurement:dmr_form_value_id=3920700840",
  "permit_limit_row": "permit_limit_row:limit_set_schedule_id=3600904607|limit_value_id=3610840344",
  "permit": "permit:permit_number=NM0028762",
  "feature": "feature:feature_id=3600602070|feature_number=001|permit_number=NM0028762",
  "parameter": "parameter:parameter_code=00400",
  "limit": "limit:limit_id=3606351872",
  "limit_value": "limit_value:limit_value_id=3610840344",
  "monitoring_period_end": "2024-10-31",
  "dmr_value_standard_units": "7.87",
  "limit_value_standard_units": "6.6",
  "limit_value_qualifier_code": ">=",
  "dmr_value_qualifier_code": "=",
  "optional_monitoring_flag": "N",
  "limit_type_code": "ENF",
  "has_reported_value": 1,
  "has_limit_value_nmbr": 1,
  "nodi_code": "",
  "dmr_comment_text": "WHEN DISCHARGING.",
  "limit_freq_of_analysis_code": "01/07",
  "statistical_base_type_code": "MIN"
}
```

## holes mentioning this measurement

```json
[]
```

## construction origin / grounding pointer

proposals on State C: ['obligation_v1/T1/when_discharging', 'obligation_v1/T3/pass_fail']

Source locations live in sealed obligation-resolution packets; this World copy carries relation-level grounding in world.sqlite.origins.json.
