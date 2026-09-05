# CLAUDE.md

Guidance for working in this repository.

## Read this first: there are two products here

This repository holds two lineages. They share a checkout and almost nothing
else. Establish which one you are in before you change anything.

| | **World IR** (live) | **Graphauthor graph-v1** (frozen) |
|---|---|---|
| Store | `taskview/` — SQLite, one table per relation | `graph_storage/` — Ladybug `.lbug` |
| Construction | nine-pass agent constructor | agent-authored `workbook/build.py` |
| Read plane | `world_explorer/` | `mcp_server/` |
| Front end | `frontend/src/world/` | `frontend/src/product/` |
| Route | `#/world` | `#/graph`, `#/review` |
| Status | all current work | untouched since extraction |

**Default to World IR.** Unless a task names graph-v1 surfaces explicitly, it
belongs to the World IR line.

---

# Part 1 — World IR (live)

## The product

A local, read-only semantic data layer that integrates heterogeneous
authoritative sources into grounded, reusable, computable world state. The
value hypothesis is reuse: cross-source meaning is constructed once and reused
across analyses instead of reconstructed per question.

An agent constructs. A human reviews and owns publication. The product never
authors interpretation.

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
convenience of a view.

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

## Construction: the nine passes

The constructor is an LLM agent, isolated per pass. It writes artifacts; the
host validates and materializes.

```text
P0  00_intention_contract.json     purposes → objectives, scope, epistemics
P1  01_vocabulary.json             relations, roles, admission, class
P2  02_mechanical_world/           deterministic compile; grounded BASE tuples
P3  03_obligations.json            the frontier: what a purpose needs decided
P4  04_packets/<obligation>.json   bounded evidence per obligation
P5  05_dispositions.json           adjudication
P6  06_admission.json, 06_world/   WORLD vs PURPOSE; the compiled world
P7  07_derivations.json            derived relations, blocking premises
P8  08_outputs/{a,b,c}.json        purpose answers
```

Still nine. v3 added no pass — normalization is a deterministic stage inside
projection, not one a human reviews — and put machine checks *inside* passes
instead. Each writes a document whose whole contract is a top-level `ok`:

```text
P1  01_abi_completeness.json       are the required consumer fields declarable
P6  06_provenance.json             is every durable assertion grounded
P8  08_abi_completeness.json       do those fields materialize before projection
```

A pass can write its artifact, exit 0, and say no in the same breath. The read
plane carries that (`PASS_ATTESTATIONS` in `world_explorer/construction.py`)
and a refused check withholds CERTIFIED — §5 lets the reader withhold
certification and never confer it, so that is the direction it resolves in.
Absence is silence: runs frozen before the checks existed read unchanged.

Lives in `research/semantic_integration/`; `ARCHITECTURE.md` there is the
current account of the pipeline. The kernel is `core/kernel.py` (wraps
`taskview.TaskView`, never forks it); the constructor line is v3, most recently
`domains/diligence/constructor_v3_1_1/`, with `constructor_v2/` frozen beside
it. Both are readable by the same read plane, which is the point.

**`research/` is user-owned.** Do not modify it, and never overwrite sealed
results, unless the task is explicitly that work.

## Surfaces

| Path | Role |
|---|---|
| `taskview/` | the store: model, TaskView, agent surface |
| `research/semantic_integration/` | kernel, constructor, benchmarks — user-owned |
| `world_explorer/` | read plane: `adapter.py` formats, `http.py` serves |
| `frontend/src/world/` | the explorer UI |
| `frontend/src/styles/` | `graphDna.ts`, `motion.ts` — the shared visual kernel |
| `scripts/build_world.py` | compile a world the explorer can open |
| `data/worlds/` | compiled worlds + sidecars (generated, not source) |

`world_explorer/adapter.py` **holds no state.** Every method reads through to
the open world. An adapter that caches is a second copy of the world with its
own staleness.

A world on disk is four files, and the origins sidecar is the one that gets
missed:

```text
bomS1.sqlite                 TaskView
bomS1.sqlite.origins.json    construction origin per assertion
bomS1.demand.json            the purpose and what it leaves unresolved
bomS1.demand.json.sha256
```

## Design authorities

In order. Benchmarks are evidence, not specification.

1. `world_ir_frontend_spec.md` — the read side
2. `constructor_frontend_spec.md` — the construction-review side
3. `Read-side World v0 — first product-shaped reuse slice.md` — product thesis

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
