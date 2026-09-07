# Evidence plans

## MEASURED

### T1 nodi_c

```json
{
  "proposition": "For FY2025 DMR measurement rows with no numeric reported result (DMR_VALUE_NMBR empty), NODI_CODE='C' has an interpretable regulatory/reporting meaning that can be mapped to a Purpose C missing-evidence state (documented no-discharge, conditional monitoring not required, other authorized no-data state, or required monitoring lacking adequate evidence).",
  "would_establish": [
    "Workspace text defining NODI code C (codebook, permit DMR instructions, NetDMR reporting guidance extract, or equivalent legend tied to this permit package).",
    "Permit-authorized reporting instructions for NM0000116 that equate a specific no-data indicator or checkbox to NODI C and state what that indicator documents.",
    "Structured source field documentation mapping NODI_CODE values to named reporting semantics."
  ],
  "would_refute": [
    "Authoritative workspace text defining NODI C as a different missing-evidence category than any candidate interpretation.",
    "Authoritative workspace text stating NODI C is not a valid or meaningful code for the affected rows.",
    "Evidence that NODI C on these rows unambiguously means optional/conditional monitoring was not required (would conflict with OPTIONAL_MONITORING_FLAG='N' on all affected rows if C were defined that way)."
  ],
  "likely_authoritative_source_types": [
    "sources/dmr_measurements.csv structural fields and co-occurrence patterns for NODI_CODE='C'",
    "sources/permit_limits.csv limit metadata for permit NM0000116 (the sole permit with C-coded FY2025 no-numeric rows)",
    "documents/gcc/final_permit.txt DMR/reporting instructions for NM0000116",
    "documents/gcc/fact_sheet.txt facility discharge and monitoring context for NM0000116"
  ],
  "insufficient_alone": [
    "Observing that NODI_CODE='C' co-occurs with empty DMR_VALUE_NMBR across 150 FY2025 rows",
    "Observing that all C-coded rows are for permit NM0000116 and OPTIONAL_MONITORING_FLAG='N'",
    "Observing that C-coded rows appear in batches of 15 parameters per monthly monitoring period",
    "Narrative that GCC discharge is infrequent or that the permittee has not discharged in years (facility history without a NODI legend)",
    "Presence of NO DISCHARGE reporting instructions in a different permit package (not NM0000116)"
  ],
  "unknowable_from_structured_data_alone": [
    "The semantic label or regulatory definition of NODI code C",
    "Whether NODI C documents no discharge, waived monitoring, absent sampling, or another authorized no-data condition",
    "Whether NODI C establishes compliance, non-applicability, or merely reports a reporting-form state"
  ]
}
```

### T1 nodi_9

```json
{
  "proposition": "NODI code '9' has a determinate regulatory or reporting meaning when a FY2025 DMR measurement row has no numeric result (empty DMR_VALUE_NMBR), sufficient to interpret no_numeric_result_case.nodi_code for Purpose C.",
  "would_establish": [
    "Explicit definition or legend for NODI code 9 in a workspace permit-package document (DMR instructions, monitoring/reporting section, or appendix codebook)",
    "A structured NODI code lookup table in workspace sources mapping code 9 to a stated meaning",
    "Permit text that names NODI code 9 and ties it to a documented no-data or not-required monitoring state for the affected parameters"
  ],
  "would_refute": [
    "Authoritative workspace text defining NODI code 9 with a meaning incompatible with a candidate interpretation",
    "Workspace evidence that NODI code 9 is unused/invalid and nonempty NODI values must remain UNINTERPRETED"
  ],
  "likely_authoritative_source_types": [
    "Final permit monitoring and DMR reporting instructions for NM0020583 (sole permit with NODI_CODE='9' rows)",
    "Permit limit DMR_COMMENT_TEXT for parameters appearing with NODI 9",
    "Structured DMR and permit-limit CSV fields documenting occurrence context (not semantics)"
  ],
  "insufficient_alone": [
    "Co-occurrence of NODI_CODE='9' with OPTIONAL_MONITORING_FLAG, parameter families (WET retest STORET codes, chlorine), or empty DMR_VALUE_NMBR",
    "Permit narrative describing conditional TRC monitoring or '(If required)' WET retests without naming NODI code 9",
    "Disjoint occurrence of NODI_CODE='C' on a different permit (NM0000116) \u2014 relation contract forbids inheriting C semantics for 9"
  ],
  "unknowable_from_structured_data_alone": [
    "The semantic label or regulatory meaning of NODI code 9; structured CSVs expose the code value and co-occurring fields but contain no codebook or legend for NODI codes"
  ]
}
```

### T1 when_discharging

```json
{
  "proposition": "The DMR comment 'WHEN DISCHARGING' (permit footnote *1) conditions stated monitoring frequencies on actual discharge occurrence at Outfall 001; numeric effluent limits remain in force for discharges when they occur; whether discharge occurred in a given monitoring period is a separate factual determination not encoded in structured limit rows.",
  "would_establish": [
    "Permit Part I.A footnote *1 text and its attachment to MEASUREMENT FREQUENCY entries marked (*1)",
    "Statement of Basis narrative tying specific parameters to 'when discharging' monitoring schedules",
    "Permit NO DISCHARGE reporting instruction for months with no discharge",
    "Permit characterization of Outfall 001 as intermittent flow with episodic backwash discharges"
  ],
  "would_refute": [
    "Permit text placing (*1) on effluent limit values themselves rather than monitoring frequencies",
    "Structured evidence that OPTIONAL_MONITORING_FLAG=Y for these rows",
    "A structured CSV field that directly records discharge occurrence per monitoring period",
    "Permit language stating limits are waived or inapplicable whenever discharge is intermittent"
  ],
  "likely_authoritative_source_types": [
    "final_permit narrative for NM0028762 (Aztec) \u2014 sole permit bearing all 17 WHEN DISCHARGING rows",
    "statement_of_basis for NM0028762 explaining monitoring frequency rationale",
    "permit_limits.csv rows linking DMR_COMMENT_TEXT to limit sets and parameters"
  ],
  "insufficient_alone": [
    "DMR_COMMENT_TEXT string in permit_limits.csv without permit-package footnote context",
    "LIMIT_FREQ_OF_ANALYSIS_CODE and LIMIT_SAMPLE_TYPE_CODE without permit narrative",
    "OPTIONAL_MONITORING_FLAG=N (does not encode discharge-conditioning semantics)",
    "DMR measurement rows showing reported values without establishing no-discharge periods"
  ],
  "unknowable_from_structured_data_alone": [
    "Whether discharge actually occurred during any specific FY2025 monitoring period",
    "How permittee should mark or report no-discharge months beyond what permit narrative states",
    "Whether a reported numeric value was collected on a discharge day versus a non-discharge day within a month"
  ]
}
```

### T1 geometric_mean

```json
{
  "proposition": "A permit-limit DMR comment containing 'GEOMETRIC MEAN' establishes that compliance evaluation cannot treat each monitoring-period DMR value as an ordinary single-period numeric comparison against the limit; instead, reported values must reflect an aggregated statistic (geometric mean) computed over sub-period samples.",
  "would_establish": [
    "Permit narrative or limit comment text that defines geometric-mean reporting as the required reported quantity",
    "Identification of the aggregation window (e.g., weekly values) and the statistic (geometric mean)",
    "Evidence that structured limit rows encode a non-single-period comparison basis distinct from ordinary AVG/MAX/MIN single-period limits",
    "Permit language tying numeric effluent limits to the same aggregated statistic used for reporting",
    "DMR measurement structure showing sub-period sample values needed to compute the aggregate"
  ],
  "would_refute": [
    "Authoritative text stating individual monitoring-period values are directly comparable to the limit despite the comment",
    "Structured fields showing STATISTICAL_BASE_TYPE_CODE or equivalent already encode geometric-mean comparison for affected limits",
    "Evidence that the geometric-mean comment applies only to reporting display and not to limit comparison semantics",
    "Proof that the comment is parameter-specific (TDS) but incorrectly duplicated to unrelated parameters, making a single global interpretation invalid"
  ],
  "likely_authoritative_source_types": [
    "Permit final text footnotes and limit tables (documents/farmington/final_permit.txt for NM0020583)",
    "Statement of basis discussion of monitoring frequency and limit basis (documents/farmington/statement_of_basis.txt)",
    "Structured permit_limits.csv DMR_COMMENT_TEXT, STATISTICAL_BASE_TYPE_CODE, LIMIT_FREQ_OF_ANALYSIS_CODE fields",
    "Structured dmr_measurements.csv monitoring period granularity and reported values"
  ],
  "insufficient_alone": [
    "Presence of 'GEOMETRIC MEAN' substring in DMR_COMMENT_TEXT without permit narrative context",
    "STATISTICAL_BASE_TYPE_CODE = AVG on rows bearing the comment (codes AVG/MAX/MIN, never a geometric-mean code)",
    "Co-occurrence of monthly MONITORING_PERIOD_END_DATE values with weekly-frequency limit codes",
    "Limit-set-level comment propagation to multiple unrelated parameters sharing one LIMIT_SET_ID"
  ],
  "unknowable_from_structured_data_alone": [
    "Whether a reported monthly DMR value already represents the geometric mean of weekly samples",
    "How weekly sub-period sample values should be grouped before computing geometric mean",
    "Whether numeric limits (e.g., 497 mg/L 30-day average TDS net increase) are compared against geometric-mean weekly values or a different aggregation",
    "Whether geometric-mean reporting instructions apply to non-TDS parameters that inherit the limit-set comment"
  ]
}
```

### T1 pass_fail

```json
{
  "proposition": "PASS=0 / FAIL=1 is a binary whole-effluent-toxicity (WET) outcome code\u20140 means pass and 1 means fail\u2014reported in the DMR concentration-max field; it is not a measured pollutant concentration and is not an ordinary numeric concentration-limit comparison.",
  "would_establish": [
    "DMR_COMMENT_TEXT on affected permit-limit rows explicitly defining PASS=0 and FAIL=1 and instructing reporters to enter 0 or 1 in the concentration-max field",
    "Permit Part II WET reporting table mapping TEM/retest STORET codes to enter 0 when NOEC is at or above the critical dilution and 1 when below",
    "Structured limit rows for pass/fail parameters using unit code 9A (pass=0;fail=1) with no numeric limit value, alongside companion TOM/TQM parameters for numeric NOEC reporting",
    "DMR measurement rows reporting literal 0 with 9A pass=0;fail=1 units for TEM3D"
  ],
  "would_refute": [
    "Authoritative text treating reported 0/1 values as mg/L, %, or other concentration magnitudes to be compared against LIMIT_VALUE_NMBR",
    "Evidence that pass/fail parameters share numeric limit thresholds comparable to conventional pollutant limits",
    "Permit language equating the 0/1 entry with the NOEC concentration itself rather than a coded pass/fail outcome"
  ],
  "likely_authoritative_source_types": [
    "permit_limits.csv DMR_COMMENT_TEXT on NM0020583 WET limit-set rows",
    "documents/farmington/final_permit.txt Part II WET reporting requirements and NOEC/failure definitions",
    "dmr_measurements.csv reported values and units for TEM3D and retest parameters"
  ],
  "insufficient_alone": [
    "Presence of LIMIT_VALUE_TYPE_CODE C3 or STATISTICAL_BASE MAX without the DMR comment or permit narrative",
    "Parameter descriptions containing 'Pass/Fail' without the explicit 0/1 coding legend",
    "Co-occurrence of 0 reported values and empty LIMIT_VALUE_NMBR on retest rows without permit reporting instructions"
  ],
  "unknowable_from_structured_data_alone": [
    "That 0 means NOEC at or above critical dilution (pass) and 1 means NOEC below critical dilution (fail)\u2014this substantive criterion is stated in permit narrative, not in CSV fields alone",
    "Definition of critical dilution and acute test failure for WET\u2014requires permit Part II text"
  ]
}
```

### T1 empty_numeric_limit

```json
{
  "proposition": "When LIMIT_VALUE_NMBR is empty in permit limit or DMR rows, the row has a single uniform semantic class: numeric effluent limit, report-only monitoring requirement, or another distinct non-numeric category.",
  "would_establish": [
    "Permit Part I limit tables showing 'Report' or 'N/A' in the cell corresponding to an empty LIMIT_VALUE_NMBR row, while a sibling row for the same pollutant carries the numeric limit in another statistical-base column",
    "Structured rows where empty LIMIT_VALUE_NMBR co-occurs with non-numeric unit descriptors (for example pass=0;fail=1) or DMR_COMMENT_TEXT describing pass/fail or geometric-mean reporting rather than a concentration limit",
    "Permit footnotes tying specific limit-table cells to monitoring/reporting-only obligations (for example 'Report the geometric mean value of weekly values') without stating a numeric effluent limit for that cell"
  ],
  "would_refute": [
    "A workspace codebook or permit narrative stating that empty LIMIT_VALUE_NMBR always denotes a numeric limit stored elsewhere",
    "Document or structured evidence that every empty LIMIT_VALUE_NMBR row is interchangeable report-only monitoring with no special pass/fail or N/A-column semantics",
    "Demonstration that all 57 empty-limit rows share one classification rule sufficient for numeric comparison under Purpose A"
  ],
  "likely_authoritative_source_types": [
    "sources/permit_limits.csv and sources/dmr_measurements.csv field co-occurrence patterns for empty LIMIT_VALUE_NMBR rows",
    "documents/*/final_permit.txt Part I effluent limit tables mapping Report/N/A cells to monitoring requirements",
    "DMR_COMMENT_TEXT and unit-code fields on empty-limit structured rows (pass/fail encoding, geometric mean instructions, WHEN DISCHARGING qualifiers)"
  ],
  "insufficient_alone": [
    "LIMIT_TYPE_CODE=ENF on all 57 empty rows (enforceability flag does not establish a numeric limit value)",
    "Presence of LIMIT_VALUE_STANDARD_UNITS unit metadata without LIMIT_VALUE_NMBR (units alone do not supply a comparison value)",
    "Document inventory or parameter names without the Part I limit-table cell text for the matching statistical base"
  ],
  "unknowable_from_structured_data_alone": [
    "Whether an empty LIMIT_VALUE_NMBR row marked ENF is report-only because the permit table cell is 'Report' rather than a numeric limit",
    "Whether empty Q1/Q2 mass-load rows are non-applicable N/A columns versus active numeric limits",
    "Full pass/fail WET compliance semantics where only DMR_COMMENT_TEXT and unit descriptors exist and permit PDF text lacks the PASS=0/FAIL=1 instruction"
  ]
}
```

### T1 document_authority

```json
{
  "proposition": "Without ranking from filename kinds, inventoried permit-package documents have distinct epistemic roles, and when their narratives disagree the issued permit text (as self-defined by its cover page and internal cross-references) governs over supporting or explanatory package documents.",
  "would_establish": [
    "Final permit cover pages that authorize discharge only 'in accordance with' named Parts I\u2013III/IV 'hereof', defining the binding permit corpus by internal part structure rather than filename labels.",
    "Final-permit cross-references that incorporate specific appendices (e.g., 'Appendix A of Part II of this permit') as part of the issued permit.",
    "Fact-sheet or statement-of-basis language framing content as 'draft permit', 'proposed', or 'DRAFT PERMIT RATIONALE', plus directions such as 'See the draft permit for limitations', showing those documents explain rather than independently establish enforceable conditions.",
    "Reasonable-potential extracts labeled as fact-sheet appendices or limit-calculation workpapers, showing they support derivation rather than standalone authorization.",
    "Explicit inter-document precedence clauses (e.g., 'in the event of conflict \u2026 shall prevail') naming which package document controls."
  ],
  "would_refute": [
    "Text stating fact sheets, statements of basis, or reasonable-potential memos are enforceable permit conditions independent of the issued permit.",
    "Text establishing a hierarchy based solely on filename kind (final_permit > fact_sheet) without permit-internal incorporation language.",
    "Absence of any issued-permit self-definition of governing parts, leaving no textual basis to prefer one inventoried file over another.",
    "Evidence that all 12 inventoried files are co-equal binding conditions with no precedence rule."
  ],
  "likely_authoritative_source_types": [
    "documents/*/final_permit.txt cover pages and part headers",
    "documents/*/final_permit.txt internal cross-references to appendices and parts",
    "documents/*/fact_sheet.txt and documents/*/statement_of_basis.txt sections on draft/proposed rationale and final determination",
    "documents/*/reasonable_potential.txt headers tying calculations to fact sheets",
    "sources/document_inventory.json for permit-to-document association only (not hierarchy)"
  ],
  "insufficient_alone": [
    "document_inventory.json document_kind field values (final_permit, fact_sheet, etc.)",
    "Filename or path tokens without accompanying permit text",
    "Structured CSV fields (permit_limits.csv, dmr_measurements.csv)",
    "construction.py UNRESOLVED marker text",
    "Training-data NPDES process descriptions"
  ],
  "unknowable_from_structured_data_alone": [
    "Which narrative permit conditions exist in each package document",
    "Which document governs when issued-permit text and a supporting document disagree",
    "Whether a separate minor-modification extract is incorporated into the issued permit or stands alone",
    "Conditional monitoring language requiring discharge-occurrence or seasonal narrative (Purposes B/C) without reading permit parts"
  ]
}
```

### T1 monitoring_frequency

```json
{
  "proposition": "Each distinct LIMIT_FREQ_OF_ANALYSIS_CODE value in permit_limits.csv encodes a specific monitoring frequency obligation (samples or measurements per calendar period, or a non-periodic monitoring mode) that can be read directly from workspace permit-package text or an in-workspace code legend.",
  "would_establish": [
    "An explicit codebook, glossary, or field definition in workspace sources naming LIMIT_FREQ_OF_ANALYSIS_CODE values and their meanings",
    "Permit Part I monitoring tables that state a MEASUREMENT FREQUENCY in plain language for the same permit number and pollutant/parameter as a structured permit_limits.csv row, allowing audited pairing of code to frequency",
    "Narrative statement-of-basis or fact-sheet sections that state monitoring frequencies for the same facility parameters represented in structured limits",
    "Permit language defining non-calendar modes (e.g., continuous monitoring, conditional retest reporting) for rows carrying sentinel-looking codes such as 99/99 or 09/99"
  ],
  "would_refute": [
    "Workspace text stating that LIMIT_FREQ_OF_ANALYSIS_CODE values are placeholders, deprecated, or not authoritative for monitoring frequency",
    "Demonstrated permit-text frequencies that systematically contradict the code paired to the same permit and parameter in permit_limits.csv",
    "Evidence that the same code value is used for materially different monitoring frequencies across permits without any documentary explanation"
  ],
  "likely_authoritative_source_types": [
    "documents/*/final_permit.txt Part I limitation and monitoring requirement tables",
    "documents/*/statement_of_basis.txt monitoring frequency discussion sections",
    "documents/*/fact_sheet.txt monitoring frequency for limited parameters sections",
    "sources/permit_limits.csv for code inventory and permit-parameter pairing only (not as a standalone legend)"
  ],
  "insufficient_alone": [
    "Unique code strings and their counts in permit_limits.csv",
    "DMR_FREQ_OF_ANALYSIS_CODE co-occurrence patterns in dmr_measurements.csv",
    "Training-data or general EPA ICIS-NPDES conventions not reproduced in workspace files",
    "Permit narrative that discusses monitoring frequency without matching the same permit number and parameter as the coded limit row"
  ],
  "unknowable_from_structured_data_alone": [
    "The semantic mapping from opaque code tokens (05/WK, 01/07, 01/01, etc.) to monitoring frequency, because structured sources contain the codes but no in-workspace codebook table",
    "Whether sentinel codes 99/99 and 09/99 denote continuous monitoring or conditional/event-triggered reporting without permit-text pairing for those exact rows",
    "The general NN/XX encoding rule (count over period unit) inferred only from pairwise correlation rather than an explicit field definition"
  ]
}
```

### T2 nodi_c

```json
{
  "proposition": "NODI code C on a FY2025 DMR row with no numeric result (empty DMR_VALUE_NMBR) has a specific, classifiable missing-evidence meaning under Purpose C (e.g., documented no-discharge, conditional monitoring not required, other documented no-data state, or missing required evidence).",
  "would_establish": [
    "Workspace text defining NODI codes or explicitly mapping code C to a missing-evidence category",
    "Permit-package instructions for permit NM0000116 (sole permit bearing all 150 C occurrences) stating how to report no-discharge or no-data on DMRs and naming code C or an equivalent ICIS field",
    "A structured codebook or legend table in sources/ linking NODI_CODE values to definitions"
  ],
  "would_refute": [
    "Explicit workspace text defining NODI C as something other than a Purpose C missing-evidence category (e.g., a numeric qualifier or compliance determination)",
    "Evidence that NODI C rows are heterogeneous in ways requiring separate semantic resolutions rather than one code-level meaning"
  ],
  "likely_authoritative_source_types": [
    "EPA/ICIS NODI codebook or DMR reporting guidance (not present in workspace)",
    "Permit NM0000116 package narrative on DMR no-discharge / no-data reporting (documents/gcc/*)",
    "Structured NODI legend in sources/ (confirmed absent)"
  ],
  "insufficient_alone": [
    "Structural correlation: all 150 FY2025 NODI C rows are permit NM0000116, limit set DISCHARGE STORM RUNOFFS FROM STORAGE, OPTIONAL_MONITORING_FLAG=N, and empty DMR_VALUE_NMBR",
    "Permit narrative that discharges are infrequent or restricted to storm-runoff overflow events without naming NODI C",
    "Analogous NO DISCHARGE checkbox instructions in a different permit (NM0028762) that do not reference NODI codes"
  ],
  "unknowable_from_structured_data_alone": [
    "The semantic label or regulatory category assigned to NODI code C",
    "Whether NODI C asserts no discharge occurred, monitoring was not required, or another no-data reason",
    "Whether empty numeric fields with NODI C satisfy or excuse FY2025 monitoring expectations"
  ]
}
```

### T2 nodi_9

```json
{
  "proposition": "NODI_CODE='9' on a FY2025 DMR measurement row with an empty DMR_VALUE_NMBR has a determinate regulatory meaning (e.g., documented no-discharge, monitoring not required, not applicable, or missing required evidence) that can be assigned without importing NODI code 'C' semantics.",
  "would_establish": [
    "Workspace text that defines NODI code 9 or maps it to a specific no-result reporting state for DMR rows",
    "Permit or DMR reporting instructions for permit NM0020583 that explicitly name code 9 or an equivalent no-data indicator tied to the parameters and periods where NODI=9 appears",
    "A structured codebook or legend in sources/ linking NODI_CODE values to meanings"
  ],
  "would_refute": [
    "Absence of any NODI code definition or legend anywhere in workspace sources or documents",
    "Evidence that NODI=9 rows fall into materially different monitoring contexts requiring different interpretations, so a single inherited meaning (including from NODI=C) is unwarranted",
    "Permit text that explains when values may be omitted but never names or equates those situations to NODI code 9"
  ],
  "likely_authoritative_source_types": [
    "sources/dmr_measurements.csv and sources/permit_limits.csv for occurrence patterns, parameters, optional-monitoring flags, and frequencies",
    "documents/farmington/final_permit.txt for NM0020583 WET retest reporting rules and conditional TRC monitoring footnote *5",
    "DMR form general instructions referenced by permits but not present in the workspace"
  ],
  "insufficient_alone": [
    "Co-occurrence of NODI=9 with OPTIONAL_MONITORING_FLAG=Y or LIMIT_FREQ_OF_ANALYSIS_CODE=09/99 on WET retest parameters",
    "Co-occurrence of NODI=9 with footnote *5 conditional chlorine monitoring on parameter 50060",
    "Aztec permit NO DISCHARGE box instructions (different permit; bears on NODI=C at NM0000116, not NODI=9 at NM0020583)",
    "Structural correlation between empty DMR_VALUE_NMBR and nonempty NODI_CODE without a code legend"
  ],
  "unknowable_from_structured_data_alone": [
    "The regulatory label or narrative meaning of ICIS/NPDES NODI code 9",
    "Whether a given NODI=9 row documents optional monitoring not performed, conditional monitoring not triggered, or missing required evidence",
    "Whether LIMIT_FREQ_OF_ANALYSIS_CODE value 09/99 itself encodes optional/not-applicable scheduling (no workspace legend for frequency codes)"
  ]
}
```

### T2 when_discharging

```json
{
  "proposition": "The permit-limit comment 'WHEN DISCHARGING' conditions monitoring requirements and associated effluent-limit compliance obligations on actual discharge occurrence; when no discharge occurs in a monitoring/reporting period, monitoring is not required and the permittee reports no discharge instead.",
  "would_establish": [
    "Permit narrative text (final permit footnotes, statement of basis) that defines footnote *1 or equivalent language as qualifying monitoring frequencies with 'when discharging'",
    "Permit text linking intermittent/no-discharge periods to alternate reporting (NO DISCHARGE box) rather than parameter monitoring",
    "Structured rows showing DMR_COMMENT_TEXT 'WHEN DISCHARGING.' attached to limit sets for the affected permit (NM0028762) with non-optional monitoring (OPTIONAL_MONITORING_FLAG = N)",
    "Correspondence between permit-table monitoring frequencies marked (*1) and the structured comment text"
  ],
  "would_refute": [
    "Permit text stating monitoring frequencies apply regardless of discharge occurrence for these parameters",
    "Evidence that 'WHEN DISCHARGING' is purely informational with no effect on monitoring or limit applicability",
    "Structured codebook or field legend defining DMR_COMMENT_TEXT as unrelated to discharge conditioning",
    "Permit text requiring monitoring even during no-discharge months without an alternate no-discharge reporting path"
  ],
  "likely_authoritative_source_types": [
    "documents/aztec/final_permit.txt (NM0028762 effluent limits, monitoring table, footnotes, no-discharge reporting instructions)",
    "documents/aztec/statement_of_basis.txt (NM0028762 rationale for monitoring frequencies 'when discharging')",
    "sources/permit_limits.csv (DMR_COMMENT_TEXT, limit set names, optional monitoring flag for affected rows)",
    "sources/dmr_measurements.csv (whether reported values or NODI codes document no-discharge periods)"
  ],
  "insufficient_alone": [
    "DMR_COMMENT_TEXT string presence in permit_limits.csv without permit narrative defining the phrase",
    "Monitoring frequency codes (LIMIT_FREQ_OF_ANALYSIS_CODE) without permit footnote cross-reference",
    "Reported numeric DMR values alone (do not establish whether discharge occurred or whether monitoring was required in a given period)",
    "OPTIONAL_MONITORING_FLAG = N alone (establishes monitoring is not optional in general, not the discharge condition)"
  ],
  "unknowable_from_structured_data_alone": [
    "Whether discharge actually occurred during any specific FY2025 monitoring period for a limit row bearing this comment",
    "The full semantic definition of DMR_COMMENT_TEXT (no structured codebook in workspace)",
    "Whether a missing numeric result in a period reflects no discharge, skipped monitoring during discharge, or another no-data state"
  ]
}
```

### T2 geometric_mean

```json
{
  "proposition": "A DMR_COMMENT_TEXT containing 'GEOMETRIC MEAN' requires that effluent-limit comparison use an aggregated geometric mean across weekly measurements within a reporting period, not a direct numeric comparison of an individual monitoring-period DMR value to the permit limit.",
  "would_establish": [
    "Permit narrative text tied to footnote *6 (or equivalent) stating that total dissolved solids at Outfall 001 must be reported as the geometric mean of weekly values.",
    "Permit text linking numeric effluent limits for TDS (or net TDS increase) to that geometric-mean reporting basis rather than to individual weekly sample results.",
    "Structured rows where the comment applies only to TDS (parameter 70295) and where DMR monitoring frequency is weekly, supporting an aggregation window before comparison."
  ],
  "would_refute": [
    "Permit text requiring geometric-mean aggregation for every parameter row carrying the shared DMR comment (e.g., BOD, E. coli, pH).",
    "Explicit permit language that an individual DMR monitoring-period value for TDS may be compared directly to the effluent limit without first computing the geometric mean of weekly values.",
    "A structured codebook or STATISTICAL_BASE_TYPE_CODE legend equating the comment to ordinary single-period AVG comparison."
  ],
  "likely_authoritative_source_types": [
    "Final permit Part I limit tables and footnotes for NM0020583 (Farmington)",
    "Permit limit schedule rows in sources/permit_limits.csv (DMR_COMMENT_TEXT, PARAMETER_CODE, LIMIT_FREQ_OF_ANALYSIS_CODE)",
    "DMR measurement rows in sources/dmr_measurements.csv showing monitoring-period granularity"
  ],
  "insufficient_alone": [
    "Presence of 'GEOMETRIC MEAN' in DMR_COMMENT_TEXT on all 40 permit_limit rows without parameter-specific permit narrative.",
    "STATISTICAL_BASE_TYPE_CODE=AVG in structured limit and DMR rows.",
    "Individual monthly DMR values in dmr_measurements.csv without accompanying weekly sample series in structured data.",
    "Geometric-mean discussion in statement-of-basis for E. coli WQS (different pollutant and aggregation basis than footnote *6 TDS language)."
  ],
  "unknowable_from_structured_data_alone": [
    "Whether a given DMR monitoring-period value already represents the geometric mean of weekly samples versus a single weekly or composite measurement.",
    "The exact calendar window for computing the geometric mean (e.g., calendar month vs. other reporting period) beyond permit monthly reporting schedule.",
    "Whether geometric-mean aggregation applies to non-TDS parameters that inherit the limit-set comment in CSV export."
  ]
}
```

### T2 pass_fail

```json
{
  "proposition": "For permit limit rows whose DMR_COMMENT_TEXT contains '(PASS = 0  FAIL = 1)', the coded values 0 and 1 are binary whole-effluent-toxicity (WET) pass/fail indicators entered in the DMR concentration (MAX) field\u2014not measured pollutant concentrations to be compared against a numeric effluent limit.",
  "would_establish": [
    "DMR_COMMENT_TEXT explicitly defining PASS=0 and FAIL=1 as reporting codes and instructing permittees to enter 0 or 1 in the concentration MAX field",
    "Permit Part II reporting table mapping 0/1 to WET survival outcome relative to critical dilution (pass when NOEC is not below critical dilution; fail when it is)",
    "Structured limit rows for pass/fail parameters (e.g., TEM3D, retest STORET codes) with no numeric LIMIT_VALUE_NMBR and unit descriptor 'pass=0;fail=1'",
    "Permit Part I WET schedule showing 'Report' (not a numeric effluent limit) for toxicity testing",
    "Permit definition of acute test failure based on statistical survival effects at/below critical dilution rather than exceedance of a concentration limit",
    "DMR measurement rows where pass/fail parameters report DMR_VALUE_NMBR of 0 with matching pass/fail unit codes and empty limit numeric fields"
  ],
  "would_refute": [
    "Numeric LIMIT_VALUE_NMBR present on pass/fail-coded parameters enabling ordinary <= or >= concentration comparison",
    "Permit text treating 0 and 1 as pollutant concentration magnitudes with concentration units (mg/L, %, etc.)",
    "Evidence that DMR_VALUE_NMBR 0/1 should be compared to LIMIT_VALUE_NMBR as enforceable numeric limits for the pass/fail parameters"
  ],
  "likely_authoritative_source_types": [
    "sources/permit_limits.csv DMR_COMMENT_TEXT and limit-value fields for WET limit-set schedule rows",
    "documents/farmington/final_permit.txt Part I WET monitoring schedule and footnote 9",
    "documents/farmington/final_permit.txt Part II WET toxicity definitions and DMR reporting requirement table",
    "sources/dmr_measurements.csv reported values for pass/fail STORET parameters in FY2025"
  ],
  "insufficient_alone": [
    "LIMIT_VALUE_QUALIFIER_CODE = MAX without accompanying comment or permit reporting instructions",
    "STATISTICAL_BASE_TYPE_CODE = VA on its own",
    "Parameter descriptions containing 'Pass/Fail' without DMR_COMMENT_TEXT or permit narrative",
    "Empty DMR_VALUE_NMBR on optional retest parameters without permit context",
    "Co-occurrence of 0/1 values in DMR_VALUE_NMBR without unit code pass=0;fail=1"
  ],
  "unknowable_from_structured_data_alone": [
    "The numeric value of critical dilution used to judge pass vs fail",
    "Full toxicological test-acceptability criteria and retest triggering logic",
    "Whether a specific FY2025 measurement period's WET test passed or failed when no numeric result was reported on optional retest rows",
    "Distinction between pass/fail binary parameters and separate NOEC-percent reporting parameters (TOM3D/TOM6C) within the same limit set without permit Part II reporting table"
  ]
}
```

### T2 empty_numeric_limit

```json
{
  "proposition": "When LIMIT_VALUE_NMBR is empty in permit limit or DMR rows, the row has a single classifiable role: enforceable numeric limit, report-only monitoring, or another homogeneous category that can be applied before numeric comparison.",
  "would_establish": [
    "A workspace codebook or field legend mapping empty LIMIT_VALUE_NMBR to one obligation class",
    "Permit narrative or structured comment text showing that all empty-limit rows share the same compliance semantics",
    "Evidence that LIMIT_VALUE_TYPE_CODE, LIMIT_TYPE_CODE, or LIMIT_VALUE_QUALIFIER_CODE uniformly distinguishes numeric limits from report-only rows when LIMIT_VALUE_NMBR is empty",
    "Document text establishing a numeric limit value stored outside LIMIT_VALUE_NMBR for empty-limit rows intended for concentration comparison"
  ],
  "would_refute": [
    "Permit tables listing 'Report' (not a numeric concentration) as the effluent limitation for parameters whose structured rows have empty LIMIT_VALUE_NMBR",
    "Permit or DMR comment text defining pass/fail or 0/1 coded reporting instead of numeric concentration limits",
    "Permit footnotes conditioning monitoring on discharge occurrence for empty-limit rows",
    "Demonstration that empty LIMIT_VALUE_NMBR rows partition into multiple materially different obligation classes with no single classifier"
  ],
  "likely_authoritative_source_types": [
    "sources/permit_limits.csv and sources/dmr_measurements.csv field patterns for rows with empty LIMIT_VALUE_NMBR",
    "DMR_COMMENT_TEXT on empty-limit permit_limit rows",
    "documents/*/final_permit.txt effluent limitation tables and footnotes",
    "documents/*/final_permit.txt Part II WET reporting instructions"
  ],
  "insufficient_alone": [
    "LIMIT_TYPE_CODE = ENF (present on all 57 empty-limit rows and many numeric-limit rows)",
    "LIMIT_VALUE_TYPE_CODE values C1/C2/C3/Q1/Q2 (same codes appear on both empty and nonempty LIMIT_VALUE_NMBR rows)",
    "Empty LIMIT_VALUE_QUALIFIER_CODE (true for all empty-limit rows but provides no positive class)",
    "OPTIONAL_MONITORING_FLAG alone (Y/N appears on both empty-limit subclasses)",
    "Correlation between empty LIMIT_VALUE_NMBR and absence of FY2025 DMR measurement rows (describes data coverage, not obligation semantics)"
  ],
  "unknowable_from_structured_data_alone": [
    "Whether a given empty-limit row is report-only monitoring versus pass/fail coded WET versus geometric-mean reporting versus conditional when-discharging monitoring",
    "The numeric limit value (if any) for parameters whose permit limitation is stated as 'Report'",
    "Whether discharge occurred for when-discharging conditional rows",
    "The applicable comparison operator for rows with empty LIMIT_VALUE_QUALIFIER_CODE"
  ]
}
```

### T2 document_authority

```json
{
  "proposition": "Inventoried permit-package documents can be assigned authoritative roles and a precedence rule for disagreement using only their narrative text (not inventory filename or document_kind labels).",
  "would_establish": [
    "Final-permit cover-page language identifying an issued AUTHORIZATION TO DISCHARGE and binding conditions set forth in named permit parts 'hereof'",
    "Fact-sheet or statement-of-basis text framed as FOR THE DRAFT NPDES PERMIT, describing proposed/draft permit conditions and rationale rather than issued authorization",
    "Cross-references within issued permit text that incorporate appendices or other parts by permit-part citation (e.g., Appendix A of Part II of this permit; Part IV of the permit)",
    "Explicit supersession language in issued permit text replacing a prior permit issuance",
    "Supporting documents that defer enforceable limits to the draft/final permit text (e.g., 'See the draft permit for limitations')"
  ],
  "would_refute": [
    "Text stating that fact sheets, statements of basis, or reasonable-potential worksheets are independently enforceable authorization documents co-equal with the issued permit",
    "A workspace-local codebook or inventory legend that ranks document_kind values as a governing hierarchy",
    "Only document_inventory.json metadata (path, sha256, bytes, document_kind) with no narrative extracts"
  ],
  "likely_authoritative_source_types": [
    "documents/*/final_permit.txt cover pages and permit-part integration language",
    "documents/*/fact_sheet.txt and documents/*/statement_of_basis.txt draft-framing and proposed-condition sections",
    "documents/*/part_ii_appendix.txt and documents/*/part_iv.txt where cited from issued permit text",
    "sources/document_inventory.json for inventory membership only (not hierarchy)"
  ],
  "insufficient_alone": [
    "document_inventory.json document_kind labels (final_permit, fact_sheet, statement_of_basis, reasonable_potential, minor_modification, part_ii_appendix, part_iv)",
    "documents/INDEX.md byte counts and facility groupings",
    "Filename stems or PDF path strings under sources/"
  ],
  "unknowable_from_structured_data_alone": [
    "Which inventoried document governs when narrative texts disagree",
    "Whether fact_sheet or statement_of_basis conditions are binding obligations versus explanatory draft rationale",
    "Whether part_iv or part_ii_appendix extracts are incorporated permit components versus independent authorities",
    "Whether minor_modification text modifies or supersedes issued final-permit Part I limits"
  ]
}
```

### T2 monitoring_frequency

```json
{
  "proposition": "Each distinct LIMIT_FREQ_OF_ANALYSIS_CODE value in permit_limits.csv denotes a specific monitoring frequency obligation (e.g., daily, weekly, five-times-weekly) that can be interpreted without external legend.",
  "would_establish": [
    "An explicit codebook or field definition in workspace sources mapping each LIMIT_FREQ_OF_ANALYSIS_CODE token to a stated monitoring frequency",
    "Permit-package narrative that uses the same opaque code tokens (05/WK, 01/07, 01/01, etc.) and defines their meaning",
    "Authoritative permit-table rows for the same permit number and parameter showing a human-readable MEASUREMENT FREQUENCY that unambiguously corresponds to each code when joined to structured limit rows"
  ],
  "would_refute": [
    "Workspace sources showing LIMIT_FREQ_OF_ANALYSIS_CODE values are arbitrary identifiers with no stable frequency semantics",
    "Demonstrated one-to-many mapping where the same code corresponds to materially different monitoring schedules in authoritative permit text",
    "Absence of any permit narrative frequency for parameters bearing a given code across all facilities in the workspace"
  ],
  "likely_authoritative_source_types": [
    "documents/*/final_permit.txt effluent limit tables with MEASUREMENT FREQUENCY columns and footnotes",
    "documents/*/statement_of_basis.txt monitoring-frequency discussion sections",
    "sources/permit_limits.csv LIMIT_FREQ_OF_ANALYSIS_CODE field joined on EXTERNAL_PERMIT_NMBR and PARAMETER_DESC",
    "sources/dmr_measurements.csv paired LIMIT_FREQ_OF_ANALYSIS_CODE and DMR_FREQ_OF_ANALYSIS_CODE values"
  ],
  "insufficient_alone": [
    "Unique value listing or co-occurrence patterns in permit_limits.csv without matching permit narrative text",
    "DMR_FREQ_OF_ANALYSIS_CODE pairings that diverge from LIMIT_FREQ_OF_ANALYSIS_CODE on some rows",
    "Statement-of-basis prose describing frequencies in plain language without using the structured code tokens",
    "construction.py require_interpreted scaffolding showing codes are currently UNINTERPRETED"
  ],
  "unknowable_from_structured_data_alone": [
    "The decoding rule for the NN/XX or NN/WK token format",
    "Whether 09/99 denotes a calendar schedule versus event-triggered retest reporting",
    "Whether 01/90 always means once per quarter versus other long-interval schedules (e.g., once per permit term) for codes not present in structured limits",
    "Footnote-conditioned sampling constraints (e.g., 'sampling on at least five different days', 'when discharging') that modify how a nominal frequency applies"
  ]
}
```

### T3 nodi_c

```json
{
  "proposition": "NODI code 'C' on a FY2025 DMR row with no numeric reported result (empty DMR_VALUE_NMBR) has an authoritative workspace-grounded meaning that determines how Purpose C should classify the row before missing-evidence disposition.",
  "would_establish": [
    "A workspace permit-package or structured-source text defining NODI code C (for example DMR reporting instructions, a NetDMR or form code legend, or permit-specific language tying code C to a documented no-data state).",
    "Explicit NM0000116 permit language linking blank numeric results or a specific reporting code to no-discharge, not-applicable, or other missing-evidence categories."
  ],
  "would_refute": [
    "Workspace text defining NODI code C with a meaning that rules out a candidate interpretation (for example a legend stating C means laboratory invalidation while permit text required treating it as documented no discharge)."
  ],
  "likely_authoritative_source_types": [
    "NM0000116 permit-package narrative under documents/gcc/ on DMR and no-discharge reporting",
    "Structured NODI or DMR field codebook tables in sources/ if present",
    "Representative FY2025 no-numeric-result rows in sources/dmr_measurements.csv showing co-occurring permit and monitoring fields for NODI_CODE='C'"
  ],
  "insufficient_alone": [
    "Structural correlation that NODI_CODE='C' always co-occurs with empty DMR_VALUE_NMBR",
    "Exclusive association of code C with permit NM0000116 across 150 FY2025 no-result rows",
    "Permit narrative about intermittent storm runoff, retention-pond overflow, or effluent prohibitions without defining NODI code C",
    "NO DISCHARGE reporting instructions appearing in a different permit package (NM0028762)"
  ],
  "unknowable_from_structured_data_alone": [
    "The regulatory or form-defined meaning of NODI code C; structured CSVs store the code value but provide no legend or definition table."
  ]
}
```

### T3 nodi_9

```json
{
  "proposition": "NODI_CODE='9' on a FY2025 DMR measurement row with no numeric reported result (DMR_VALUE_NMBR empty) has a determinate regulatory/reporting meaning that can be applied uniformly across all 36 affected occurrences.",
  "would_establish": [
    "Workspace text (permit package for NM0020583, DMR reporting instructions, or structured codebook) that explicitly defines NODI code 9 or maps it to a named no-data / not-applicable / no-discharge state",
    "Permit language for NM0020583 tying a specific DMR reporting mechanism (checkbox, comment, or code) to the absence of numeric results for the parameters that carry NODI 9 in the structured extract",
    "A single coherent interpretation supported by both structured correlation and authoritative permit text for all parameter families sharing NODI 9"
  ],
  "would_refute": [
    "Evidence that NODI 9 means the same thing as NODI code C (used on a different permit with different parameters and monitoring flags)",
    "Evidence that NODI 9 uniformly means 'no discharge' for all 36 rows including optional WET retest parameters",
    "A workspace NODI legend showing code 9 with a definition that contradicts permit-conditional monitoring for TRC or '(If required)' WET retests"
  ],
  "likely_authoritative_source_types": [
    "sources/dmr_measurements.csv \u2014 occurrence profile, parameter codes, optional_monitoring_flag, permit association",
    "sources/permit_limits.csv \u2014 limit comments, optional monitoring flags, frequency codes for NODI-9-linked limits",
    "documents/farmington/final_permit.txt \u2014 NM0020583 monitoring/reporting conditions for TRC and WET retests",
    "documents/farmington/statement_of_basis.txt \u2014 TRC monitoring rationale for NM0020583",
    "Cross-permit comparison via structured rows for NODI code C on NM0000116 (to test inheritance prohibition)"
  ],
  "insufficient_alone": [
    "Structured correlation showing NODI 9 appears only on permit NM0020583 with empty DMR_VALUE_NMBR",
    "Permit footnote *5 stating TRC is monitored when chlorine is used (does not name NODI 9)",
    "Permit text labeling WET retests as '(If required)' (does not name NODI 9)",
    "NO DISCHARGE REPORTING instructions in documents/aztec/final_permit.txt (permit NM0028762, different facility, references checkbox not NODI code)",
    "OPTIONAL_MONITORING_FLAG=Y on WET retest limits without a code-to-meaning mapping"
  ],
  "unknowable_from_structured_data_alone": [
    "The semantic label or regulatory state encoded by NODI code 9 (no codebook table exists in structured sources)",
    "Whether NODI 9 on chlorine rows documents conditional non-use of chlorine versus missing required monitoring evidence",
    "Whether NODI 9 on WET retest rows documents retest-not-triggered versus other no-data states",
    "Whether NODI 9 is interchangeable with NODI C used exclusively on permit NM0000116"
  ]
}
```

### T3 when_discharging

```json
{
  "proposition": "The DMR_COMMENT_TEXT value 'WHEN DISCHARGING' (mirroring permit footnote *1) conditions monitoring frequency and sample-collection obligations to periods when the outfall is actually discharging; it does not suspend numeric effluent limits when no discharge occurs, and discharge occurrence in a given monitoring period is a separate factual determination.",
  "would_establish": [
    "Permit-package text for NM0028762 defining footnote *1 as 'When discharging.' and attaching it to monitoring-frequency markers (*1) in the effluent limit table",
    "Permit narrative stating specific parameters 'shall be monitored [daily/weekly/quarterly] when discharging'",
    "Permit NO DISCHARGE REPORTING instruction for months with no discharge from any outfall",
    "Structured permit_limits rows showing DMR_COMMENT_TEXT='WHEN DISCHARGING.' on the affected limit sets with OPTIONAL_MONITORING_FLAG=N and ENF limit type"
  ],
  "would_refute": [
    "Permit text stating numeric effluent limits do not apply or are waived whenever discharge does not occur",
    "Permit text equating 'WHEN DISCHARGING' with OPTIONAL_MONITORING_FLAG=Y or making the limits themselves discharge-conditional rather than monitoring-conditional",
    "Evidence that DMR_COMMENT_TEXT 'WHEN DISCHARGING' appears on permits other than NM0028762 with materially different footnote semantics"
  ],
  "likely_authoritative_source_types": [
    "final_permit.txt effluent limit table and footnotes for NM0028762",
    "statement_of_basis.txt monitoring-frequency rationale for NM0028762",
    "permit_limits.csv DMR_COMMENT_TEXT and monitoring metadata for affected rows",
    "dmr_measurements.csv reported values and NODI/optional-monitoring fields for the same limit sets"
  ],
  "insufficient_alone": [
    "DMR_COMMENT_TEXT string in permit_limits.csv without permit footnote or narrative text",
    "Presence of reported DMR values in dmr_measurements.csv (does not establish discharge occurrence or comment semantics)",
    "OPTIONAL_MONITORING_FLAG=N (indicates limits are not optional-monitoring rows, not the meaning of the comment)",
    "document_inventory.json filename listing without opening permit text"
  ],
  "unknowable_from_structured_data_alone": [
    "Whether discharge actually occurred in any specific monitoring period",
    "Automatic mapping from DMR_COMMENT_TEXT to permit footnote *1 without permit document text",
    "Compliance disposition for a no-discharge month absent DMR no-discharge indicator fields in structured extracts"
  ]
}
```

### T3 geometric_mean

```json
{
  "proposition": "A permit limit DMR comment containing 'GEOMETRIC MEAN' establishes that aggregated reporting\u2014not ordinary single-period numeric comparison\u2014governs how individual monitoring-period values relate to applicable effluent limits.",
  "would_establish": [
    "Permit narrative or limit-table footnotes defining what must be reported (geometric mean of weekly values) and what statistic is compared to numeric limits (e.g., 30-day average)",
    "Explicit contrast in the same permit between parameters that cannot be averaged and parameters requiring geometric-mean aggregation",
    "Structured rows where the comment text identifies the pollutant and reporting statistic, linked to permit footnotes for that pollutant",
    "DMR or permit language stating which reported aggregate constitutes evidence of violation"
  ],
  "would_refute": [
    "Permit text requiring direct comparison of each individual weekly or monthly sample to the effluent limit without aggregation",
    "Evidence that the geometric-mean comment applies uniformly to every parameter sharing the limit-set schedule comment, not only the named pollutant",
    "Numeric effluent limits stated as instantaneous or single-sample maxima for the same rows governed by the geometric-mean comment"
  ],
  "likely_authoritative_source_types": [
    "final_permit.txt footnotes and effluent-limit tables for permit NM0020583",
    "statement_of_basis.txt discussion of TDS monitoring and limit derivation",
    "permit_limits.csv DMR_COMMENT_TEXT and parameter linkage on limit set schedule 3600891019",
    "dmr_measurements.csv exemplar TDS reporting rows (to observe reporting grain, not as compliance legend)"
  ],
  "insufficient_alone": [
    "Presence of 'GEOMETRIC MEAN' in DMR_COMMENT_TEXT on all 40 schedule rows without reading which pollutant the text names",
    "STATISTICAL_BASE_TYPE_CODE = AVG on structured limit rows",
    "LIMIT_FREQ_OF_ANALYSIS_CODE = 01/07 (weekly) without permit narrative",
    "A single monthly DMR numeric value for TDS without underlying weekly sub-period data"
  ],
  "unknowable_from_structured_data_alone": [
    "Whether each monthly DMR reported value is already the geometric mean of that month's weekly measurements",
    "The exact aggregation window for limit comparison when permit states both weekly monitoring and 30-day average limits",
    "Whether non-TDS parameters on the same limit set are semantically subject to geometric-mean reporting when the comment text names only TDS"
  ]
}
```

### T3 pass_fail

```json
{
  "proposition": "PASS=0 / FAIL=1 in DMR_COMMENT_TEXT instructs binary whole-effluent-toxicity (WET) pass/fail reporting (0=pass, 1=fail) based on whether NOEC for survival is below the critical dilution; it is not an ordinary numeric pollutant-concentration comparison against an effluent limit.",
  "would_establish": [
    "DMR_COMMENT_TEXT on permit_limits rows for NM0020583 WET limit set explicitly stating PASS=0 and FAIL=1 with reporting instructions",
    "Permit Part II WET reporting table mapping TEM3D/TEM6C and retest STORET codes to enter 1 if NOEC < critical dilution else 0",
    "Structured unit encoding pass=0;fail=1 on pass/fail parameters (TEM*, retest codes) with empty numeric limit values",
    "Reported DMR measurements using pass=0;fail=1 units with values 0 or 1, not concentration magnitudes",
    "Permit text separately requiring numeric NOEC reporting on TOM* parameters in percent"
  ],
  "would_refute": [
    "Permit or structured evidence showing PASS/FAIL values are compared numerically to a concentration limit (mg/L, %, etc.)",
    "Evidence that 0 and 1 represent measured pollutant concentrations rather than categorical test outcomes",
    "Codebook or limit row assigning a numeric LIMIT_VALUE_NMBR to pass/fail parameters for concentration comparison"
  ],
  "likely_authoritative_source_types": [
    "sources/permit_limits.csv DMR_COMMENT_TEXT and unit fields for WET parameters",
    "documents/farmington/final_permit.txt Part II Whole Effluent Toxicity reporting requirements",
    "sources/dmr_measurements.csv reported values and units for TEM3D/TEM6C"
  ],
  "insufficient_alone": [
    "Presence of PASS=0/FAIL=1 comment text without permit narrative reporting table",
    "LIMIT_VALUE_TYPE_CODE C3 or STATISTICAL_BASE MAX without WET context",
    "Co-occurrence of the shared comment on TOM/TQM rows that use percent units",
    "DMR phrase 'CONCENTRATION MAX' without cross-reading permit reporting instructions"
  ],
  "unknowable_from_structured_data_alone": [
    "That 0 means NOEC at or above critical dilution (pass) and 1 means NOEC below critical dilution (fail)",
    "That pass/fail applies only to TEM and retest STORET codes, not to separate numeric NOEC (TOM) or COV (TQM) fields in the same limit set",
    "The biological/statistical criteria defining pass vs fail (critical dilution comparison)"
  ]
}
```

### T3 empty_numeric_limit

```json
{
  "proposition": "When LIMIT_VALUE_NMBR is empty, each permit limit row can be classified as (a) an enforceable numeric discharge limit subject to concentration comparison, (b) report-only monitoring with no numeric compliance limit, or (c) a non-numeric reporting obligation (pass/fail, conditional applicability, or aggregated reporting) that blocks ordinary numeric comparison.",
  "would_establish": [
    "Permit Part I limitation tables that mark a pollutant/limit column as 'Report' or 'N/A' rather than a numeric value, for rows whose structured LIMIT_VALUE_NMBR is empty",
    "Structured DMR_COMMENT_TEXT on empty-limit rows that explicitly defines pass/fail encoding (PASS=0, FAIL=1) or geometric-mean reporting or when-discharging conditionality",
    "Corroborating pairing where the same permit and parameter has a populated LIMIT_VALUE_NMBR on one limit-type row and an empty LIMIT_VALUE_NMBR on another, showing the empty row is not the sole numeric limit carrier",
    "A workspace codebook or field legend defining LIMIT_VALUE_TYPE_CODE (C1/C2/C3/Q1/Q2) semantics for empty versus populated LIMIT_VALUE_NMBR"
  ],
  "would_refute": [
    "A single uniform rule that all empty LIMIT_VALUE_NMBR rows denote numeric limits",
    "A single uniform rule that all empty LIMIT_VALUE_NMBR rows denote report-only monitoring",
    "Treating LIMIT_TYPE_CODE='ENF' alone as proof that an empty LIMIT_VALUE_NMBR row is a numeric enforceable limit",
    "Inferring numeric limits from LIMIT_VALUE_TYPE_CODE or STATISTICAL_BASE_TYPE_CODE without permit text or DMR comment support"
  ],
  "likely_authoritative_source_types": [
    "sources/permit_limits.csv structured fields (LIMIT_VALUE_NMBR, LIMIT_VALUE_TYPE_CODE, LIMIT_TYPE_CODE, DMR_COMMENT_TEXT, PARAMETER_CODE, STATISTICAL_BASE_TYPE_CODE)",
    "documents/*/final_permit.txt Part I limitation and monitoring requirement tables",
    "documents/*/fact_sheet.txt or statement_of_basis.txt narrative explaining report-only versus numeric limits"
  ],
  "insufficient_alone": [
    "LIMIT_VALUE_NMBR empty without permit-table or DMR-comment corroboration",
    "LIMIT_TYPE_CODE='ENF' on all 57 empty rows",
    "LIMIT_VALUE_TYPE_CODE distribution (C3/Q2/C2/Q1/C1) without a workspace codebook",
    "Co-occurrence of empty LIMIT_VALUE_NMBR with OPTIONAL_MONITORING_FLAG values",
    "dmr_measurements.csv row counts alone (no FY2025 measurement rows have empty LIMIT_VALUE_NMBR in this workspace)"
  ],
  "unknowable_from_structured_data_alone": [
    "Whether a blank-comment empty-limit row is report-only monitoring versus a data omission, without matching permit Part I text",
    "The regulatory meaning of LIMIT_VALUE_TYPE_CODE values (C1/C2/C3/Q1/Q2)",
    "Whether WHEN DISCHARGING empty rows are inapplicable for a given monitoring period without discharge-occurrence evidence",
    "The correct numeric comparison operator for pass/fail-encoded WET retest rows beyond the DMR comment's 0/1 reporting instruction"
  ]
}
```

### T3 document_authority

```json
{
  "proposition": "Inventoried permit-package documents can be classified by their own text into enforceable authorization content versus draft/supporting material, and cross-document conflicts are resolvable only where the documents themselves state issuance status, incorporation by reference, or proposed-versus-final relationships.",
  "would_establish": [
    "Issued authorization pages that state 'AUTHORIZATION TO DISCHARGE' and enumerate Parts I\u2013III/IV as binding conditions establish enforceable permit obligations.",
    "Documents headed 'FOR THE DRAFT NPDES PERMIT' or 'STATEMENT OF BASIS' that describe 'proposed' or 'draft' permit conditions establish permitting rationale and proposed conditions used to develop the permit, not standalone enforceable authorization.",
    "Text stating that information 'was used to develop the proposed permit' establishes an administrative-record/supporting role.",
    "Text incorporating 'Appendix A of Part II' or 'Part IV hereof' into the issued authorization establishes that those appended parts are part of the enforceable permit package.",
    "Supersession language ('This permit supersedes and replaces...') establishes replacement of a prior issued permit."
  ],
  "would_refute": [
    "A workspace-wide rule that document_kind labels alone (final_permit, fact_sheet, etc.) establish a governing hierarchy without reading document text.",
    "Treating fact sheets or statements of basis as enforceable authorization when their headers and body text identify them as draft/proposed documents.",
    "A single universal conflict clause applying equally to all 12 inventoried files when no such general clause appears in the workspace texts.",
    "Inferring governing authority for minor_modification.pdf from filename when the extracted text contains only Part I tables and no issuance or precedence language."
  ],
  "likely_authoritative_source_types": [
    "sources/document_inventory.json for what files exist per permit",
    "Issued authorization text in final_permit extracts (cover page and Part I\u2013IV scope statements)",
    "Draft/supporting explanatory text in fact_sheet and statement_of_basis extracts",
    "Incorporation-by-reference passages linking appendices to issued permit parts",
    "Calculation worksheet extracts (reasonable_potential) only where referenced as supporting analysis in explanatory documents"
  ],
  "insufficient_alone": [
    "document_inventory.json fields document_kind, filename, bytes, and sha256",
    "Structural correlation between inventory kinds and permit CSV rows",
    "Presence of numeric limits in a file without accompanying issuance or incorporation language",
    "Training-data or EPA generic definitions of NPDES document types"
  ],
  "unknowable_from_structured_data_alone": [
    "Which inventoried text is enforceable authorization versus supporting material",
    "Which document governs when draft/proposed text disagrees with issued authorization text",
    "Whether minor_modification text independently modifies or merely duplicates issued Part I",
    "Internal precedence among all permit parts beyond explicit cross-references in opened texts"
  ]
}
```

### T3 monitoring_frequency

```json
{
  "proposition": "Each distinct LIMIT_FREQ_OF_ANALYSIS_CODE value (e.g. 05/WK, 01/07, 01/01, 01/90, 02/30, 02/07, 09/99, 99/99) establishes a specific, reusable monitoring-frequency obligation that can be interpreted for Purpose B without per-row permit narrative lookup.",
  "would_establish": [
    "A workspace codebook, legend, or definitional passage that maps LIMIT_FREQ_OF_ANALYSIS_CODE tokens to monitoring frequencies in plain language or a formal schedule grammar.",
    "Permit-package text that explicitly names the opaque codes (05/WK, 01/07, etc.) and states the frequency each code denotes.",
    "Consistent, document-grounded pairing of each code value with a single human-readable frequency across all permits and parameters in the workspace, together with text explaining the NN/XX code format."
  ],
  "would_refute": [
    "Authoritative workspace text stating that LIMIT_FREQ_OF_ANALYSIS_CODE values are placeholders, internal-only, or not intended to denote monitoring frequency.",
    "Demonstration that the same code value maps to materially different document-stated frequencies across permits without any reconciling definition.",
    "Evidence that retest or continuous-monitoring rows use frequency codes that denote event-driven or non-calendar obligations, undermining a single calendar-frequency reading for all codes."
  ],
  "likely_authoritative_source_types": [
    "sources/permit_limits.csv LIMIT_FREQ_OF_ANALYSIS_CODE field values and co-occurring permit/parameter identifiers",
    "documents/*/final_permit.txt Part I monitoring-requirement tables and footnotes",
    "documents/*/statement_of_basis.txt sections on monitoring frequency for limited parameters",
    "documents/farmington/final_permit.txt Part II WET reporting tables referencing retest parameter codes"
  ],
  "insufficient_alone": [
    "Observing that a code string resembles a count/period pattern (e.g. 05/WK looks like five per week) without workspace definitional text.",
    "CSV co-occurrence of a code with a permit number and parameter code without opening the matching permit document frequency column.",
    "DMR_FREQ_OF_ANALYSIS_CODE values in dmr_measurements.csv, which reflect reported events rather than limit-schedule code definitions.",
    "Training-data knowledge of ICIS-NPDES or EPA code dictionaries not present in the workspace."
  ],
  "unknowable_from_structured_data_alone": [
    "The semantic mapping from opaque LIMIT_FREQ_OF_ANALYSIS_CODE tokens to calendar monitoring frequencies; structured CSVs contain the codes but no legend table.",
    "Whether 09/99 denotes a calendar schedule versus event-driven retest reporting obligations.",
    "Whether 99/99 denotes continuous metering versus another special schedule class.",
    "The precise meaning of the denominator in codes like 01/90 (90-day period vs calendar quarter) without definitional text."
  ]
}
```

## OBSERVED

Plans are host-authored before/during retrieval. Compare whether NODI plans reject CSV correlation.

## HYPOTHESIS

An evidence plan can constrain retrieval to obligation-relevant sources.
