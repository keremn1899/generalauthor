# World programming — NPDES Constructor v3.1.1 (sources absent)

**Question:** Is ordinary SQL/Python over the automatically constructed World sufficient to express useful domain analyses?

This is **not** RAW-vs-WORLD. Programs below read only `06_world/world.sqlite` (and vocabulary for table names). No permit PDFs, no ECHO CSV.

**MEASURED / OBSERVED / HYPOTHESIS** labeled throughout.

World freeze hashes: `reports/world_freeze.json`. Analyses use the frozen P8 World, which equals the P6 World on every trial.

---

## Interface reality

There is no single stable consumer schema. Five trials invented five Worlds.

| Trial | Programmable shape | Analyses that run as SQL without renaming |
|---|---|---|
| T1 | Wide DMR + limit tables with native codes (`permit_nbr`, `nodi_code`, `dmr_value_nbr`, `limit_value_nbr`, `optional_monitoring_flag`) | 1, 2, 3 |
| T2 | Normalized IDs (`facility_id`, `parameter_id`) plus WORLD `numeric_exceedance_result` | 2 (NODI); 1 via stored exceedance table |
| T3 | Different extract names; generic evaluator join missed tables | requires reading that trial’s vocabulary |
| T4 | Strongest: 1:1 `measurement_limit_evaluation_pair`, `dmr_reported_value_kind`, `limit_value_attributes`, `limit_source_flags` | 1, 2, 3 |
| T5 | Registry + assertion tables; NODI present on measurement assertion | 2; 1 needs vocabulary-guided joins |

**OBSERVED.** A programmer who opens T4 can compute. A programmer who assumes T1’s column names fail on T3/T4. Vocabulary `semantic_identity` bindings exist but P0 field ids are prose, so they do not form a portable ABI (`ABI ok=False` on all trials).

---

## Analysis 1 — applicable-limit / exceedance

### T1 (wide tables)

```sql
SELECT m.permit_nbr, m.perm_feature_nbr, m.parameter_code, m.monitoring_period_end,
       m.dmr_value_nbr, l.limit_value_nbr
FROM reported_dmr_measurement m
JOIN permit_limit_schedule_row l
  ON m.permit_nbr = l.permit_nbr
 AND m.perm_feature_nbr = l.perm_feature_nbr
 AND m.parameter_code = l.parameter_code
 AND m.statistical_base_code = l.statistical_base_code
WHERE m.dmr_value_nbr IS NOT NULL AND l.limit_value_nbr IS NOT NULL
  AND CAST(m.dmr_value_nbr AS REAL) > -1e30
  AND CAST(l.limit_value_nbr AS REAL) > -1e30
  AND CAST(m.dmr_value_nbr AS REAL) > CAST(l.limit_value_nbr AS REAL)
  AND IFNULL(l.optional_monitoring_flag, 'N') NOT IN ('Y', 'y');
```

**MEASURED.** Naive permit+feature+parameter join: 586 rows. Adding statistical-base match: 300 rows. GOLD M mechanical exceedances: 28.

**OBSERVED.** Over-count has two World-visible causes:

1. No WORLD row for *the* applicable limit (T1 `applicable_limit_selection` is PURPOSE; World stores `measurement_limit_candidate_join` 3632 candidates).
2. SQL `>` ignores `limit_qualifier_code` (pH minimum vs BOD maximum). Qualifier is in World; comparison polarity is not a derived relation.

**HYPOTHESIS.** Exceedance is programmable once the programmer uses qualifier polarity *and* a selected-limit relation. The first is source-semantics recovery from a stored code. The second is missing WORLD state (constructor left it PURPOSE / UNRESOLVED).

### T4 (normalized 1:1 pair)

```sql
SELECT f.facility_id, feat.feature_number, par.parameter_code, mp.period_end_date,
       v.dmr_value_nmbr, a.limit_value_nmbr
FROM measurement_limit_evaluation_pair p
JOIN dmr_reported_value_kind v ON v.measurement_id = p.measurement_id
JOIN limit_value_attributes a ON a.limit_row_id = p.limit_row_id
JOIN limit_source_flags s ON s.limit_row_id = p.limit_row_id
JOIN facility f ON f.facility_id = p.facility_id
JOIN permit_feature feat ON feat.feature_id = p.feature_id
JOIN parameter par ON par.parameter_id = p.parameter_id
JOIN monitoring_period mp ON mp.period_id = p.period_id
WHERE v.value_kind = 'numeric'
  AND a.has_numeric_value = 1
  AND CAST(v.dmr_value_nmbr AS REAL) > CAST(a.limit_value_nmbr AS REAL)
  AND IFNULL(s.optional_monitoring_flag, 'N') NOT IN ('Y', 'y');
```

**MEASURED.** 78 rows. Still above GOLD M 28, for the same qualifier-polarity reason (e.g. pH 7.0 vs minimum 6.6). Optional-monitoring exclusion is World-native (`limit_source_flags`). DMR–limit pairing is 824 1:1 (`dmr_limit_correspondence`), so candidate explosion is gone.

### T2

**MEASURED.** World already contains `numeric_exceedance_result`: 39 `exceeds=1`, 349 `exceeds=0`. GOLD M has 28 exceedances. This is programming-by-reading a constructor judgment table, not recomputing from measurements.

---

## Analysis 2 — monitoring-evidence state

### T1

```sql
SELECT nodi_code, count(*) FROM reported_dmr_measurement GROUP BY 1;
```

**MEASURED.** blank 638 / `9` 36 / `C` 150. Matches GOLD E counts exactly.

`no_ordinary_numeric_result_measurement` has 186 rows (36+150). `documented_no_discharge_assertion` has **0** rows.

**OBSERVED.** The World stores NODI *codes*, not the canonical states `ESTABLISHED_NO_DISCHARGE` / `ESTABLISHED_MONITORING_NOT_REQUIRED`. Mapping `C`→no-discharge and `9`→not-required is EPA code knowledge. That is the point at which the programmer recovers source semantics.

### T4

```sql
SELECT nodi_code, value_kind, count(*) FROM dmr_reported_value_kind GROUP BY 1, 2;
```

**MEASURED.** `(numeric, blank)` 638; `(nodi, 9)` 36; `(nodi, C)` 150. Same partition, with an explicit `value_kind` that GOLD E’s `OBSERVATION_PRESENT` vs documented-no-data distinction can hang on — still not the gold state names.

### T2

`documented_no_discharge_notation` has 70 rows (not 150). `reported_measurement_stated.nodi_code` still has the raw codes. Partial semantic closure in World, incomplete.

---

## Analysis 3 — held-out follow-up (D-shaped, evaluator SQL)

Intention (not shown to constructor during A/B/C): exceedance of an enforceable numeric limit, or required monitoring without an adequate observation; exclude report-only, NODI C, NODI 9; keep unresolved separate.

### T1

```sql
-- exceedance: analysis 1
-- missing required: numeric absent and NODI not in (C, 9)
SELECT permit_nbr, perm_feature_nbr, parameter_code, monitoring_period_end, nodi_code
FROM reported_dmr_measurement
WHERE (dmr_value_nbr IS NULL OR CAST(dmr_value_nbr AS REAL) <= -1e30)
  AND IFNULL(nodi_code, '') NOT IN ('C', '9');
```

**MEASURED.** Missing-without-C-or-9 = 0. Follow-up collapses to the analysis-1 exceedance set (inflated). GOLD E agrees there is no structured `REQUIRED_MONITORING_MISSING`.

### T4

Union of analysis-1 exceedance (78) with missing-without-C-or-9 (0) = 78 follow-up rows if the programmer uses `>` polarity. T4 Purpose C additionally emitted 48 `required_monitoring_lacks_adequate_evidence` — those are Purpose IR, not World tuples (`documented_nodata_reason` in World has 0 rows).

**OBSERVED.** D-shaped follow-up *can* be expressed over T1/T4 World for (a) NODI partitioning and (b) numeric comparison. It cannot faithfully apply staged-TDS *11 limits, when-discharging exceptions, or report-only exclusion beyond `optional_monitoring_flag`, because those GOLD S semantics were not admitted as World relations.

---

## Where the programmer must recover source semantics

| Need | In World? | Recovery |
|---|---|---|
| NODI C means no discharge | code only (T1/T4); 70 notations (T2); 0 T1 assertions | EPA NODI legend |
| NODI 9 means monitoring not required | code only | EPA NODI legend |
| Report-only vs enforceable | `optional_monitoring_flag` / `limit_type_code` (T1/T4); T2 `limit_source_classification` 39 ACCEPT enforceable-numeric | partial; not full GOLD S report-only ledger |
| Min vs max limit polarity | `limit_qualifier_code` stored | programmer must interpret qualifier |
| Staged TDS *10 vs *11 in FY2025 | T1 has `permit_limit_active_month` and two effective intervals in limits; P3 never scored the clause | dates are there; the *stage* interpretation is not |
| Operative permit vs fact sheet | T4 `source_permit_document.path` includes `fact_sheet.pdf` vs `final_permit.pdf` | path string, not an authority role |
| When-discharging / first-discharge WET | sparse extracted comment text | not computable as a closed relation |

---

## Verdict on programmability

**MEASURED.** Ordinary SQL over World is sufficient for:

1. counting FY2025 DMR rows and NODI partitions that match GOLD E cardinally
2. joining measurements to numeric limits and excluding optional-monitoring flags
3. emitting a D-shaped follow-up that is “numeric `>` plus non-C/9 missing,” with missing=0

**OBSERVED.** It is **not** sufficient, without reconstructing permit/source meaning, for:

- exact GOLD M exceedance (28) — qualifier polarity and applicable-limit uniqueness
- GOLD S staged / conditional / authority clauses
- a portable ABI across trials

**HYPOTHESIS.** T4 is the best programming surface of the five Worlds. A later RAW-vs-WORLD LLM benchmark should freeze **one** World (T4 or a repaired successor), not mix five incompatible schemas. That benchmark is not justified until this sealed result is interpreted; it is not run here.
