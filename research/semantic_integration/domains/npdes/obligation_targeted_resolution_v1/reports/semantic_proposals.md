# Semantic proposals

## MEASURED

### T1 nodi_c

- admit: UNRESOLVED
- scope: ONE_RELATION_OR_VOCABULARY epistemic: UNRESOLVED
- delta: None
- grounding: ['sources/dmr_measurements.csv: 150 FY2025 rows with empty DMR_VALUE_NMBR and NODI_CODE=C, all NM0000116, all OPTIONAL_MONITORING_FLAG=N', 'construction.py: known nodi_code values for Purpose C are [""]; C is not in known list', 'documents/gcc/final_permit.txt: no NODI code definition or NO DISCHARGE reporting instruction for NM0000116', 'documents/gcc/fact_sheet.txt: discharge infrequency narrative without NODI C mapping']

### T1 nodi_9

- admit: UNRESOLVED
- scope: ONE_RELATION_OR_VOCABULARY epistemic: UNRESOLVED
- delta: None
- grounding: [{'source_id': 'sources/dmr_measurements.csv', 'location': 'line 1 (header)', 'text': 'NODI_CODE column present without legend'}, {'source_id': 'sources/dmr_measurements.csv', 'location': 'line 2, DMR_FORM_VALUE_ID=3920662047', 'text': 'Representative FY2025 NODI_CODE=9 row with empty DMR_VALUE_NMBR'}, {'source_id': 'documents/farmington/final_permit.txt', 'location': 'Part I §C.2, lines 198-201', 'text': 'References EPA Form 3320-1 general instructions not present in workspace'}]

### T1 when_discharging

- admit: ADMIT_DISPOSABLE
- scope: ONE_RELATION_OR_VOCABULARY epistemic: SOURCE_ESTABLISHED
- delta: Register 'WHEN DISCHARGING.' as a known permit-limit comment whose monitoring_condition is discharge_occurrence. Extend monitoring_requirement_fy2025 with a reusable comment-to-condition mapping. Split the existing conditional_discharge_dependent_monitoring unresolved into (a) resolved comment semantics and (b) a retained factual unresolved for discharge_occurrence_in_period because structured DMR rows do not encode discharge days or NODI/no-discharge status.
- grounding: ["documents/aztec/final_permit.txt Part I.A footnote *1 ('When discharging.' on MEASUREMENT FREQUENCY)", 'documents/aztec/final_permit.txt Part I.C.5 NO DISCHARGE REPORTING', 'documents/aztec/statement_of_basis.txt Section 5 monitoring-frequency narrative', "sources/permit_limits.csv DMR_COMMENT_TEXT='WHEN DISCHARGING.' with OPTIONAL_MONITORING_FLAG=N"]

### T1 geometric_mean

- admit: UNRESOLVED
- scope: WORLD epistemic: UNRESOLVED
- delta: None
- grounding: ['documents/farmington/final_permit.txt lines 80–82, 97–98, 121 (footnote *6: report geometric mean of weekly values for TDS discharge)', 'documents/farmington/statement_of_basis.txt lines 521–522, 538 (TDS net incremental increase limit stated as 30-day average)', 'sources/permit_limits.csv LIMIT_VALUE_ID=3610673282 (TDS-specific geometric-mean comment on BOD row with AVG base)', 'sources/permit_limits.csv LIMIT_VALUE_ID=3610673300 (TDS row with same comment and AVG base)', 'sources/dmr_measurements.csv DMR_FORM_VALUE_ID=3831416442 and 3831416458 (monthly single values stored without weekly sub-period or geometric-mean fields)']

### T1 pass_fail

- admit: ADMIT_DISPOSABLE
- scope: ONE_RELATION_OR_VOCABULARY epistemic: SOURCE_ESTABLISHED
- delta: Replace blanket pass_fail_reporting_semantics unresolved holes (triggered by shared DMR_COMMENT_TEXT) with a unit-based classifier: rows with pass/fail unit 9A and no numeric limit are modeled as binary_pass_fail_limit and binary_pass_fail_measurement relations; numeric_comparison_candidate remains limited to rows with both reported and limit numeric values. TOM/TQM rows that share the comment but have numeric limits are not flagged as pass/fail semantics unresolved.
- grounding: ["sources/permit_limits.csv row LIMIT_VALUE_ID=3610839676: (PASS = 0  FAIL = 1) REPORT PASS AS '0' OR REPORT FAIL AS '1' IN CONCENTRATION MAX.", 'sources/permit_limits.csv row LIMIT_VALUE_ID=3610839682: LIMIT_UNIT_CODE=9A; STANDARD_UNIT_DESC=pass=0;fail=1; empty LIMIT_VALUE_NMBR', 'sources/permit_limits.csv row LIMIT_VALUE_ID=3610839684: LIMIT_VALUE_NMBR=23; LIMIT_UNIT_CODE=23; STANDARD_UNIT_DESC=%', 'sources/dmr_measurements.csv row DMR_FORM_VALUE_ID=3832994493: DMR_VALUE_NMBR=0; DMR_VALUE_STANDARD_UNITS=9A', 'documents/farmington/final_permit.txt Part II lines 512-514: Enter 1 if NOEC < critical dilution, else 0', 'documents/farmington/final_permit.txt Part II line 515: Report NOEC value for survival on TOM3D/TOM6C separately']

### T1 empty_numeric_limit

- admit: UNRESOLVED
- scope: ONE_SOURCE_VALUE epistemic: SOURCE_ESTABLISHED
- delta: No admissible reusable mapping. A correct Purpose A treatment would need a derived classification field (for example limit_value_role or comparison_eligibility) keyed off DMR_COMMENT_TEXT patterns, statistical_base_type_code, unit encoding, and permit-table crosswalk—not a single boolean or enum applied uniformly to every empty LIMIT_VALUE_NMBR row.
- grounding: ['sources/permit_limits.csv aggregate partition of 57 empty LIMIT_VALUE_NMBR rows by DMR_COMMENT_TEXT and the zero-row count for nonempty LIMIT_VALUE_STANDARD_UNITS.', "documents/gcc/final_permit.txt and documents/farmington/final_permit.txt mapping structured empty cells to permit-table 'Report' labels.", 'sources/permit_limits.csv sibling-row patterns (3610129901 vs 3610129867; 3610840340 vs 3610840342/3610840343) showing emptiness on one statistical base alongside numeric limits on siblings.', 'sources/permit_limits.csv row 3610839676 pass/fail unit and comment encoding.', 'documents/farmington/final_permit.txt TDS geometric-mean footnote *6.']

### T1 document_authority

- admit: ADMIT_DISPOSABLE
- scope: ONE_RELATION_OR_VOCABULARY epistemic: SOURCE_ESTABLISHED
- delta: Add reusable document-authority roles keyed on inventory document_kind (not filename ranking): final_permit and permit-referenced part appendices are authorizing; fact_sheet, statement_of_basis, and reasonable_potential are supporting and defer enforceable limitations to the issued permit. On disagreement, authorizing documents govern supporting documents via functional precedence (authorizing_over_supporting) without requiring a named conflict clause. Kinds absent from the mapping remain unestablished.
- grounding: ['documents/gcc/final_permit.txt:19-21', 'documents/farmington/final_permit.txt:24-25', 'documents/gcc/final_permit.txt:149-150', 'documents/gcc/fact_sheet.txt:191', 'documents/gcc/fact_sheet.txt:504-506', 'documents/aztec/statement_of_basis.txt:556-558', 'documents/aztec/reasonable_potential.txt:12-14', 'documents/farmington/statement_of_basis.txt:1-3']

### T1 monitoring_frequency

- admit: UNVERIFIED_PROPOSAL
- scope: ONE_RELATION_OR_VOCABULARY epistemic: MODEL_HYPOTHESIS
- delta: Would map each LIMIT_FREQ_OF_ANALYSIS_CODE to a structured monitoring frequency (analysis count and calendar period, or sentinel semantics for 99/99 continuous and 09/99 conditional retest) on monitoring_requirement_fy2025.limit_freq_of_analysis_code, satisfying purpose B require_interpreted for monitoring_frequency_code.
- grounding: Permit Part I plain-language frequencies (documents/farmington/final_permit.txt, documents/gcc/final_permit.txt, documents/aztec/final_permit.txt) paired structurally to CSV LIMIT_FREQ_OF_ANALYSIS_CODE values on matching EXTERNAL_PERMIT_NMBR and PARAMETER_CODE; narrative corroboration in documents/farmington/statement_of_basis.txt and documents/gcc/fact_sheet.txt. No workspace source states the NN/PP rule or prints code strings.

### T2 nodi_c

- admit: UNRESOLVED
- scope: ONE_RELATION_OR_VOCABULARY epistemic: UNRESOLVED
- delta: If a NODI C interpretation were admitted, construction.py would need to extend purpose.require_interpreted for nodi_code_semantics (relation no_numeric_result_case, purpose C) from known=[""] to include the admitted code meaning, enabling missing-evidence classification for 150 FY2025 measurements. No such delta is proposed because workspace evidence does not establish any interpretation.
- grounding: Admissible evidence is limited to: (1) sources/dmr_measurements.csv — 150 rows with NODI_CODE=C and empty DMR_VALUE_NMBR on NM0000116 for FY2025 monitoring periods; (2) sources/permit_limits.csv — linked storm-runoff limit set rows with OPTIONAL_MONITORING_FLAG=N; (3) documents/gcc/final_permit.txt — conditional discharge narrative and DMR reporting instructions without NODI definitions; (4) documents/gcc/fact_sheet.txt — background on infrequent discharge without NODI mapping; (5) documents/aztec/final_permit.txt — alternate no-discharge checkbox mechanism in a different permit; (6) OBLIGATION.md — confirmation that no NODI codebook exists in workspace sources. No workspace source provides an authoritative definition or legend for NODI code C.

### T2 nodi_9

- admit: UNRESOLVED
- scope: ONE_RELATION_OR_VOCABULARY epistemic: UNRESOLVED
- delta: None
- grounding: ["sources/dmr_measurements.csv NODI_CODE='9' occurrence partition (36 rows, NM0020583 only)", "sources/dmr_measurements.csv NODI_CODE='C' contrast partition (150 rows, NM0000116 only)", 'sources/permit_limits.csv optional/required flags and frequency codes for parameters 50060 and 22415', 'documents/farmington/final_permit.txt footnote *5 and Part II §D.3 retest reporting table', 'OBLIGATION.md: no structured NODI legend']

### T2 when_discharging

- admit: ADMIT_DISPOSABLE
- scope: ONE_RELATION_OR_VOCABULARY epistemic: SOURCE_ESTABLISHED
- delta: Map DMR_COMMENT_TEXT containing 'WHEN DISCHARGING' to monitoring_applicability_condition=DISCHARGE_OCCURRENCE on permit_limit and monitoring_requirement_fy2025 rows; register 'WHEN DISCHARGING.' as a known permit_limit_comment_text value; remove conditional_discharge_dependent_monitoring unresolved holes for those rows. Per-period discharge occurrence remains a separate factual input, not inferred from the comment definition.
- grounding: ["documents/aztec/final_permit.txt lines 92-94: footnote *1 = 'When discharging.'", 'documents/aztec/final_permit.txt lines 56-66, 72-80: monitoring frequencies marked (*1) on intermittent-flow limits', 'documents/aztec/final_permit.txt lines 150-153: NO DISCHARGE DMR reporting when no discharge in sampling month', 'documents/aztec/statement_of_basis.txt lines 506-511: discharge-conditioned monitoring schedule paraphrased', 'sources/permit_limits.csv: 17 rows with DMR_COMMENT_TEXT=WHEN DISCHARGING. and OPTIONAL_MONITORING_FLAG=N']

### T2 geometric_mean

- admit: ADMIT_DISPOSABLE
- scope: ONE_SOURCE_VALUE epistemic: SOURCE_ESTABLISHED
- delta: Restrict aggregated_reporting_requirement unresolved flags and geometric-mean comparison semantics to permit_limit rows where PARAMETER_CODE is 70295 (TDS, footnote *6). Do not treat identical DMR_COMMENT_TEXT on BOD, E. coli, pH, or other non-TDS parameters as imposing geometric-mean aggregation before limit comparison.
- grounding: ["documents/farmington/final_permit.txt footnote *6: 'Total dissolved solids measured at Outfall 001. Report the geometric mean value of weekly values.'", 'documents/farmington/final_permit.txt Part I reporting requirements items 3–4: reported weekly average and other aggregate statistics exceeding limits constitute violations', 'documents/farmington/final_permit.txt footnote *8: net TDS depends on aggregated discharge and influent values (footnotes *6 and *7 require geometric mean of weekly values)', 'sources/permit_limits.csv row LIMIT_VALUE_ID=3610673300, PARAMETER_CODE=70295: structured row whose comment matches footnote *6 language']

### T2 pass_fail

- admit: ADMIT_DISPOSABLE
- scope: ONE_RELATION_OR_VOCABULARY epistemic: SOURCE_ESTABLISHED
- delta: Add a reusable pass/fail vocabulary classifier keyed on LIMIT_UNIT_DESC/DMR_UNIT_DESC matching pass=0;fail=1 and on DMR_COMMENT_TEXT containing PASS=0/FAIL=1 instructions. Derive wet_pass_fail_reporting rows from measurement_limit_pair with reporting_role=wet_outcome_code, outcome_semantics={0: pass, 1: fail}, and is_numeric_concentration_comparison=false. Remove pass_fail_reporting_semantics purpose.unresolved entries for rows matching the classifier; add purpose.require_interpreted for wet_pass_fail_outcome on the derived relation. Numeric comparison derivation remains unchanged (pass/fail rows already lack has_limit_value_nmbr).
- grounding: ["sources/permit_limits.csv: DMR_COMMENT_TEXT '(PASS = 0  FAIL = 1) REPORT PASS AS '0' OR REPORT FAIL AS '1' IN CONCENTRATION MAX...'", 'sources/permit_limits.csv: LIMIT_UNIT_DESC=pass=0;fail=1 with empty LIMIT_VALUE_NMBR on TEM3D pass/fail rows', 'documents/farmington/final_permit.txt Part II §3.c: \'Enter a "1" if the No Observed Effect Concentration (NOEC) for survival is less than the critical dilution, otherwise enter a "0".\'', 'documents/farmington/final_permit.txt Part II §D.b: acute test failure defined by statistical lethal effect at or below critical dilution, not numeric limit comparison', 'sources/dmr_measurements.csv: DMR_VALUE_NMBR=0 with DMR_UNIT_DESC=pass=0;fail=1 and empty LIMIT_VALUE_NMBR']

### T2 empty_numeric_limit

- admit: UNRESOLVED
- scope: ONE_RELATION_OR_VOCABULARY epistemic: SOURCE_ESTABLISHED
- delta: Add a reusable empty-limit obligation classifier on permit_limit rows (comment-pattern and permit-text corroborated categories) so Purpose A excludes non-numeric obligation types from numeric comparison rather than leaving 18 blank-comment rows and discharge-condition applicability unclassified.
- grounding: sources/permit_limits.csv aggregate (57 empty LIMIT_VALUE_NMBR rows partitioned by DMR_COMMENT_TEXT; LIMIT_VALUE_TYPE_CODE non-discriminating); sources/permit_limits.csv row LIMIT_VALUE_ID=22415 (pass/fail comment with empty LIMIT_VALUE_NMBR); documents/gcc/final_permit.txt PART I Outfall 001 (Report as effluent limitation); documents/gcc/final_permit.txt PART II WET table (0/1 pass/fail coding); documents/aztec/final_permit.txt PART I table and *1 When discharging footnote; documents/farmington/final_permit.txt *6 geometric mean footnote; documents/farmington/final_permit.txt PART I WET table (VALUE=Report); documents/farmington/final_permit.txt PART II WET table (0/1 pass/fail coding).

### T2 document_authority

- admit: ADMIT_DISPOSABLE
- scope: ONE_RELATION_OR_VOCABULARY epistemic: SOURCE_ESTABLISHED
- delta: Replace the blanket permit_document_text_not_available unresolved with document authority roles on permit_document: issued_authorization documents govern enforceable obligations; draft_supporting documents provide rationale and defer limits; inventory document_kind is used only as a fixed lookup keyed to narrative-established roles (not as a filename hierarchy). Documents whose authority role is not established from the packet remain unresolved.
- grounding: [{'source_id': 'documents/gcc/final_permit.txt', 'location': 'lines 4-21', 'proposition': 'Issued-permit cover page binds authorization to effluent limitations and conditions in named permit parts of this document.'}, {'source_id': 'documents/gcc/final_permit.txt', 'location': 'lines 23-24', 'proposition': 'Issued permit supersedes prior permit issuance.'}, {'source_id': 'documents/gcc/final_permit.txt', 'location': 'lines 149-150', 'proposition': 'Appendix content incorporated by permit-part citation within the issued permit.'}, {'source_id': 'documents/gcc/fact_sheet.txt', 'location': 'lines 1-4', 'proposition': 'Fact sheet frames itself as a draft NPDES permit document.'}, {'source_id': 'documents/gcc/fact_sheet.txt', 'location': 'lines 34-35', 'proposition': 'Fact sheet describes proposed permit action, not final authorization.'}, {'source_id': 'documents/aztec/statement_of_basis.txt', 'location': 'lines 1-4', 'proposition': 'Statement of basis uses draft-permit framing.'}, {'source_id': 'documents/aztec/statement_of_basis.txt', 'location': 'lines 556-558', 'proposition': 'Supporting document defers enforceable effluent limitations to permit text.'}, {'source_id': 'documents/farmington/final_permit.txt', 'location': 'lines 24-25', 'proposition': 'Issued permit integrates Parts I-IV by cross-reference within the authorization document.'}]

### T2 monitoring_frequency

- admit: UNRESOLVED
- scope: ONE_RELATION_OR_VOCABULARY epistemic: MODEL_HYPOTHESIS
- delta: Would add interpreted monitoring-frequency semantics to monitoring_requirement_fy2025.limit_freq_of_analysis_code (purpose B require_interpreted monitoring_frequency_code), replacing opaque pass-through with decoded cadence labels or structured period objects. Not proposed because grounding is insufficient.
- grounding: Packet contradictory_evidence and known_limitations: permit text never uses opaque tokens; PASS_TASK rules forbid treating structural CSV correlation alone as a code legend; no workspace file defines LIMIT_FREQ_OF_ANALYSIS_CODE semantics.

### T3 nodi_c

- admit: UNRESOLVED
- scope: ONE_RELATION_OR_VOCABULARY epistemic: SOURCE_ESTABLISHED
- delta: None
- grounding: ['OBLIGATION.md lines 4-18: obligation nodi_c status UNRESOLVED; no codebook in structured sources', 'construction.py lines 584-590: nodi_code_semantics known values limited to empty string', "sources/dmr_measurements.csv: 150 FY2025 rows with NODI_CODE='C', empty DMR_VALUE_NMBR, permit NM0000116, OPTIONAL_MONITORING_FLAG='N'", 'documents/gcc/final_permit.txt lines 103-122: NM0000116 reporting section lacks NODI legend and NO DISCHARGE instruction', 'documents/gcc/final_permit.txt lines 192-197: discharge context does not define NODI C', 'documents/aztec/final_permit.txt lines 150-153: NO DISCHARGE instructions apply to NM0028762, not NM0000116']

### T3 nodi_9

- admit: UNRESOLVED
- scope: ONE_RELATION_OR_VOCABULARY epistemic: SOURCE_ESTABLISHED
- delta: None. No new known value or mapping for no_numeric_result_case.nodi_code should be added; obligation nodi_9 remains intentionally unresolved at the vocabulary layer.
- grounding: ["construction.py purpose.require_interpreted('nodi_code_semantics', relation='no_numeric_result_case', field='nodi_code', known=['']) already marks nodi_code as without established known values.", 'documents/farmington/final_permit.txt and documents/aztec/final_permit.txt retained snippets contain no NODI code 9 definition.', 'PACKET known_limitations confirm absence of a structured NODI codebook and absence of NM0020583 permit text mapping code 9.']

### T3 when_discharging

- admit: ADMIT_DISPOSABLE
- scope: ONE_RELATION_OR_VOCABULARY epistemic: SOURCE_ESTABLISHED
- delta: Map DMR_COMMENT_TEXT 'WHEN DISCHARGING.' to monitoring_condition_code=DISCHARGE_OCCURRENCE on permit_limit and monitoring_requirement_fy2025. Remove EXPLICIT_UNRESOLVED holes for conditional_discharge_dependent_monitoring. Admit 'WHEN DISCHARGING.' as a known permit_limit_comment_text value. Does not encode per-period discharge occurrence or waive numeric limits.
- grounding: ["documents/aztec/final_permit.txt lines 72-79, 92-93: footnote *1 'When discharging.' on monitoring-frequency cells", 'documents/aztec/final_permit.txt lines 150-153: NO DISCHARGE reporting path for months without discharge', "documents/aztec/statement_of_basis.txt lines 506-511: permit-writer rationale conditioning each parameter's monitoring on discharge", 'documents/aztec/final_permit.txt lines 155-163: limits remain enforceable for reported values', 'sources/permit_limits.csv: 17 rows with DMR_COMMENT_TEXT=WHEN DISCHARGING., OPTIONAL_MONITORING_FLAG=N, LIMIT_TYPE_CODE=ENF']

### T3 geometric_mean

- admit: ADMIT_DISPOSABLE
- scope: ONE_RELATION_OR_VOCABULARY epistemic: SOURCE_ESTABLISHED
- delta: Replace blanket geometric-mean unresolved holes with a reusable parameter-code rule: exclude parameter 70295 rows whose dmr_comment_text contains GEOMETRIC MEAN from numeric_comparison_candidate (aggregated reporting is not ordinary single-period comparison); do not emit aggregated_reporting_requirement unresolved holes for non-70295 rows because permit footnotes name TDS only.
- grounding: ['documents/farmington/final_permit.txt Part I footnotes *6–*8 (lines 121–124)', 'documents/farmington/final_permit.txt Part I TDS effluent table (lines 80–103)', 'documents/farmington/final_permit.txt Part I.C items 3–4 (lines 216–223)', 'documents/farmington/statement_of_basis.txt TDS discussion (lines 521–548)', 'sources/permit_limits.csv rows limit_value_id=3610673300, 3610838803 (parameter 70295, AVG, geometric-mean comment)', 'sources/permit_limits.csv contradictory_evidence: 24 non-TDS rows on schedule 3600891019']

### T3 pass_fail

- admit: ADMIT_DISPOSABLE
- scope: ONE_RELATION_OR_VOCABULARY epistemic: SOURCE_ESTABLISHED
- delta: Add reusable detection of pass=0;fail=1 unit descriptions, derive a pass_fail_outcome_reporting relation for matching measurement-limit pairs, register interpreted outcome values {0: pass, 1: fail}, and stop emitting pass_fail_reporting_semantics unresolved obligations for rows that match the established unit-and-comment pattern.
- grounding: [{'source_id': 'sources/permit_limits.csv', 'location': 'LIMIT_UNIT_DESC=pass=0;fail=1 on TEM3D and retest rows', 'field': 'LIMIT_UNIT_DESC'}, {'source_id': 'documents/farmington/final_permit.txt', 'location': 'Part II Section 3.c, lines 512-520', 'field': 'narrative pass/fail entry rule'}, {'source_id': 'sources/dmr_measurements.csv', 'location': 'DMR_UNIT_DESC=pass=0;fail=1 with DMR_VALUE_NMBR in {0,1}', 'field': 'DMR_UNIT_DESC'}]

### T3 empty_numeric_limit

- admit: UNRESOLVED
- scope: ONE_RELATION_OR_VOCABULARY epistemic: MECHANICALLY_DERIVED
- delta: Introduce empty_limit_semantics (or equivalent) as an interpreted field on permit_limit rows with empty LIMIT_VALUE_NMBR, derived from comment-pattern rules; do not treat LIMIT_TYPE_CODE='ENF' alone as evidence of a numeric concentration limit in the empty slot; leave comment-blank rows explicitly unresolved rather than defaulting to report-only or numeric.
- grounding: ['sources/permit_limits.csv: DMR_COMMENT_TEXT PASS/FAIL encoding on 12 WET retest rows (LIMIT_VALUE_ID pattern 3610673260 cited in packet).', "sources/permit_limits.csv: DMR_COMMENT_TEXT 'WHEN DISCHARGING.' on representative keys 3610840341|3600904607 and 3610840340|3600904607.", 'sources/permit_limits.csv: DMR_COMMENT_TEXT referencing geometric mean of weekly values (farmington TDS rows cross-referenced in packet to documents/farmington/final_permit.txt footnotes *6-*7).', "sources/permit_limits.csv: LIMIT_TYPE_CODE='ENF' on all 57 empty-limit rows—insufficient as a classifier per packet contradictory evidence."]

### T3 document_authority

- admit: ADMIT_DISPOSABLE
- scope: ONE_RELATION_OR_VOCABULARY epistemic: SOURCE_ESTABLISHED
- delta: Add document_authority_role to permit_document via a reusable kind-to-role table grounded in packet text: final_permit maps to issued_authorization; fact_sheet and statement_of_basis map to draft_supporting; unmapped kinds remain empty. Issued authorization governs enforceable conditions in explicitly named Parts; draft/supporting documents do not establish standalone enforceable authorization; explicit incorporation governs referenced appendices.
- grounding: ['documents/gcc/final_permit.txt authorization cover (Parts I–III binding; supersedes prior permit)', 'documents/farmington/final_permit.txt authorization cover (Parts I–IV binding; supersedes prior permit)', 'documents/gcc/final_permit.txt Part II lines 149-150 (Appendix A incorporation by reference)', 'documents/gcc/fact_sheet.txt header and Sections VIII/XVI (draft/per proposed-permit/administrative-record roles)', 'documents/aztec/statement_of_basis.txt header (draft-permit document)', 'documents/farmington/statement_of_basis.txt lines 593-597 (defers to final permit)']

### T3 monitoring_frequency

- admit: UNRESOLVED
- scope: None epistemic: None
- delta: None
- grounding: []

## OBSERVED

Scope may be WORLD while admit is UNVERIFIED_PROPOSAL.

## HYPOTHESIS

Proposal-before-mutation plus epistemic admission keeps unverified legal claims out of World truth.
