# Consensus spine

Naming differences are not treated as semantic instability.

## MEASURED stability

### Concept / referent stability

- **5/5:** `Document`, `LimitValue`, `Measurement`
- **4/5:** `Limit`, `Outfall`, `Parameter`, `Permit`
- **3/5:** `LimitSchedule`
- **2/5:** `LimitRow`, `LimitSet`, `MonitoringEvent`, `MonitoringPeriod`, `MonitoringRequirement`
- **1/5:** `Facility`

### Relation-role stability

- **5/5:** `CandidateCorrespondence`, `DocumentInventory`, `Fy2025Scope`, `LimitBase`, `MeasurementBase`, `NumericComparison`
- **4/5:** `MissingEvidence`
- **2/5:** `EffectiveInterval`, `MonitoringObligation`, `OtherRelation`, `SeasonalMonth`
- **1/5:** `CodePayload`

### Requirement stability

- **5/5:** `interpret_comment`, `interpret_frequency`, `interpret_nodi`, `interpret_optional_monitoring`, `interpret_qualifier`, `unique_applicable_limit`
- **4/5:** `numeric_limit`, `numeric_measurement`
- **3/5:** `document_text_unavailable`, `interpret_limit_type`, `interpret_seasonal_month`, `materializable_candidates`, `materializable_fy2025_measurements`, `materializable_no_result`, `other_requirement`
- **2/5:** `materializable_monitoring`, `pass_fail_semantics`
- **1/5:** `aggregated_reporting`, `interpret_sample_type`, `interpret_statistical_base`, `interpret_unit`, `interpret_value_type`, `materializable_documents`, `report_only_gap`

## Stable core

Semantics independently constructed in **5/5** (MEASURED):

- Referents: `Document`, `LimitValue`, `Measurement`
- Relations: `CandidateCorrespondence`, `DocumentInventory`, `Fy2025Scope`, `LimitBase`, `MeasurementBase`, `NumericComparison`
- Requirements: `interpret_comment`, `interpret_frequency`, `interpret_nodi`, `interpret_optional_monitoring`, `interpret_qualifier`, `unique_applicable_limit`

### OBSERVED core reading

Every trial materializes measurements, limits, a FY2025/purpose-scoped correspondence, a document inventory, numeric comparison candidates, missing-evidence/NODI handling, and comment/opaque-text interpretation. Every trial authors uniqueness of applicable limit (surface names differ) and NODI interpretation.

## Frequent extensions

4/5 or 3/5:

- Relations: `MissingEvidence`
- Requirements: `numeric_limit`, `numeric_measurement`, `document_text_unavailable`, `interpret_limit_type`, `interpret_seasonal_month`, `materializable_candidates`, `materializable_fy2025_measurements`, `materializable_no_result`, `other_requirement`

## Trial-local semantics

1/5 or 2/5:

- Relations: `EffectiveInterval`, `MonitoringObligation`, `OtherRelation`, `SeasonalMonth`, `CodePayload`
- Requirements: `materializable_monitoring`, `pass_fail_semantics`, `aggregated_reporting`, `interpret_sample_type`, `interpret_statistical_base`, `interpret_unit`, `interpret_value_type`, `materializable_documents`, `report_only_gap`

## HYPOTHESIS

Seasonal-month flags, sample-type, unit, value-type, pass/fail extras, and geometric-mean comments are trial-local elaborations. `interpret_frequency` is 5/5 but single-element ablation-redundant for primary E1 — stable does not mean purpose-required.
