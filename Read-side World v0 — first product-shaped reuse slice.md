# Read-side World v0 — first product-shaped reuse slice

We are beginning implementation of the minimal read-side product built on the existing semantic-integration research kernel.

Do not turn this into a general platform.

Do not modify or overwrite any sealed research results.

## Product thesis

The product is:

> A local, read-only semantic data layer that integrates heterogeneous authoritative sources into grounded, reusable, computable world state.

Its core value hypothesis is:

> Cross-source meaning can be constructed once and reused across multiple analyses instead of being reconstructed independently for every question.

This milestone should make that hypothesis concrete using the existing BOM domain.

---

# Goal

Construct the existing BOM semantic world once, then support multiple independent read-side analyses over that same compiled world.

The result should feel like the beginning of a product rather than another isolated experiment, but remain extremely small.

No actions or write-back.

---

# Existing research must remain unchanged

Preserve:

- existing C0 results;
- C1 reports;
- scaling results;
- C2 live campaign;
- operational-frontier experiment;
- TaskView implementation;
- semantic-integration kernel behavior.

Do not regenerate or overwrite any sealed artifacts.

New outputs must use new paths.

---

# Product boundary

Treat one local directory as a World workspace.

Create a minimal experimental workspace under a new path such as:

```text
research/semantic_integration/readside_v0/
```

or another clearly non-product path consistent with repository conventions.

Do not migrate the repository wholesale to a new folder structure yet.

The workspace should reference/reuse the existing BOM compiler and compiled semantic state rather than copying its implementation.

---

# Required read-side operations

Expose the smallest reasonable Python and/or CLI-style surface for:

```text
build/open world
list relations
query SQL
inspect/explain a semantic tuple
list stale relations
list unresolved semantic obligations if available
show construction-origin account
```

Prefer wrappers over the existing `SemanticWorld` methods.

Do not add a second storage abstraction.

Do not hide the existing SQL surface.

---

# `explain` requirement

Provide a useful read-side explanation for an assertion.

For a tuple such as:

```text
acceptable_replacement(
    part:R210,
    part:R200,
    context:high_vibration_cabinet
)
```

the output should expose at least:

```text
relation
role values
construction origin
grounding/source pointers
construction method if recorded
current/stale information that is actually available
```

Do not synthesize an LLM explanation.

This must be deterministic inspection of stored state.

---

# Multi-purpose reuse slice

Use one compiled BOM world as the input to at least three distinct read-side analyses.

Choose analyses supported naturally by the existing fixture and vocabulary.

Candidates include:

```text
A. replacement readiness / viable replacements

B. specification-conflict audit

C. lifecycle, sourcing, compatibility, or engineering-risk analysis
   only if supported by the existing fixture
```

Do not add artificial source facts solely to create a third analysis.

If the existing fixture cannot support a meaningful third analysis, implement two strong analyses and state the limitation.

Each analysis should be expressed primarily as SQL/relational computation over World state.

Do not call an LLM.

---

# Reuse accounting

For each analysis, record:

```text
relations consumed
mechanical assertions reused
semantic assertions reused
derived assertions reused
source files that the consumer itself needed to access directly
```

The desired consumer behavior is:

```text
direct raw-source access = 0
```

after World construction.

Also record common relations/assertions reused by more than one analysis.

This is not yet a full economic study.

It is a structural reuse study.

---

# Raw-source comparison

For each analysis, briefly identify what reconciliation or semantics would have to be reconstructed if the analysis were implemented directly against raw fixture sources.

Do not fabricate token or monetary savings.

Classify this concretely, for example:

```text
identifier reconciliation
cross-source relation
context interpretation
conflict handling
semantic replacement judgment
```

The report should distinguish:

```text
MEASURED
from repository execution

STRUCTURAL OBSERVATION
from inspecting dependencies

HYPOTHESIS
about future economic value
```

---

# No new ontology abstractions unless forced

Do not add:

```text
ObjectType
Metric
Action
Workflow
Dashboard
Agent
UniversalProvider
GenericSelector
```

or similar abstractions.

Use the current relational kernel.

If ergonomics are awkward, document them instead of immediately fixing them.

We want the first real consumer usage to tell us what API is missing.

---

# No actions

This product branch is explicitly READ-SIDE.

Do not implement:

```text
external mutations
approval workflows
write-back
action types
operational commands
```

The world may be rebuilt/rerun from changed evidence as already supported, but it does not take business actions.

---

# Output

Produce:

```text
README/report describing Read-side World v0
the minimal executable read interface
2–3 example analyses
example deterministic `explain`
reuse-accounting report
focused tests
```

The report must answer:

1. What does a user get after compiling a World?
2. What analyses became ordinary SQL/relational computation?
3. Which semantic relationships were reused across analyses?
4. Did any analysis need to reopen raw sources?
5. What semantics would otherwise have to be reconstructed separately?
6. Which current kernel ergonomics are awkward for a real consumer?
7. What functionality was deliberately excluded?
8. Does this result provide evidence of reuse, or only a product-shaped demonstration?

Be conservative on the final question.

---

# Stop condition

Stop after the first usable read-side slice exists and the reuse report is written.

Do not:

- generalize source adapters;
- add a second domain;
- run provider inference;
- build automatic ontology authoring;
- redesign invalidation;
- create UI;
- modify TaskView;
- productize beyond this local experimental slice.