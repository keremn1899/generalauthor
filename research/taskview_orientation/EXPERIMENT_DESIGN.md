# TaskView orientation-reuse experiment

**Status:** design for review; participant execution is not authorized

**Primary comparison:** RAW / NATIVE versus preconstructed TaskView v0

**Construction economics:** deliberately out of scope

## Decision

Run one dependency-migration case first, based on the existing
`jsonlib-v3-migration` TaskView fixture. Do not add a Graphify arm to the first
paid pilot.

The existing fixture is the strongest starting point because it already contains
the task-born distinctions the mechanism needs: `in_scope`, `boundary`,
`excluded`, `unresolved_scope`, `protected_by`, `compatible_via`,
`affected_service`, `requires_change`, and `verification_gap`. It also already
exercises invalidation and scoped exhaustive results.

It is not executable as a causal experiment yet. Its groundings are illustrative
URIs, and its module explicitly says it does not claim to extract its assertions
from sources. Before any participant run, Stage 0 must create the participant-
readable source snapshot described below and replace every illustrative grounding
with a path, line span, and source hash in that snapshot.

The older abstraction-frontier worlds are not the primary case. They are useful
structured-retrieval fixtures, but their task is answered from canonical generic
facts and they do not provide the implementation-local source regions required
here. The current Graphauthor repository itself is also not the first world: it
is mutable, historically dense, and would make case correctness and parity much
more expensive to audit. It is a plausible later legacy-removal replication.

## A. Exact falsifiable hypothesis

### Primary hypothesis: repeated orientation cost

Let `O_post` be model-visible bytes from repository searches and source reads in
Phases 2–5 classified before execution as `ORIENTATION_SUPPORT` or `IRRELEVANT`.
It excludes phase-local oracle spans and includes repeated reads.

For four matched RAW/TASKVIEW pairs on the frozen episode:

1. the median paired reduction in `O_post` for TASKVIEW will be at least 30%;
2. TASKVIEW will have lower `O_post` in at least three of four pairs; and
3. TASKVIEW will not reduce implementation-local correctness, and will inspect
   at least one phase-local oracle source in at least 80% of the phases that
   require local reasoning.

This is a mechanism threshold for a tiny pilot, not an effect-size estimate or a
significance test. Failure to meet it is evidence against the first mechanism as
instantiated by this surface and case.

### Secondary hypotheses

- **Earlier focus:** TASKVIEW reduces bytes/tokens and wall time before the first
  phase-local oracle source read in Phases 2–5.
- **Less reconstruction:** TASKVIEW causes fewer later re-reads of evidence used
  to establish protectedness, exclusion, affectedness, and unresolved scope.
- **Better scope control:** TASKVIEW makes fewer inclusion, exclusion, and
  scoped-versus-global completeness errors.
- **Useful invalidation:** after changed evidence, TASKVIEW is more likely to
  withdraw the invalid verification judgment and use a current rerun before
  making an exhaustive claim.

Total tokens are secondary. The mechanism may still be supported if total cost
is similar but broad exploration falls, local effort is preserved, and
correctness improves.

## B. Candidate task

### Primary: `jsonlib` v2 to v3 dependency migration

The frozen world contains 25–35 small files across inventory, lockfiles,
deployment metadata, task scope, architecture, runtime inventory, three service
implementations, tests, and unrelated sibling services. The exact count and all
bytes are frozen before Stage 1. No generated file or hidden oracle is visible to
either arm.

Why it creates orientation burden:

- dependency evidence, deployment membership, service/component realization,
  scope, boundary ownership, adapter compatibility, and verification live in
  different files;
- three services mention the legacy library, but only one needs a direct change;
- one service is protected, one is excluded at a vendor boundary, and one
  dynamic consumer remains unresolved;
- later phases return to those distinctions while requiring fresh inspection of
  different local implementations.

| Task-conditioned state | Exploration originally required | Later reuse | Why generic structure is insufficient | Local reasoning still required |
| --- | --- | --- | --- | --- |
| `affected_service(checkout)`, `affected_service(reporting)` | compose lockfiles, service/component map, production inventory, task scope, and exclusions | selects local targets in Phases 1, 2, 4, and 5 | `depends_on` and `implements` also lead to the excluded partner bridge and say nothing about task scope | exact v3 call shape and behavior-preservation details |
| `requires_change(checkout)` | compare affected services with accepted adapter protection and exclusions | prevents re-triaging all services in Phases 1 and 5 | a structural index cannot decide whether an adapter is accepted for this migration | comments and decimal-number behavior in checkout's decoder |
| `protected_by(reporting, reporting-v3-adapter)` | inspect the adapter, migration contract, and reporting verification | directs Phase 2 to the adapter and reporting call site | the existence of an adapter does not imply accepted task compatibility | canonical ordering, decimal serialization, and the covered edge case |
| `excluded(partner-gateway, vendor-owned-v2-boundary)` and `boundary(partner-gateway)` | combine task charter with boundary contract and ownership evidence | avoids reconsidering partner as a direct edit while still locating its local contract in Phase 3 | topology cannot decide that a connected component is intentionally outside the change surface | identify the exact byte-stable wire field |
| `unresolved_scope(external-worker)` | inspect the dynamic consumer registry and its incomplete lookup | prevents an invalid global-completion claim in Phases 3 and 5 | missing topology is ambiguous; it does not express a known unresolved mapping | identify the dynamic lookup mechanism and what evidence would close it |
| `verified_by(service, test)` and `verification_gap` | inspect task-relevant assertions in each suite, not just test-to-service naming | reused, invalidated in Phase 4, and recomputed in Phase 5 | a `test -> service` edge does not establish that the test verifies this migration behavior | determine whether the changed checkout test still covers the required semantics and design its replacement |

This case is TaskView-like rather than Graphify-like because the treatment's
useful advantage comes from accepted task judgments—what must change, what is
protected, what is excluded, and what remains unresolved—not from dependency
reachability alone.

### Reserved replication families, not part of Stage 1

- An API/schema migration in which a compatibility facade protects some callers
  while one serialized field remains locally incompatible.
- Removal of Graphauthor's legacy Pipeline-B compatibility path, after freezing a
  clean repository snapshot and independently auditing the correct removal and
  non-removal surfaces.

## C. Proposed sequential episode

### Frozen arms

```text
A — RAW / NATIVE
    read-only frozen source snapshot
    normal native search/read tools
    writable scratch area
    no TaskView database, tools, or treatment language

C — TASKVIEW
    byte-identical read-only source snapshot
    identical native search/read tools and writable scratch area
    preconstructed frozen TaskView
    describe, query_sql, assertion, and contract-bound rerun
```

The native tool schemas, system instructions, budgets, and source visibility are
otherwise identical. Count the additional TaskView tool descriptions in C's
model-visible input cost. RAW may write notes or construct an ordinary scratch
artifact if it independently chooses to; its construction and use are counted.
Neither arm may edit source files. The harness alone applies the frozen Phase 4
replacement between turns.

Both arms use a fresh context per episode and the same context across all five
phases. There is no context truncation, summarization, handoff, or artificial
memory reset. Each next phase is delivered only after the prior structured answer
is committed. This deliberately allows RAW to remember its work; cheap in-context
retention is a legitimate way for TaskView to lose.

Each answer must cite source paths and line spans for local conclusions. The
participant may use any supplied native repository tool. TASKVIEW also receives
the frozen four-operation surface.

### Phase 1 — triage plus first local decision

> We are migrating `jsonlib` v2 to v3. Identify the in-scope production service
> or services that require a direct integration edit. For each, cite the local
> implementation and state the two decoding invariants that must be preserved and
> the v3 call shape that preserves them.

Expected coarse orientation: checkout alone requires direct change. Required
local conclusion: the checkout decoder must preserve comment acceptance and
decimal-number semantics by using the fixture-defined v3 decoder configuration.

### Phase 2 — protected service, new local nuance

> Review the affected production service that does not require a direct
> integration edit. Determine which service it is and why it does not require
> one. Cite the relevant adapter and local call site, explain the
> canonical-key-order and decimal-serialization behavior that makes that decision
> valid, and identify the existing verification assertion.

Expected reuse: reporting is affected but protected. Required local conclusion:
the adapter's concrete encoding translations and the exact reporting test
assertion; these details are absent from TaskView.

### Phase 3 — exclusion and unresolved mapping

> Review the remaining boundary/exclusion and unresolved consumer in the
> migration scope. Recover their identities from the available evidence. For
> each, state its current task status and cite the evidence. Then name the
> boundary wire field that must remain byte-stable and the dynamic registry lookup
> mechanism that prevents the consumer mapping from being closed.

Expected reuse: partner is a boundary exclusion; external-worker is unresolved.
Required local conclusions: the exact wire field and runtime lookup mechanism.

### Phase 4 — changed evidence and invalidation

The harness replaces the checkout contract test with a frozen revision that
retains only a smoke case and removes the commented-decimal scenario. Both arms
receive the same changed file and notification:

> A new revision of the checkout verification file has landed. Inspect the
> changed bytes, update any retained task state you rely on, and report which
> prior verification conclusion is no longer justified and which downstream
> result must be reconsidered. Do not propose the replacement test yet.

Correct reaction: withdraw `verified_by(checkout, checkout-contract)`; in the
TASKVIEW arm this makes `verification_gap` stale. The phase is wrong if the
participant merely trusts the old view.

### Phase 5 — local repair plus scoped exhaustiveness

> Follow this temporal order exactly. (1) Report the current verification-gap set
> before introducing any hypothetical replacement verification assertion. (2)
> Inspect the checkout implementation and nearby test conventions and specify the
> minimal replacement verification assertion or assertions needed. (3) Do not
> insert the proposed replacement into retained TaskView state during this phase.
> (4) State whether there are any other gaps in the current `affected_service`
> universe, name the universe supporting that conclusion, and separately state
> whether whole-world migration completeness is justified.

Correct result: the gap set is exactly checkout; the replacement verifies both
comments and decimal-number preservation; there are no other gaps in the current
`affected_service` universe; global completion remains unjustified because the
external worker is unresolved and the partner boundary is not an exhaustive
model of its internals.

## D. Frozen treatment contents

### Initial referents

Two libraries; three JSON components; checkout, reporting, partner-gateway, and
external-worker services; the reporting v3 adapter; and checkout/reporting
contract tests. These are thin stable identities, not payload-bearing entities.

### Base relations and initial tuples

| Relation | Frozen tuples |
| --- | --- |
| `component(component)` | checkout-json; reporting-json; partner-json |
| `depends_on(component, dependency)` | each of the three components depends on jsonlib-v2 |
| `implements(service, component)` | checkout→checkout-json; reporting→reporting-json; partner-gateway→partner-json |
| `production_service(service)` | checkout; reporting; partner-gateway |
| `in_scope(subject)` | checkout; reporting |
| `boundary(subject)` | partner-gateway |
| `excluded(subject, basis)` | partner-gateway, because the vendor-owned boundary remains on the supported v2 protocol |
| `unresolved_scope(subject)` | external-worker |
| `protected_by(service, adapter)` | reporting→reporting-v3-adapter |
| `compatible_via(service, old_library, new_library, adapter)` | reporting, jsonlib-v2, jsonlib-v3, reporting-v3-adapter |
| `verified_by(service, test)` | checkout→checkout-contract; reporting→reporting-contract |

### Derived relations

| Relation | Frozen derivation contract | Initial rows |
| --- | --- | --- |
| `legacy_component` | component joined to dependency on jsonlib-v2 | all three JSON components |
| `affected_service` | in-scope production service implementing a legacy component, minus exclusions | checkout; reporting |
| `requires_change` | affected service minus accepted protections and exclusions | checkout |
| `verification_gap` | affected service with no `verified_by` tuple | empty |
| `boundary_affected_service` | affected service joined to boundary | empty |

The derivations are the current deterministic SQL derivations with frozen,
declared inputs. Participants do not author or edit them.

### Completeness declarations

| Target | Status | Universe | Frozen basis |
| --- | --- | --- | --- |
| `legacy_component` | COMPLETE | `component` | every component in the pinned build inventory was evaluated |
| `affected_service` | COMPLETE | `production_service` | pinned production inventory, realization map, scope, and exclusions were evaluated |
| `requires_change` | COMPLETE | `affected_service` | every affected service was checked for accepted protection and exclusion |
| `verification_gap` | COMPLETE | `affected_service` | every affected service was checked against current task-relevant verification assertions |
| `boundary_affected_service` | UNKNOWN | `boundary` | the partner boundary is represented but its internal consumers are opaque |

After Phase 4, `verification_gap` is stale until rerun. Its frozen contract still
permits `COMPLETE over affected_service`: the affected universe is unchanged and
the derivation evaluates every current member against the updated `verified_by`
relation. It does not permit a whole-world completeness claim.

### Grounding and construction ledger

Before Stage 1, every tuple receives one ledger record with:

```text
relation and tuple
source path plus exact line span
source SHA-256
semantic judgment represented
construction rule: copied / deterministic composition / reviewed task judgment
RAW-obtainable: yes, with explanation
reviewer and frozen review result
```

Required source mapping:

| Assertions | Participant-visible sources |
| --- | --- |
| components and dependencies | `inventory/components.toml`, three pinned lockfiles |
| implementations and production universe | `deploy/service-components.yaml`, `deploy/production-services.yaml` |
| scope and exclusion | `tasks/migrate-jsonlib-v3.md`, `architecture/partner-gateway.md` |
| unresolved worker | `runtime/dynamic-consumers.md` and its registry implementation |
| reporting protection and compatibility | reporting adapter/call site, v3 migration contract, reporting contract test |
| verification | checkout and reporting contract tests plus their local implementations |

Grounding returned by `describe(why=...)` names only participant-visible sources;
it must not expose hidden oracle prose.

### Smallest completeness harness change

Do not change the TaskView logical model. Put an experiment-only adapter in front
of the existing surface with a frozen map:

```text
verification_gap
→ COMPLETE over affected_service
→ frozen basis string
→ no known gaps
```

The participant-visible operation is only `rerun("verification_gap")`. The
adapter supplies the immutable contract to the existing `rerun` call and rejects
relations without a frozen contract. This removes the participant's present
ability to submit `status`, `universe`, `basis`, or `known_gaps` while reusing the
existing staleness and receipt implementation. It is experiment harness work,
not a fifth TaskView operation or a product redesign.

## E. RAW parity argument

RAW and TASKVIEW receive byte-identical initial source trees, native tool
descriptions, phase prompts, evidence changes, context policy, time limits, and
answer schemas. TASKVIEW additionally receives only precomputed judgments whose
ledger entries point into that same source tree.

Parity is accepted only if two reviewers can reconstruct every TaskView tuple
from the cited participant-visible evidence and agree that the tuple is a
reasonable task judgment. Any assertion requiring author knowledge outside the
snapshot is removed. Derived rows must reproduce from the frozen base tuples and
declared derivations. The Phase 4 file replacement is identical in both arms;
the TASKVIEW database is not silently repaired by the harness.

Construction effort is intentionally free to TASKVIEW in this experiment. That
is the controlled intervention, not a parity defect.

## F. Oracle

Scoring is field-level, not answer-text equality. Citations must resolve to the
frozen snapshot and support the claimed local fact.

| Phase | Coarse/task-state fields | Local-reasoning fields | Completeness/change fields |
| --- | --- | --- | --- |
| 1 | direct-change set is exactly checkout | comment acceptance; decimal preservation; correct fixture-defined v3 call; valid citations | none |
| 2 | reporting is affected but needs no direct edit because of the accepted adapter | canonical ordering; decimal serialization; exact verifying assertion; valid citations | none |
| 3 | partner excluded at boundary; external-worker unresolved | byte-stable partner field; dynamic lookup mechanism; valid citations | no global closure claim |
| 4 | checkout's prior verification relationship is withdrawn | changed test no longer exercises both migration invariants | identifies stale/reconsidered verification-gap result |
| 5 | gap set is exactly checkout | replacement test checks comments and decimal type/value; valid citations | no other gap over current `affected_service`; no whole-world completeness claim |

Report these aggregate dimensions separately:

```text
task scope
affected/change set
exclusions and unresolved mappings
local implementation semantics
verification surface
reaction to changed evidence
scoped exhaustive conclusion
```

Do not collapse them into one score until after the dimension-level comparison
is visible. A participant that gets scope from TaskView but guesses the local
details has not demonstrated the proposed mechanism.

## G. Telemetry

### Raw measurements

Capture per phase and per tool response:

```text
input/output model-visible bytes and provider-reported tokens
wall time
tool name and arguments
repository search calls and search scope
source read path, byte/line ranges, bytes returned
unique and repeated files/ranges read
TaskView describe/query_sql bytes and rows returned
assertion/rerun calls and results
final structured answer and citations
```

The runner must preserve one stateful participant session across the five turns.
The existing relational-materialization runner explicitly documents a one-shot
adapter, so it must not be reused while pretending that a prefix is sequential.

### Frozen source-interaction classification

Before participant execution, two reviewers label line spans—not merely whole
files—for each phase:

- `LOCAL_ORACLE`: needed to establish that phase's implementation-local answer;
- `ORIENTATION_SUPPORT`: evidence for reusable affectedness, protection, scope,
  exclusion, verification mapping, or unresolved state;
- `IRRELEVANT`: visible source outside both sets.

Mixed tool results are apportioned by returned bytes. A repository search is
also marked `BROAD` when its requested scope is outside the phase-local oracle
directory or uses the repository root. This prevents a lucky local search hit
from making a broad search look local.

The primary classification is immutable after participant execution begins. It
is defensible because it is frozen before runs and tied to an explicit oracle,
but it is not a direct measure of cognitive effort and can miss alternative valid
evidence. An unanticipated legitimate source path may count for correctness after
arm-blinded adjudication as `ALTERNATIVE_VALID_LOCAL`; it does not change primary
`O_post`, focus-ratio, irrelevant-read, or reconstruction metrics. A separately
reported sensitivity analysis may add accepted alternative witnesses and must
state whether any qualitative conclusion changes.

### Derived metrics

```text
O_post
    ORIENTATION_SUPPORT + IRRELEVANT repository bytes in Phases 2–5

net orientation bytes
    O_post + TaskView bytes returned in Phases 2–5

focus ratio
    LOCAL_ORACLE source bytes / all repository source bytes

time/bytes to first LOCAL_ORACLE read

irrelevant unique files
repeated broad searches
repeated orientation-source reads
previously established exclusions re-investigated
task-scope mistakes
```

Focus ratio is only interpreted alongside absolute local bytes and local
correctness. It is misleading if a participant reads almost nothing, guesses, or
receives a direct answer.

### Semantic reconstruction events

Freeze four reusable events and their support spans:

```text
R1 checkout is the only direct-change service
R2 reporting is protected by the accepted adapter
R3 partner-gateway is excluded at the v2 boundary
R4 external-worker remains unresolved
```

For Phases 2–5, count a reconstruction when a participant reopens/searches the
support spans for an already established event before reaching the phase-local
region. A trajectory-based proxy for reconstruction cost is the broad source
bytes from phase start to first local-oracle read, annotated with which R-events
were revisited. This is observable but not a claim about hidden reasoning.

## H. Confounds and expected ways TaskView can lose

| Threat or loss mode | Design response | Interpretation |
| --- | --- | --- |
| TaskView directly answers the task | every scored phase includes local facts absent from all relations; blind Stage 0 reviewers attempt answers from TaskView alone | if they can answer local fields, revise the case |
| treatment is generic Graphify | audit that the decisive treatment rows are protected, excluded, unresolved, requires-change, and verification judgments | remove the case if generic edges explain the advantage |
| RAW remembers everything in context | preserve the same untruncated context across phases | if RAW reuse is cheap, the mechanism legitimately loses |
| orientation overhead exceeds avoided exploration | include TaskView payload in net-orientation and total-visible-byte metrics | a database that is too expensive to inspect is a real failure |
| participant ignores TaskView | log discoverability and calls without forcing queries | first occurrence is surface evidence; do not reclassify it as compliance failure |
| stale abstraction anchors the participant | Phase 4 makes the prior verification assertion wrong | trusting stale state is scored as incorrect |
| TaskView gives an invalid completeness advantage | freeze server-side contracts and identical raw evidence; never accept participant-authored completeness | any unsupported receipt invalidates the run apparatus |
| local reasoning dominates all cost | score broad and local effort separately | TaskView can fail economically even if orientation falls slightly |
| initial broad sweep answers all later phases | later evidence changes and different local questions are released sequentially | if RAW still needs no later exploration, the case is too easy or retention is sufficient |
| task facts are too obvious | Stage 0 requires distributed witness evidence and a nontrivial near miss for each task judgment | revise rather than spend participant calls |

## I. Costed pilot

### Stage 0 — static construction and audit: 0 participant episodes

1. Create and freeze the small source tree and Phase 4 replacement.
2. Build the grounding/construction ledger and source hashes.
3. Have two reviewers verify RAW obtainability and TaskView correctness.
4. Have a blind reviewer answer each local oracle field with TaskView only; any
   reliably answerable field is leakage and must be changed.
5. Verify that RAW orientation requires evidence from at least four source
   categories and that each local phase has a one- or two-file oracle region.
6. Run only deterministic fixture, parity, derivation, staleness, oracle, and
   telemetry smoke checks. Do not invoke a participant model.

### Stage 1 — tiny mechanism pilot: 8 episodes, 40 participant turns

- one frozen case;
- one fixed participant model/version and tool policy;
- four independent matched replicates per arm;
- each replicate is one five-turn stateful episode;
- eight episodes total: four RAW and four TASKVIEW;
- alternate/randomize arm order, freeze sampling settings and budgets, and do no
  within-episode retries.

This is the smallest matrix that can reveal whether the effect recurs rather
than depending on one lucky trajectory. It supports a go/no-go mechanism review,
not population inference.

### Stage 2 — replication, only after a Stage 1 continue decision

Add the API/schema case and legacy-subsystem-removal case, four matched pairs per
case: 16 additional episodes and 80 participant turns. Optionally add four more
pairs on the primary case only if Stage 1 is directionally positive but noisy.

### Stage 3 — end-to-end economics, only after replication

Test construction, validation, maintenance, reuse, and wrong-state risk. Do not
infer end-to-end value from the prebuilt-view experiment.

## J. Kill, revise, and continue criteria

### Kill or rethink TaskView for this mechanism

- TASKVIEW reduces median paired `O_post` by less than 15%, or is lower in no
  more than two of four pairs, with no compensating improvement in scope/local
  correctness; or
- net orientation cost is consistently higher and correctness is no better; or
- stale anchoring causes worse changed-evidence correctness in at least two pairs.

The 15–30% region is inconclusive: do not call it a win.

### Revise the experiment before more inference

- Stage 0 finds a hidden fact, invalid grounding, or direct-answer leakage;
- participants do not inspect local sources in the supposedly local phases;
- RAW can establish all task judgments from one obvious file or generic
  dependency lookup;
- telemetry cannot reliably distinguish broad from local returned bytes;
- the stateful context or Phase 4 evidence is not actually identical by arm; or
- more than half of TASKVIEW episodes never discover the view, in which case one
  discoverability-only apparatus revision may be tested before killing it.

### Continue to cross-family replication

Continue only if the primary 30%/three-of-four threshold passes, implementation-
local correctness is not lower, local source inspection remains present, and no
parity or leakage audit fails. Similar total tokens do not block continuation if
focus and correctness improve as hypothesized.

### Continue to end-to-end construction testing

Continue only after the orientation effect replicates in at least two task
families and survives changed evidence. Then compare the observed reuse value
against construction, validation, maintenance, and wrong-state costs.

## Review conclusion

This experiment does not ask whether TaskView understands the repository for the
agent. It asks whether a correct, prebuilt task-conditioned view preserves four
coarse judgments long enough to reduce their repeated reconstruction, while the
agent still has to read and reason about the exact local code that determines
the answer. That claim is narrow, observable, and allowed to fail.
