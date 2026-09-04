# Purpose dependency and backward slice

Analysis-only graph. Sealed originals were not deleted from.

## Evaluator-side dependency

```text
Purpose A (applicable numeric limits, FY2025)
  → unique applicable limit per measurement
  → CandidateCorrespondence / NumericComparison / ReportOnlyOrNonNumeric
  → Measurement, Limit, interval/FY2025 grounding
  → structured DMR + permit_limits
  ↳ holes: uniqueness, non-numeric limit, comment-conditioned applicability

Purpose B (monitoring obligations)
  → MonitoringObligation + comment/optional/frequency interpretation
  → DocumentInventory (authority / narrative conditions)
  → permit_limits + document_inventory.json
  ↳ holes: uninterpreted comment, WHEN DISCHARGING, document text unavailable

Purpose C (missing evidence)
  → MissingEvidence + interpret_nodi
  → Measurement result / NODI field grounding
  ↳ holes: NODI semantics, missing reported value
```

## MEASURED backward slice

Slice starts from Purpose A/B/C required outputs and all E1-scored semantic holes.

- union of normalized requirement schemas across trials: 24
- PURPOSE_REACHABLE requirements: 12 — `document_text_unavailable`, `interpret_comment`, `interpret_limit_type`, `interpret_nodi`, `interpret_optional_monitoring`, `interpret_qualifier`, `materializable_candidates`, `materializable_fy2025_measurements`, `numeric_limit`, `numeric_measurement`, `report_only_gap`, `unique_applicable_limit`
- NOT_PURPOSE_REACHABLE candidates: 8 — `aggregated_reporting`, `interpret_frequency`, `interpret_sample_type`, `interpret_seasonal_month`, `interpret_statistical_base`, `interpret_unit`, `interpret_value_type`, `pass_fail_semantics`
- AMBIGUOUS_DEPENDENCY requirements: 4 — `materializable_documents`, `materializable_monitoring`, `materializable_no_result`, `other_requirement`

- PURPOSE_REACHABLE relations: 7 — `CandidateCorrespondence`, `DocumentInventory`, `Fy2025Scope`, `LimitBase`, `MeasurementBase`, `MissingEvidence`, `NumericComparison`
- remaining relation labels: `CodePayload`, `EffectiveInterval`, `MonitoringObligation`, `OtherRelation`, `SeasonalMonth`

Per-trial semantic-element counts (factorized referents+relations+requirement schemas):

| trial | elements | req schemas | rel schemas | ref schemas |
| --- | --- | --- | --- | --- |
| T1 | 27 | 14 | 9 | 4 |
| T2 | 34 | 11 | 12 | 11 |
| T3 | 34 | 16 | 6 | 12 |
| T4 | 30 | 13 | 9 | 8 |
| T5 | 33 | 16 | 7 | 10 |

## OBSERVED

- Primary E1 seams do not include wet-seasonal GOLD (`S-AZTEC-WET-SEASONAL` was 0/5 in the sealed Python probe). Seasonal-month interpretation is therefore a candidate non-reachable extra relative to the tested purpose slice.
- Qualifiers, optional-monitoring flags, and limit-type codes sit on the comparison/applicability path: AMBIGUOUS until ablation.
- CommentPayload relations are reachable when they carry WHEN DISCHARGING / report-only comments.

## HYPOTHESIS

A purpose-reachable core of roughly a dozen schemas is sufficient; extras are reviewable dead semantic mass rather than hidden E1 coverage.
