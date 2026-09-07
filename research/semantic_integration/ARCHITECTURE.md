# Semantic-integration architecture

This file is an **index**. It is not a second constitution.

| Read | For |
| --- | --- |
| [`CONSTITUTION.md`](CONSTITUTION.md) | Load-bearing semantic properties, change bars, what a valid World is |
| [`CONSTRUCTION.md`](CONSTRUCTION.md) | Product construction loop, `runtime_v0`, research constructor, agent brief |
| [`reports/open_weaknesses.md`](reports/open_weaknesses.md) | Current iffy bits (evidence, not a plan to implement) |
| [`reports/minimal_semantic_integration_synthesis_v0.md`](reports/minimal_semantic_integration_synthesis_v0.md) | Experimental synthesis after the NPDES campaign |

The product kernel (TaskView) is unchanged by this document. A kernel change still needs a concrete representational counterexample. Constructor v3 has none.

---

## Layers (dependency direction)

```text
FOUNDATIONAL          taskview/ + invariants in CONSTITUTION.md
        ↑
CONTRACTS             grounding / materializability / consumer identity / write boundary
        ↑
MECHANISMS            runtime_v0, SemanticWorld wrap, sidecars, construction.py
        ↑
RESEARCH STRATEGIES   nine-pass P0–P8, packets, REFINED, cue verifier, Probe A/B
```

Experimental strategies may depend on contracts and TaskView.

Foundational semantics must never depend on an experimental strategy.

`runtime_v0` may depend on TaskView and `core/`. TaskView must not import `runtime_v0`. Default Constructor v3 runtime must not import Probe A strategies or the v2 cue verifier.

---

## What is not this index

- **Constructor v3.1.1** is a fail-closed materializability hardening of the research constructor, not generic heterogeneous-source ingestion. See `domains/diligence/constructor_v3_1_1/ADR.md`.
- **Nine-pass artifacts** are that compiler's emission. The construction-review UI (`constructor_frontend_spec.md`, `world_explorer/construction.py`) reads them. They are not World IR ontology.
- **`construction.py`** is a supported feeding mechanism, not a primitive.
- **Sealed reports** stay sealed. Do not rewrite them to match this index.

Historical layer notes that this file used to carry (P0–P8 as “the” compiler, Probe A/B as §4) now live in `CONSTRUCTION.md` §4 and `CONSTITUTION.md` §6.
