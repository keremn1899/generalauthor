# Trial results

Labels: **MEASURED** unless marked OBSERVED or HYPOTHESIS.

Model: Composer 2.5. Structurally valid trials: 4/5.

| Trial | valid | iters | groups | instances | E1 | E4 distinctions | TDS | authority |
|---|---|---|---|---|---|---|---|---|
| T1 | yes | 3 | 8 | 2036 | 0.86 | 9/9 | TRIGGER | yes |
| T2 | yes | 2 | 8 | 1642 | 0.71 | 8/9 | TRIGGER | no |
| T3 | yes | 3 | 6 | 138 | 0.29 | 7/9 | MISS | yes |
| T4 | yes | 3 | 5 | 960 | 0.43 | 7/9 | TRIGGER | yes |
| T5 | no | 3 | 0 | 0 | 0.00 | 0/9 | MISS | no |

## Per-trial programs

### T1

- referents 3, maps 3, relations 7, requirements 4
- relations: measurement, limit_row, permit_document, candidate_limit, limit_with_document, limit_measurement, nodi_report
- requirements: applicable_limit, monitoring_obligation, monitoring_activity, nodi_interpretation
- row counts: `{"measurement": 824, "limit_row": 105, "permit_document": 12, "candidate_limit": 1292, "limit_with_document": 433, "limit_measurement": 1292, "nodi_report": 894}`

### T2

- referents 2, maps 2, relations 3, requirements 3
- relations: measurement, limit_row, candidate_limit
- requirements: applicable_limit, monitoring_obligation, missing_evidence
- row counts: `{"measurement": 824, "limit_row": 105, "candidate_limit": 1004}`

### T3

- referents 3, maps 3, relations 6, requirements 4
- relations: measurement, limit_row, permit_document, candidate_limit, missing_numeric_result, limit_permit_document
- requirements: applicable_limit, monitoring_obligation, conditional_monitoring_correspondence, missing_evidence_interpretation
- row counts: `{"measurement": 824, "limit_row": 105, "permit_document": 12, "candidate_limit": 0, "missing_numeric_result": 0, "limit_permit_document": 0}`

### T4

- referents 3, maps 3, relations 5, requirements 4
- relations: measurement, limit_row, document_row, candidate_limit, nodi_measurement
- requirements: applicable_limit, monitoring_obligation, permit_documentation, missing_evidence
- row counts: `{"measurement": 824, "limit_row": 105, "document_row": 12, "candidate_limit": 0, "nodi_measurement": 824}`

### T5

- referents 3, maps 3, relations 7, requirements 5
- relations: measurement, limit_row, document_row, candidate_limit, enforceable_candidate, no_numeric_result, permit_document
- requirements: applicable_limit, enforceable_comparison, monitoring_obligation, permit_evidence, missing_evidence_nodi
- row counts: `{}`

