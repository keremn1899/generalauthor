# One-off graph programming v1

**Status: frozen for the frozen-view SQL-native vs graph-native campaign.**

The deterministic acceptance gate is
`tests/test_one_off_programming_v1_acceptance.py`. It covers neutral schema
description, generated-contract execution, authored-contract precedence,
predicate-constrained expansion and paths, set algebra/intermediate reuse,
named compact answers, retained audit evidence, full-mode compatibility, and
the legacy answer-list form. Product changes to this surface require an
acceptance defect; experiment outcomes do not reopen it.

This is the frozen one-off read surface for a materialized task graph.

## Schema before interpretation

`describe` returns only representation facts:

- graph version and schema fingerprint;
- node kinds;
- logical predicates, their physical carrier, direction, and observed endpoint kinds;
- bounds and operations for `lookup`, `expand`, `path`, and an ephemeral program.

It does not return landmarks, centrality, recommended procedures, task instructions, Compass material, or inferred edges. `orient` remains the separately scoped product/orchestration view.

## Immediate programmability

`run_ephemeral_traversal` first uses an authored `graph.md` or workbook traversal document when one exists. Without either, it derives an in-memory minimal contract from `describe`'s stored schema. It writes no `graph.md`, carries no orientation prose or named traversal, and supports the same bounded predicate vocabulary. A named traversal remains unavailable until someone authors one.

## Compact results

An ephemeral or named traversal may name answer sets and request a compact response:

```yaml
answers:
  affected: $affected
  uncovered: $uncovered
result_mode: compact
```

The model receives named ID sets, traversal identity, and the execution receipt. It does not receive intermediate node/edge/path evidence. The full evidence packet, program, and receipt are retained server-side under `audit_evidence_ref` for audit/logging. `result_mode: full` is the default and preserves the previous evidence-packet response; legacy `answers: [variable]` remains supported.

## Deliberate non-decisions

This does not add a capability-security/profile system and does not expose raw Cypher in the one-off surface. Those are separate product decisions. The bounded program remains the graph-native escape hatch for a novel relational task.

## Frozen-view experiment mode

Every graph-treatment case must use automatic minimal-contract mode:

- no `graph.md`, workbook traversal document, or named traversal;
- no `orient`, `search`, or raw Cypher;
- exposed graph calls: `describe`, `lookup`, `expand`, `path`, and
  `run_ephemeral_traversal`.

`compact` remains an available result mode rather than an instruction to the
participant. The SQL arm may likewise compute server-side and return a small
projection. The experiment measures the represented interaction surface,
including whether the participant composes a program and chooses compact
output; it does not prescribe either strategy.
