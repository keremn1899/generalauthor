# Obligation refinements

## MEASURED

n_refinements=12

### T1 geometric_mean

```json
{
  "parent": "geometric_mean",
  "children": [
    {
      "obligation_id": "tds_weekly_geometric_mean_reporting",
      "exact_semantic_question": "For TDS limits (parameter 70295) under footnote *6, does geometric-mean-of-weekly-values reporting block ordinary single-period numeric comparison of individual DMR monitoring-period values?",
      "relation_contract": "TDS aggregated weekly geometric-mean reporting is not an ordinary single-period numeric comparison"
    },
    {
      "obligation_id": "limit_set_tds_comment_carryover",
      "exact_semantic_question": "For non-TDS parameters that inherit the TDS-specific geometric-mean DMR comment via limit-set propagation, does that comment establish any non-ordinary comparison rule for individual monitoring-period values?",
      "relation_contract": "limit-set-propagated TDS geometric-mean comment does not alter non-TDS single-period comparison semantics"
    }
  ],
  "why_necessary": "All 40 occurrences share one identical DMR_COMMENT_TEXT that explicitly names TDS at Outfall 001, but structured data attaches it to 10 parameters (BOD, pH, TSS, cyanide, flow, chlorine, E. coli, TDS, percent removals). Permit footnote *6 authoritatively applies only to TDS discharge reporting. TDS net-increase limits use 30-day average enforcement language in the statement of basis, while footnote *6 requires geometric mean of weekly values \u2014 a materially different question than whether BOD monthly values should skip ordinary comparison because of a TDS comment copied at limit-set level.",
  "occurrence_partition": {
    "tds_weekly_geometric_mean_reporting": {
      "count": 16,
      "rule": "DMR_COMMENT_TEXT contains 'GEOMETRIC MEAN' AND PARAMETER_CODE = '70295'",
      "representative_examples": [
        "3610673300|3600891019",
        "3610673275|3600891019",
        "3610673287|3600891019"
      ]
    },
    "limit_set_tds_comment_carryover": {
      "count": 24,
      "rule": "DMR_COMMENT_TEXT contains 'GEOMETRIC MEAN' AND PARAMETER_CODE != '70295'",
      "representative_examples": [
        "3610673284|3600891019",
        "3610673282|3600891019",
        "3610673283|3600891019",
        "3610673281|3600891019"
      ]
    }
  },
  "mechanically_computable": true
}
```

### T1 empty_numeric_limit

```json
{
  "parent": "empty_numeric_limit",
  "children": [
    {
      "obligation_id": "empty_limit_report_or_na_permit_cell",
      "exact_semantic_question": "When LIMIT_VALUE_NMBR is empty and DMR_COMMENT_TEXT is blank, does the row correspond to a permit limit-table Report or N/A cell (monitoring/reporting only, not a numeric effluent limit for that statistical base)?",
      "expected_disposition": "SUPPORTED_RESOLUTION",
      "resolution_summary": "Report-only monitoring or non-numeric permit-table cell; not a numeric limit row for comparison."
    },
    {
      "obligation_id": "empty_limit_when_discharging_mass_column",
      "exact_semantic_question": "When LIMIT_VALUE_NMBR is empty, DMR_COMMENT_TEXT contains WHEN DISCHARGING., and LIMIT_VALUE_TYPE_CODE is Q1 or Q2, is the row a non-applicable mass-load limit column rather than a numeric effluent limit?",
      "expected_disposition": "SUPPORTED_RESOLUTION",
      "resolution_summary": "Non-applicable N/A mass-load column; numeric concentration limits reside on sibling C2/C3 rows."
    },
    {
      "obligation_id": "empty_limit_wet_pass_fail_encoding",
      "exact_semantic_question": "When LIMIT_VALUE_NMBR is empty and DMR_COMMENT_TEXT encodes PASS=0/FAIL=1 (with pass=0;fail=1 unit descriptors), is the row a pass/fail WET reporting obligation rather than an ordinary numeric concentration limit?",
      "expected_disposition": "SUPPORTED_RESOLUTION",
      "resolution_summary": "Special pass/fail reporting semantics; not report-only monitoring and not an ordinary numeric concentration limit."
    },
    {
      "obligation_id": "empty_limit_geometric_mean_schedule_row",
      "exact_semantic_question": "When LIMIT_VALUE_NMBR is empty and DMR_COMMENT_TEXT requires reporting the geometric mean of weekly values, is the row a report-only or non-numeric statistical-base cell while numeric limits appear on sibling rows?",
      "expected_disposition": "SUPPORTED_RESOLUTION",
      "resolution_summary": "Report-only/non-numeric cell under geometric-mean reporting instructions; numeric limits appear on sibling AVG/C2 or mass-load rows."
    }
  ],
  "why_necessary": "Retrieved permit text and structured rows show four materially different reasons LIMIT_VALUE_NMBR is empty: permit-table Report/N/A cells, N/A mass-load columns under WHEN DISCHARGING, pass/fail WET encoding, and geometric-mean TDS reporting rows. A single trichotomy (numeric limit vs report-only vs something else) assigns different correct answers to different 57-row subsets, so the parent obligation cannot be resolved uniformly.",
  "occurrence_partition": {
    "empty_limit_report_or_na_permit_cell": [
      "3610129868|3600833505",
      "3610129868|3600833510",
      "3610129869|3600833505",
      "3610129869|3600833510",
      "3610129870|3600833505",
      "3610129870|3600833510",
      "3610129871|3600833505",
      "3610129871|3600833510",
      "3610129901|3600833505",
      "3610129901|3600833510",
      "3610129902|3600833505",
      "3610129902|3600833510",
      "3610838795|3600904358",
      "3610838796|3600904358",
      "3610838797|3600904358",
      "3610838798|3600904358",
      "3610838799|3600904358",
      "3610838800|3600904358"
    ],
    "empty_limit_when_discharging_mass_column": [
      "3610840336|3600904606",
      "3610840337|3600904606",
      "3610840338|3600904606",
      "3610840339|3600904606",
      "3610840340|3600904607",
      "3610840341|3600904607",
      "3610840349|3600904607",
      "3610840350|3600904607",
      "3610840367|3600904606",
      "3610840368|3600904606",
      "3610840369|3600904606",
      "3610840370|3600904606"
    ],
    "empty_limit_wet_pass_fail_encoding": [
      "3610839676|3600904539",
      "3610839677|3600904539",
      "3610839678|3600904539",
      "3610839679|3600904539",
      "3610839680|3600904539",
      "3610839681|3600904539",
      "3610839682|3600904539",
      "3610839683|3600904539",
      "3610839684|3600904539",
      "3610839685|3
```

### T1 monitoring_frequency

```json
{
  "parent": "monitoring_frequency",
  "children": [
    "monitoring_frequency_calendar_codes",
    "monitoring_frequency_noncalendar_codes"
  ],
  "why_necessary": "Retrieved permit text establishes plain-language calendar sampling frequencies (1/Day, 1/Week, 5/Week, 2/Week, 1/Quarter, 2/month) that pair consistently with six of eight code values, but two codes (99/99, 09/99) attach to qualitatively different monitoring modes\u2014continuous totalizing flow and conditional WET retest reporting\u2014whose permit language never uses the opaque code strings and is not reducible to a samples-per-period calendar obligation.",
  "occurrence_partition": {
    "monitoring_frequency_calendar_codes": [
      "01/01",
      "01/07",
      "02/07",
      "05/WK",
      "01/90",
      "02/30"
    ],
    "monitoring_frequency_noncalendar_codes": [
      "99/99",
      "09/99"
    ]
  },
  "mechanically_computable": true
}
```

### T2 nodi_9

```json
{
  "parent": "nodi_9",
  "children": [
    {
      "obligation_id": "nodi_9_wet_optional_retest",
      "exact_semantic_question": "What does NODI code 9 mean for a FY2025 no-numeric-result DMR row on optional WET retest parameters (22415, 22416, 22418, 22419, 51443, 51444) with OPTIONAL_MONITORING_FLAG=Y and LIMIT_FREQ_OF_ANALYSIS_CODE=09/99?",
      "occurrence_count": 24
    },
    {
      "obligation_id": "nodi_9_trc_conditional",
      "exact_semantic_question": "What does NODI code 9 mean for a FY2025 no-numeric-result DMR row on parameter 50060 (Chlorine, total residual) with OPTIONAL_MONITORING_FLAG=N and daily grab monitoring conditioned by footnote *5?",
      "occurrence_count": 12
    }
  ],
  "why_necessary": "All 36 NODI=9 rows share empty DMR_VALUE_NMBR and permit NM0020583, but retrieved evidence partitions them into two monitoring regimes: optional conditional WET retest lines labeled '(If required)' in the permit versus nominally required daily TRC monitoring that footnote *5 conditions on chlorine use. A single code-9 interpretation would conflate permitted optional omission with conditional non-activation of a scheduled parameter.",
  "occurrence_partition": {
    "nodi_9_wet_optional_retest": {
      "permit": "NM0020583",
      "parameters": [
        "22415",
        "22416",
        "22418",
        "22419",
        "51443",
        "51444"
      ],
      "optional_monitoring_flag": "Y",
      "limit_freq_of_analysis_code": "09/99",
      "dmr_form_value_ids_example": [
        "3920662047",
        "3920662059",
        "3920662071",
        "3920662083"
      ]
    },
    "nodi_9_trc_conditional": {
      "permit": "NM0020583",
      "parameters": [
        "50060"
      ],
      "optional_monitoring_flag": "N",
      "limit_freq_of_analysis_code": "01/01",
      "dmr_form_value_ids_example": [
        "3920642644",
        "3920642676",
        "3920642708"
      ]
    }
  },
  "mechanically_computable": true
}
```

### T2 geometric_mean

```json
{
  "parent": "geometric_mean",
  "children": [
    {
      "id": "tds_weekly_geometric_mean_aggregation",
      "exact_semantic_question": "For TDS limits (parameter 70295) under NM0020583 footnote *6, must effluent-limit comparison use the geometric mean of weekly values rather than an individual monitoring-period DMR value?",
      "recommended_disposition": "SUPPORTED_RESOLUTION",
      "resolution_summary": "Permit footnote *6 requires reporting the geometric mean of weekly TDS values at Outfall 001. Net TDS limits (*8) are computed from aggregated discharge and influent values. Compliance comparison therefore operates on aggregated weekly geometric means (or net values derived from them), not on treating a single DMR monitoring-period cell as an ordinary single-sample numeric comparison."
    },
    {
      "id": "non_tds_misattached_geometric_mean_comment",
      "exact_semantic_question": "For permit_limit rows whose DMR_COMMENT_TEXT contains 'GEOMETRIC MEAN' but whose PARAMETER_CODE is not TDS (70295), does the comment impose geometric-mean aggregation before limit comparison?",
      "recommended_disposition": "SUPPORTED_NEGATIVE",
      "resolution_summary": "The shared DMR comment text is TDS-specific (matches footnote *6 only). Final permit limit tables assign non-TDS pollutants different footnotes and sampling bases (e.g., BOD *1 five-day sampling, E. coli *2/*3 CFU limits). No permit text requires geometric-mean reporting for those parameters. The comment on their structured rows is a limit-set propagation artifact and does not block ordinary single-period numeric comparison for those parameters."
    }
  ],
  "why_necessary": "All 40 structured occurrences share one identical TDS-focused DMR_COMMENT_TEXT attached at the limit-set level, but permit narrative establishes geometric-mean-of-weekly-values reporting only for total dissolved solids (footnote *6). Applying one aggregation rule to all 10 affected parameter codes would contradict permit Part I tables for BOD, E. coli, pH, cyanide, flow, and other pollutants.",
  "occurrence_partition": {
    "tds_weekly_geometric_mean_aggregation": "DMR_COMMENT_TEXT contains 'GEOMETRIC MEAN' (case-insensitive) AND PARAMETER_CODE = '70295'",
    "non_tds_misattached_geometric_mean_comment": "DMR_COMMENT_TEXT contains 'GEOMETRIC MEAN' (case-insensitive) AND PARAMETER_CODE != '70295'"
  },
  "mechanically_computable": true
}
```

### T2 empty_numeric_limit

```json
{
  "parent": "empty_numeric_limit",
  "children": [
    {
      "obligation_id": "empty_limit_report_only_monitoring",
      "exact_semantic_question": "When LIMIT_VALUE_NMBR is empty and DMR_COMMENT_TEXT is blank, is the row report-only monitoring with no numeric concentration limit for comparison?",
      "occurrence_count": 18,
      "allowed_dispositions": [
        "SUPPORTED_RESOLUTION",
        "UNRESOLVED"
      ]
    },
    {
      "obligation_id": "empty_limit_geometric_mean_reporting",
      "exact_semantic_question": "When LIMIT_VALUE_NMBR is empty and DMR_COMMENT_TEXT references geometric mean reporting, is the row an aggregated reporting obligation rather than a per-period numeric concentration limit?",
      "occurrence_count": 15,
      "allowed_dispositions": [
        "SUPPORTED_RESOLUTION"
      ]
    },
    {
      "obligation_id": "empty_limit_conditional_when_discharging",
      "exact_semantic_question": "When LIMIT_VALUE_NMBR is empty and DMR_COMMENT_TEXT is 'WHEN DISCHARGING.', is the row conditional monitoring/reporting (not a standing numeric limit) whose applicability depends on discharge?",
      "occurrence_count": 12,
      "allowed_dispositions": [
        "SUPPORTED_RESOLUTION"
      ]
    },
    {
      "obligation_id": "empty_limit_pass_fail_coded_wet",
      "exact_semantic_question": "When LIMIT_VALUE_NMBR is empty and DMR_COMMENT_TEXT specifies PASS=0/FAIL=1 reporting, is the row a pass/fail coded WET obligation rather than a numeric concentration limit?",
      "occurrence_count": 12,
      "allowed_dispositions": [
        "SUPPORTED_RESOLUTION"
      ]
    }
  ],
  "why_necessary": "Retrieved permit text and DMR_COMMENT_TEXT show that empty LIMIT_VALUE_NMBR does not denote one homogeneous class. The 57 affected rows partition into four materially different obligation types: plain report-only monitoring (permit 'Report' limits), geometric-mean TDS reporting, conditional when-discharging monitoring, and pass/fail coded WET (0/1 vs critical dilution). A single parent answer of 'numeric limit', 'report-only', or 'something else' would misclassify a large fraction of rows.",
  "occurrence_partition": {
    "rule": "Partition permit_limits.csv rows with empty LIMIT_VALUE_NMBR by DMR_COMMENT_TEXT pattern, in priority order: (1) contains 'PASS = 0' and 'FAIL = 1' -> pass_fail_coded_wet; (2) contains 'GEOMETRIC MEAN' -> geometric_mean_reporting; (3) equals or starts with 'WHEN DISCHARGING' -> conditional_when_discharging; (4) otherwise -> report_only_monitoring.",
    "counts": {
      "empty_limit_report_only_monitoring": 18,
      "empty_limit_geometric_mean_reporting": 15,
      "empty_limit_conditional_when_discharging": 12,
      "empty_limit_pass_fail_coded_wet": 12
    },
    "total": 57,
    "exhaustive": true,
    "mutually_exclusive": true
  },
  "mechanically_computable": {
    "partition_from_structured": true,
    "partition_fields": [
      "LIMIT_VALUE_NMBR",
      "DMR_COMMENT_TEXT"
    ],
    "requires_permit_text_for_resolution": {
      "empty_limit_report_only_monitoring": true,
      "empty_limit_geometric_mean_reporting": false,
      "empty_limit_conditional_when_discharging": false,
      "empty_limit_pass_fail_coded_wet": false
    },
    "notes": "DMR_COMMENT_TEXT alone mechanically partitions all 57 rows. Resolving the report-only subclass (blank comment) still requires permit narrative crosswalk; the other three subclasses are established by DMR comment plus matching permit excerpts already retrieved."
  }
}
```

### T2 monitoring_frequency

```json
{
  "parent": "monitoring_frequency",
  "children": [
    {
      "obligation_id": "monitoring_frequency_calendar_codes",
      "exact_semantic_question": "What calendar-periodic monitoring frequencies do LIMIT_FREQ_OF_ANALYSIS_CODE values 01/01, 01/07, 02/07, 02/30, 05/WK, and 01/90 establish when joined to permit Part I tables?",
      "codes": [
        "01/01",
        "01/07",
        "02/07",
        "02/30",
        "05/WK",
        "01/90"
      ]
    },
    {
      "obligation_id": "monitoring_frequency_continuous_code",
      "exact_semantic_question": "What monitoring obligation does LIMIT_FREQ_OF_ANALYSIS_CODE 99/99 establish?",
      "codes": [
        "99/99"
      ]
    },
    {
      "obligation_id": "monitoring_frequency_event_triggered_code",
      "exact_semantic_question": "What monitoring or reporting obligation does LIMIT_FREQ_OF_ANALYSIS_CODE 09/99 establish for WET retest parameters?",
      "codes": [
        "09/99"
      ]
    }
  ],
  "why_necessary": "Retrieved evidence shows materially different obligation types under the same field: most codes align with calendar MEASUREMENT FREQUENCY text in permit tables, 99/99 aligns with continuous flow monitoring only, and 09/99 marks conditional WET retest reporting described as '(If required)' rather than a periodic schedule. A single interpretation rule cannot treat all eight codes uniformly.",
  "occurrence_partition": {
    "monitoring_frequency_calendar_codes": "permit_limit rows where LIMIT_FREQ_OF_ANALYSIS_CODE in {01/01, 01/07, 02/07, 02/30, 05/WK, 01/90}",
    "monitoring_frequency_continuous_code": "permit_limit rows where LIMIT_FREQ_OF_ANALYSIS_CODE = 99/99",
    "monitoring_frequency_event_triggered_code": "permit_limit rows where LIMIT_FREQ_OF_ANALYSIS_CODE = 09/99"
  },
  "mechanically_computable": true
}
```

### T3 nodi_9

```json
{
  "parent": "nodi_9",
  "children": [
    "nodi_9_wet_retest_optional",
    "nodi_9_chlorine_trc"
  ],
  "why_necessary": "Retrieved evidence shows NODI code 9 on FY2025 no-numeric-result rows partitions into two parameter families with materially different monitoring-obligation structures on the same permit (NM0020583). WET retest parameters (22415, 22416, 22418, 22419, 51443, 51444) are optional (OPTIONAL_MONITORING_FLAG=Y, frequency 09/99) and permit-labeled '(If required)'. Chlorine total residual (50060) is non-optional in structured limits (OPTIONAL_MONITORING_FLAG=N, frequency 01/01) but permit footnote *5 makes field monitoring conditional on chlorine use. A single uniform interpretation of NODI 9 across both families is not established by workspace text and would conflate conditional retest-not-required cases with conditional TRC-use cases.",
  "occurrence_partition": {
    "nodi_9_wet_retest_optional": {
      "filter": "NODI_CODE='9' AND DMR_VALUE_NMBR empty AND PARAMETER_CODE IN ('22415','22416','22418','22419','51443','51444')",
      "count": 24,
      "representative_dmr_form_value_ids": [
        "3920662047",
        "3920662059",
        "3920662071",
        "3920662083"
      ]
    },
    "nodi_9_chlorine_trc": {
      "filter": "NODI_CODE='9' AND DMR_VALUE_NMBR empty AND PARAMETER_CODE='50060'",
      "count": 12,
      "representative_dmr_form_value_ids": [
        "3920642644",
        "3920642676",
        "3920642708"
      ]
    }
  },
  "mechanically_computable": true
}
```

### T3 geometric_mean

```json
{
  "parent": "geometric_mean",
  "children": [
    {
      "id": "geometric_mean_tds_reporting",
      "exact_semantic_question": "For TDS permit limits linked to footnotes *6\u2013*8, what does the geometric-mean-of-weekly-values reporting requirement establish about comparison of individual monitoring-period values to effluent limits?",
      "relation_contract": "TDS reporting uses geometric mean of weekly values; enforceable net-increase limits are 30-day averages\u2014individual weekly samples are not the comparison unit",
      "supported_disposition": "SUPPORTED_RESOLUTION"
    },
    {
      "id": "geometric_mean_comment_on_non_tds_limits",
      "exact_semantic_question": "For non-TDS parameters on limit set schedule 3600891019 that share a DMR comment naming TDS geometric-mean reporting, does that comment block ordinary single-period numeric comparison?",
      "relation_contract": "schedule-level comment artifact does not impose geometric-mean comparison on parameters not named in the comment or permit footnotes",
      "supported_disposition": "SUPPORTED_NEGATIVE"
    }
  ],
  "why_necessary": "Retrieved evidence shows one DMR_COMMENT_TEXT string on 40 permit_limit rows spanning 10 parameters, but permit footnotes *6\u2013*7 and the comment text itself name only TDS. Non-TDS rows (BOD, pH, TSS, E. coli, etc.) retain ordinary numeric limits and 5/week monitoring without geometric-mean footnotes. Treating all 40 rows under a single comparison rule would conflate TDS aggregated-reporting semantics with unrelated parameters.",
  "occurrence_partition": {
    "geometric_mean_tds_reporting": {
      "parameter_code": "70295",
      "count": 16,
      "representative_limit_value_ids": [
        "3610673275",
        "3610673300",
        "3610838803"
      ]
    },
    "geometric_mean_comment_on_non_tds_limits": {
      "parameter_codes": [
        "00310",
        "00400",
        "00530",
        "00720",
        "50050",
        "50060",
        "51040",
        "81010",
        "81011"
      ],
      "count": 24,
      "representative_limit_value_ids": [
        "3610673282",
        "3610673290",
        "3610673269"
      ]
    }
  },
  "mechanically_computable": true
}
```

### T3 empty_numeric_limit

```json
{
  "parent": "empty_numeric_limit",
  "children": [
    {
      "id": "empty_limit_pass_fail_reporting",
      "exact_semantic_question": "When LIMIT_VALUE_NMBR is empty and DMR_COMMENT_TEXT encodes PASS=0/FAIL=1 reporting, is the row a numeric concentration limit or pass/fail reporting?",
      "expected_disposition": "SUPPORTED_RESOLUTION",
      "resolution": "Pass/fail reporting (non-numeric); not an ordinary concentration limit for numeric comparison."
    },
    {
      "id": "empty_limit_geometric_mean_reporting",
      "exact_semantic_question": "When LIMIT_VALUE_NMBR is empty and DMR_COMMENT_TEXT requires geometric-mean reporting of weekly values, is the row a per-period numeric limit or aggregated report-only monitoring?",
      "expected_disposition": "SUPPORTED_RESOLUTION",
      "resolution": "Aggregated report-only monitoring per permit footnotes; not a single-period numeric concentration limit in LIMIT_VALUE_NMBR."
    },
    {
      "id": "empty_limit_when_discharging",
      "exact_semantic_question": "When LIMIT_VALUE_NMBR is empty and DMR_COMMENT_TEXT is 'WHEN DISCHARGING.', is the row a numeric limit applicable regardless of discharge, or conditionally applicable monitoring?",
      "expected_disposition": "UNRESOLVED",
      "resolution": "Conditionally applicable monitoring/reporting; numeric limits for the same parameter may exist on sibling rows, but period-level applicability requires discharge-occurrence evidence not in structured sources."
    },
    {
      "id": "empty_limit_report_slot_blank_comment",
      "exact_semantic_question": "When LIMIT_VALUE_NMBR is empty and DMR_COMMENT_TEXT is blank, is the row report-only monitoring (per permit Report/N/A columns) or an unclassified data gap?",
      "expected_disposition": "SUPPORTED_RESOLUTION",
      "resolution": "For rows matched to permit Part I tables showing Report or N/A in the corresponding limit column, report-only monitoring with no numeric limit in that slot; where permit text is not retrieved, remains UNRESOLVED."
    }
  ],
  "why_necessary": "Retrieved evidence shows empty LIMIT_VALUE_NMBR is not semantically uniform across the 57 occurrences. Permit text and structured DMR comments establish at least four materially different obligation types (pass/fail encoding, geometric-mean reporting, when-discharging conditionality, and report-only permit slots with or without sibling numeric limits). A single parent answer would over-generalize and block Purpose A numeric comparison logic differently per partition.",
  "occurrence_partition": {
    "empty_limit_pass_fail_reporting": {
      "rule": "DMR_COMMENT_TEXT contains both 'PASS = 0' and 'FAIL = 1' (case-insensitive)",
      "count": 12,
      "permits": [
        "NM0020583"
      ]
    },
    "empty_limit_geometric_mean_reporting": {
      "rule": "DMR_COMMENT_TEXT contains 'GEOMETRIC MEAN' (case-insensitive) and not matched by pass_fail rule",
      "count": 15,
      "permits": [
        "NM0020583"
      ]
    },
    "empty_limit_when_discharging": {
      "rule": "DMR_COMMENT_TEXT contains 'WHEN DISCHARGING' (case-insensitive)",
      "count": 12,
      "permits": [
        "NM0028762"
      ]
    },
    "empty_limit_report_slot_blank_comment": {
      "rule": "DMR_COMMENT_TEXT is blank or whitespace only",
      "count": 18,
      "permits": [
        "NM0000116",
        "NM0020583"
      ]
    }
  },
  "mechanically_computable": true
}
```

### T3 document_authority

```json
{
  "parent": "document_authority",
  "children": [
    "document_establishment_role",
    "cross_document_governance"
  ],
  "why_necessary": "Retrieved texts answer two distinct questions with different evidence and residual limits. Establishment depends on each document's self-described role (issued authorization, draft rationale, incorporated appendix, or calculation support). Governance depends on the relationship between conflicting texts (issued versus proposed, incorporated versus standalone extract, or unsupported duplicate), and no single workspace rule resolves all pairwise conflicts among the 12 inventoried files.",
  "occurrence_partition": {
    "document_establishment_role": [
      "document_inventory.json"
    ],
    "cross_document_governance": [
      "document_inventory.json"
    ]
  },
  "mechanically_computable": {
    "document_establishment_role": "partially \u2014 detectable from document headers and phrases such as 'AUTHORIZATION TO DISCHARGE', 'FOR THE DRAFT', 'STATEMENT OF BASIS', 'Appendix A of Part II', and 'used to develop the proposed permit'; not fully computable for minor_modification or unlabeled extracts.",
    "cross_document_governance": "partially \u2014 issued-versus-draft and incorporation-by-reference relationships are text-detectable; no general pairwise precedence rule is available for all inventoried kinds."
  }
}
```

### T3 monitoring_frequency

```json
{
  "parent": "monitoring_frequency",
  "children": [
    "monitoring_frequency_periodic_codes",
    "monitoring_frequency_continuous_code",
    "monitoring_frequency_retest_codes"
  ],
  "why_necessary": "Retrieved evidence shows LIMIT_FREQ_OF_ANALYSIS_CODE values serve materially different obligation types. Most codes (05/WK, 01/07, 01/01, 02/07, 02/30, 01/90) align with calendar-period sampling frequencies stated in permit Part I tables when joined by permit and parameter. Code 99/99 appears only for continuous totalizing-meter flow, which is not a sample-count-per-period obligation. Code 09/99 appears only on WET retest parameter rows whose permit narrative describes conditional retesting after test failure rather than a fixed calendar schedule. Treating all codes as one homogeneous 'monitoring frequency' question obscures these distinct semantic contracts.",
  "occurrence_partition": {
    "monitoring_frequency_periodic_codes": [
      "05/WK",
      "01/07",
      "01/01",
      "02/07",
      "02/30",
      "01/90"
    ],
    "monitoring_frequency_continuous_code": [
      "99/99"
    ],
    "monitoring_frequency_retest_codes": [
      "09/99"
    ]
  },
  "mechanically_computable": true
}
```

## OBSERVED

Preferred: JUSTIFIED_FACTORIZATION into a small reusable set. Flag OVERFRAGMENTATION if dozens of children appear.

## HYPOTHESIS

Evidence contact should split only when consequences differ (e.g. comment families already split evaluator-side).
