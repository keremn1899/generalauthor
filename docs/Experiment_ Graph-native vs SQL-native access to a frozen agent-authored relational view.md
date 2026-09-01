# Experiment: Graph-native vs SQL-native access to a frozen agent-authored relational view

**Status:** design specification for implementation discussion.  
**Purpose:** mechanism identification following the seed-53 and seed-54 exploratory results.

## 1. Motivation

The preceding clean experiments produced a recurring H0/R8 pattern:

```text
seed 53:
A native       6/8
B SQLite       6/8
C Graphauthor  8/8
D optional     6/8

seed 54:
A native       6/8
B SQLite       6/8
C Graphauthor  8/8
D optional     6/8
```

This is exploratory evidence for the **forced-C treatment bundle**, not for graph topology or graph runtime specifically.

The existing B/C comparison is causally ambiguous. The two arms differ in more than representation:

```text
B:
generic SQLite construction requirement
+ agent-selected extraction
+ SQL access

C:
Graphauthor construction process
+ agent-selected extraction
+ graph representation
+ graph-native access
```

The agents may therefore construct different relational worlds before they ever query them.

The next experiment deliberately asks a narrower question.

> **Once an agent-authored relational view exists, what does graph-shaped access itself buy?**

The experiment must not attempt to simultaneously test graph construction, autonomous representation choice, persistence economics, or sequential amortization.

---

# 2. Primary causal question

Given the **same frozen relational knowledge**, does exposing that knowledge through a graph-native programming model improve agent task execution relative to exposing it through an idiomatic SQL-native relational model?

Formally, for a frozen canonical relation set \(R\):

\[
R_S = R_G
\]

where:

- \(S\) receives an idiomatic SQL-native representation of \(R\);
- \(G\) receives an idiomatic graph-native representation of \(R\).

The primary estimand is:

\[
\Delta_{\text{accuracy}}
=
Accuracy_G - Accuracy_S
\]

Secondary estimands include differences in tool calls, wall time, token usage, source fallbacks, and performance by relational operation class.

This is **not** a comparison of physical database engines.

The independent variable is the **agent-facing computational representation and access model**.

---

# 3. Central experimental invariant

## Same semantics, different native programming models

The experiment must establish semantic parity without forcing encoding parity.

A single upstream process produces a representation-neutral canonical relation set such as:

```yaml
entities:
  - id: service:a
    kind: service
  - id: service:b
    kind: service

facts:
  - subject: service:a
    predicate: depends_on
    object: service:b
    evidence: ...
```

That artifact is then:

1. frozen;
2. hashed;
3. audited;
4. deterministically compiled into the two treatment representations.

No model participates in the S/G conversion.

Therefore:

```text
raw source world
        │
        ▼
upstream builder agent
        │
        ▼
canonical relational view
        │
     freeze/hash
        │
        ├─────────────────────┐
        ▼                     ▼
deterministic SQL        deterministic graph
materialization          materialization
        │                     │
        ▼                     ▼
fresh S executor         fresh G executor
```

The task executors never independently reconstruct their respective worlds.

This is essential.

> Do not ask two independent agents to “construct the same database/graph” and describe the resulting comparison as matched construction.

---

# 4. Why the canonical intermediate representation exists

The canonical representation is an **experimental interchange format only**.

It should not itself become an agent-facing product abstraction.

Its purpose is to guarantee:

\[
Facts_S = Facts_G
\]

and:

\[
Evidence_S = Evidence_G
\]

before execution begins.

It should be deliberately boring and representation-neutral:

```text
entity
entity type
subject
predicate
object
evidence/source reference
```

It must not contain graph-specific conveniences such as:

- adjacency lists;
- precomputed reachability;
- shortest paths;
- inverse-edge indexes exposed as semantic facts;
- traversal hints;
- graph landmarks;
- summaries optimized for graph reasoning.

Likewise it should not contain SQL-specific conveniences beyond what is necessary to faithfully compile the same semantic world.

---

# 5. Upstream agent-authored construction

The relational view should remain **agent-authored**.

For each generated experimental case:

```text
case
 ↓
builder agent
 ↓
source exploration
 ↓
agent-authored extractor / construction
 ↓
canonical relation set
 ↓
freeze
```

The builder must be upstream of downstream treatment assignment.

It must not know whether the resulting view will later be consumed through SQL or a graph interface.

This prevents construction from being implicitly optimized for either treatment.

The builder output should retain:

- canonical entities;
- canonical relations;
- evidence/provenance;
- source scope;
- construction program/extractor where applicable;
- build receipt;
- content hash.

The same frozen build is consumed by both downstream arms.

---

# 6. Construction quality is measured, not silently assumed

For every oracle-relevant relation \(r\), record:

\[
D_r =
\text{relation was discovered during construction}
\]

\[
P_r =
\text{relation is present in frozen materialization}
\]

The S and G arms necessarily have identical \(P_r\), because both compile from the same frozen relation set.

Construction coverage should be reported separately from downstream task performance.

At minimum record:

\[
Coverage =
\frac{\text{oracle-relevant relations represented}}
{\text{oracle-relevant relations}}
\]

Do not silently repair missing relations differently for S and G.

Do not use downstream task success to decide whether a build was admissible.

If a minimum construction-admission rule is required operationally, define it mechanically and preregister it before execution.

The cleanest downstream analysis may additionally report the subset of cases with 100% oracle-relevant relation coverage.

---

# 7. Treatment S — SQL-native relational access

The SQL treatment must be an **idiomatic relational representation**, not a graph API implemented on SQLite.

Bad design:

```sql
relations(
    src TEXT,
    predicate TEXT,
    dst TEXT
)
```

combined with experimenter-provided helpers such as:

```text
neighbors()
expand()
traverse()
path()
```

That would largely preserve the graph programming model while merely changing its implementation language.

The experiment would then risk concluding that “SQLite performs as well as graphs” after giving SQLite a graph abstraction.

Instead, compile the canonical relation set into a schema natural for relational querying.

Illustratively:

```sql
services(...)
teams(...)
runbooks(...)

service_dependencies(
    service_id,
    dependency_service_id
)

service_owners(
    service_id,
    team_id
)

runbook_coverage(
    runbook_id,
    service_id
)
```

Exact schema design may depend on the experimental world.

The governing principle is:

> The SQL representation should express the same semantic facts through a normal relational schema.

The S agent receives ordinary SQL capabilities:

- schema inspection;
- SQLite access;
- arbitrary SELECTs;
- joins;
- recursive CTEs;
- aggregation;
- indexes if agent-created indexing is ordinarily allowed;
- ordinary host-language code if available under the benchmark envelope.

Do **not** cripple SQL.

If the agent chooses to implement recursive graph logic itself using SQL or Python, that is permitted.

The cost of doing so is part of the measured treatment.

The experimenter must not provide that abstraction in advance.

---

# 8. Treatment G — graph-native access

The graph treatment receives the exact same semantic facts through the actual graph-shaped programming surface being tested.

Illustratively:

```text
lookup
neighbors / expand
traverse
path
```

or the smallest current Graphauthor graph-access surface that genuinely represents the intended product.

The graph treatment may expose:

- typed nodes;
- typed directed edges;
- adjacency;
- bounded traversal;
- paths;
- graph-native filtering/composition;

provided these operations are genuinely part of the graph programming model being evaluated.

The graph arm must not receive semantic information unavailable to S.

---

# 9. Semantic parity audit

Before execution, mechanically verify that S and G encode the same canonical world.

For every canonical entity and relation:

```text
canonical fact
    ↓
present in SQL?
present in graph?
same direction?
same predicate meaning?
same evidence?
```

The audit should detect at least:

- missing entities;
- missing relations;
- extra relations;
- reversed orientation;
- predicate remapping errors;
- evidence mismatches;
- duplicated or collapsed entities.

The two downstream treatments should not begin unless the parity audit succeeds.

---

# 10. No hidden graph advantages

The graph treatment must not receive additional derived semantics unless the SQL treatment receives semantically equivalent information.

Examples that would violate isolation if graph-only:

- precomputed transitive closure;
- automatic blast-radius sets;
- graph-specific summaries;
- additional inferred edges;
- hidden inverse predicates;
- task-specific landmarks;
- automatically selected traversal roots;
- extra provenance;
- richer semantic typing.

If Graphauthor normally computes such information, exclude it from this experiment or expose the equivalent semantic information to S.

Those capabilities can be tested separately later.

The present experiment concerns **graph-shaped access to the same relational world**.

---

# 11. No hidden SQL-to-graph wrapping

The inverse contamination must also be prevented.

Do not provide S with experimenter-authored abstractions equivalent to:

```text
neighbors(entity)
incoming(entity)
reachable(a, b)
path(a, b)
expand(frontier)
```

merely implemented over SQLite.

This would test implementation substrate rather than programming representation.

The distinction is:

```text
allowed:
agent independently realizes it needs traversal
→ writes recursive SQL/Python
→ pays measured cost

not allowed:
benchmark provides traversal abstraction
→ calls it "SQLite"
```

---

# 12. Raw-source access

The primary experiment should prevent arbitrary raw-source exploration from washing out the representation contrast.

Relational operations tested by the benchmark should be answerable from the frozen relational view.

However, some task-local payload may legitimately require source access.

Both treatments should therefore receive the same narrow escape hatch, for example:

```text
fetch_source(entity_id)
```

or an equivalent bounded evidence-fetch mechanism.

They should not receive unrestricted repository grep/search during the primary mechanism test unless the existing workload makes this unavoidable.

Every fallback should be recorded.

Define:

\[
F_S =
\text{raw-source fallbacks in SQL arm}
\]

\[
F_G =
\text{raw-source fallbacks in graph arm}
\]

A difference in fallback behavior may itself be mechanistically informative.

If unrestricted source access must remain available for compatibility with the workload, log it precisely and treat source fallback as an important secondary outcome.

---

# 13. Workload

The mechanism experiment should concentrate on the region where the previous experiments actually discriminated:

```text
H0 / R8
```

R1 is saturated and contributes little information.

H2 produced successful alternative strategies in seed 54 and is less useful for initially identifying the graph-vs-SQL mechanism.

Prefer additional fresh H0/R8-like cases over recreating the full H0/H2 × R1/R8 factorial.

The cases should preserve the existing task family and evaluator semantics as much as possible so this experiment remains connected to the replicated exploratory effect.

Use fresh generated cases/seeds.

Do not hand-author tasks specifically to favor graph traversal.

---

# 14. Relational operation taxonomy

Each scored operation should be labeled offline by its dominant relational shape.

Possible classes include:

```text
direct lookup
inverse lookup
join
fan-out
fan-in
intersection
multi-hop reachability
path finding
exhaustive enumeration
mixed relational/source-local
```

This taxonomy must not be shown to participants.

The purpose is to determine whether any treatment difference is concentrated in graph-shaped operations rather than spread uniformly across task types.

A particularly informative result would be:

```text
SQL ≈ graph:
  lookup
  ordinary join

graph > SQL:
  multi-hop reachability
  paths
  repeated fan-out
  intersections
```

Such a result would be substantially more useful than a single aggregate score difference.

---

# 15. Relation-use instrumentation

For each oracle-relevant relation \(r\), distinguish:

```text
discovered
persisted
used
```

Construction determines the first two.

Execution instrumentation should conservatively record the third when visible tool/query events establish use.

Define:

\[
U_r =
\text{relation visibly used during task execution}
\]

Lack of an observed use event must not be interpreted as proof the agent did not reason about the relation internally.

Where possible, retain:

- SQL query text;
- graph operation calls;
- returned entity/relation IDs;
- source fetches;
- operation ordering.

This supports post hoc mechanistic analysis without relying on hidden reasoning or self-report.

---

# 16. Arms

The smallest critical experiment is:

| Arm | Frozen relational knowledge | Agent-facing access |
|---|---|---|
| S | identical canonical view | SQL-native relational |
| G | identical canonical view | graph-native |

An optional native baseline A may be retained for continuity with earlier experiments:

| Arm | Frozen relational knowledge | Agent-facing access |
|---|---|---|
| A | none | existing native/raw tools |

However:

\[
G-S
\]

is the critical causal contrast.

The experiment should not become unnecessarily large merely to preserve historical factorial structure.

A construction-only arm can be considered later if needed to decompose the original C treatment further.

---

# 17. Primary outcomes

## 17.1 Task correctness

Primary:

\[
Accuracy_G - Accuracy_S
\]

Report operation-level outcomes, not only whole-episode success.

## 17.2 Cost

Record at minimum:

- wall-clock time;
- model/tool calls;
- token usage if available;
- SQL or graph query count;
- source fallback count;
- execution failures/timeouts.

Construction cost is upstream and identical for S/G within a case.

Therefore downstream execution cost can be compared separately from initial materialization cost.

## 17.3 Operational reliability

Record valid execution rate separately from correctness conditional on valid execution.

Do not erase failed trajectories by considering only successful attempts.

---

# 18. Interpretation table

The experiment should be designed so that the major possible outcomes have clear interpretations.

### Outcome A

\[
G > S
\]

with identical relational knowledge.

Supported interpretation:

> Graph-native access provides an execution advantage over idiomatic SQL-native access for this relational workload.

This would justify further investigation of which graph operations produce the advantage.

It would still not establish that graphs are universally better, cheaper, or autonomously selected.

---

### Outcome B

\[
G \approx S > native
\]

Supported interpretation:

> The valuable primitive is likely explicit relational materialization rather than graph-native access specifically.

This would weaken the case for graph runtime as the core product while strengthening the broader relational-materialization thesis.

---

### Outcome C

\[
G \approx S
\]

and both fail similarly despite high canonical coverage.

Supported interpretation:

> The recurring original C advantage probably came from some other part of the Graphauthor treatment bundle, such as construction procedure or source coverage.

The next experiment should then isolate construction.

---

### Outcome D

The original Graphauthor construction repeatedly produces better oracle-relation coverage than generic construction, but S/G perform similarly once facts are held constant.

Supported interpretation:

> Construction/coverage is the likely earned primitive; graph topology is incidental.

This would be an important positive mechanism result even though the graph-vs-SQL comparison itself is null.

---

### Outcome E

\[
G > S
\]

specifically on path/reachability/fan-out operations while direct lookups and joins are similar.

Supported interpretation:

> The advantage is associated with graph-shaped relational computation rather than a generic quality difference between arms.

This would be particularly strong evidence for the product's graph-native layer.

---

# 19. Explicit non-claims

This experiment does **not** establish:

- autonomous graph selection;
- spontaneous materialization;
- graph construction quality;
- sequential amortization;
- long-lived persistence value;
- maintenance economics;
- graph database engine superiority;
- universal graph superiority over SQL;
- product latency superiority;
- graph-specific value outside the tested relational operation family.

Those are separate questions.

---

# 20. Why this experiment matters

The current evidence leaves several competing explanations for the recurring forced-C advantage:

```text
1. Graphauthor discovers more relevant relations.

2. Explicit relational materialization helps,
   regardless of graph vs SQL.

3. Graph-native traversal helps agents use
   the same relational information more effectively.

4. Some interaction among construction,
   representation, and execution produces the gain.
```

The current experiment isolates explanation 3.

The falsifiable thesis is:

> **Once relational knowledge is held constant, graph-shaped access only earns a product role if agents can exploit it more effectively than an idiomatic SQL representation of the same knowledge.**

A null result is therefore informative rather than a failed experiment.

If SQL performs equally well once it has the same facts, the project should not preserve graph machinery merely because graphs are conceptually attractive.

If graph-native access continues to outperform SQL under exact semantic parity, the project has isolated a substantially stronger and more specific property than the existing forced-Graphauthor result.

---

# 21. Implementation questions to resolve before preregistration

Before converting this document into an executable preregistration, inspect the existing harness and decide:

1. What exact H0/R8 workload generator should be retained?
2. How should the upstream builder be invoked without downstream-treatment leakage?
3. What representation-neutral canonical format is smallest and sufficient?
4. What mechanical parity checks are required?
5. What is the most idiomatic SQL schema for the current semantic world?
6. What exact graph-native surface should G expose?
7. Which Graphauthor conveniences must be disabled because they add semantics rather than access?
8. What raw-source escape hatch is genuinely necessary?
9. What tool/query events can be instrumented reliably?
10. What oracle information is available for relation-coverage scoring without leaking to participants?
11. What sample size is affordable if the experiment concentrates only on H0/R8?
12. What exact criteria distinguish apparatus failure from treatment failure?

Do not implement until these questions are resolved against the current repository.

---

# 22. Design invariant summary

The experiment should remain reducible to:

```text
one source world
        ↓
one upstream agent-authored relational materialization
        ↓
one frozen canonical semantic state
        ↓
        ├─────────────────────────┐
        ▼                         ▼
idiomatic SQL-native         idiomatic graph-native
representation              representation
        │                         │
        ▼                         ▼
fresh identical model       fresh identical model
        │                         │
        └──────────┬──────────────┘
                   ▼
          same task + oracle
```

The two executor arms must differ in **how the same relational world is naturally programmed**, and in as little else as possible.

That is the experiment.