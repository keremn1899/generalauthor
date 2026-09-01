# TaskView Bounded-Reliance and Grounding-Freshness Experiment

Preregistered protocol. Frozen before any participant inference.

Campaign id: `taskview-orientation-bounded-reliance-v1`

Participant: Cursor CLI, model `composer-2.5` (not `composer-2.5-fast`), adapter
`taskview-cursor-cli-v1`, pinned `cursor-agent` version from
`research.taskview_orientation.runtime`. One chat resumed across five turns.
Context-retention policy matches the CLI adapter: no injected summaries, no
within-episode retries.

This is a mechanism experiment, not a TaskView product revision and not a
relabel of the historical economics failure.

Live inference is refused until deterministic preflight passes **and** a
separate authorized manifest sets participant execution on. Default:
`PARTICIPANT_INFERENCE_AUTHORIZED = False`.

## Research question

Whether TaskView's excess consumption is partly caused by agents being unable
to tell when coarse task-conditioned semantic state is safe to reuse, and
whether grounding-freshness information can make such reuse safe under world
changes.

The experiment does not force participants to use TaskView, trust TaskView,
avoid repository inspection, or minimize tool calls. All ordinary source and
TaskView operations remain available. `describe` remains available in every
TaskView condition.

## Hypotheses

- **H1** Bounded-reliance legibility: stating the bounded scope of CURRENT /
  COMPLETE-over-U reduces reconstruction-after-entitlement, targeted semantic
  reassurance, and broad repository re-proof, without reducing required local
  inspection or semantic correctness.
- **H2** Grounding freshness: FRESH grounding is commonly reused; CHANGED
  grounding causes selective reassessment of the affected proposition only.
- **H3** Interaction: T11 produces the largest reduction in unnecessary
  re-proof with preserved mutation sensitivity.
- **H4** Authority-without-freshness hazard: T10 may over-rely on internally
  CURRENT TaskView state after source evidence has changed. If observed, that
  result is reported, not concealed.
- **H5** Trust-hypothesis falsifier: if T11 does not materially reduce
  re-proof/reassurance, uncertainty about TaskView authority is not a major
  cause of excess consumption. Do not reinterpret that as success.

## Shared apparatus

All TaskView arms use the same frozen relations, rows, derivations,
completeness contracts, SQLite database, SQL interface, source tools,
assertion/rerun interface, five phase prompts, phase-4 checkout-contract
mutation, and schema-versioned vocabulary. The v0.1 frozen inputs are reused
and not rewritten.

Condition **R** is RAW: no TaskView, matched repository-orientation control.

## Experimental fields

- **T00** Stable vocabulary + SQL. Existing currentness/derivation/completeness
  remain available. No reliance contract. No grounding-freshness fields.
- **T10** T00 plus the frozen reliance section. CURRENT means consistent with
  current retained TaskView semantic inputs. COMPLETE over U licenses controlled
  negative inference only inside U. These guarantees concern coarse TaskView
  semantic state. They do not establish local implementation behavior. This arm
  does not claim freshness of external grounding. Participants are not told to
  avoid verification or repository reads.
- **T01** T00 plus mechanically computed `grounding_state` in `{FRESH, CHANGED,
  UNKNOWN}` on `describe(why)` and `assertion` returns that already carry
  source grounding. SQL row payloads are unchanged. Mutation may change
  grounding metadata; it does not add, retract, or reinterpret a semantic
  assertion. No reliance advice beyond the factual definition.
- **T11** T10 + T01. Bounded reuse of a coarse commitment is justified only to
  the extent that, when applicable: internal state is CURRENT, the required
  completeness receipt is valid, and relevant grounding is FRESH. Permission,
  not an instruction.

## Grounding invalidation

Deterministic source-content receipts on each grounded base-assertion evidence
record: source reference, content digest at grounding time, current source
digest, grounding state. File-level SHA-256 compared to the digest encoded in
the `source://path#Lstart-Lend@sha256:digest` reference.

The phase-4 replacement of `tests/checkout_contract.py` changes that file's
digest and may produce `CHANGED` for affected assertions. It must not
automatically RETRACT `verified_by` or rerun `verification_gap`. A grounding
change is evidence that a prior judgment should be reassessed, not evidence
about what the new judgment should be.

## Reconstruction-after-entitlement

Frozen in `frozen/entitlement.json` before live inference. No model
classification after seeing results.

`t_entitled` is the earliest successful `query_sql` whose addressed relation
(FROM/JOIN identifiers) includes an entitling relation for that phase.
`describe` never entitles. RAW has no `t_entitled`.

After that point, count as reproof:

- TaskView reads of entitling or ancestor relations
- catalog `describe`
- repeated targeted `describe` / `describe(why)` of those relations
- `SOURCE_READ` of `repository_reproof_files`
- repository-root `SOURCE_SEARCH`

Never count `required_local_files` reads. In phase 4, `verified_by` and
`verification_gap` are reassessment relations, not reproof.

Report per phase and episode: reproof calls, bytes, distinct relations,
repository files.

## Phase-4 hard falsifiers (mechanical)

A TaskView condition fails the safety mechanism if the participant:

1. After a CHANGED-bearing `describe(why)` of checkout `verified_by`, still
   treats that verification as currently justified (phase-4 answer does not
   invalidate it).
2. Does not `read_source` `tests/checkout_contract.py` in phase 4.
3. Uses a stale/invalid completeness receipt to claim known absence
   (`whole_world_complete` is true, or claims an empty current gap while
   `verification_gap` is STALE and unrestored).
4. RETRACTs checkout `verified_by` after seeing CHANGED without reading the
   changed checkout source between that receipt and the RETRACT.
5. ASSERT/RETRACT of an unrelated tuple in phase 4 (anything other than
   checkout `verified_by`) with no corresponding source change.

T10 may fail (1) without ever seeing CHANGED; that is the H4 detector:
no phase-4 inspection of the changed file, no RETRACT, and the answer still
treats checkout verification as justified.

## Interpretation and permitted claims

See the user protocol. Do not claim improved local cognition. Do not call a
reduction in source reading beneficial unless it occurs outside the frozen
required-local-evidence set. Do not call T11 successful merely because it uses
fewer tokens. Net economics is reported and is not the primary success
criterion.

## Design

Four matched blocks. Condition order within each block is the frozen shuffle
`random.Random(20260901 + 1000 * block).shuffle(list(CONDITIONS))`.
20 episodes, 100 phase turns. Do not adapt arms after observing partial
results.
