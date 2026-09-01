# TaskView Compiled Decision-Projection Experiment

Preregistered protocol. Frozen before any participant inference.

Campaign id: `taskview-orientation-compiled-projection-v1`

Participant: Cursor CLI, model `composer-2.5` (not `composer-2.5-fast`), adapter
`taskview-cursor-cli-v1`, pinned `cursor-agent` version from
`research.taskview_orientation.runtime`. One chat resumed across five turns.
No injected summaries, no within-episode retries.

This is a cheap falsification of the compiled-granularity hypothesis. It is
not a TaskView product revision, not a bounded-reliance retest, and not a
grounding-freshness experiment.

Live inference is refused until deterministic preflight passes **and** a
separate authorized manifest sets participant execution on. Default:
`PARTICIPANT_INFERENCE_AUTHORIZED = False`.

## Research question

Whether compiling atomic task relations into a deterministic decision-level
projection substantially reduces model-side semantic reassembly without
reducing necessary local source inspection.

## Conditions

Two conditions, shared frozen TaskView fixture, T10-style contract, identical
tools after delivery.

- **ATOMIC** — T10-style TaskView. At session start the coarse state is
  delivered as named-relation tuples. Ordinary query/describe/assertion/rerun
  remain available.
- **COMPILED** — identical except the same coarse state is delivered as a
  deterministic `migration_surface` projection. Ordinary atomic tools remain
  available. Voluntary reopening is the measured behavior.

No RAW. No T00/T01/T11. No additional replicates after seeing results.

## Design

Three matched blocks. Condition order within block is the frozen shuffle
`random.Random(20260902 + 1000 * block).shuffle(["ATOMIC", "COMPILED"])`.
6 episodes, 30 phase turns.

## Information parity

Every compiled field maps to existing TaskView tuples or existing completeness
metadata. No LLM summaries. No new semantic judgments. Canonical database
unchanged.

## Primary metric

Reconstruction / reassembly after the initial delivery. Frozen in
`frozen/reassembly.json`. No model classification.

## Continuation rule

SUPPORTED FOR CONTINUATION only if COMPILED has lower reassembly bytes in 3/3
blocks, median matched reduction ≥ 50%, lower acquisition-inclusive bytes in
at least 2/3, and the frozen safety/preservation checks pass.

Otherwise: COMPILED-GRANULARITY HYPOTHESIS NOT SUPPORTED.

Do not call 1/3 or 2/3 directional movement promising. Do not add another live
experiment to rescue a failure.
