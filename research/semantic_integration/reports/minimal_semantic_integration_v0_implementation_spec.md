# Minimal Semantic Integration System — v0 implementation spec

**Status:** research-only implementation specification.  
**Not:** an implementation, a TaskView/kernel change, a Constructor change, or a replacement for `CONSTITUTION.md`, `CONSTRUCTION.md`, `ARCHITECTURE.md`, `world_ir_frontend_spec.md`, or `constructor_frontend_spec.md`.

Product authority: [`../CONSTITUTION.md`](../CONSTITUTION.md), [`../CONSTRUCTION.md`](../CONSTRUCTION.md). This spec remains the research-only v0 implementation sketch that Spike 1 partially realized.

This document asks whether the synthesis in `minimal_semantic_integration_synthesis_v0.md` compiles into a **small believable piece of software**, given what already exists.

Labels used throughout:

```text
EXISTING          already implemented; reuse
PROPOSED_V0       needed for the smallest credible loop; not yet productized
RESEARCH_ONLY     experimentally useful; must not enter the v0 runtime
NOT_NEEDED        out of v0 even as research promotion
```

Authority order for this pass:

1. Frozen foundation: `taskview/` plus [`CONSTITUTION.md`](../CONSTITUTION.md).
2. Existing compiler contracts: Constructor v3.1.1 `RelationContract` / `field_sources` / ABI materializability (do not invent a second ABI).
3. Experimental synthesis: `reports/minimal_semantic_integration_synthesis_v0.md`.
4. Product UI specs: read, not rewritten. v0 does not implement them.

---

## 0. Classification of the current stack

The repository already contains **two compilers** over the same foundation. v0 must pick one loop and not merge them.

| Loop | Shape | Classification for v0 |
| --- | --- | --- |
| TaskView + `SemanticWorld` | SQLite referents / n-ary relations / derivations / grounding / revision | **EXISTING foundation** |
| Constructor v3 P0–P8 | Isolated LLM passes, packets, dispositions, admission, nine artifacts | **RESEARCH_ONLY compiler** |
| Purpose-First Python Spine | Host writes `construction.py`; in-memory `World`/`Purpose`; JSON snapshot | **EXISTING experiment; the v0 *loop*** |
| World explorer + constructor review UI | G6 read-side / docket | **NOT_NEEDED for v0** |

v0 is the spine loop persisted into TaskView. It is not a ninth-pass productization of Constructor v3, and it is not a new kernel.

The post-v2 contract work sits in the **compiler/contracts** layer (`ARCHITECTURE.md` §2), not in TaskView. v0 reuses that layer's invariants and does not create a competing ABI.

---

## 1. v0 boundary

### What v0 does

```text
folder of authoritative sources
→ declared purpose
→ boring reconstructible source helpers
→ host (outside the runtime) authors construction.py
→ runtime executes construction.py into a candidate TaskView SQLite
→ deterministic validation (grounding, contracts, materializability)
→ accept or discard the candidate as a whole
→ accepted World is queryable with SQL and Python
→ purpose requirements emit structured unresolved failure records
→ host may revise construction.py and repeat
```

That is the experimentally motivated loop from the synthesis, cut to what a runtime must actually do.

### What v0 explicitly does not do

```text
run P0–P8
factor semantic obligations in the kernel
store REFINED / evidence plans / proposals / near-misses as World types
open a G6 explorer or constructor docket
ingest a corpus of prose automatically
edit ontology through a UI
write back to sources
canonicalize entities
score confidence
maintain a persistent Source IR
```

Host conversation, obligation factoring, evidence packets, dry-runs, and refinement remain **host behavior**. The runtime only has to make those behaviors *possible* by exposing grounded World state and factual requirement failures.

---

## 2. Existing components that can be reused

Inspected:

- `taskview/store.py`, `taskview/model.py`, `taskview/agent_surface.py`
- `research/semantic_integration/core/{kernel,origins,source}.py`
- Constructor v3.1.1 `runtime/{contracts,provenance,abi_completeness,normalizer}.py`
- Purpose-First Python Spine `world_api.py`, `source.py`, `runner.py`
- Compiled-world sidecars in `scripts/build_world.py` / `world_explorer/adapter.py`
- Post-v2 summary: contracts + role identity normalize; no semantic-family World types

| Capability | Existing location | Reuse unchanged? | Small change needed? | New v0 work? |
| --- | --- | --- | --- | --- |
| Referents | `taskview._tv_referents` | Yes | No | No |
| Relation schemas | `_tv_relations` | Yes | No | No |
| Role contracts (name/type/column) | `_tv_roles` | Yes for physical roles | **Do not** add `semantic_identity` to TaskView | Consumer identity stays in contract sidecar |
| Grounded assertions | `_tv_assertions` + `_tv_groundings` | Store yes | TaskView still *allows* empty grounding | Fail-closed check at candidate commit (**EXISTING** as `validate_provenance`, **PROPOSED_V0** to tighten) |
| Derivations | `_tv_derivations` + `register_derivation` / `run_derivation` | Yes | No | No |
| Purpose requirements | PFPS `Purpose.require_*`; Constructor P0 `00_intention_contract.json` | Mechanism in PFPS | Persist checks against TaskView rows | Thin `purpose.py` over TaskView |
| Unresolved requirements | PFPS `holes`; BOM `*.demand.json`; Constructor P3 obligations | PFPS failure *grain* | Do not reuse BOM demand shape or P3 obligation objects | Persist factual failure rows / sidecar |
| Semantic identity / field bindings | `RoleSpec.semantic_identity`, `PurposeProjectionContract.field_sources` | **Reuse this ABI** | Strip diligence-hardcoded field lists | Generic binding document per purpose |
| ABI materialization | v3.1.1 `check_abi` + `normalize_world`; invariant `SATISFIED(f) ⇒ f ∈ Normalize(W)` | **Reuse invariant** | Diligence `CANONICAL_RELATIONS` / `REQUIRED_IDENTITIES` are domain | Generic Normalize over purpose-declared fields |
| SQLite persistence | `TaskView` | Yes | No | No |
| Source helpers | PFPS `source.py` | Yes as reconstructible lib | Add targeted text read/search | No persistent Source IR |
| Construction execution | PFPS `runner.py` `exec(construction.py)` | Loop yes | Persist into TaskView, not in-memory `World` | Candidate-file commit |
| Revision metadata | `_tv_view.revision`, `relation_version`, completeness receipts | Intra-file yes | No candidate/accepted World | File-level accepted vs candidate |
| Construction origin (who decided) | `.origins.json` via `ConstructionOrigin` | Yes for MECHANICAL/SEMANTIC/DERIVED/ADJUDICATED | This is **not** epistemic admission | Do not overload it |
| World vs Purpose scope | Constructor `06_admission.json`; `RelationContract.scope` | Sidecar yes | Not a TaskView column | Keep as contract/admission sidecar |
| SQL consumer | `TaskView.query_semantic` | Yes for raw World | Unstable table names | Projected ABI views |
| Python consumer | `SemanticWorld` / `TaskView` | Yes | Tighten ungrounded `assert_tuple` | See §6 |
| Agent describe/query/assert/rerun | `TaskViewAgentSurface` | Consumption yes | Schema declaration remains build-time | Host uses full Python + commit API |
| Nine-pass constructor | `constructor_v3_1_1/` | No | — | **RESEARCH_ONLY** |
| Explorer / review UI | `world_explorer/`, frontend specs | No | — | **NOT_NEEDED** |

**Do not assume the synthesis requires new tables because PFPS used JSON.** TaskView already is the durable World.

**Do not copy Constructor v3 into v0.** Its contracts, provenance check, and normalizer *invariants* are reusable; its pass machine is not required for the loop.

---

## 3. Minimal persistent data model

### 3.1 Reuse TaskView as-is — **EXISTING**

No new `_tv_*` tables.

```text
_tv_view                view_id, task_spec_ref, revision
_tv_referents           id, label
_tv_relations           name, description, mode BASE|DERIVED, relation_version
_tv_roles               relation_name, ordinal, role_name, role_type, column_name
_tv_assertions          assertion_id, relation_name, origin ASSERTED|DERIVED, created_revision
_tv_groundings          subject_type, subject_id, kind SOURCE|WORLD|ASSERTION|DERIVATION, reference, detail
_tv_derivations         sql, inputs, execution_status, fingerprints
_tv_completeness        local completeness receipts
<name>                  one ordinary SQLite table per declared relation
```

Why these persist: they **are** the World. Deleting them loses semantic integration work (synthesis §6).

Deterministic invariants that depend on them:

- referents are thin handles
- tuples are typed n-ary assertions
- DERIVED rows come only from registered SQL
- grounding pointers do not copy source bodies
- relation version / view revision drive staleness of derivations

### 3.2 Sidecars beside the SQLite file — **EXISTING pattern, v0 contents**

Compiled worlds today are four files (`scripts/build_world.py`):

```text
world.sqlite
world.sqlite.origins.json
world.demand.json
world.demand.json.sha256
```

v0 keeps a sidecar cluster. It does **not** reuse the BOM `demand.json` obligation schema (candidate tuples a purpose wanted). That schema is a BOM-frontier experiment, not a general purpose contract.

Proposed accepted-world files:

```text
world.sqlite                         EXISTING TaskView
world.sqlite.origins.json            EXISTING ConstructionOrigin per assertion
world.purpose.json                   PROPOSED_V0 purpose contract + required consumer fields + field_sources
world.contracts.json                 PROPOSED_V0 relation contracts (physical name, roles, semantic_identity, scope)
world.admission.json                 PROPOSED_V0 WORLD|PURPOSE per relation (Constructor P6 idea, not a pass)
world.source_manifest.json           PROPOSED_V0 source path → content hash at accept time
world.failures.json                  PROPOSED_V0 requirement failure records (see §3.3 alternative)
```

`world.purpose.json` and `world.contracts.json` are the **same ABI mechanism** as Constructor `00_intention_contract` / `01_vocabulary` / `RoleSpec.semantic_identity` / `field_sources`. They are not a second ABI. They are the compiler documents without the nine-pass filenames.

### 3.3 Per candidate item: persist or not

| Item | Persist? | Where | Why it cannot stay host-local | If deleted |
| --- | --- | --- | --- | --- |
| Referent | Yes | TaskView | Identity of World participants | Semantic joins become ungrounded names |
| Relation schema / roles | Yes | TaskView | Typed n-ary meaning | SQL surface disappears |
| `semantic_identity` / `field_sources` | Yes | contracts/purpose sidecar | Consumers depend on identity, not physical names (post-v2 §3, §8) | ABI becomes constructor-name luck |
| Assertion tuples | Yes | relation tables | Durable claims | Integration work lost |
| Grounding | Yes | `_tv_groundings` | Fail-closed established-truth | Ungrounded World looks established |
| Derivation SQL + inputs | Yes | `_tv_derivations` | Maintained computation | Stale/current becomes uncheckable |
| Construction origin | Yes | origins sidecar | Who decided; must not merge with `_tv_assertions.origin` | Human vs mechanical is laundered |
| Purpose contract | Yes | purpose sidecar | Executable requirements, not prompt text | Unresolved is undefined |
| Requirement *schema* | Yes | inside purpose sidecar | What was demanded | Failures have no contract |
| Unresolved *occurrences* | Yes | see below | Host cannot reconstruct which rows failed after accept | SQL/Python cannot inspect holes |
| Scope WORLD/PURPOSE | Yes | admission/contracts sidecar | Purpose-independence test is a durable classification | Purpose policy looks like World law |
| Epistemic admission enum table | **No** | — | Enforce by commit policy (§4–§5), not a new ontology | — |
| Semantic obligation / REFINED | **No** | host notes | Reconstructible from failures + later construction.py | — |
| Evidence plan / packet | **No** | host/workspace | Reconstructible source helpers | — |
| Source inspection profiles | **No** | cache only | Regenerable | — |
| Source file hashes | Yes | source_manifest | Receipt of what World was compiled against | Cannot detect source move vs World |
| Candidate World | Transient file | temp sqlite | Never mixed into accepted | — |

### 3.4 Unresolved occurrences — smallest choice

**Do not** add `_tv_obligations`.

Two acceptable v0 representations (open decision §19.1):

**A (recommended).** Ordinary PURPOSE-scoped BASE relation in the same TaskView, declared by construction.py, e.g. `purpose_requirement_failure` with roles:

```text
requirement_id TEXT
affected_identity TEXT      -- semantic_identity or source key, not a family name
failure_kind TEXT           -- factual: UNINTERPRETED, NOT_NUMERIC, CARDINALITY_*, NO_MATERIALIZABLE_PATH, EXPLICIT_UNRESOLVED, NOT_ESTABLISHED
relation_name TEXT
subject_json TEXT           -- row keys / role values
grounding_ref TEXT
```

Why persist: the synthesis loop requires “SQL/Python → unresolved semantic inspection” without reopening raw sources. A host-only JSON file from the last `construction.py` run is lost if someone queries only `world.sqlite`.

Why not a kernel primitive: it is just another named relation. TaskView already represents uncertainty as accepted semantic state in ordinary relations (`taskview/README.md`).

**B.** `world.failures.json` only. Smaller, but then SQL over holes requires joining a sidecar. Acceptable if v0 consumers always open the cluster, not the sqlite file alone.

v0 should pick one. Not both.

### 3.5 What must not get a table

```text
semantic_frontier
semantic_obligation
REFINED
evidence_plan
candidate_interpretation
semantic_proposal
near-miss
decision_record
consequence_dry_run
semantic_family
confidence
```

**RESEARCH_ONLY / NOT_NEEDED.** Host may write whatever notes it wants beside a run. The kernel does not know their names.

---

## 4. Semantic assertion/admission model

Keep two existing axes, and add **one** commit rule. Do not add an epistemology framework.

### Axis 1 — Who decided (**EXISTING**)

`ConstructionOrigin` in `.origins.json`:

```text
MECHANICAL | SEMANTIC | DERIVED | ADJUDICATED
```

This answers construction accounting. It must not be used as “established World truth.”

`_tv_assertions.origin` remains `ASSERTED | DERIVED` (how the row entered the table). Do not merge the two origins (`CLAUDE.md` / kernel docstring).

### Axis 2 — Where it belongs (**EXISTING compiler**)

`RelationContract.scope` / `world.admission.json`:

```text
WORLD | PURPOSE
```

Test (synthesis §5, Constructor P6): *If this purpose disappeared, would the proposition keep the same meaning and truth conditions?*

### Axis 3 — Why it may be used (**PROPOSED_V0 commit policy, not a new enum table**)

Computed at validation time from grounding + scope + origin:

```text
ESTABLISHED_WORLD
  WORLD scope
  + SOURCE grounding (or DERIVED from ESTABLISHED_WORLD inputs)

ESTABLISHED_DERIVED
  DERIVED relation whose declared inputs are currently ESTABLISHED_*

PURPOSE_POLICY
  PURPOSE scope
  + ADJUDICATED origin
  (user-certified for this purpose; no claim of external law)

UNVERIFIED
  WORLD scope without SOURCE (or model-only)
  → must not be in accepted World BASE tables

UNRESOLVED
  explicit failure / purpose.unresolved
  → failure records, not established tuples
```

The synthesis example is then mechanical:

```text
"The final permit legally overrides the fact sheet."
  scope = WORLD
  no SOURCE in corpus
  → may be a host proposal; must not become ESTABLISHED_WORLD
  → must not satisfy a contract requiring established World truth

"For this analysis, use the final permit."
  scope = PURPOSE
  origin = ADJUDICATED
  → PURPOSE_POLICY may satisfy Purpose-specific contracts
  → still must not be projected as World law
```

**Invariant (the only new one v0 must enforce):**

> A purpose requirement that declares `requires_established_world = true` is satisfied only by `ESTABLISHED_WORLD` / `ESTABLISHED_DERIVED` materialization. `PURPOSE_POLICY` and `UNVERIFIED` do not count.

No confidence scores. No family types. No third store.

`SemanticWorld.assert_tuple` today synthesizes `GroundingKind.WORLD` when the caller omits observations (`core/kernel.py` `_assertion_groundings`). That is **unsafe to reuse as-is** for World BASE commits. v0 must stop treating origin-only WORLD grounding as established (small wrap change, not a TaskView schema change).

---

## 5. Grounding invariant

Adequate grounding is a **pointer**, not copied source text (`Grounding`, `SourceObservation`).

### 5.1 What may be represented vs what may be treated as established

| Kind | May be represented in accepted World? | May satisfy established-World requirement? | May satisfy Purpose-policy requirement? |
| --- | --- | --- | --- |
| Source-established BASE | Yes, WORLD, `GroundingKind.SOURCE` with non-empty reference | Yes | Yes |
| Mechanically derived | Yes, DERIVED, `GroundingKind.DERIVATION`, inputs declared | Yes iff inputs are established | Yes iff inputs are admitted for that purpose |
| User-certified Purpose policy | Yes, PURPOSE, `ADJUDICATED`, grounding may be `WORLD`/`ASSERTION` citing the certification record | **No** | Yes |
| User assertion about external reality | Only if it is really a Purpose policy, **or** SOURCE-grounded World fact | Only with SOURCE | If certified as policy |
| Model proposal / hypothesis | **No** in accepted World BASE | No | No |
| Explicit unresolved | Failure records only | No | No |

Constructor `validate_provenance` (**EXISTING**) requires every durable assertion to have one of `SOURCE | WORLD | ASSERTION | DERIVATION` with a non-empty reference. That is necessary and **not sufficient** for established World truth, because origin-only `WORLD` grounding currently passes it.

**PROPOSED_V0 tightening** (constructor-runtime style, still not a kernel change):

```text
WORLD-scoped BASE
  → at least one SOURCE grounding with non-empty reference
  → otherwise candidate commit fails

PURPOSE-scoped BASE
  → SOURCE optional
  → origin MUST be ADJUDICATED for policy that satisfies Purpose contracts
  → SEMANTIC/MECHANICAL Purpose rows are still allowed if SOURCE-grounded
    (purpose-local mechanical extracts)

DERIVED
  → register_derivation + successful run
  → no manual assert_tuple (already TaskView)

Missing grounding
  → fail closed; do not insert; do not synthesize WORLD-from-origin
```

Fail closed means: the candidate World is discarded. Partial tables never become accepted.

`UNRESOLVED` is success when the corpus cannot establish the proposition (NODI). That is a **failure record**, not an admitted tuple with a fake code legend.

---

## 6. Minimal Python construction API

Do not design a DSL. Do not freeze PFPS in-memory `World` as the store.

The agent may use ordinary Python, `pandas`, csv, regex, whatever. Durable effects go only through the commit surface.

### 6.1 Names — prefer EXISTING TaskView / SemanticWorld

Do not invent `world.relation` if `declare_relation` already exists.

```python
# EXISTING (SemanticWorld / TaskView)
world.add_referent(id, label=..., observations=...)
world.declare_relation(name, roles, mode=BASE|DERIVED, description=...)
world.assert_tuple(relation, values, origin=..., grounding=...)
world.retract_tuple(relation, values)
world.register_derivation(relation, sql=..., inputs=...)
world.rerun(relation, completeness=...)
world.query_semantic(sql)

# PROPOSED_V0 (purpose checks over the same store)
purpose.require(...)               # declare a named requirement
purpose.require_unique(...)        # EXISTING PFPS behavior, reimplemented on TaskView rows
purpose.require_materializable(...)
purpose.require_interpreted(...)
purpose.require_numeric(...)
purpose.unresolved(...)            # explicit hole; does not invent a fact
```

`world.map` from PFPS is **RESEARCH_ONLY** as a bulk helper. If kept, it is sugar over `assert_tuple` and must pass per-row grounding. Ungrounded `map` is forbidden for WORLD BASE.

### 6.2 Operations

#### `add_referent`

| | |
| --- | --- |
| Inputs | stable id, optional label, optional SOURCE observations |
| Durable effect | `_tv_referents` row; optional SOURCE groundings |
| Grounding | optional for the handle; **properties of the thing live in relations** |
| Validation | non-empty id (EXISTING) |
| Failure | `TaskViewError`; candidate aborted if uncaught |

Do **not** add referent `kind` to TaskView. PFPS `referent(kind, key)` encoding kinds into the id is host convenience. Kinds, if needed, are relations.

#### `declare_relation`

| | |
| --- | --- |
| Inputs | name, ordered `Role(name, type)`, BASE/DERIVED |
| Durable effect | `_tv_relations` + `_tv_roles` + physical table |
| Grounding | n/a |
| Validation | identifier rules (EXISTING); role types from `RoleType` |
| Failure | `TaskViewError` |

`semantic_identity` is **not** an argument here. It is declared in `world.contracts.json` (same as Constructor vocabulary). Physical names may vary (post-v2 B1/B2).

#### `assert_tuple`

| | |
| --- | --- |
| Inputs | relation, role values, `ConstructionOrigin`, `AssertionGrounding` |
| Durable effect | row in relation table + `_tv_assertions` + groundings + origins sidecar |
| Required grounding | WORLD BASE: SOURCE observations required. PURPOSE policy: certification record required. |
| Validation | BASE only (EXISTING); fail if WORLD BASE lacks SOURCE |
| Failure | raise; no silent WORLD-from-origin synthesis |

#### `register_derivation` / `rerun`

| | |
| --- | --- |
| Inputs | output relation, raw SQL, declared inputs, completeness claim |
| Durable effect | DERIVED materialization (EXISTING) |
| Grounding | `GroundingKind.DERIVATION` on produced assertions (EXISTING kernel wrap) |
| Validation | SQL read-only over declared inputs (EXISTING) |
| Failure | `DerivationError`; candidate not accepted |

#### `purpose.require_*`

| | |
| --- | --- |
| Inputs | requirement id, target relation/field, cardinality or known-set, whether established-World is required |
| Durable effect | requirement recorded in purpose sidecar; on check, zero or more failure records |
| Grounding | failures may cite the row's grounding |
| Validation | relation/field must exist |
| Failure of the *check* | not a Python exception; it is unresolved state. Exception only on malformed require() |

PFPS already implements UNIQUE / MATERIALIZABLE / INTERPRETED / NUMERIC / EXPLICIT_UNRESOLVED. Reuse those **failure kinds**. Do not add a semantic-family taxonomy.

#### `purpose.unresolved`

Writes an `EXPLICIT_UNRESOLVED` failure. Does not insert a World fact. This is how `WHEN DISCHARGING` becomes a sharper later requirement in a *subsequent* `construction.py`, not via a kernel `REFINED` type.

### 6.3 Exploratory Python

Unconstrained. Profiling, joins, parsing, temporary dataframes are not World state. Only commit-API calls persist.

---

## 7. Source helper API

**EXISTING:** PFPS `source.py` (`Source` over a folder). Reconstructible. Not World semantics.

Promote as a library the host and `construction.py` may import. Cache is disposable.

| Helper | Status |
| --- | --- |
| `tables` / `fields` / `n_rows` / `rows` | EXISTING |
| `profile` / `distinct_values` | EXISTING |
| `key_candidates` | EXISTING |
| `value_overlap` | EXISTING |
| `join` / `join_profile` | EXISTING |
| `parse_date` / `interval_contains` / `looks_numeric` | EXISTING |
| `document_inventory` | EXISTING (reads a JSON inventory if present) |
| targeted text read / search in a named file | **PROPOSED_V0** (small; spine file currently stops at inventory) |

Not included:

```text
persistent Source IR          NOT_NEEDED
whole-corpus embedding index  NOT_NEEDED
automatic prose-to-KG         NOT_NEEDED
```

Structural overlap (`value_overlap` 100%) is **not** semantic identity. Only `assert_tuple` / contracts commit identity.

Cache rule (synthesis §6):

```text
delete helper cache → regenerate
delete World        → semantic work is lost
```

---

## 8. Execution lifecycle

One complete run:

```text
1. Project directory exists (sources/ + purpose text or world.purpose.json draft).
2. Host inspects sources with helpers (no World writes).
3. Host writes or revises construction.py.
4. Runtime copies sources + construction.py into an isolated candidate dir.
5. Runtime creates empty candidate.sqlite (new TaskView).
6. exec(construction.py) against that TaskView + Source helpers.
7. Validators:
     grounding / established-World rule
     contracts present for every declared relation
     ABI materializability for required consumer fields
     derivation runs current
8. If any validator not ok → delete candidate; accepted World unchanged.
9. If ok → atomic replace:
     accepted world.sqlite + sidecars
10. Consumers open accepted files only.
```

### Transaction boundary

TaskView already wraps individual `assert_tuple` in SQLite transactions. That is **not** the product transaction.

The product transaction is **candidate file vs accepted file**.

```text
failed construction must not partially mutate the accepted World
```

Constructor passes already write into pass workspaces rather than mutating a live published sqlite. v0 copies that idea without the nine directories.

### Candidate vs accepted

| | |
| --- | --- |
| Candidate | temp sqlite + sidecars; disposable |
| Accepted | the only World SQL/Python may treat as current |
| Rollback | keep previous accepted files; drop candidate |
| Revert | restore a previous accepted snapshot if the project keeps history; v0 may keep only `accepted` + `previous` (two generations) |
| Intra-file `_tv_view.revision` | EXISTING; useful inside one sqlite, not a substitute for candidate/accepted |

### Source-change

See §14. A changed source hash does not mutate accepted tuples. It marks the accepted World `SOURCE_MOVED` in the manifest. Reconstruction is a new candidate run.

---

## 9. Requirement and unresolved-state mechanics

Runtime mechanism:

```text
purpose.require*(...)
→ deterministic check over current relation tables
→ satisfied (no row) OR failure records
```

**Not** in the kernel:

```text
obligation factoring
parent/child REFINED
evidence packets
ranking heuristics
```

Those are host interpretations of failure records.

### Failure record grain — factual, not taxonomic

Reuse PFPS fields:

```text
requirement_id
failure_kind
relation
subject          # identifying role values / semantic_identity / source key
expected
observed
grounding
```

`failure_kind` vocabulary for v0 (closed, mechanical):

```text
NO_MATERIALIZABLE_PATH
CARDINALITY_OVERSATISFIED
CARDINALITY_UNDERSATISFIED
MULTIPLE_CANDIDATES
UNINTERPRETED
NOT_NUMERIC
NOT_ESTABLISHED          # required established-World, only PURPOSE_POLICY/UNVERIFIED present
EXPLICIT_UNRESOLVED
ABI_NO_BINDING
ABI_NOT_MATERIALIZABLE
ABI_AMBIGUOUS
```

No `NODI_FAMILY`, no `WHEN_DISCHARGING_FAMILY`. The host may later group `UNINTERPRETED` rows that share the same comment string. That grouping is not a stored type.

ABI failures (`NO_BINDING` / `NOT_MATERIALIZABLE` / `AMBIGUOUS`) are **EXISTING** Constructor v3.1.1 statuses. They belong in the same failure channel so the host sees them. They are not a second product.

---

## 10. Consumer ABI

Reconcile with post-v2 / v3.1.1. **Do not create a second ABI.**

### Stable identity

Consumer programs depend on **consumer field identity**, not constructor relation or role names (`ARCHITECTURE.md` §2; post-v2 §3, §8).

Representation:

```text
RoleSpec.semantic_identity          EXISTING
PurposeProjectionContract
  output_fields
  field_sources[consumer_field] = {semantic_identity, transform}
                                    EXISTING
```

v0 stores these in `world.contracts.json` / `world.purpose.json`.

Constructor-authored physical table and role names may vary (Probe B B1–B4). Identity is the binding, not the spelling.

### Deterministic Normalize / project

**EXISTING invariant (v3.1.1):**

```text
SATISFIED(f)  ⇒  f ∈ Normalize(W)
UNSATISFIED: NO_BINDING | NOT_MATERIALIZABLE
AMBIGUOUS: multiple roles in one relation claim the same semantic_identity
INCOMPLETE_PURPOSE before projection if required fields are not SATISFIED
```

No LLM at query time. No fuzzy name repair. Missing bindings fail locally.

**PROPOSED_V0:** the same functions, parameterized by the purpose's declared field set. Do **not** import diligence `REQUIRED_IDENTITIES` / `CANONICAL_RELATIONS` into a generic runtime. Those lists are **RESEARCH_ONLY** domain fixtures.

`semantic_family_hint` remains metadata with no runtime behavior (`contracts.py` header). **NOT_NEEDED** as a World type (post-v2 §6, §9).

### Absent materialization

Declared binding + empty World route → `ABI_NOT_MATERIALIZABLE` → purpose projection withheld. This already happened on diligence T1/T3 (`replay.py`). v0 keeps that fail-closed behavior.

Projected ABI tables may be:

- extra DERIVED relations registered by the runtime after Normalize, or
- a read-only query API that runs Normalize in process

Prefer DERIVED relations in the accepted sqlite so `query_semantic` sees a stable surface without a second database. Normalize must still be the single source of truth (ABI check calls the same function).

---

## 11. SQL surface

Three layers. Only the last two are stable.

| Surface | What | Stable? |
| --- | --- | --- |
| Raw World relations | Constructor-authored table names | No |
| Normalized semantic ABI | Tables/columns named by consumer identity | **Yes** (given a purpose contract) |
| Purpose projections | Purpose output relations | **Yes** for that purpose |

Consumers should query ABI / purpose projections. Raw World remains inspectable for grounding (`describe why`).

`TaskView.query_semantic` (**EXISTING**) already restricts SQL to declared semantic tables and blocks `_tv_*` and hidden ids. That is the programmer surface. v0 does not add a query DSL.

Illustrative shape only (not NPDES architecture):

```sql
-- Stable ABI: consumer field identities, not constructor spellings
SELECT period, parameter, reported_value, limit_value, comparison
FROM monitoring_result
WHERE outfall = '001';

-- Unresolved inspection (if failures are a PURPOSE relation)
SELECT requirement_id, failure_kind, affected_identity, COUNT(*) AS n
FROM purpose_requirement_failure
GROUP BY 1, 2, 3;

-- Grounded established fact remains ordinary SQL
SELECT *
FROM limit_applies
WHERE condition IS NOT NULL;
```

A programmer who `SELECT`s a raw constructor table named `tbl_dmr_join_v3` is outside the stability contract. That is acceptable; the ABI is the product promise.

G6 explorer SQL is **NOT_NEEDED** for v0. The same sqlite is what the explorer would later open.

---

## 12. Host / compiler responsibilities

Deliberately **not** runtime:

```text
purpose interpretation
source exploration
representation choice
construction.py authoring
join-selection reasoning
requirement selection
semantic obligation factoring
evidence planning
targeted retrieval
obligation refinement
scope inference
proposal / conversation
minimality / refactoring
```

> None of these names implies a kernel abstraction.

The host is an ordinary Python agent with source helpers, the commit API, and SQL. Prompts instructing it to act as a semantic integration engineer are **host configuration**, not modules.

Constructor P3–P5 (obligations, packets, dispositions) are one **RESEARCH_ONLY** host strategy. v0 must not require them.

---

## 13. Minimal human interaction

No UI. No forms. No ontology editor. No decision cards.

Contract only:

```text
host shows current understanding in ordinary language
host shows evidence and SQL/Python consequences when a change is consequential
user replies in natural language
host infers scope (World vs Purpose vs this-analysis)
host dry-runs by executing a candidate World (lifecycle §8)
host asks clarification only if plausible interpretations have materially different candidate diffs
on acceptance, commit goes through the same grounding/origin rules as construction.py
```

This is the conversational/proposal probes' boundary, kept **host-side**. Dry-run = candidate sqlite, not a new primitive.

The write boundary of `constructor_frontend_spec.md` §1.1 still applies if a review UI is built later:

```text
THE WORLD IS READ-ONLY.
CONSTRUCTION IS WHERE WRITES GO.
THE ONLY PATH FROM A VERDICT TO A WORLD TUPLE IS A REBUILD.
```

v0 already obeys that: acceptance replaces the candidate as a whole. No endpoint patches one tuple in accepted `world.sqlite`.

`world_ir_frontend_spec.md` §17 exclusions (write-back, workflow, actions) remain **NOT_NEEDED**.

---

## 14. Change / staleness model

Do not build incremental truth maintenance. TaskView already stales **derived** relations when input `relation_version` moves. BASE source-file movement is separate.

### Source versions

At accept time, `world.source_manifest.json` records path, size, and content hash for every file `construction.py` / helpers read (or, simpler and sufficient: every file under `sources/`).

`SourceObservation.source_revision` (**EXISTING**) should be that hash when assertions are SOURCE-grounded.

### What becomes stale

```text
source hash changed
  → accepted World status SOURCE_MOVED
  → DERIVED relations that depend on BASE tables are not automatically rerun
  → BASE tuples remain as historical claims about the previous evidence

construction.py changed but sources did not
  → not source staleness; it is a new candidate when the host runs
```

### Changed evidence does not make a fact false

Absence of the old bytes is not a denial. The World does not retract `limit_applies` because a CSV was edited. The host reconstructs. Unaffected accepted semantics remain **if** the new construction re-asserts the same tuples; they are not magically preserved by an incremental engine.

### What triggers reconstruction

Host decision, or a consumer noticing `SOURCE_MOVED`. No background watcher required in v0.

Unaffected semantics can remain across a rebuild because assertion ids are stable hashes of relation+values (`taskview.store._stable_id`). Re-asserting the same tuple is idempotent (`inserted=False`). That is enough.

---

## 15. Concrete repository shape

Do **not** add a top-level `semantic/` package that looks like a second kernel.

| Path | Role |
| --- | --- |
| `taskview/` | **EXISTING** foundation. Do not modify for v0. |
| `research/semantic_integration/core/` | **EXISTING** wrap. v0 may tighten `assert_tuple` grounding synthesis here later; that is still not TaskView. |
| `research/semantic_integration/domains/diligence/constructor_v3_1_1/runtime/{contracts,provenance,abi_completeness,normalizer}.py` | **EXISTING** ABI mechanism. Lift *invariants* into v0 research runtime; do not import diligence field lists as product. |
| `research/semantic_integration/domains/npdes/purpose_first_python_spine_v1/{world_api,source,runner}.py` | **EXISTING** loop prototype. `source.py` is the helper library to copy. `world_api.py` is in-memory and must not remain the store. |
| `research/semantic_integration/runtime_v0/` | **PROPOSED_V0 research package** (create only when implementing): `commit.py`, `purpose.py`, `abi.py`, `source_helpers.py`, `project.py` |
| `research/semantic_integration/domains/**` probes | **RESEARCH_ONLY** |
| `world_explorer/`, `frontend/` | **NOT_NEEDED** for v0 |
| `scripts/build_world.py` | BOM demo path. Do not hijack. |

`runtime_v0` is research code until a later productization explicitly graduates it. It must depend downward on TaskView. TaskView must not import it (`ARCHITECTURE.md` §5).

---

## 16. End-to-end vertical slice

Smallest fixture. **Do not** use the NPDES corpus.

```text
fixtures/v0_slice/
  sources/
    orders.csv          order_id, account_code, amount, comment
    accounts.csv        account_code, legal_name
    note.txt            one paragraph: "GM means geometric mean for TDS only"
  purpose.txt           "For each order, report legal_name and a numeric amount.
                         Leave non-numeric amounts unresolved."
```

Loop that proves v0:

1. Host reads purpose + profiles CSVs (helpers).
2. Host writes `construction.py`:
   - referents for accounts/orders
   - WORLD relation `order_amount` SOURCE-grounded from CSV
   - WORLD correspondence `account_code` join (structural overlap committed as identity only where the host asserts it)
   - `purpose.require_numeric(amount)`
   - one row with comment `GM` fails numeric → failure record
3. Runtime materializes candidate TaskView, validates grounding, accepts.
4. SQL `SELECT legal_name, amount FROM … ABI …` succeeds **without** opening CSVs.
5. Failure record exists for the GM row (`NOT_NUMERIC` / `UNINTERPRETED`).
6. Host revises `construction.py` using `note.txt` (targeted read): TDS-scoped interpretation **or** leaves it `purpose.unresolved`.
7. Second candidate run: either a derived numeric for the TDS case, or a sharper `EXPLICIT_UNRESOLVED` plus the rest still queryable.

If step 4 still requires CSVs, v0 has failed. If step 6 writes `REFINED` into sqlite, v0 has overfitted the experiments.

---

## 17. Implementation order

Derived from existing code: persist into TaskView first (it already exists), then fail-closed commit (Constructor already proved the check belongs outside the kernel), then purpose failures (PFPS), then generic ABI (v3.1.1 invariant minus domain lists), then consumer SQL, then source hashes.

| Increment | Becomes possible | Invariant tested | Deliberately postponed |
| --- | --- | --- | --- |
| 1. Persist `construction.py` into a candidate TaskView | Durable referents/relations/tuples | Ordinary Python can fill TaskView | Requirements, ABI, UI, P0–P8 |
| 2. Atomic candidate → accepted | Failed runs leave previous World intact | No partial accepted mutation | History beyond previous+accepted |
| 3. Fail-closed grounding | Ungrounded WORLD BASE cannot accept | SOURCE required; no origin-only WORLD synthesis | Full epistemic enum table |
| 4. Purpose require_* + failure records | Unresolved inspection via SQL/sidecar | Checks are deterministic; UNRESOLVED is not a fact | Obligation factoring |
| 5. Purpose/contracts sidecars + generic Normalize | Constructor names may vary; consumers bind identity | `SATISFIED ⇒ materialized`; no second ABI | Diligence canonical relation library |
| 6. SQL/Python on accepted ABI tables | Query without raw sources | `query_semantic` over projected relations | Explorer UI |
| 7. `source_manifest` + SOURCE_MOVED | Source change is visible, not a silent denial | Hashes recorded; no auto-retract | Incremental TMS |

Conversational automation, targeted prose retrieval campaigns, and Constructor passes are **not** in this sequence.

---

## 18. Deletion test

| Mechanism | Concrete necessity | Delete from v0? |
| --- | --- | --- |
| TaskView referents/relations/assertions | No durable World | No |
| `_tv_groundings` | Cannot fail closed or cite sources | No |
| Derivations | Maintained SQL computation | No (even the slice's ABI projection may use them) |
| Origins sidecar | Who-decided vs how-entered | No |
| Fail-closed SOURCE rule for WORLD BASE | Model proposals become World law | No |
| Purpose sidecar + require_* | Unresolved is undefined; purpose is prompt-only | No |
| Failure records | Cannot inspect unresolved without raw sources | No |
| `semantic_identity` / `field_sources` | Post-v2: synonymous role names miss consumers | No |
| Deterministic Normalize + ABI check | LLM projection at query time; silent misses | No |
| Candidate vs accepted files | Partial mutation of published World | No |
| Source helpers library | Host cannot inspect folder boringly | No (but they are not World) |
| Source manifest hashes | Cannot tell World from moved evidence | No |
| WORLD vs PURPOSE admission sidecar | Purpose policy masquerades as World | No |
| Epistemic status table | Commit policy already distinguishes established vs unverified | **Yes — delete** |
| Obligation / REFINED tables | Host can group failure rows | **Yes — delete** |
| Evidence-plan store | Reconstructible retrieval | **Yes — delete** |
| P0–P8 pass machine | Spine loop does not need it | **Yes — delete from v0** |
| Semantic-family types | Post-v2: not required | **Yes — delete** |
| Persistent Source IR | Helpers regenerate | **Yes — delete** |
| Explorer UI | SQL/Python suffice | **Yes — delete** |
| Conversational proposal engine | Host can dry-run candidates manually | **Yes — delete from v0** |
| Two-generation revert | Nice; one accepted file still proves the loop | Defer |
| In-memory PFPS `World` as store | Would lose SQL reuse of TaskView | **Yes — do not ship** |

If the architecture still looks large after this table, the extras are almost all sidecars that Constructor already had, not new ontology.

---

## 19. Open decisions

Fewer than ten. Not re-litigating sealed experiments (ordinary Python construction, no family types, UNRESOLVED is success, contracts not relation names).

| # | Decision | When |
| --- | --- | --- |
| 1 | Failure records as a PURPOSE relation in sqlite vs `world.failures.json` only | **Must decide before coding** |
| 2 | PURPOSE-scoped tables in the same sqlite as WORLD vs a second purpose sqlite | **Must decide before coding.** Recommend one sqlite + admission sidecar (Constructor P6 already admits PURPOSE counts that may not enter `06_world`). |
| 3 | Construction API names: wrap `SemanticWorld` vs PFPS `World.referent/map` sugar | **Must decide before coding.** Recommend SemanticWorld names; keep PFPS `require_*`. |
| 4 | Tighten grounding in `SemanticWorld.assert_tuple` vs only `validate_provenance` at commit | **Must decide before coding.** Recommend both: API refuses WORLD BASE without SOURCE; commit re-validates. |
| 5 | ABI projection as DERIVED tables vs in-process Normalize at query | Can **defer** if ABI check already calls Normalize; pick DERIVED before any UI. |
| 6 | Keep `previous` accepted generation or only current | **Defer** |
| 7 | Exact source-manifest granularity (whole `sources/` vs files actually read) | **Defer**; whole folder is simpler |
| 8 | Whether user-certified policy needs a durable certification artifact besides origins=`ADJUDICATED` | Can **defer**; ADJUDICATED + PURPOSE scope is enough for the slice |
| 9 | Graduation of `runtime_v0` out of `research/` | **Requires a product decision**, not new semantic evidence |

None of these is a kernel counterexample.

---

## 20. Proposed v0 size

After deletion:

```text
new persistent TaskView tables              0
sidecars beyond today's origins             ~4 (purpose, contracts, admission, source_manifest)
                                            + failures if not a relation
core runtime modules                        ~5 (commit, purpose, abi, source_helpers, project)
public Python commit operations             ~8 (add_referent, declare_relation, assert_tuple,
                                               retract, register_derivation, rerun,
                                               purpose.require_*, purpose.unresolved)
deterministic validators                    3 (grounding/established-World, ABI materializability,
                                               atomic candidate accept)
host-specific mechanisms in product code    0
```

That is small enough to be software. The intelligence stays in the host that writes `construction.py`.

Existing code this size **already almost is**: TaskView + Constructor provenance/ABI + PFPS runner. v0 is the **join** of those three, minus the nine-pass machine and minus in-memory World.

---

## Final judgment

```text
V0_IMPLEMENTATION_SHAPE_COHERENT
```

A small implementation can reuse TaskView as the foundation, reuse Constructor v3.1.1 **contract / provenance / materializability invariants** without a second ABI, and support the synthesis loop by persisting the Purpose-First Python Spine into a candidate SQLite World.

No correctness counterexample in the sealed experiments requires changing the frozen semantic calculus (thin referents, named typed n-ary relations, derivations). Scope ≠ admission is enforceable by commit policy and sidecars that already exist in spirit (`origins.json`, `06_admission.json`, `RoleSpec.semantic_identity`).

The design is coherent **only if** v0 does not:

- modify TaskView
- promote `REFINED` / obligations into the kernel
- import diligence canonical fields as the generic ABI
- keep PFPS in-memory World as the store
- treat `SemanticWorld`'s origin-only WORLD grounding as established truth

Those are implementation hazards, not foundational gaps.

---

## STOP

This document is a research implementation spec.

It does not implement the loop.  
It does not modify TaskView, Constructor, kernel, `ARCHITECTURE.md`, or frontend specs.  
It does not begin a migration.
