# Semantic-integration layers

This is a research constructor stack. The product kernel (TaskView) is unchanged.

## 1. Foundational (hard to change)

`taskview/` — Referent, named typed n-ary Relation, Derivation, grounding, open-world UNRESOLVED, World vs purpose lifetime.

No constructor prompt, adjudication strategy, semantic-family hint, or diligence-only rule belongs here.

A kernel change needs a correctness counterexample. Constructor v3 has none. Current iffy bits after the NPDES / E2E programmability campaign — including this kernel bar — are recorded in [`reports/open_weaknesses.md`](reports/open_weaknesses.md).

## 2. Semantic contracts (expected to evolve)

Machine-readable ABI: `RelationContract` (roles with optional `semantic_identity`), `PurposeProjectionContract` (`field_sources` to consumer fields), derivation/projection contracts.

Constructors may name tables and roles freely. Consumer programs depend on **consumer field identity**, not constructor relation names.

## 3. Replaceable compiler passes

```
P0 intention → P1 vocabulary/contracts → P2 mechanical
→ P3 frontier → P4 packets → P5 adjudicate → P6 admit
→ normalize → P7 derive → P8 project
```

P8 is deterministic. Normalization is deterministic given contracts.

P6 World commit is validated by `validate_provenance()`: every durable assertion must have SOURCE, WORLD, ASSERTION, or DERIVATION grounding.

Required consumer identities are checked by ABI completeness (`SATISFIED` / `UNSATISFIED` / `AMBIGUOUS`) before projection. `SATISFIED` is a realizability guarantee, not merely a declaration guarantee: for required consumer field/relation \(f\), \(SATISFIED(f) \Rightarrow f \in \text{Normalize}(W)\). ABI completeness and normalization share the same materialization semantics. Declared bindings that cannot be materialized from World produce `UNSATISFIED: NOT_MATERIALIZABLE` and yield `INCOMPLETE_PURPOSE` before projection. Missing bindings fail locally; they are not fuzzy-repaired.

Default P5 is a bounded single adjudicator. A DISTINCT-only negative-closure gate may downgrade DISTINCT to UNRESOLVED. It must not change SAME or upgrade UNRESOLVED.

## 4. Experimental (not a core dependency)

Cue-list verifier, critic, entailment, proof-obligation gates, pairwise/multistep proof, semantic-family hints, Probe A/B strategy code.

Sealed under `semantic_proof_benchmark_v1/` and `schema_normalization_v1/`. Default Constructor v3 must not import them.

## 5. Allowed dependency direction

Experimental strategies may depend on contracts and TaskView.

Foundational semantics must never depend on an experimental strategy.

Default v3 runtime may depend on A/B/C contracts and TaskView. It must not depend on Probe A strategies or the v2 cue verifier.
