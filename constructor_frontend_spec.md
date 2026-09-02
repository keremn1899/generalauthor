# Constructor Front-End Specification

**Status:** Working front-end contract for the construction-review surface
**Companion:** `world_ir_frontend_spec.md` — this document extends it forward in time
**Scope:** Human review of, and intervention in, an agent-authored construction
**Non-goal:** Becoming an ontology authoring tool

---

## 1. Product boundary

The read-side explorer answers *what is true and why*. This surface answers
*how did this become true, and where should a person intervene*.

It is a **review and intervention surface over an agent's construction**. The
constructor (composer-2.5, passes P0–P8) authors the world. A human reads what
it did, disagrees where it is wrong, and owns publication. That division is
already the product boundary in `CLAUDE.md`:

> The editor agent owns interpretation and authors construction programs. […]
> A human owns publication.

It helps a human answer:

- What did the constructor understand my purpose to be?
- What vocabulary did it invent, and are those the right distinctions?
- What did it establish mechanically, and is that grounded?
- What did it decline to decide, and why?
- Was that decline correct?
- Which of these decisions is a purpose actually waiting on?
- If I overturn this, what has to be rebuilt, and what will that cost?
- What in this world was decided by a person rather than by the machine?

It is **not**:

- an ontology editor;
- a pipeline builder;
- a place to run a constructor;
- a benchmark console;
- a transcript viewer;
- a replacement for the read-side explorer.

### 1.1 Frozen artifacts, one world

This version reads a **completed** construction from disk. There is no
streaming, no cancellation, no partial state, and no cross-trial comparison.
One world is under review at a time.

Live runs and trial comparison are separate feature discussions. Neither should
shape this surface.

---

## 2. What the constructor emits — frozen

The front end reads these artifacts. It does not change their shape.

| Pass | Artifact | The human question |
|---|---|---|
| P0 | `00_intention_contract.json` | Did it understand what I asked for? |
| P1 | `01_vocabulary.json` | Are these the right things and distinctions? |
| P2 | `02_mechanical_world/world.sqlite`, `02_mechanical_report.json` | Did the deterministic part land, and is it grounded? |
| P3 | `03_obligations.json` | Is this the right frontier? |
| P4 | `04_packets/<obligation_id>.json` | Did it look at the right evidence? |
| P5 | `05_dispositions.json` | **Is this judgment right?** |
| P6 | `06_admission.json`, `06_world/world.sqlite` | World-true, or only true for this purpose? |
| P7 | `07_derivations.json`, `construction/derivations/derive_purposes.py` | What rests on what; what blocks? |
| P8 | `08_outputs/{a,b,c}.json` | Is the answer right, and what is it standing on? |

Each pass directory also holds `agent.json`, `transcript.stdout.txt`,
`transcript.stderr.txt` and `workspace_snapshot/`.

**P7 and P8 already have surfaces.** `06_world/world.sqlite` is the world the
read-side explorer opens; §8.6 (derivation explorer) and §8.7 (frontier) of the
companion spec are the P7 and P3 views. This document specifies what is missing
between them.

---

## 3. Structural inspiration

Explicitly **code review** and **a CI build page**. Not Pipeline Builder.

From code review, take:

- a **queue of things needing a decision**, not a map of the system;
- **the diff as the unit** — what changed from the previous run, or from what
  was mechanically established;
- **the reviewer's verdict is a first-class recorded object**, attributable and
  reversible;
- **inline evidence** — the packet sits beside the judgment, never a click away.

From a CI build page, take:

- a **spine of stages** with per-stage status, always visible, never the front
  door;
- **failure localized to a stage** — you land on the first thing that broke;
- **"what will re-run"** stated before you trigger anything;
- **artifacts per stage**, downloadable and inspectable, without narration.

From neither: a canvas of the pipeline. Nine passes in a line do not need one.

---

## 4. The three surfaces

```text
┌──────────┬─────────────────────────────────────────┐
│  SPINE   │                                         │
│  P0 ✓    │            THE DOCKET                   │
│  P1 ✓    │      (front door — what needs me)       │
│  P2 ✓    │                                         │
│  P3 ✓    │   ┌───────────────────────────────┐     │
│  P4 ✓    │   │  THE WORLD EXPLORER           │     │
│  P5 ⚠ 81 │   │  (body — an item, opened)     │     │
│  P6 ~    │   │                               │     │
│  P7 ~    │   └───────────────────────────────┘     │
│  P8 ~    │                                         │
└──────────┴─────────────────────────────────────────┘
```

**Front door: the docket.** What needs a human. Never a pipeline.

**Body: the read-side explorer**, opened at the mark under discussion, with the
evidence packet beside it. An unresolved obligation is *already* a mark on the
field — hollow chip, dotted spokes. Adjudicating it is the mark filling in.

**Rail: the spine.** Nine passes, their state, and what an intervention costs.
Persistent, narrow, secondary.

---

## 5. The pass spine is a derivation graph

This is the load-bearing idea and it is reused machinery, not new machinery.

`_tv_derivations` already lets us say *this ran against input version N; the
input is now at N+3*. §8.6 turned that from a flag into an account. **Point the
same reasoning at passes instead of relations.**

A pass is:

```text
CERTIFIED     ran, scored clean, inputs unmoved since
PROVISIONAL   ran, but an input has moved since it ran
FAILED        ran and did not produce a valid artifact
STALE         an upstream pass has been intervened in
```

The consequence is the feature: **the cost of an intervention is knowable
before it is made.**

| Intervention | Invalidates | Preserves |
|---|---|---|
| Adjudicate (P5 disposition) | P6, P7 outputs, P8 | P0–P4, P7 program |
| Admit (P6 world/purpose) | P7 outputs, P8 | P0–P5 |
| Amend (P1 vocabulary) | P2 → P8 | P0 |

Cost is stated in passes **and** in wall clock, from the frozen `TIMEOUTS` map:
adjudication is P6+P7+P8; vocabulary amendment is the whole chain. The UI must
show this before the action, not after.

**A pass may not be marked certified by the front end.** Certification comes
from the scorers. The front end reports state; it does not confer it.

---

## 6. Interventions

A human can do exactly three things. Naming them tightly is most of the design.

### 6.1 Adjudicate

Overturn one P5 disposition. Cheap, local, and where the measured failure is.

An adjudication records:

```text
obligation_id
disposition          the human's verdict
supporting_evidence  locations from the packet, cited not typed
support_claim        one sentence: what the cited evidence establishes
supersedes           the machine disposition being overturned
actor, at            who and when
```

The burdens do not relax for a human. `SAME_ENTITY` and `DISTINCT` still
require establishing evidence; absence still does not establish distinctness.
A person who cannot cite a location cannot close the obligation. The correct
outcome of an unclear packet is that it stays `UNRESOLVED`.

### 6.2 Admit

Move a relation between `WORLD` and `PURPOSE`. Records the same shape, plus the
purpose-independence test the human applied.

### 6.3 Amend

Supply a distinction the constructor missed — a relation, a role, a contract
field. Expensive: it rebuilds nearly everything. The UI must make the cost
loud.

### 6.4 Every intervention is a proposal

Durable changes enter through propose, which auto-commits; revert is the
backward path. There are no silent edits and no in-place mutation of a pass
artifact. An overturned disposition is *superseded*, never overwritten — the
machine's original judgment stays readable, because the disagreement is the
most interesting record in the system.

---

## 7. ADJUDICATED — the fourth construction origin

### 7.1 The problem

`ConstructionOrigin` is today `MECHANICAL | SEMANTIC | DERIVED`. If a person's
judgment enters as `SEMANTIC`, the world launders a human decision as a machine
one, and every downstream claim about how the world was constructed becomes
untrue.

### 7.2 The addition

```text
MECHANICAL    deterministic compilation from sources
SEMANTIC      the constructor's adjudicated judgment
DERIVED       computed from other relations, maintained
ADJUDICATED   a person's judgment, superseding or supplying one
```

This is a member of the sidecar `StrEnum` in
`research/semantic_integration/core/origins.py`. **It does not touch
`core/kernel.py`.** The semantic calculus does not move — Referent, named typed
n-ary Relation, Derivation, grounding, origin, revision, stale/current, scope,
unresolved — only the construction-origin axis grows a fourth value.

TaskView's `ASSERTED`/`DERIVED` bookkeeping is untouched and remains a
different question.

### 7.3 Its mark

Origin is geometry, not colour. The existing vocabulary:

```text
MECHANICAL    chip, outlined
SEMANTIC      chip, filled
DERIVED       chip with a shelf beneath it
UNRESOLVED    chip outline, empty, dotted spokes
```

Proposed:

```text
ADJUDICATED   chip with a rule above it
```

Symmetric to `DERIVED` and readable as what it is: *derived* rests on something
below; *adjudicated* had someone standing over it. Implementable as
`shelfNode` with a sign flip, so the gap is governed by one constant on both
sides.

Calibration pending; the *structure* — that it is a shape and not a hue — is
not.

### 7.4 SHOW

`ShowLayer` gains `adjudicated`, default **on**. A person must never have to
opt in to seeing which parts of the world a person decided.

---

## 8. Views

### 8.1 The docket

The front door. One row per obligation still open, or decided in a way that
merits review.

```text
┌───────────────────────────────────────────────────────────────┐
│ 81 open · 20 decided · 3 blocking a purpose                   │
├───────────────────────────────────────────────────────────────┤
│ ⚠ identity_judgment(Northbridge Analytics, Northbridge LLC)   │
│   UNRESOLVED · blocks purpose B · 4 observations              │
│   "packet preserves multiple live candidates"                 │
├───────────────────────────────────────────────────────────────┤
│   clause_presence(contract_07, change_of_control)             │
│   UNRESOLVED · non-blocking · 2 observations                  │
└───────────────────────────────────────────────────────────────┘
```

**Ordered by what it unblocks, never by arrival.** P7 already declares
`blocking_unresolved_state` and `non_blocking_unresolved_state` per derived
relation; an obligation whose relation appears in a blocking premise of a
purpose output sorts above one that does not. This is an earned ordering, read
from the artifacts, not a heuristic.

Each row must carry **the machine's own reason for declining**, from
`rationale`. That sentence is what makes a three-second decision possible.

Filters: blocking / all; open / decided; by relation; by purpose.

### 8.2 The obligation

One item, opened. Three panes, no navigation between them.

```text
┌──────────────────┬─────────────────────┬──────────────────────┐
│ THE PROPOSITION  │ THE PACKET          │ THE JUDGMENT         │
│                  │                     │                      │
│ relation         │ selected_observ.    │ machine: UNRESOLVED  │
│ values           │  ▸ crm.csv:L14      │ rationale            │
│ why_demanded     │    "Northbridge…"   │ ─────────────────    │
│ required_by      │  ▸ registry.csv:L3  │ your verdict:        │
│ current state    │    "Northbridge…"   │ [SAME][DIST][UNRES]  │
│                  │ selection_rationale │ cite: ☑ L14 ☐ L3    │
│                  │ known_missing_info  │ support_claim: ___   │
└──────────────────┴─────────────────────┴──────────────────────┘
```

Rules:

- Evidence is **cited by selection**, never retyped. A verdict's
  `supporting_evidence` can only contain locations present in the packet.
- `known_missing_information` is displayed as prominently as what was found.
  It is the constructor's own account of why it may be wrong.
- A closing verdict (`SAME_ENTITY`, `DISTINCT`, `ACCEPT`, `REJECT`) requires at
  least one citation and a `support_claim`. `UNRESOLVED` requires neither.
- The field, showing this obligation's mark and its neighborhood, is available
  beside or beneath. The obligation is a mark; the mark is the same mark.

### 8.3 The vocabulary review

`01_vocabulary.json` as a reviewable list, not a form. One card per relation:
name, roles and types, meaning, admission, construction class, grounding
contract, and — for `SEMANTIC` relations — the full `RelationContract`
(dispositions, scope, algebra, epistemic contract).

The diff is against **what the purposes asked for**: P0's
`required_semantic_distinctions` per purpose, matched against the relations
that claim to serve it via `required_by`. A required distinction with no
relation is the interesting row.

The schema canvas (`SchemaCanvas.tsx`) is the graph projection of this view and
already exists.

### 8.4 The intake

`02_mechanical_report.json` as a coverage account: referents, base tuples,
candidate tuples, notes. The only question with teeth is **grounding
completeness** — every BASE tuple must ground to exact source locations, and
the view's job is to make an ungrounded tuple impossible to miss.

Sources are listed with what each contributed. A source that contributed
nothing is a finding.

### 8.5 The admission gate

`06_admission.json`: each persistent relation with its admission, reason, and
purpose-independence test. Two columns, `WORLD` and `PURPOSE`, and the
intervention is moving a card between them.

The rule this view enforces visually: **purpose outputs are not promoted into
the World.** A relation that appears in an `08_outputs` shape and is also
admitted `WORLD` is a finding.

### 8.6 The brief

`00_intention_contract.json` beside the purpose file it was compiled from.
Two columns, source left, contract right. The only question is whether the
compilation dropped or invented a requirement, so the view is a reading view
and carries no intervention of its own — a disagreement here is an amendment,
which is §6.3.

### 8.7 The answer

`08_outputs/{a,b,c}.json` in the shape the purpose declared, with each output
row linked to the derivation that produced it (§8.6 of the companion spec) and
onward to the obligations that were blocking or non-blocking premises.

This closes the loop: an answer, the computation, the world it read, the
judgments that world rests on, the evidence those judgments cite.

---

## 9. Visual state vocabulary — additions

The companion spec's §9 governs marks. This adds only:

```text
PASS STATE          certified · provisional · failed · stale
                    weight and rule, never colour

ADJUDICATED         chip with a rule above it (§7.3)

SUPERSEDED          the machine's original disposition, shown at
                    reduced strength beneath the human's verdict —
                    present, legible, not current

BLOCKING            an obligation a purpose output waits on:
                    marked by inset rule in the docket margin,
                    the same mark §8.6 uses for a moved input
```

The three status colours remain the queue's. Construction state stays
geometric.

---

## 10. The seams

The seams are the product. Enumerated, because an unlisted seam does not get
built.

```text
docket row              → the obligation, opened (§8.2)
obligation              → its mark on the field
obligation              → the derivation that waits on it
verdict recorded        → passes P6–P8 go stale on the spine
spine pass              → its artifact view (§8.3–§8.7)
vocabulary relation     → its extension in the read-side table
vocabulary relation     → the obligations generated for it
admission card moved    → passes P7–P8 go stale
purpose output row      → its derivation → its premises → its obligations
adjudicated mark        → the verdict, the citation, the person
```

---

## 11. Interaction rules

**Clicking a docket row** opens the obligation. It does not adjudicate.

**Recording a verdict** stages a proposal. It does not re-run anything. The
spine goes stale and states the cost; running is a separate, deliberate act.

**Clicking a pass** opens its artifact view. It never opens a transcript.

**Clicking an adjudicated mark** shows the human verdict, its citations, and
the machine judgment it superseded.

**Reverting an adjudication** restores the machine disposition and returns the
downstream passes to the state they had. Revert is the backward path; there is
no other one.

---

## 12. Front-end API requirements

Served by the read plane, over frozen artifacts, under the same bearer guard.

```text
GET  /construction                    passes, states, artifact presence, counts
GET  /construction/pass?id=p5         one pass artifact, parsed
GET  /construction/docket             obligations + machine dispositions + blocking
GET  /construction/obligation?id=…    proposition + packet + disposition + verdict
GET  /construction/cost?at=p5         what an intervention here invalidates
POST /construction/verdict            record an adjudication as a proposal
POST /construction/admission          record an admission change as a proposal
DELETE /construction/verdict?id=…     revert
```

Rules carried from the companion spec: retrieval does not call a model; exact
misses stay exact misses; the reads are deterministic and cheap enough that the
docket is not paginated below a thousand obligations.

Verdicts persist beside the run, never inside a pass artifact.

---

## 13. Deliberately not built

- **Pass transcripts as prose.** The agent's reasoning is not evidence; the
  grounding is. `agent.json` may contribute files-written and tool counts to a
  pass view. The narration is not surfaced.
- **A pipeline canvas.** Nine passes in a line.
- **The trial matrix.** T1–T5 × p0–p8 is research apparatus. A useful second
  screen; a terrible first one.
- **Live run control.** Frozen artifacts only.
- **Free-text evidence.** Citations are selections from the packet.
- **Bulk adjudication.** "Accept all remaining" is how 81 careful declines
  become 81 unsupported closures.

---

## 14. First implementation slice

Build the hardest screen first, all the way, before scaffolding the others.

1. `ADJUDICATED` in `ConstructionOrigin`, its mark, its SHOW layer.
2. The construction read plane: `/construction`, `/construction/docket`,
   `/construction/obligation`.
3. **The docket (§8.1) and the obligation (§8.2), complete** — including
   citation-by-selection, the burdens, and the verdict as a proposal.
4. The spine (§5) with pass state and the cost statement.
5. Then, and only then, §8.3–§8.7.

The demo this produces: *the constructor declined 81 times; here is exactly
the evidence it looked at; you agree or you do not; three passes go amber and
the surface says what rebuilding them costs.*

---

## 15. Acceptance cases

**Under-closure corrected.** An obligation the constructor left `UNRESOLVED`
where the packet establishes identity. A person cites two locations, records
`SAME_ENTITY`, and the mark on the field fills in with a rule above it. P6–P8
go stale. The machine's judgment remains readable beneath.

**Under-closure upheld.** A packet that genuinely preserves multiple live
candidates. The person records `UNRESOLVED`, which is a decision and is
recorded as one. Nothing goes stale.

**Closure refused.** A person selects `SAME_ENTITY` and cites nothing. The
verdict cannot be recorded.

**Cost before action.** Before any verdict is staged, the spine states which
passes it invalidates and what they cost.

**Provenance survives.** Opening any purpose output reaches, in finite clicks,
the human verdicts it rests on — and distinguishes them from the machine's.

**Revert.** An adjudication is reverted; the machine disposition is current
again and the downstream passes return to their prior state.

---

## 16. Guiding principle

The read side visualizes **meaning**. This side visualizes **decisions** — who
made each one, on what evidence, and what it would cost to make it differently.

The constructor is good at the safe half and honest about the rest. Its
measured failure is not error but under-closure: 81 declines where the evidence
was sufficient. That is not a modelling problem. It is a docket.

The surface's only job is to make those decisions cheap to review, expensive to
fake, and impossible to confuse with the machine's.
