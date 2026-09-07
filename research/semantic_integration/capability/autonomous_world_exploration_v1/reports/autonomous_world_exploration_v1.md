# Autonomous World exploration v1

**Judgment:** `AGENT_NATIVE_EXPLORATION_SUPPORTED`

Not used: `EXPLICIT_ORIENTATION_PHASE_SUPPORTED` (E1 did not materially improve downstream scores), `READ_SIDE_GUIDANCE_NEEDED`.

**Frozen inputs:** end_to_end_v1 T1 Worlds; hashes unchanged after every episode. `runtime_v0` unchanged. Compact header only (PURPOSE, WORLD CONTRACT without rows, READ RULES, REVISION). Composer 2.5. 3 domains × 2 arms × 3 replicates = 18 episodes.

Sealed. Do not add leads, summaries, graph APIs, exploration planners, ABI, or runtime changes from this result.

---

## Headline

| | E0 on-demand | E1 orient then tasks |
| --- | --- | --- |
| Target-class cells (CORRECT + UNRESOLVED_CORRECTLY) | 46/54 | 46/54 |
| Establishable correct | 39/45 | 40/45 |
| Correct unresolved | 7/9 | 6/9 |
| Harbor T4 grain | 0/3 | 0/3 |
| Harbor T5 unresolved | 1/3 | 0/3 |
| Multi-hop T3 | 9/9 | 9/9 |
| Novel T6 | 9/9 | 9/9 |
| Makerspace all tasks | 18/18 | 18/18 |
| Mean task reads | 6.4 | 6.3 (+10.2 in orient) |
| `describe()` despite header | 0 | 0 |

E0 ≈ E1. E0 search is not pathological.

---

## Required answers

### 1. Can fresh agents orient themselves from the compact header?

**MEASURED:** yes. E0 completes factual, multi-hop, and novel tasks with ~6 reads and no `describe()`. E1 notes show purpose-relevant maps before tasks appear.

### 2. How much purpose-relevant structure do they discover without knowing future tasks?

**OBSERVED:** E1 notes cover WORLD/PURPOSE split, unresolved failures, join paths, remaps, and (usually) grounding. Behavioral discovery of the eight hidden targets is high; see `discovery_results.md`.

### 3. Do they discover useful cross-relation paths autonomously?

**MEASURED:** T3 multi-hop 18/18. Notes include job–vessel–berth, award–org–disbursement, checkout–tool remap.

### 4. Do they recognize WORLD vs PURPOSE grain?

**OBSERVED:** E1 notes often yes (harbor R1 lists WORLD `billed_hours` vs PURPOSE `billable_hours`). Downstream T4 still uses PURPOSE grain 6/6. Recognition in notes ≠ application under a question.

### 5. Do they find unresolved state?

**MEASURED:** yes (failure-state inspection E0 7/9, E1 orient 9/9). Applying it to polar T5 remains weak.

### 6. Do they inspect grounding when necessary?

**MEASURED:** E1 orientation 6/9 episodes; E0 task phase 0/9. Factual answers did not require grounding tables. Header rule 5 is followed mainly when orientation explicitly mentions grounding.

### 7. How much state do they need before becoming effective?

**MEASURED:** header (~2.2–2.4 KB) plus on the order of six file/SQL reads. Not a full scan.

### 8. Does an explicit exploration phase improve downstream correctness?

**MEASURED:** no material improvement. 46/54 vs 46/54. Harbor grain unchanged. Harbor T5 slightly worse under E1.

### 9. Are agents better exploring on demand once given the actual task?

**HYPOTHESIS:** yes for this pack. Preferred small-product outcome: give header + problem; do not require an orientation ritual.

### 10. What exploration operations recur naturally?

HEADER → Python `ConstructionWorld` → filtered SELECTs / successive relation reads → PURPOSE failures when the question is epistemic. Joins more often in orientation than in on-demand answering. See `exploration_behavior.md`.

### 11. Is the compact header enough?

**MEASURED:** yes for catalog. Zero `describe()` rediscovery. Empty constructor meanings (seed/makerspace) did not block exploration. Row contents and referent-prefix joins still require queries, which is appropriate.

### 12. What additional product-provided exploration machinery is justified?

**HYPOTHESIS:** none. Not leads, not summaries, not graph navigation, not preloaded samples. Residual failures are grain/false-closure/overlay reasoning, already measured in `world_read_programming_v1`.

### 13. Does the evidence support compile domain → small header → SQL/Python → ordinary agency?

**HYPOTHESIS:** yes, for autonomous exploration of these Worlds. Programmability was already `PROGRAMMABLE_WORLD_SUPPORTED`. This probe adds: agents find purpose-relevant structure on demand without extra exploration product.

---

## Hypotheses

| id | reading |
| --- | --- |
| H1 Native on-demand | **Supported.** E0 ≈ E1; E0 not pathological. |
| H2 Orientation helps | **Not supported** as a correctness intervention. Notes are nicer; scores are not. |
| H3 Interface problem | **Not supported.** State was found. |

---

## STOP

Do not modify `runtime_v0`, implement ABI, add leads, add domain summaries, add graph APIs, add an exploration planner, modify TaskView, repair Worlds, or start a larger benchmark.
