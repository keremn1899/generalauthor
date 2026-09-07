# World read-side discipline & programming v1

**Judgments:**

```text
PROGRAMMABLE_WORLD_SUPPORTED
MIXED_WORLD_READ_PROGRAMMING_RESULT
```

Not used: `WORLD_READ_CONTRACT_SUPPORTED` (A1 still has unsupported closures), `GRAPH_READ_API_JUSTIFIED`, `ABI_READ_SURFACE_IS_BOTTLENECK`.

**Frozen inputs:** end_to_end_v1 T1 Worlds (`harbor_towing`, `seed_grants`, `makerspace_checkout`). Hashes unchanged after every episode. `runtime_v0` hashes unchanged vs freeze. Composer 2.5 on all 6 Part A + 12 Part B runs.

This report seals the probe. Do not modify runtime, Worlds, TaskView, or add graph/ABI machinery from this result.

---

## Headline

| | A0 | A1 |
| --- | --- | --- |
| Part A establishable correct | 16/21 | 18/21 |
| Part A correct unresolved | 12/15 | 12/15 |
| Part A unsupported closures | 3 (all harbor Q6) | 3 (all harbor Q6) |
| WRONG_GRAIN (Q3) | 0/3 | 2/3 |
| UNRESOLVED_AS_FALSE (Q6) | 0/3 | 0/3 |
| PROPOSITION_CONTAMINATION (Q4) | 1/3 | 1/3 |
| Control regression | none | none |
| Part B programs correct | 18/18 | 18/18 |

---

## Required questions

### 1. Does the compact initial World contract reduce unresolved→false errors?

**MEASURED:** no. Harbor Q6 is `false` in 3/3 A0 and 3/3 A1.

**OBSERVED:** A1 consumers cited `insufficient_evidence` and still closed the polar question.

### 2. Does it reduce WORLD/PURPOSE grain confusion?

**MEASURED:** yes, materially. Q3: 0/3 A0 → 2/3 A1. A1 C1/C2 counted blank WORLD `billed_hours` (J6 only).

### 3. Does it prevent unresolved neighboring propositions from contaminating established facts?

**MEASURED:** no change in rate. Seed Q4 correct in 1/3 each arm.

### 4. Does it harm any previously correct controls?

**MEASURED:** no. 27/27 control cells target in both arms.

### 5. How much read-side introspection does A1 remove?

**MEASURED:** none. A1 adds 1176 bytes and slightly more reads (CONTRACT.md). Both arms call `inspect_world` once. See `read_surface_metrics.md`.

### 6. Can fresh agents write nontrivial relational programs over World?

**MEASURED:** yes. 12/12 P1 correct: grouped sums with joins and filters (authorized-only, established-charge-only).

### 7. Can they perform graph-shaped traversal without a native graph query language?

**MEASURED:** yes. 12/12 P2 correct via SQL joins/filters over referent columns (vessel→job→berth; award→org→awards→disbursements; member→checkout→remapped tool). No Cypher, no NetworkX, no recursive CTE required.

### 8. Which mechanisms do they naturally choose?

**MEASURED:** SQL_MULTI_RELATION 26, MIXED_SQL_PYTHON 10. 29/36 submitted codes contain JOIN. 0 recursive SQL. 0 graph libraries. 0 model-side-only composition.

### 9. Can mixed programs preserve unresolved separately from false/zero?

**MEASURED:** yes, in Part B P3 (12/12). Harbor: established total 0 with a separate insufficient_evidence list. Seed: Active remaining 15000 with sibling A-105 listed, remaining not zeroed. Makerspace: C5 fee kept, PENDING listed separately.

**OBSERVED:** Part A polar Q6 still collapses unresolved to false. Explicit “list unresolved separately” in a programming task works; a yes/no question does not.

### 10. Does one World support several distinct programs without rebuild?

**MEASURED:** yes. Each Part B episode ran P1+P2+P3 on one sqlite. Hashes unchanged.

### 11. Are failures caused by missing semantics, vocabulary discovery, consumer reasoning, or computational expressiveness?

**OBSERVED:** consumer reasoning (Part A). Semantics present. Names found. SQL expressed the graph-shaped tasks.

### 12. Is a native graph API justified by evidence?

**HYPOTHESIS:** no. Graph-shaped tasks succeeded as relational projections. `GRAPH_READ_API_JUSTIFIED` would require repeated traversal failure on the current surface.

### 13. Is a compact stable initial contract justified?

**HYPOTHESIS:** **partially, not as sealed.** It is cheap and it helped grain without control regression. It failed the preregistered 0-unsupported-closure bar. Do not promote it into the runtime. A next contract increment, if any, should state polar-question discipline explicitly. That is still host text, not a kernel primitive.

### 14. Does this strengthen the product thesis from “semantic database that answers held-out questions” to “semantic substrate that agents can program against”?

**HYPOTHESIS:** yes on programmability. Agents wrote join/group/filter programs and referent traversals against constructor-authored relations, without sources, without a graph database. The compiled World is a substrate, not only a Q&A context. Read-side yes/no discipline remains the weaker half.

---

## Part A success bar

Required: A1 0 unsupported closures **and** material improvement on preregistered families **and** no control regression.

Grain improved; controls held; unsupported closures did not go to 0. Therefore **not** `WORLD_READ_CONTRACT_SUPPORTED`.

## Part B success bar

Relational, graph-shaped, and mixed programs worked on ordinary SQL/Python in every episode. `PROGRAMMABLE_WORLD_SUPPORTED`.

---

## STOP

Sealed. Do not modify `runtime_v0`, implement ABI, add graph APIs, add Cypher/SPARQL, change TaskView, repair frozen Worlds, modify construction, add conversation, or start a larger benchmark.
