# Occurrence-first baseline (Arm A)

Naive comparison condition. ~20 sampled occurrences. Not a statistical benchmark.

## MEASURED

n=20 dispositions={'UNRESOLVED': 5, 'SUPPORTED_NEGATIVE': 3, 'SUPPORTED_RESOLUTION': 12} mean documents touched=4.9

| case | obligation | occurrence | disposition | docs |
| --- | --- | --- | --- | --- |
| A01 | nodi_c | measurement:dmr_form_value_id=3896611092 | UNRESOLVED | 5 |
| A02 | nodi_c | measurement:dmr_form_value_id=3896611091 | UNRESOLVED | 5 |
| A03 | nodi_c | measurement:dmr_form_value_id=3896611100 | UNRESOLVED | 6 |
| A04 | nodi_9 | measurement:dmr_form_value_id=3920662047 | UNRESOLVED | 7 |
| A05 | nodi_9 | measurement:dmr_form_value_id=3920662059 | UNRESOLVED | 4 |
| A06 | nodi_9 | measurement:dmr_form_value_id=3920662071 | SUPPORTED_NEGATIVE | 6 |
| A07 | when_discharging | 3610840344|3600904607 | SUPPORTED_RESOLUTION | 5 |
| A08 | when_discharging | 3610840345|3600904607 | SUPPORTED_RESOLUTION | 4 |
| A09 | when_discharging | 3610840341|3600904607 | SUPPORTED_RESOLUTION | 4 |
| A10 | geometric_mean | 3610673284|3600891019 | SUPPORTED_NEGATIVE | 4 |
| A11 | geometric_mean | 3610673282|3600891019 | SUPPORTED_NEGATIVE | 5 |
| A12 | pass_fail | 3610839676|3600904539 | SUPPORTED_RESOLUTION | 4 |
| A13 | pass_fail | 3610839677|3600904539 | SUPPORTED_RESOLUTION | 4 |
| A14 | empty_numeric_limit | 3610129901|3600833510 | SUPPORTED_RESOLUTION | 5 |
| A15 | empty_numeric_limit | 3610129901|3600833505 | SUPPORTED_RESOLUTION | 5 |
| A16 | document_authority | document_inventory.json | SUPPORTED_RESOLUTION | 5 |
| A17 | monitoring_frequency | permit_limit_row:limit_set_schedule_id=3600904607|limit_value_id=3610840344 | SUPPORTED_RESOLUTION | 5 |
| A18 | monitoring_frequency | permit_limit_row:limit_set_schedule_id=3600904607|limit_value_id=3610840345 | SUPPORTED_RESOLUTION | 5 |
| A19 | monitoring_frequency | permit_limit_row:limit_set_schedule_id=3600833510|limit_value_id=3610129867 | SUPPORTED_RESOLUTION | 5 |
| A20 | monitoring_frequency | permit_limit_row:limit_set_schedule_id=3600833510|limit_value_id=3610129901 | SUPPORTED_RESOLUTION | 5 |

Inconsistent interpretations across sibling samples:

{
  "nodi_c": [
    "The structured DMR row for dmr_form_value_id 3896611092 records NODI_CODE=C with no numeric DMR_VALUE_NMBR for required flow monitoring (parameter 50050, limit_value_id 3610129868, optional_monitoring",
    "The structured DMR row records NODI_CODE 'C' with no numeric flow value for the November 2024 monitoring period. The workspace does not contain any authoritative NODI code legend or permit text that d",
    "The occurrence is a Federal FY2025 DMR flow measurement (parameter 50050, Outfall 001, permit NM0000116) with an empty numeric result and NODI_CODE 'C'. Purpose C requires interpreting nodi_code seman"
  ],
  "nodi_9": [
    "This measurement is an optional, conditionally required WET retest parameter (OPTIONAL_MONITORING_FLAG=Y; permit labels retest reporting as '(If required)'). For the same DMR event (period ending 11/3",
    "The occurrence is a Purpose C no_numeric_result_case with nodi_code '9' and an empty DMR_VALUE_NMBR for parameter 22415 (Whole effluent toxicity - retest #1, Pimephales promelas), flagged OPTIONAL_MON",
    "Parameter 22415 is Pimephales promelas WET retest #1, marked optional in structured sources (OPTIONAL_MONITORING_FLAG=Y). Permit NM0020583 Part II.D.3.c labels retest parameter 22415 as '(If required)"
  ],
  "when_discharging": [
    "Discharge from Outfall 001 (backwash water) occurred during Federal FY2025, so the conditional monitoring requirement was applicable. The permit authorizes intermittent backwash discharge and ties TSS",
    "The permit authorizes intermittent backwash discharge from Outfall 001 and ties pH monitoring frequency to discharge occurrence via footnote *1 'When discharging.', which matches the structured DMR_CO",
    "The DMR_COMMENT_TEXT 'WHEN DISCHARGING.' implements permit footnote *1 for Outfall 001 backwash water limits. For this permit limit row (pH maximum 9.0 standard units, grab sample, monthly DMR reporti"
  ],
  "geometric_mean": [
    "The DMR comment text reproduces permit footnote *6 language for Total Dissolved Solids discharge monitoring, but this occurrence is the BOD5 30-day average concentration limit (limit_value_id 36106732",
    "The structured DMR comment on this row repeats footnote *6 language about Total Dissolved Solids geometric-mean reporting, but the authoritative permit assigns that instruction only to the Total Disso"
  ],
  "pass_fail": [
    "For permit NM0020583 limit row 3610839677 (parameter 22416, Whole effluent toxicity - retest #2), the concentration-max DMR field carries a binary pass/fail indicator for the second required acute WET",
    "Parameter 22415 is the Pimephales promelas Retest 1 reporting code for 48-hour acute NOEC freshwater toxicity. The DMR concentration-max field carries a binary outcome code, not a pollutant concentrat"
  ],
  "empty_numeric_limit": [
    "The empty LIMIT_VALUE_NMBR on this 30-day average (STATISTICAL_BASE_TYPE_CODE AVG) total suspended solids limit row denotes report-only monitoring. The permit requires reporting of 30-day average TSS ",
    "The empty LIMIT_VALUE_NMBR on limit value 3610129901 (TSS, statistical base 3C/AVG, schedule 3600833510) classifies this row as report-only monitoring. The authorized permit requires reporting of 30-d"
  ],
  "monitoring_frequency": [
    "For this pH minimum limit (parameter 00400, limit value 6.6 su) on permit NM0028762 outfall 001, the structured frequency code 01/07 requires one grab pH measurement per week during periods when the p",
    "Monitoring is required once per week (weekly), conditioned on discharge occurring ('when discharging'). The permit's Part I effluent limits table for pH at Outfall 001 specifies measurement frequency ",
    "Monitoring is required once per week (1/Week), using grab samples, for the total suspended solids daily maximum limit of 50 mg/L at Outfall 001.",
    "For this limit row, monitoring is required once per week (1/Week). The permit Part I monitoring table for Total Suspended Solids at Outfall 001 specifies measurement frequency '1/Week' with grab sampl"
  ]
}

## OBSERVED

See table. Duplicate retrieval is expected when each row is judged independently.

## HYPOTHESIS

Occurrence-first repeats codebook/permit lookups for the same meaning.
