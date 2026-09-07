# Refinement results

## MEASURED

### T1 geometric_mean

parent_status=REFINED independently_admitted=False independently_unresolved=False
n_children=4 mechanically_computable=True partition_complete=True
- `non_tds_limit_set_comment_carryover` n=24 disp=SUPPORTED_NEGATIVE admit=ADMIT_DISPOSABLE epi=SOURCE_ESTABLISHED
  partition: DMR_COMMENT_TEXT contains 'GEOMETRIC MEAN' (case-insensitive) AND PARAMETER_CODE != '70295'
- `tds_discharge_geometric_mean_reporting` n=4 disp=SUPPORTED_RESOLUTION admit=ADMIT_DISPOSABLE epi=SOURCE_ESTABLISHED
  partition: DMR_COMMENT_TEXT contains 'GEOMETRIC MEAN' AND PARAMETER_CODE = '70295' AND MONITORING_LOCATION_CODE = '1'
- `tds_net_increase_avg_enforcement` n=4 disp=SUPPORTED_NEGATIVE admit=ADMIT_DISPOSABLE epi=SOURCE_ESTABLISHED
  partition: DMR_COMMENT_TEXT contains 'GEOMETRIC MEAN' AND PARAMETER_CODE = '70295' AND MONITORING_LOCATION_CODE = '2' AND LIMIT_VALUE_NMBR is non-empty
- `tds_residual_reporting_locations` n=8 disp=UNRESOLVED admit=UNRESOLVED epi=UNRESOLVED
  partition: DMR_COMMENT_TEXT contains 'GEOMETRIC MEAN' AND PARAMETER_CODE = '70295' AND ((MONITORING_LOCATION_CODE = '2' AND LIMIT_VALUE_NMBR is empty) OR MONITORING_LOCATION_CODE = '0')

### T1 empty_numeric_limit

parent_status=REFINED independently_admitted=False independently_unresolved=False
n_children=4 mechanically_computable=True partition_complete=True
- `permit_table_report_only_cell` n=18 disp=SUPPORTED_NEGATIVE admit=ADMIT_DISPOSABLE epi=SOURCE_ESTABLISHED
  partition: LIMIT_VALUE_NMBR is empty AND DMR_COMMENT_TEXT is blank (after trim) AND DMR_COMMENT_TEXT does not contain PASS=0/FAIL=1, GEOMETRIC MEAN, or WHEN DISCHARGING (case-insensitive priority to other partitions)
- `conditional_when_discharging_mass_load_na` n=12 disp=SUPPORTED_NEGATIVE admit=ADMIT_DISPOSABLE epi=SOURCE_ESTABLISHED
  partition: LIMIT_VALUE_NMBR is empty AND upper(DMR_COMMENT_TEXT) contains 'WHEN DISCHARGING'
- `pass_fail_wet_reporting` n=12 disp=SUPPORTED_NEGATIVE admit=ADMIT_DISPOSABLE epi=SOURCE_ESTABLISHED
  partition: LIMIT_VALUE_NMBR is empty AND upper(DMR_COMMENT_TEXT) contains both 'PASS = 0' and 'FAIL = 1'
- `geometric_mean_aggregated_reporting` n=15 disp=SUPPORTED_NEGATIVE admit=ADMIT_DISPOSABLE epi=SOURCE_ESTABLISHED
  partition: LIMIT_VALUE_NMBR is empty AND upper(DMR_COMMENT_TEXT) contains 'GEOMETRIC MEAN'

### T2 geometric_mean

parent_status=REFINED independently_admitted=False independently_unresolved=False
n_children=3 mechanically_computable=True partition_complete=True
- `non_tds_comment_carryover` n=24 disp=SUPPORTED_NEGATIVE admit=ADMIT_DISPOSABLE epi=SOURCE_ESTABLISHED
  partition: upper(DMR_COMMENT_TEXT) contains 'GEOMETRIC MEAN' AND PARAMETER_CODE != '70295'
- `tds_report_only_weekly_geom_mean` n=12 disp=SUPPORTED_RESOLUTION admit=ADMIT_DISPOSABLE epi=SOURCE_ESTABLISHED
  partition: upper(DMR_COMMENT_TEXT) contains 'GEOMETRIC MEAN' AND PARAMETER_CODE = '70295' AND LIMIT_VALUE_NMBR is empty
- `tds_numeric_net_increase_comparison` n=4 disp=SUPPORTED_NEGATIVE admit=ADMIT_DISPOSABLE epi=SOURCE_ESTABLISHED
  partition: upper(DMR_COMMENT_TEXT) contains 'GEOMETRIC MEAN' AND PARAMETER_CODE = '70295' AND LIMIT_VALUE_NMBR is non-empty

### T2 empty_numeric_limit

parent_status=REFINED independently_admitted=False independently_unresolved=False
n_children=4 mechanically_computable=True partition_complete=True
- `blank_comment_report_only` n=18 disp=SUPPORTED_NEGATIVE admit=ADMIT_DISPOSABLE epi=SOURCE_ESTABLISHED
  partition: LIMIT_VALUE_NMBR is empty (after trim) AND DMR_COMMENT_TEXT is blank (after trim)
- `when_discharging_non_applicable` n=12 disp=SUPPORTED_NEGATIVE admit=ADMIT_DISPOSABLE epi=SOURCE_ESTABLISHED
  partition: LIMIT_VALUE_NMBR is empty (after trim) AND upper(DMR_COMMENT_TEXT) contains 'WHEN DISCHARGING'
- `pass_fail_wet_encoding` n=12 disp=SUPPORTED_NEGATIVE admit=ADMIT_DISPOSABLE epi=SOURCE_ESTABLISHED
  partition: LIMIT_VALUE_NMBR is empty (after trim) AND upper(DMR_COMMENT_TEXT) contains 'PASS = 0' AND 'FAIL = 1'
- `geometric_mean_aggregated_reporting` n=15 disp=SUPPORTED_NEGATIVE admit=ADMIT_DISPOSABLE epi=SOURCE_ESTABLISHED
  partition: LIMIT_VALUE_NMBR is empty (after trim) AND upper(DMR_COMMENT_TEXT) contains 'GEOMETRIC MEAN'

### T3 geometric_mean

parent_status=REFINED independently_admitted=False independently_unresolved=False
n_children=3 mechanically_computable=True partition_complete=True
- `geom_mean_non_tds_carryover` n=24 disp=SUPPORTED_NEGATIVE admit=ADMIT_DISPOSABLE epi=SOURCE_ESTABLISHED
  partition: DMR_COMMENT_TEXT contains 'GEOMETRIC MEAN' (case-insensitive) AND PARAMETER_CODE != '70295'
- `geom_mean_tds_report_only` n=12 disp=SUPPORTED_RESOLUTION admit=ADMIT_DISPOSABLE epi=SOURCE_ESTABLISHED
  partition: DMR_COMMENT_TEXT contains 'GEOMETRIC MEAN' AND PARAMETER_CODE = '70295' AND LIMIT_VALUE_NMBR is null or empty
- `geom_mean_tds_net_increase_comparison` n=4 disp=SUPPORTED_NEGATIVE admit=ADMIT_DISPOSABLE epi=SOURCE_ESTABLISHED
  partition: DMR_COMMENT_TEXT contains 'GEOMETRIC MEAN' AND PARAMETER_CODE = '70295' AND LIMIT_VALUE_NMBR is present and non-empty

### T3 empty_numeric_limit

parent_status=REFINED independently_admitted=False independently_unresolved=False
n_children=4 mechanically_computable=True partition_complete=True
- `empty_limit_blank_comment_report_only` n=18 disp=SUPPORTED_RESOLUTION admit=ADMIT_DISPOSABLE epi=SOURCE_ESTABLISHED
  partition: has_limit_value_nmbr = false AND trim(DMR_COMMENT_TEXT) = ''
- `empty_limit_when_discharging_column` n=12 disp=SUPPORTED_RESOLUTION admit=ADMIT_DISPOSABLE epi=SOURCE_ESTABLISHED
  partition: has_limit_value_nmbr = false AND upper(DMR_COMMENT_TEXT) contains 'WHEN DISCHARGING'
- `empty_limit_pass_fail_wet_encoding` n=12 disp=SUPPORTED_RESOLUTION admit=ADMIT_DISPOSABLE epi=SOURCE_ESTABLISHED
  partition: has_limit_value_nmbr = false AND upper(DMR_COMMENT_TEXT) contains 'PASS = 0' AND upper(DMR_COMMENT_TEXT) contains 'FAIL = 1'
- `empty_limit_geometric_mean_reporting` n=15 disp=SUPPORTED_RESOLUTION admit=ADMIT_DISPOSABLE epi=SOURCE_ESTABLISHED
  partition: has_limit_value_nmbr = false AND upper(DMR_COMMENT_TEXT) contains 'GEOMETRIC MEAN'

## OBSERVED

TDS/non-TDS recovery: {
  "T1:geometric_mean": {
    "tds": true,
    "nontds": true,
    "recovered": true
  },
  "T2:geometric_mean": {
    "tds": true,
    "nontds": true,
    "recovered": true
  },
  "T3:geometric_mean": {
    "tds": true,
    "nontds": true,
    "recovered": true
  }
}
fragmented=[]

## HYPOTHESIS

A refined parent is superseded by children; it is not independently UNRESOLVED.
