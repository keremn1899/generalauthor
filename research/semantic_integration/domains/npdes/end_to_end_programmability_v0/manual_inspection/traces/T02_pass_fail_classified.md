# T02 pass_fail_classified

application_key: `measurement:dmr_form_value_id=3920662053`

## application result

- before comparison/monitoring/evidence: UNRESOLVED_SEMANTIC / FREQUENCY_UNINTERPRETED / UNRESOLVED_SEMANTIC
- after comparison/monitoring/evidence: PASS / FREQUENCY_UNINTERPRETED / DETERMINATE
- unresolved before: `limit_sample_type_code;monitoring_frequency_code;pass_fail_reporting_semantics;permit_limit_comment_text`
- unresolved after: `limit_sample_type_code;monitoring_frequency_code;permit_limit_comment_text`

## World tuple

```json
{
  "measurement": "measurement:dmr_form_value_id=3920662053",
  "permit_limit_row": "permit_limit_row:limit_set_schedule_id=3600904539|limit_value_id=3610839682",
  "permit": "permit:permit_number=NM0020583",
  "feature": "feature:feature_id=3600584105|feature_number=TX1|permit_number=NM0020583",
  "parameter": "parameter:parameter_code=TEM3D",
  "limit": "limit:limit_id=3606351401",
  "limit_value": "limit_value:limit_value_id=3610839682",
  "monitoring_period_end": "2024-11-30",
  "dmr_value_standard_units": "0",
  "limit_value_standard_units": "",
  "limit_value_qualifier_code": "",
  "dmr_value_qualifier_code": "=",
  "optional_monitoring_flag": "N",
  "limit_type_code": "ENF",
  "has_reported_value": 1,
  "has_limit_value_nmbr": 0,
  "nodi_code": "",
  "dmr_comment_text": "(PASS = 0  FAIL = 1) REPORT PASS AS '0' OR REPORT FAIL AS '1' IN CONCENTRATION MAX. ABOVE.  IF ALL TESTS PASS FOR THE FIRST YEAR OF THE PERMIT, THE FREQUENCY WILL BE REDUCED FOR YEARS 2-5 TO:  1/6 MONTHS FOR DAPHNIA PULEX & 1/YR FOR PIMEPHALES PROMELAS (SEE FOOTNOTE 9, PAGE 3 OF PART I OF PERMIT).",
  "limit_freq_of_analysis_code": "01/90",
  "statistical_base_type_code": "MAX"
}
```

## holes mentioning this measurement

```json
[]
```

## construction origin / grounding pointer

proposals on State C: ['obligation_v1/T1/when_discharging', 'obligation_v1/T3/pass_fail']

Source locations live in sealed obligation-resolution packets; this World copy carries relation-level grounding in world.sqlite.origins.json.
