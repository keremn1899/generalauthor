# Minimal Semantic Integration System — Synthesis v0

**Status:** research synthesis after the NPDES purpose-first / obligation / refinement campaign.  
**Not:** a TaskView schema change, Constructor promotion, product-spec replacement, or host-strategy fossilization.

Product authority after the architecture pass: [`../CONSTITUTION.md`](../CONSTITUTION.md) and [`../CONSTRUCTION.md`](../CONSTRUCTION.md). This file remains experimental evidence, not law.

Sealed experiments this document synthesizes (do not modify):

- Purpose-First Python Spine Probe  
- Semantic Spine Anatomy Probe  
- Conversational Semantic Review Probe  
- Semantic Proposal & Scope Clarification Probe  
- Obligation-Driven Targeted Semantic Resolution Probe v1  
- Semantic Refinement & Admission Microprobe v1  

Host compiler concepts named below (`semantic obligation`, `REFINED`, evidence plan, proposal, dry-run, …) remain **host/research metadata** until a deterministic kernel invariant requires them.

---

## 1. The product in one sentence

Build a local, read-only semantic compilation layer that lets an agent turn heterogeneous authoritative sources into a small grounded relational model sufficient for a declared purpose, while leaving unsupported meaning explicitly unresolved.

More operationally:

```text
folder + purpose
→ agent explores
→ executable semantic spine
→ deterministic World
→ unresolved semantic obligations
→ selective evidence / human resolution
→ reusable grounded semantics
→ SQL / Python / agents
```

The value proposition remains:

> **Compile meaning once, compute over it many times.**

The experiments now support this shape without requiring a universal knowledge graph, a bespoke ontology language, broad prose ingestion, or a large fixed semantic taxonomy.

---

## 2. What the experiments appear to have established

The strongest construction result is the Purpose-First Python probe: five independent Composer 2.5 runs all produced executable constructions, recovered all seven pre-registered distinctions, materialized candidate correspondence, and exposed staged TDS, `WHEN DISCHARGING`, and source-authority seams. Ordinary Python removed the brittle custom-IR confound.

The anatomy work then showed that these apparently large construction programs did not correspond to hundreds of ontology concepts. Across trials, the conceptual core was roughly six stable requirement schemas plus six stable relation schemas; the apparent size came mainly from grounding, execution scaffolding, and requirement instantiation. Mean raw semantic pressure was about 2,972 hole occurrences, but only about 35 candidate obligations and roughly six consequential human-review questions.

The targeted-resolution work showed that those obligations can drive selective evidence search. Eight selected obligations covered 418 occurrences; evidence contact refined them to roughly 12–16 reusable questions rather than exploding into row-level cases. Establishable `WHEN DISCHARGING`, pass/fail, and geometric-mean semantics were found, while missing NODI legends correctly remained unresolved.

The refinement follow-up repaired the remaining grain/admission ambiguity. All nine tested coarse obligations became explicitly `REFINED`, not simultaneously unresolved and partially admitted; child partitions remained mechanically reconstructible, and broader unsupported document-authority generalizations stayed unverified.

Finally, conversational probes support a host-owned proposal boundary: ambiguous natural-language corrections can be interpreted, dry-run, localized, and clarified without mutating durable semantics first. Purpose-scoped feedback need not silently become World semantics.

Taken together, these experiments suggest that the difficult semantic machinery belongs mostly in **host behavior**, while the durable substrate can remain small.

---

## 3. The foundational layer

Freeze very little.

| Area | v0 stance |
| --- | --- |
| Semantic representation | thin Referents + named typed n-ary Relations |
| Maintained computation | Derivations |
| Evidence | exact grounding/provenance on durable semantic assertions |
| Intent | explicit Purpose contract |
| Uncertainty | unresolved is first-class |
| Epistemics | scope and admission are separate |
| Storage/query | SQLite / ordinary SQL |
| Construction language | ordinary Python |
| Effects | read-only sources; controlled semantic commit |
| Consumer surface | SQL + Python |

Everything else should have to earn its way into the foundation.

The basic semantic representation remains:

```text
REFERENT
RELATION
DERIVATION
```

A Referent is only a stable handle for something that needs to participate in semantic relations.

A Relation is a named proposition schema with typed roles. Arbitrary finite arity is allowed because many useful integration judgments are contextual and cannot be cleanly reduced to binary edges without artificial reification.

A Derivation records deterministic maintained computation over grounded relations.

Provenance, epistemic state, purpose scope, revision state, and construction origin are cross-cutting metadata, not competing ontological primitives.

The experiments have not produced a correctness/computation counterexample requiring a richer foundational ontology.

---

## 4. The most important invariant

The system should aggressively separate:

```text
what the agent can think
```

from:

```text
what the system may durably claim
```

The host should have normal Python, normal source access, statistics, joins, search, parsing, and arbitrary exploratory computation.

Semantic commitment goes through a narrow controlled boundary.

Conceptually:

```python
world.referent(...)
world.relation(...)
world.derive(...)
world.assert_grounded(...)

purpose.require(...)
purpose.unresolved(...)
```

Exact API names are not important yet.

The invariant is:

> **Let the agent compute freely. Make durable semantic commitment constrained.**

This has now repeated across almost every experiment.

Structural correlation did not become NODI truth. Literal `WHEN DISCHARGING` detection created unresolved semantics rather than invented rules. The evidence resolver could hypothesize broader document authority without admitting it. Human assertions could be distinguished from source-established facts.

This should be one of the hardest architectural boundaries.

---

## 5. Purpose is the strongest prior

The system should not begin by exhaustively understanding the folder.

It should begin with:

```text
"What are you trying to compute or understand?"
```

Purpose bounds semantic attention.

The host then explores only enough source structure to construct the distinctions required by that purpose.

This is a major lesson of the Python-spine experiment: purpose interpretation, distinction selection, semantic-field identification, and join predicates were agent work; CSV loading, profiling, joins, date parsing, numeric checks, and grouping were deterministic work.

Purpose therefore belongs in the runtime as an executable contract rather than just prompt text.

It can contain things like:

```text
required outputs
required cardinalities
required interpreted fields
completeness expectations
consumer-facing semantic identities
```

But purpose does not own all truth.

The admission question remains:

> If this purpose disappeared, would the proposition retain the same meaning and truth conditions?

If yes, it may belong to World.

If no, it belongs to Purpose.

---

## 6. Source inspection should stay boring

Do not build a giant persistent Source IR.

The host needs simple deterministic helpers:

```text
list sources
inspect schema
sample values
profile frequencies/nulls
test uniqueness
test inclusion/overlap
parse dates/intervals
inspect candidate joins
inventory documents
read selected text
```

Those helpers are reconstructible.

They are not semantic state.

That means:

```text
delete source-inspection cache
→ regenerate it

delete World
→ semantic integration work is lost
```

This distinction keeps the implementation honest.

Candidate structural evidence should also remain separate from semantic commitment:

```text
"these columns overlap 100%"
```

does not mean:

```text
"these fields have the same semantic identity"
```

Structure proposes.

Semantic compilation commits.

---

## 7. The host agent is the semantic compiler

The host should own almost everything that varied experimentally.

Its job is to:

```text
understand purpose
inspect sources
choose useful distinctions
write semantic construction Python
declare purpose requirements
execute
inspect failures
factor semantic obligations
retrieve targeted evidence
refine obligations when evidence reveals heterogeneity
propose semantic changes
infer scope
explain consequences
converse with user when needed
```

These are capabilities of the semantic compiler, not new ontology primitives.

This is a crucial implementation rule:

> **Do not promote successful host strategies into foundational APIs unless deterministic enforcement requires it.**

For example, the following should remain compiler/research concepts for now:

```text
semantic frontier
semantic obligation
REFINED
evidence plan
candidate interpretation
semantic proposal
near-miss
decision record
consequence dry-run
```

They are useful ways for the host to organize work.

The kernel does not need to know most of their names.

---

## 8. The semantic frontier is compiled, not predefined

A purpose requirement fails.

That produces concrete blocked computations.

Those can be grouped into reusable semantic obligations.

Evidence may then reveal that an obligation is itself too coarse.

So the actual process is:

```text
failed requirement
→ affected occurrences
→ candidate reusable obligation
→ evidence contact
→ resolve OR refine OR remain unresolved
```

The geometric-mean result is the canonical example.

Forty rows carried the same comment, but evidence showed a meaningful split between TDS semantics and non-TDS comment carryover. The correct outcome was not forty judgments and not one universal judgment; it was a small mechanically reconstructible semantic partition.

So the frontier should be thought of as a **dynamically factored set of unresolved questions**.

Not a fixed taxonomy.

Not a flat list necessarily.

But also not something that requires a general graph framework.

Parent/child provenance is enough.

---

## 9. Evidence resolution should be obligation-first

Do not search all prose for useful facts.

Take one exact semantic obligation and ask:

```text
What evidence would establish or refute this proposition?
```

Then retrieve only that evidence.

The resolver gets a bounded packet containing:

```text
exact semantic question
purpose/relation contract
candidate interpretations
source identities
small retained evidence set
allowed dispositions
```

The bounded judge may then return:

```text
SUPPORTED
SUPPORTED_NEGATIVE
UNRESOLVED
```

with exact grounding.

If the corpus cannot establish the proposition, `UNRESOLVED` is success.

This behavior was especially important for NODI: occurrence-local evidence could tempt a model into interpretations, while reusable obligation-first resolution correctly determined that the corpus contained no code legend.

---

## 10. Resolution may sharpen rather than close

The product must not treat semantic resolution as synonymous with “answer obtained.”

`WHEN DISCHARGING` illustrates the right behavior.

Evidence can establish:

```text
monitoring applicability depends on discharge occurrence
```

while leaving:

```text
did discharge occur in this period?
```

unknown.

That is semantic progress.

The system has transformed an opaque comment into a precise factual dependency.

In the successful T1 run, this reduced the original 17 semantic-comment holes and introduced the sharper `discharge_occurrence_in_period` requirement instead.

A core philosophy should therefore be:

> **Good compilation converts vague uncertainty into narrower computable dependencies, even when it cannot eliminate uncertainty.**

---

## 11. Human interaction

The ordinary user should never edit ontology structure.

The host should expose its current semantic understanding and consequences in ordinary language.

Externally:

```text
user ↔ host
```

Internally:

```text
utterance
→ interpretation
→ inferred scope
→ candidate semantic delta
→ disposable execution
→ consequence diff
→ clarify if materially ambiguous
→ proposal
→ acceptance
→ commit
```

Clarification should not be triggered merely by linguistic uncertainty.

It should be triggered when plausible semantic interpretations have materially different consequences.

The user may respond naturally:

```text
"yes"
"not quite"
"only for this analysis"
"that's generally true"
"I don't know"
"those are separate legal entities but the same account"
```

The host owns translation into formal semantics.

The user owns purpose, domain distinctions, corrections, policies, and certification of consequences.

---

## 12. Scope and epistemic admission are independent

This deserves explicit architectural treatment.

A proposition can be World-scoped yet not established.

For example:

```text
"The final permit legally overrides the fact sheet."
```

may express a purpose-independent proposition.

Therefore:

```text
scope = WORLD
```

can be appropriate.

But if it comes only from an unsupported user assertion or model generalization:

```text
epistemic_status = UNVERIFIED
```

and it must not satisfy contracts requiring established World truth.

Conversely:

```text
"For this analysis, use the final permit."
```

is legitimately usable as a user-certified Purpose policy without pretending to establish external law.

This means every durable semantic proposition effectively has two axes:

```text
WHERE DOES IT BELONG?
World / Purpose / narrower context

WHY MAY IT BE USED?
source-established
mechanically derived
user-certified policy
user-asserted
model-proposed
unresolved
```

The exact enum vocabulary can wait.

The distinction cannot.

---

## 13. The actual v0 product loop

The smallest credible product is:

```text
1. Point at a local folder.

2. Tell the host what you are trying to do.

3. Host explores sources and writes construction.py.

4. Runtime executes construction.py into SQLite World state.

5. Host shows:
   - what it integrated
   - what remains semantically unresolved
   - which unresolved questions materially affect the purpose

6. User can immediately:
   - query World with SQL
   - use Python
   - ask the host questions

7. Host may investigate a semantic obligation:
   - inspect targeted evidence
   - resolve/refine/remain unresolved
   - dry-run consequences
   - propose important changes

8. Accepted/established semantics persist.

9. Future computation reuses them.
```

That is enough for v0.

The whole product does not need to “finish the ontology” before becoming useful.

---

## 14. What to implement first

The first implementation should include only the pieces necessary to complete that loop.

The durable data layer needs SQLite tables for referents, relation schemas/roles, relation tuples/assertions, derivations, source grounding, purpose requirements, unresolved requirement instances, and basic revision/construction metadata.

The Python runtime needs a tiny World/Purpose commit API plus deterministic validation that prevents ungrounded durable assertion and checks required consumer contracts.

The source helper library needs CSV/JSON/database inspection, document inventory, structured profiling, and targeted text access.

The host prompt/tool environment needs full ordinary Python and instructions to act as a semantic integration engineer.

The product surface needs a conversation plus a very plain World/requirements inspector and SQL/Python access.

That is enough.

---

## 15. What v0 should explicitly not contain

Do not initially build:

```text
universal knowledge graph UI
manual ontology editor
custom agent-facing DSL
semantic-family hierarchy
persistent giant Source IR
automatic whole-corpus prose extraction
general text-to-KG pipeline
workflow/governance engine
write-back/actions
confidence-score framework
complex adjudication protocol
ontology visual designer
large ontology library
automatic canonical entity collapse
```

Most of these would either weaken the product thesis or prematurely fossilize mechanisms that currently work best because the host remains flexible.

---

## 16. Minimality

Minimality remains a design objective, but not a first-shot requirement.

The experiments showed that first-shot constructions can contain locally redundant semantics while still discovering the important distinctions; 23 of 30 tested single-element removals were locally redundant under the tested purposes.

So:

```text
first draft
→ backward slice from purpose
→ factor repeated obligations
→ remove dead semantic mass
→ preserve behavior
```

is preferable to demanding that the host synthesize the unique minimal ontology in one pass.

The system should optimize toward:

> **smallest semantic state sufficient for the declared purpose and accepted constraints**

rather than:

> smallest ontology according to a universal complexity metric.

---

## 17. The architectural boundary

The clearest synthesis of all the experiments is:

```text
FOUNDATION
────────────────────────
sources are authoritative
read-only
referents
typed n-ary relations
derivations
grounding/provenance
purpose contracts
epistemic admission
SQLite / SQL

HOST / SEMANTIC COMPILER
────────────────────────
source exploration
representation search
construction.py authoring
requirement generation
obligation factoring
evidence planning
targeted retrieval
obligation refinement
scope inference
semantic proposals
conversation
minimality/refactoring

OPTIONAL / EXPERIMENTAL
────────────────────────
exact obligation-ranking heuristics
exact retrieval algorithm
near-miss presentation strategy
specific semantic-family diagnostics
confidence scores
automatic admission policy
visual UI
ontology graph projection
```

Dependency direction should be strictly downward.

Foundation knows nothing about the host strategies.

Host strategies depend on Foundation.

Experimental mechanisms depend on both and can be deleted without invalidating the core.

---

## 18. The system's promise

The product should not promise:

> “We automatically understand all your data.”

It should promise something closer to:

> **Give the system a purpose and messy authoritative evidence. It will construct the smallest grounded semantic model it can justify, make that model directly programmable, tell you exactly where meaning remains unresolved, and preserve semantic work so you do not have to reconcile the same evidence again in every analysis.**

That is both more defensible and more interesting.

The architecture's fundamental safety property is equally simple:

> **The system may reason expansively, but it must fail closed at semantic commitment.**

And the implementation principle that follows is:

> **Keep the runtime small and boring. Put intelligence in the host.**

---

Open weaknesses after this campaign (materialization of supported deltas, establishability without a hidden GOLD, read-surface over-reading of hole prose, ABI pressure still untested as a product failure) are recorded in [`open_weaknesses.md`](open_weaknesses.md). That note does not promote host mechanisms into the kernel.

## STOP

This document records an experimental synthesis.

It does not:

- modify TaskView / kernel
- modify Constructor v3.1.1
- promote `REFINED`, obligation factoring, or evidence plans into foundational APIs
- invent a runtime semantic-family taxonomy
- replace `world_ir_frontend_spec.md` or `constructor_frontend_spec.md`
- start a fifth domain
- build UI
