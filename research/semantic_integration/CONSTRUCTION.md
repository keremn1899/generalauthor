# Construction architecture

**Status:** product-shaped construction story for World IR.  
**Authority for semantics:** [`CONSTITUTION.md`](CONSTITUTION.md).  
**Not:** a new constructor, a pass machine, or a second calculus.

This document says how a World is made. It does not add semantic kinds.

---

## 1. The loop

```text
purpose + heterogeneous workspace
            ↓
     capable construction agent
            ↓
 arbitrary programming / exploration
            ↓
       World construction boundary
            ↓
        candidate World
            ↓
 deterministic validation / publication
            ↓
        accepted World
```

That is the product construction architecture.

The agent's internal artifact shape is not part of the architecture. One program, several programs, a nine-pass research compiler, or another strategy are all allowed if they produce a candidate that satisfies the constitution.

Consumers then use the accepted World with SQL, Python, agents, and the read-side explorer, without rereading the heterogeneous sources.

---

## 2. What lives where

```text
CONSTRUCTION AGENT                    CONSTRUCTION BOUNDARY
─────────────────                     ─────────────────────
understand purpose                    candidate TaskView sqlite
inspect the workspace                 grounding / origin / admission sidecars
write ordinary code                   purpose requirements + failures
convert, parse, join, profile         WORLD BASE SOURCE check
invent helpers and temp files         atomic publish or discard
choose distinctions
declare World vs Purpose
leave unsupported meaning unresolved

ACCEPTED WORLD                        NOT WORLD
──────────────                        ────────
referents, relations, tuples          source files
derivations                           inspection caches
grounding pointers                    helper modules, temp DBs, parsers
purpose contract + unresolved rows    evidence packets, obligations, prompts
construction-origin account           nine-pass JSON, transcripts
```

The hard split, repeated across the experiments:

> Let the agent compute freely. Make durable semantic commitment constrained.

---

## 3. Current mechanism: `runtime_v0`

`research/semantic_integration/runtime_v0/` is a supported construction-boundary implementation. It is not ontology.

Today it does this:

1. Read `purpose.txt` and `construction.py` from a project root.
2. Execute `construct(source, world, purpose)` against a **candidate** directory.
3. Require WORLD BASE SOURCE grounding at assert time and again at accept.
4. Persist purpose payload and WORLD/PURPOSE admission as sidecars.
5. On success, publish candidate → accepted as a directory rename.
6. On any failure or ungrounded WORLD BASE, delete the candidate. Accepted fingerprints stay put.

`construction.py` is a strongly supported authoring shape: ordinary Python, the language the Purpose-First spine showed was sufficient to recover distinctions a custom IR had missed. The filename, the `construct(...)` signature, and the helper types are replaceable. Agent-authored semantic compilation is not.

`Source` helpers (list, schema, sample, profile, read) are reconstructible. They are not a Source IR. Native support for every file format is not a kernel responsibility.

Spike 1 sealed `SPIKE1_RUNTIME_LOOP_SUPPORTED`. Capability end-to-end v1 sealed `END_TO_END_SEMANTIC_COMPILATION_SUPPORTED` on three small domains using this runtime. Those results are evidence that the boundary works; they are not a claim that the top construction surface is finished.

---

## 4. Research constructor (P0–P8) — evidence, not workflow

The diligence/NPDES nine-pass constructor is a research compiler:

```text
P0 intention → P1 vocabulary → P2 mechanical
→ P3 frontier → P4 packets → P5 adjudicate → P6 admit
→ P7 derive → P8 project
```

Isolated LLM passes write artifacts; the host validates and materializes. `world_explorer/construction.py` and `constructor_frontend_spec.md` read that artifact shape. They are a review surface over that compiler, not the product construction ontology.

Keep the invariants that compiler earned:

- WORLD vs PURPOSE admission;
- provenance / SOURCE grounding on durable WORLD BASE;
- fail-closed ABI materializability (`SATISFIED ⇒` actually in `Normalize(W)`);
- machine checks that can refuse even when the process exits 0;
- no experimental Probe A/B or cue-verifier imports in default runtime.

Do not require a future agent to emit `00_intention_contract.json` through `08_outputs`. Do not describe Constructor v3.1.1 as generic heterogeneous-source ingestion. v3.1.1 is a fail-closed materializability hardening of this research constructor (declared bindings that cannot be materialized become `INCOMPLETE_PURPOSE` before projection). The kernel hash did not change.

`domains/npdes/kernel_assets/KERNEL.md` is a frozen *research* construction brief (C0–C4). It is not this product architecture.

---

## 5. Construction-agent brief

Give the agent the destination, not a workflow. Exact API names in any one runtime may differ; the contract does not.

### Product

You are helping build a local semantic compilation layer. A user has a purpose and a folder of heterogeneous authoritative evidence. Your job is to construct the smallest grounded World that is sufficient for that purpose, and to leave unsupported meaning explicitly unresolved. The World must be reusable: later SQL, Python, and agents should compute over it without reconstructing source-specific semantics from the original files.

The runtime does not author interpretation. You do. A human owns publication and any later verdict. Failed attempts must not mutate an already-accepted World.

### Purpose

The user's purpose is the bound on attention and the definition of sufficiency. Understand it. Do not begin by exhaustively modelling the folder. Do not treat purpose-specific policy, thresholds, or analysis-only labels as World truth. Test: if this purpose disappeared, would the proposition still have the same meaning and truth conditions? If no, it is Purpose-scoped.

### World

A World is thin referents, named typed n-ary relations, and deterministic derivations, with grounding, construction origin, revision, stale/current, scope/completeness, and explicit unresolvedness. See `CONSTITUTION.md`. It is not a property graph, not a document store, and not a copy of the sources.

### Validity boundary

You may explore and program without limit above the boundary. You may only durably claim what the constitution allows. In particular:

- WORLD BASE assertions need establishing SOURCE grounding.
- Derived rows come from registered deterministic computation, not hand-inserted “derived” facts.
- A missing positive assertion is not a denial. Do not close the world from absence.
- If the purpose needs a distinction the evidence does not establish, record it unresolved. That is success, not a defect to paper over.
- Do not invent code legends, legal overrides, or other World laws from structural correlation or from a single occurrence.
- Record who decided (mechanical / semantic / derived / human-adjudicated) without laundering a human verdict as the machine's.

The current boundary mechanism is `runtime_v0`: write a program that the host executes into a candidate; the host validates and either publishes or discards. Another program shape is allowed if the host can still validate the same properties.

### Environment

You have ordinary programming: inspect files, write code, use libraries, convert formats, create helper modules, temporary databases, parsers, queries, and other local artifacts. Those artifacts are scaffolding. The accepted World is the product. You do not need a universal Source IR, a custom ontology language, or a nine-pass protocol.

### Success

A candidate that the host accepts, that a consumer can query without the original files, that is sufficient for the purpose where evidence exists, and that is honest where it does not. Smaller is better once the purpose is met. Rebuild after a human verdict; never patch the accepted sqlite.

---

## 6. What the next experiment should test

Not another nine-pass hardening. Not a kernel change. Not a Source IR.

The top construction surface:

> Can a fresh capable agent, given a precise purpose, heterogeneous real evidence, ordinary programming capability, and the World contract, autonomously construct a valid and useful World?

That test is not run from this document. Open weaknesses that would confound it if prematurely architected away are in [`reports/open_weaknesses.md`](reports/open_weaknesses.md): establishability without a hidden GOLD, obligation grain, corpus-level authority questions, read-surface over-reading of unresolved prose, ABI as an untested product failure.

---

## 7. Pointers

| Want | Read |
| --- | --- |
| Semantic properties | `CONSTITUTION.md` |
| Current boundary code | `runtime_v0/` |
| Spike that closed the loop | `reports/minimal_semantic_integration_v0_spike1.md` |
| Why ordinary Python | `domains/npdes/purpose_first_python_spine_v1/reports/purpose_first_python_spine_v1.md` |
| Small-domain top-surface evidence | `capability/end_to_end_v1/reports/end_to_end_semantic_compilation_v1.md` |
| Research compiler | `domains/diligence/constructor_v3_1_1/` and its `ADR.md` |
| Review UI over that compiler | `constructor_frontend_spec.md` |
| Guest-harness sketch (unimplemented) | `reports/drop_in_harness_v0_spec.md` |
