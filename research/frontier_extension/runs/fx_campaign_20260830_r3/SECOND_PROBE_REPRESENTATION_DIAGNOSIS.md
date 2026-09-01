# Frontier-extension second probe: expert diagnosis of the representation

## Research-lead decision

**I would stop investing in graph-native programming as Graphauthor's primary agent-facing language and stop treating specialized graph storage as the product thesis.** The campaign shows that graph-v1 is expressive enough to execute substantial topology, but it is not reliably programmable by this frontier agent and it produced no net economic advantage even in the cases deliberately engineered to favor reusable graph computation.

I would preserve only a narrower thesis: a relational Task IR can profit from a small set of conventional graph operators—reachability, constrained paths, cycles, and perhaps ordering—compiled over the same relational store. I would fund one decisive interface-controlled experiment, then terminate the graph-language branch unless that operator layer beats SQL on at least one preregistered regime without sacrificing reliability.

What would change my mind is not a faster LadybugDB run or better graph-v1 prose. It would be a same-backend result in which a conventional graph interface:

- matches SQL's valid and exact rate across repeated trajectories;
- removes almost all schema/parameter repair;
- and reduces total model interactions or visible bytes materially—about 25%—on reusable topology or constrained-path cases.

Absent that result, the rational default is SQL plus optional graph operators.

## Evidence status and campaign facts

The labels below are used literally:

- **OBSERVED** — directly present in the sealed campaign, participant-visible files, per-cell records, oracle, or grader.
- **INFERRED** — the best explanation of those observations.
- **SPECULATIVE** — plausible, but not established by this campaign.

**OBSERVED.** The per-cell records show:

| Arm | Exact | Valid executions | Timeouts | Participant-facing errors | Interactions | Model-visible bytes | Wall time |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| T_SQL | 11/14 | 14/14 | 0 | 0 | 119 | 273,522 | 927 s |
| T_GRAPH | 7/14 | 9/14 | 5 | 135 | 286 | 1,389,005 | 2,542 s |

The `RESULTS.md` headline says T_GRAPH was valid in 7/14 cases, but its own row table, `EXECUTION_REPORT.md`, and the sealed cell records show nine valid executions and seven exact answers. I use the per-cell value, 9/14 valid, throughout.

Among the seven paired-exact cases requested for close analysis—FX03, FX04, FX05, FX06, FX07, FX08, and FX12—the comparison is still unfavorable:

| Arm | Interactions | Model-visible bytes | Participant-facing errors | Wall time |
| --- | ---: | ---: | ---: | ---: |
| T_SQL | 58 | 122,092 | 0 | 407 s |
| T_GRAPH | 77 | 167,033 | 72 | 1,095 s |

Only FX08 used fewer visible bytes in graph (20,916 versus 22,352), a saving of 1,436 bytes, while still taking 11 rather than 7 interactions, producing four errors, and taking 97 rather than 47 seconds.

**INFERRED.** This is enough to reject graph-v1 as the current default programming surface. It is not enough to reject graph semantics in every possible interface.

## Why the model fights graph-v1

### The mistakes are not arbitrary

**OBSERVED.** Across failed or rejected graph operations, the participant supplied `from` 27 times, `predicates` 44 times, `edge_types` 22 times, `references` 14 times, `id` 8 times, and `kind` 6 times. The exact error clusters include:

- 16 `path(..., from=...)` failures;
- 12 `expand(..., references=...)` failures;
- 11 `expand(..., from=...)` failures;
- 9 `expand(..., predicates=...)` failures;
- 8 `lookup(..., id=...)` failures;
- 6 `lookup(..., kind=...)` failures;
- 5 uses of `depends_on` as an `edge_type`;
- 5 uses of `retires` and `targets` as `edge_types`.

These forms have recognizable origins:

| Invented form | Closest learned convention | What it means here |
| --- | --- | --- |
| `from`, `to` | Gremlin/dataflow DSLs, generic path APIs, natural-language source/target | Especially non-arbitrary: `from` is valid inside graph-v1 programs, just not in the direct `expand`/`path` calls. |
| `references` on expansion/path | Generic REST/resource APIs and graph seed lists | Also induced internally: `references` is the correct direct argument for `lookup`. |
| `predicates` on direct calls | RDF/SPARQL vocabulary and graph traversal DSLs | Again induced internally: `predicates` is correct inside ephemeral traversal steps. |
| `node_id` or `id` | NetworkX-style node arguments, REST object identity, ordinary Python APIs | A natural singular form when the caller has one seed; graph-v1 requires plural `node_ids` for direct expansion and `references` for lookup. |
| `kind` on lookup/filter | Property-graph labels, ORM/REST filters, SQL `WHERE kind=...` | `kinds` is valid in program filters/expands, but `lookup(kind=..., name=...)` is not a direct operation. |
| `depends_on`, `retires`, `targets` as edge types | Cypher relationship types such as `[:DEPENDS_ON]`; NetworkX/Gremlin edge labels | Graph-v1 instead reserves `edge_types` for the physical carrier (`leadsto`) and calls semantic relations `edge_labels` in direct calls but `predicates` in programs. |

**INFERRED.** The participant was repeatedly converging on a conventional graph API. More importantly, several “hallucinations” were correct graph-v1 vocabulary transferred across the wrong graph-v1 layer. The surface makes the model remember two dialects:

```text
direct lookup:       references
direct expand:       node_ids + edge_labels
direct path:         source_ids + target_ids + edge_labels

program lookup:      references
program expand/path: from/to + predicates + kinds
```

That is stronger evidence of an interface problem than a generic claim that models are bad at graphs.

### Is graph-v1 fighting model priors?

**INFERRED — yes, strongly.** The API is internally explainable to its designer: physical carriers are separate from logical predicates; retrieval conveniences are separate from the program IR; plural arguments normalize batching. But the distinctions cut across the abstractions an agent is likely to have learned. In mainstream graph systems, `depends_on` is exactly the thing one would call an edge type or relationship label. A capable agent should not need to remember that it is an `edge_label` in one call, a `predicate` in another, and never an `edge_type` despite traversing an edge.

A technically coherent contract can still be a poor agent language. Graph-v1 currently is one.

### Documentation problem versus API-design mismatch

There is a real documentation defect.

**OBSERVED.** `describe` reports capability names and bounds but not the direct call signatures. It also advertises `project`, `search`, and `select_landmarks` among ephemeral operations. The frozen treatment validator rejects `search` and `select_landmarks` explicitly and rejects `project` as outside the frozen vocabulary. Participants incurred nine rejected program calls across those three advertised operations. The short access policy names the five top-level operations but does not resolve their parameter schemas.

Better documentation could plausibly eliminate many first-order failures: publish exact JSON schemas, remove unavailable operations from `describe`, show one valid direct call and one valid program, and return structured “expected keys” feedback.

**INFERRED.** Documentation alone would not eliminate the interaction tax. It would teach the agent to suppress the conventional terms it keeps producing and to preserve product-specific distinctions across layers. That is a conceptual/API-design mismatch. A language requiring continual inhibition of familiar vocabulary is paying a fixed cognitive tax even when perfectly documented.

## Expressiveness is not programmability

| Property | Score | Evidence and judgment |
| --- | --- | --- |
| **Expressiveness** | **adequate** | All candidates passed mechanical graph feasibility, and graph produced exact answers for deep closure, constrained reachability, ordered-sequence, reuse, cyclic, and set-composition cases. It is not “strong” because tight step/bound limits and split programs complicated several intended computations. |
| **Discoverability** | **very weak** | `describe` omitted argument schemas, exposed product operations excluded by the frozen treatment, and did not make the carrier/label/program-predicate distinction operationally obvious. The agent often inspected implementation source or learned by exception. |
| **Programmability** | **very weak** | Seven exact answers, five timeouts, 135 participant-facing errors, and repeated plausible-but-invalid programs. Success depended on finding a narrow happy path. |
| **Composability** | **weak** | Named variables, set algebra, and named answers worked. But the first four-output programs for FX06 and FX07 were invalid or split; FX13's constrained multi-output case timed out; and variables did not persist across program calls. |
| **Debuggability** | **weak** | Python `TypeError` sometimes supplied a useful hint, and several cases recovered. But recovery was expensive, invalid recipes often yielded little actionable schema feedback, and bounded/empty results were hard to distinguish from wrong direction, wrong vocabulary, truncation, or genuine absence. |
| **Economics** | **very weak** | Even conditional on paired exactness, graph used 33% more interactions, 37% more visible bytes, 72 participant errors versus zero, and 2.7× the wall time. The intended compact/server-side advantage did not survive total interaction cost. |

**INFERRED.** The language is capable of representing the computations after the correct program has been found. The principal failure is getting a frontier model to construct and repair that program reliably enough for autonomous use.

## What happened in the successful graph cases

The following reconstructions describe the effective computation, not every probe.

| Case | Effective SQL program | Effective graph program | More direct match to computation | Easier for the model |
| --- | --- | --- | --- | --- |
| **FX03** | Recursive reverse dependency closure from legacy package → join implemented modules → restrict to task-target production services → project services. | Lookup task/package → expand target deployment and production services → traverse reverse `depends_on` closure → expand to implementing services → intersect. | Graph, narrowly: the core is reachability plus intersection. | SQL. It was exact with 0 errors/8 interactions; graph needed 4 errors/11 interactions. |
| **FX04** | Recursive affected-module closure → join production/migration scope → anti-join services crossing deprecated boundary. | Lookup task, package, and boundary anchors → expand production and boundary membership → intersect approved services → subtract deprecated services. | SQL or set algebra equally; the actual task is mostly qualified membership and anti-join, not path enumeration. | SQL. Graph reached exact only after multiple incorrect direction/kind assumptions. |
| **FX05** | Recursive dependency closure plus ordered relational joins through service→module, package→migration, migration→deployment, and service→deployment; project services and deployment. | Broad neighborhood expansion, repeated path probes, then manual synthesis of the six production services and production deployment. The participant did not obtain the answer through one reliable `walk_sequence`/named-answer program. | SQL for the instantiated computation; a clean ordered-path primitive could have been graph-natural, but that is not what the participant operationalized. | SQL: 0 errors/10 interactions versus graph's 31 errors/11 interactions. |
| **FX06** | Recursive closure → affected production services → reuse as source for deployments, verification anti-join, and boundary membership → four projections. | Multi-step reverse closure (split to respect practical bounds) → implementing services ∩ production → derive deployments; separate programs derived verified/uncovered and boundary sets. | Graph for closure; relational/set expressions for the three derived classifications. Overall tie semantically. | SQL, decisively in total cost. |
| **FX07** | Large recursive closure → affected production set → derive deployments, uncovered services, boundary-sensitive services; repeated final CTE text across projections. | One compact program reused the 300-node closure for affected/deployment/uncovered; separate boundary programs recomputed or rebuilt part of the scope. | Graph for the 300-node closure and in-call reuse. | SQL: fewer interactions, half the visible bytes, no API errors. |
| **FX08** | Cycle-safe recursive `UNION` closure → production services → join owners and deployments. | Split bounded reverse expansion (depth 3 then 2) with visited-node behavior → intersect production services → expand owners and deployments in one named-answer program. | Graph. This is the cleanest positive semantic example. | SQL overall; graph's only benefit was 1.4 KB fewer visible bytes, outweighed by four errors and four extra interactions. |
| **FX12** | Recursive closure → affected ∩ production ∩ boundary-crossing → anti-join verified → project services and deployments. | Split closure depth 4+2 → intersect with production → traverse verification both ways to recover verified services → difference → deployments, all in a compact named-answer program. | Relational set composition; neither representation has a semantic monopoly. | SQL: 7 interactions/12.7 KB/0 errors versus graph 10/20.9 KB/11 errors. |

**OBSERVED.** Large successful graph cases establish genuine expressiveness. They do not establish economic value. In several cases exactness came after substantial exploration, failed calls, guessed stable IDs, or multiple programs; it cannot be credited to a clean one-shot graph abstraction.

## FX06 and FX07: the intended reuse test

### SQL

**OBSERVED.** FX06 completed in 9 model/environment interactions, returned 22,484 visible bytes, and logged 115 SQL statements plus 64 result events. FX07 completed in 8 interactions, 13,552 bytes, and logged 273 statements plus 160 result events. Neither episode created a temporary table or view.

At the semantic level, one recursive CTE defining the legacy-dependent module set, followed by an affected-production-service relation, was sufficient. The final FX06 and FX07 query families repeated that CTE text under different final `SELECT`s rather than physically materializing it once across statements. FX07 also used many small exploratory/per-node statements.

**INFERRED.** SQL naturally expressed reuse as a shared relational definition, but the participant did not optimize physical reuse. It did not need to: a few large shell interactions kept the statement chatter inside the SQLite client process, and total model-visible material remained modest. This is an important distinction between database statement count and agent interaction count.

### Graph

**OBSERVED.** FX06 took 11 interactions, 27,315 visible bytes, 10 participant errors, and 225 seconds. It executed 48 successful graph-operation events. A successful `fx06_full` program bound a reverse dependency closure and reused it to construct affected services. Verification/uncovered/boundary reasoning occurred in separate programs; the attempted all-output program was invalid. There was no persistent named closure shared across graph calls.

FX07 took 12 interactions, 25,998 bytes, 4 participant errors, and 214 seconds, with 91 successful graph-operation events. A compact program genuinely bound the 300-node closure once and reused the affected-service set to emit affected services, deployments, and uncovered services. Boundary-sensitive services were obtained through separate boundary programs; the first four-output program was invalid.

In both cases, compact graph programs kept their large internal node sets server-side. That is a real property of the abstraction.

### Did reusable topology produce a concrete advantage?

**OBSERVED — no, not at the episode level.** The internal closure reuse was real, especially in FX07, but it did not reduce total model-visible material or interactions:

| Case | SQL interactions / bytes / wall | Graph interactions / bytes / wall |
| --- | --- | --- |
| FX06 | 9 / 22,484 / 99 s | 11 / 27,315 / 225 s |
| FX07 | 8 / 13,552 / 80 s | 12 / 25,998 / 214 s |

**INFERRED.** Programming and debugging the graph cost more than server-side reuse saved. The engineered best case for graph therefore yielded proof of capability, not proof of advantage.

## The non-monotonic dose response

**OBSERVED.** Performance did not worsen monotonically with structural burden:

```text
Depth/closure:       FX01 graph wrong → FX02 invalid → FX03 exact
Reuse:               FX14 graph wrong → FX06 exact → FX07 exact
Cyclic topology:     FX08 exact → FX09 invalid
```

The deepest depth case (FX03, closure 240) succeeded after the shallower cases failed. The large reuse case (FX07, closure 300) succeeded while the small control (FX14, closure 20) was wrong. A medium cyclic case succeeded while its larger sibling timed out.

**INFERRED.** Participant trajectory and API-program construction luck dominated topology burden in this one-run-per-cell campaign. Topology still affects execution once a valid program exists, but it did not predict whether the participant reached that program.

For an autonomous product, this is damaging. A representation that is excellent conditional on reaching its happy path but unreliable in reaching it has poor expected value. Tail failures matter more than elegant successful traces when an agent must operate without a human repairing its syntax and ontology.

## Negative and absence reasoning: FX10 and FX11

**OBSERVED.** The oracle answer was empty in both cases, and both prompts explicitly said the frozen task view was complete for the declared production dependency scope.

The SQL participant successfully computed large recursive legacy-dependent module closures. It then made an unsupported semantic move:

- in FX10 it explicitly added a fallback that treated remaining services as production-relevant when no service was deployed to the task-target deployment;
- in FX11 it used the same `OR NOT EXISTS` fallback and later omitted the production restriction, returning services deployed to production and staging.

Thus SQL found transitive legacy dependence but failed to respect the empty intersection with the declared production scope. Its answers were plausible positive sets, not absence proofs.

The graph participant repeatedly failed to reach service nodes within its chosen expansions, treated that as evidence of a missing/disconnected representation rather than the task's intended negative result, guessed identifiers, broadened traversal, and timed out. It did not construct and complete the exhaustive bounded closure plus production intersection required by the closed-world instruction.

**INFERRED.** Both participants failed to internalize the operational consequence of closed scope: after exhaustive computation, an empty intersection is the answer. SQL's failure was primarily reasoning, not representational inability. Graph combined the same reluctance to accept emptiness with API and traversal-bound uncertainty.

The distinction is subtle: the participants did not simply claim “no path found proves no path.” They did the opposite—they distrusted a negative computational result and kept inventing a positive interpretation or searching for omitted data. That is still a failure to use the supplied closed-world condition.

**INFERRED.** Absence proofs are exactly where external symbolic computation should help, yet neither representation converted that theoretical benefit into reliable behavior. Neither surface made “the declared finite scope has been exhausted; empty is terminal” a first-class proof object. SQL exposed enough power, but the model overrode the result. Graph made exhaustiveness harder to recognize because EMPTY could also mean wrong direction, wrong parameter dialect, hop bounds, truncation, or disconnected seeds.

**SPECULATIVE.** A typed `prove_empty(set_expression, closed_scope=...)` operator with an execution receipt might help more than either a generic graph API or generic SQL. This campaign did not test such an operator.

## Graph semantics, programming API, and physical backend

These are separate layers:

```text
logical graph semantics
        ↓
agent programming API
        ↓
physical execution backend
```

**OBSERVED.** Only one of the 135 graph participant-facing errors in the sealed r3 records was a LadybugDB `GraphInUseError`. The dominant errors were parameter names, semantic-predicate versus physical-edge-type confusion, bounds, invalid recipes, and excluded operations.

If the same graph operations were compiled over SQLite tables, the following would likely disappear or improve:

- Ladybug single-owner locking and process-lifecycle risk;
- some physical operation latency;
- deployment complexity from maintaining a second store.

The following would remain unless the agent-facing API changed:

- `from` versus `node_ids`/`source_ids`;
- `predicates` versus `edge_labels` versus physical `edge_types`;
- `id`/`kind` lookup assumptions;
- program vocabulary, bounds, result-shape, and composition errors;
- closed-world reasoning failures.

**INFERRED.** A SQLite-backed graph projection is scientifically worth testing only as the implementation of a conventional interface control. A dedicated “Ladybug versus SQLite graph backend” participant experiment has low information value because backend locking does not explain the dominant result.

## Counterfactual: a conventional graph interface

Suppose the participant had received:

```python
neighbors(nodes, relation="depends_on", direction="out")
reachable(seed, relation="depends_on", max_depth=8)
paths(source, target, constraints=...)
filter(nodes, kind="service", ...)
union(...)
difference(...)
```

**INFERRED.** This would remove a meaningful fraction of the observed graph tax. It directly accepts the vocabulary the participant repeatedly invented: singular/plural nodes, relation/predicate names as the logical edge selector, conventional source/target, and explicit set operations. It also removes the physical `leadsto` carrier from the task-facing ontology and collapses the direct/program dialect split.

It would not necessarily fix:

- failure to honor production and closed-world scope;
- choosing the wrong semantic computation;
- SQL's large pretrained familiarity advantage;
- the absence of a meaningful efficiency gain on these output sizes;
- retry variance unrelated to parameter names.

The two proposed hypotheses are not mutually exclusive.

- **H-interface: high confidence, about 85%.** Graph semantics may be useful, and graph-v1 is an unnatural agent interface. The recurring “wrong” forms and the surface's internal dialect split directly support this.
- **H-representation: moderate confidence, about 65%.** Even with a better graph API, SQL may already be reliable and economical enough that graph adds little product value. The paired-exact cases support this: graph had no total-cost win even when it eventually worked.

If forced to choose the better causal explanation for the observed graph failures, H-interface is better supported. If choosing what to build today, H-representation still controls the decision: do not build a new language until the conventional operator counterfactual demonstrates incremental value over SQL.

## SQL's pretrained familiarity is part of the result

**OBSERVED.** SQL produced zero participant-facing query errors across 14 episodes. The model freely used `WITH RECURSIVE`, joins, anti-joins, `NOT EXISTS`, subqueries, grouping, and Python's SQLite client. It sometimes wrote inefficient or semantically wrong SQL, but it did not struggle to address the language.

**INFERRED.** The campaign compares a mature ubiquitous language with a novel bespoke graph DSL at least as much as it compares relations with graphs. That limits any claim that relational semantics are intrinsically superior.

It does not make the product comparison unfair. Pretrained familiarity is a real deployment property. If an existing language already expresses the computation adequately, a new agent language must overcome both its implementation cost and its model-learning disadvantage. “The graph DSL would win after enough specialized training or scaffolding” is not a product advantage unless that training/scaffolding is cheaper and more reliable than using SQL.

## The remaining graph-shaped niche

| Candidate operation | Evidence from this campaign | Judgment |
| --- | --- | --- |
| Reachability / bounded closure | Positive expressiveness evidence in FX03, FX06–08, FX12; negative economic evidence versus SQL. | Worth one operator, not a whole language. |
| Cycle-safe reachability | FX08 graph exact and slightly smaller payload; FX09 graph timed out while SQL was exact. | Mixed, leaning negative for graph-v1; modest positive evidence for a visited-set closure primitive. |
| Ordered edge-label sequence | FX05 graph exact only after 31 errors and largely manual synthesis; SQL was direct and reliable. | Negative evidence for graph-v1; no clean test of an ideal `walk_sequence`. |
| Constrained paths / shortest paths | FX04 exercised constrained reachability, but the successful graph solution reduced to boundary set membership; many path calls elsewhere failed or were misdirected. | No meaningful evidence of an ideal primitive's advantage. |
| Bounded path enumeration | The tasks did not require returning a meaningful path family. | No meaningful evidence. |
| Cycle analysis as an output | Cycles existed, but detecting/explaining cycles was not the task. | No meaningful evidence. |
| Topological ordering | Not instantiated as a participant output. | No meaningful evidence. |
| Negative reachability proof | FX10/11 failed in both arms. | Negative evidence for both generic surfaces; potentially a niche for a proof-carrying operator. |

**INFERRED.** There is not enough demonstrated value to justify an entire graph-native programming surface. The rational design is a small library of graph operators over a relational Task IR, with SQL remaining the general escape hatch.

## Implications for Task IR

**OBSERVED.** This experiment did not compare Task IR with any alternative, so it provides no evidence that Task IR itself improves agent performance.

**INFERRED architectural judgment:**

| Option | Judgment |
| --- | --- |
| **A. Graph-native IR + specialized graph backend** | Deprioritize. It couples ontology, agent language, and storage to the weakest observed layer and adds operational complexity without a demonstrated benefit. |
| **B. Canonical relational IR / SQLite + arbitrary SQL + optional graph operators** | Best near-term choice. It exploits model familiarity, inspectability, source-grounding-friendly tables, mature execution, and complete expressive coverage while preserving explicit topology where useful. |
| **C. Representation-neutral logical IR compiled into task-dependent physical structures** | Best long-term boundary, but not the first implementation target. It avoids declaring graphs or tables to be the ontology. The danger is building a compiler architecture before proving that multiple physical projections pay for themselves. |
| **D. Typed relational Task IR with named-set algebra, proof receipts, and a tiny topology library** | My preferred concrete form of B, designed so it can evolve toward C. Entities, typed relations, classifications, constraints, claims, and provenance remain canonical relations; `reachable`, `paths`, `cycles`, and `toposort` are compiled operators; named sets and absence proofs have explicit receipts. |

This architecture is legible to agents, inspectable by humans, easy to ground to sources, suitable for heterogeneous Task-IR structures, and simpler to implement than a graph-native ontology plus specialized store. It also lets the physical planner choose recursive SQL, indexes, in-memory adjacency, or another structure without changing the language the agent sees.

## Kill and deprioritization decisions

**STOP:**

- trying to prove that specialized graph storage is faster for agent episodes;
- treating graph as the ontology of the product;
- extending graph-v1's bespoke direct/program vocabulary;
- spending participant budget on larger versions of the same scale ladders;
- treating successful execution after many repairs as evidence of good programmability;
- trying to solve FX10/11 merely with more graph documentation.

**CONTINUE:**

- relational externalization through a canonical, inspectable Task IR;
- arbitrary SQL as the mature general-purpose computation surface;
- a very small conventional graph-operator layer compiled over relational data;
- compact named answers, server-side intermediate computation, audit evidence, and explicit provenance—these are valuable independent of graph storage;
- research on proof-carrying empty results and closed-scope reasoning.

**UNKNOWN:**

- whether a conventional graph interface can beat SQL on constrained paths or reusable closure;
- whether real long-horizon SWE tasks create larger intermediate-state savings than these synthetic worlds;
- whether a proof-specific operator can make absence reasoning reliable;
- whether shortest-path, cycle explanation, or topological-order outputs form a commercially important workload.

## The single next participant experiment

### Causal question

Does graph semantics provide incremental agent value when backend and interface familiarity costs are controlled, or was graph-v1's deficit mainly an unnatural API layered over an otherwise useful representation?

### Arms

1. **SQL:** canonical relational Task IR in SQLite with arbitrary read-only SQL.
2. **Conventional graph operators:** the identical SQLite database, exposed only through `reachable`, `neighbors`, `paths`, `filter`, `union`, `intersection`, and `difference`, with complete JSON schemas and logical relation names. Operators compile to SQL; no physical carrier vocabulary is exposed.

Do not include LadybugDB and do not add a third graph-v1 arm. The current campaign already establishes graph-v1's product failure; the next experiment should decide whether any graph-language branch survives.

### Held constant

- identical canonical facts, row/index layout, SQLite process model, and resource limits;
- identical prompts, answer contracts, graders, oracle, model, context budget, timeout, and tool-result accounting;
- equal capability to compute compact named sets server-side;
- no orientation prose, search, landmarks, raw sources, or treatment-specific hints;
- randomized arm order and fresh sessions.

### Smallest useful case set

Use four diagnostic cases, with two independent participant trajectories per arm: 16 episodes total.

1. deep bounded reachability;
2. large four-output closure reuse;
3. ordered constrained path;
4. closed-world negative reachability.

Use new isomorphic worlds rather than exposing old answers. Two trajectories are the bare minimum because this campaign showed that happy-path acquisition, not topology size, can dominate a single run.

### Primary outcomes

Rank these in advance:

1. exact named-set correctness;
2. valid completion before timeout;
3. first-valid-program rate and parameter/schema repair count;
4. total model/environment interactions;
5. total model-visible bytes;
6. wall time as a secondary operational measure.

### Decision rules

- **Kill H-interface**—the claim that only graph-v1's interface was the problem—if the conventional graph arm still has materially lower validity/exactness than SQL, a median repair count above one, or no efficiency win in either the reuse or path case.
- **Kill H-representation**—the claim that SQL is already good enough and graph adds no value—only if the conventional graph arm matches SQL on every exact/valid cell and reduces interactions or visible bytes by at least 25% in both the reuse and ordered-path cases across both trajectories.
- **Terminate the broad graph-language branch** if neither demanding condition is met. A result of “rough parity with nicer syntax” is insufficient to justify a second general-purpose language.

This experiment has higher information value than a Task-IR-versus-generic-index study right now because it can close the immediate graph representation branch with only 16 episodes. Task IR deserves a separate experiment after its default computational substrate is chosen.

## If this were my project

1. **What happened?** Graph-v1 represented the hard computations, but the model repeatedly tried to turn it into a conventional graph API. When it found the happy path, it could run large closures and named-set algebra server-side. Reaching that path was unreliable and expensive. SQL benefited from both a good relational projection and enormous pretrained familiarity.

2. **What survives?** Explicit topology can be useful as an operator-level abstraction. Compact named outputs, server-side intermediates, provenance, and execution receipts also survive—but none requires a graph-native store or language.

3. **What should be abandoned?** Graph as product ontology, graph-v1 as the primary programming surface, and specialized graph storage as the main performance thesis.

4. **What is the strongest remaining thesis?** A task-conditioned, source-grounded relational IR with named sets and proof receipts, SQL as the universal escape hatch, and a tiny conventional topology library compiled over the same data.

5. **Where would I spend the next £1,000 of model inference?** On the 16-episode same-SQLite SQL-versus-conventional-graph-operator experiment above, reserving enough for adjudication or replacement of an invalid infrastructure cell. Its purpose is to kill or retain the entire optional graph-language branch.

6. **Where would I refuse to spend it?** On graph-v1 documentation-only reruns, Ladybug-versus-SQL speed comparisons, bigger synthetic closure ladders, or another single-trajectory campaign whose successful cells can be explained by eventually guessing the API.
