# TaskView BOM scaling and bounded-frontier preflight

## Status and boundary

Experiment ID: `taskview-bom-scaling-v1`

Scientific baseline: `taskview-bom-c0-v1`

Frozen seed: `20260901`

This is research infrastructure, not a TaskView or Graphauthor product path.
It does not change TaskView relations, derivations, storage, or invalidation.
It performs no provider/model inference.

```text
SEMANTIC_FRONTIER_INFERENCE_AUTHORIZED = False
PROVIDER_INFERENCE_CALLS = 0
```

## Hypotheses

H1 asks whether selected semantic-frontier evidence remains bounded while this
controlled mechanically resolvable world family grows. H2 asks whether each of
the two frozen frontier tuples can be presented as one relation-specific,
closed-packet adjudication.

Neither hypothesis is defined to pass at S100. Proportional evidence selection,
new frontier tuples, collapsing mechanical coverage, broad serialization, or
pathological mechanical materialization are negative evidence.

## Frozen scales

`S1` is a byte copy of the original four sources, mutation, and C0 oracle.
`S10` and `S100` append deterministic cohorts generated from
`sha256(seed:index)`. Each cohort uses the same four authority classes and adds
12 parts, 12 listings, four BOM requirements, and two structured candidate
records. Cohort-specific mechanical part types prevent accidental cross-cohort
compatibility products.

S10 and S100 additionally contain four sensor-interface and four relay
near-neighbor candidates for the two original replaced parts. They share
voltage, temperature ranges, manufacturer families, supplier, and exact
`candidate_replacement` links. These are ordinary source records; they contain
no relevance, frontier, or oracle fields.

Only the original two positive `acceptable_replacement` tuples occur in C0.
Generated candidate links are MECHANICAL and do not create acceptance tuples.
S1's oracle answers and source evidence are unchanged.

## Independent C0 and C1

The scale generator freezes explicit C0 relation extensions. BASE extensions
come from the generation plan, while expected DERIVED extensions are calculated
with a pure-Python relation evaluator independent of TaskView SQL. C1 runs the
existing structural adapters and unchanged TaskView derivations independently
at each scale. Comparison is exact tuple-set comparison.

## Selector rule

The selector receives a proposed relation tuple, not an oracle disposition. It:

1. selects manufacturer observations for the tuple's two exact part referents;
2. selects BOM observations for its exact context referent;
3. selects the engineering-note record whose exact candidate pair matches;
4. selects mechanical relation tuples involving those referents and context;
5. includes only the exact `candidate_replacement(new_part, old_part)` tuple.

The implementation contains no literal frontier part IDs. It does not serialize
other candidates for the same replaced part. Candidate-population metrics are
computed separately to test recall and distractor inclusion.

## Frontier-size definitions

Structural frontier sparsity:

```text
frontier_record_ratio
= unique selected source records across both assertions
  / total source records
```

Acquisition frontier ratio:

```text
frontier_packet_ratio
= deduplicated two-assertion campaign model-visible bytes
  / total raw source bytes
```

The campaign byte count includes the two canonical packet payloads and one copy
of `protocol.json`, `packet_schema.json`, and `output_schema.json`. The packets
share no selected record, so only the stable protocol/schema is deduplicated.
Per-assertion model-visible bytes count the fixed protocol/schema separately for
each hypothetical isolated adjudication.

Packet payload bytes are partitioned into:

- raw selected record text;
- normalized mechanical context;
- grounding/provenance metadata;
- JSON envelope/escaping overhead.

Protocol/schema bytes are counted separately and once in campaign acquisition.
The sum is reported as total serialized frontier packet bytes. Runtime is not
recorded because it would make the generated report nondeterministic; relation
output cardinality and recomputation amplification expose scaling work.

## Mutation

Every scale carries the original X100 maximum-temperature mutation, 80 C to
60 C. The expected semantic delta remains removal of X100/BOM-A from
`temperature_compatible` and `eligible_part`. TaskView relation-granular
invalidation is measured but not changed.

## C2 protocol

C2 adjudicates exactly one supplied
`acceptable_replacement(candidate, replaced_part, context)` assertion. Allowed
decisions are `ACCEPT`, `REJECT`, and `UNRESOLVED`. Grounds must resolve to a
source/location pair in the supplied packet. The reason is explanatory and the
decision is scored.

C2 cannot add entities or relations, search outside the packet, alter semantic
state, rewrite schemas or derivations, or make procurement recommendations.
The hidden two-cell oracle is derived once from positive membership in the
already-frozen C0 extension. C0 absence is not assigned a disposition.

`run_c2` checks `SEMANTIC_FRONTIER_INFERENCE_AUTHORIZED` before calling its
injected provider and fails closed while the flag is false.

## Stop condition

Stop after deterministic scale generation, C1 comparison, selector stress,
mutation measurements, scaling seal, packet/schema/oracle freeze, and C2
preflight. No inference follows from preflight success.
