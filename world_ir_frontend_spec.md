# World IR Front-End Specification

**Status:** Working front-end contract for the read-side World IR product  
**Primary renderer:** G6 canvas  
**Scope:** Human exploration of a compiled semantic world  
**Non-goal:** Redesigning the canonical World IR around visualization

---

## 1. Product boundary

The front end is a **read-side human explorer over World IR**.

It helps a human answer:

- What referents exist?
- What named relations connect or describe them?
- What semantic assertions are currently established?
- What is mechanically derived versus semantically authored?
- What is unresolved?
- Why does a relation/assertion exist?
- What source evidence grounds it?
- What derived results depend on it?
- What is stale, incomplete, or outside a declared scope?

It is **not**:

- an action/workflow system;
- a write-back interface to source systems;
- a replacement for Python/SQL;
- a graph-native rewrite of World IR;
- a giant force-directed visualization of every tuple;
- a new ontology representation.

The same World IR should support:

```text
World IR
  ├─ SQL
  ├─ Python
  ├─ LLM/programmatic access
  └─ G6 human exploration
```

---

# 2. Canonical semantic model — frozen

The canonical World IR is not a property graph.

The semantic core is:

```text
REFERENT
NAMED TYPED N-ARY RELATION
DERIVATION
```

with mandatory/cross-cutting state such as:

```text
GROUNDING
REVISION
ORIGIN
STALE/CURRENT STATE
SCOPE
COMPLETENESS
UNRESOLVED / EPISTEMIC STATE WHERE REPRESENTED
```

The visual layer MUST NOT change this representation.

## 2.1 Referent

A referent is thin and stably addressable.

Conceptually:

```text
Referent
  id
  optional display label
  optional source/external identities
  grounding
```

Kinds, properties, classifications, compatibility, membership, affectedness, etc. are not required to be intrinsic fields. They may remain relations.

## 2.2 Named typed n-ary relation

A relation has:

```text
NamedRelation
  stable name
  ordered named roles
  role types
  zero or more tuples
```

A tuple has:

```text
RelationTuple
  role values
  optional stable assertion identity
  construction origin / assertion state
  grounding
```

Example:

```text
acceptable_replacement(
  new_part = part:X110,
  old_part = part:X160,
  context = context:outdoor_enclosure
)
```

The `context` role is part of the assertion's meaning. It must not be visually discarded.

## 2.3 Derivation

Derived semantic state remains a named relation, with an associated derivation record:

```text
Derivation
  output relation
  computation / SQL / expression
  input relations
  revisions
  execution receipt
  stale/current state
  scope/completeness
```

The front end may visualize the derivation graph, but it must not invent a second computation model.

---

# 3. Visualization architecture

G6 receives a **projection** of World IR.

```text
World IR
    ↓
GraphProjection
    ↓
G6
```

The projection is allowed to optimize presentation.

The projection is NOT canonical semantic state.

No front-end convenience should require rewriting the World kernel.

---

# 4. Lossless graph projection

The universal G6 representation of an n-ary relation is an **incidence graph**:

```text
referent ─role─> relation assertion node <─role─ referent
```

Example:

```text
part:X110
    |
    | new_part
    v
[ acceptable_replacement ]
    ^                  ^
    | old_part         | context
    |                  |
part:X160      context:outdoor_enclosure
```

This can represent arbitrary finite arity without information loss.

The relation assertion node represents one tuple, not merely the relation schema.

---

# 5. Visual primitives

The front end should need only a few primitive visual kinds.

## 5.1 Referent node

Represents a stable referent.

Suggested card:

```text
┌─────────────────┐
│ Part            │
│ X160            │
│                 │
│ voltage   24 V  │
│ lifecycle active│
└─────────────────┘
```

Displayed "properties" may actually be scalar/unary relations projected into the card.

The UI must not imply that these properties are intrinsically stored on the referent.

## 5.2 Relation assertion node

Used when a relation is n-ary, epistemically important, expanded, or otherwise deserves first-class inspection.

Example:

```text
┌────────────────────────┐
│ acceptable_replacement │
│ SEMANTIC               │
│ CURRENT                │
└────────────────────────┘
```

Edges connecting to referents are labelled with role names.

## 5.3 Collapsed binary relation edge

A binary tuple may be rendered as an ordinary edge by default:

```text
supplier_listing ── listing_of ──> part
```

This is a visual shorthand for the canonical relation assertion.

The user must be able to expand/select the edge and inspect its full assertion metadata and grounding.

## 5.4 Literal / scalar presentation

Scalar-valued relations should normally appear as:

- referent-card fields;
- inspector values;
- table columns;
- badges;

rather than canvas nodes.

Avoid:

```text
X160 → rated_voltage → 24
X160 → min_temp → -20
```

unless explicitly requested for debugging or provenance.

## 5.5 Source/evidence node

Source observations should normally remain hidden.

They appear when provenance/evidence is expanded.

Example:

```text
acceptable_replacement(...)
       ↓ grounded_by
engineering_notes.md lines 6–14
       ↓ grounded_by
bom.csv row 2
```

## 5.6 Derivation node

Derivations may appear in computation/lineage mode.

Example:

```text
voltage_compatible ─┐
temperature_compatible ─┼─> eligible_part
acceptable_replacement ─┘
```

A derived assertion may expand further to the particular input tuples used where that lineage is available.

---

# 6. Default projection rules

Use simple deterministic projection defaults.

```text
unary/classification relation
→ badge, property, filter, or table field

binary referent↔referent relation
→ ordinary labelled edge

n-ary relation
→ assertion node + role-labelled edges

scalar-valued relation
→ card property / inspector / table by default

derived relation
→ normal semantic result with DERIVED badge;
   derivation shown on demand

semantic assertion
→ normal semantic result with SEMANTIC badge;
   grounding shown on demand

mechanical assertion
→ normal semantic result with MECHANICAL badge;
   optionally hidden by default at higher semantic zoom

unresolved semantic obligation
→ visually distinct unresolved relation/question projection
```

These are presentation rules only.

---

# 7. Semantic zoom

The canvas should support multiple conceptual zoom levels.

## 7.1 World/schema level

Shows vocabulary rather than individual tuples.

Example:

```text
SupplierListing ─ listing_of ─ Part
Part ─ candidate_replacement ─ Part
Part ─ acceptable_replacement ─ Part + Context
Part ─ used_in ─ BOMItem
```

This answers:

> What kind of world is represented here?

Schema view should expose:

- relation name;
- ordered roles;
- role types;
- BASE/DERIVED mode;
- short meaning/description.

## 7.2 Referent level

Focus on one referent and a bounded semantic neighborhood.

Example:

```text
part:X160
├─ listing_of ← supplier:ABC-829
├─ used_in → BOM-A
├─ candidate_replacement ← X110
└─ acceptable_replacement ← X110
     context: outdoor_enclosure
```

This is likely the primary human exploration mode.

## 7.3 Assertion level

Expand one relation tuple into its full role structure.

Example:

```text
X110 ─new_part────┐
                  ↓
       [acceptable_replacement]
                  ↑
X160 ─old_part────┤
outdoor ─context──┘
```

## 7.4 Evidence / derivation level

Expand downward into:

- source grounding;
- construction origin;
- derivation inputs;
- dependency lineage;
- completeness/scope;
- stale/current state.

This answers:

> Why does the World believe or compute this?

---

# 8. Core front-end views

The G6 canvas can remain the main surface, but it should be paired with lightweight inspectors/lenses.

## 8.1 Search

Search should resolve to:

- referents;
- relation names;
- possibly assertion IDs;
- source handles where useful.

Selecting a result focuses or materializes the relevant canvas neighborhood.

## 8.2 Referent explorer

Selecting a referent shows:

- label / identity;
- useful projected properties;
- attached relations grouped by relation name;
- semantic/mechanical/derived counts if useful;
- unresolved obligations involving the referent;
- provenance only on demand.

## 8.3 Relation explorer

Selecting a relation schema shows:

- name;
- meaning;
- roles;
- mode;
- count;
- current/stale/completeness state where meaningful.

Its extension should be viewable as a table.

Example:

| new_part | old_part | context | state |
|---|---|---|---|
| X110 | X160 | outdoor_enclosure | ASSERTED_TRUE |
| R210 | R200 | high_vibration_cabinet | ASSERTED_TRUE |
| X110 | X160 | indoor_panel | UNRESOLVED |

Selecting a row focuses the corresponding graph projection.

The table and graph are two projections of the same relation state.

## 8.4 Assertion inspector

Selecting an edge or relation node should expose:

```text
relation
role values
assertion ID if present
construction origin
assertion/epistemic state
current/stale state
grounding
construction method
relation/World revision
```

No LLM-generated explanation is required.

## 8.5 Provenance inspector

For a selected assertion:

```text
acceptable_replacement(
  X110,
  X160,
  outdoor_enclosure
)
```

show source grounding such as:

```text
engineering_notes.md
  lines 6–14

bom.csv
  row 2

construction origin
  SEMANTIC
```

Source evidence may be expanded into temporary canvas nodes or rendered in a side panel.

## 8.6 Derivation / dependency explorer

For a derived relation/assertion:

```text
eligible_part(...)
```

show:

```text
eligible_part
  ↑
  ├─ voltage_compatible
  ├─ temperature_compatible
  └─ acceptable_replacement
```

Where available, allow drill-down from relation-level dependency into tuple-level provenance.

## 8.7 Semantic frontier / unresolved view

Unresolved semantic demand should be first-class.

Example:

```text
acceptable_replacement(
  X110,
  X160,
  indoor_panel
) = ?
```

Display:

```text
state
  UNRESOLVED

demanded by
  viable_replacement / analysis purpose

available evidence
  [if packet/evidence-selection state is available]

current positive assertion
  none
```

Important:

```text
missing positive assertion != false
```

The front end must not visually imply falsehood from absence.

---

# 9. Visual state vocabulary

The canvas should visually distinguish at least:

```text
MECHANICAL
SEMANTIC
DERIVED
UNRESOLVED
STALE
CURRENT
INCOMPLETE / UNKNOWN completeness where applicable
```

Exact colors/shapes are presentation choices.

Semantics are not.

Useful toggles:

```text
SHOW
☑ semantic
☑ derived
☐ mechanical
☑ unresolved
☐ provenance
☐ source observations
```

Mechanical detail may overwhelm semantic seams and should often be suppressible.

---

# 10. Graph density and expansion

Never render the entire World by default.

Exploration should be bounded.

Recommended controls:

```text
expand relation
expand referent neighborhood
expand N hops
show relation schema
show relation extension/table
show derivation
show provenance
collapse assertion
collapse binary relation
```

Large relation extensions should remain table/query results until individual rows are selected.

The G6 canvas is an exploration workspace, not a database dump.

---

# 11. Tables and graph coexistence

Do not choose between graph and table.

Use each for what it represents well.

Graph:

- referent neighborhoods;
- schema relationships;
- cross-authority seams;
- dependency paths;
- provenance paths;
- selected n-ary assertions.

Table:

- relation extensions;
- n-ary tuples at scale;
- query results;
- sorting/filtering/comparison.

A selected table row should focus its graph projection.

A selected graph relation should be able to open its relation table.

---

# 12. Python / analytics are separate consumers

The front end does not need to implement arbitrary analytical visualization inside the World explorer.

The read-side architecture remains:

```text
World IR
  ↓
SQL / Python
  ↓
pandas / numpy / scipy / networkx / matplotlib / etc.
```

Analytical charts, distributions, maps, simulations, and domain-specific dashboards should normally be generated from Python/SQL results.

The G6 front end is primarily for **semantic-world exploration and explanation**.

---

# 13. Queries and computed selections

The front end may expose a query result on the canvas.

Example workflow:

```text
run SQL / select relation subset
        ↓
result table
        ↓
"show on canvas"
        ↓
bounded graph projection
```

Do not invent a new graph query language solely for visualization.

SQL + current World APIs remain the read substrate unless a concrete limitation appears.

---

# 14. Front-end API requirements

The UI projection layer needs read access equivalent to:

```text
list/describe relation schemas
read relation tuples
query SQL / semantic query
inspect tuple
read construction origin
read grounding
read stale/current state
read completeness/scope
read derivation metadata/dependencies
read unresolved obligations where available
```

If current APIs are awkward, create an adapter/projection layer before changing World IR.

Suggested boundary:

```text
SemanticWorld
    ↓
WorldExplorerAdapter
    ↓
GraphProjection
    ↓
G6
```

`WorldExplorerAdapter` may normalize output for the front end.

It must not become a second semantic store.

---

# 15. Suggested projection objects

The front end may use a presentation-only structure like:

```ts
type VisualReferent = {
  id: string
  label?: string
  displayType?: string
  properties?: Record<string, unknown>
}

type VisualRelationAssertion = {
  id: string
  relation: string
  roles: Array<{
    role: string
    value:
      | { kind: "referent"; id: string }
      | { kind: "scalar"; value: unknown }
  }>
  origin?: "MECHANICAL" | "SEMANTIC" | "DERIVED"
  epistemic?: string
  stale?: boolean
}

type VisualEdge = {
  source: string
  target: string
  roleOrRelation: string
}

type VisualGrounding = {
  provider?: string
  nativeHandle?: string
  sourceRevision?: string
  nativeLocation?: string
}
```

These are projection contracts only.

Do not copy them into the semantic kernel merely because the front end uses them.

---

# 16. Interaction rules

## Clicking a referent

- focus;
- show attached relations;
- optionally expand selected relation families;
- open inspector.

## Clicking a binary edge

- inspect full underlying relation tuple;
- expose origin/grounding;
- allow "expand relation assertion."

## Clicking an n-ary assertion node

- show all roles and values;
- show grounding;
- show epistemic state;
- show derivation if derived;
- show source evidence on demand.

## Clicking a relation schema

- show description/roles;
- show relation table;
- allow "show selected tuples on canvas."

## Clicking provenance

- show exact source pointer/location;
- optionally materialize source observation nodes.

## Clicking unresolved state

- explain why the obligation exists if demand metadata is available;
- do not offer write/action workflow in this read-side product.

---

# 17. Product scope: read-side only

Explicitly excluded:

```text
source-system mutations
actions
workflow execution
approval flows
write-back
automated operational decisions
```

The front end may inspect semantic resolution state.

It does not need to perform external actions.

If semantic authoring/editing is later added, treat it as a separate feature discussion rather than assuming it now.

---

# 18. Non-negotiable architectural rules

1. **Canonical World IR remains relational.**
   G6 is a projection.

2. **N-ary relation semantics must never be flattened lossy.**
   Role identity matters.

3. **Binary edge rendering is shorthand only.**
   The underlying tuple remains inspectable.

4. **A missing assertion must not automatically render as false.**

5. **Grounding/provenance belongs to the assertion, not merely the referent.**

6. **Derived state must remain distinguishable from base mechanical/semantic assertions.**

7. **Tables and graph are complementary projections.**

8. **Scalar relations do not need to become graph nodes.**

9. **Do not display the whole World by default.**
   Exploration is local/query-driven.

10. **Do not redesign World IR for front-end convenience.**
    Add projection/adaptation code first.

---

# 19. Minimal first implementation

A first useful front end can be very small.

Required:

```text
G6 canvas
search
referent selection
binary relation edges
n-ary relation assertion nodes
role-labelled edges
relation table
assertion inspector
grounding/provenance inspector
origin badges
unresolved state
local expansion/collapse
```

Optional later:

```text
schema semantic zoom
derivation graph
source-observation expansion
completeness overlays
staleness overlays
saved layouts
query-to-canvas
large-world clustering
domain-specific cards
```

Do not block the first implementation on the optional list.

---

# 20. Initial acceptance cases

Use the existing BOM World as the first front-end fixture.

The UI should faithfully render examples such as:

## Binary cross-source relation

```text
listing_of(listing, part)
```

Default:

```text
SupplierListing ─ listing_of ─> Part
```

## Ternary semantic assertion

```text
acceptable_replacement(
  part:X110,
  part:X160,
  context:outdoor_enclosure
)
```

Must retain all three roles.

## Unresolved semantic obligation

```text
acceptable_replacement(
  part:X110,
  part:X160,
  context:indoor_panel
) = UNRESOLVED
```

Must not appear as rejected/false.

## Derived state

```text
eligible_part(...)
```

Must be visually distinguishable as derived and allow dependency inspection.

## Conflict

```text
spec_conflict(...)
```

Should expose affected referents and source-grounded conflicting observations without forcing every literal observation into the default canvas.

---

# 21. Success criterion

The front end succeeds when a human can move from:

```text
"What is in this World?"
```

to:

```text
"What is this thing?"
"How is it related?"
"What does this assertion actually mean?"
"Why is it here?"
"Where did it come from?"
"What computation depends on it?"
"What is unresolved?"
```

without needing to understand the source file formats or database schema.

That is the human analogue of the Python/LLM programming value:

> semantic compilation moves heterogeneous-source reconciliation below the consumer interface.

---

# 22. Guiding principle

The front end should visualize **meaning**, not storage.

The canonical semantic shape is:

```text
thin referents
+
named typed n-ary relations
+
maintained derivations
+
grounding / epistemic state
```

G6 provides a flexible human projection of that state.

The visual system may evolve aggressively.

The semantic representation should remain stable unless a concrete correctness/computation counterexample demonstrates that the current core cannot faithfully represent something required.
