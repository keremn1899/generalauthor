# Constructor v3.1.1 — ABI Materializability Invariant Sealed Report

**Architecture Status**: Compiler Hardening Sealed Increment (Deterministic Python Only)
**TaskView Kernel Hash**: `7704e551b50cacb9` (Identical to v3.1, 0 kernel changes)
**Model Calls**: 0 | **Source Evidence Rereads**: 0

---

## 1. Architectural Increment

### Inadequacy of Previous v3.1 `SATISFIED` Definition
In Constructor v3.1, `check_abi` inspected only `01_vocabulary.json`. A required semantic identity was marked `SATISFIED` as long as a role binding was declared in the vocabulary schema. This allowed a critical divergence: in frozen trial T3, `active` was reported `SATISFIED`, yet normalization reported `contract_active` as missing because the table contained 0 assertions in World. Similarly, in trial T1, `clause_kind` was reported `SATISFIED`, but the constructor marked `clause_presence` as a `PURPOSE` admission relation, leaving 0 assertions in the World and causing normalization to miss `contract_clause_kind`. Under v3.1, `SATISFIED` meant only that a declaration binding existed, failing to guarantee that the compiler could mechanically compile the required consumer interface.

### The Exact Compiler Invariant Enforced in v3.1.1
Constructor v3.1.1 establishes the foundational compiler invariant:

\[\forall f \in \text{RequiredConsumerFields}: \quad \text{SATISFIED}(f) \implies f \in \text{Normalize}(W)\]

where \(\text{Normalize}(W)\) denotes the canonical consumer interface produced mechanically from the World and its contracts.

To satisfy this invariant:
1. **BINDING**: A valid `semantic_identity` or `field_sources` binding must declare how the requirement is mapped.
2. **MATERIALIZABILITY**: The required semantic value/relation must be mechanically materializable from the current World using the declared contracts and the deterministic normalizer.
3. **SINGLE SOURCE OF TRUTH**: ABI completeness directly invokes `normalize_world()` to eliminate any discrepancy between compiler admission checks and downstream normalization.
4. **FAIL-CLOSED PROJECTION**: If a declared binding cannot be materialized, it produces `UNSATISFIED: NOT_MATERIALIZABLE`. The purpose status immediately fails closed to `INCOMPLETE_PURPOSE` before exact projection.

---

## 2. Direct Answers to Required Questions

1. **Does `SATISFIED` now guarantee actual materializability?**  
   **Yes.** Under v3.1.1, `SATISFIED` requires both a declared binding and successful non-empty mechanical extraction into the canonical consumer table by the normalizer. If a binding is declared but unmaterializable from World, it is strictly reported as `UNSATISFIED` with reason `NOT_MATERIALIZABLE`.

2. **Were there any `SATISFIED` requirements that normalization failed to produce?**  
   **No.** Across 335 audited checks covering certified World, all 8 Probe B morphisms, the 5 frozen participant Worlds, and 4 negative controls, exactly 0 invariant violations occurred.

3. **What exactly caused the frozen v3.1 T3 `contract_active` miss?**  
   In T3, `contract_lifecycle_judgment` was declared in the vocabulary with role `active` (`semantic_identity="active"`), but pass P6 asserted 0 tuples into that table (all 5 contract terms were classified as `UNRESOLVED`, and ungrounded/boolean tuples were omitted). Because the table in `06_world/world.sqlite` had 0 rows, normalizer `_active_rows` returned empty, and `contract_active` was missed. This was **Cause B**: declared binding without enough World semantics to materialize the canonical relation.

4. **What exactly caused the frozen v3.1 T1 `contract_clause_kind` miss?**  
   In T1, `clause_presence` was declared with `roles: [contract, clause_kind, disposition]`, but assigned admission class `PURPOSE` rather than `WORLD`. During P6 admission, purpose-scoped relations were deliberately omitted from persistence into `06_world/world.sqlite`. Consequently, `clause_presence` in World had 0 rows, causing `_clause_rows` to return empty. This was **Cause B**: declared binding without enough World semantics to materialize the canonical relation.

5. **Were either of those normalizer bugs, or were the Worlds semantically insufficient despite declared bindings?**  
   **Neither was a normalizer bug.** In both T1 and T3, the Worlds were semantically insufficient (0 rows persisted in the relevant World database tables). The normalizer operated correctly according to specification. The bug was in the v3.1 ABI completeness check, which checked only schema declarations without verifying World contents.

6. **Do declared-but-unmaterializable bindings now become `INCOMPLETE_PURPOSE` before projection?**  
   **Yes.** In both T1 and T3, unmaterializable bindings produce `UNSATISFIED (NOT_MATERIALIZABLE)`, setting `abi["ok"] = False`. `write_workspace_outputs` halts projection and outputs `INCOMPLETE_PURPOSE` for all dependent purposes, recording `skipped: True` and `reason: ABI_COMPLETENESS` in `08_normalization.json`.

7. **Does ABI completeness use the same materialization semantics as the normalizer?**  
   **Yes.** ABI completeness directly imports and executes `normalize_world()` from `normalizer.py`. There is a single source of truth for realizability.

8. **Did the certified normalization suite remain exact?**  
   **Yes.** The certified baseline and all 8 Probe B morphisms remain 100% exact: `world_correctness: {A: true, B: true, C: true, D: true, all_exact: true}`, with `missing_mappings: []` and `false_mappings: []`.

9. **Did any model call or source reread occur?**  
   **No.** Model calls: 0. Source evidence rereads: 0. All operations are deterministic compiler logic.

10. **Did any kernel abstraction change?**  
    **No.** `taskview/` kernel abstractions remain untouched. SHA256 prefix is `7704e551b50cacb9` (identical to v3.1). Kernel diff: 0 lines.

11. **Did experimental code leak into foundational/runtime dependencies?**  
    **No.** `test_dependencies.py` verified 0 forbidden imports across `constructor_v3_1_1/runtime/` (violations: 0).

12. **Is the frozen system now: `READY_FOR_UNTOUCHED_DOMAIN` or `NOT_READY`?**  
    **`READY_FOR_UNTOUCHED_DOMAIN`.** All readiness requirements are completely fulfilled.

---

## 3. Regression Analysis: Frozen v3.1 T1 & T3

| Trial | Missed Interface | Schema Declaration | World Table State | Root Cause Category | v3.1 Status | v3.1.1 Status | Downstream Result |
|---|---|---|---|---|---|---|---|
| **T1** | `contract_clause_kind` (`clause_kind`) | Declared on `clause_presence` | `clause_presence` in `06_world` has 0 rows (`PURPOSE` admission omitted) | **Cause B** (Semantically insufficient World) | `SATISFIED` | `UNSATISFIED: NOT_MATERIALIZABLE` | `INCOMPLETE_PURPOSE` (projection halted) |
| **T3** | `contract_active` (`active`) | Declared on `contract_lifecycle_judgment` | `contract_lifecycle_judgment` in `06_world` has 0 rows (`UNRESOLVED` lifecycle) | **Cause B** (Semantically insufficient World) | `SATISFIED` | `UNSATISFIED: NOT_MATERIALIZABLE` | `INCOMPLETE_PURPOSE` (projection halted) |
| **T3** | `contract_clause_kind` (`clause_kind`) | Declared on `clause_kind_judgment` | Not persisted in `06_world` (`PURPOSE` admission) | **Cause B** (Semantically insufficient World) | `SATISFIED` | `UNSATISFIED: NOT_MATERIALIZABLE` | `INCOMPLETE_PURPOSE` (projection halted) |

---

## 4. Validation Results

### Certified Suite & Probe B Morphisms Replay

| Suite / Morphism | ABI OK | Satisfied Fields | Unsatisfied | Normalized Recovered | Normalized Missing | Exactness (A/B/C/D) | Behavioral Equivalence |
|---|---|---|---|---|---|---|---|
| **Certified Baseline** | True | 13/13 | [] | 7/7 | [] | All Exact (True) | Baseline |
| `rename` | True | 13/13 | [] | 7/7 | 0 | All Exact (True) | True |
| `role_surface` | True | 13/13 | [] | 7/7 | 0 | All Exact (True) | True |
| `orientation` | True | 13/13 | [] | 7/7 | 0 | All Exact (True) | True |
| `layout` | True | 13/13 | [] | 7/7 | 0 | All Exact (True) | True |
| `epistemic` | True | 13/13 | [] | 7/7 | 0 | All Exact (True) | True |
| `decompose` | True | 13/13 | [] | 7/7 | 0 | All Exact (True) | True |
| `noise` | True | 13/13 | [] | 7/7 | 0 | All Exact (True) | True |
| `counterparty_bind` | True | 13/13 | [] | 7/7 | 0 | All Exact (True) | True |

### Frozen Participant Trials Replay (v3.1 vs v3.1.1)

| Trial | v3.1 ABI Status | v3.1.1 ABI Status | Unsatisfied Fields & Reasons | Recovered Relations | Missing Relations | Purpose Status (A/B/C/D) |
|---|---|---|---|---|---|---|
| **T1** | ok=True (13/13 SATISFIED) | ok=False (12/13 SATISFIED) | clause_kind: NOT_MATERIALIZABLE | 6/7 | ['contract_clause_kind'] | INCOMPLETE_PURPOSE |
| **T2** | ok=True (13/13 SATISFIED) | ok=True (13/13 SATISFIED) | None | 7/7 | [] | COMPLETE |
| **T3** | ok=True (13/13 SATISFIED) | ok=False (11/13 SATISFIED) | active: NOT_MATERIALIZABLE, clause_kind: NOT_MATERIALIZABLE | 5/7 | ['contract_active', 'contract_clause_kind'] | INCOMPLETE_PURPOSE |
| **T4** | ok=True (13/13 SATISFIED) | ok=True (13/13 SATISFIED) | None | 7/7 | [] | COMPLETE |
| **T5** | ok=True (13/13 SATISFIED) | ok=True (13/13 SATISFIED) | None | 7/7 | [] | COMPLETE |

### Deterministic Negative Controls (N1–N4)

| Control | Name | Condition | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|
| **N1** | no binding | Synthetic test fixture | UNSATISFIED (NO_BINDING) | UNSATISFIED (NO_BINDING) | PASS |
| **N2** | declared but not materializable | Synthetic test fixture | UNSATISFIED (NOT_MATERIALIZABLE) | UNSATISFIED (NOT_MATERIALIZABLE) | PASS |
| **N3** | declared and materializable | Synthetic test fixture | SATISFIED (MATERIALIZED) | SATISFIED (MATERIALIZED) | PASS |
| **N4** | ambiguous realization | Synthetic test fixture | AMBIGUOUS | AMBIGUOUS | PASS |

### Comprehensive Invariant Audit

- **Total Checks Audited**: 335
- **Invariant 1 Violations** (`SATISFIED(f) ⇒ f ∈ Normalize(W)`): **0**
- **Invariant 2 Violations** (`COMPLETE purpose ⇒ all required fields exist`): **0**
- **Audit Status**: **PROVEN_CLOSED**

---

## 5. Readiness Judgment

### **Verdict: READY_FOR_UNTOUCHED_DOMAIN**

### Justification Against All Blocking Criteria:
1. **Materializability Guarantee**: `SATISFIED` strictly guarantees materializability (\(\text{violations} = 0\)).
2. **Downstream Safety**: Declared but unmaterializable bindings become `INCOMPLETE_PURPOSE` before projection, preventing silent downstream omissions.
3. **Certified Suite Exactness**: Certified baseline and all 8 Probe B morphisms remain 100% exact.
4. **Deterministic Negative Controls**: N1 (no binding), N2 (unmaterializable), N3 (materializable), and N4 (ambiguity detection) all pass deterministically.
5. **Kernel Non-Regression**: Kernel diff is 0 lines (`TaskView` hash `7704e551b50cacb9` preserved).
6. **Zero Model & Evidence Calls**: 0 LLM calls, 0 source rereads.
7. **Hygiene**: Zero forbidden imports into runtime dependencies.

The deterministic compiler boundary is now fully aligned with the consumer contract.

