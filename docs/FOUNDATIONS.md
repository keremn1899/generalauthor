# Ontology Author foundations

This note records the design principles that currently define Ontology Author.

It is intentionally smaller than the research vision around the product. These
are constraints on the product we have now, not commitments to a future
agent-memory or ontology-lifecycle system.

## 1. What a World is

A **World** is a purpose-relative semantic abstraction over available evidence.
It preserves the distinctions needed for a declared class of work while
remaining explicit about meaning that the evidence does not establish.

A World is not intended to be a maximally faithful model of reality or a
universal ontology of a workspace.

A useful test for abstraction sufficiency is:

> Could two situations represented identically by this World require different
> correct outcomes for its declared purpose?

If yes, the World is too coarse for that purpose.

Purpose therefore does more than filter an already complete body of knowledge.
It helps determine the conceptual carving itself: what needs a referent, which
distinctions must survive, which relations matter, which uncertainties matter,
and what it means for construction to have done enough.

## 2. Truth is not purpose-relative; representation is

Purpose does not make incompatible facts true.

Two source entities do not become literally identical because one purpose can
safely abstract over their distinction. A World may introduce a coarser
purpose-level referent while another World over the same evidence preserves a
finer distinction.

Different Worlds may therefore be different valid conceptualizations of the
same evidence without being competing attempts to discover one canonical
ontology.

Shared or overlapping grounding across Worlds does not imply World-level
conceptual identity.

## 3. Local closure, global openness

A World can have a principled stopping condition because its obligations are
purpose-relative.

The useful closure question is not:

> Have we represented everything relevant about the workspace?

It is:

> Given this purpose and the available evidence, have we represented the
> distinctions currently required by the purpose, or made the missing ones
> explicitly unresolved?

A World may therefore close locally while the universe of future purposes
remains open.

Future work can arise from regulations, incidents, customers, organizational
change, new products, new tools, or questions that were not foreseeable during
construction. The same evidence may later need a different conceptual carving.

A useful maxim is:

> **A World should be able to finish. The possible set of Worlds never does.**

## 4. Hard semantic boundary, free intelligence

Ontology Author separates free intelligent construction from a narrow durable
semantic boundary.

```text
PURPOSE + WORKSPACE
        ↓
capable coding agent
        ↓
free construction / exploration / programming
        ↓
validated semantic boundary
        ↓
sealed World
        ↓
SQL / Python / agents / inspection
```

The product should constrain durable output where objective validation is
possible rather than prescribing how a capable agent must reason.

The semantic kernel defines an admissible language for grounded
conceptualizations; it does not define the one correct conceptualization.

The current core remains intentionally small:

- referents;
- named typed n-ary relations;
- assertions;
- grounding;
- deterministic derivations;
- construction origin and assertion origin;
- revision and relation-level staleness;
- WORLD / PURPOSE scope;
- scoped completeness;
- explicit unresolvedness.

Do not add a semantic primitive because a construction workflow is awkward.
A kernel change should be justified by a concrete correctness case that cannot
be represented honestly with the existing boundary.

## 5. Construction is mutable; Worlds are sealed

The public lifecycle remains:

```text
construction state
mutable, conversational, agent-authored
        ↓
validation
        ↓
World
sealed, read-only, reusable semantic state
```

A consumer does not mutate a sealed World. Changed meaning enters through
construction and rebuild.

A failed rebuild must not corrupt the current World.

This boundary is useful for later refinement as well: if use exposes a missing
distinction, the response is to revise construction and produce a new World
revision, not to edit semantic truth in place.

## 6. Unresolvedness and completeness are first-class

Missing positive assertion is not denial.

An empty query result supports a negative conclusion only when a declared
completeness scope licenses that conclusion.

Unsupported meaning should remain unresolved rather than becoming convenient
durable truth.

Unresolvedness is purpose-relative: a World need not enumerate every unknown in
the workspace, only unresolved distinctions that matter to its declared work.

Grounding makes semantic commitments auditable. It is evidence for why the
World committed to a proposition, not a proof that the proposition is
infallible.

## 7. Purpose is natural language, not an ontology DSL

`PURPOSE.md` is the durable articulation of what the World exists to support.
It may state important distinctions that the World must preserve, but it should
not prescribe relation names, schemas, mappings, or ontology structure.

The agent remains free to choose a conceptualization that satisfies those
semantic obligations.

Purpose can be refined through conversation when later work reveals that it was
underspecified. That does not imply that Ontology Author itself should contain a
purpose-planning engine.

## 8. Ontology Author is the persistence substrate, not the lifecycle intelligence

The coding agent does the interpretive and strategic work.

Longer-term agent workflows may eventually decide:

- whether semantic work is worth persisting;
- whether an existing World is relevant;
- whether it is sufficient for a new task;
- whether construction should be refined;
- whether a materially different purpose deserves another World;
- whether repeated semantic reasoning should become ordinary deterministic
  software.

Those are intelligence and workflow questions. They should not be encoded into
the kernel unless experiments demonstrate a missing semantic primitive.

A useful division is:

```text
agent workflow
  notices consequential distinctions
  exercises judgment
  decides what deserves persistence
          ↓
Ontology Author
  gives selected semantic interpretation a grounded,
  testable, programmable, reusable form
          ↓
future work
```

## 9. Multiple Worlds are allowed to disagree in carving

One project may contain several Worlds over overlapping evidence.

They may differ in identity grain, vocabulary, relations, event structure, and
other representational choices because their purposes preserve different
observable distinctions.

Do not force them toward one global ontology merely because they touch the same
source entities.

Future cross-World tooling may expose shared grounding or source
correspondence, but source correspondence is weaker than conceptual equality.

## 10. Sufficiency before minimality

The immediate target is a useful, grounded, purpose-sufficient World.

Exact minimality is not required. Construction can begin with a plausible
abstraction and become finer when use demonstrates that a consequential
distinction was lost.

Likewise, absence of demand for a distinction is not sufficient reason to
assert that the distinction is globally irrelevant.

When future needs are unknown, preserving or introducing a distinction is safer
than asserting an unsupported equivalence.

## 11. Product boundary

Ontology Author is a local semantic compilation and persistence layer.

It is not, by default:

- a universal enterprise ontology;
- a workflow engine;
- an autonomous agent-memory policy;
- a source-acquisition or exhaustive context-discovery system;
- a write-back system;
- a global entity-reconciliation service;
- a requirement that consumers reason only through the World.

Retrieval, raw evidence inspection, ordinary code, SQL, Python, and other agent
tools remain available. A World is useful when durable semantic interpretation
is worth carrying forward.

## 12. Current design discipline

When considering a future feature, first ask:

> Does this strengthen the durable semantic substrate or make that substrate
> materially more legible to capable consumers?

If not, it probably belongs in the surrounding agent workflow or in an
application built on top.

And when research reveals a new failure, diagnose it before changing the
kernel. The failure may instead be in construction, representation choice,
consumer interpretation, information access, or model reasoning.

Research hypotheses, open questions, and staged experiments are recorded
separately in [`RESEARCH_DIRECTION.md`](RESEARCH_DIRECTION.md). That note is
not product specification.
