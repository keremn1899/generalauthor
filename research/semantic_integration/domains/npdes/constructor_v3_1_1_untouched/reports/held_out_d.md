# Held-out Purpose D — WORLD_ONLY

Purpose D was sealed in `fixture/evaluator_only/purpose_d.md` until A/B/C Worlds were hashed (`reports/world_freeze.json`).

**Mode:** WORLD_ONLY. Participant `sources/` absent. No PDF or ECHO CSV. Frozen Constructor v3.1.1 prompts (`d_world_only`). Model `composer-2.5` / reported `Composer 2.5`.

Optional `(W, D, original sources) → ΔW_D` was **not** run. Spec: if World-only cannot fully satisfy D, record absent semantics; do not immediately expose sources. Those absences are recorded below.

Labels: **MEASURED**, **OBSERVED**, **HYPOTHESIS**.

---

## Protocol

1. Freeze P8 `06_world/world.sqlite` (equals P6 on every trial).
2. Copy World + `01_vocabulary.json` + `00_intention_contract.json` + `KERNEL.md` + `taskview/` into a fresh isolated workspace.
3. Copy Purpose D in as `D_TASK.md` only. No `sources/`.
4. Run isolated Composer 2.5. Do not modify World relation meanings.

---

## Isolation and World bytes

| Trial | rc | Timeout | Leaks | Sources present | Source-path mentions | Frozen World hash unchanged |
|---|---|---|---|---|---|---|
| T1–T5 | 0 | no | 0 | no | 0 | yes |

Hashes match `world_freeze.json` after D:

| Trial | SHA-256 |
|---|---|
| T1 | `sha256:73e519493de8f8b333d85665204cdfb92123ce715027340399ba19f2c0b8ab13` |
| T2 | `sha256:233283e3dfb8ac2ae60086ed491df43bfb42830fff11843eacb72ce603cc3123` |
| T3 | `sha256:01b211ff025b027897335856d4667883b8792f17a48f83508622d2e8a77aa7c0` |
| T4 | `sha256:a281569a4c24b0dfddc1d6bd02da3f3e937240419e8b486489dccd8bf48bad19` |
| T5 | `sha256:ac3d6248e28f52d446db419690f01a4302443fab4f46b9d572e0e1ab4d4a07bd` |

**MEASURED.** World bytes did not change. No new World relations, no new mechanical construction, no new semantic obligations, no ABI additions. New purpose-only state: `purpose_ir/d/output.json` and `08_outputs/d.json`. Agents queried `world.sqlite` via Python/SQL (`compute_purpose_d.py`).

`INCOMPLETE_PURPOSE` was not marked (same P8-style LLM projection as A/B/C).

---

## Outputs vs evaluator oracles

GOLD M has **28** mechanical-exceedance *rows* (statistical-base grain) collapsing to **10** unique `(permit, outfall, parameter, period)` keys. D outputs are at period grain. Scoring below uses unique keys unless noted.

GOLD E: 150 NODI C rows, 36 NODI 9 rows, 0 structured `REQUIRED_MONITORING_MISSING`. D scoring below uses unique `(permit, outfall, parameter, period)` keys.

| Trial | follow_up | unresolved | excluded | Exceedance hit/miss/extra (of 10 keys) | Report-only in exceedance | Missing-required ∩ NODI 9 |
|---|---|---|---|---|---|---|
| T1 | 34 (22 ex + 12 miss) | 14 | 180 (70 no_discharge, 110 report_only) | 10 / 0 / 12 | 13 | **12** |
| T2 | 26 (all exceedance) | 98 | 94 (70 no_discharge, 24 not_required) | 4 / 6 / 22 | 13 | 0 |
| T3 | 24 (10 ex + 14 miss) | 0 | 204 | 10 / 0 / 0 | 1 | **12** |
| T4 | 49 (1 ex + 48 miss) | 188 | 192 (NODI C and similar) | 1 / 9 / 0 | 1 | 0 |
| T5 | 10 (all exceedance) | 1 | 122 (86 report_only, 36 no_discharge) | 10 / 0 / 0 | 1 | 0 |

**MEASURED.** D executed from existing World on all five trials.

**OBSERVED.**

- T3/T5 recover all 10 unique GOLD M exceedance keys from World SQL with almost no extras.
- T4 reuses its conservative A/B/C posture: one exceedance (`NM0000116` TSS 210 vs 50 daily max) and 48 missing-required, 188 unresolved (including unit-mismatch). Under-closure, not a World-byte change.
- T1/T2 treat some GOLD report-only rows as exceedance follow-up (13 keys). Safety leak at D, even with `optional_monitoring_flag` in World.
- T1/T3 classify **all 12 unique NODI 9 keys** as `missing_required_monitoring`. The code is in World; the *meaning* “conditional monitoring not required” was not a World relation, so the D agent recovered EPA legend incorrectly. Safety: not-required → follow-up.

**HYPOTHESIS.** Exact D is limited by missing WORLD semantics (applicable-limit uniqueness, qualifier polarity, NODI canonical states, staged TDS), not by inability to query the compiled World.

---

## Could D run? What was absent?

| Required D semantic | Classification | Notes |
|---|---|---|
| FY2025 facility/outfall/parameter/period identity | `REUSED_EXISTING_WORLD` | Present in every World |
| Numeric reported value vs numeric limit | `DERIVABLE_FROM_EXISTING_WORLD` | T3/T5 D; T1 over-generates |
| Enforceable vs report-only | `DERIVABLE_FROM_EXISTING_WORLD` (partial) / `MISSING_DUE_TO_CONSTRUCTOR_FAILURE` (T1/T2 extras) | Flag stored; GOLD S ledger not |
| Documented no-discharge (NODI C) | `REUSED_EXISTING_WORLD` | Excluded on T1/T2/T3/T4/T5 |
| Monitoring not required (NODI 9) | `UNRESOLVED` or misclassified | T2 excluded 24 as not_required; T1/T3 → missing-required |
| Required monitoring missing | Gold: none in structured rows | T4 48 rows = constructor over-generation (`PURPOSE_ONLY` analog, derived at D time) |
| Staged TDS *11 in FY2025 | `MISSING_DUE_TO_CONSTRUCTOR_FAILURE` | Dates exist; stage interpretation never admitted |
| Source-authority (permit vs fact sheet) | `MISSING_DUE_TO_CONSTRUCTOR_FAILURE` | Paths at most |
| When-discharging / first-discharge WET | `UNRESOLVED` / missing | Not a closed World relation |

No `NEW_REUSABLE_WORLD_SEMANTIC` was added during D. That is the intended reuse test: compile meaning once, compute D later.

---

## ΔWorld

**MEASURED incremental construction:** 0 new mechanical relations, 0 new semantic relations, 0 new semantic obligations, 0 source observations, 0 World-fact invalidations.

**Optional source-exposed ΔWorld:** not run.

Question *does D trigger only the minimum new semantic construction required by the new intention?* **MEASURED:** it triggered none. Residual D error is from using incomplete existing World, not from rebuilding A/B/C.

---

## Reuse of A/B/C

**OBSERVED.** T4 D exceedance count (1) matches T4 Purpose A (`exceeds_limit` once). T5 D’s 10 unique exceedance keys are consistent with T5 A’s 28 `exceeds` rows at statistical-base grain. T1/T2 D re-derived from measurement/limit tables rather than copying A JSON (A was not in the WORLD_ONLY workspace).

This is `compile meaning once / compute over it many times` for the mechanical DMR/limit core. It is not reuse of GOLD S permit-prose closures, because those mostly never entered World.
