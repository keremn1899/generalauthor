# Evidence packets

## MEASURED

### T1 nodi_c

candidates: [{'id': 'documented_no_discharge', 'label': 'NODI C documents that no discharge occurred during the monitoring period (permit-authorized no-discharge reporting).', 'status': 'not_established'}, {'id': 'conditional_monitoring_not_required', 'label': 'NODI C indicates monitoring was not required for the period (conditional/optional limit not applicable).', 'status': 'not_established_and_structurally_inconsistent', 'note': "All 150 FY2025 C-coded rows have OPTIONAL_MONITORING_FLAG='N'."}, {'id': 'other_authorized_no_data', 'label': 'NODI C marks another permit-authorized no-data reporting state (e.g., zero flow, not sampled, below quantification with authorized zero reporting).', 'status': 'not_established'}, {'id': 'missing_required_evidence', 'label': 'NODI C indicates required monitoring was reported without a numeric result and without an established no-data authorization for the period.', 'status': 'not_established'}, {'id': 'unresolved_code', 'label': 'NODI C is present in structured data but its semantic meaning cannot be resolved from workspace sources.', 'status': 'supported_by_absence_of_establishing_text'}]
n_retained: 7
limitations: ['No NODI codebook or NODI_CODE field legend appears in structured sources (dmr_measurements.csv, permit_limits.csv) or in the NM0000116 permit package documents inspected.', 'documents/gcc/final_permit.txt contains NetDMR reporting requirements but no definition of NODI codes and no NO DISCHARGE box instruction equivalent to other permits in the inventory.', 'Structural co-occurrence (C with empty DMR_VALUE_NMBR, single permit, batched parameters) identifies affected rows but is not a code legend per PASS_TASK and PRINCIPLES.', 'Facility discharge-infrequency narrative does not state that reporters use NODI C, or what C documents, for Purpose C classification.', 'External EPA NetDMR or national NODI dictionaries are out of scope and were not used.']

- `sources/dmr_measurements.csv` line 246 (representative row dmr_form_value_id=3896611092): EXTERNAL_PERMIT_NMBR=NM0000116, PARAMETER_CODE=50050, MONITORING_PERIOD_END_DATE=10/31/2024, DMR_VALUE_NMBR=(empty), OPTIONAL_MONITORING_FLAG=N, NODI_CODE=C
- `sources/dmr_measurements.csv` aggregated FY2025 filter (FY 2024-10-01 through 2025-09-30; empty DMR_VALUE_NMBR): 186 FY2025 no-numeric rows total; NODI_CODE distribution: C=150, 9=36. All 150 C rows: EXTERNAL_PERMIT_NMBR=NM0000116 only; OPTIONAL_MONITORING_FLAG=N for all; parameters {01105:40, 50050:20, 00400:20, 01040:20, 01042:20, 00530:20, 00900:10}; 10 monthly reporting events with 15 parameters each.
- `construction.py` lines 584-591: purpose.require_interpreted("nodi_code_semantics", relation="no_numeric_result_case", field="nodi_code", known=[""], purpose="C", per="measurement")
- `documents/gcc/final_permit.txt` Part I Section A, line 66: Flow                     Report MGD        Report MGD        ***               ***                1/Day        Estimate
- `documents/gcc/final_permit.txt` Part I Section B, lines 103-115: B.     REPORTING OF MONITORING RESULTS (MINOR DISCHARGERS)

Discharge Monitoring Report (DMR) results shall be electronically reported to EPA
per 40 CFR 127.16. To submit electronically, access the NetDMR website at
https://netdmr.epa.gov.
- `documents/gcc/final_permit.txt` Part II Section C, lines 196-197: 2. Discharges are restricted to overflows from the retention pond due to catastrophic or chronic
precipitation events.
- `documents/gcc/fact_sheet.txt` Section III, lines 126-127: In addition, because discharge is very infrequent, with the last
discharge occuring more than five years ago, it is impossible to have the permittee submit data

### T1 nodi_9

candidates: [{'id': 'standard_nodi_legend', 'statement': 'NODI code 9 is a standardized DMR no-data indicator with a fixed EPA/NetDMR label (e.g., a specific documented absence-of-data reason).', 'status': 'not_established', 'reason': 'No NODI code legend or glossary appears anywhere in workspace sources or permit-package documents.'}, {'id': 'optional_or_conditional_monitoring', 'statement': "NODI code 9 means monitoring or reporting was not required for the period (optional WET retest lines marked '(If required)', or TRC only when chlorine is used per footnote *5).", 'status': 'not_established', 'reason': 'Farmington permit text describes conditional monitoring contexts but never references NODI, code 9, or a DMR no-data indicator field tying those conditions to this code.'}, {'id': 'inherits_nodi_c', 'statement': 'NODI code 9 carries the same meaning as NODI code C seen on NM0000116 rows.', 'status': 'excluded', 'reason': 'Relation contract forbids inheriting C semantics for 9; codes appear on disjoint permits (NM0000116 vs NM0020583) with no cross-definition in workspace.'}, {'id': 'no_discharge', 'statement': 'NODI code 9 documents a no-discharge period.', 'status': 'not_established', 'reason': 'Farmington final permit contains no NO DISCHARGE DMR box instruction; workspace documents contain zero mentions of NODI or code 9.'}]
n_retained: 7
limitations: ["Workspace search found zero occurrences of 'NODI', 'No Data Indicator', or 'code 9' in any documents/ permit-package text.", "Structured sources contain no NODI codebook; only observed values are '' (empty), 'C' (150 FY2025 no-numeric rows on NM0000116), and '9' (36 FY2025 no-numeric rows on NM0020583).", 'All 36 NODI-9 rows are on permit NM0020583 spanning WET retest parameters (22415, 22416, 22418, 22419, 51443, 51444) and chlorine 50060; contextual permit conditions differ across parameter families but no workspace text maps NODI 9 to any of them.', 'Structural co-occurrence (optional monitoring flags, parameter types, empty numeric fields) cannot establish code semantics per PASS_TASK and PRINCIPLES.', 'EPA DMR Form 3320-1 general instructions (referenced by permit) are not in the workspace and cannot be cited.']

- `sources/dmr_measurements.csv` line 1 (header): ACTIVITY_ID,EXTERNAL_PERMIT_NMBR,...,DMR_VALUE_NMBR,...,NODI_CODE
- `sources/dmr_measurements.csv` line 2, DMR_FORM_VALUE_ID=3920662047: 3602878711,NM0020583,0,3600584105,TX1,EXO,...,22415,Whole effluent toxicity - retest #1,...,3920662047,C3,3832994492,,,,,,12/16/2024,9
- `sources/dmr_measurements.csv` line 246, DMR_FORM_VALUE_ID=3896611092: 3602720951,NM0000116,0,3600545262,001,EXO,...,50050,"Flow, in conduit or thru treatment plant",...,3896611092,Q2,3835977355,,,,,,01/28/2025,C
- `sources/permit_limits.csv` line PARAMETER_CODE=22415, EXTERNAL_PERMIT_NMBR=NM0020583: (PASS = 0  FAIL = 1) REPORT PASS AS '0' OR REPORT FAIL AS '1' IN CONCENTRATION MAX. ABOVE.  IF ALL TESTS PASS FOR THE FIRST YEAR OF THE PERMIT, THE FREQUENCY WILL BE REDUCED FOR YEARS 2-5 TO:  1/6 MONTHS FOR DAPHNIA PULEX & 1/YR FOR PIMEPHALES PROMELAS (SEE FOOTNOTE 9, PAGE 3 OF PART I OF PERMIT).
- `documents/farmington/final_permit.txt` Part I footnote *5, lines 117–120: *5      This facility uses Ultraviolet disinfection. Total Residual Chlorine (TRC) shall be monitored any time chlorine is used within the treatment plant for disinfection, equipment cleaning, maintenance, or any other purpose. The effluent limitation for TRC is the instantaneous maximum grab sample taken during periods of chlorine use and cannot be averaged for reporting purposes.
- `documents/farmington/final_permit.txt` Part II §3.c reporting table, lines 518–520: (If required) Retest 1 – Enter a “1” if the NOEC for         22418                 22415
        survival is less than the critical dilution,
        otherwise enter “0”.
- `documents/farmington/final_permit.txt` Part I §C.2, lines 198–201: All DMRs shall be electronically reported per 40 CFR 127.16. To submit electronically, access the NetDMR website at www.epa.gov/netdmr ... you must report on the Discharge Monitoring Report (DMR) Form EPA. No. 3320-1 in accordance with the "General Instructions" provided on the form.

### T1 when_discharging

candidates: [{'id': 'monitoring_conditional_on_discharge', 'statement': 'The comment qualifies monitoring-frequency obligations: the stated frequency applies only on days/periods when the outfall is discharging.', 'evidence_status': 'supported'}, {'id': 'limits_apply_when_discharge_occurs', 'statement': 'Numeric effluent limits remain applicable to effluent when a discharge occurs; the comment does not suspend or waive limit values.', 'evidence_status': 'supported'}, {'id': 'no_discharge_exempts_monitoring', 'statement': 'When no discharge occurs during a sampling month, monitoring for (*1)-marked parameters is not required; the permittee reports no discharge instead.', 'evidence_status': 'supported'}, {'id': 'optional_monitoring_flag_semantics', 'statement': 'WHEN DISCHARGING is encoded by OPTIONAL_MONITORING_FLAG=Y making the requirement optional.', 'evidence_status': 'refuted_by_structured_data'}, {'id': 'structured_discharge_occurrence', 'statement': 'Structured CSV fields alone establish whether discharge occurred in each monitoring period.', 'evidence_status': 'not_established'}]
n_retained: 7
limitations: ['All 17 structured occurrences belong to permit NM0028762 (Aztec); resolution is grounded in that permit package only.', 'Structured sources do not record whether discharge occurred in any FY2025 monitoring period; DMR rows for these limits show reported numeric values but do not distinguish discharge days within a month.', 'No NODI_CODE values appear in dmr_measurements.csv for NM0028762 rows, so structured data alone cannot demonstrate how no-discharge months were reported.', 'The permit does not define a machine-readable rule for aggregating monthly/quarterly statistics across partial discharge within a period (e.g., how many discharge days trigger weekly monitoring compliance).']

- `documents/aztec/final_permit.txt` Part I.A, lines 72-80 (monitoring table); footnotes lines 92-93: pH 00400 MINIMUM 6.6 MAXIMUM 9.0 MEASUREMENT FREQUENCY 1/Week (*1) Grab
Flow Report MGD Report MGD MEASUREMENT FREQUENCY 2/Week (*1) Estimate (*2)
Total Suspended Solids MEASUREMENT FREQUENCY 1/Week (*1) Grab
Total Residual Chlorine MEASUREMENT FREQUENCY 1/Day (*1) Grab
Cyanide, Total Recoverable MEASUREMENT FREQUENCY 1/Quarter (*1) Grab
Total Dissolved Solids MEASUREMENT FREQUENCY 1/Quarter (*1) 
- `documents/aztec/final_permit.txt` Part I.A.1, lines 56-66: 1. FINAL Effluent Limits – Outfall 001 – Intermittent Flow

During the period beginning the effective date of the permit and lasting to the permit expiration date (unless otherwise noted), the permittee is authorized to discharge backwash water to the lower Animas Ditch... Such discharges shall be limited and monitored by the permittee as specified below.
- `documents/aztec/final_permit.txt` Part I.C.5, lines 150-153: 5. NO DISCHARGE REPORTING

If there is no discharge from any outfall during the sampling month, place an "X" in the NO DISCHARGE box located in the upper right corner of the Discharge Monitoring Report.
- `documents/aztec/statement_of_basis.txt` Section 5 'Monitoring Frequency for Limited Parameters', lines 506-511: Flow shall be estimated daily when discharging. Estimated flow measurements are not subject to the accuracy provisions established at Part III.C.6 of the permit. The pollutant TRC shall be monitored daily when discharging by instantaneous grab which according to Part 136 is defined as analysis within 15 minutes of collection. pH shall continue to be monitored weekly when discharging. TDS and Cyani
- `documents/aztec/statement_of_basis.txt` Section II, lines 146-147: Filter backwash using potable water occurs from once per day to once every three to four days depending on the plant and the time of year.
- `documents/aztec/statement_of_basis.txt` Section VIII, lines 615-616: Effluent discharges flows are intermittent and are not directly discharged to Animas River.
- `sources/permit_limits.csv` row for LIMIT_VALUE_ID 3610840344 (representative of 17 rows): EXTERNAL_PERMIT_NMBR=NM0028762, LIMIT_SET_NAME=DISCHARGE BACKWASH WATER, DMR_COMMENT_TEXT=WHEN DISCHARGING., PARAMETER_CODE=00400, PARAMETER_DESC=pH, OPTIONAL_MONITORING_FLAG=N, LIMIT_FREQ_OF_ANALYSIS_CODE=01/07, LIMIT_TYPE_CODE=ENF

### T1 geometric_mean

candidates: [{'id': 'aggregate_before_compare', 'description': "Individual monitoring-period DMR values must not be compared directly to the limit; compliance requires computing a geometric mean over weekly sub-period samples and comparing that aggregate (or reporting it where limits say 'Report')."}, {'id': 'reporting_only', 'description': 'The comment governs only how values are reported on the DMR (geometric mean of weekly values) while numeric limits may still use a different statistic (e.g., 30-day average) for enforcement comparison.'}, {'id': 'limit_set_metadata_artifact', 'description': 'The geometric-mean comment is TDS-specific permit language propagated at limit-set level to unrelated parameters; it does not change comparison semantics for non-TDS limits.'}, {'id': 'unresolved', 'description': 'Structured sources do not establish how monthly DMR values relate to weekly geometric means or which aggregation window applies for limit comparison.'}]
n_retained: 8
limitations: ['No codebook or structured legend maps STATISTICAL_BASE_TYPE_CODE to geometric mean.', 'Weekly sub-period sample values are not present in dmr_measurements.csv; cannot verify whether reported monthly values are pre-aggregated geometric means.', "Only NM0020583 (farmington) permit documents were opened; all 40 occurrences belong to that permit's limit set 3600645646.", "Permit documents for aztec and gcc contain unrelated geometric-mean mentions (metals RP analysis, fecal coliform) not tied to this obligation's DMR_COMMENT_TEXT trigger."]

- `sources/permit_limits.csv` row LIMIT_VALUE_ID=3610673282, LIMIT_SET_SCHEDULE_ID=3600891019: DMR_COMMENT_TEXT=TOTAL DISSOLVED SOLIDS (TDS) MEASURED AT OUTFALL 001. REPORT THE GEOMETRIC MEAN VALUE OF THE WEEKLY VALUES.; PARAMETER_CODE=00310 (BOD); STATISTICAL_BASE_TYPE_CODE=AVG; LIMIT_FREQ_OF_ANALYSIS_CODE=05/WK
- `sources/permit_limits.csv` row LIMIT_VALUE_ID=3610673300, LIMIT_SET_SCHEDULE_ID=3600891019: DMR_COMMENT_TEXT=TOTAL DISSOLVED SOLIDS (TDS) MEASURED AT OUTFALL 001. REPORT THE GEOMETRIC MEAN VALUE OF THE WEEKLY VALUES.; PARAMETER_CODE=70295 (Solids, total dissolved); STATISTICAL_BASE_TYPE_CODE=AVG; LIMIT_VALUE_NMBR=497; LIMIT_VALUE_STANDARD_UNITS=497; LIMIT_FREQ_OF_ANALYSIS_CODE=01/07
- `documents/farmington/final_permit.txt` lines 80–82, 97–98, 121: Total Dissolved Solids, Discharge (*6) … Report … 1/Week … | Total Dissolved Solids, Net Increase (*8) … 497 mg/L … 1/Week | *6 Total dissolved solids measured at Outfall 001. Report the geometric mean value of weekly values.
- `documents/farmington/final_permit.txt` lines 123–124: *8 Net total dissolved solids calculated by taking the difference between Outfall 001 discharge and flow weighted average influent of the two drinking water treatment plants.
- `documents/farmington/statement_of_basis.txt` lines 521–522, 538: temporary 30-day average TDS net incremental increase limit of 497 mg/L … EPA … revised … TDS net incremental increase limit of 497 mg/L to 449 mg/L
- `documents/farmington/statement_of_basis.txt` lines 373–374: primary contact designated use of the receiving stream are the monthly geometric mean of E. coli bacteria of 126 cfu/100 mL … and single sample of 410 cfu/100 mL
- `sources/dmr_measurements.csv` row DMR_FORM_VALUE_ID=3831416442, LIMIT_VALUE_ID=3610673282, MONITORING_PERIOD_END_DATE=10/31/2024: PARAMETER_CODE=00310 (BOD); DMR_VALUE_STANDARD_UNITS=4; LIMIT_VALUE_STANDARD_UNITS=30; STATISTICAL_BASE_TYPE_CODE=AVG; DMR_VALUE_QUALIFIER_CODE==
- `sources/dmr_measurements.csv` row DMR_FORM_VALUE_ID=3831416458, LIMIT_VALUE_ID=3610673300, MONITORING_PERIOD_END_DATE=10/31/2024: PARAMETER_CODE=70295 (Solids, total dissolved); DMR_VALUE_STANDARD_UNITS=269; LIMIT_VALUE_STANDARD_UNITS=497; STATISTICAL_BASE_TYPE_CODE=AVG; DMR_VALUE_QUALIFIER_CODE==

### T1 pass_fail

candidates: [{'label': 'binary_wet_outcome_code', 'description': '0 and 1 are categorical pass/fail codes for whole-effluent-toxicity test outcome. 0 = pass (NOEC at or above critical dilution); 1 = fail (NOEC below critical dilution). Values are entered in the DMR concentration-max field but do not represent a measured concentration magnitude.', 'supported_by': ['DMR_COMMENT_TEXT pass/fail legend on all 12 affected limit rows', 'final_permit.txt Part II reporting table for TEM3D/TEM6C and retest codes', '9A pass=0;fail=1 unit on pass/fail limit rows with empty LIMIT_VALUE_NMBR']}, {'label': 'numeric_concentration_comparison', 'description': 'Reported 0/1 values are pollutant concentrations (mg/L, %, etc.) compared numerically against LIMIT_VALUE_NMBR.', 'supported_by': [], 'refuted_by': ['DMR comment explicitly defines 0/1 as pass/fail codes, not concentrations', 'Pass/fail parameters have no numeric LIMIT_VALUE_NMBR; companion TOM3D/TOM6C parameters carry numeric NOEC reporting separately']}, {'label': 'shared_comment_different_reporting_regimes', 'description': 'All 12 rows share the PASS=0/FAIL=1 comment at the limit-set level, but only TEM/retest parameters (8 rows) use binary 0/1 reporting; TOM3D/TOM6C/TQM3D/TQM6C (4 rows) report numeric NOEC or coefficient-of-variation values per separate permit instructions.', 'supported_by': ['permit_limits.csv rows 101–106 show TOM/TQM parameters with 23% limits under same comment', 'final_permit.txt distinguishes pass/fail entry (TEM codes) from NOEC concentration reporting (TOM codes)']}]
n_retained: 8
limitations: ['Critical dilution magnitude is not stated in the inspected structured rows; only the comparison logic (NOEC vs critical dilution) is established from permit text.', 'Four of twelve affected limit rows (TOM3D, TOM6C, TQM3D, TQM6C) share the PASS=0/FAIL=1 comment but are governed by separate numeric-reporting instructions; the pass/fail legend applies to TEM and retest parameters, not to those four.', 'Sublethal retest parameters (22418, 22419) use the same 0/1 coding in structured data; permit retest table text inspected references survival NOEC vs critical dilution for retest 1–3.']

- `sources/permit_limits.csv` row LIMIT_VALUE_ID=3610839676, PARAMETER_CODE=22415: (PASS = 0  FAIL = 1) REPORT PASS AS '0' OR REPORT FAIL AS '1' IN CONCENTRATION MAX. ABOVE.
- `sources/permit_limits.csv` row LIMIT_VALUE_ID=3610839682, PARAMETER_CODE=TEM3D: LIMIT_VALUE_NMBR=empty; LIMIT_UNIT_CODE=9A; STANDARD_UNIT_DESC=pass=0;fail=1; PARAMETER_DESC=Low Flow Pass/Fail Static Renewal 48Hr Acute Daphnia pulex
- `sources/permit_limits.csv` row LIMIT_VALUE_ID=3610839684, PARAMETER_CODE=TOM3D: LIMIT_VALUE_NMBR=23; LIMIT_UNIT_CODE=23; STANDARD_UNIT_DESC=%; PARAMETER_DESC=NOAEC Lethal Statis Renewal 48 Hr Acute Daphnia pulex
- `sources/dmr_measurements.csv` row DMR_FORM_VALUE_ID=3832994493, LIMIT_VALUE_ID=3610839682, MONITORING_PERIOD_END=2024-11-30: DMR_VALUE_NMBR=0; DMR_VALUE_STANDARD_UNITS=9A; limit/standard unit desc pass=0;fail=1; DMR_VALUE_QUALIFIER_CODE==
- `documents/farmington/final_permit.txt` Part II, lines 512–514, reporting table: Enter a "1" if the No Observed Effect Concentration (NOEC) for survival is less than the critical dilution, otherwise enter a "0".
- `documents/farmington/final_permit.txt` Part II, lines 518–520, retest reporting row: (If required) Retest 1 – Enter a "1" if the NOEC for survival is less than the critical dilution, otherwise enter "0".
- `documents/farmington/final_permit.txt` Part II, line 515, reporting table: Report the NOEC value for survival                          TOM3D                 TOM6C
- `documents/farmington/final_permit.txt` Part II, lines 390–393, NOEC and failure definitions: Acute test failure is defined as a demonstration of a statistically significant lethal effect at test completion to a test species at or below the critical dilution

### T1 empty_numeric_limit

candidates: [{'label': 'numeric_limit', 'statement': 'Empty LIMIT_VALUE_NMBR still denotes an enforceable numeric effluent limit row suitable for numeric comparison once the value is recovered from elsewhere.'}, {'label': 'report_only_monitoring', 'statement': "Empty LIMIT_VALUE_NMBR denotes a monitoring/reporting requirement without a numeric effluent limit for that statistical-base cell (permit table 'Report' or equivalent)."}, {'label': 'non_applicable_limit_column', 'statement': 'Empty LIMIT_VALUE_NMBR marks a non-applicable limit-table column (for example N/A mass-load base) while a sibling row carries the numeric limit for comparison.'}, {'label': 'special_non_numeric_reporting', 'statement': 'Empty LIMIT_VALUE_NMBR marks a non-standard reporting obligation (pass/fail WET encoding or geometric-mean aggregated reporting) that is not an ordinary numeric concentration limit.'}]
n_retained: 8
limitations: ['No ICIS/NPDES codebook or field legend in the workspace defines LIMIT_VALUE_NMBR emptiness semantics directly.', 'PASS=0/FAIL=1 instructions for WET retest rows appear in structured DMR_COMMENT_TEXT but were not found in the extracted farmington final_permit.txt text searched within budget.', 'Only 3 of 12 permit-package documents were opened; not every empty-limit row was individually matched to permit-table text.', 'FY2025 DMR measurements contain zero rows with empty LIMIT_VALUE_NMBR, so Purpose A comparison blocking is inferred from permit_limit structure rather than observed FY2025 DMR joins.']

- `sources/permit_limits.csv` row LIMIT_VALUE_ID=3610129901|LIMIT_SET_SCHEDULE_ID=3600833510 alongside sibling 3610129867|3600833510: 3610129867,C3,50,19,mg/L,19,mg/L,50,DD,MAX,<=,,ENF ... 3610129901,C2,,19,mg/L,19,mg/L,,3C,AVG,,,ENF (both Solids, total suspended; AVG row has empty LIMIT_VALUE_NMBR and empty LIMIT_VALUE_QUALIFIER_CODE; MAX sibling has 50 and <=)
- `documents/gcc/final_permit.txt` Part I effluent limit table, lines 68-74: Total Suspended          N/A               N/A               Report            50                 1/Week               Grab
Solids
Total Copper             N/A               N/A               0.011             0.011              1/Week               Grab
Dissolved Copper         N/A               N/A               Report            Report             1/Week               Grab
Dissolved Cadmium    
- `sources/permit_limits.csv` row LIMIT_VALUE_ID=3610840340|LIMIT_SET_SCHEDULE_ID=3600904607 with siblings on LIMIT_ID=3606351871: 3610840340,Q1,,26,lb/d,01,kg/d,,MK,AVG,,,ENF ... DMR_COMMENT_TEXT=WHEN DISCHARGING. ... sibling 3610840342,C2,20,19,mg/L,19,mg/L,20,3C,AVG,<=,,ENF ... sibling 3610840343,C3,30,19,mg/L,19,mg/L,30,DD,MAX,<=,,ENF
- `documents/aztec/final_permit.txt` Part I table lines 79 and footnote lines 92-93: Total Suspended Solids                 N/A              N/A          20                30       1/Week (*1)         Grab
...
*1 When discharging.
- `sources/permit_limits.csv` row LIMIT_VALUE_ID=3610839676|LIMIT_SET_SCHEDULE_ID=3600904539: PARAMETER_DESC=Whole effluent toxicity - retest #1 ... LIMIT_VALUE_NMBR= ... LIMIT_UNIT_DESC=pass=0;fail=1 ... STANDARD_UNIT_DESC=pass=0;fail=1 ... DMR_COMMENT_TEXT=(PASS = 0  FAIL = 1) REPORT PASS AS '0' OR REPORT FAIL AS '1' IN CONCENTRATION MAX. ABOVE.
- `documents/farmington/final_permit.txt` Part I table lines 87-92: Cadmium                        N/A             N/A            N/A            N/A          N/A         Report       1/Quarter            Grab
2,3,7,8-TCDD Dioxin            N/A             N/A            N/A            N/A          N/A         Report       1/Quarter            Grab
Pentachlorophenol              N/A             N/A            N/A            N/A          N/A         Report       1/Q
- `documents/farmington/final_permit.txt` Part I TDS table lines 97-98 and footnote line 121: Total Dissolved Solids, Net     27,664 lbs/day      Report           N/A          497 mg/L          Report         N/A        1/Week    12-Hour
...
*6      Total dissolved solids measured at Outfall 001. Report the geometric mean value of weekly values.
- `sources/permit_limits.csv` aggregate over 57 rows with empty LIMIT_VALUE_NMBR: 57/105 permit_limits rows have empty LIMIT_VALUE_NMBR; all have LIMIT_TYPE_CODE=ENF; all have empty LIMIT_VALUE_QUALIFIER_CODE; partition by DMR_COMMENT_TEXT: blank 18, WHEN DISCHARGING. 12, PASS=0/FAIL=1 12, geometric mean 15; zero rows have nonempty LIMIT_VALUE_STANDARD_UNITS when LIMIT_VALUE_NMBR is empty.

### T1 document_authority

candidates: [{'id': 'filename_kind_hierarchy', 'statement': 'document_inventory.json document_kind values (final_permit > fact_sheet > reasonable_potential, etc.) determine both content authority and conflict precedence.', 'status': 'refuted_by_evidence', 'reason': 'Farmington inventory entry document_kind=statement_of_basis opens with a FACT SHEET header; GCC fact_sheet and Aztec statement_of_basis both use draft/proposed framing. No workspace text ranks kinds.'}, {'id': 'issued_permit_self_defined_corpus', 'statement': 'The issued permit text defines its own governing corpus (cover-page Parts I–III/IV and internally cross-referenced appendices). Supporting package documents explain draft/proposed rationale and calculations but defer enforceable limitations to the issued permit.', 'status': 'supported_by_evidence', 'reason': "Final-permit cover pages authorize discharge only under named parts 'hereof'; supporting docs label content as draft/proposed and point to the draft/issued permit for limitations."}, {'id': 'all_documents_co_equal', 'statement': 'All twelve inventoried files are independently binding with no precedence rule.', 'status': 'refuted_by_evidence', 'reason': 'Fact sheets and statements of basis explicitly discuss proposed/draft conditions and administrative record, not standalone authorization.'}, {'id': 'explicit_conflict_clause_required', 'statement': "Precedence is unknowable unless a workspace file contains an explicit 'in the event of conflict' clause between package documents.", 'status': 'partially_supported_limitation', 'reason': 'No explicit inter-document conflict clause was found, but issued-permit self-definition plus supporting-document draft framing still establishes functional precedence without a named conflict rule.'}]
n_retained: 8
limitations: ["No workspace text states an explicit 'in the event of conflict between [document A] and [document B], [X] shall prevail' rule across all inventoried file types.", 'documents/gcc/minor_modification.txt was not shown by retrieved text to be incorporated by reference into documents/gcc/final_permit.txt; its standalone authority relative to the issued permit remains unestablished.', 'Reasonable-potential and fact-sheet/statement-of-basis narrative may still contain condition-relevant facts (e.g., discharge occurrence, seasonal triggers) that must be read from permit parts to resolve Purposes B and C; this packet resolves document authority, not every conditional monitoring obligation.', 'document_inventory.json associates documents with permits but provides no precedence or incorporation metadata beyond kind labels and hashes.']

- `documents/gcc/final_permit.txt` lines 19-21, cover page: in accordance with this cover page and effluent limitations, monitoring requirements, and other conditions set forth in Parts I [Requirements for NPDES Permits], II [Other Conditions], and III [Standard Conditions for NPDES Permits] hereof.
- `documents/farmington/final_permit.txt` lines 24-25, cover page: in accordance with this cover page and the effluent limitations, monitoring requirements, and other conditions set forth in Part I, Part II, Part III, and Part IV hereof.
- `documents/gcc/final_permit.txt` lines 149-150, Part II: Current EPA Region 6 minimum quantification levels (MQLs) for reporting and compliance are provided in Appendix A of Part II of this permit.
- `documents/gcc/fact_sheet.txt` line 191, Section V title: V.     DRAFT PERMIT RATIONALE AND PROPOSED PERMIT CONDITIONS
- `documents/gcc/fact_sheet.txt` lines 504-506, Section XV: XV.     FINAL DETERMINATION

The public notice describes the procedures for the formulation of final determinations.
- `documents/aztec/statement_of_basis.txt` lines 556-558, Section F: F.       FINAL EFFLUENT LIMITATIONS

See the draft permit for limitations.
- `documents/aztec/reasonable_potential.txt` lines 12-14: STEP 1:             REFERENCE IMPLEMENTATION PROCEDURES                                   APPENDIX A
                    INPUT FACILITY AND RECEIVING STREAM DATA                                of FACT SHEET
- `documents/farmington/statement_of_basis.txt` lines 1-3, header: PERMIT NO. NM0020583                    FACT SHEET                             Page 1

                                FACT SHEET

### T1 monitoring_frequency

candidates: [{'id': 'calendar_count_over_period', 'statement': 'For calendar codes, LIMIT_FREQ_OF_ANALYSIS_CODE has the form NN/PP where NN is the number of required analyses and PP is a period token (01=day, 07=week, 30=month, 90=quarter, WK=week count literal), as inferred from permit-text frequency paired to the same permit and parameter.', 'codes_supported_in_workspace': {'05/WK': "five analyses per week (permit text: 'Five/Week' or '5/Week')", '01/07': "one analysis per week (permit text: '1/Week')", '01/01': "one analysis per day (permit text: '1/Day' or 'Daily')", '02/07': "two analyses per week (permit text: '2/Week')", '01/90': "one analysis per quarter (permit text: '1/Quarter' or 'Once/Quarter')", '02/30': "two analyses per month (permit text: '2/month')"}, 'evidence_basis': 'Permit Part I tables name MEASUREMENT FREQUENCY in plain language for the same EXTERNAL_PERMIT_NMBR and PARAMETER_CODE as structured rows; no workspace file states the NN/PP rule explicitly.'}, {'id': 'continuous_flow', 'statement': '99/99 denotes continuous monitoring (not a periodic sample count), as used for NM0020583 flow with sample type Totalizing Meter.', 'codes_supported_in_workspace': {'99/99': 'continuous flow monitoring'}, 'evidence_basis': "Permit text says 'Continuous' for flow; structured row carries 99/99. Literal code string absent from documents."}, {'id': 'conditional_retest', 'statement': "09/99 denotes conditional WET retest reporting triggered by test failure ('If required'), not a fixed calendar sampling frequency.", 'codes_supported_in_workspace': {'09/99': 'report only when retest required after WET failure'}, 'evidence_basis': "Permit retest table labels rows '(If required) Retest N'; structured WET retest parameters carry 09/99. Literal code string absent from documents."}, {'id': 'unresolved_no_legend', 'statement': 'Codes cannot be interpreted from workspace sources alone because no in-workspace codebook defines LIMIT_FREQ_OF_ANALYSIS_CODE and permit documents never print the opaque tokens.', 'evidence_basis': 'PASS_TASK constraint; grep of documents/ finds zero literal code matches.'}]
n_retained: 8
limitations: ['No workspace file defines LIMIT_FREQ_OF_ANALYSIS_CODE as a field or prints the opaque code strings; interpretation relies on permit-parameter crosswalk, which PASS_TASK cautions is not itself a code legend.', "Sentinel codes 99/99 and 09/99 never appear in document text; their meanings are inferred only from row pairing with 'Continuous' and 'If required' retest language.", 'The general NN/PP encoding convention is not stated authoritatively anywhere in the workspace.', 'Coverage is limited to three permits (NM0000116, NM0020583, NM0028762); codes are only exemplified for parameters present in this dataset.', "Conditional footnotes (e.g., aztec '*1 When discharging') modulate when monitoring applies but are separate from the code-to-frequency mapping."]

- `documents/farmington/final_permit.txt` lines 56–86: pH ... Five/Week (*1) ... Biochemical Oxygen ... 5/Week (*1) ... Total Residual Chlorine ... Daily ... Total Dissolved Solids ... 1/Week ... Cyanide ... 2/month ... Cadmium ... 1/Quarter
- `documents/farmington/final_permit.txt` line 63: Flow ... Continuous ... Totalizing Meter
- `documents/farmington/final_permit.txt` lines 518–523: (If required) Retest 1 – Enter a “1” if the NOEC for survival is less than the critical dilution, otherwise enter “0”. ... 22418 ... 22415 ... (If required) Retest 2 ... 22419 ... 22416
- `documents/gcc/final_permit.txt` lines 57–74: pH ... 1/Day ... Flow ... 1/Day ... Total Suspended Solids ... 1/Week ... Total Aluminum ... 1/Week ... Total Copper ... 1/Week
- `documents/aztec/final_permit.txt` lines 72–82: pH ... 1/Week (*1) ... Flow ... 2/Week (*1) ... Total Suspended Solids ... 1/Week (*1) ... Total Residual Chlorine ... 1/Day (*1) ... Cyanide, Total Recoverable ... 1/Quarter (*1) ... Total Dissolved Solids ... 1/Quarter (*1)
- `documents/farmington/statement_of_basis.txt` lines 638–644: BOD5 and TSS, are proposed to be monitored five times per week, with sampling on at least five different days. ... monitoring frequencies of daily for TRC and five times per week for E. coli, pH and flow are consistent with the previous permit. Report requirements of once per week for TDS is also consistent with the previous permit.
- `documents/gcc/fact_sheet.txt` lines 345–348: Based on the discharge frequency of the facility, the NMIP requires that pH has daily monitoring frequency and all other limited parameters have weekly monitoring frequency requirements. Flow is proposed to be monitored daily by estimate.
- `sources/permit_limits.csv` header + representative rows (e.g. NM0020583 pH 00400 → 05/WK; NM0000116 pH 00400 → 01/01; NM0028762 flow 50050 → 02/07): LIMIT_FREQ_OF_ANALYSIS_CODE is a populated field on every permit limit row; eight distinct values appear (01/07, 01/90, 05/WK, 01/01, 09/99, 02/30, 99/99, 02/07) with no accompanying code-definition column.

### T2 nodi_c

candidates: [{'label': 'documented_no_discharge_period', 'description': 'NODI C indicates the permittee reported that no discharge occurred for the monitoring period, excusing numeric pollutant/flow values.'}, {'label': 'conditional_monitoring_not_required', 'description': 'NODI C indicates monitoring was not required because the conditional limit set (storm-runoff discharge) did not apply for the period.'}, {'label': 'other_documented_no_data_state', 'description': 'NODI C indicates some other EPA/ICIS-standard no-data reason distinct from missing required evidence.'}, {'label': 'missing_required_monitoring_evidence', 'description': 'NODI C is merely a placeholder for absent numeric reporting while monitoring remained required (OPTIONAL_MONITORING_FLAG=N).'}]
n_retained: 8
limitations: ['No NODI code definition or legend appears anywhere in sources/ or documents/; only the CSV field NODI_CODE carries the value C.', 'All 150 occurrences are on permit NM0000116; permit-package text for that permit does not define ICIS NODI codes.', 'Structural correlation with storm-runoff limits and empty numeric fields is not a code legend per workspace rules.', 'External EPA ICIS/NODI documentation is out of scope and was not used.']

- `sources/dmr_measurements.csv` row dmr_form_value_id=3896611092 (representative); lines 246-249: EXTERNAL_PERMIT_NMBR=NM0000116, PARAMETER_CODE=50050, MONITORING_PERIOD_END_DATE=10/31/2024, DMR_VALUE_NMBR= (empty), NODI_CODE=C
- `sources/dmr_measurements.csv` aggregate query over all rows with NODI_CODE=C and empty DMR_VALUE_NMBR: 150 rows; all EXTERNAL_PERMIT_NMBR=NM0000116; all FY2025 monitoring periods; no other NODI codes share this C+empty-value pattern besides separate NODI 9 rows on NM0020583
- `sources/permit_limits.csv` rows limit_value_id 3610129868-3610129869; lines 58-59: EXTERNAL_PERMIT_NMBR=NM0000116, LIMIT_SET_NAME=DISCHARGE STORM RUNOFFS FROM STORAGE, PARAMETER_DESC=Flow in conduit or thru treatment plant, OPTIONAL_MONITORING_FLAG=N, LIMIT_FREQ_OF_ANALYSIS_CODE=01/01
- `documents/gcc/final_permit.txt` Part II.B Authorized Discharges; Part II.C items 2-4; lines 182-203: Discharges are restricted to overflows from the retention pond due to catastrophic or chronic precipitation events. ... If a discharge of storm runoff from a quarry (mining) area is necessary, the discharge must comply with effluent limitations established at Outfall 001.
- `documents/gcc/fact_sheet.txt` Section on Cadmium; lines 322-324: As previously described the permittee has not discharged in over five years and is unable to obtain a sample to analyze at the appropriate detection level.
- `documents/gcc/final_permit.txt` Part I.B Reporting of Monitoring Results; lines 103-115: Discharge Monitoring Report (DMR) results shall be electronically reported to EPA per 40 CFR 127.16. ... Monitoring information shall be submitted quarterly.
- `documents/aztec/final_permit.txt` Part I item 5 NO DISCHARGE REPORTING; lines 150-153: If there is no discharge from any outfall during the sampling month, place an "X" in the NO DISCHARGE box located in the upper right corner of the Discharge Monitoring Report.
- `OBLIGATION.md` known_structured_evidence field: structured CSVs + document inventory; no codebook table in structured sources

### T2 nodi_9

candidates: [{'label': 'Monitoring not required / not applicable for optional WET retest lines', 'basis': "NODI=9 appears on optional (OPTIONAL_MONITORING_FLAG=Y) WET retest parameters whose permit reporting table labels retests '(If required)'.", 'workspace_status': 'Permit explains when retest values may be omitted from reporting logic but never names NODI code 9 or equates omission to code 9.'}, {'label': 'Conditional TRC monitoring not triggered (chlorine not used)', 'basis': 'NODI=9 appears on daily TRC rows (parameter 50060) while footnote *5 requires TRC monitoring only when chlorine is used.', 'workspace_status': 'Footnote establishes a conditional monitoring obligation but does not define NODI code 9 or state which DMR no-data code applies when chlorine is unused.'}, {'label': 'No discharge (same as NODI code C)', 'basis': 'Other no-result rows in the dataset use NODI=C at a different permit (NM0000116); aztec permit text describes a NO DISCHARGE box on the DMR form.', 'workspace_status': 'Rejected by relation contract and occurrence partition: all 36 NODI=9 rows are NM0020583; all 150 NODI=C rows are NM0000116. No workspace text maps code 9 to no discharge.'}, {'label': 'Missing required monitoring evidence', 'basis': 'Empty numeric field with a nonempty no-data code could indicate unreported required data.', 'workspace_status': 'Cannot be established or ruled out from structured fields alone; no code legend distinguishes deficiency from permitted omission.'}]
n_retained: 8
limitations: ['No NODI code definition, DMR form EPA 3320-1 general instructions, or ICIS codebook appears anywhere in the workspace.', 'LIMIT_FREQ_OF_ANALYSIS_CODE value 09/99 appears only in structured CSVs with no document legend.', 'Pass/fail WET reporting semantics for retest parameters are separately unresolved in construction.py.', 'Discharge occurrence for conditional limits is not established from structured sources.', 'Training-data or EPA-wide NODI legends are out of scope per PASS_TASK.md.']

- `sources/dmr_measurements.csv` header row + NODI_CODE='9' rows (36 total); representative FY2025 rows dmr_form_value_id 3920662047, 3920662059, 3920662071, 3920662083: NODI_CODE column present. All 36 rows with NODI_CODE='9' have empty DMR_VALUE_NMBR, EXTERNAL_PERMIT_NMBR=NM0020583. Parameters: 50060 (12 rows, OPTIONAL_MONITORING_FLAG=N, LIMIT_FREQ_OF_ANALYSIS_CODE=01/01); WET retest parameters 22415/22416/22418/22419/51443/51444 (24 rows, OPTIONAL_MONITORING_FLAG=Y, LIMIT_FREQ_OF_ANALYSIS_CODE=09/99). No other NODI codes share this 9/optional-WET-retest partiti
- `sources/dmr_measurements.csv` NODI_CODE='C' rows (150 total) contrast: All 150 rows with NODI_CODE='C' and empty DMR_VALUE_NMBR have EXTERNAL_PERMIT_NMBR=NM0000116 (GCC), OPTIONAL_MONITORING_FLAG=N, and parameters including flow, pH, copper, and aluminum — disjoint from every NODI=9 row.
- `sources/permit_limits.csv` parameter 22415 limit row, LIMIT_VALUE_ID 3610839676: PARAMETER_CODE=22415, PARAMETER_DESC='Whole effluent toxicity - retest #1', OPTIONAL_MONITORING_FLAG=Y, LIMIT_FREQ_OF_ANALYSIS_CODE=09/99, DMR_COMMENT_TEXT='(PASS = 0  FAIL = 1) REPORT PASS AS '0' OR REPORT FAIL AS '1' IN CONCENTRATION MAX. ABOVE. ...'
- `sources/permit_limits.csv` parameter 50060 limit row, LIMIT_VALUE_ID 3610673291: PARAMETER_CODE=50060, PARAMETER_DESC='Chlorine, total residual', OPTIONAL_MONITORING_FLAG=N, LIMIT_FREQ_OF_ANALYSIS_CODE=01/01, LIMIT_FREQ sample type GR (grab), daily frequency months all Y.
- `documents/farmington/final_permit.txt` Part I, footnote *5 (lines 117–120): *5      This facility uses Ultraviolet disinfection. Total Residual Chlorine (TRC) shall be monitored any time chlorine is used within the treatment plant for disinfection, equipment cleaning, maintenance, or any other purpose. The effluent limitation for TRC is the instantaneous maximum grab sample taken during periods of chlorine use and cannot be averaged for reporting purposes.
- `documents/farmington/final_permit.txt` Part II §D.3 REPORTING, retest table (lines 506–526): c. The permittee shall submit the results of each valid toxicity test on the subsequent monthly DMR for that reporting period as follows below. ... (If required) Retest 1 – Enter a "1" if the NOEC for survival is less than the critical dilution, otherwise enter "0". ... Parameter STORET CODE ... 22418 ... 22415
- `construction.py` _declare_purpose_requirements, nodi_code_semantics requirement (lines 584–590): purpose.require_interpreted('nodi_code_semantics', relation='no_numeric_result_case', field='nodi_code', known=[''], purpose='C', per='measurement')
- `OBLIGATION.md` known_structured_evidence field: known_structured_evidence: structured CSVs + document inventory; no codebook table in structured sources

### T2 when_discharging

candidates: [{'interpretation': 'Monitoring frequencies and associated effluent-limit compliance obligations apply only during periods when the permittee is actually discharging; no-discharge periods require no parameter monitoring and instead use NO DISCHARGE DMR reporting.', 'status': 'supported'}, {'interpretation': 'The comment is informational only and does not change whether monitoring is required in a given period.', 'status': 'refuted'}, {'interpretation': 'The comment converts the requirement into optional monitoring (equivalent to OPTIONAL_MONITORING_FLAG = Y).', 'status': 'refuted'}, {'interpretation': 'Effluent numeric limits are voided entirely regardless of discharge occurrence.', 'status': 'refuted'}]
n_retained: 7
limitations: ['All 17 structured occurrences are for permit NM0028762 only; resolution is grounded in the aztec permit package and may not generalize to other permits not in the workspace.', 'Structured sources contain no codebook defining DMR_COMMENT_TEXT; the semantic link between the CSV comment and permit footnote *1 is established by textual correspondence in the NM0028762 permit package, not by a structured legend.', 'Whether discharge actually occurred during any specific FY2025 monitoring period is not established from structured DMR data: 140 FY2025 measurement rows for these limit_value_ids all have blank NODI_CODE and numeric DMR_VALUE_NMBR, providing no structured no-discharge signal.', "Per-period discharge occurrence remains a separate factual question outside the comment's definitional meaning."]

- `documents/aztec/final_permit.txt` lines 56–66, 72–80: 1. FINAL Effluent Limits – Outfall 001 – Intermittent Flow
...
pH 00400 MINIMUM 6.6 MAXIMUM 9.0 1/Week (*1) Grab
...
Flow Report MGD Report MGD *** *** 2/Week (*1) Estimate (*2)
Total Suspended Solids N/A N/A 20 30 1/Week (*1) Grab
Total Residual Chlorine N/A N/A N/A 11 µg/L 1/Day (*1) Grab
- `documents/aztec/final_permit.txt` lines 92–94: Footnotes:
*1 When discharging.
*2 "Estimate" flow measurements shall not be subject to the accuracy provisions established at Part III.C.6. Flow may be estimated using sound analytical techniques.
- `documents/aztec/final_permit.txt` lines 150–153: 5. NO DISCHARGE REPORTING

If there is no discharge from any outfall during the sampling month, place an "X" in the NO
DISCHARGE box located in the upper right corner of the Discharge Monitoring Report.
- `documents/aztec/statement_of_basis.txt` lines 506–511: Flow shall be estimated daily when discharging. Estimated flow measurements are not subject to
    the accuracy provisions established at Part III.C.6 of the permit. The pollutant TRC shall be
    monitored daily when discharging by instantaneous grab which according to Part 136 is defined
    as analysis within 15 minutes of collection. pH shall continue to be monitored weekly when
    dischargin
- `documents/aztec/statement_of_basis.txt` lines 146–147: Filter backwash using potable water occurs from once per day to once every three to four days
depending on the plant and the time of year.
- `sources/permit_limits.csv` row LIMIT_VALUE_ID=3610840344 (representative of 17 rows): EXTERNAL_PERMIT_NMBR=NM0028762, LIMIT_SET_NAME=DISCHARGE BACKWASH WATER, DMR_COMMENT_TEXT=WHEN DISCHARGING., PARAMETER_CODE=00400 (pH), OPTIONAL_MONITORING_FLAG=N, LIMIT_FREQ_OF_ANALYSIS_CODE=01/07
- `sources/permit_limits.csv` aggregate over 17 rows with DMR_COMMENT_TEXT containing WHEN DISCHARGING: 17 rows; all EXTERNAL_PERMIT_NMBR=NM0028762; limit sets: DISCHARGE BACKWASH WATER (A, 11 rows) and QUARTERLY REPORTING (Q, 6 rows); all OPTIONAL_MONITORING_FLAG=N

### T2 geometric_mean

candidates: [{'id': 'aggregate_before_compare', 'statement': 'The comment requires computing the geometric mean of weekly values within the applicable reporting period and comparing that aggregate (or a net value derived from such aggregates) to effluent limits, rather than treating an individual DMR monitoring-period value as the compliance comparison quantity.'}, {'id': 'reporting_only', 'statement': 'The comment governs how values are reported on the DMR but does not alter which numeric quantity is compared to effluent limits.'}, {'id': 'applies_to_all_comment_rows', 'statement': "Every permit_limit row whose DMR_COMMENT_TEXT contains 'GEOMETRIC MEAN'—including BOD, E. coli, pH, and other non-TDS parameters—requires geometric-mean aggregation before limit comparison."}, {'id': 'ordinary_single_period', 'statement': 'Individual monitoring-period DMR values may be compared directly to permit limits despite the geometric-mean comment.'}]
n_retained: 8
limitations: ['Only documents/farmington/final_permit.txt was opened; permit narrative for NM0020583 is authoritative for footnote *6 but was not cross-checked against every parameter named in the 40 structured rows.', "Permit footnote *6 states reporting requirement ('Report the geometric mean value of weekly values') but does not use the word 'compare'; linkage to limit comparison is inferred from weekly aggregation context and net-TDS calculation footnotes, not an explicit 'compare geometric mean to limit' sentence.", 'Parent obligation cannot receive a single disposition without REFINEMENT because structured occurrences conflate TDS-specific geometric-mean reporting with misattached limit-set comment rows for other parameters.']

- `documents/farmington/final_permit.txt` Part I limit table, Total Dissolved Solids Discharge (*6): Total Dissolved Solids,
                              Report          Report          N/A          Report        Report        N/A          1/Week
Discharge (*6)                                                                                                                       Composite
- `documents/farmington/final_permit.txt` Footnotes, *6: *6      Total dissolved solids measured at Outfall 001. Report the geometric mean value of weekly values.
- `documents/farmington/final_permit.txt` Footnotes, *8: *8      Net total dissolved solids calculated by taking the difference between Outfall 001 discharge and flow weighted average1 influent of the two drinking water treatment plants.
- `documents/farmington/final_permit.txt` Part I reporting requirements, items 3–4: 3. If any 30 day average, monthly average, 7 day average, weekly average, or daily maximum
   value exceeds the effluent limitations specified in Part I.A, the permittee shall report the
   excursion in accordance with the requirements of Part III.D.

4. Any 30 day average, monthly average, 7 day average, weekly average, or daily maximum
   value reported in the required Discharge Monitoring Repor
- `sources/permit_limits.csv` row LIMIT_VALUE_ID=3610673284, PARAMETER_CODE=00310 (BOD): DMR_COMMENT_TEXT=TOTAL DISSOLVED SOLIDS (TDS) MEASURED AT OUTFALL 001.  REPORT THE GEOMETRIC MEAN VALUE OF THE WEEKLY VALUES.; PARAMETER_CODE=00310; PARAMETER_DESC="BOD, 5-day, 20 deg. C"; LIMIT_FREQ_OF_ANALYSIS_CODE=05/WK; STATISTICAL_BASE_TYPE_CODE=AVG
- `sources/permit_limits.csv` row LIMIT_VALUE_ID=3610673300, PARAMETER_CODE=70295 (TDS): DMR_COMMENT_TEXT=TOTAL DISSOLVED SOLIDS (TDS) MEASURED AT OUTFALL 001.  REPORT THE GEOMETRIC MEAN VALUE OF THE WEEKLY VALUES.; PARAMETER_CODE=70295; PARAMETER_DESC="Solids, total dissolved"; LIMIT_FREQ_OF_ANALYSIS_CODE=01/07; LIMIT_VALUE_NMBR=497; STATISTICAL_BASE_TYPE_CODE=AVG
- `sources/permit_limits.csv` aggregate of 40 rows with 'GEOMETRIC MEAN' in DMR_COMMENT_TEXT: 40 rows share identical DMR_COMMENT_TEXT; 10 distinct PARAMETER_CODE values: 00310, 00400, 00530, 00720, 50050, 50060, 51040, 70295, 81010, 81011; all EXTERNAL_PERMIT_NMBR=NM0020583, LIMIT_SET_SCHEDULE_ID=3600891019
- `sources/dmr_measurements.csv` row DMR_FORM_VALUE_ID context LIMIT_VALUE_ID=3610673284, MONITORING_PERIOD_END_DATE=2024-10-31: PARAMETER_CODE=00310; LIMIT_VALUE_ID=3610673284; DMR_VALUE_NMBR=182; DMR_VALUE_STANDARD_UNITS=82.62799931; LIMIT_VALUE_STANDARD_UNITS=757.72599363; LIMIT_FREQ_OF_ANALYSIS_CODE=05/WK; STATISTICAL_BASE_TYPE_CODE=AVG

### T2 pass_fail

candidates: [{'id': 'binary_wet_outcome_codes', 'statement': 'PASS=0 and FAIL=1 are DMR reporting codes for whole-effluent-toxicity test outcome: enter 0 when the test passes (NOEC for survival is not below the critical dilution) and 1 when it fails (NOEC is below the critical dilution), using the DMR concentration MAX field as a carrier.', 'support': 'DMR_COMMENT_TEXT, permit Part II reporting table, pass/fail unit descriptor, empty limit numerics on pass/fail parameters'}, {'id': 'ordinary_numeric_limit_comparison', 'statement': 'Reported 0/1 values are pollutant concentrations to be compared against a numeric effluent limit using standard <= or >= concentration logic.', 'support': 'none for pass/fail parameters; refuted by empty LIMIT_VALUE_NMBR, pass=0;fail=1 units, and permit narrative'}, {'id': 'no_data_or_nodi_placeholder', 'statement': '0/1 are generic missing-data or NODI placeholders unrelated to WET pass/fail semantics.', 'support': 'none; refuted by explicit comment text and permit reporting instructions tied to toxicity outcome'}]
n_retained: 8
limitations: ['Critical dilution numeric value is not stated in the inspected structured fields or retained permit excerpts.', 'Whether a specific optional retest row without a reported value reflects pass, fail, or not-required cannot be resolved from structured data alone.', 'All 12 affected occurrences belong to one permit (NM0020583) and one WET limit set; generalization to other permits is not established by this workspace.', 'Permit document text was inspected only for NM0020583 (farmington); no cross-permit codebook exists in structured sources.']

- `sources/permit_limits.csv` limit set 3600657354 / LIMIT_SET_SCHEDULE_ID 3600904539, rows sharing DMR_COMMENT_TEXT (e.g., LIMIT_VALUE_ID 3610839682, PARAMETER_CODE TEM3D): (PASS = 0  FAIL = 1) REPORT PASS AS '0' OR REPORT FAIL AS '1' IN CONCENTRATION MAX. ABOVE.  IF ALL TESTS PASS FOR THE FIRST YEAR OF THE PERMIT, THE FREQUENCY WILL BE REDUCED FOR YEARS 2-5 TO:  1/6 MONTHS FOR DAPHNIA PULEX & 1/YR FOR PIMEPHALES PROMELAS (SEE FOOTNOTE 9, PAGE 3 OF PART I OF PERMIT).
- `sources/permit_limits.csv` LIMIT_VALUE_ID 3610839682, PARAMETER_CODE TEM3D: LIMIT_VALUE_NMBR=(empty); LIMIT_UNIT_DESC=pass=0;fail=1; LIMIT_VALUE_QUALIFIER_CODE=(empty); STATISTICAL_BASE_TYPE_CODE=VA; PARAMETER_DESC=Low Flow Pass/Fail Static Renewal 48Hr Acute Daphnia pulex
- `documents/farmington/final_permit.txt` Part II, Section 3.c, Reporting Requirement table, lines 512-514: Enter a "1" if the No Observed Effect Concentration (NOEC) for survival is less than the critical dilution, otherwise enter a "0".
- `documents/farmington/final_permit.txt` Part II, Section D.b, lines 390-394: The NOEC (No Observed Lethal Effect Concentration) is herein defined as the greatest effluent dilution at and below which lethality that is statistically different from the control (0% effluent) at the 95% confidence level does not occur. Acute test failure is defined as a demonstration of a statistically significant lethal effect at test completion to a test species at or below the critical dilut
- `documents/farmington/final_permit.txt` Part I, Page 3, lines 106-109 and footnote *9, lines 125-126: WHOLE EFFLUENT TOXICITY TESTING (48-Hr Acute Static Renewal/ NOEC) (*9) ... Daphnia pulex Report Once/Quarter ... Pimephales promelas Report Once/Quarter ... *9 Monitoring and reporting requirements begin on the effective date of this permit. See PART II, Whole Effluent Toxicity testing requirements for additional WET monitoring and reporting conditions, and a frequency reduction option.
- `sources/dmr_measurements.csv` DMR_FORM_VALUE_ID 3920662053, LIMIT_VALUE_ID 3610839682, MONITORING_PERIOD_END_DATE 11/30/2024: DMR_VALUE_NMBR=0; DMR_UNIT_DESC=pass=0;fail=1; DMR_VALUE_QUALIFIER_CODE==; LIMIT_VALUE_NMBR=(empty); LIMIT_VALUE_STANDARD_UNITS=(empty); PARAMETER_CODE=TEM3D
- `sources/dmr_measurements.csv` DMR_FORM_VALUE_ID 3920662047, LIMIT_VALUE_ID 3610839676, MONITORING_PERIOD_END_DATE 11/30/2024: DMR_VALUE_NMBR=(empty); LIMIT_VALUE_NMBR=(empty); NODI_CODE=9; OPTIONAL_MONITORING_FLAG=Y; PARAMETER_DESC=Whole effluent toxicity - retest #1
- `documents/farmington/final_permit.txt` Part II, Section 3.c, Reporting Requirement table, lines 515-517: Report the NOEC value for survival ... TOM3D ... TOM6C ... Report the highest (critical dilution or control) Coefficient of Variation ... TQM3D ... TQM6C

### T2 empty_numeric_limit

candidates: [{'id': 'uniform_numeric_limit', 'label': 'Empty LIMIT_VALUE_NMBR still denotes an enforceable numeric concentration limit whose value is recoverable from the row or a single alternate field', 'status': 'refuted_for_parent'}, {'id': 'uniform_report_only', 'label': 'Empty LIMIT_VALUE_NMBR uniformly means report-only monitoring with no numeric compliance comparison', 'status': 'refuted_for_parent'}, {'id': 'heterogeneous_non_numeric_obligations', 'label': 'Empty LIMIT_VALUE_NMBR marks multiple distinct non-numeric or non-concentration obligation types (report-only, pass/fail coded WET, geometric-mean reporting, conditional when-discharging monitoring)', 'status': 'supported_by_evidence'}]
n_retained: 8
limitations: ['No codebook or field legend in workspace structured sources defines LIMIT_VALUE_TYPE_CODE or empty LIMIT_VALUE_NMBR semantics.', "18 empty-limit rows have blank DMR_COMMENT_TEXT; classification for those rows relies on matching permit narrative 'Report' language, not a structured flag.", 'Zero FY2025 DMR measurement rows have empty LIMIT_VALUE_NMBR in this workspace, so Purpose A comparison behavior for these rows cannot be observed from DMR data.', "Whether discharge occurred for 'when discharging' rows is not established in structured sources.", 'Geometric-mean TDS rows may have numeric limits elsewhere in the permit schedule (e.g., net-increase mg/L limits) that apply to a different limit row, not the empty LIMIT_VALUE_NMBR row under inspection.']

- `sources/permit_limits.csv` aggregate over 57 rows with empty LIMIT_VALUE_NMBR: All 57 rows have LIMIT_VALUE_NMBR empty, LIMIT_VALUE_QUALIFIER_CODE empty, and LIMIT_TYPE_CODE = ENF. LIMIT_VALUE_TYPE_CODE is C3 (29), Q2 (10), C2 (9), Q1 (8), or C1 (1)—the same code set appears on rows with nonempty LIMIT_VALUE_NMBR. DMR_COMMENT_TEXT partitions the 57 rows: 18 blank, 15 geometric-mean TDS, 12 WHEN DISCHARGING., 12 pass/fail WET.
- `documents/gcc/final_permit.txt` PART I Outfall 001 table, lines 66-74: Flow                     Report MGD        Report MGD        ***               ***                1/Day        Estimate
Total Suspended          N/A               N/A               Report            50                 1/Week               Grab
Dissolved Copper         N/A               N/A               Report            Report             1/Week               Grab
Dissolved Cadmium        N/A    
- `documents/gcc/final_permit.txt` PART II WET reporting table, lines 374-376: Enter a "1" if the No Observed Effect
 Concentration (NOEC) for survival is less than
the critical dilution, otherwise enter a "0".
- `documents/aztec/final_permit.txt` PART I table and footnotes, lines 78-93: Flow                                Report MGD Report MGD           ***               ***       2/Week (*1)     Estimate (*2)
Cyanide, Total Recoverable            Report           Report     Report             Report    1/Quarter (*1)       Grab
Total Dissolved Solids                Report           Report     Report             Report    1/Quarter (*1)       Grab
...
*1 When discharging.
- `documents/farmington/final_permit.txt` PART I footnote *6, line 121: *6      Total dissolved solids measured at Outfall 001. Report the geometric mean value of weekly values.
- `documents/farmington/final_permit.txt` PART I WET table, lines 106-109: WHOLE EFFLUENT TOXICITY TESTING                                                   MEASUREMENT
(48-Hr Acute Static Renewal/ NOEC) (*9)                      VALUE                 FREQUENCY                           SAMPLE TYPE
Daphnia pulex                                                Report                Once/Quarter                        24-Hr Composite
Pimephales promelas                     
- `documents/farmington/final_permit.txt` PART II WET reporting table, lines 512-514: Enter a "1" if the No Observed Effect Concentration        TEM3D           TEM6C
        (NOEC) for survival is less than the critical
        dilution, otherwise enter a "0".
- `sources/permit_limits.csv` row LIMIT_VALUE_ID=22415, EXTERNAL_PERMIT_NMBR=NM0020583: DMR_COMMENT_TEXT="(PASS = 0  FAIL = 1) REPORT PASS AS '0' OR REPORT FAIL AS '1' IN CONCENTRATION MAX. ABOVE." LIMIT_VALUE_NMBR= (empty) LIMIT_VALUE_QUALIFIER_CODE= (empty) LIMIT_TYPE_CODE=ENF PARAMETER_CODE=22415

### T2 document_authority

candidates: [{'id': 'inventory_kind_hierarchy', 'statement': 'document_inventory.json document_kind values (final_permit, fact_sheet, etc.) define a fixed governing hierarchy among package documents.', 'status': 'refuted'}, {'id': 'issued_permit_authorization_governs', 'statement': 'Narrative text of the issued final permit (AUTHORIZATION TO DISCHARGE and conditions set forth in named permit parts of that document) establishes enforceable permit obligations; draft supporting documents establish proposed-condition rationale and background, and defer enforceable limits to the permit text.', 'status': 'supported'}, {'id': 'all_package_documents_equally_binding', 'statement': 'Every inventoried package document is an independently enforceable authorization source with no precedence rule.', 'status': 'refuted'}, {'id': 'structured_inventory_only', 'statement': 'Only filename/hash inventory metadata is available; narrative authority cannot be established.', 'status': 'refuted'}]
n_retained: 8
limitations: ['Only 5 of 12 inventoried narrative documents were opened under budget; reasonable_potential worksheets and gcc/minor_modification.txt were not directly inspected.', "No workspace text states an explicit general rule such as 'if the fact sheet disagrees with the issued permit, the issued permit governs'; precedence is inferred from issued-authorization versus draft-supporting document roles.", "Farmington Part IV content lives in a separate inventory file (documents/farmington/part_iv.txt) while the final permit cover references Part IV 'hereof'; the package does not contain an explicit conflict-resolution clause among separately filed part extracts.", 'documents/gcc/final_permit.txt Part III extract in workspace appears truncated/corrupted (non-standard content after the Part III header), limiting verification of standard-condition integration for that facility.', 'Structured CSVs and document_inventory.json alone cannot establish narrative authority; resolution depends on permit-package text extracts under documents/.']

- `documents/gcc/final_permit.txt` lines 4-21: AUTHORIZATION TO DISCHARGE UNDER THE
NATIONAL POLLUTANT DISCHARGE ELIMINATION SYSTEM
...
is authorized to discharge ... in accordance with this cover page and effluent limitations, monitoring requirements, and other
conditions set forth in Parts I [Requirements for NPDES Permits], II [Other Conditions], and
III [Standard Conditions for NPDES Permits] hereof.
- `documents/gcc/final_permit.txt` lines 23-24: This permit supersedes and replaces NPDES Permit No. NM0000116 issued November 23,
2010.
- `documents/gcc/final_permit.txt` lines 149-150: Current EPA Region 6 minimum quantification levels (MQLs) for reporting and compliance are
provided in Appendix A of Part II of this permit.
- `documents/gcc/fact_sheet.txt` lines 1-4: NPDES PERMIT NO. NM0000116
                                  FACT SHEET
FOR THE DRAFT NATIONAL POLLUTANT DISCHARGE ELIMINATION SYSTEM
(NPDES) PERMIT TO DISCHARGE TO WATERS OF THE UNITED STATES
- `documents/gcc/fact_sheet.txt` lines 34-35: Proposed revocation and reissuance of the current permit issued with an effective date of June 1,
2016, and an expiration date of May 31, 2021.
- `documents/aztec/statement_of_basis.txt` lines 1-4: NPDES PERMIT NO. NM0028762
                     STATEMENT OF BASIS
FOR THE DRAFT NATIONAL POLLUTANT DISCHARGE ELIMINATION SYSTEM
(NPDES) PERMIT TO DISCHARGE TO WATERS OF THE UNITED STATES
- `documents/aztec/statement_of_basis.txt` lines 556-558: F.       FINAL EFFLUENT LIMITATIONS

See the draft permit for limitations.
- `documents/farmington/final_permit.txt` lines 24-25: in accordance with this cover page and the effluent limitations, monitoring requirements, and other
conditions set forth in Part I, Part II, Part III, and Part IV hereof.

### T2 monitoring_frequency

candidates: [{'id': 'standalone_codebook', 'statement': 'Each LIMIT_FREQ_OF_ANALYSIS_CODE token has a fixed workspace-defined meaning (e.g., 05/WK = five times per week, 01/07 = once per week) independent of permit narrative.', 'disposition': 'UNRESOLVED', 'rationale': 'No workspace file defines the NN/XX or NN/WK encoding. PASS_TASK.md states that if a definition is not in a workspace file, UNRESOLVED is correct, and that structural CSV correlation is not a code legend.'}, {'id': 'permit_crosswalk_calendar', 'statement': "For calendar-scheduled parameters, each code's frequency is established by joining structured limit rows to the matching permit's Part I MEASUREMENT FREQUENCY column for the same permit number and pollutant.", 'disposition': 'UNRESOLVED', 'rationale': 'Permit tables use human-readable frequencies (Five/Week, 1/Day, 1/Week, 2/month, Once/Quarter, Continuous) that consistently align with structured codes on matched rows, but the workspace never states that the structured token encodes that text. Inference requires a cross-source join not authorized as a code legend.'}, {'id': 'non_calendar_codes', 'statement': '09/99 and 99/99 establish ordinary periodic sampling frequencies comparable to 01/07 or 05/WK.', 'disposition': 'SUPPORTED_NEGATIVE', 'rationale': "99/99 appears only on continuous flow (TM sample type) where permit text says 'Continuous'. 09/99 appears only on WET retest parameters described as '(If required)' additional reporting, not a calendar schedule."}]
n_retained: 8
limitations: ['No workspace file explicitly defines LIMIT_FREQ_OF_ANALYSIS_CODE semantics or the NN/XX encoding scheme.', 'Permit narrative uses notations such as Five/Week, 1/Day, 1/Week, Once/Quarter, and Continuous — never the structured tokens 05/WK, 01/01, 01/07, etc.', 'Footnotes and conditions (e.g., *1 sampling on five different days; *1 when discharging) modify nominal frequencies but are not encoded in the code field.', '09/99 rows are event-triggered WET retests, not periodic calendar schedules.', 'Codes present in permit text but absent from permit_limits.csv (e.g., Aztec WET Once/Term, GCC WET Once/5 years) cannot be decoded from structured data in this workspace.', 'DMR_FREQ_OF_ANALYSIS_CODE sometimes differs from LIMIT_FREQ_OF_ANALYSIS_CODE on reported measurements, so DMR-side codes do not provide a standalone legend.']

- `sources/permit_limits.csv` line 1 (header); lines 2, 6, 12, 49: LIMIT_FREQ_OF_ANALYSIS_CODE,... | Row 2 (NM0020583 BOD5): ...,12,05/WK,... | Row 6 (NM0000116 pH): ...,GR,01/01,... | Row 12 (NM0028762 pH): ...,GR,01/07,... | Row 49 (NM0020583 WET retest #1): ...,24,09/99,...
- `documents/farmington/final_permit.txt` lines 56–57, 65, 76: pH ... MEASUREMENT FREQUENCY ... Five/Week (*1) ... Grab
Biochemical Oxygen ... 5/Week (*1)
E. Coli Bacteria ... 5/Week (*1) ... Grab
- `documents/farmington/final_permit.txt` lines 111–112: Footnotes:
*1      Sampling on at least five different days.
- `documents/gcc/final_permit.txt` lines 57–58, 66–68: pH ... MAXIMUM ... 1/Day ... Grab
Flow ... 1/Day ... Estimate
Total Suspended Solids ... 50 ... 1/Week ... Grab
- `documents/aztec/final_permit.txt` lines 72–73, 78–80, 92–93: pH ... 1/Week (*1) ... Grab
Flow ... 2/Week (*1) ... Estimate (*2)
Total Residual Chlorine ... 1/Day (*1) ... Grab
Footnotes:
*1 When discharging.
- `documents/farmington/final_permit.txt` lines 63, 78, 86, 108–109: Flow ... Continuous ... Totalizing Meter
Total Residual Chlorine ... Daily ... Grab (*5)
Cyanide ... 2/month ... Grab
Daphnia pulex ... Once/Quarter ... 24-Hr Composite
- `documents/farmington/final_permit.txt` lines 500–504, 518–520: b. A valid test for each species must be reported during each reporting period specified in PART I of this permit ... Additional results are reported under the retest codes below.
(If required) Retest 1 – Enter a "1" if the NOEC for survival is less than the critical dilution, otherwise enter "0". ... 22418 ... 22415
- `documents/farmington/statement_of_basis.txt` lines 636–643: Regulations require permits to establish monitoring requirements to yield data representative of the monitored activity (40 CFR §122.48(b)) ... BOD5 and TSS, are proposed to be monitored five times per week, with sampling on at least five different days. ... monitoring frequencies of daily for TRC and five times per week for E. coli, pH and flow are consistent with the previous permit. Report requ

### T3 nodi_c

candidates: [{'label': 'documented_no_discharge_period', 'statement': 'Code C documents that no discharge occurred during the monitoring period, analogous to a no-discharge DMR reporting action.', 'status': 'unestablished', 'note': 'All 150 FY2025 C rows are on permit NM0000116 with empty DMR_VALUE_NMBR, but the NM0000116 permit package in workspace does not define NODI C or provide NO DISCHARGE box instructions.'}, {'label': 'form_defined_no_data_indicator', 'statement': 'Code C is an EPA DMR No Data Indicator with a fixed form-defined meaning.', 'status': 'unestablished', 'note': 'No NODI or No Data Indicator legend appears in workspace structured sources or permit-package text extracts.'}, {'label': 'monitoring_not_required', 'statement': 'Code C marks a period where required monitoring was not applicable or not triggered.', 'status': 'weakened_by_structured_evidence', 'note': "All 150 FY2025 rows with NODI_CODE='C' have OPTIONAL_MONITORING_FLAG='N', indicating monitoring is not marked optional in structured limit data."}, {'label': 'missing_evidence_despite_required_monitoring', 'statement': 'Code C is only a reporting placeholder and does not by itself establish any documented no-data state for Purpose C.', 'status': 'compatible_with_absence_of_definition', 'note': 'Workspace sources show the code value but not its semantics; absent establishing text, classification must remain unresolved.'}]
n_retained: 7
limitations: ['No NODI or No Data Indicator codebook exists in sources/ structured tables.', 'No workspace document defines the meaning of NODI code C.', 'EPA dictionaries, NetDMR legends, and training-data definitions are out of scope and were not used.', 'Structural correlation of C with empty numeric results and permit NM0000116 cannot substitute for an authoritative code definition.']

- `OBLIGATION.md` lines 4-18: "exact_semantic_question": "What does NODI code C mean for a FY2025 DMR row with no numeric result?" ... "known_structured_evidence": "structured CSVs + document inventory; no codebook table in structured sources" ... "current_epistemic_status": "UNRESOLVED"
- `construction.py` lines 584-590: purpose.require_interpreted(
        "nodi_code_semantics",
        relation="no_numeric_result_case",
        field="nodi_code",
        known=[""],
        purpose="C",
        per="measurement",
    )
- `sources/dmr_measurements.csv` line 1 header; line 246 representative row: ...,DMR_VALUE_NMBR,...,NODI_CODE
3602720951,NM0000116,...,50050,"Flow, in conduit or thru treatment plant",...,3896611092,..., ,...,01/28/2025,C
- `sources/dmr_measurements.csv` structured profile of FY2025 no-result rows: 186 FY2025 rows with empty DMR_VALUE_NMBR: NODI 'C' = 150 (all permit NM0000116, OPTIONAL_MONITORING_FLAG 'N'); NODI '9' = 36 (permit NM0020583).
- `documents/gcc/final_permit.txt` lines 103-122: B.     REPORTING OF MONITORING RESULTS (MINOR DISCHARGERS)

Discharge Monitoring Report (DMR) results shall be electronically reported to EPA
per 40 CFR 127.16. ... Monitoring information shall be
submitted quarterly. Each quarterly submittal shall include separate forms for each
month of the reporting period.
- `documents/gcc/final_permit.txt` lines 192-197: 2. Discharges are restricted to overflows from the retention pond due to catastrophic or chronic
precipitation events.
- `documents/aztec/final_permit.txt` lines 150-153: 5. NO DISCHARGE REPORTING

If there is no discharge from any outfall during the sampling month, place an "X" in the NO
DISCHARGE box located in the upper right corner of the Discharge Monitoring Report.

### T3 nodi_9

candidates: [{'label': 'Not applicable / monitoring not required for this reporting period', 'basis': "Permit labels WET retest DMR lines as '(If required)' and sets OPTIONAL_MONITORING_FLAG=Y with frequency code 09/99 on linked limits; permit footnote *5 states TRC shall be monitored only when chlorine is used.", 'status': 'unsupported_as_uniform_meaning — applies to different parameter families under the same code without workspace text naming NODI 9'}, {'label': 'No discharge during sampling month', 'basis': 'Aztec permit NM0028762 contains NO DISCHARGE REPORTING instructions (checkbox on DMR form).', 'status': "refuted_for_nodi_9 — text is for a different permit (not NM0020583), references an 'X' in a NO DISCHARGE box rather than NODI code 9, and does not cover optional WET retest parameters"}, {'label': 'Same meaning as NODI code C', 'basis': 'Both are nonempty NODI codes on FY2025 rows lacking numeric results.', 'status': 'refuted — NODI C appears only on permit NM0000116 (150 rows, mandatory parameters); NODI 9 appears only on permit NM0020583 (36 rows, distinct parameter set including optional WET retests)'}, {'label': 'Indeterminate / code legend absent from workspace', 'basis': 'No NODI codebook in structured sources; no permit text for NM0020583 defines NODI code 9.', 'status': 'supported_negative — workspace lacks establishing text'}]
n_retained: 8
limitations: ['Structured sources contain no NODI codebook or legend (confirmed in OBLIGATION.md known_structured_evidence).', 'No opened permit-package document for NM0020583 defines NODI code 9 or maps DMR no-data codes to permit states.', 'All 36 NODI 9 occurrences are on permit NM0020583; NODI C occurrences are on a different permit (NM0000116), preventing cross-code inference from co-occurrence.', 'Permit-package documents for NM0020583 lack a NO DISCHARGE REPORTING section comparable to aztec/final_permit.txt.', 'Structured data alone cannot distinguish documented conditional non-monitoring from inadequate monitoring evidence for chlorine rows.']

- `sources/dmr_measurements.csv` line 2, DMR_FORM_VALUE_ID=3920662047: 3602878711,NM0020583,...,22415,Whole effluent toxicity - retest #1,...,OPTIONAL_MONITORING_FLAG=Y,...,LIMIT_FREQ_OF_ANALYSIS_CODE=09/99,...,DMR_VALUE_NMBR empty,...,NODI_CODE=9
- `sources/dmr_measurements.csv` line 330, DMR_FORM_VALUE_ID=3920642644: 3602878711,NM0020583,...,50060,"Chlorine, total residual",...,OPTIONAL_MONITORING_FLAG=N,...,LIMIT_FREQ_OF_ANALYSIS_CODE=01/01,...,DMR_VALUE_NMBR empty,...,NODI_CODE=9
- `sources/dmr_measurements.csv` line 246, DMR_FORM_VALUE_ID=3896611092: 3602720951,NM0000116,...,50050,"Flow, in conduit or thru treatment plant",...,OPTIONAL_MONITORING_FLAG=N,...,DMR_VALUE_NMBR empty,...,NODI_CODE=C
- `sources/permit_limits.csv` line 49, LIMIT_VALUE_ID=3610839676, PARAMETER_CODE=22415: NM0020583,...,22415,Whole effluent toxicity - retest #1,...,OPTIONAL_MONITORING_FLAG=Y,...,LIMIT_FREQ_OF_ANALYSIS_CODE=09/99,...,DMR_COMMENT_TEXT begins '(PASS = 0  FAIL = 1) REPORT PASS AS '0' OR REPORT FAIL AS '1'...'
- `sources/permit_limits.csv` line 67, LIMIT_VALUE_ID=3610673291, PARAMETER_CODE=50060: NM0020583,...,50060,"Chlorine, total residual",...,OPTIONAL_MONITORING_FLAG=N,...,LIMIT_FREQ_OF_ANALYSIS_CODE=01/01,...,LIMIT_VALUE_NMBR=19 ug/L
- `documents/farmington/final_permit.txt` lines 117-120, footnote *5: *5      This facility uses Ultraviolet disinfection. Total Residual Chlorine (TRC) shall be monitored any time chlorine is used within the treatment plant for disinfection, equipment cleaning, maintenance, or any other purpose. The effluent limitation for TRC is the instantaneous maximum grab sample taken during periods of chlorine use and cannot be averaged for reporting purposes.
- `documents/farmington/final_permit.txt` lines 518-520: (If required) Retest 1 – Enter a “1” if the NOEC for         22418                 22415
        survival is less than the critical dilution,
        otherwise enter “0”.
- `documents/aztec/final_permit.txt` lines 150-153: 5. NO DISCHARGE REPORTING

If there is no discharge from any outfall during the sampling month, place an "X" in the NO
DISCHARGE box located in the upper right corner of the Discharge Monitoring Report.

### T3 when_discharging

candidates: [{'id': 'monitoring_conditional', 'text': 'The comment makes stated monitoring frequencies and sample collection apply only during periods when the outfall is discharging; months with no discharge are handled via NO DISCHARGE DMR reporting instead of performing the (*1)-marked monitoring.', 'support': "Permit footnote *1 'When discharging.' annotates monitoring-frequency cells; statement of basis repeats 'when discharging' for flow, TRC, pH, TDS, and cyanide monitoring."}, {'id': 'limit_waived_no_discharge', 'text': 'The comment suspends numeric effluent limit applicability whenever discharge does not occur in a period.', 'support': 'Not found in permit text; Part I.A numeric limits remain specified and excursion/violation language applies to reported DMR values exceeding limits.'}, {'id': 'optional_monitoring_flag', 'text': 'The comment is equivalent to OPTIONAL_MONITORING_FLAG=Y, making the limit row optional.', 'support': 'Refuted structurally: all 17 affected rows have OPTIONAL_MONITORING_FLAG=N and LIMIT_TYPE_CODE=ENF.'}]
n_retained: 8
limitations: ["All 17 workspace occurrences of DMR_COMMENT_TEXT 'WHEN DISCHARGING' are on permit NM0028762; resolution is grounded in the aztec permit package only.", 'Structured CSVs do not encode an explicit link field between DMR_COMMENT_TEXT and permit footnote *1; linkage is established by textual match and co-occurring limit parameters/frequencies.', 'Whether discharge occurred in any specific monitoring period cannot be determined from structured CSV fields alone; that remains a separate operational fact.', 'Structured DMR extracts in this workspace do not include a NO DISCHARGE indicator field, so no-discharge months cannot be identified programmatically from dmr_measurements.csv.']

- `documents/aztec/final_permit.txt` lines 72–79, 92–93: pH ... 1/Week (*1) ... Flow ... 2/Week (*1) ... Total Suspended Solids ... 1/Week (*1) ... Total Residual Chlorine ... 1/Day (*1) ... Cyanide, Total Recoverable ... 1/Quarter (*1) ... Total Dissolved Solids ... 1/Quarter (*1)

Footnotes:
*1 When discharging.
- `documents/aztec/final_permit.txt` lines 150–153: 5. NO DISCHARGE REPORTING

If there is no discharge from any outfall during the sampling month, place an "X" in the NO DISCHARGE box located in the upper right corner of the Discharge Monitoring Report.
- `documents/aztec/final_permit.txt` lines 56–66: 1. FINAL Effluent Limits – Outfall 001 – Intermittent Flow

   During the period beginning the effective date of the permit and lasting to the permit expiration date (unless otherwise noted), the permittee is authorized to discharge backwash water ... Such discharges shall be limited and monitored by the permittee as specified below.
- `documents/aztec/statement_of_basis.txt` lines 506–511: Flow shall be estimated daily when discharging. Estimated flow measurements are not subject to the accuracy provisions established at Part III.C.6 of the permit. The pollutant TRC shall be monitored daily when discharging by instantaneous grab which according to Part 136 is defined as analysis within 15 minutes of collection. pH shall continue to be monitored weekly when discharging. TDS and Cyani
- `documents/aztec/statement_of_basis.txt` lines 146–147: Filter backwash using potable water occurs from once per day to once every three to four days depending on the plant and the time of year.
- `sources/permit_limits.csv` row LIMIT_VALUE_ID=3610840344, LIMIT_SET_SCHEDULE_ID=3600904607: NM0028762,LIMIT_SET_NAME=DISCHARGE BACKWASH WATER,DMR_COMMENT_TEXT=WHEN DISCHARGING.,PARAMETER_CODE=00400 (pH),OPTIONAL_MONITORING_FLAG=N,LIMIT_TYPE_CODE=ENF,LIMIT_FREQ_OF_ANALYSIS_CODE=01/07
- `sources/permit_limits.csv` row LIMIT_VALUE_ID=3610840336, LIMIT_SET_SCHEDULE_ID=3600904606: NM0028762,LIMIT_SET_NAME=QUARTERLY REPORTING,DMR_COMMENT_TEXT=WHEN DISCHARGING.,PARAMETER_CODE=70295 (Solids total dissolved),OPTIONAL_MONITORING_FLAG=N,LIMIT_TYPE_CODE=ENF,LIMIT_FREQ_OF_ANALYSIS_CODE=01/90
- `documents/aztec/final_permit.txt` lines 155–163: 6. If any daily maximum or monthly average value exceeds the effluent limitations specified in Part I. A, the permittee shall report the excursion ...
7. Any daily maximum or monthly average value reported in the required Discharge Monitoring Report which is in excess of the effluent limitation specified in Part I. A shall constitute evidence of violation of such effluent limitation and of this pe

### T3 geometric_mean

candidates: [{'id': 'tds_aggregated_reporting', 'text': 'For TDS limits governed by footnotes *6–*8, weekly measurements must be aggregated (geometric mean of weekly values) for reporting; numeric net-increase limits are 30-day averages, so individual weekly samples or undifferentiated monthly DMR scalars are not the comparison unit for limit exceedance.'}, {'id': 'schedule_wide_geometric_mean', 'text': 'Every permit_limit row sharing the limit-set DMR comment must use geometric-mean aggregation for all parameters on that schedule, blocking ordinary single-period comparison for BOD, pH, E. coli, etc.'}, {'id': 'reporting_only_no_comparison_block', 'text': 'The comment is a reporting instruction only and does not alter whether a reported monitoring-period value may be compared to a numeric effluent limit.'}]
n_retained: 8
limitations: ['Workspace contains no weekly sub-period measurement rows; cannot verify whether monthly DMR values equal geometric means of weekly samples.', 'Permit does not state an explicit formula mapping weekly geometric means to the 30-day average net-increase limit used for enforcement.', 'Structured CSV attaches the same DMR_COMMENT_TEXT to 24 non-TDS parameters; permit footnotes *6–*7 name only TDS, so parameter-specific applicability must be resolved by refinement.']

- `sources/permit_limits.csv` row limit_value_id=3610673282 (representative of 40 rows on schedule 3600891019): DMR_COMMENT_TEXT=TOTAL DISSOLVED SOLIDS (TDS) MEASURED AT OUTFALL 001.  REPORT THE GEOMETRIC MEAN VALUE OF THE WEEKLY VALUES.; PARAMETER_CODE=00310 (BOD); LIMIT_FREQ_OF_ANALYSIS_CODE=05/WK
- `sources/permit_limits.csv` rows limit_value_id=3610673300, 3610838803 (TDS net increase, monitoring_location_code=2): PARAMETER_CODE=70295; LIMIT_VALUE_NMBR=497 then 449; STATISTICAL_BASE_TYPE_CODE=AVG; LIMIT_FREQ_OF_ANALYSIS_CODE=01/07; DMR_COMMENT_TEXT contains REPORT THE GEOMETRIC MEAN VALUE OF THE WEEKLY VALUES
- `documents/farmington/final_permit.txt` Part I footnotes *6–*8 (lines 121–124): *6      Total dissolved solids measured at Outfall 001. Report the geometric mean value of weekly values.
*7      Total dissolved solids flow weighted average measured at intake of the two drinking water treatment plants. Report the geometric mean value of weekly values.
*8      Net total dissolved solids calculated by taking the difference between Outfall 001 discharge and flow weighted average1 
- `documents/farmington/final_permit.txt` Part I TDS effluent table (lines 80–103): Total Dissolved Solids, Discharge (*6) ... Report ... 1/Week
Total Dissolved Solids, Water Plants Intake (*7) ... Report ... 1/Week
Total Dissolved Solids, Net Increase (*8) ... 497 mg/L ... 449 mg/L ... 1/Week
- `documents/farmington/final_permit.txt` footnote *5 (lines 117–120): The effluent limitation for TRC is the instantaneous maximum grab sample taken during periods of chlorine use and cannot be averaged for reporting purposes.
- `documents/farmington/final_permit.txt` Part I.C items 3–4 (lines 216–223): If any 30 day average, monthly average, 7 day average, weekly average, or daily maximum value exceeds the effluent limitations specified in Part I.A, the permittee shall report the excursion...
Any 30 day average, monthly average, 7 day average, weekly average, or daily maximum value reported in the required Discharge Monitoring Report which is in excess of the effluent limitation specified in Par
- `documents/farmington/statement_of_basis.txt` TDS discussion (lines 521–548): temporary 30-day average TDS net incremental increase limit of 497 mg/L... EPA proposes a revision... to 449 mg/L... reporting results monthly.
- `sources/dmr_measurements.csv` row dmr_form_value_id=3832994550 (representative TDS net increase monthly report): PARAMETER_CODE=70295; MONITORING_PERIOD_END_DATE=11/30/2024; LIMIT_VALUE_ID=3610673300; DMR_VALUE_NMBR=347; LIMIT_VALUE_NMBR=497; STATISTICAL_BASE_TYPE_CODE=AVG

### T3 pass_fail

candidates: [{'id': 'binary_wet_outcome', 'statement': 'PASS=0 and FAIL=1 are categorical DMR codes for whole-effluent-toxicity test outcome: report 0 when the test passes (NOEC for survival is not less than the critical dilution) and report 1 when the test fails (NOEC for survival is less than the critical dilution).', 'evidence_alignment': 'supported'}, {'id': 'numeric_concentration_comparison', 'statement': 'Reported 0 or 1 values are numeric pollutant concentrations to be compared against a concentration-based effluent limit using ordinary numeric comparison.', 'evidence_alignment': 'refuted'}, {'id': 'dmr_form_field_label_only', 'statement': "'CONCENTRATION MAX' in the DMR comment refers only to the DMR form column label for entering the pass/fail code, without establishing a concentration limit comparison.", 'evidence_alignment': 'supported'}]
n_retained: 8
limitations: ['The PASS=0/FAIL=1 DMR_COMMENT_TEXT is replicated on all 12 rows in the WET limit set, including TOM/TQM parameters that use percent units for numeric NOEC or coefficient-of-variation reporting; the pass/fail coding applies to TEM and retest codes, not to TOM/TQM.', "Structured sources do not define the numeric value of 'critical dilution' for automated pass/fail determination; permit narrative references the concept but the threshold is not encoded as LIMIT_VALUE_NMBR on pass/fail rows.", 'Six of twelve permit limit rows are optional retest parameters (OPTIONAL_MONITORING_FLAG=Y) with no FY2025 reported values in dmr_measurements.csv; semantics are established from permit text but occurrence-level applicability depends on whether a retest was triggered.', 'Evidence is from permit NM0020583 (Farmington) only; all 12 affected structured rows belong to this permit.']

- `sources/permit_limits.csv` row LIMIT_VALUE_ID=3610839676, PARAMETER_CODE=22415: (PASS = 0  FAIL = 1) REPORT PASS AS '0' OR REPORT FAIL AS '1' IN CONCENTRATION MAX. ABOVE.
- `sources/permit_limits.csv` row LIMIT_VALUE_ID=3610839682, PARAMETER_CODE=TEM3D: LIMIT_UNIT_DESC=pass=0;fail=1, STANDARD_UNIT_DESC=pass=0;fail=1, LIMIT_VALUE_NMBR=(empty)
- `sources/permit_limits.csv` row LIMIT_VALUE_ID=3610839684, PARAMETER_CODE=TOM3D: LIMIT_UNIT_DESC=%, STANDARD_UNIT_DESC=%, LIMIT_VALUE_NMBR=(empty); same DMR_COMMENT_TEXT as pass/fail rows
- `documents/farmington/final_permit.txt` Part II Section 3.c, lines 512-514: Enter a "1" if the No Observed Effect Concentration (NOEC) for survival is less than the critical dilution, otherwise enter a "0".
- `documents/farmington/final_permit.txt` Part II Section 3.c, lines 515-516: Report the NOEC value for survival                          TOM3D                 TOM6C
- `documents/farmington/final_permit.txt` Part II Section 3.c, lines 518-520: (If required) Retest 1 – Enter a "1" if the NOEC for survival is less than the critical dilution, otherwise enter "0".
- `documents/farmington/final_permit.txt` Part II Section D.1.b, lines 390-394: Acute test failure is defined as a demonstration of a statistically significant lethal effect at test completion to a test species at or below the critical dilution
- `sources/dmr_measurements.csv` row DMR_FORM_VALUE_ID=3832994493, PARAMETER_CODE=TEM3D, MONITORING_PERIOD_END_DATE=11/30/2024: DMR_VALUE_NMBR=0, DMR_UNIT_DESC=pass=0;fail=1, DMR_VALUE_STANDARD_UNITS=0, LIMIT_VALUE_NMBR=(empty), LIMIT_VALUE_STANDARD_UNITS=(empty)

### T3 empty_numeric_limit

candidates: [{'id': 'report_only_monitoring', 'statement': "Empty LIMIT_VALUE_NMBR denotes a monitoring/reporting requirement with no numeric effluent limit in that limit slot (permit tables show 'Report' or 'N/A' for that column)."}, {'id': 'numeric_limit_elsewhere', 'statement': 'Empty LIMIT_VALUE_NMBR on one limit-type row for a parameter does not mean no numeric limit exists; the same permit and parameter may carry the numeric limit on a sibling row with populated LIMIT_VALUE_NMBR.'}, {'id': 'pass_fail_non_numeric', 'statement': 'Empty LIMIT_VALUE_NMBR on WET retest rows denotes pass/fail reporting encoded as 0/1 rather than a concentration limit.'}, {'id': 'conditional_or_aggregated_reporting', 'statement': 'Empty LIMIT_VALUE_NMBR rows tied to WHEN DISCHARGING or geometric-mean reporting footnotes denote monitoring obligations whose numeric comparison applicability depends on conditions or aggregation not captured in LIMIT_VALUE_NMBR.'}, {'id': 'unresolved_data_gap', 'statement': 'Empty LIMIT_VALUE_NMBR might reflect missing structured encoding rather than an established non-numeric classification, especially where permit text is not matched in this workspace.'}]
n_retained: 8
limitations: ['No workspace codebook defines LIMIT_VALUE_TYPE_CODE (C1/C2/C3/Q1/Q2); classification cannot be resolved from structured fields alone.', 'No FY2025 dmr_measurements.csv rows have empty LIMIT_VALUE_NMBR, so measurement-period applicability of these permit-limit rows cannot be tested against reported values in this workspace slice.', 'Pass/fail WET retest semantics are established primarily via structured DMR_COMMENT_TEXT; farmington/final_permit.txt Part II defines test failure conceptually but does not reproduce the exact PASS=0/FAIL=1 DMR encoding in retrieved sections.', 'WHEN DISCHARGING rows require discharge-occurrence evidence not present in structured sources; classification as conditionally applicable monitoring remains partially unresolved per period.', 'Blank-comment empty-limit rows (18/57) require permit-text matching per parameter; not all parameters were cross-checked against documents within the 5-document budget.']

- `documents/gcc/final_permit.txt` Part I Section A limitation table, lines 66-74: Flow                     Report MGD        Report MGD        ***               ***                1/Day        Estimate

Total Suspended          N/A               N/A               Report            50                 1/Week               Grab
Solids
Total Aluminum           0.78              0.78              0.75              0.75               1/Week               Grab
Total Copper            
- `documents/gcc/fact_sheet.txt` Technology-based limitations discussion, lines 227-233: The 40 CFR 411.37 ELG of 50 mg/l was the basis for establishment of TSS effluent limitation at Outfall 001. ... TSS reported maximum daily discharge did exceed the daily max limit of 50 mg/l. As a result, it is proposed in the draft permit that the permittee report 30-day average for TSS.
- `documents/aztec/final_permit.txt` Part I limitation table, lines 78-82: Flow                                Report MGD Report MGD           ***               ***       2/Week (*1)     Estimate (*2)
Total Suspended Solids                 N/A              N/A          20                30       1/Week (*1)         Grab
Total Residual Chlorine                N/A              N/A        N/A              11 µg/L      1/Day (*1)         Grab
Cyanide, Total Recoverable      
- `documents/aztec/final_permit.txt` Footnotes, line 93: *1 When discharging.
- `documents/farmington/final_permit.txt` Part I limitation table, lines 63-87: Flow                       Report MGD      Report MGD      Report MGD     ***              ***         ***         Continuous     Totalizing Meter
...
Total Dissolved Solids,                                                                                                               12-Hour
                              Report          Report          N/A          Report        Report        N/A 
- `documents/farmington/final_permit.txt` Footnotes, lines 121-122: *6      Total dissolved solids measured at Outfall 001. Report the geometric mean value of weekly values.
*7      Total dissolved solids flow weighted average measured at intake of the two drinking water treatment plants. Report the geometric mean value of weekly values.
- `sources/permit_limits.csv` 12 rows with DMR_COMMENT_TEXT containing PASS/FAIL encoding (e.g., LIMIT_VALUE_ID 3610673260 pattern): (PASS = 0  FAIL = 1) REPORT PASS AS '0' OR REPORT FAIL AS '1' IN CONCENTRATION MAX. ABOVE.  IF ALL TESTS PASS FOR THE FIRST YEAR OF THE PERMIT, THE FREQUENCY WILL BE REDUCED FOR YEARS 2-5 TO:  1/6 MONTHS FOR DAPHNIA PULEX & 1/YR FOR PIMEPHALES PROMELAS (SEE FOOTNOTE 9, PAGE 3 OF PART I OF PERMIT).
- `sources/permit_limits.csv` All 57 rows with empty LIMIT_VALUE_NMBR; field LIMIT_TYPE_CODE: LIMIT_TYPE_CODE = ENF for all 57 empty-limit rows (51 with OPTIONAL_MONITORING_FLAG = N, 6 with Y).

### T3 document_authority

candidates: [{'id': 'issued_authorization_binding', 'statement': "Documents whose text is an issued 'AUTHORIZATION TO DISCHARGE' establish enforceable permit conditions only in the Parts explicitly named on the authorization page; draft fact sheets and statements of basis establish proposed conditions and permitting rationale but not standalone enforceable authorization.", 'support': 'gcc/final_permit.txt and farmington/final_permit.txt authorization language; gcc/fact_sheet.txt and aztec/statement_of_basis.txt draft headers; fact_sheet administrative-record language.'}, {'id': 'inventory_kind_hierarchy', 'statement': 'document_kind labels in document_inventory.json establish a governing hierarchy among inventoried files.', 'support': 'Rejected by relation contract and absence of codebook; inventory provides only path, filename, kind, permit, bytes, sha256, origin.'}, {'id': 'all_files_equally_enforceable', 'statement': 'Every inventoried permit-package file establishes equally enforceable permit obligations.', 'support': "Rejected because draft/supporting documents self-identify as 'FOR THE DRAFT' and describe 'proposed permit' conditions used to develop the permit."}, {'id': 'universal_conflict_rule', 'statement': 'A single general workspace text states which inventoried document governs for every possible disagreement.', 'support': 'Not found. Governance is relationship-specific: issued authorization over proposed text; incorporated appendices via explicit reference; minor_modification lacks precedence text.'}]
n_retained: 8
limitations: ['sources/document_inventory.json lists 12 files with document_kind labels but contains no textual authority or conflict-resolution rules.', 'Only five permit text files were opened under budget; reasonable_potential worksheets and standalone part_ii_appendix/part_iv extracts were not opened as primary documents, though farmington Part IV scope is established via farmington/final_permit.txt authorization text.', 'documents/gcc/minor_modification.txt lacks any governing or precedence language; workspace text does not establish whether it independently modifies the issued permit or merely duplicates Part I tables also present in documents/gcc/final_permit.txt.', 'No workspace text provides a general pairwise precedence rule for all inventoried kinds (e.g., reasonable_potential worksheet versus issued Part I limits) without document-specific reading and comparison.', 'Internal precedence among all subparts within an issued permit beyond explicit cross-references (e.g., Part I versus Part II) is not fully specified in retained snippets.']

- `documents/gcc/final_permit.txt` authorization cover, lines 19-28: in accordance with this cover page and effluent limitations, monitoring requirements, and other conditions set forth in Parts I [Requirements for NPDES Permits], II [Other Conditions], and III [Standard Conditions for NPDES Permits] hereof.

This permit supersedes and replaces NPDES Permit No. NM0000116 issued November 23, 2010.

This permit shall become effective on June 1, 2021

This permit and 
- `documents/farmington/final_permit.txt` authorization cover, lines 24-27: in accordance with this cover page and the effluent limitations, monitoring requirements, and other conditions set forth in Part I, Part II, Part III, and Part IV hereof.

This permit supersedes and replaces NPDES Permit No. NM0020583 issued on September 30, 2016.
- `documents/gcc/final_permit.txt` Part II, lines 149-150: Current EPA Region 6 minimum quantification levels (MQLs) for reporting and compliance are provided in Appendix A of Part II of this permit.
- `documents/gcc/fact_sheet.txt` header, lines 1-4: NPDES PERMIT NO. NM0000116
                                  FACT SHEET
FOR THE DRAFT NATIONAL POLLUTANT DISCHARGE ELIMINATION SYSTEM
(NPDES) PERMIT TO DISCHARGE TO WATERS OF THE UNITED STATES
- `documents/gcc/fact_sheet.txt` Section VIII, lines 435-437: The NMAC, Section 20.6.4.8 “Antidegradation Policy and Implementation Plan” sets forth the requirements to protect designated uses through implementation of the State water quality standards. The limitations and monitoring requirements set forth in the proposed permit are
- `documents/gcc/fact_sheet.txt` Section XVI, lines 508-510: XVI. ADMINISTRATIVE RECORD

The following information was used to develop the proposed permit:
- `documents/aztec/statement_of_basis.txt` header, lines 1-4: NPDES PERMIT NO. NM0028762
                     STATEMENT OF BASIS
FOR THE DRAFT NATIONAL POLLUTANT DISCHARGE ELIMINATION SYSTEM
(NPDES) PERMIT TO DISCHARGE TO WATERS OF THE UNITED STATES
- `documents/farmington/statement_of_basis.txt` Section on reasonable potential monitoring, lines 593-597: for Cadmium (0.05 ug/L, EPA 200.9) , 2,3,7,8-TCDD Dioxin (1.0E-5 ug/L, EPA 1613B), Pentachlorophenol (7.4 ug/L, EPA 604), Aldrin (0.004 ug/L, EPA 608), Chlordane (0.014 ug/L, EPA 608), and Toxaphene (0.24 ug/L, EPA 608)). EPA would reconsider this monitoring requirement for the final permit if the result(s) indicate no reasonable potential exists.

### T3 monitoring_frequency

candidates: [{'id': 'periodic_count_per_period', 'description': 'Codes encode a sample count and period denominator (e.g. 05/WK = five samples per week; 01/07 = one sample per seven-day period; 02/30 = two samples per thirty-day period; 01/90 = one sample per ninety-day period). Supported only by permit-document pairing, not by any code legend in the workspace.', 'codes': ['05/WK', '01/07', '01/01', '02/07', '02/30', '01/90']}, {'id': 'continuous_metering', 'description': 'Code 99/99 denotes continuous totalizing-meter flow monitoring rather than discrete sample collection on a calendar schedule.', 'codes': ['99/99']}, {'id': 'event_driven_retest', 'description': 'Code 09/99 marks WET retest reporting parameters whose permit narrative describes conditional retesting after test failure, not a fixed calendar sampling interval.', 'codes': ['09/99']}, {'id': 'uninterpretable_without_legend', 'description': 'Opaque codes cannot be assigned reusable monitoring-frequency semantics from workspace sources alone because no document names the codes or defines the NN/XX grammar.'}]
n_retained: 8
limitations: ['No workspace file contains a LIMIT_FREQ_OF_ANALYSIS_CODE legend; grep across all documents/ found zero occurrences of opaque code strings.', 'Permit documents state monitoring frequencies in human-readable form only; interpretation of codes requires joining structured rows to narrative tables by permit and parameter, which PASS_TASK.md treats as insufficient alone for a code legend.', 'Code 09/99 has no document-stated calendar frequency; retest obligations are conditional on WET test outcomes.', 'Codes 09/99 and 99/99 each appear only at NM0020583; cross-permit generalization is limited.', 'WET limits for NM0028762 (Once/Term) and NM0000116 (Once/5 years) do not appear in permit_limits.csv with FY2025-overlapping frequency codes, so document pairing cannot cover all permit-package monitoring frequencies.', 'Eight distinct code values appear in FY2025-overlapping permit_limit rows (105 affected occurrences per OBLIGATION.md); retained snippets cover representative codes only within the 8-snippet budget.']

- `documents/farmington/final_permit.txt` lines 57, 63, 86, 108–109; footnote line 112: pH ... Five/Week (*1) ... Grab
Flow ... Continuous ... Totalizing Meter
Cyanide ... 2/month ... Grab
Daphnia pulex ... Once/Quarter ... 24-Hr Composite
Pimephales promelas ... Once/Quarter ... 24-Hr Composite
*1      Sampling on at least five different days.
- `documents/gcc/final_permit.txt` lines 58, 66–74: pH ... 1/Day ... Grab
Flow ... 1/Day ... Estimate
Total Suspended Solids ... 1/Week ... Grab
Total Aluminum ... 1/Week ... Grab
Total Copper ... 1/Week ... Grab
Dissolved Copper ... 1/Week ... Grab
Dissolved Cadmium ... 1/Week ... Grab
Total Hardness ... 1/Week ... Grab
- `documents/aztec/final_permit.txt` lines 72, 78–82: pH ... 1/Week (*1) ... Grab
Flow ... 2/Week (*1) ... Estimate (*2)
Total Suspended Solids ... 1/Week (*1) ... Grab
Total Residual Chlorine ... 1/Day (*1) ... Grab
Cyanide, Total Recoverable ... 1/Quarter (*1) ... Grab
Total Dissolved Solids ... 1/Quarter (*1) ... Grab
- `documents/farmington/statement_of_basis.txt` lines 638–643: Technology based pollutants; BOD5 and TSS, are proposed to be monitored five times per week, with sampling on at least five different days. Flow is proposed to be monitored continuously using a totalizing meter. ... The monitoring frequencies of daily for TRC and five times per week for E. coli, pH and flow are consistent with the previous permit.
- `documents/farmington/final_permit.txt` lines 500–504, 563–564: Additional results are reported under the retest codes below.
...
If the initial WET test conducted fails, the permittee will conduct three retests.
- `sources/permit_limits.csv` row LIMIT_VALUE_ID=3610673290 (EXTERNAL_PERMIT_NMBR=NM0020583, PARAMETER_CODE=00400): NM0020583,...,00400,pH,...,LIMIT_FREQ_OF_ANALYSIS_CODE=05/WK,...
- `sources/permit_limits.csv` row LIMIT_VALUE_ID=3610673294 (EXTERNAL_PERMIT_NMBR=NM0020583, PARAMETER_CODE=50050): NM0020583,...,50050,"Flow, in conduit or thru treatment plant",...,LIMIT_FREQ_OF_ANALYSIS_CODE=99/99,LIMIT_SAMPLE_TYPE_CODE=TM,...
- `sources/permit_limits.csv` row LIMIT_VALUE_ID=3610839676 (PARAMETER_CODE=22415, Whole effluent toxicity - retest #1): NM0020583,...,22415,Whole effluent toxicity - retest #1,...,OPTIONAL_MONITORING_FLAG=Y,LIMIT_FREQ_OF_ANALYSIS_CODE=09/99,...

## OBSERVED

Packets freeze what the adjudicator may use.

## HYPOTHESIS

Bounded packets prevent later search from laundering extra corpus into a judgment.
