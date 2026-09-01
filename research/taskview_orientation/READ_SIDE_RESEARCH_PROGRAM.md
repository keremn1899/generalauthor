# TaskView read-side research program

**Status:** design only. This document does not select or implement TaskView v0.2,
does not authorize participant inference, and does not treat the sealed v0.1
episodes as observations in a future live experiment.

## 0. Question, fixed evidence, and experimental object

The research question is:

> How should TaskView expose stable semantic vocabulary, dynamic state, and
> epistemic metadata so that an agent can consume task-conditioned state without
> repeatedly reconstructing how to use TaskView?

The following are fixed premises, not quantities to re-estimate here:

- repository-side `O_post` fell by a median 43.12%, with 4/4 directional wins;
- the apparent local-correctness decline was an exact-representation oracle
  mismatch, not demonstrated semantic harm;
- TaskView consumption remained net economically negative;
- post-phase-1 consumption was approximately 80% description/introspection, 14%
  SQL results, and 6% maintenance;
- all 111 observed SQL calls addressed one relation; all used `SELECT *`; none
  used a join, subquery, CTE, aggregate, or set operation;
- 105/111 calls are expressible as a simple get/filter and all 111 with simple
  ordering/limit modifiers; and
- all 20/20 phase-clusters used multiple relations and composed their results in
  model reasoning; 0/20 composed them in SQL and 0/20 showed unambiguous graph
  traversal.

The observed access pattern is therefore **mostly flat relation reads followed by
model-side relational composition**. This says something about the common access
pattern at the present scale. It says nothing against named n-ary relations as the
semantic representation, and nothing against SQLite/SQL as the physical substrate.

The layers must remain distinct throughout the program:

```text
semantic representation    named typed n-ary relations
physical/query substrate   SQLite and SQL
common agent access        currently flat reads + model-side composition
```

The experiment manipulates principally the third layer. A lack of observed joins is
not evidence against the first two.

## 1. Read-side planes and information lifetimes

### 1.1 Plane decomposition

| Plane | Contents | Necessary property |
| --- | --- | --- |
| Vocabulary | relation names, ordered roles, exposed column aliases, one-line meanings, BASE/DERIVED mode | compact, stable, versioned separately from ordinary row changes |
| State | current tuples returned by a relation access | exact revision must be recoverable; serialization should not silently imply completeness |
| Epistemic | view/relation revision, derivation state, completeness status and named universe, known gaps, provenance/grounding | must make safe negative inference possible without conflating empty with complete |
| Query | SQL, get/filter/select, bundle, conditional read, and escape-hatch rules | should change access ergonomics without changing relation meaning |

The current `describe` response crosses all four planes. It can return stable names and
roles, dynamic relation state, completeness/currentness, and instructions needed to
form a later SQL call. That coupling is the suspected source of contract
amplification.

### 1.2 Lifetime classification

“Revision-sensitive” below means state revision, unless explicitly called schema
revision. Schema change must have its own token; an assertion changing rows must not
invalidate an otherwise stable vocabulary contract.

| Information | Across phases | Across episode | Revision-sensitive | Tuple-sensitive | Task-sensitive |
| --- | :---: | :---: | :---: | :---: | :---: |
| query protocol and operation grammar | yes | yes | no | no | no |
| TaskView identity and task-spec identity | yes | yes | no | no | yes |
| relation names, role names/types, column aliases | yes | yes, absent schema change | schema only | no | yes |
| one-line relation meaning | yes | yes, absent schema change | schema/contract only | no | yes |
| BASE/DERIVED mode and derivation input names | yes | yes, absent schema change | schema/definition only | no | yes |
| current rows | only until a relevant mutation | no | yes | yes | yes |
| relation/view revision token | no | no | is the change signal | no | yes |
| derivation execution/currentness state | only until an input changes or rerun occurs | no | yes | relation-level | yes |
| completeness declaration (`COMPLETE`, `INCOMPLETE`, `UNKNOWN`) | until a new receipt | no | yes | target relation | yes |
| completeness universe and basis | often stable in intent, not in receipt validity | not assumed | yes | target relation | yes |
| known gaps | only until a new receipt | no | yes | target relation/universe | yes |
| assertion origin and grounding | while that assertion remains active | not assumed | yes | yes | yes |
| automatic relevance choice | no | no | prompt/state dependent | possibly | strongly yes |

This yields the central design rule to test: **deliver schema-versioned vocabulary on a
schema lifetime; deliver rows and epistemic status on a state lifetime; deliver
grounding on a tuple lifetime.** Do not retransmit one merely because another changed.

## 2. Design-space map

The candidate letters in this section name architectures. Factorial cells later use
different codes to avoid overloading those letters.

| Candidate | Stable contract | Normal state access | Semantic context | State granularity | Epistemic delivery | Main proposition | Main risk |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A. Pull introspection + SQL | pulled, potentially repeatedly | SQL | explicit `describe` | one or SQL-selected relations | explicit inspection | current baseline | stable and dynamic information are reacquired together |
| B. Pushed contract + SQL | pushed once per schema version | SQL | contract at initialization | SQL-selected | separately inspectable | contract rediscovery, not SQL, is the dominant cost | pushing the entire vocabulary wastes context when few relations matter |
| C. Pushed contract + simple access | pushed once | `get`/`select`; SQL escape hatch remains | contract at initialization | normally one relation | separately inspectable | a constrained common path reduces request friction and over-reading | output differences or forced capability loss can masquerade as a query-language effect |
| D. SQL + automatic relation context | no separate learning dialogue | SQL | compact card on first use or semantic need | SQL-selected | attached on first use/revision trigger | retain SQL while eliminating explicit schema learning | automatic attachment may duplicate context or make opaque parser-dependent decisions |
| E. Bundled semantic projection | pushed or embedded | task snapshot/bundle request | bundle header | multiple named relations | bundle-level plus per-relation exceptions | call/envelope and repeated-phase overhead dominate | relevance selection may move task reasoning into TaskView and leak the answer |
| F. Revision-addressed conditional reads | pushed or first-use | conditional relation read / delta | first full response, then handle | one relation or explicit set | always returns freshness decision; detail on change | repeated reads are rational checks that can become cheap `not_modified` responses | cache/handle complexity and unsafe stale reuse |

Candidate F is genuinely distinct from C. C changes the request language. F changes
the temporal transfer model: state is addressed by revision and unchanged state is not
resent.

### 2.1 Candidate payload sketches

The sketches are intentionally conceptual. Field spelling and whitespace must be
frozen before replay so byte comparisons are not tuned after seeing results.

**A — pull + SQL**

```json
{"describe":"protected_by"}
```

```json
{
  "relation": {
    "name": "protected_by",
    "roles": [
      {"role":"service","column":"service_id"},
      {"role":"adapter","column":"adapter_id"}
    ],
    "meaning":"Accepted adapter protection for a service."
  },
  "state":"CURRENT"
}
```

```sql
SELECT * FROM protected_by
```

**B — pushed contract + SQL**

```text
task_view=migration-v1 schema=sha256:…
protected_by(service->service_id, adapter->adapter_id)
  Accepted adapter protection for a service.
verification_gap(service->service_id)
  Affected services without current task-relevant verification.
…
```

The contract is charged once. A state call returns only the SQL rows and a small query
envelope. Currentness, completeness, and grounding remain available through explicit,
targeted inspection.

**C — pushed contract + simple access**

```text
select(relation="protected_by",
       filters={"service":"service:reporting"},
       order=[], limit=null)
```

```json
{"relation":"protected_by","rows":[{"service_id":"service:reporting","adapter_id":"adapter:canonical-json"}]}
```

The SQL escape hatch remains installed and its use is logged. “Simple path wins” means
the participant actually used it; availability alone is a different estimand. For an
isolated live comparison, SQL and simple access must use the same output envelope and
row-key convention. Otherwise request language and response representation are
confounded.

**D — SQL with automatic first-use/revision context**

```sql
SELECT * FROM verification_gap
```

```json
{
  "relation":"verification_gap",
  "signature":"verification_gap(service->service_id)",
  "meaning":"Affected services without current task-relevant verification.",
  "revision":13,
  "derivation":"CURRENT",
  "coverage":{"status":"COMPLETE","universe":"affected_service","state":"CURRENT"},
  "rows":[]
}
```

On another query at revision 13 the stable signature/meaning is omitted. On a relevant
revision change, dynamic epistemic fields are attached again. The relation card is
triggered by relations parsed from SQL, not by a task-relevance model.

**E — bundled projection**

```json
{
  "snapshot_revision":13,
  "relations":{
    "affected_service":{"rows":[{"service_id":"service:checkout"}]},
    "protected_by":{"rows":[{"service_id":"service:reporting","adapter_id":"adapter:canonical-json"}]},
    "verification_gap":{"coverage":{"status":"COMPLETE","universe":"affected_service","state":"CURRENT"},"rows":[]}
  }
}
```

There are three distinct bundle selectors and they must not be conflated:

1. participant names the relations (no automatic relevance judgment);
2. a frozen task-authored projection names them (task conditioning is part of the
   treatment and must be leakage-audited); or
3. an automatic selector infers relevance from the current prompt (moves reasoning
   into TaskView and is not suitable for the first probe).

**F — revision-addressed conditional read**

```text
get("verification_gap", if_relation_revision=7)
```

```json
{"relation":"verification_gap","relation_revision":7,"not_modified":true,"derivation":"CURRENT","coverage_state":"CURRENT"}
```

After an input mutation, the same call must not return a bare `not_modified`; it must
return `STALE`, a changed revision, or new rows plus a current receipt. Conditional
transfer can suppress unchanged rows, never epistemic invalidation.

## 3. Independent design dimensions

The architectures are points in a factored space, not indivisible packages.

| Dimension | Levels | Independent manipulation? | Important constraint |
| --- | --- | :---: | --- |
| contract delivery | pull / push | yes | pushed bytes must be charged; pull remains available for targeted grounding |
| contract scope | full catalog / first-use relation card / participant-selected subset | yes | automatic task-selected subset is a separate relevance manipulation |
| schema lifetime | per call / per phase / per episode / schema-revision-triggered | yes | ordinary row revision must not trigger schema retransmission |
| request language | general SQL / constrained lookup / both | mostly | forced lookup changes general capability; lookup-plus-SQL tests affordance and use |
| escape-hatch policy | absent / present but neutral / present and discouraged | yes | existence and actual use must be reported separately |
| response representation | physical column keys / semantic role keys / compact tuples | yes | hold fixed when estimating request-language cost |
| semantic context | explicit request / first-use attachment / every response | yes | context trigger must be mechanical, not inferred task relevance |
| state granularity | one relation / participant-named multi-relation / auto bundle | yes | auto bundle introduces a selector mechanism |
| currentness | explicit status call / every response / revision-triggered | yes | empty results need enough status to avoid unsafe inference |
| completeness detail | none inline / compact status+universe / full receipt | yes | compact form must preserve status, named universe, and receipt validity |
| grounding | explicit tuple request / inline for every tuple / inline on uncertainty | yes | grounding is tuple-sensitive and can dominate row bytes |
| temporal transfer | full rows / ETag-style `not_modified` / row delta | yes | invalidation behavior is part of correctness, not only compression |
| relevance selector locus | none / participant / frozen task author / automatic model | yes | selector quality and interface quality are different causal mechanisms |

Useful independent contrasts require holding response bytes and capabilities constant
where possible. A natural candidate surface may later combine several winning levels;
the mechanism experiment should not.

## 4. Is the proposed 2×2 appropriate?

Use unambiguous cell codes because the proposed cell letters conflict with candidate
letters A–D above:

| | SQL only | lookup available + SQL escape |
| --- | --- | --- |
| pull contract | `P-SQL` | `P-LOOKUP` |
| stable pushed contract | `S-SQL` | `S-LOOKUP` |

This factorial can estimate:

- the contract-delivery main effect: `(S-SQL + S-LOOKUP) - (P-SQL + P-LOOKUP)`;
- the simple-path availability main effect: `(P-LOOKUP + S-LOOKUP) - (P-SQL + S-SQL)`;
- whether a simple path matters only when the vocabulary is already known.

It is clean only under four controls:

1. SQL and lookup return byte-identical row/envelope representations;
2. both lookup cells retain the same SQL escape hatch and tool visibility;
3. pushed-contract bytes, tool-schema bytes, and pull-description bytes are all
   charged regardless of where in the episode they arrive; and
4. the lookup operation supports every task-required call in this fixture.

Even then, the second factor estimates **availability/default affordance**, not the
intrinsic cost of the query languages, because participants may use SQL in a lookup
cell. Removing SQL would estimate a forced common-path effect, but would reduce general
capability. The sealed fact that all 111 calls are representable permits a narrowly
valid forced-lookup replay, not a general claim of capability equivalence.

The 2×2 also does not identify automatic context, epistemic signaling, bundling, or
temporal caching. `P-LOOKUP` is not a leading product candidate and consumes live
episodes mainly to estimate an interaction.

**Recommendation:** do not start with the complete factorial. Use offline replay for
all four cells, then a fractional, mechanism-targeted live design (§10). If simple
access shows a material effect under a stable contract, add `P-LOOKUP` later to measure
the interaction before making a general causal claim.

## 5. Competing behavioral hypotheses

| Hypothesis | Distinguishing prediction | Evidence against it |
| --- | --- | --- |
| H1 — interface-induced semantic uncertainty | a pushed schema-versioned contract sharply reduces description bytes/calls and may reduce relation breadth or cross-phase rereads | description falls but breadth, rereads, repository exploration, and epistemic refreshes do not |
| H2 — rational broad retrieval | pushed contract removes description traffic while distinct relations, rows, and phase-level flat composition remain approximately unchanged | stable contract also produces a large, reproducible fall in breadth or row retrieval without a correctness loss |
| H3 — query-language friction | with contract and response format held fixed, lookup availability is used and reduces rows/bytes, full scans, tool errors, or calls | agents continue choosing SQL, or lookup use changes syntax but not retrieval/error metrics |
| H4 — epistemic caution | stable vocabulary alone is insufficient; compact revision/currentness/completeness signals reduce explicit refreshes and repeated reads while preserving calibrated absence reasoning | inline signals do not change refresh behavior, or they reduce bytes only by causing false certainty |
| H5 — model-side composition is optimal at this scale | separate one-relation reads and model-side composition persist under known schema and cheap access, with no local/safety penalty | agents adopt server-side composition when it is equally discoverable and materially reduce payload/calls |
| H6 — phase-boundary memory re-grounding | rereads cluster at new prompts even when state revision is unchanged; conditional reads or visible revision continuity reduce them | rereads are just as common within phases or after explicit unchanged revision signals |
| H7 — task-snapshot convenience | participant-named bundles reduce envelopes and repeated reads beyond a sum of relation results | bundles mainly over-return rows, or only automatic task selection wins |

H2 and H5 are not failure hypotheses. At tiny cardinalities, broad retrieval of several
relations may be the efficient strategy. The desired conclusion can be “contract cost
was waste; flat retrieval was not.”

## 6. Deterministic trajectory counterfactuals

No participant calls occur in this stage. It is payload accounting over the sealed
TASKVIEW trajectories, and it does not claim that behavior would have stayed fixed.

### 6.1 Build a logical-access ledger

For each successful and failed TaskView call, preserve:

```text
episode, phase, sequence
operation and exact arguments
view/schema/relation revision at call time
relations referenced
projection, filters, order, limit
returned rows in stable relation-role order
derivation/currentness/completeness state
whether an assertion/rerun intervened
observed canonical UTF-8 JSON byte count
```

Parse SQL into a restricted AST and classify it mechanically. Do not infer the
participant's intent. Validate the prompt's reported 89 enumerations, 16 filters, six
order/limit variants, and 111 single-relation calls from this ledger before using it.
Unparseable or mismatching calls are retained as escape-hatch calls, not silently
translated.

Reconstruct state at each event from a copy of the sealed initial database plus the
recorded assertion/rerun sequence, or verify against the exact recorded result payload
when available. Never query the final database snapshot as if it represented every
earlier phase.

### 6.2 Freeze serializers before totals

For each candidate, preregister:

- canonical key order, separators, Unicode encoding, null/default omission rules;
- the exact pushed contract;
- tool names, descriptions, and argument schemas;
- first-use, phase, and revision cache rules;
- error payloads; and
- whether request, system/tool-schema, and response bytes are in each ledger.

Compute two byte ledgers:

1. **sealed-compatible result bytes:** exact model-visible TaskView result/error bytes,
   matching the historical response-side definition;
2. **fully loaded read bytes:** pushed contract + tool schema delta + TaskView
   result/error payloads. Report request bytes and provider tokens separately where
   measurable; do not invent per-tool token attribution the provider does not expose.

Moving a contract to initialization must not make it disappear from accounting.

### 6.3 Required replay scenarios

For each of the four sealed TASKVIEW trajectories, calculate:

1. observed v0.1 payload;
2. one stable contract + the observed SQL result sequence;
3. one stable contract + translated simple lookups, using the same result serializer;
4. automatic first-use relation card + observed SQL rows;
5. first-use card with epistemic metadata retransmitted only when the relevant
   relation/receipt revision changes;
6. participant-named phase bundle containing the union of relations actually accessed
   in that phase; and
7. revision-addressed conditional reads where an unchanged `(relation, revision,
   query)` returns `not_modified`.

For bundles, the observed per-phase union is an accounting lower bound, not evidence
that an automatic selector could choose it prospectively. Also report all-relations and
one-extra-relation sensitivity cases so selector error is visible.

### 6.4 Floors, residuals, and admission gates

For each trajectory and candidate report:

```text
contract bytes
semantic context bytes
dynamic row bytes
epistemic bytes
grounding bytes
error bytes
maintenance bytes
tool-schema delta
total read bytes
repository O_post
net orientation
```

Compute three counterfactuals:

- **trajectory-preserving:** same logical calls, candidate serialization;
- **mechanical dedup floor:** one delivery per unique `(relation, query, relevant
  revision)` plus mandatory safety metadata; and
- **row floor:** unique canonical rows plus the minimum discriminating epistemic state.
  This is diagnostic only, because it may not be a usable interface.

For matched replicate `i`, the consumption budget that preserves net zero is:

```text
budget_i = RAW_O_post_i - TASKVIEW_repository_O_post_i
net_delta_i(candidate) = candidate_read_bytes_i - budget_i
```

Report medians and all directional results; do not average away one expensive
trajectory. Because initialization placement differs, report both the sealed-compatible
post-phase metric and an **acquisition-inclusive net** that charges the full initial
contract.

Admission rules for a live probe:

- **admit:** trajectory-preserving acquisition-inclusive replay is net-positive at the
  median and in at least 3/4 pairs, with safety metadata intact;
- **conditional:** only the mechanical dedup floor crosses net zero, identifying a
  behavioral reuse mechanism that a live probe must demonstrate;
- **deprioritize:** even the floor is net-negative at the median, unless the candidate
  has a separately preregistered mechanism for reducing repository `O_post` large
  enough to close the measured gap; and
- **reject:** it is more expensive than v0.1 in at least 3/4 trajectory-preserving
  replays without adding a safety or capability benefit, or its cheapest payload fails
  the epistemic discriminability tests in §8.

These gates reject candidates from the next live shortlist, not the relational model or
SQL storage.

## 7. Mechanical “behavioral greed” measures

Metrics are computed per phase and episode. The episode is the independent unit; five
phases are not five replicates.

| Metric | Mechanical definition |
| --- | --- |
| relation breadth | count of distinct semantic relations referenced in successful state reads; also report fraction of declared relations |
| state query count | count of successful state-returning calls, split by SQL, lookup, bundle, and conditional read |
| relation access count | sum of relation references across successful queries; multi-relation SQL would count each relation |
| phase relation reread rate | accesses after the first to the same `(relation, relevant revision)` in a phase / relation accesses |
| episode relation refresh rate | accesses in a later phase to an unchanged `(relation, relevant revision)` / eligible later-phase accesses |
| exact-query reread rate | repeats of normalized `(relation, projection, filters, order, limit, revision)` / state queries |
| rows retrieved | sum of returned row instances, including duplicates across calls |
| unique delivered rows | cardinality of `(relation, canonical role tuple, relation revision)` across responses |
| row reread amplification | row instances retrieved / unique delivered rows; report zero-denominator cases separately |
| byte reread amplification | dynamic-state bytes / bytes of unique delivered rows at their revisions |
| full-scan rate | successful single-relation state calls with no filter / successful single-relation state calls; order/limit is reported separately |
| filter rate | calls with at least one equality/range predicate / successful state calls |
| limit/order rate | calls with order or limit modifier / successful state calls |
| introspection operations | catalog, relation-card, status, and grounding calls, split by kind |
| contract amplification | vocabulary/introspection bytes / dynamic-state bytes; report numerator and denominator too |
| epistemic refreshes | explicit status/describe calls after first delivery, split by whether a relevant revision changed |
| stale-read attempts | state reads issued while a referenced derived relation is stale |
| simple-path adoption | representable state calls made through lookup / all representable state calls |
| SQL escape use | SQL calls in a simple-path arm, split into representable and non-representable |
| tool error rate | participant-caused rejected calls / participant tool calls, by operation and error class |

Do not use “rows eventually needed” as a primary metric. Determining need from answer
text is subjective and arm-dependent. `Unique delivered rows` is reproducible; an
optional blinded annotation of answer-supported rows may be reported only as
sensitivity analysis.

## 8. Epistemic safety and falsification

### 8.1 Required negative-state vocabulary

Every candidate must let the participant distinguish:

```text
PRESENT
NO_MATCH_OBSERVED
KNOWN_ABSENT_WITHIN_NAMED_UNIVERSE
NOT_YET_ESTABLISHED (never run / failed / unknown)
STALE
OUTSIDE_DECLARED_UNIVERSE or UNIVERSE_MEMBERSHIP_UNKNOWN
```

An empty `rows` array alone means only `NO_MATCH_OBSERVED`. It becomes known absence
only when the target derivation succeeded, is current, has a current `COMPLETE` receipt,
and its named universe is sufficient. `COMPLETE` never means whole-world complete
unless the named universe itself is the whole world and that claim is justified.

### 8.2 Pre-live deterministic safety suite

Construct payload fixtures with identical empty rows and different metadata:

1. current + successful + `COMPLETE` over a sufficient named universe;
2. current + `INCOMPLETE` with known gaps;
3. current + `UNKNOWN`;
4. stale derivation carrying an old `COMPLETE` receipt;
5. `NEVER_RUN` and `FAILED` derivations;
6. current target with an incomplete/stale derived universe; and
7. a filtered subject proven outside the named universe versus one whose universe
   membership is unknown.

Serialized payloads must be pairwise distinguishable where the allowed inference
differs. A cache/conditional-read candidate must propagate invalidation even when row
bytes did not change. This suite is a hard pre-live gate.

### 8.3 Live safety scoring

Freeze a semantic rubric, not an exact-string oracle, for:

- whether absence is scoped to the named universe;
- whether currentness and completeness are both checked;
- whether stale/unknown state is described as unresolved rather than absent;
- whether whole-world completeness is rejected when the fixture does not support it;
- correct response to the phase-4 mutation; and
- preservation of source-grounded local inspection.

Adjudicate answer semantics arm-blind. Canonical relation identifiers may be accepted,
but prose expressing the same proposition must score identically. The prior
exact-representation mismatch must not recur.

Hard safety falsifiers are:

- the surface makes two differently justified absence states observationally
  identical;
- a stale/unknown/incomplete result is labelled or documented as known absent;
- a cache returns `not_modified` across relevant invalidation without a stale/change
  signal; or
- an automatic bundle omits state while implying that its projection is complete.

In a live probe, any unambiguous false closed-world conclusion triggers arm review and
blocks selection, even if byte economics improve. It is not automatically causal from
one stochastic episode; inspect the trajectory and reproduce with a deterministic
surface test before attributing it to the interface.

## 9. Modest-scale implications (theory only)

Let `R` be declared relations, `U` accessed relations, `N` rows in the view, `K` rows
returned after filtering, `Q` calls, and `D` rows changed since the last read.

| Candidate | More relations | More rows/relation | Smaller relevant fraction | Principal asymptotic concern |
| --- | --- | --- | --- | --- |
| A pull + SQL | repeated catalog can approach `O(P·R)` across phases | SQL can keep payload near `O(K)` | full catalog pull is poor | vocabulary repetition |
| B push + SQL | one `O(R)` contract | SQL can keep payload near `O(K)` | pushing all `R` becomes wasteful | session-start contract size |
| C push + lookup | one `O(R)` contract | good only if filters/limits are used; enumeration is `O(N)` | same pushed-contract problem | constrained path may encourage or discourage precision depending on defaults |
| D auto context + SQL | context near `O(U)` per schema revision | SQL remains selective | favorable when `U << R` | parser-triggered context and multi-relation query semantics |
| E bundle | participant bundle near `O(U + K)`; automatic/all-state can approach `O(R)` | snapshot can approach `O(N)` | automatic selector quality dominates | over-return and hidden relevance reasoning |
| F conditional/delta | first use near `O(U)` | initial read `O(K)`, later changes near `O(D)` | favorable for repeated small subset | cache invalidation and handle state |

At the current tiny cardinalities, separate relation reads can rationally beat a join in
authoring effort and be negligible in returned bytes. Nothing in this table justifies a
world-size experiment yet. It only rules out obvious pathologies: per-phase full
catalog retransmission, unconditional all-state bundles, and caches without explicit
invalidation.

## 10. Minimal live probe after replay

### 10.1 Arms

Only candidates that pass the replay and deterministic safety gates proceed. The
default minimal diagnostic set is five arms:

| Code | Surface | Contrast |
| --- | --- | --- |
| `R` | fresh RAW control | current-world repository and net-economic anchor |
| `T0` | pull contract + SQL | fresh v0.1 conceptual baseline |
| `T1` | stable pushed contract + SQL; epistemic detail explicit | `T1 - T0`: contract rediscovery (H1 vs H2) |
| `T2` | same stable contract; simple lookup preferred; same SQL escape hatch; byte-identical result representation | `T2 - T1`: simple-path availability and actual use (H3) |
| `T3` | same stable contract and SQL; compact epistemic status attached on first access and relevant revision change | `T3 - T1`: epistemic signaling (H4/H6) |

This is a fractional mechanism design, not a contest among polished product variants.
It deliberately leaves automatic semantic cards, bundles, and deltas for a later probe
unless replay shows one clearly dominates and a listed arm fails admission.

All TaskView arms keep identical semantic relations, row contents, derivations,
mutation/rerun behavior, source tools, and local-task prompts. `T1`–`T3` receive the
same stable vocabulary bytes. `T2` changes only the request affordance; its SQL escape
hatch remains available and measurable. `T3` attaches only dynamic epistemic fields,
not an additional semantic summary.

For the mechanism contrast, `T1`–`T3` also retain `T0`'s on-demand catalog operation;
push does not make a repeat pull impossible. A repeated pull returns the ordinary
catalog and is charged. This lets the probe observe whether a stable, schema-versioned
promise actually removes rediscovery behavior instead of guaranteeing the desired
metric by deleting the operation. Targeted relation status and tuple grounding remain
available in every TaskView arm.

### 10.2 Replication and ordering

- Three fresh episodes per arm: 15 episodes, 75 phase turns.
- Block by replicate. Within each replicate, use a preregistered seeded random
  permutation of the five arms.
- Use the same scientific world, five prompts, model version, provider, system context,
  tool availability outside the manipulation, and context-retention policy.
- Do not use canary, preflight, dry-run, v0.1 scientific, or aborted episodes as live
  observations. They may validate infrastructure or set fixed historical budgets only.
- Treat this as a mechanism probe: report exact episode values, medians, ranges, and
  directional counts. Three replicates do not support population-level significance
  claims.
- If the leading contrast is directionally inconsistent or within a preregistered
  indifference band, do not add a favorable arm ad hoc. A second preregistered block
  may add one episode to every arm (maximum 20) before unblinding outcomes.

### 10.3 Primary measures and fair accounting

Primary:

1. acquisition-inclusive net orientation relative to the fresh matched RAW episode;
2. TaskView-visible read consumption, split into vocabulary, state, epistemic,
   grounding, errors, and maintenance;
3. introspection operations and contract amplification;
4. relation breadth, episode refresh rate, rows retrieved, and full-scan rate; and
5. epistemic correctness, especially negative inference after the phase-4 revision.

Preserve and report the sealed outcomes as well:

```text
repository O_post
TaskView-visible consumption
sealed-compatible net orientation
acquisition-inclusive net orientation
relation breadth and rereads
rows retrieved and query count
introspection count and participant tool errors
local source inspection
local correctness under semantic adjudication
currentness/completeness correctness
```

The historical `net orientation = O_post + post-phase-1 TaskView bytes` remains for
comparability. The acquisition-inclusive measure is co-primary for surface choice,
because push placement otherwise receives a free accounting advantage. Report provider
tokens and total model-visible bytes as secondary resource measures, without claiming
fine-grained cognitive attribution.

### 10.4 Live guardrails and kill criteria

An episode is apparatus-invalid, not a scientific loss, if surface parity, telemetry,
provider continuity, source mutation timing, or payload accounting fails.

Block an arm from v0.2 consideration if any of the following hold:

- it fails a hard epistemic falsifier in §8;
- semantically adjudicated local correctness or required local source inspection is
  lower than matched RAW in at least two of three replicates without an alternative
  valid local witness;
- its median acquisition-inclusive net is worse than `T0` and it adds neither safety
  nor capability;
- its reduction comes from omitted rows/status that another arm exposes;
- an automatic selector or bundle makes a scored task judgment unavailable to the
  other arms; or
- participant tool errors show the nominal common path is not usable (same structural
  error in at least two of three episodes).

Candidate-specific non-success criteria:

- stable contract: description traffic does not materially fall;
- simple path: low adoption, frequent representable SQL escape, or unchanged row/error
  economics;
- inline epistemics: refreshes do not fall, or false certainty increases;
- bundle: gains vanish when the selector is participant-named or one-extra-relation
  bytes are charged;
- conditional reads: revision invalidation is not reliable.

Do not claim an improvement in “local cognition.” The permitted claims concern
observable inspection, semantic answer correctness, interface behavior, and bytes.

## 11. Expected-result interpretation matrix

| Observed pattern | Supported explanation | Decision implication |
| --- | --- | --- |
| `T1` collapses introspection, keeps safety/local guardrails, and crosses net zero | H1; stable contract delivery was the dominant defect | retain SQL and simplify contract lifetime/delivery |
| `T1` collapses introspection but relation breadth, rows, and flat composition stay stable | H2/H5; broad retrieval is likely rational at this scale | do not optimize away flat reads; retain SQL unless another contrast wins |
| `T1` reduces both introspection and breadth/rereads | semantic uncertainty induced some over-reading | stable contract is core; measure whether effect persists before adding query complexity |
| `T2` is adopted and materially lowers rows/bytes/errors versus `T1` | H3 | investigate constrained common path plus SQL escape hatch |
| `T2` is available but agents mostly use SQL | no demonstrated simple-path benefit | keep SQL; do not equate API existence with use |
| `T2` changes syntax but not rows/bytes/errors | request language was cosmetic at this scale | prefer the smaller/safer contract, not a query-language rewrite |
| `T3` reduces status/describe refresh and rereads beyond `T1`, with calibrated absence | H4/H6 | currentness/completeness signaling belongs in the core read contract |
| `T3` saves bytes but produces false known-absence claims | caution was desirable | reject the cheaper signaling design |
| flat reads + model composition persist in `T1`–`T3` | H5 | treat this as a valid common access pattern, not relational failure |
| participant-named bundle wins replay/live | call/envelope granularity matters | investigate explicit bundle access |
| only automatically selected bundle wins | relevance selection, not serialization, caused the gain | audit as a separate task-reasoning mechanism; do not credit TaskView access alone |
| conditional reads win only across unchanged phases | phase-boundary re-grounding is real and cacheable | investigate revision handles after invalidation safety is proven |
| no safe candidate approaches positive acquisition-inclusive economics | read overhead is not a local API problem | reconsider consumption architecture, task conditioning, or delivery channel more fundamentally |

## 12. What to test first

1. **Run no participants now.** First build the deterministic logical-access ledger and
   replay A–F over all sealed TASKVIEW trajectories.
2. Freeze the epistemic discriminability suite and reject unsafe/uneconomic
   serializations.
3. The first live causal contrast should be **fresh pull+SQL (`T0`) versus stable
   pushed contract+SQL (`T1`)**, embedded in the five-arm diagnostic if resources
   permit. It changes only the mechanism implicated by the dominant 80% cost while
   leaving SQL, relational semantics, state granularity, and model-side composition
   available.
4. Test simple access and revision-triggered epistemics as orthogonal contrasts against
   the same `T1` control. Do not test a bundle first: prospective relevance selection
   is a larger, task-sensitive mechanism and would make a win hard to attribute.
5. Do not run a world-size experiment until the current-world contract, query, and
   epistemic effects are separated.

The first decision is therefore not “SQL or a simpler API.” It is whether stable
vocabulary should have a different delivery lifetime from dynamic state. The sealed
evidence makes that the highest-value uncertainty to resolve; the proposed contrasts
then determine whether any additional query or epistemic mechanism earns its cost.
