# T07 unaffected_after_when_discharging

application_key: `measurement:dmr_form_value_id=3896611165`

## application result

- before comparison/monitoring/evidence: WITHIN_LIMIT / FREQUENCY_UNINTERPRETED / DETERMINATE
- after comparison/monitoring/evidence: WITHIN_LIMIT / FREQUENCY_UNINTERPRETED / DETERMINATE
- unresolved before: `limit_sample_type_code;monitoring_frequency_code`
- unresolved after: `limit_sample_type_code;monitoring_frequency_code`

## World tuple

```json
{
  "measurement": "measurement:dmr_form_value_id=3896611165",
  "permit_limit_row": "permit_limit_row:limit_set_schedule_id=3600833510|limit_value_id=3610129865",
  "permit": "permit:permit_number=NM0000116",
  "feature": "feature:feature_id=3600545262|feature_number=001|permit_number=NM0000116",
  "parameter": "parameter:parameter_code=00400",
  "limit": "limit:limit_id=3605908064",
  "limit_value": "limit_value:limit_value_id=3610129865",
  "monitoring_period_end": "2025-07-31",
  "dmr_value_standard_units": "8",
  "limit_value_standard_units": "6",
  "limit_value_qualifier_code": ">=",
  "dmr_value_qualifier_code": "=",
  "optional_monitoring_flag": "N",
  "limit_type_code": "ENF",
  "has_reported_value": 1,
  "has_limit_value_nmbr": 1,
  "nodi_code": "",
  "dmr_comment_text": "",
  "limit_freq_of_analysis_code": "01/01",
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
