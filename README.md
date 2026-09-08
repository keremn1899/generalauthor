# Ontology Author

Ontology Author lets coding agents construct and maintain purpose-fit
ontologies from the evidence in your workspace.

The resulting ontology is a **World**: grounded, programmable semantic state
that can be queried with SQLite or Python, reused by future agents, and
inspected locally.

Ontology Author is a local semantic compilation layer. The coding agent does
the interpretive work in conversation; Ontology Author gives that work a
durable, testable, computational form.

## Why a World?

Many repository questions are not just retrieval questions. Before an agent
can answer them reliably, it may need to reconcile identity across files,
determine which relationships apply, preserve distinctions between sources,
and represent what the evidence does not establish. Without durable semantic
state, each new task repeats that work:

```text
question
  → reopen sources
  → reconcile identities
  → reconstruct semantics
  → answer
```

With a World, that work can become reusable project state:

```text
workspace evidence + purpose
  → conversational semantic construction
  → World

later questions
  → SQLite / Python / agent reasoning over the World
```

This does not replace retrieval. Retrieval remains useful for finding and
checking evidence. The difference is that the semantic interpretation needed
for recurring work can be compiled once and computed over many times.

## Quickstart

The conversation with a coding agent is the control plane. Install Ontology
Author, attach it to the harness you use, and ask the agent normally.

The package is not yet published to PyPI. Install the current repository
checkout with [uv](https://docs.astral.sh/uv/):

```bash
git clone https://github.com/keremn1899/generalauthor.git ontology-author
cd ontology-author
uv tool install .
```

From the project you want the agent to understand, attach the capability to
one or more supported coding-agent harnesses:

```bash
author attach cursor
author attach codex
author attach claude
```

Then ask for semantic work in ordinary conversation. For example:

```text
Build a World for understanding support entitlements in this repository,
including subscriptions, policy, negotiated terms, and unresolved identity.
```

The agent can inspect the workspace, discuss ambiguities, author construction
code, run checks and queries, revise its interpretation, and rebuild the
World across subsequent turns. It does not need a schema supplied as a CLI
form or a one-shot compiler invocation.

When construction is ready, inspect the result locally:

```bash
author open
```

If the project contains several Worlds, name the one to open:

```bash
author open support-entitlements
```

The deterministic commands are useful implementation primitives for the
attached agent:

```bash
author create support-entitlements
author rebuild support-entitlements
```

`author create` initializes a project-local World directory. `author rebuild`
constructs and validates a new candidate, then replaces that World only when
validation succeeds. `author list` is available as a small discovery
convenience.

## What a World contains

A World is a purpose-fit ontology represented with:

```text
referents
named typed n-ary relations
assertions
deterministic derivations
```

It also retains semantic state needed to interpret and maintain those
relations:

```text
grounding · construction origin · revision · staleness
completeness · WORLD / PURPOSE scope · explicit unresolvedness
```

### Referents

Referents are stable handles, not property-bearing objects. A referent can
identify a customer, service, contract, or other entity without pretending
that all of its meaning belongs in one object record. Meaning is expressed by
relations involving that handle.

### Relations

Relations are named and typed, and may have any arity. A relation can connect
two referents, describe a referent with scalar values, or express a higher-arity
claim involving several entities. This keeps the model from forcing every
meaning into either node properties or binary edges.

### Grounding

World assertions retain compact grounding references to the evidence and
construction context that support them. Grounding makes a semantic commitment
auditable; it is not a claim that the system has mathematically proven the
commitment true. Source content remains in the project workspace rather than
being copied into every World.

### Derived meaning

Relations may be derived deterministically from other relations using ordinary
read-only SQL. The World records derivation inputs, execution state, and
completeness. If an input changes, dependent derived state becomes stale and
can be rebuilt.

### Open-world semantics

Absence is not automatically false. An empty query result supports a negative
conclusion only when an explicit completeness claim establishes that the
relevant universe was completely considered. Otherwise, the result may simply
mean that the World does not currently establish the requested tuple.

### Unresolved meaning

When the evidence does not support a conclusion, construction can preserve
that fact as explicit unresolved state rather than guessing. Unresolvedness is
relative to the World’s purpose: a World records the distinctions needed for
its declared work, not every possible uncertainty in the workspace.

## Purpose and construction

Every World has a purpose established in conversation. The attached agent
persists its current interpretation in `PURPOSE.md`. That document is natural
language, not a form, schema, or DSL. It normally contains a concise synthesis
of the purpose and exact user quotations that materially establish or refine
it.

The principle is simple: a World should represent the meaning needed for its
purpose while remaining honest about what the evidence does not establish. It
is not intended to be a universal ontology of the repository.

Construction is free-form and agent-authored. The hard boundary is the World
that consumers receive, not a prescribed reasoning workflow:

```text
conversation + workspace
        ↓
purpose + construction
        ↓
temporary candidate
        ↓
validation
        ↓
world/
```

Everything outside `world/` is mutable construction state. `world/` is the
sealed, reusable artifact. A failed rebuild leaves the existing World
byte-stable. Changes happen through reconstruction; consumers do not mutate a
World directly.

This is the operating boundary:

```text
conversation      construction and semantic maintenance
World             durable semantic state
SQLite / Python   computation
frontend          inspection
```

## Project layout

Worlds live inside the ordinary project that provides their evidence:

```text
my-project/
  ...ordinary project evidence...

  .worlds/
    support-entitlements/
      PURPOSE.md
      construction.py
      ...other World-scoped helpers, checks, and artifacts...

      world/
        world.sqlite
        world.sqlite.origins.json
        world.admission.json
        world.purpose.json
```

`construction.py` is the designated runtime entrypoint, but it is not the
only permitted construction artifact. An agent may create other programs or
files inside the named World directory when they help author or check that
World. There is no required `sources/` directory: the project itself is the
evidence environment.

## Compute directly

The inspector is not a gate. A World’s SQLite database is a first-class
computation surface:

```bash
sqlite3 .worlds/support-entitlements/world/world.sqlite
```

Once construction has declared a relation, query it with ordinary SQL:

```sql
SELECT *
FROM support_entitlement
LIMIT 20;
```

The installed Python API provides the same direct access to semantic queries:

```python
from ontology_author.world import Project

world = Project(".worlds/support-entitlements").open_world()
try:
    rows = world.query_semantic(
        "SELECT * FROM support_entitlement LIMIT 20"
    )
    print(rows)
finally:
    world.close()
```

The semantic query API accepts read-only `SELECT`/`WITH` queries over declared
World relations. Direct `world.sqlite` access remains available when a
consumer needs the full SQLite computation surface.

## Local inspector

Open a World with:

```bash
author open [world]
```

This starts the local read-only World API, serves the bundled production
frontend, and opens the inspector in a browser. No separate Node, npm, Vite,
backend, or development-port setup is required for normal use.

The inspector is for reading durable semantic state, including vocabulary and
schema, referents, relations, assertions, grounding, derivations,
staleness/completeness, and unresolved state where represented. It does not
resolve semantic uncertainty or adjudicate meaning. Those decisions belong in
the coding-agent conversation and enter a later World through reconstruction.

## Multiple Worlds

One project may contain several independent Worlds for different purposes:

```text
.worlds/
  support-entitlements/
  renewal-risk/
  product-eligibility/
```

Each has its own purpose, construction state, diagnostics, and sealed `world/`
bundle. The same project evidence may support several valid purpose-fit
conceptualizations; they are not required to be competing attempts at one
canonical model.

## Portability

Copy a World’s complete `world/` directory when another process needs to
consume the semantic artifact:

```text
World bundle
    → semantic consumption

World bundle + original project evidence
    → provenance verification

World construction + project evidence
    → reconstruction
```

The bundle does not copy all project source evidence and does not depend on an
absolute database path. Grounding references identify evidence; verification
and reconstruction require the original evidence environment.

## Architecture

```text
PURPOSE + WORKSPACE
        ↓
coding agent
        ↓
free construction
        ↓
World semantic boundary
        ↓
sealed World
        ↓
SQL / Python / agents / inspector
```

The implementation follows one useful principle:

> **Hard output boundary, soft construction process.**

Capable intelligence lives in the host coding agent. The semantic kernel
constrains durable output; consumers remain free to query and compute over the
resulting World.

## What Ontology Author is not

Ontology Author is not primarily a visual ontology editor, workflow engine,
model launcher, source-ingestion framework, or MCP server. It does not write
back to authoritative systems, and it does not claim to model everything in a
workspace. Its positive identity is narrower: conversational construction of
purpose-fit semantic state that can be reused computationally.

## Status

Ontology Author is an early open-source product. It is local and read-only at
the World boundary, and its pre-1.0 API and SQLite schema may evolve. World
construction quality depends substantially on the capability of the attached
coding agent. External write-back and external action semantics are not part of
the current product.

## Development

Install development dependencies and run the current product tests:

```bash
uv sync --extra dev
uv run --extra dev pytest
```

Build the production inspector and package artifacts:

```bash
cd frontend
npm ci
npm run build
cd ..
uv build
```

The frontend build writes the bundled inspector assets consumed by
`author open`. The Python package exposes the current product through the
`ontology_author` namespace.

## License

Apache-2.0. See [`LICENSE`](LICENSE).
