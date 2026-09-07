# World IR constitution

**Status:** authoritative for the live World IR / semantic-integration line.  
**Not:** a TaskView schema change, a constructor promotion, a frontend rewrite, or a literature review.

This document states the load-bearing semantic properties of the product. It distinguishes those properties from today's APIs and from research compiler tactics.

Companion: [`CONSTRUCTION.md`](CONSTRUCTION.md) — how a World is constructed.  
Index: [`ARCHITECTURE.md`](ARCHITECTURE.md).

Sealed experiments are evidence, not specification. Current iffy bits: [`reports/open_weaknesses.md`](reports/open_weaknesses.md).

---

## 0. The product

A local semantic compilation layer.

Given a user purpose and a heterogeneous evidence/workspace environment, a capable agent constructs the smallest grounded semantic World sufficient for that purpose, and leaves meaning that is not established unresolved.

The World is reusable and programmable through ordinary consumers — SQL, Python, agents, the read-side explorer. Consumers should not reconstruct source-specific semantics from the original files.

The product promise:

> Give the system a purpose and messy authoritative evidence. It will construct the smallest grounded semantic model it can justify, make that model directly programmable, tell you exactly where meaning remains unresolved, and preserve that work so the same evidence need not be reconciled again for every analysis.

It does not promise automatic understanding of all data, a universal knowledge graph, or a finished ontology before the World is useful.

The safety property:

> The construction agent may reason and program expansively. Durable semantic commitment fails closed.

---

## 1. How to read this document

Four kinds of thing are kept distinct:

| Kind | Meaning | Change bar |
| --- | --- | --- |
| **Primitive** | A semantic kind the World is made of | Foundational. Move only on a concrete representational counterexample. |
| **Invariant** | A property that must remain true of any valid World | Foundational, even if the API that currently enforces it changes. |
| **Contract** | A check or ABI that protects an invariant | Evolving. Replace the check, keep the guarantee. |
| **Mechanism** | Today's store, wrap, file, or runtime | Replaceable if an equivalent mechanism preserves the invariant. |
| **Strategy** | A compiler/host tactic that happened to work | Experimental. Do not promote into kernel or product ontology. |
| **Presentation** | How a human surface shows the World | Not semantic law. |

Each entry below answers, compactly: what it means; what kind of thing it is; what it protects; what fails if it disappears; what it requires and what requires it; whether the *property* is necessary or only today's *mechanism*; what would justify keeping or replacing it; and what evidence currently supports it.

Product guarantees used as the link language:

| Guarantee | One-line |
| --- | --- |
| Semantic fidelity | Compiled meaning matches what the evidence can actually establish. |
| Epistemic honesty | Unsupported meaning stays unresolved rather than becoming fake certainty. |
| Evidence accountability | Durable WORLD BASE claims remain traceable to establishing evidence. |
| Purpose sufficiency | The World is built to answer the declared purpose, not to model the universe. |
| Semantic reuse | Meaning is compiled once and consumed many times without rereading sources. |
| Determinism | Same World + same derivation/projection yields the same computed result. |
| Change safety | Input movement is visible as stale/current; failed work cannot corrupt accepted state. |
| Purpose isolation | Purpose-specific analytical meaning does not silently become World truth. |
| Open-world safety | Absence of a positive assertion is not a denial. |
| Publication integrity | Only a validated candidate may replace an accepted World. |
| Minimality | Prefer the smallest World sufficient for the purpose and accepted constraints. |
| Construction freedom | The agent may inspect, program, and invent local artifacts above the semantic boundary. |

---

## 2. Semantic primitives

These three are the calculus. Provenance, origin, revision, scope, completeness, and unresolvedness are cross-cutting state, not competing kinds.

### Referent

| | |
| --- | --- |
| **Kind / bar** | Primitive / foundational |
| **Means** | A thin, stable handle for something that must participate in relations. Optional display label. No intrinsic properties, kinds, or classifications. |
| **Protects** | Semantic fidelity, semantic reuse |
| **If it disappears** | Identity collapses into attribute bags or fat graph nodes; the same thing cannot be reused across relations without copying properties. |
| **Requires** | Nothing else in the calculus. Grounding may attach, but is not the referent. |
| **Required by** | Relations that mention participants; World identity over time. |
| **Property vs mechanism** | Thin identity is the property. Today's `id` + optional `label` in `_tv_referents` is the mechanism. |
| **Keep-or-replace** | Keep the thinness. Replace the store if needed. A correctness counterexample would be a required intrinsic field that cannot be an ordinary relation. None has appeared. |
| **Evidence** | TaskView doctrine; no NPDES / E2E / diligence constructor required a richer object model. Analogue: typed identifiers, not knowledge-graph nodes with properties. |

### Named typed n-ary relation

| | |
| --- | --- |
| **Kind / bar** | Primitive / foundational |
| **Means** | A named proposition schema with ordered, named, typed roles, and zero or more tuples. Arbitrary finite arity. A tuple is an assertion of that proposition, not a second kind. |
| **Protects** | Semantic fidelity, semantic reuse |
| **If it disappears** | Contextual judgments get smashed into binary edges or reified dummy nodes; meaning that lives in a role (for example a context) is lost. |
| **Requires** | Referents (for `REFERENT` roles); role types. |
| **Required by** | Almost every World claim; derivations; consumer SQL. |
| **Property vs mechanism** | Named typed n-ary propositions are the property. One SQLite table per relation, `Role` / `RoleType`, and constructor-chosen names are the mechanism. Consumer programs should depend on consumer field identity, not on those physical names. |
| **Keep-or-replace** | Keep n-ary named roles. Physical table names and the current role-type enum are replaceable. Binary-only graphs have already been rejected as a rewrite of the calculus. |
| **Evidence** | TaskView; World IR frontend spec §2; diligence/NPDES Worlds use unary through 4+-ary relations routinely. |

### Derivation

| | |
| --- | --- |
| **Kind / bar** | Primitive / foundational |
| **Means** | Deterministic maintained computation whose output is itself a named relation. Inputs, expression (today: SQL), execution receipt, stale/current, and local completeness belong to it. |
| **Protects** | Determinism, change safety, semantic reuse |
| **If it disappears** | Computed meaning is either re-derived ad hoc by every consumer, or baked in as unaccountable BASE tuples. |
| **Requires** | Named relations as inputs and output; revision so staleness is detectable. |
| **Required by** | Purpose projections, any maintained view over BASE. |
| **Property vs mechanism** | Maintained deterministic computation is the property. Raw SQL + `register_derivation` / `run_derivation` is the current mechanism. Another deterministic engine could preserve the property. |
| **Keep-or-replace** | Keep “derived rows come only from a registered computation over declared inputs.” Replace SQL if a counterexample needs it; none has. |
| **Evidence** | TaskView staleness/rerun; runtime_v0 and constructors both reuse this rather than inventing a second computation model. |

---

## 3. Foundational invariants

### Open-world assertion

| | |
| --- | --- |
| **Kind / bar** | Invariant / foundational |
| **Means** | A missing positive assertion is not a denial. Closed-world DISTINCT, “not in the table ⇒ false,” and invented negative closure from absence are forbidden. |
| **Protects** | Open-world safety, epistemic honesty |
| **If it disappears** | The World silently answers “no” for facts it never examined. NODI-style codes become fake legends. |
| **Requires** | Explicit unresolvedness as the honest alternative. |
| **Required by** | Negative claims, completeness receipts, any DISTINCT-like consumer question. |
| **Property vs mechanism** | The open-world reading is the property. How negatives are *represented* (an explicit relation, an unresolved failure row, a completeness `UNKNOWN`) is mechanism. |
| **Keep-or-replace** | A DISTINCT-only negative-closure gate may downgrade DISTINCT to UNRESOLVED; it must not upgrade UNRESOLVED or mint SAME from absence. That rule is the invariant, not a particular gate implementation. |
| **Evidence** | CLAUDE.md load-bearing facts; NPDES NODI C/9 correctly left unresolved for want of a codebook; E2E Worlds refused unsupported closure. |

### Explicit unresolvedness

| | |
| --- | --- |
| **Kind / bar** | Invariant / foundational |
| **Means** | Meaning the purpose needs and the evidence does not establish is recorded as unresolved, not guessed. Unresolved is purpose-relative: it is a failure of a purpose requirement, not a World fact that “X is unknown in the universe.” |
| **Protects** | Epistemic honesty, purpose sufficiency |
| **If it disappears** | Agents fill holes; consumers over-read hole prose as established condition meaning. |
| **Requires** | A purpose (otherwise “needed but missing” is undefined); open-world reading. |
| **Required by** | Construction success criteria; read-side honesty. |
| **Property vs mechanism** | First-class unresolvedness is the property. Today's representations — `purpose_requirement_failure`, Constructor P3 obligations, BOM `demand.json` — are mechanisms. The kernel does not need a primitive named Obligation. |
| **Keep-or-replace** | Keep the obligation to leave unsupported meaning explicit. Replace the row shape. E2E State A over-read of hole prose is a presentation/convention problem until a domain cannot *represent* unresolvedness. |
| **Evidence** | Purpose-First Python Spine `WHEN DISCHARGING` emitted as unresolved rather than World law; Spike 1 GM row; E2E non-establishable questions. |

### Evidence accountability

| | |
| --- | --- |
| **Kind / bar** | Invariant / foundational |
| **Means** | Durable WORLD BASE assertions remain accountable to establishing evidence. Grounding is a pointer, not a copy of the source body. |
| **Protects** | Evidence accountability, semantic fidelity |
| **If it disappears** | The World can contain established-looking tuples with no way to say why. Publication becomes laundering. |
| **Requires** | Source observations that actually exist; WORLD vs PURPOSE (PURPOSE rows need not carry SOURCE). |
| **Required by** | Fail-closed WORLD commit; read-side “why does this exist.” |
| **Property vs mechanism** | Accountability is the property. `Grounding` / `GroundingKind` / `_tv_groundings` / `SourceObservation` are the current representation. They may change. |
| **Keep-or-replace** | Removing SOURCE from WORLD BASE must make accept fail. Changing pointer format does not. Kernel `SemanticWorld.assert_tuple` still synthesizes origin-only WORLD grounding when observations are omitted; that is a mechanism leak. The construction wrap and accept validator currently close it. |
| **Evidence** | Constructor `validate_provenance`; runtime_v0 `GroundingError` + `validate_world_base_source`; Spike 1 ungrounded candidate rejected. Analogue: data provenance, not copied corpora. |

### WORLD versus PURPOSE lifetime

| | |
| --- | --- |
| **Kind / bar** | Invariant / foundational |
| **Means** | If the current purpose disappeared, would the proposition still have the same meaning and truth conditions? If yes, it is eligible for World. If it depends on this analysis, threshold, policy, or requested decision, it belongs to Purpose unless those dependencies are explicit arguments that make the proposition independently meaningful. |
| **Protects** | Purpose isolation, semantic reuse |
| **If it disappears** | `answer_to_purpose_a(...)` is stored as World law; the next purpose inherits a previous analysis. |
| **Requires** | A declared purpose; a place to put purpose-scoped rows that are still queryable. |
| **Required by** | Admission, consumer trust that World tuples survive purpose change. |
| **Property vs mechanism** | The lifetime test is the property. Constructor `06_admission.json`, runtime `world.admission.json`, and `scope=` on `declare_relation` are mechanisms. Scope as an ordinary relation, as TaskView's worked example does, is also a valid mechanism. |
| **Keep-or-replace** | Keep the test. Do not add a TaskView column just to name it. A second axis — *why it may be used* (source-established, derived, user-certified policy, unresolved) — is also an invariant; today's enums can wait. |
| **Evidence** | KERNEL.md World vs Purpose; proposal/scope probe; synthesis §12. |

### Two origins that disagree

| | |
| --- | --- |
| **Kind / bar** | Invariant / foundational |
| **Means** | `_tv_assertions.origin` (`ASSERTED` \| `DERIVED`) is how the tuple entered the table. `ConstructionOrigin` (`MECHANICAL` \| `SEMANTIC` \| `DERIVED` \| `ADJUDICATED`) is who decided it. They answer different questions. `ADJUDICATED` is a human verdict, not a flavour of `SEMANTIC`. |
| **Protects** | Epistemic honesty, change safety |
| **If it disappears** | A person's decision is laundered as the machine's; every downstream claim about construction becomes untrue. |
| **Requires** | Assertion identity; a recording channel that is not the TaskView origin column. |
| **Required by** | Construction review; “what did a person decide.” |
| **Property vs mechanism** | Two questions, two answers is the property. The `.origins.json` sidecar is the mechanism (deliberately not a TaskView schema change). |
| **Keep-or-replace** | Keep the distinction. The sidecar path and enum names are replaceable. Merging the two columns is not. |
| **Evidence** | `core/origins.py`; CLAUDE.md; constructor-review geometry encodes this structurally. |

### Revision, stale/current, completeness

| | |
| --- | --- |
| **Kind / bar** | Invariant / foundational |
| **Means** | The World is versioned. Staleness is per-relation, never per-tuple: a derivation is stale when declared inputs have moved. Completeness is a local claim for one derivation run against a named universe (`COMPLETE` \| `INCOMPLETE` \| `UNKNOWN`). Absence is authoritative only for a current successful `COMPLETE`. |
| **Protects** | Change safety, determinism, open-world safety |
| **If it disappears** | Consumers cannot tell computed current from computed last week; empty results get over-read as exhaustive. |
| **Requires** | Derivation; declared inputs; view/relation revision. |
| **Required by** | Rerun; read-side stale lists. |
| **Property vs mechanism** | Per-relation stale/current and local completeness are the property. TaskView receipts and `relation_version` are the mechanism. |
| **Keep-or-replace** | Keep “stale is a relation, not a tuple.” A different receipt format is fine. |
| **Evidence** | TaskView README; `is_stale` / completeness receipts. |

### Publication integrity

| | |
| --- | --- |
| **Kind / bar** | Invariant / foundational |
| **Means** | The accepted World is not mutated by failed construction. The only product transaction that replaces accepted semantic state is candidate → validate → accept, as a whole. A human verdict reaches World tuples only by rebuild, never by patching the compiled sqlite. |
| **Protects** | Publication integrity, change safety |
| **If it disappears** | Crashes and bad programs corrupt the live World; “just this one obviously correct tuple” collapses the write boundary. |
| **Requires** | A candidate that is not the accepted file; fail-closed validation. |
| **Required by** | Construction freedom (the agent can fail safely). |
| **Property vs mechanism** | Atomic replace-or-discard is the property. `publish_candidate` directory rename is the mechanism. |
| **Keep-or-replace** | Keep “failed candidate leaves accepted fingerprints unchanged.” Filesystem vs another store is replaceable. |
| **Evidence** | Spike 1; E2E failure-path probe; constructor frontend spec write boundary. |

### Purpose as bound, not owner of truth

| | |
| --- | --- |
| **Kind / bar** | Invariant / foundational |
| **Means** | Construction starts from what the user is trying to compute or understand. Purpose bounds attention and defines sufficiency. It does not own all truth: World-eligible propositions remain World-eligible if the purpose vanishes. |
| **Protects** | Purpose sufficiency, minimality, purpose isolation |
| **If it disappears** | Either exhaustive folder ontology, or a World that is only a query cache. |
| **Requires** | An explicit purpose contract (today: text + executable requirements). |
| **Required by** | Unresolvedness; admission; consumer field requirements. |
| **Property vs mechanism** | Purpose-bounded compilation is the property. `purpose.txt`, P0 intention contracts, and `Purpose.require_*` are mechanisms. |
| **Keep-or-replace** | Keep “do not begin by understanding the whole folder.” The requirement API can evolve. |
| **Evidence** | Purpose-First Python Spine (purpose interpretation was agent work; CSV plumbing was not); anatomy probe's small conceptual core. |

### Deterministic commitment below the agent

| | |
| --- | --- |
| **Kind / bar** | Invariant / foundational |
| **Means** | Once a candidate World exists, validation, derivation rerun, normalization, and projection are deterministic. The agent does not get a second chance to “fix” those results by vibe. |
| **Protects** | Determinism, publication integrity |
| **If it disappears** | Two accepts of the same candidate disagree; consumers cannot trust computed columns. |
| **Requires** | Registered derivations; mechanical validators. |
| **Required by** | Fail-closed materializability; reuse. |
| **Property vs mechanism** | Determinism after commit is the property. Particular validators are contracts. |
| **Keep-or-replace** | Keep the split: agent authors, host materializes. |
| **Evidence** | Constructor P7/P8; v3.1.1 normalizer; runtime_v0 accept path. |

### Construction freedom above the boundary

| | |
| --- | --- |
| **Kind / bar** | Invariant / foundational |
| **Means** | A construction agent may inspect sources, write ordinary code, use libraries, convert formats, create helpers, temporary databases, intermediate representations, parsers, queries, or other local artifacts. Those artifacts are not World state. Deleting a source-inspection cache regenerates it; deleting the World loses semantic integration work. |
| **Protects** | Construction freedom, semantic fidelity (by not forcing a Source IR) |
| **If it disappears** | Either the kernel grows a universal parser, or the agent is trapped in a custom DSL and loses the distinctions that ordinary Python found. |
| **Requires** | A hard commit boundary (see publication integrity, evidence accountability). |
| **Required by** | Heterogeneous ingestion without making formats a kernel concern. |
| **Property vs mechanism** | Free computation above a narrow commit is the property. `construction.py`, `Source` helpers, and isolated LLM passes are strategies/mechanisms. |
| **Keep-or-replace** | Keep the split. Do not build a persistent Source IR because inspection was useful. Purpose-First Python Spine is the positive evidence: ordinary Python removed the brittle custom-IR confound. |
| **Evidence** | Synthesis §4–§6; Spike 1; E2E construction; drop-in harness premises. |

### Minimality

| | |
| --- | --- |
| **Kind / bar** | Invariant (objective) / evolving |
| **Means** | Optimize toward the smallest semantic state sufficient for the declared purpose and accepted constraints. Not the unique minimal ontology on a universal complexity metric, and not a first-shot requirement. |
| **Protects** | Minimality, purpose sufficiency, semantic reuse |
| **If it disappears** | Worlds accumulate dead mass; consumers drown in locally redundant relations. |
| **Requires** | Purpose (otherwise “sufficient” is undefined). |
| **Required by** | Nothing else as a hard gate today. |
| **Property vs mechanism** | Sufficiency-minimality is the property. Post-construction slicing and obligation factoring are strategies. |
| **Keep-or-replace** | Keep as an objective. Anatomy: first-shot constructions can be locally redundant and still find the distinctions; 23/30 tested single-element removals were locally redundant under the tested purposes. |
| **Evidence** | Anatomy probe; synthesis §16. |

---

## 4. Contracts that protect the invariants

These are expected to evolve. Replacing a contract is allowed if the protected invariant remains.

### Fail-closed WORLD BASE grounding

WORLD BASE tuples require SOURCE grounding with a non-empty reference. PURPOSE-scoped rows (policy, requirement failures) may omit it. Protected invariant: evidence accountability. Current mechanisms: Constructor `validate_provenance`; runtime_v0 assertion-time `GroundingError` plus accept-time scan. Kernel `SemanticWorld` still allows origin-only WORLD grounding — the contract currently lives in the construction wrap, not in TaskView. That placement is replaceable; the fail-closed property is not.

### Fail-closed materializability

If a consumer requirement is claimed `SATISFIED`, that field must actually appear in the mechanical materialization of the World (`SATISFIED(f) ⇒ f ∈ Normalize(W)`). Declared-but-empty bindings are `UNSATISFIED: NOT_MATERIALIZABLE` and fail closed before projection. Protected invariants: semantic fidelity, purpose sufficiency. Current mechanism: Constructor v3.1.1 ABI completeness sharing `normalize_world()`. This is **not** generic heterogeneous ingestion; it is a realizability contract learned on the research constructor. Runtime_v0 Spike 1 did not need the full ABI to complete the folder → accepted SQLite loop. Cross-reconstruction `semantic_identity` stability is known pressure, not yet a demonstrated product failure.

### Consumer field identity

Consumer programs depend on consumer field identity, not constructor relation names. Protected invariant: semantic reuse across reconstructions. Current mechanism: `semantic_identity` / `field_sources` on compiler contracts, not TaskView columns. Do not add `semantic_identity` to TaskView to make this feel more foundational.

### Write boundary

The compiled World is read-only. Construction is where writes go. The only path from a verdict to a World tuple is a rebuild. Protected invariant: publication integrity. Current mechanisms: no mutating explorer endpoint; candidate directory publish; constructor-review records a verdict beside the run.

### Dependency direction

Experimental strategies may depend on contracts and TaskView. Foundational semantics must never depend on an experimental strategy. TaskView must not import `runtime_v0`. Protected invariant: change safety of the calculus.

---

## 5. Current mechanisms (replaceable)

| Mechanism | Implements | Must not be mistaken for |
| --- | --- | --- |
| `taskview/` SQLite, one table per relation | Primitives + revision/stale/completeness/grounding store | The only conceivable World store |
| `SemanticWorld` wrap + `.origins.json` | Construction origin beside TaskView | A second calculus |
| `runtime_v0` (`ConstructionWorld`, `Project`, `Purpose`, `publish_candidate`) | Construction boundary: execute program → candidate → validate → accept | Ontology; the only construction API |
| `construction.py` / `construct(source, world, purpose)` | A strongly supported way to feed the kernel | A semantic primitive or required filename |
| `world.admission.json` / Constructor `06_admission.json` | WORLD vs PURPOSE classification | A TaskView column |
| `purpose_requirement_failure` | Explicit unresolvedness as an ordinary PURPOSE relation | A kernel `UNRESOLVED` type |
| Reconstructible `Source` helpers | Construction freedom | A persistent Source IR |
| Compiled-world sidecar cluster (`origins`, purpose/demand, hashes) | Purpose contract + origin account next to sqlite | One true sidecar schema for all lineages |
| G6 explorer / construction docket | Presentation of World and of a research constructor run | A new semantic model |

`runtime_v0` is the plausible product-shaped mechanism for feeding the kernel. It is research-quality code that already implements the construction boundary. Graduating it to a named product surface is a later packaging decision, not a calculus change.

---

## 6. Experimental / research strategies (not product ontology)

Useful in experiments. The kernel does not need their names. A future construction agent may ignore all of them and still produce a valid World.

```text
nine-pass P0–P8 workflow
isolated per-pass LLM agents
semantic obligation / frontier objects
evidence packet / evidence plan
REFINED parent/child obligations
cue-list verifier, critic, entailment, proof-obligation gates
semantic-family hints
Probe A/B strategy code
proposal / dry-run / near-miss / decision-record objects
compact-header conventions as if they were kernel law
drop-in .<product>/ layout (design only)
Constructor C0–C4 order in KERNEL.md
```

v3.1.1 is a fail-closed materializability hardening of the research constructor. It is not the generic heterogeneous-source ingestion mechanism.

The nine-pass constructor remains valuable evidence: it discovered WORLD vs PURPOSE admission, provenance validation, ABI realizability, and the cost of treating SATISFIED as a declaration. Those *invariants* stay. The pass machine does not.

---

## 7. What a valid World is

A valid candidate World is a TaskView (or equivalent store) plus sidecars such that:

1. It uses only the three primitives, with cross-cutting state as metadata rather than new kinds.
2. WORLD BASE tuples are SOURCE-grounded.
3. PURPOSE-scoped meaning is classified as such.
4. Derived relations come only from registered deterministic computation.
5. Unsupported purpose-needed meaning is explicit, not filled.
6. Missing positives are not denials.
7. Construction origin is recorded without being collapsed into assertion origin.
8. Accept is atomic: validation failure discards the candidate and leaves the previous accepted World unchanged.

A World may be useful while still incomplete. Unresolvedness is not construction failure.

---

## 8. Frozen before the next experiment

Frozen:

- the three primitives;
- the invariants in §3;
- the fail-closed contracts in §4 as *properties* (their APIs may still evolve);
- TaskView as the current store, absent a representational counterexample;
- the rule that host/compiler tactics are not kernel types.

Not frozen, and not to be fossilized by the next experiment:

- nine-pass filenames and workflow;
- `construction.py` as the only authoring shape;
- particular `Purpose.require_*` APIs;
- ABI field lists from diligence;
- Source IR, format packs, or a second calculus.

The next experimental frontier is the **top construction surface**: whether a fresh capable agent, given a precise purpose, heterogeneous real evidence, ordinary programming capability, and this constitution, can autonomously construct a valid and useful World. That experiment is not defined here and must not be run from this document.

---

## 9. Authority

| Document | Role |
| --- | --- |
| This file | Semantic properties and change bars |
| [`CONSTRUCTION.md`](CONSTRUCTION.md) | Product construction architecture and agent brief |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | Thin index and dependency direction |
| `taskview/` | Current store implementing the calculus |
| `world_ir_frontend_spec.md` | Read-side presentation contract |
| `constructor_frontend_spec.md` | Review UI over the *research* nine-pass constructor |
| `reports/minimal_semantic_integration_synthesis_v0.md` | Experimental synthesis; evidence, not law |
| `reports/open_weaknesses.md` | Current iffy bits |
| Sealed domain/capability reports | Evidence. Do not rewrite to match this file. |

Change this constitution when a concrete correctness counterexample shows a listed invariant cannot represent something required, or when a contract's mechanism is replaced by an equivalent. Do not change it to match a convenient constructor tactic.
