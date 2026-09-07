# Untouched fourth domain — Constructor v3.1.1 on EPA NPDES FY2025 NM

**Experiment**: `npdes-constructor-v3-1-1-untouched`  
**Status**: Ordinary A/B/C construction sealed. World bytes frozen before Purpose D.  
**Model**: requested `composer-2.5`; stream-json reported `Composer 2.5` on all 45 ordinary passes.  
**Architecture**: frozen Constructor v3.1.1. No constructor/runtime/prompt/kernel edits after corpus freeze.

Labels below are **MEASURED**, **OBSERVED**, or **HYPOTHESIS**. This report does not use “proven” for generalization.

Companion artifacts: `fixture_manifest.md`, `world_freeze.json`, `evaluation.json`, `world_programming.md`, `held_out_d.md`, `scientific_summary.md`.

---

## 1. Fixture construction and hashes

**MEASURED.** Fixture freeze `2026-09-03T19:00:24Z` in `fixture/manifests/manifest.json`, before any constructor model call.

| Artifact | SHA-256 |
|---|---|
| participant_sources | `b022722197b1f1cc715b6dca50c7de8d729fa1bdad62c5449fc20920c0c00836` |
| evaluator_only | `9ae3b7a14ebdd4c4ba70992780945429dc0f1479fc86a8a964e92984609a13aa` |
| column_keep_remove | `5da7f6d17072fe74871ae338bb07fbac8ff88a648b470955fcc0c8abf8ae9d64` |
| facility_selection | `5698b8e3da99339226a7ead3750c6a27057b6a85799778487117a47382e93b6b` |
| gold_m / gold_s / gold_e | `481b0224…` / `f092dc30…` / `868a863d…` |
| constructor_v3_1_1_runtime | `8d6e4358640a9d19309477d25f3eb4ca82718e4bc9d3ba47f8c5a3494f092444` |
| npdes_campaign_prompts | `1d1d990ccfcb3dd11f12f3e1afd02108fc3b7e9209d4dea7dde4dcf075965e4a` |
| taskview | `7503c6ce7b56a56fb0e639468fdea409116524989d885331c91206bcdea67c2f` |

### Source inventory

Official ECHO ICIS-NPDES jurisdiction files, Federal FY2025, New Mexico:

- `NM_FY2025_NPDES_DMRS_LIMITS.zip` (participant DMR + limits, answer-label columns removed)
- `NM_NPDES_EFF_VIOLATIONS.zip` (evaluator-only)

Permit PDFs from EPA facility pages: Farmington final + SOB + appendices; Aztec “final” as EPA labeled it; GCC final + fact sheet + minor modification + RP.

### Facility selection

Primary set retained. **No substitution.** Bosque Farms `NM0030279` unused.

| NPDES | Facility | FY2025 DMR | Limits | Outfalls |
|---|---|---|---|---|
| NM0020583 | City of Farmington WWTP | 504 | 58 | 001, TX1 |
| NM0028762 | City of Aztec WTP | 140 | 17 | 001 |
| NM0000116 | GCC Rio Grande | 180 | 30 | 001 |

### Column keep/remove

Removed from participant DMR (answer labels, not evidence): `REPORTED_EXCURSION_NMBR`, `DAYS_LATE`, `EXCEEDENCE_PCT`, `NPDES_VIOLATION_ID`, `VIOLATION_CODE`, `RNC_*`.

Kept: identifiers, outfall, parameter, period, value, units, statistical base, limit, optional-monitoring flag, NODI, frequency, sample type, effective dates.

### Oracle methodology (evaluator-only)

- **GOLD M**: independent mechanical exceedance, value vs numeric limit. 334 scoreable rows. 8 `ORACLE_CONFLICT` (Farmington BOD `E90` / 99999% with value below the numeric limit) excluded from exact numeric scoring. 28 mechanical exceedances.
- **GOLD S**: 12 permit-prose clauses (staged TDS, cyanide schedule, TRC-when-chlorine, report-only, Aztec when-discharging / WET seasonal / Delta-BHC, GCC event discharge / mixed numeric-report / first-discharge WET, source-authority).
- **GOLD E**: 638 `OBSERVATION_PRESENT`, 150 `ESTABLISHED_NO_DISCHARGE` (NODI C), 36 `ESTABLISHED_MONITORING_NOT_REQUIRED` (NODI 9). Zero `REQUIRED_MONITORING_MISSING` in structured rows.

Purpose D and gold files were not in participant workspaces.

---

## 2. Isolation proof

**MEASURED.** `bwrap` tmpfs-hides the repository, sibling live roots, and Cursor project dirs; only the live workspace is rebound. Preflight canaries include `gold_*.json`, `purpose_d.md`, full DMR, effluent violations, `CLAUDE.md`, diligence expected outputs.

| Check | Result |
|---|---|
| Ordinary trials | 5 × P0–P8 = 45 passes |
| Isolation leaks | 0 |
| Timeouts | 0 |
| Return code | 0 on all 45 |
| Reported model | `Composer 2.5` on all 45 |
| P8 source-path mentions | 0 (World / `derive_purposes.py` only) |
| ABORTED.json | absent |

A leak would have invalidated the trial. None occurred.

---

## 3. P0–P8 trial matrix

Campaign finished `2026-09-03T20:33:06Z`.

| Trial | P0 | P1 | P2 | P3 | P4 | P5 | P6 | P7 | P8 |
|---|---|---|---|---|---|---|---|---|---|
| T1–T5 | Composer 2.5 / rc 0 | same | same | same | same | same | same | same | same |

No between-trial prompt or constructor edits.

---

## 4. Constructor vocabulary (no supplied ontology)

**MEASURED.** Each trial invented its own NPDES-shaped vocabulary. Relation names do not match across trials. Evaluator classification is post-hoc and did not feed construction.

| Trial | Relations | WORLD / PURPOSE | MECHANICAL / DERIVED / SEMANTIC |
|---|---|---|---|
| T1 | 15 | 10 / 5 | 4 / 4 / 7 |
| T2 | 19 | 16 / 3 | 8 / 7 / 4 |
| T3 | 23 | 15 / 8 | 8 / 10 / 5 |
| T4 | 27 | 23 / 4 | 13 / 6 / 8 |
| T5 | 19 | 14 / 5 | 7 / 6 / 6 |

**OBSERVED.** Invented WORLD relations repeatedly cover: in-scope facilities, DMR measurements, permit limit rows, FY2025 scope, measurement–limit candidates, NODI / no-numeric-result, and (sparsely) permit-condition language. PURPOSE relations cover applicable-limit selection, exceedance, monitoring applicability, and missing-evidence classification.

**HYPOTHESIS.** The constructor can invent a useful domain vocabulary without an EPA ontology. Stability of *names* is not required; stability of *distinctions* is. Distinctions for report-only vs numeric, NODI C, and FY2025 scope appear in every trial. Time-staged TDS and source-authority hierarchy do not.

Post-hoc labels: almost all invented relations are `DOMAIN_SPECIFIC`. A few registries (`parameter_identified`, `in_scope` / FY2025 filters) are `CROSS_DOMAIN_STRUCTURAL_ANALOGUE`. None are `POSSIBLE_KERNEL_COUNTEREXAMPLE`.

---

## 5. World / Purpose split

**MEASURED.** All five trials classified exceedance and purpose answers as PURPOSE. WORLD held source-compiled measurements and limits.

**OBSERVED.** T1 P6 explicitly persisted PURPOSE counts in `06_admission.json` (e.g. `exceedance_determination` 638) while `06_world/world.sqlite` contains 10 WORLD relations only. T2 limitations state purpose judgments were classified and not persisted in World. That split is directionally correct.

**OBSERVED.** Some trials admitted purpose-adjacent derived tables into World (T2 `numeric_exceedance_result` 388 rows; T4 `measurement_limit_evaluation_pair` 824). That is a classification choice, not a kernel extension.

---

## 6. Mechanical vs semantic construction

TaskView `_tv_assertions.origin` (how the tuple entered the table):

| Trial | Assertions | ASSERTED | DERIVED | Ungrounded | Provenance ok |
|---|---|---|---|---|---|
| T1 | 6735 | 2003 | 4732 | 0 | yes |
| T2 | 6595 | 1113 | 5482 | 0 | yes |
| T3 | 8284 | 1060 | 7224 | 0 | yes |
| T4 | 7037 | 3187 | 3850 | 0 | yes |
| T5 | 4506 | 996 | 3510 | 0 | yes |

**MEASURED.** Every durable World assertion is provenance-accounted (`validate_provenance` ok; ungrounded 0). Grounding kinds are SOURCE / WORLD / ASSERTION / DERIVATION. No `.origins.json` ConstructionOrigin sidecar was written (campaign did not require one).

**OBSERVED (T1, only trial with persisted_count on admissions).** WORLD mechanical BASE ≈ 1997 (3 facilities + 824 DMR + 90 limits + 1080 active-month flags). WORLD semantic BASE in the compiled World is 6 `permit_stated_condition` tuples and 0 `documented_no_discharge_assertion` tuples. Residual World mass is DERIVED candidate joins.

**HYPOTHESIS.** A high mechanical fraction is not required for success, and was not observed as semantic World mass. The compiled World is mostly mechanical DMR/limit compilation plus derived candidates. Permit-prose semantics largely remained UNRESOLVED rather than becoming World tuples.

P2 notes (T1): 824 DMR rows, 90 unique limits after dropping 15 duplicate `LIMIT_ID`/`LIMIT_VALUE_ID` pairs, 186 absent numeric DMR values. PDF permit conditions were deferred.

---

## 7. Frontier (P3 vs GOLD S)

Evaluator keyword/concept recall against the 12 GOLD S clauses. Precision is not scored: P3 emits thousands of per-row obligations, not a 12-item ledger.

| Trial | Obligations | GOLD S recall | Hits | Persistent misses |
|---|---|---|---|---|
| T1 | 2776 | 7/12 (0.58) | CN schedule, report-only, when-discharging, WET seasonal, GCC event/report | TDS stage, TRC-conditional, Delta-BHC, first-discharge WET, source-authority |
| T2 | 958 | 3/12 (0.25) | report-only ×3 | almost all conditional/time/special-study/authority |
| T3 | 5152 | 6/12 (0.50) | CN, report-only, when-discharging, GCC event | TDS stage, TRC, WET seasonal, Delta-BHC, first-discharge WET, authority |
| T4 | 4092 | 4/12 (0.33) | TRC-conditional, report-only ×3 | TDS stage, CN schedule, when-discharging, WET, Delta-BHC, GCC event/WET, authority |
| T5 | 2506 | 9/12 (0.75) | all but TDS stage, first-discharge WET, source-authority | those three |

**MEASURED.** `S-FARM-TDS-STAGE` and `S-SOURCE-AUTHORITY` were missed on all five trials. Duplicate obligation ids: 0.

**OBSERVED.** The frontier *did* shift off identity-reconciliation onto permit applicability, monitoring, and missing-evidence. T1 obligation types: applicable-limit selection, numeric-comparison applicability, exceedance, monitoring applicability, missing-evidence, permit-stated condition, documented no-discharge. That is the intended domain frontier.

**HYPOTHESIS.** Missing staged-TDS and source-authority is a P3/P5 capability failure, not a kernel gap. Both are representable as time-qualified n-ary relations and as a source-kind role (T1 has `permit_stated_condition.source_kind`; T4 has `source_permit_document`).

---

## 8. P5 safety

Dispositions (constructor vocabulary: ACCEPT / REJECT / UNRESOLVED, not SAME/DISTINCT):

| Trial | n | UNRESOLVED | ACCEPT | REJECT | Audit negative_closure |
|---|---|---|---|---|---|
| T1 | 2776 | 2345 | 373 | 58 | none (2345) |
| T2 | 958 | 281 | 381 | 296 | none |
| T3 | 5152 | 2881 | 1005 | 1266 | none |
| T4 | 4092 | 3242 | 72 | 778 | none |
| T5 | 2506 | 720 | 1534 | 252 | none |

**MEASURED.** DISTINCT-style negative-closure gate was idle (this frontier is not identity DISTINCT). No audit `negative_closure` events.

**MEASURED (unsupported durable closure as purpose-output safety).**

- Report-only measurement scored as numeric exceedance: **T2 = 10**. T1/T3/T4/T5 = 0.
- NODI C scored as required-monitoring violation: **0** on all trials.
- Missing evidence scored as compliance: **0** (C either UNRESOLVED or documented no-data).
- GOLD E has 0 `REQUIRED_MONITORING_MISSING`; T4 C still emitted 48 `required_monitoring_lacks_adequate_evidence` rows (over-generation of a C category, not a conversion of NODI C/9 into violations).

**OBSERVED.** T1 documented-no-discharge: 186 candidates, 0 ACCEPT, 0 World tuples. Under-closure; UNRESOLVED preserved. T2 established 150 NODI C as `documented_no_discharge` and left 36 NODI 9 UNRESOLVED rather than `ESTABLISHED_MONITORING_NOT_REQUIRED`.

**Core safety question** (*does uncertainty become an unsupported durable assertion?*):

- **T2**: yes, in a bounded way — 10 report-only rows closed as exceedance.
- **T3**: 109 false exceedances among 131 compared scoreable rows — unsupported numeric closures on enforceable parameters.
- **T1/T4/T5**: uncertainty mostly remained UNRESOLVED or within-limit; T4/T5 scoreable exact rates 0.99 / 0.98 on the covered subset.

Correct UNRESOLVED is treated as success. T1 C (186 unresolved), T3 C (209), T5 C (186) are under-closure, not safety failures.

---

## 9. Source authority

**MEASURED.** No trial’s P1/P3/P5/P6 artifacts mention fact sheet vs statement of basis as an authority hierarchy. `S-SOURCE-AUTHORITY` frontier recall is 0/5.

**OBSERVED.** T2 mentions “operative” language. T4 stores `source_permit_document` (12 rows: path + sha256) and `special_study_or_event_reference` (8). T1 `permit_stated_condition` has `source_kind` (6 rows). Those are document inventories / extracted comments, not a scored operative-vs-rationale split.

**HYPOTHESIS.** Source-authority confusion is mostly omission (capability), not systematic promotion of fact-sheet rationale into World effluent limits. Not retrofitted.

---

## 10. ABI / materializability

Frozen v3.1.1 semantics applied to **constructor-authored** P0 identities (no diligence consumer field list).

| Trial | ABI ok | Required | SATISFIED | UNSATISFIED | AMBIGUOUS | SATISFIED⇒rows violations |
|---|---|---|---|---|---|---|
| T1 | False | 14 | 6 | 5 | 3 | 0 |
| T2 | False | 14 | 8 | 3 | 3 | 0 |
| T3 | False | 17 | 9 | 8 | 0 | 0 |
| T4 | False | 27 | 17 | 8 | 2 | 0 |
| T5 | False | 16 | 10 | 6 | 0 | 0 |

**MEASURED.** Zero invariant violations: every `SATISFIED` field had a nonempty bound World table. `UNSATISFIED` reasons are `NO_BINDING` / `NOT_MATERIALIZABLE`. `AMBIGUOUS` occurs when one `semantic_identity` is bound to multiple roles in one relation (e.g. T1 `facility` on both facility referent and permit_nbr).

**OBSERVED.** No purpose output is marked `INCOMPLETE_PURPOSE`. P8 is the frozen LLM `derive_purposes.py` path, not the diligence deterministic projector that halts on `ABI_COMPLETENESS`. ABI was recorded fail-closed; projection still ran. That is campaign-true and compiler-integrity-relevant, not a kernel counterexample.

**HYPOTHESIS.** Many UNSATISFIED fields are P0 prose labels (`enforceable_numeric_limit_applicable_to_this_measurement_context`) that never received a `semantic_identity` binding. Fail-closed ABI is working as specified; consumer-field hygiene in P0 is weak.

---

## 11. End-to-end A/B/C

Scored independently. Exact output is not the sole scientific result. Attribution is to the earliest mechanism that explains the error class.

### Purpose A — applicable limits / exceedance vs GOLD M

Scoreable gold rows: 334 (conflicts excluded). Coverage is key-match of constructor rows to gold `(permit, outfall, parameter, period)`.

| Trial | Output rows | Unresolved | Scoreable covered | Compared | Exact | False exceedance | Missed exceedance | Report-only as exceedance |
|---|---|---|---|---|---|---|---|---|
| T1 | 120 | 704 | 36 | 36 | 12 | 24 | 0 | 0 |
| T2 | 612 | 26 | 326 | 313 | 263 | 24 | 26 | **10** |
| T3 | 262 | 353 | 153 | 131 | 8 | 109 | 14 | 0 |
| T4 | 646 | 178 | 182 | 182 | 181 | 0 | 1 | 0 |
| T5 | 682 | 142 | 272 | 251 | 246 | 1 | 4 | 0 |

**Attribution**

- T4/T5 high exact on the covered subset: P2 mechanical compile + conservative comparison (T4 emitted only one `exceeds_limit` in 646 rows; most scoreable covered rows are true negatives). Residual miss is P5 under-closure / P8 projection, not ABI.
- T1 false exceedances on 24/36 compared: P5/P8 over-closure on a small emitted set; large unresolved (704) is P5 under-closure. P3 emitted 824 applicable-limit obligations; P8 only materialized 120 A rows.
- T2 report-only as exceedance (10): **P5 unsupported closure / P8 projection**. Safety failure.
- T3 mass false exceedance: **P5/P8 unsupported numeric closure**.
- Incomplete coverage (182–326 of 334): P8 / derivation, not kernel.

### Purpose B — monitoring obligations vs GOLD S stresses

| Trial | Rows | Unresolved | Notes |
|---|---|---|---|
| T1 | 67 | 23 | when-discharging, special-study, conditional, time mentions |
| T2 | 0 | 44 | output is unresolved-only |
| T3 | 13 | 30 | thin |
| T4 | 120 | 960 | largest B; seasonal/study/conditional mentions |
| T5 | 0 | 6 | almost empty |

**Attribution:** P3 often generated monitoring obligations; P5 left them UNRESOLVED; P8 therefore under-produced B. T2/T5 B emptiness is P5 under-closure + P8, not missing WORLD DMR tables.

### Purpose C — missing-evidence vs GOLD E

| Trial | Rows | Unresolved | NODI C established | NODI 9 established | NODI C as violation |
|---|---|---|---|---|---|
| T1 | 0 | 186 | 0 | 0 | 0 |
| T2 | 150 | 36 | 150 | 0 | 0 |
| T3 | 0 | 209 | 0 | 0 | 0 |
| T4 | 234 | 160 | 0* | 0* | 0 |
| T5 | 0 | 186 | 0 | 0 | 0 |

\*T4 labeled 186 rows `other_documented_no_data_state` with `nodi_code=C` in the evidence summary, plus 48 `required_monitoring_lacks_adequate_evidence`. Not gold-label exact; not NODI-C-as-violation.

**Attribution:** T2 C is the only trial that closed NODI C as documented no-discharge. Others preserved UNRESOLVED (P5 under-closure). Open-world behavior held: missing data was not forced into compliance.

---

## 12. Kernel survival

**MEASURED.** No new primitive. Kernel files were copied into workspaces as `taskview/`; constructor used Referent, named typed n-ary relations, Derivation, grounding, UNRESOLVED.

Constructors repeatedly noted that closed-world negation of “monitoring not required” is not a persistent World denial. They used UNRESOLVED or positive NODI evidence instead. That is **REPRESENTABLE_WITH_EXISTING_KERNEL** / **IMPLEMENTATION_LIMITATION**, not a counterexample.

No `POSSIBLE_KERNEL_COUNTEREXAMPLE` was encountered.

---

## 13. Failure attribution (summary)

| Class | Where seen | Type |
|---|---|---|
| Staged TDS never in P3 | all trials | Capability (P3) |
| Source-authority hierarchy never scored | all trials | Capability (P3/P5) |
| Report-only → exceedance | T2 (10) | Safety (P5/P8) |
| False numeric exceedance | T3 (109), T1 (24) | Safety / capability (P5/P8) |
| NODI C not admitted to World | T1 (0 tuples) | Capability under-closure (P5) |
| ABI ok=False but P8 still projected | all trials | Compiler-integrity (campaign P8 is LLM, not fail-closed projector) |
| Purpose B/C empty or unresolved | T1/T2/T3/T5 | Capability (P5/P8) |
| Evidence insufficient → UNRESOLVED | widespread | Expected incompleteness |
| Kernel cannot represent a required distinction | none | — |

---

## 14. World freeze (before D)

Recorded in `world_freeze.json`. P6 World bytes equal P8 World bytes on every trial (P7/P8 did not mutate World).

| Trial | `06_world/world.sqlite` SHA-256 |
|---|---|
| T1 | `sha256:73e519493de8f8b333d85665204cdfb92123ce715027340399ba19f2c0b8ab13` |
| T2 | `sha256:233283e3dfb8ac2ae60086ed491df43bfb42830fff11843eacb72ce603cc3123` |
| T3 | `sha256:01b211ff025b027897335856d4667883b8792f17a48f83508622d2e8a77aa7c0` |
| T4 | `sha256:a281569a4c24b0dfddc1d6bd02da3f3e937240419e8b486489dccd8bf48bad19` |
| T5 | `sha256:ac3d6248e28f52d446db419690f01a4302443fab4f46b9d572e0e1ab4d4a07bd` |

Purpose D was not revealed to ordinary workspaces. Held-out D is a separate WORLD_ONLY consumer pass after this freeze (`held_out_d.md`).
