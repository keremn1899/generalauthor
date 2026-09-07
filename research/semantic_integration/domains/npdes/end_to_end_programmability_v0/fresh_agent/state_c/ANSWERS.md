# ANSWERS — Federal FY2025 NPDES World (state_c)

Source: `accepted/world.sqlite` (read-only). Three permits: NM0020583, NM0028762, NM0000116. 824 FY2025 measurements (`fy2025_measurement`), 105 permit-limit schedules (`permit_limit`), 510 recorded holes (`_hole`).

---

## Q1 — Determinacy

### Established (determinate for at least one purpose)

| Relation | Rows | What is established |
|---|---:|---|
| `fy2025_measurement` | 824 | FY2025 measurement scope materialized (`fy2025_measurements_materializable`) |
| `measurement_limit_pair` | 824 | One applicable limit per measurement (`unique_applicable_limit_per_measurement`) |
| `numeric_comparison_candidate` | 342 | Both `reported_value_for_comparison` and `limit_value_for_comparison` are NUMERIC; numeric exceedance is mechanically computable for Purpose A |
| `monitoring_requirement_fy2025` | 105 | FY2025 monitoring obligations materialized (`monitoring_requirements_materializable`) |
| `no_numeric_result_case` | 186 | Missing-numeric-result cases materialized (`no_numeric_result_cases_materializable`) |
| `pass_fail_outcome_reporting` | 8 | Pass/fail reporting rows present (wet outcome code interpreted) |

**342 of 824** measurement/limit pairs are determinate for Purpose A numeric exceedance comparison.

### Indeterminate cases (510 holes in `_hole`)

Holes group by unresolved prerequisite and affected purpose(s):

| Unresolved prerequisite | Failure kind | Holes | Relation(s) | Purpose(s) | What blocks determination |
|---|---|---:|---|---|---|
| `nodi_code_semantics` | UNINTERPRETED | 186 | `no_numeric_result_case` | C (also blocks A numeric comparison) | NODI codes `9` (36 rows) and `C` (150 rows) are not in the known vocabulary `[""]`; missing-evidence state cannot be classified |
| `monitoring_frequency_code` | UNINTERPRETED | 105 | `monitoring_requirement_fy2025` | B | `limit_freq_of_analysis_code` values (e.g. `05/WK`, `01/01`, `01/07`) not in known `[""]` |
| `limit_sample_type_code` | UNINTERPRETED | 105 | `monitoring_requirement_fy2025` | B | `limit_sample_type_code` values (e.g. `12`, `GR`) not in known `[""]` |
| `permit_limit_comment_text` | UNINTERPRETED | 52 | `permit_limit` / `monitoring_requirement_fy2025` | B, C | Comment text (e.g. geometric-mean TDS reporting instructions) not in known `["", "WHEN DISCHARGING."]` |
| `aggregated_reporting_requirement` | EXPLICIT_UNRESOLVED | 40 | `monitoring_requirement_fy2025` | B, C | Geometric-mean aggregated reporting applicability to individual monitoring periods not established from structured sources |
| `discharge_occurrence_in_period` | EXPLICIT_UNRESOLVED | 17 | `monitoring_requirement_fy2025` | B, C | Discharge-conditioned monitoring is established, but whether discharge occurred in each period is not recorded |
| `pass_fail_reporting_semantics` | EXPLICIT_UNRESOLVED | 4 | `measurement_limit_pair` | A, B, C | Pass/fail limit rows reference reporting semantics whose structured unit vocabulary is not established |
| `permit_document_text_not_available` | EXPLICIT_UNRESOLVED | 1 | `permit_document` | B, C | Permit documents are inventoried by filename/hash only; narrative conditions are not available as structured evidence |

### Purpose-level summary

**Purpose A — applicable discharge limits**

- **Determinate:** 342 rows in `numeric_comparison_candidate` (no holes on that relation).
- **Indeterminate:** 482 measurements lack a computable numeric comparison:
  - 186 in `no_numeric_result_case` (no reported numeric value; `nodi_code_semantics` unresolved).
  - 296 with `has_reported_value=1`, `has_limit_value_nmbr=0`, `limit_type_code=ENF` — reported concentration exists but no numeric limit value is available for comparison (`limit_value_for_comparison` not NUMERIC).
  - 4 underlying limit rows carry `pass_fail_reporting_semantics` holes (affecting 8 `pass_fail_outcome_reporting` measurements).

**Purpose B — monitoring obligations**

- All 105 `monitoring_requirement_fy2025` rows remain indeterminate: every row is blocked by `monitoring_frequency_code` and `limit_sample_type_code` (210 B-only holes). Additional B/C holes apply to subsets (comment text, aggregated reporting, discharge occurrence, permit document availability).

**Purpose C — missing-evidence semantics**

- All 186 `no_numeric_result_case` rows remain indeterminate pending `nodi_code_semantics` (186 C-only holes). NODI code values present are `9` and `C`; their meanings are **not** established in this World and are not inferred here.

---

## Q2 — Numeric result separation

### Mechanically computable numeric comparison (exceedance determinable)

**342 rows** in `numeric_comparison_candidate`, pairing measurements from `measurement_limit_pair` where:

- `has_reported_value = 1` and `has_limit_value_nmbr = 1`
- `reported_value_for_comparison` (field `dmr_value_standard_units`) — NUMERIC
- `limit_value_for_comparison` (field `limit_value_standard_units`) — NUMERIC
- `limit_comparison_operator` interpreted (e.g. `<=`)
- Zero holes recorded against `numeric_comparison_candidate`

| Permit | Computable rows |
|---|---:|
| NM0020583 | 264 |
| NM0028762 | 60 |
| NM0000116 | 18 |

### Exceedance determination cannot yet be made (482 measurements)

| Category | Rows | Relation | Blocking factor |
|---|---:|---|---|
| No reported numeric result | 186 | `no_numeric_result_case` | `has_reported_value` absent; `nodi_code` present (`9` or `C`) but `nodi_code_semantics` UNINTERPRETED |
| Reported value, no numeric limit | 288 | `measurement_limit_pair` (not in `numeric_comparison_candidate` or `no_numeric_result_case`) | `has_reported_value=1`, `has_limit_value_nmbr=0`, `limit_type_code=ENF` — no numeric limit for comparison |
| Pass/fail reporting (subset of above) | 8 | `pass_fail_outcome_reporting` | Numeric exceedance comparison not applicable; 4 limit rows have `pass_fail_reporting_semantics` EXPLICIT_UNRESOLVED |

The 288 reported-value/no-limit cases break down by permit: NM0020583 (204), NM0028762 (80), NM0000116 (12). The 186 no-numeric-result cases: NM0000116 (150), NM0020583 (36).

**Separation check:** `numeric_comparison_candidate` and `no_numeric_result_case` are disjoint (0 overlapping measurements). Together with the 296 ENF no-limit-value cases (which include the 8 pass/fail rows), they account for all 824 `fy2025_measurement` rows.

---

## Q3 — Semantic sharpening: discharge occurrence vs. monitoring-condition meaning

### The World does represent discharge-conditioned monitoring

`monitoring_requirement_fy2025` carries a `monitoring_condition` field. The requirement `monitoring_condition_from_comment` is INTERPRETED with known values `["", "discharge_occurrence"]`.

- **17 rows** have `monitoring_condition = 'discharge_occurrence'`, all on permit **NM0028762**, with `dmr_comment_text = 'WHEN DISCHARGING.'`.
- Grounding on `discharge_occurrence_in_period` holes confirms the monitoring condition meaning **is** established: `{"dmr_comment_text": "WHEN DISCHARGING.", "monitoring_condition": "discharge_occurrence"}`.

The World separates *what the condition means* (established) from *whether discharge occurred* (unresolved).

### Cases where uncertainty is about discharge occurrence (not condition meaning)

**17 `monitoring_requirement_fy2025` rows** (6 parameters at outfall 001, permit NM0028762) carry `discharge_occurrence_in_period` holes (`EXPLICIT_UNRESOLVED`, purposes B and C). The recorded gap: *"Comment semantics establish discharge-conditioned monitoring, but structured sources do not record whether discharge occurred in each monitoring period."*

These 17 rows have **zero** `permit_limit_comment_text` or `aggregated_reporting_requirement` holes — their comment semantics are resolved; only discharge occurrence is unknown.

### Cases where uncertainty is about monitoring-condition meaning (not discharge)

**88 `monitoring_requirement_fy2025` rows** have `monitoring_condition = ''` (empty). Their uncertainty concerns interpretation of permit-limit comments and coded fields, not discharge occurrence:

| Unresolved prerequisite | Rows affected | Nature of uncertainty |
|---|---:|---|
| `permit_limit_comment_text` | 52 | Comment text (e.g. geometric-mean TDS reporting) not in established vocabulary |
| `aggregated_reporting_requirement` | 40 | Whether aggregated (geometric-mean) reporting applies to individual monitoring periods |
| `monitoring_frequency_code` | 105 (all rows) | Frequency codes not interpreted |
| `limit_sample_type_code` | 105 (all rows) | Sample-type codes not interpreted |

The 40 aggregated-reporting cases are a subset of the 52 comment-text cases (TDS geometric-mean limits on NM0020583). None overlap with the 17 discharge-occurrence cases.

Additionally, **186 `no_numeric_result_case` rows** (Purpose C) have uncertainty about missing-evidence semantics (`nodi_code_semantics`), not about discharge occurrence. **1 global hole** (`permit_document_text_not_available`) notes that narrative permit text is unavailable as structured evidence.

### Sharpening conclusion

The World explicitly models a discharge-vs-meaning distinction for monitoring obligations:

- **Discharge-sharpened:** 17 cases where `monitoring_condition` is established as `discharge_occurrence` and the remaining question is `discharge_occurrence_in_period`.
- **Meaning-sharpened:** 88+ cases (all non-discharge monitoring requirements plus comment/frequency/sample-type holes) where uncertainty remains about what the monitoring condition or reporting obligation means, not whether discharge happened.

---
