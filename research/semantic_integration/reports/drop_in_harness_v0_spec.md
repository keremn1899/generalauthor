# Drop-in Harness v0 — Footprint, Lifecycle, and Boundaries

**Status:** design specification only. Not an implementation.  
**Foundation:** frozen Spike 1 `runtime_v0` (`SPIKE1_RUNTIME_LOOP_SUPPORTED`) over TaskView.  
**Judgment:** `DROP_IN_HARNESS_SHAPE_COHERENT`

The harness is a **guest** in an arbitrary existing workspace. It compiles heterogeneous evidence into a grounded programmable World, then stays out of the agent's way. Permanent software handles invariants. Agent intelligence handles strategies.

```text
semantic compilation
+ durable grounded World
+ compact semantic header
+ ordinary SQL/Python access
+ hard epistemic/lifecycle invariants
```

Nothing else is the harness.

The hidden directory name is an open decision. This document writes it as `.<product>/`. Examples are not a naming vote.

---

## 0. Premises (not reopened)

- TaskView is the SQLite World. No new semantic kernel.
- Thin referents, typed n-ary relations, derivations.
- WORLD BASE fails closed without SOURCE grounding.
- PURPOSE is purpose-specific analytical / unresolved state, not external World truth.
- Candidate → accepted publication is the only product transaction that changes accepted semantic state.
- Purpose failures are an ordinary PURPOSE relation (`purpose_requirement_failure`).
- Sources are read-side with respect to compilation. No persistent Source IR.
- Compact header (PURPOSE, WORLD CONTRACT, READ RULES, REVISION) is sufficient initial context.
- SQL + Python are sufficient computation. No graph API, leads, summaries, or exploration planner.
- Do not promote obligations, REFINED, evidence plans, proposals, app registries, or workflow machinery.

Inspected for this spec: `runtime_v0/{world,purpose,source_helpers,commit,project}.py`, `core/{kernel,origins,source}.py`, Spike 1 report, v0 implementation spec §3 sidecars.

---

## 1. Workspace model

**Workspace root** is a directory the host passes to attach/open. Any directory. A git repository is not required.

**Drop-in** means: given that directory (and a purpose on first compile), the harness locates or creates `.<product>/` under it and thereafter mutates only that tree as harness lifecycle. The user does not reorganize the workspace.

**Filesystem semantics only.** No workspace-management service.

| Question | v0 answer |
| --- | --- |
| Any directory as root? | Yes. |
| Repository required? | No. |
| Files outside `.<product>/` mutated by harness lifecycle? | No. They are user/project artifacts. The harness may read them. An agent may edit them for the *user's task*; that is not harness lifecycle. |
| Read-only workspace? | v0 cannot write `.<product>/`. Fail locally, inspectable. Do not silently use external state. See §13. |
| Sources outside the root? | Observationally allowed (absolute path recorded). Portability breaks. Prefer workspace-relative paths. |
| Symlinks, mounts, connected files? | Ordinary OS semantics. Hash the bytes observed. Record the path as presented. No special resource graph. |
| Multiple harness roots in one tree? | v0: one `.<product>/` per attached root. Nested workspaces are just nested directories; attaching a child does not own the parent. |

Do not invent include/exclude engines, workspace IDs, or a catalog of workspaces.

---

## 2. Source discovery

There is no required `sources/` directory.

The agent discovers evidence with ordinary tools (list, read, SQL, Python) during construction. The user *may* constrain the evidence set (a path list or glob in the purpose sidecar). Absence of a constraint means: explore the workspace normally, excluding `.<product>/`.

Three grades, not three stores:

| Grade | What it is | Durable? |
| --- | --- | --- |
| Workspace artifact | Any file the OS can see | User-owned |
| Candidate evidence | What the agent looked at | Ephemeral (trace, not harness state) |
| Actually used source | Bytes that SOURCE-ground an accepted WORLD assertion | Recorded as grounding pointers + hashes, not copied |

**Source manifest is an output of construction**, not an input IR.

Prefer: workspace-relative path + content hash + native location (row/span), which Spike 1 already puts on `SourceObservation` (`native_handle`, `source_revision`, `native_location`) and TaskView `_tv_groundings`.

Do **not** copy source bodies into `.<product>/` unless a later correctness case demands it (none does today: Spike 1 SQL still answered after unlinking CSVs because the World holds the compiled tuples).

Do **not** create a persistent Source IR.

`Source` today is rooted at `Project.sources_dir` (`runtime_v0/project.py`). Drop-in needs a small change: helpers rooted at the **workspace root** (or an explicit path list), emitting workspace-relative `native_handle`s. That is not a new IR.

---

## 3. Harness-owned footprint

Spike 1 already publishes, beside the sqlite:

```text
world.sqlite
world.sqlite.origins.json
world.admission.json
world.purpose.json
```

`Project` currently also assumes, at the *project* root:

```text
construction.py
purpose.txt
sources/          # convention — drop
candidate/
accepted/
```

### Classification

| Artifact | Class | Why |
| --- | --- | --- |
| `world.sqlite` | **REQUIRED** (accepted) | The World. Delete it → compiled meaning is gone. |
| `world.sqlite.origins.json` | **REQUIRED** | `ConstructionOrigin` is not a TaskView column. Delete it → MECHANICAL/SEMANTIC/DERIVED/ADJUDICATED is lost. Do not fold into TaskView. |
| `world.admission.json` | **REQUIRED** | WORLD vs PURPOSE is not a TaskView column. Delete it → PURPOSE overlays become indistinguishable from World truth. Do not add a `_tv_*` table to avoid the sidecar. |
| `world.purpose.json` | **REQUIRED** | Declared purpose text + recorded `require_*` list as compiled. Header PURPOSE and reconstructibility. |
| `construction.py` | **REQUIRED** | Reusable compiler. Delete it → World still *readable*, but semantic compilation work cannot be replayed. Not itself World truth. |
| `purpose.txt` | **NOT_NEEDED** as a second file | Collapse into `world.purpose.json` (`text`) plus the in-progress declared purpose written there before rebuild. Spike 1's separate `purpose.txt` was a fixture convenience. |
| `source_manifest.json` | **OPTIONAL** | Distinct SOURCE `(path, hash)` pairs are already in `_tv_groundings`. A denormalized receipt speeds staleness listing. If kept, it must be generated at accept, not hand-authored. |
| `contracts.json` / ABI | **NOT_NEEDED** | Deferred. Constructor-authored names are the physical interface. |
| `candidate/` | **TRANSIENT** | Isolated build. Discarded on failure; consumed on accept. |
| `accepted/` | **REQUIRED** as a directory *role* | Holds the published sqlite + required sidecars. Name may be the harness root itself; a subdirectory matches existing `publish_candidate`. |
| `cache/` | **NOT_NEEDED** | No watcher, no incremental TM, no precomputed exploration. |
| `last_error.json` | **OPTIONAL** | Makes the last failed candidate inspectable after discard. Reconstructible from a preserved failed candidate; v0 may write a small receipt instead of keeping the whole tree. |
| `accepted.previous` | **TRANSIENT crash window only** | Today's `publish_candidate` already renames through `.previous` then deletes it. Not a retained generation. See §5. |
| `.demand.json` / Constructor P0–P8 | **NOT_NEEDED** | Wrong lineage. |
| Copied sources | **NOT_NEEDED** | Grounding pointers suffice. |

**Collapse already justified:** `purpose.txt` into `world.purpose.json`.  
**Do not collapse** origins or admission into sqlite (would be a TaskView/kernel change).  
**Do not collapse** construction.py into the sqlite (code is not a tuple).

---

## 4. Ownership boundary

> The harness may freely mutate only `.<product>/` as part of its lifecycle.

| Kind | Who | Where |
| --- | --- | --- |
| Harness mutation | Runtime commit/publish | `.<product>/` only |
| Source observation | Read | Anywhere the agent/runtime can open; no write |
| Agent task mutation | Agent, for the user's project task | Ordinary workspace files; **outside** the semantic-harness contract |

No permissions framework, sandbox product, or ACL. If the host already sandboxes the agent, that is operational, not this spec.

---

## 5. Candidate / accepted lifecycle

Reuse Spike 1 `commit.py` semantics. Relocate the directories under `.<product>/`.

```text
1. attach(workspace_root)
2. load .<product>/ if present
3. receive declared purpose (first run or explicit update)
4. agent explores the workspace (not .<product>/ as evidence)
5. agent authors/revises .<product>/construction.py
6. runtime builds isolated .<product>/candidate/
7. validate (WORLD BASE SOURCE scan; construction errors)
8. atomically publish candidate → accepted, or discard candidate
9. expose accepted World + compact header
10. agent reads/programs with SQL/Python
```

**Candidate location:** `.<product>/candidate/` (transient).  
**Accepted location:** `.<product>/accepted/` containing the four required World files.  
**Validation boundary:** `ConstructionWorld.assert_tuple` refuse + `validate_world_base_source` at accept. PURPOSE may omit SOURCE.  
**Atomicity:** keep `publish_candidate`: copy to `accepted.staging`, rename `accepted` → `accepted.previous`, rename staging → `accepted`, delete previous, delete candidate.  
**Failure:** discard candidate; **accepted bytes unchanged** (already tested). Workspace files outside `.<product>/` untouched.  
**Process death mid-publish:** if `accepted/` is missing and `accepted.previous` exists, reopen recovers `previous` → `accepted` and reports a crashed publish. No retained history beyond that crash window.  
**Previous generation as a product feature:** not in v0.  
**Patch accepted in place:** never. The only path to changed accepted semantic state is reconstruction / accepted candidate publication.

---

## 6. First-run behavior

Inputs:

```text
workspace root
+
declared purpose (natural language)
```

User-visible: the workspace looks as it did. The agent explores it. Compilation, if it succeeds, leaves a hidden `.<product>/`. No schema upload, source wizard, ontology form, or project template.

Initializing the hidden directory is an implementation detail. It is not a user-facing “create project” step.

`sources/` is not created.

---

## 7. Reopen behavior

```text
discover .<product>/accepted/world.sqlite
→ read sidecars; fail inspectably if inconsistent (see §17)
→ derive compact header
→ agent operates immediately
```

No reconstruction merely to use the World. No row preload. No summaries, leads, or exploration plans.

---

## 8. Compact read contract

Derived cheaply at reopen from sqlite + admission + purpose sidecar + `_tv_view.revision`. Already prototyped in the exploration probe as header-only (no rows).

**PURPOSE** — `world.purpose.json` `text`.

**WORLD CONTRACT** — for each admitted relation: name; constructor `description` or “(none provided)”; ordered roles/types from TaskView; WORLD | PURPOSE; BASE | DERIVED. Do not block on missing descriptions.

**READ RULES** (stable host text, not World tuples):

```text
Unresolved / insufficient / unknown / uninterpreted is not false.
An empty result alone means no matching tuple was observed, not established absence.
PURPOSE relations are purpose-specific analytical state and do not replace more direct WORLD facts.
Unknown neighboring propositions do not invalidate independently established propositions unless an explicit dependency says so.
Inspect grounding when evidential status matters.
```

**REVISION** — `view_id` + schema/view revision from TaskView (Spike 1 `WORLD_ID = "v0"` plus `_tv_view.revision`). Optionally include hashes of accepted files (`fingerprint_accepted` already exists).

No verbose bundle.

---

## 9. Purpose lifecycle

v0: **one current declared purpose per accepted World.**

Purpose is **compiler input plus the compact-header contract**, not a project identity and not a multi-purpose accumulator.

| Change | Rebuild? |
| --- | --- |
| Typo in purpose text that does not change what must be decided | Conservative: still rebuild if the stored purpose string would disagree with the header. Do not silently edit `world.purpose.json` on an accepted World. |
| New questions / different sufficiency frontier | Rebuild. |
| Same purpose, more evidence | Rebuild (new candidate). |
| “Reuse this World for a different purpose” | Not a v0 operation. A later purpose may *read* the World as data; it does not become that World’s PURPOSE without reconstruction. |

Multi-purpose accumulation is future pressure (ABI / stable identities). Not designed here.

---

## 10. Source change / staleness

Changed evidence **triggers reconsideration**. It does **not** automatically make old claims false.

The accepted World remains **historical / current-at-build** semantic state until a new candidate is accepted.

Mechanical detection from SOURCE groundings (and optional manifest):

| Event | Detectable? | Consumer may assume until rebuild |
| --- | --- | --- |
| Source unchanged (path+hash match) | Yes | World still matches those bytes |
| Source modified (hash mismatch) | Yes | World is stale relative to that file; tuples are not thereby false |
| Source deleted | Yes (path missing) | Same: stale, not retracted |
| Source moved/renamed | Path miss + possible hash hit elsewhere: **best-effort**, not solved | Stale at old path |
| New file appears | Not unless listed as used. Do not scan the whole disk as a watcher. Agent/user may notice and rebuild | Unincorporated; not a World denial |

No background watchers. No incremental truth maintenance. Reconstruction creates a new candidate.

---

## 11. Construction program lifecycle

`.<product>/construction.py` is **required durable compiler state**.

- Lives inside harness state (not a user `src/` convention).
- Agent may revise it. Humans may inspect/edit it.
- It is not semantic truth. The accepted World is.
- At accept, record its hash in `world.purpose.json` (or a one-line `construction.receipt`) — **open: exact field**, but the receipt is justified so reopen can say “program drifted.”
- If `construction.py` changes without rebuild: accepted World **unchanged**. Receipt mismatch is inspectable staleness of the *compiler*, not of World tuples.

---

## 12. Workspace portability

Smallest assumption for “copy/zip/clone/move the workspace and the harness still works”:

```text
all actually-used sources are inside the workspace root
SOURCE native_handle values are workspace-relative
.<product>/ is copied with the workspace
```

What breaks:

| Break | Why |
| --- | --- |
| Absolute paths outside the tree | Copy does not take those files |
| Connected services / live URLs as sources | Not in the zip |
| Environment-specific deps of `construction.py` | Python import graph is not the World |

v0 does not solve remote sync. Relative references are the portability contract.

---

## 13. External-state mode

```text
~/.local/.../<workspace-id>/
```

**DEFER.** Needed later for read-only or “do not touch this repo” trees. v0 prefers one local hidden directory. Do not implement dual-root lookup until a concrete host requires it.

---

## 14. Reusable applications and project artifacts

Dashboards, `analysis.py`, notebooks, models, reports, web apps, visualizers, optimizers are **ordinary workspace artifacts**. The agent places them wherever the existing project already keeps such things.

No `apps/`, no registry, no application manifest in v0.

**Future pressure (not designed):** a persistent program that joins `job_charge` will break when a later construction names that relation `tow_charge`. That is the strongest current motivation for a deferred semantic ABI / `semantic_identity` — a **consumer stability** problem, not a drop-in footprint problem. ABI remains deferred.

---

## 15. Persistence boundary

```text
WORLD     .<product>/accepted/     durable semantic commitments
PROJECT   anywhere else            ordinary reusable files/programs
SCRATCH   agent tmp / chat         ephemeral reasoning
```

The harness stores only WORLD. It does not store PROJECT or SCRATCH.

Deletion test: §18.

---

## 16. Security / trust (v0 minimum)

- Raw evidence is read-side for compilation.
- Accepted World is never patched in place.
- `.<product>/` is writable by the harness; that is the trust boundary for semantic mutation.
- Agent edits elsewhere are outside the semantic-harness contract.
- Ungrounded WORLD BASE cannot enter accepted World (`GroundingError` + accept scan).

No RBAC, multi-user auth, policy engine, or secrets product.

---

## 17. Failure behavior

Bias: fail locally; preserve accepted; make the problem inspectable; do not silently repair semantic state.

| Failure | Observe | Accepted World | Workspace files |
| --- | --- | --- | --- |
| `construction.py` crashes | `RunResult` reason `construction_error`; optional `last_error.json` | Unchanged | Unchanged |
| Validation / ungrounded WORLD | reason `ungrounded_world_base`; candidate discarded | Unchanged | Unchanged |
| SQLite candidate corrupt | construction/open error; discard | Unchanged | Unchanged |
| Source missing at rebuild | construction or grounding error | Prior accepted remains | Unchanged |
| Accepted World missing | cannot consume; if `.previous` exists, recover once (§5) | — | Unchanged |
| Sidecar missing/inconsistent | fail open-for-consume inspectably (need admission to know PURPOSE) | Do not invent admission | Unchanged |

**Reconstructible:** candidate tree, header, optional manifest (from groundings).  
**Irreplaceable without rebuild:** accepted sqlite + origins + admission + purpose, and `construction.py` as the replayable compiler.

Do not auto-heal origins or admission from guesses.

---

## 18. Deletion test

| Component | Why needed | If deleted | Regenerable? | Durable / transient |
| --- | --- | --- | --- | --- |
| `accepted/world.sqlite` | Semantic state | Meaning gone | Only by rerunning construction against sources | Durable |
| `accepted/world.sqlite.origins.json` | Who decided | Origin axis gone | No (not in TaskView) | Durable |
| `accepted/world.admission.json` | WORLD vs PURPOSE | Scope collapse | No without TaskView change | Durable |
| `accepted/world.purpose.json` | Purpose + requirements + optional construction hash | Header PURPOSE gone | Partial from memory, not from sqlite | Durable |
| `construction.py` | Replayable compiler | Cannot rebuild faithfully | No | Durable |
| `source_manifest.json` | Convenience staleness list | Walk `_tv_groundings` | Yes | Optional durable |
| `candidate/` | Isolated build | In-flight compile lost | Yes | Transient |
| `last_error.json` | Inspect last fail | Rerun to see | Yes | Optional |
| `cache/` | — | — | — | Not needed |
| Copied sources | — | — | — | Not needed |
| `sources/` convention | — | — | — | Not needed |
| App registry | — | — | — | Not needed |

---

## 19. Explicit non-goals

```text
required project layout
sources/ convention
apps/ convention
workspace/ convention
application framework
graph interface / graph database
ontology UI
exploration planner
domain summaries
purpose leads
persistent Source IR
workflow system
write-back to sources
multi-user collaboration
enterprise authorization
incremental truth-maintenance engine
background file watcher
general artifact registry
Constructor P0–P8 as the drop-in loop
BOM demand.json
world explorer / G6 as a harness requirement
ABI / semantic_identity in v0
external-state mode
retained generation history
```

---

## 20. Concrete examples

### Existing software repository

```text
repo/
    src/
    docs/
    data/
    notebooks/
    ...
    .<product>/
        construction.py
        candidate/          # absent except during a build
        accepted/
            world.sqlite
            world.sqlite.origins.json
            world.admission.json
            world.purpose.json
```

`data/` stays `data/`. The harness does not move it.

### Existing messy evidence folder

```text
diligence-room/
    export.csv
    contracts/
    notes.docx
    model.xlsx
    ...
    .<product>/
        construction.py
        accepted/
            ...
```

### Greenfield

An agent **may** create:

```text
new-project/
    sources/
    analysis/
    reports/
    .<product>/
        ...
```

That layout is an **agent/user project convention**, not a harness invariant. The harness would work equally if those folders did not exist.

---

## 21. Deterministic acceptance tests (not implemented here)

Engineering tests that should follow implementation:

1. Drop into an arbitrary existing directory; no `sources/` required.
2. Harness lifecycle does not touch unrelated workspace files (fingerprint them).
3. Failed candidate preserves accepted World fingerprints (`test_runtime_v0_spike1.py` already has this grain).
4. Failed candidate preserves workspace files outside `.<product>/`.
5. Delete `.<product>/` → remainder of workspace intact.
6. Copy/move workspace with relative SOURCE handles → World still opens; staleness scan still matches.
7. Absolute external source → documented portability break (test the warning, not magic repair).
8. Reopen accepted World without reconstruction; header derivable.
9. Source hash change detected; accepted tuples not auto-retracted.
10. `construction.py` edit does not mutate accepted sqlite.
11. Generated `analysis.py` may live at workspace root or under `reports/`; harness ignores it.
12. Read-only workspace → inspectable failure, no external-state fallback in v0.
13. Crash after `accepted → previous` and before staging rename → recover previous.
14. Missing `world.admission.json` → consume fails closed, no invented WORLD-default.

---

## 22. Open decisions

Fewer than ten. Implementation-blocking only.

1. **Hidden directory name** (`.<product>/`).
2. **Accepted as `.<product>/accepted/` vs files directly in `.<product>/`.** Subdirectory matches existing `publish_candidate` and keeps `construction.py` off the published World tree. Prefer subdirectory.
3. **Whether `source_manifest.json` is written** or staleness is always derived from `_tv_groundings`.
4. **Exact receipt field** for `construction.py` hash (inside `world.purpose.json` vs tiny sibling).
5. **External-state mode** — classified DEFER, listed so it is not “forgotten,” not designed.
6. **Optional `last_error.json` vs preserving a failed candidate tree** — prefer a small receipt; trees get large.
7. **Evidence constraint file** (optional path list). Default: none.

Not reopened: TaskView schema, kernel calculus, ABI, graph API, multi-purpose Worlds, retained generations as a product feature.

---

## 23. Relationship to existing `runtime_v0`

| Existing | Disposition |
| --- | --- |
| `ConstructionWorld` fail-closed WORLD BASE | **Reuse unchanged** |
| `validate_world_base_source` / `publish_candidate` / `discard_candidate` / `fingerprint_accepted` | **Reuse unchanged** (paths become under `.<product>/`) |
| `purpose_requirement_failure` + `Purpose.require_*` | **Reuse unchanged** |
| `.origins.json` via `SemanticWorld` | **Reuse unchanged** |
| `world.admission.json` + `world.purpose.json` sidecars | **Reuse unchanged** |
| TaskView / `SemanticWorld` / no new `_tv_*` | **Reuse unchanged** |
| `Project.sources_dir = root / "sources"` | **Small change** — no required `sources/`; `Source` rooted at workspace (or explicit paths) |
| `Project` candidate/accepted at *workspace* root | **Small change** — nest under `.<product>/` |
| `purpose.txt` sibling of `construction.py` at project root | **Small change** — purpose lives in `world.purpose.json`; first-run purpose is an argument, then that sidecar |
| `Source.tables()` only `.csv`/`.json` under `sources/` | **Small change** — helpers remain optional; agent may read any file with ordinary Python; structured helpers take workspace-relative paths |
| Compact header derivation | **New v0 work** (read-only; already sketched in exploration probe, not in runtime) |
| Staleness listing from SOURCE hashes | **New v0 work** (mechanical, no watcher) |
| Attach/open workspace without Project layout | **New v0 work** (thin host API around existing `Project.run` / `open_accepted`) |
| Crash recovery of `accepted.previous` | **Small change** to publish/open |
| Constructor v3, explorer UI, ABI, graph | **Not needed** |
| TaskView schema or kernel change to avoid sidecars | **Not needed** — no invariant requires it |

Desired drop-in shape does **not** require changing TaskView or the semantic kernel. Sidecars exist because origin and WORLD/PURPOSE are not TaskView columns; that is already the frozen design.

---

## Final shape

```text
arbitrary-workspace/
    ... user-owned contents (untouched by harness lifecycle) ...

    .<product>/                          # name: open decision
        construction.py                  # DURABLE compiler (not World truth)
        candidate/                       # TRANSIENT (absent at rest)
        accepted/                        # DURABLE published World
            world.sqlite
            world.sqlite.origins.json
            world.admission.json
            world.purpose.json           # purpose text + requirements
                                         #   + construction hash receipt
```

| | |
| --- | --- |
| DURABLE | `construction.py`, `accepted/*` required four |
| TRANSIENT | `candidate/`, publish staging/previous |
| RECONSTRUCTIBLE | compact header, optional source manifest, last-error receipt |

Optional only if an implementer wants them: `source_manifest.json`, `last_error.json`.

### Lifecycle (10 steps)

1. Attach a directory as workspace root.  
2. If `.<product>/accepted/` exists, open it and expose the compact header.  
3. If not, take a declared purpose and create `.<product>/`.  
4. Agent explores the existing workspace; it does not invent a project layout.  
5. Agent writes `.<product>/construction.py`.  
6. Runtime executes it into `candidate/`.  
7. Validate WORLD BASE SOURCE (and construction errors).  
8. Publish atomically to `accepted/` or discard `candidate/` and keep prior accepted.  
9. Agent consumes via header + SQL/Python. No rebuild to read.  
10. Source or purpose or construction-program drift is detectable; only a new accepted candidate changes World truth.

---

## Judgment

```text
DROP_IN_HARNESS_SHAPE_COHERENT
```

The Spike 1 runtime already is the compile/validate/publish loop. Drop-in is a **relocation and decoupling** (`sources/` and workspace-root `accepted/` are fixture conventions, not invariants), plus a cheap header and a mechanical staleness list. It is not a platform, and it does not need a TaskView or kernel change.

---

## STOP

Do not implement the harness from this document in the same pass. Do not modify `runtime_v0`, TaskView, Constructor, architecture specs, or ABI.
