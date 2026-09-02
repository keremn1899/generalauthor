# Experimental semantic-integration kernel

Research infrastructure, not a product path. TaskView remains the storage
implementation. This package discovers an API boundary around the pieces the BOM
experiment reused unchanged.

```text
research/semantic_integration/
  core/                 # Referent, relation, grounding, assert/retract,
                        # derivation, stale/rerun, completeness, SQL, origins
  harness/              # C0 / C1 / frontier / C2
  domains/bom/          # BOM vocabulary, C2 campaign, oracle-free frontier
  domains/taskview_migration/
  benchmarks/relation_granular_invalidation/
```

Existing experiments stay intact:

- `research/taskview_bom/`
- `research/taskview_bom_scaling/` (`SEMANTIC_FRONTIER_INFERENCE_AUTHORIZED = False`)

## C2

The live campaign is authorized only for the two frozen `acceptable_replacement`
packets:

```bash
uv run --extra dev python -m research.semantic_integration.domains.bom.c2.campaign
```

Results are under `domains/bom/c2/results/`. Tests inject a scripted provider
and do not call a model.

## Oracle-free operational frontier

S1 purpose-driven obligations from C1, frozen before C0 evaluation:

```bash
uv run --extra dev python -m research.semantic_integration.domains.bom.operational_frontier.freeze
uv run --extra dev python -m research.semantic_integration.domains.bom.operational_frontier.evaluate
```

## World IR as a Python programming substrate

Paired RAW vs WORLD analyses over frozen S1. No inference.

```bash
uv run --extra dev python -m research.semantic_integration.domains.bom.world_programming.run
```

## Benchmark

```bash
uv run --extra dev python -m research.semantic_integration.benchmarks.relation_granular_invalidation.measure
```
