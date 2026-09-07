# CLAUDE.md

Guidance for working in this repository.

## Read this first: there are two products here

This repository holds two lineages. They share a checkout and almost nothing
else. Establish which one you are in before you change anything.

| | **World IR** (live) | **Graphauthor graph-v1** (frozen) |
|---|---|---|
| Store | `taskview/` — SQLite, one table per relation | `graph_storage/` — Ladybug `.lbug` |
| Construction | capable agent → World construction boundary (`runtime_v0` is the current mechanism; nine-pass constructor is research) | agent-authored `workbook/build.py` |
| Read plane | `world_explorer/` | `mcp_server/` |
| Front end | `frontend/src/world/` | `frontend/src/product/` |
| Route | `#/world` | `#/graph`, `#/review` |
| Status | all current work | untouched since extraction |

**Default to World IR.** Unless a task names graph-v1 surfaces explicitly, it
belongs to the World IR line.

---

# Part 1 — World IR (live)

## The product

A local semantic compilation layer. Given a user purpose and a heterogeneous
evidence/workspace, a capable agent constructs the smallest grounded World
sufficient for that purpose and leaves unestablished meaning unresolved.
Consumers (SQL, Python, agents, the explorer) reuse that World instead of
reconstructing source-specific semantics from the original files.

An agent constructs. A human reviews and owns publication. The product runtime
never authors interpretation.

Authoritative account: `research/semantic_integration/CONSTITUTION.md`.
Construction loop and agent brief: `research/semantic_integration/CONSTRUCTION.md`.

## The semantic calculus — frozen

```text
REFERENT                    thin; carries no properties
NAMED TYPED N-ARY RELATION  roles are named and typed
DERIVATION                  maintained, per-relation
```

with grounding, origin, revision, stale/current, scope/completeness, and an
explicit unresolved state.

This does not move. Change it only for a concrete correctness counterexample
showing the core cannot represent something required — not for the
convenience of a view. Details and change bars are in the constitution.

Three facts that are easy to get wrong and are load-bearing:

- **Unresolved is purpose-relative**, not world state.
- **Staleness is per-relation**, never per-tuple.
- **A missing positive assertion is not a denial.** No closed-world DISTINCT
  from absence.

## Two origins that disagree

Both are called origin and they answer different questions. Do not merge them.

```text
_tv_assertions.origin        ASSERTED | DERIVED
                             how the tuple entered the table

ConstructionOrigin           MECHANICAL | SEMANTIC | DERIVED | ADJUDICATED
                             who decided it; sidecar `.origins.json`,
                             not a TaskView schema change
```

`ADJUDICATED` is a human verdict superseding or supplying a machine judgment.
A person's decision entering as `SEMANTIC` launders it as the machine's, and
every downstream claim about construction becomes untrue.

## Construction

The product construction story is not a pass machine:

```text
purpose + heterogeneous workspace
        → capable construction agent
        → arbitrary programming / exploration
        → World construction boundary
        → candidate World
        → deterministic validation / publication
        → accepted World
```

`runtime_v0` is the current boundary mechanism (`construction.py` executed into
a candidate TaskView, then accept or discard). `construction.py` is a supported
authoring shape, not a semantic primitive.

The nine-pass P0–P8 constructor in `domains/diligence/constructor_v3_1_1/`
(with `constructor_v2/` frozen beside it) is **research compiler strategy**.
It earned invariants the constitution keeps (WORLD vs PURPOSE, provenance,
fail-closed materializability). It is not the permanent product workflow.
v3.1.1 is that compiler's ABI-materializability hardening, not generic
heterogeneous-source ingestion.

The construction-review read plane (`world_explorer/construction.py`) still
reads nine-pass artifacts. That is a reviewer of the research compiler, not
World IR ontology.

The kernel is `core/kernel.py` (wraps `taskview.TaskView`, never forks it).
`research/semantic_integration/ARCHITECTURE.md` is a thin index.

**`research/` is user-owned.** Do not modify it, and never overwrite sealed
results, unless the task is explicitly that work.

## Surfaces

| Path | Role |
|---|---|
| `taskview/` | the store: model, TaskView, agent surface |
| `research/semantic_integration/` | constitution, kernel wrap, `runtime_v0` boundary, research constructor, benchmarks — user-owned |
| `research/semantic_integration/runtime_v0/` | current construction-boundary mechanism (not ontology) |
| `world_explorer/` | read plane: `adapter.py` formats, `http.py` serves; `construction.py` reads the research nine-pass run |
| `frontend/src/world/` | the explorer UI |
| `frontend/src/styles/` | `graphDna.ts`, `motion.ts` — the shared visual kernel |
| `scripts/build_world.py` | compile a BOM-lineage world the explorer can open |
| `data/worlds/` | compiled worlds + sidecars (generated, not source) |

`world_explorer/adapter.py` **holds no state.** Every method reads through to
the open world. An adapter that caches is a second copy of the world with its
own staleness.

A compiled World is a TaskView sqlite plus sidecars. The origins sidecar is
the one that gets missed. Two current clusters exist; they are mechanisms,
not two calculi:

```text
BOM / explorer lineage              runtime_v0 accepted/
bomS1.sqlite                        world.sqlite
bomS1.sqlite.origins.json           world.sqlite.origins.json
bomS1.demand.json                   world.purpose.json
bomS1.demand.json.sha256            world.admission.json
```

## Design authorities

In order. Benchmarks are evidence, not specification.

1. `research/semantic_integration/CONSTITUTION.md` — semantic properties
2. `research/semantic_integration/CONSTRUCTION.md` — construction architecture and agent brief
3. `world_ir_frontend_spec.md` — the read-side presentation contract
4. `constructor_frontend_spec.md` — review UI over the research nine-pass constructor
5. `Read-side World v0 — first product-shaped reuse slice.md` — early read-side product thesis

Do not recover product behavior from deleted design history, old branches,
trial outputs, or database fixtures.

## Front-end rules

- **Meaning is carried structurally, never decoratively.** Construction origin
  is geometry — filled, outlined, shelf, hollow. Colour is for status only.
  Anything encoded as colour alone will be retuned away.
- **Two laws, both code, neither a metaphor.** `styles/motion.ts` is gravity:
  `emit` is a body given the escape impulse gravity spends at its home,
  `absorb` its time reverse, `settle` an analytic damped spring.
  `styles/light.ts` is illumination: a source is whatever a person acted on,
  falling off inverse-square over *graph* distance, expressed as opacity —
  never colour. **Nothing moves, and nothing is lit, that a person did not
  cause**; `flow` is the one exception, and it is the machine making you wait.
  `styles/transition_map.md` §0 is the argument; `scripts/check_field_laws.py`
  is the enforcement.
- Anything you would be sad to rebuild goes in `frontend/src/styles/`, not in
  a page. Motion and DNA carried across surfaces; things that lived inside a
  canvas component did not.
- No table library. Windowed rows, fixed height, SQL-side sorting.
- Retrieval and traversal do not call a model.
- Exact misses stay exact misses; search results stay candidates.

## The write boundary

The read-side spec's §17 excludes the product reaching outside itself. It does
not exclude a human recording a judgment.

```text
THE WORLD IS READ-ONLY.  No surface writes a compiled world.
CONSTRUCTION IS WHERE WRITES GO.  A verdict is an input to the next build.
THE ONLY PATH FROM A VERDICT TO A WORLD TUPLE IS A REBUILD.
```

Structural, not disciplinary: there is no endpoint that mutates a compiled
world. The prohibited shortcut, named so it is recognizable — applying a
verdict directly into `06_world/world.sqlite` to skip the rebuild. It is
always one tuple, always obviously correct, and it collapses the boundary.

## Commands

```bash
# read plane (bearer devtoken) + Vite proxying /world
uv run --extra all python scripts/run_world_explorer.py --world data/worlds/bomS1.sqlite
cd frontend && npm run dev          # http://localhost:5173/#/world?apiToken=devtoken

# compile a world the explorer can open
uv run --extra all python scripts/build_world.py

# tests
uv run --extra all --extra dev pytest tests/world_explorer tests/taskview -q

# frontend typecheck — there is no tsconfig.app.json
cd frontend && npx tsc -p tsconfig.json --noEmit

# the field laws: no live stylesheet writes a duration the spine already has
uv run python scripts/check_field_laws.py
```

`npx tsc` reports pre-existing failures in `src/app`, `src/field`, `src/inbox`
and `src/explorations/trial-legacy`. Filter to the paths you touched.

`pkill -f run_world_explorer.py` exits 144 and kills a compound shell. Run the
kill and the restart as separate commands.

---

# Part 2 — Graphauthor graph-v1 (frozen)

Still present, still tested, not under development. Extend it only when a task
names it. Its authorities are `product/graph-harness-product.md`,
`product/harness-contract.md`, `product/named-traversal-contract.md`.

One construction model: a workbook holding sources, an optional prepared atom
stream, the agent-authored `build.py`, and `out/encoding.json`. The product
never authors or runs `build.py`; the host validates and materializes its
output. There are no domain format packs, server-owned construction jobs,
staged constructors, or one-shot LLM graph generators.

Never add another construction path to this lineage. Extend the parser or
segmenter protocols, or the workbook boundary, instead.

- Parsers, segmenters and workbook programs have no graph-write authority.
- Durable changes enter through propose, which auto-commits; revert is the
  backward path.
- Node kinds and predicates are chosen by the workbook program.
- **One process owns a Ladybug graph file at a time.**

```bash
uv run --extra all python scripts/run_local_product.py
python scripts/workbook.py prepare --workbook workbook --source source.html
python scripts/workbook.py validate --workbook workbook --encoding workbook/out/encoding.json
python scripts/workbook.py materialize --workbook workbook --encoding workbook/out/encoding.json
```

---

# Repository hygiene

Generated graphs, worlds, sidecars, layouts, caches and run outputs are not
source. Opening a tracked Ladybug graph may modify it even during read-only
inspection.

**Preserve unrelated worktree changes.** Stage by explicit path, never `git add
-A`. Constructor runs and research work are often in flight in the same
checkout. Never restore graph or world binaries without establishing their
ownership.

The full pytest suite writes ~1.9G of materialized graphs into `tmp_path`;
`pytest.ini` caps retention for that reason. Prefer running the directory you
are working in.

Install the repository guard once per clone:

```bash
git config core.hooksPath scripts/hooks
```
