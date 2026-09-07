# Minimal Semantic Integration v0 — Spike 1

Research-only vertical slice. Not a productization. Not an ABI increment.

Product reading: `runtime_v0` is the current construction-boundary *mechanism* (`CONSTRUCTION.md`). This report remains the sealed spike evidence. Do not rewrite it.

Runtime: `research/semantic_integration/runtime_v0/`  
Fixture: `research/semantic_integration/runtime_v0/fixtures/minimal_v0/`  
Tests: `tests/semantic_integration/test_runtime_v0_spike1.py`

```text
SPIKE1_RUNTIME_LOOP_SUPPORTED
```

---

## MEASURED

`pytest tests/semantic_integration/test_runtime_v0_spike1.py`: **7 passed**.

| Test | Result |
| --- | --- |
| Valid candidate accepted (sqlite + origins + purpose + admission) | pass |
| SQL after deleting `orders.csv` and `accounts.csv` | pass |
| `purpose_requirement_failure` grouped by SQL | pass |
| WORLD BASE `grounding=None` raises; Project.run rejects; no accepted World | pass |
| Rejected candidate leaves accepted fingerprints unchanged | pass |
| Exception after valid asserts: candidate discarded, accepted unchanged | pass |
| Explicit unresolved + PURPOSE policy without SOURCE; GM not decoded | pass |

TaskView / kernel / Constructor / architecture specs: **not modified**.

New runtime (excluding tests and fixture `construction.py`): **866 lines** across six modules (`world.py`, `purpose.py`, `source_helpers.py`, `commit.py`, `project.py`, `__init__.py`). Fixture construction: 88 lines. Tests: 254 lines.

No `_tv_*` tables were added. Failures live in ordinary relation `purpose_requirement_failure`.

---

## OBSERVED

Ordinary `construction.py` can populate TaskView if it is executed against a **candidate** `SemanticWorld` wrap rather than the in-memory Purpose-First spine `World`.

The existing `SemanticWorld.assert_tuple` still synthesizes origin-only `WORLD` grounding when observations are omitted. Spike 1 does **not** change that kernel helper. `ConstructionWorld.assert_tuple` refuses WORLD BASE without SOURCE, and `validate_world_base_source` re-checks at accept time. PURPOSE-scoped rows (policy, requirement failures) may omit SOURCE.

A failed or ungrounded run never publishes. Directory publish is candidate → staging → accepted; the candidate tree is deleted on failure.

SQL `JOIN account` / `customer_order` answers legal name and amount text after the CSV files are unlinked. The GM row remains `amount_text = 'GM'` plus `NOT_NUMERIC` and `EXPLICIT_UNRESOLVED` failure rows. Nothing in the runtime invents a GM interpretation.

ABI normalization, `field_sources`, obligations, `REFINED`, and Constructor P0–P8 were not required to complete this loop.

---

## HYPOTHESIS

The sealed v0 spec’s increments 1–4 are sufficient for the folder → construction → candidate → validate → accepted SQLite → purpose failures → SQL loop. Fail-closed WORLD grounding is a **wrap + accept validator**, not a TaskView schema change. Host compiler concepts do not need kernel names for this slice.

---

## Answers

1. **Could ordinary `construction.py` populate TaskView directly?**  
   Yes, via `ConstructionWorld` over `SemanticWorld` / TaskView. The in-memory PFPS `World` is not the store.

2. **Were any TaskView schema changes required?**  
   No.

3. **Was fail-closed WORLD grounding enforceable outside the kernel?**  
   Yes. Assertion-time `GroundingError` plus accept-time SOURCE scan. Kernel `SemanticWorld` behavior is unchanged.

4. **Could Purpose failures be represented as an ordinary relation?**  
   Yes. `purpose_requirement_failure` is PURPOSE-scoped BASE in the same sqlite. SQL inspects it; no `world.failures.json`.

5. **Did a failed candidate leave accepted World unchanged?**  
   Yes. SHA-256 fingerprints of accepted artifacts matched before and after both an ungrounded run and a mid-construction exception.

6. **Could SQL operate without reopening raw sources?**  
   Yes. After unlinking both CSVs, the join query still returned Acme/100 and Beta/GM.

7. **How much new runtime code was required?**  
   866 lines in `runtime_v0/` (six modules). Tests 254. Frozen `construction.py` 88.

8. **Which existing components were reused?**  
   TaskView (`add_referent`, `declare_relation`, `assert_tuple`, `query_semantic`, grounding tables, revisions). `SemanticWorld` + `.origins.json`. `ConstructionOrigin`, `AssertionGrounding`, `SourceObservation`. PFPS-shaped source helpers and `require_*` / `unresolved` checks. No Constructor v3.1.1 import. No diligence ABI.

9. **Did anything force ABI work earlier than expected?**  
   No. Consumers queried constructor-authored table/column names. That is acceptable for spike 1; it is not a stable ABI.

10. **Did any host/research concept leak into product/runtime abstractions?**  
    No `REFINED`, obligation, evidence plan, proposal, or semantic-family type. `purpose_requirement_failure` is an ordinary relation, as specified. `analysis_policy` is ordinary PURPOSE-scoped BASE.

---

## Judgment

```text
SPIKE1_RUNTIME_LOOP_SUPPORTED
```

The loop works without changing TaskView or kernel semantics.

---

## STOP

No ABI normalization. No semantic-resolution automation. No model capability runs. No architecture-spec edits.
