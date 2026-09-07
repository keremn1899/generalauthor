# ANSWERS — Federal FY2025 NPDES World Analysis

Source: `accepted/world.sqlite` (state_a; 3 permits, 4 discharge features, 824 FY2025 measurements in `fy2025_measurement` / `measurement_limit_pair`, 105 rows in `monitoring_requirement_fy2025`, 535 rows in `_hole`).

Per READ RULES: unresolved is not false; a missing tuple is not an established negative. NODI code meanings are taken only from the World's `nodi_code_semantics` requirement (known set: `[""]` only) — codes `C` and `9` are present but uninterpreted; no meanings are invented here.

---

## Q1 — Determinacy

FY2025 monitoring/compliance cases that remain indeterminate, grouped by the unresolved prerequisite recorded in `_hole`:

### Purpose A — applicable discharge limits (measurement/limit pairs)

| Indeterminate cases | Relation | Count | Unresolved prerequisite | Failure kind |
|---|---|---:|---|---|
| No ordinary numeric reported result | `no_numeric_result_case` | 186 | `nodi_code_semantics` — `nodi_code` values `C` (150) and `9` (36) are not in the World's known set `[""]` | UNINTERPRETED |
| Reported value present, no numeric limit for comparison | `measurement_limit_pair` (not in `numeric_comparison_candidate` or `no_numeric_result_case`) | 296 | No numeric `limit_value_for_comparison` — all have `has_reported_value=1`, `has_limit_value_nmbr=0`, `limit_type_code=ENF`, and non-numeric `limit_value_type_code` values (`C3` 108, `Q2` 70, `Q1` 58, `C2` 48, `C1` 12) | (no hole row; prerequisite not materialized) |
| Pass/fail reporting semantics | `measurement_limit_pair` | 48 measurements across 12 limit schedules | `pass_fail_reporting_semantics` — permit limit comment describes pass/fail reporting (`PASS = 0  FAIL = 1`) requiring interpretation beyond ordinary numeric concentration comparison | EXPLICIT_UNRESOLVED |

**Established for Purpose A:** 342 of 824 measurements are in `numeric_comparison_candidate` with both `reported_value_for_comparison` and `limit_value_for_comparison` materialized, and `limit_comparison_operator`, `reported_value_qualifier`, and `statistical_base_for_limit_comparison` interpreted (operators `<=`/`>=`; qualifiers `<`/`=`/`>`; bases `AVG`/`MAX`/`MIN`). These 342 have no `pass_fail_reporting_semantics` hole (0 overlap).

### Purpose B — monitoring obligations

| Indeterminate cases | Relation | Count | Unresolved prerequisite | Failure kind |
|---|---|---:|---|---|
| All FY2025 monitoring requirements | `monitoring_requirement_fy2025` | 105 | `limit_sample_type_code` — non-empty codes (e.g. `12`, `24`) not in known `[""]` | UNINTERPRETED |
| All FY2025 monitoring requirements | `monitoring_requirement_fy2025` | 105 | `monitoring_frequency_code` — non-empty codes (e.g. `01/07`, `05/WK`, `01/90`) not in known `[""]` | UNINTERPRETED |
| Aggregated (geometric mean) reporting | `monitoring_requirement_fy2025` | 40 | `aggregated_reporting_requirement` — comment references geometric mean of weekly values; applicability to individual monitoring periods not established from structured sources | EXPLICIT_UNRESOLVED |
| Discharge-conditioned monitoring | `monitoring_requirement_fy2025` | 17 | `conditional_discharge_dependent_monitoring` — comment `WHEN DISCHARGING.`; structured sources do not establish whether discharge occurred for the evaluated period | EXPLICIT_UNRESOLVED |

### Purpose C — missing-evidence semantics

| Indeterminate cases | Relation | Count | Unresolved prerequisite | Failure kind |
|---|---|---:|---|---|
| No numeric result rows | `no_numeric_result_case` | 186 | `nodi_code_semantics` (same as Purpose A above) | UNINTERPRETED |

### Cross-cutting (Purposes B and C)

| Prerequisite | Relation | Count | Failure kind |
|---|---|---:|---|
| `permit_limit_comment_text` | `permit_limit` | 69 of 105 rows (non-empty `dmr_comment_text` not in known `[""]`) | UNINTERPRETED |
| `permit_document_text_not_available` | `permit_document` | 1 (12 documents inventoried by filename/hash only; narrative permit conditions unavailable) | EXPLICIT_UNRESOLVED |

**Not established as indeterminate:** absence of a positive tuple for any case not listed above. The 36 `monitoring_requirement_fy2025` rows with empty `dmr_comment_text` have no `permit_limit_comment_text` hole.

---

## Q2 — Numeric result separation

### Mechanically computable numeric comparison (exceedance can be computed)

**342 measurements** in `numeric_comparison_candidate` (41.5% of 824 FY2025 measurements).

Each row has:
- Numeric `dmr_value_standard_units` and `limit_value_standard_units`
- Interpreted `limit_value_qualifier_code` (`<=` or `>=`)
- Interpreted `dmr_value_qualifier_code` (`<`, `=`, or `>`)
- Interpreted `statistical_base_type_code` (`AVG`, `MAX`, or `MIN`)

Distribution of comparison shapes: `<=`/`=`/`AVG` (170), `<=`/`=`/`MAX` (99), `>=`/`=`/`MIN` (50), plus 23 rows with non-equality reported qualifiers (`<` or `>`).

These rows are materialized under requirements `numeric_comparison_candidates_materializable`, `reported_value_for_comparison`, and `limit_value_for_comparison`.

### Exceedance determination cannot yet be made

**482 measurements** (58.5%) fall outside `numeric_comparison_candidate`:

| Bucket | Relation | Count | Why comparison is blocked |
|---|---|---:|---|
| No numeric reported result | `no_numeric_result_case` | 186 | `has_reported_value=0`; NODI codes present (`C` 150, `9` 36) but semantically uninterpreted |
| Reported value, no numeric limit | `measurement_limit_pair` only | 296 | `has_reported_value=1`, `has_limit_value_nmbr=0`; limit value types are non-numeric (`C1`/`C2`/`C3`/`Q1`/`Q2`) |

Additionally, **48 measurements** tied to `pass_fail_reporting_semantics` holes cannot use ordinary numeric concentration comparison regardless of bucket (24 are in `no_numeric_result_case`, 24 are in the 296 "reported but no numeric limit" group; 0 overlap with `numeric_comparison_candidate`).

**Separation is disjoint:** `numeric_comparison_candidate` and `no_numeric_result_case` have 0 overlapping measurements. The 296 third bucket is disjoint from both.

---

## Q3 — Semantic sharpening: discharge-occurrence uncertainty

The World **does** represent discharge-conditioned monitoring, and it distinguishes condition meaning from discharge-occurrence uncertainty.

### Cases where uncertainty is about whether discharge occurred

**17 rows** in `monitoring_requirement_fy2025` carry an `EXPLICIT_UNRESOLVED` hole for `conditional_discharge_dependent_monitoring` (Purposes B and C).

- All 17 have `dmr_comment_text = 'WHEN DISCHARGING.'`
- All belong to permit `NM0028762`
- The World's spec note: *"Permit limit comment references discharge occurrence; structured sources do not establish whether discharge occurred for the evaluated period."*
- The monitoring **condition meaning** (`WHEN DISCHARGING.`) is present in structured evidence; what remains unresolved is **discharge occurrence** for the evaluated period.

These 17 requirements cover 6 parameters (EPA codes `00400`, `00530`, `50050`, `50060`, `70295`, `78248`).

### Related measurement activity (obligation still unresolved)

**140 measurements** in `measurement_limit_pair` are paired with limits whose `dmr_comment_text` is `WHEN DISCHARGING.` (same 17 limit schedules). Of these:
- 60 are in `numeric_comparison_candidate` (numeric values reported)
- 80 have reported values but no numeric limit (`has_limit_value_nmbr=0`)
- 0 are in `no_numeric_result_case`

The World's discharge-occurrence uncertainty is registered at the **requirement** level (`monitoring_requirement_fy2025` + `_hole`), not as measurement-level holes. Numeric comparison may be mechanically possible for 60 of the 140 measurements, but whether monitoring was required for those periods remains indeterminate pending discharge-occurrence evidence.

### Cases where uncertainty is about monitoring-condition meaning (not discharge occurrence)

For contrast, these are **not** discharge-occurrence cases:

| Prerequisite | Count | Nature of uncertainty |
|---|---:|---|
| `aggregated_reporting_requirement` | 40 requirements | Whether geometric-mean aggregated reporting applies to individual monitoring periods (condition interpretation), not whether discharge occurred |
| `pass_fail_reporting_semantics` | 48 measurements | How to interpret pass/fail reporting semantics for compliance |
| `nodi_code_semantics` | 186 cases | What NODI codes `C` and `9` signify (code semantics uninterpreted; no discharge-occurrence framing in `_hole`) |
| `permit_document_text_not_available` | 1 global | Narrative permit text unavailable to resolve conditions |

No `no_numeric_result_case` row is linked to a discharge-conditioned limit (0 overlap).
