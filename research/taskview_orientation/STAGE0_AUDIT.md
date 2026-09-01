# TaskView orientation experiment — final Stage 0 audit

**Status:** frozen and ready for final authorization review

**Participant models run:** none

**Experimental comparison:** RAW / NATIVE versus PRECONSTRUCTED TASKVIEW

## 1. Exact final five-phase prompts

The machine-readable authority is `frozen/prompts.json`.

### Phase 1

> We are migrating jsonlib v2 to v3. Identify the in-scope production service or
> services that require a direct integration edit. For each, cite the local
> implementation, state the two decoding invariants that must be preserved, and
> give the v3 call shape that preserves them.

### Phase 2

> Review the affected production service that does not require a direct
> integration edit. Determine which service it is and why it does not require
> one. Cite the relevant adapter and local call site, explain the
> canonical-key-order and decimal-serialization behavior that makes that decision
> valid, and identify the existing verification assertion.

### Phase 3

> Review the remaining boundary/exclusion and unresolved consumer in the
> migration scope. Recover their identities from the available evidence. For
> each, state its current task status and cite the evidence. Then name the
> boundary wire field that must remain byte-stable and the dynamic registry lookup
> mechanism that prevents the consumer mapping from being closed.

### Phase 4

> A new revision of the checkout verification file has landed. Inspect the
> changed bytes, update any retained task state you rely on, and report which
> prior verification conclusion is no longer justified and which downstream
> result must be reconsidered. Do not propose the replacement test yet.

### Phase 5

> Follow this temporal order exactly. (1) Report the current verification-gap set
> before introducing any hypothetical replacement verification assertion. (2)
> Inspect the checkout implementation and nearby test conventions and specify the
> minimal replacement verification assertion or assertions needed. (3) Do not
> insert the proposed replacement into retained TaskView state during this phase.
> (4) State whether there are any other gaps in the current affected_service
> universe, name the universe supporting that conclusion, and separately state
> whether whole-world migration completeness is justified.

The harness additionally rejects a Phase 5 `ASSERT verified_by` mutation. The
proposed repair is answer-only.

## 2. Source tree and hashes

The participant-readable world contains 34 UTF-8 files and 8,646 bytes.

| Top-level category | Files |
| --- | ---: |
| architecture | 2 |
| config | 1 |
| deploy | 3 |
| docs | 1 |
| inventory | 2 |
| lockfiles | 3 |
| runtime | 3 |
| services | 12 |
| tasks | 1 |
| tests | 4 |
| vendor | 1 |
| root project metadata | 1 |

```text
initial source tree SHA-256
3adaa9dfdead7b37a79b805d40af2875fda7d9e0961b986d4f32cac8ae312f9e

Phase 4 checkout replacement SHA-256
1bab4e90c5e7ee7cde1d243ee9f406c873dc4f47e5244770fea99eca7f7a485d
```

The complete per-file byte, line, and hash inventory is
`frozen/source_manifest.json`. The distractors are staging services, standard
library JSON users, a service already using v3 with different semantics, and
nearby release/architecture material. They are plausible near-misses rather than
padding. No participant-visible file lists all TaskView conclusions.

## 3. Frozen TaskView

### Referents

Two libraries, three migration components, four services, one accepted adapter,
and two contract tests.

### Base relations and tuples

| Relation | Initial tuples |
| --- | --- |
| `component` | checkout-json; reporting-json; partner-json |
| `depends_on` | each component → jsonlib-v2 |
| `implements` | checkout→checkout-json; reporting→reporting-json; partner-gateway→partner-json |
| `production_service` | checkout; reporting; partner-gateway |
| `in_scope` | checkout; reporting |
| `boundary` | partner-gateway |
| `excluded` | partner-gateway, vendor-owned supported-v2 basis |
| `unresolved_scope` | external-worker |
| `protected_by` | reporting→reporting-json-v3 adapter |
| `compatible_via` | reporting, v2, v3, reporting adapter |
| `verified_by` | checkout→checkout contract; reporting→reporting contract |

### Derived relations

| Relation | Initial materialized rows | Completeness |
| --- | --- | --- |
| `legacy_component` | all three migration components | COMPLETE over `component` |
| `affected_service` | checkout; reporting | COMPLETE over `production_service` |
| `requires_change` | checkout | COMPLETE over `affected_service` |
| `verification_gap` | empty | COMPLETE over `affected_service` |
| `boundary_affected_service` | empty | UNKNOWN over `boundary` |

The SQL and declared inputs are frozen in `fixture.py`; their hash is
`7cede224db7f39bb7e8e310ddc566af0764a6485aabf855cfd1a37acfe5a17b3`.

```text
TaskView database SHA-256
68cba47f20bf706ebf11975c53924578bf2310050ea623e4d1fd7f43df2d1830

semantic snapshot SHA-256
1436e74fad2741b7587d2579a70ec30e6142deff126917049187dba42665f0e0

fixture revision
33
```

The database hash shown above was the audit-time value at document creation; the
machine-readable manifest is authoritative if an explicit pre-execution refreeze
changes SQLite receipt UUIDs while preserving the semantic snapshot hash.

## 4. Grounding and RAW parity

The ledger contains 21 base assertions:

- 12 copied generic source facts;
- 2 deterministic task-conditioned compositions;
- 7 reviewed task-conditioned judgments;
- 21/21 marked RAW-obtainable.

Every evidence item contains a participant-visible path, exact inclusive line
span, and source SHA-256. Ledger SHA-256:

```text
ae2b39b6f4897fd9c3813aaf1e5a7fc89a54bb9b1c1dec9867e079fbfba878cf
```

Two independent review methods pass with no disagreement:

1. ledger-first resolution of every path, span, hash, construction category, and
   RAW-obtainable declaration;
2. source-first reconstruction of all 21 tuples without reading ledger tuples,
   followed by exact comparison.

The second pass separately records why `protected_by`, `excluded`,
`unresolved_scope`, `verified_by`, `compatible_via`, and `in_scope` are reasonable
interpretations. All derived outputs reproduce exactly. The machine-readable
receipt is `frozen/parity_review.json`.

## 5. TaskView-only leakage audit

The source-blind reviewer input contains `describe`, semantic relation rows, and
grounding references, but no source contents. It deliberately reveals:

```text
checkout requires change
reporting is protected
partner-gateway is excluded and a boundary
external-worker is unresolved
initial verification_gap is empty and scoped COMPLETE
```

It does not reveal the decoder call, comment/Decimal implementation, canonical
translation, exact report output, signed wire field, wildcard lookup mechanism,
or replacement test assertions. None of the frozen forbidden local tokens occurs
in the reviewer input. Result: PASS. See `frozen/leakage_audit.json`.

## 6. Completeness wrapper

The participant-visible operation is exactly:

```text
rerun("verification_gap")
```

It selects the fixture-owned contract:

```text
COMPLETE over affected_service
basis = every affected service checked against current task-relevant verification
known_gaps = none
```

It rejects participant-supplied `status`, `universe`, `basis`, or `known_gaps`,
rejects any relation without a participant-visible frozen contract, and rejects
COMPLETE when the derived universe is stale or not complete. Existing TaskView
staleness, derivation, receipt, and internal-table guards remain unchanged.

## 7. Stateful runner

`EpisodeRunner` constructs one provider session object and calls that same object
for five turns. The session ID must remain stable. Each answer is validated and
written before the next phase is released. There is no transcript prepending,
reset, summary injection, or memory wipe.

The Phase 4 replacement occurs once, after Phase 3 answer commit and before the
Phase 4 prompt. RAW and TASKVIEW receive identical bytes and notification.
TaskView state is not repaired by the runner; the treatment participant must
retract the obsolete `verified_by` tuple.

Both arms receive identical instrumented source search/read and scratch tools.
TASKVIEW alone receives the four frozen operation categories. A model-specific
adapter must implement the `StatefulParticipantSession` protocol and maintain a
real provider conversation; no such provider was invoked in Stage 0.

## 8. Telemetry

Raw JSONL records preserve:

```text
episode, arm, replicate, phase, turn, sequence, timestamp
tool name and arguments
search query and scope
source path, line range, per-line bytes and source version
model-visible input/output bytes
provider tokens when supplied
tool and participant-turn wall time
TaskView operation, returned rows and visible bytes
structured answer and citations
Phase 4 mutation boundary and hashes
```

Aggregation recomputes total visible bytes, tool calls by type, searches, reads,
unique/repeated files, TaskView operation counts, `O_post`, net orientation bytes,
focus ratio, time/bytes before the first local file read, irrelevant files,
repeated broad searches, repeated orientation reads, and R1–R4 reconstruction
events. Raw events—not summaries—are the retained authority.

## 9. Frozen source-span classification

`frozen/span_classification.json` fixes per-phase line spans as:

```text
LOCAL_ORACLE
ORIENTATION_SUPPORT
IRRELEVANT (default)
```

Search is BROAD when rooted at the repository, outside the phase's local
directories, or cross-service after a target is known. Mixed results allocate
model-visible bytes proportionally to the frozen labels of their returned source
lines.

Primary labels are immutable after execution begins. An adjudicated alternative
witness may affect correctness as `ALTERNATIVE_VALID_LOCAL`, but never primary
metrics; it is included only in a separately reported sensitivity analysis.

The four reconstruction events remain:

- R1: checkout is the only direct-change service;
- R2: reporting is protected by the accepted adapter;
- R3: partner-gateway is excluded at the v2 boundary;
- R4: external-worker remains unresolved.

Each has frozen support spans, first-establishment phase, reuse phases, and an
observable reopening/search rule.

## 10. Oracle and answers

Every phase has an exact answer-field schema. Coarse task state, local semantics,
verification/change, completeness, and citations are scored independently. Phase
5 has distinct fields:

```text
current_verification_gap
proposed_replacement_verification
other_gaps_in_affected_service
completeness_universe
whole_world_complete
whole_world_blockers
```

Exact automatic scoring is preserved alongside arm-blinded adjudication for
semantically equivalent prose or valid alternative citations. Alternative
citations never alter primary source labels. Oracle SHA-256:

```text
f5fa3f5c8f9730ca99bb31604a6b62a1a1b0e6190c8c023fc49baa39a40dd9d6
```

## 11. Deterministic apparatus results

Focused tests:

```text
44 passed
```

This includes all 24 existing TaskView tests and 20 Stage 0 apparatus tests.
Checks cover hashes, ledger spans, two parity paths, semantic reproduction,
initial and stale completeness, contract-bound rerun, completeness injection,
Phase 5 mutation rejection, leakage, prompt localization, frozen classification,
internal-table isolation, native-tool parity, five-turn statefulness, the exact
mutation boundary, raw telemetry, treatment-byte charging, manifest hashes, and
both-arm scripted lifecycle probes.

The scripted dry run invoked no participant model. Both arms completed one
five-turn session, received byte-identical source trees, applied one mutation,
and produced fully correct fixture-derived answers. Its metric values are useful
only as a deterministic telemetry example, not experimental evidence:

| Scripted arm | `O_post` | Net orientation bytes | Focus ratio | Total visible bytes | TaskView-visible bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| RAW | 5,887 | 5,887 | 0.290 | 20,032 | 0 |
| TASKVIEW | 500 | 1,481 | 0.869 | 16,603 | 6,452 |

Receipt: `frozen/dry_run_receipt.json`.

## 12. Manifest

The authoritative machine-readable manifest is
`frozen/experiment_manifest.json`.

```text
experiment version: taskview-orientation-v1
git commit: f09857064979227cd8e0bb7fa23c57dab495e36d
working-tree apparatus identifier:
a3206e6b3ff64d86bbfa356d009b6b3245122a92c220979a4c2fc8a0bf1380ee
episodes: 8
replicates per arm: 4
turns per episode: 5
retry policy: none
```

The manifest includes all frozen input hashes, apparatus-code hashes, TaskView
runtime hashes, prompts, tool schemas, oracle, classifier, ledger, reviews,
database, dry-run receipt, budgets, sampling settings, and blocked arm order.

## 13. Discrepancies from the original design

Three intentional corrections were applied before freeze:

1. Phase 2 no longer names reporting; Phase 3 no longer names partner-gateway or
   external-worker.
2. Phase 5 reports the pre-repair gap before proposing an answer-only repair, and
   the harness rejects that repair as a retained-state mutation.
3. Primary span labels can no longer be amended from trajectories; alternatives
   are correctness adjudications plus sensitivity analysis only.

The source world contains 34 files, within the designed 25–35 range. The runner
uses a small controlled native source-tool surface rather than a general shell so
source writes, reads, and returned bytes are fully observable. Both arms receive
the same surface.

## 14. Final audit questions

### A. TaskView rather than Graphify?

Yes. Nine base assertions are task-conditioned. The decisive state is
`in_scope`, `protected_by`, `compatible_via`, `excluded`, `boundary`,
`unresolved_scope`, and `verified_by`, with `affected_service`,
`requires_change`, and `verification_gap` derived from it. Generic dependency
edges alone include the excluded partner and cannot decide protection or
verification relevance.

### B. Local source reasoning still required?

Yes. The leakage audit cannot recover any of the eight scored implementation
details. Every phase requires at least one frozen local source span.

### C. Prompts leave orientation work?

Yes. Phase 2 supplies a task role, not reporting's identity. Phase 3 supplies two
task roles, not either identity. Phase 4 names only the newly changed evidence;
the participant must recover its prior semantic relationship. Phase 5 names
checkout only after that change but does not provide the current gap or scope
conclusion.

### D. RAW parity defensible?

Yes. The 21-record ledger resolves entirely into the 34-file source world and is
reconstructed independently with no missing or extra tuple.

### E. Completeness exposes unavailable knowledge?

No. `affected_service` is complete only over the explicit pinned production
universe that RAW can enumerate and compose from visible files. The partner
boundary remains UNKNOWN and external-worker remains explicitly unresolved.

### F. Prompt/state ambiguity exploitable?

No known ambiguity remains. Phase 5's current gap precedes hypothetical repair,
and the harness rejects the prohibited mutation.

### G. Broad versus local measurement works?

Yes. The dry-run JSONL includes mixed root searches, orientation reads, local
reads, TaskView calls, and changed-source versioning. Reaggregation produces the
table above and frozen R-events without reading pre-aggregated metrics.

### H. Mixed-result interpretation

- **Large `O_post` reduction + net reduction:** primary mechanism and immediate
  prebuilt-view economics supported; continue to replication.
- **Large `O_post` reduction + net increase:** orientation suppression supported,
  but the frozen interface costs more than it saves; do not claim net efficiency.
- **Small `O_post` reduction + correctness improvement:** primary mechanism does
  not pass; retain a narrower scope/correctness hypothesis only after review.
- **Orientation reduction + worse local reasoning:** fail the guardrail; treat as
  anchoring or premature-localization harm and do not replicate unchanged.
- **TaskView largely ignored:** this frozen surface failed to deliver the
  mechanism; at most one preregistered discoverability-only revision is warranted.
- **RAW retains orientation cheaply:** TaskView loses for this single-context case;
  do not reinterpret that as an apparatus failure.

## 15. Unresolved execution binding

The final reviewer must select the exact participant model/provider version and
bind a genuine stateful provider adapter, then refreeze only those manifest
fields and resulting manifest hash. The case, prompts, sources, TaskView,
classifier, oracle, budgets, and arm order must not change. This is the expected
authorization-time binding, not a parity or leakage blocker.

The manifest deliberately says `participant_execution_authorized: false` until
that review occurs.

## Recommendation

```text
AUTHORIZE 8-EPISODE PILOT
```

Recommendation is contingent only on the final reviewer filling and freezing the
exact model/version and confirming the adapter maintains one real provider
session. No participant should run from the current placeholder manifest.
