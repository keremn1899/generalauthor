# What the World IR canvases carry over from the product page

The product canvas (`frontend/src/product/`) is a frozen lineage. It is also the
only place in this repository where a graph surface was tuned against real use
over a long time, so it is the closest thing the World IR surfaces have to a
design ancestor.

Reuse across a frozen boundary is not free. Whatever we take either becomes a
shared module — which means the frozen lineage now has a live dependency — or a
fork, which starts identical and drifts. Neither is wrong; picking one silently
is. This file is the ledger: for each thing the World canvases take, whether it
is **shared**, **forked**, or **dropped**, and why.

The rule the ledger enforces: *shared by default, forked only where sharing
would change the frozen surface, and a fork always names its ancestor in its own
docstring.*

---

## Shared — one module, both lineages

These live in `frontend/src/styles/`. The product imports them; so do we. A
change here is a change to both surfaces, which is the point.

| What | Module | Note |
|---|---|---|
| Palettes, focus, chrome, status | `graphDna.ts` — `GRAPH_DNA_THEME`, `GRAPH_DNA_PROVISIONAL_THEME`, `GRAPH_DNA_FOCUS`, `GRAPH_DNA_CHROME`, `GRAPH_DNA_STATUS` | |
| Mark geometry | `graphDna.ts` — `GRAPH_DNA_GEOMETRY`, `GRAPH_DNA_CHIP` | |
| Interaction constants | `graphDna.ts` — `GRAPH_DNA_INTERACTION` | including `selectionSpeed: 8`, `selectionClearance: 11`, `selectionDotGap: 4.5`, `selectionLine: 1.5`, `selectionMotion` |
| The motion spine | `motion.ts` — `createMotionPlans`, `DEFAULT_MOTION_PLANS`, `motionCssVariables` | `DEFAULT_MOTION_PLANS` was added for the World side and is now what `usePresence` reads, so "the kernel's timings" is an object rather than a convention |
| Presence / lifecycle | `useMotion.ts`, `usePresence.ts`, `presence.css` | |
| G6 state motion | `motionG6.ts` | |
| Type face | `typography.ts` | Jost, 400 |
| Overlay chrome | `product/OverlayPanel.tsx`, `product/overlayChrome.ts` | The one place the World page imports **from** `product/` rather than from `styles/`. It is read-only use of a frozen module; if it ever needs to change for us, it moves to `styles/` first |

Two constants are **World-only additions** to a shared module:

- `GRAPH_DNA_INTERACTION.selectionPlateClearance: 5` — the product had one kind
  of mark, so one clearance was enough. We ring plates as well as discs, and 11
  units around a chip 10 units tall is a box with more air than mark in it.
  Added rather than retuned: changing `selectionClearance` would have moved the
  product's rings.

## Forked — same idea, separate file

### Marching ants — `styles/SelectionAnts.tsx` (ancestor: `explorations/SelectionAntRing.tsx`)

Carried over whole in behaviour: beads sized in **graph space** so the dotted
look survives zoom, bead count dropping rather than fusing into a solid outline,
`pathLength={100}` normalising the dash cycle, arrival and departure on the
kernel's `emit`/`absorb`, the march pausing while a mark is dragged.

Forked, not shared, for one concrete reason: `SelectionAntRing` draws a
`<circle>`, and `product/ProductGraphCanvas.css` animates
`.gdna__ant-ring circle` **by element name**. The generalisation needs a
`<path>` — one element that can be a circle, a square-cornered box, or a line.
Editing the ancestor in place would have silently stopped the frozen product's
beads from marching. The two are kept apart deliberately.

What is new, and belongs to World IR rather than to the ancestor:

- **Three geometries, because there are three marks.** A referent takes a
  circle; an assertion or demand plate takes a square-cornered rect; a binary
  assertion *is* the filament, so the beads march along the line itself, trimmed
  clear of the disc at each end.
- **No radius on the rect.** It would be the only rounded corner on the map.
- **Nothing is traced around a mark a filter is hiding.** An outline is a claim
  that something is inside it. Selection survives the filter; its drawing does
  not.
- **A filament too short to march is not drawn.** Beads on it would sit inside
  the discs; the lit palette still says what is selected.

Not carried: `withdrawOnDrag`. The product could let the ring fall away while a
node moves. On the field the ring stays attached and only the march pauses,
because the field's whole contract is that existing marks do not move — a ring
that detaches would be the one thing on screen implying they might.

---

## Dropped

- **The G6 `selected` element state.** Both canvases used to lay a translucent
  halo under the selected disc and thicken the selected edge. On a field of
  filled discs the halo read as a smudge rather than as a choice, and it said
  the same thing the ants say, more quietly — two marks for one fact. Selection
  is now drawn in exactly one place. `applySelection` is gone from both
  `WorldCanvas` and `SchemaCanvas`, and neither passes a `selected` style.
- **Bolder label text as a selection cue.** Colour and weight are already spent:
  weight is the type face's one voice, and colour is status. Selection needed a
  channel of its own, which is what an outline is.

---

## Invariants both lineages hold

Carried over as rules, not as code — worth restating because a violation reads
as a local styling choice rather than as drift:

- **Meaning is structural, never decorative.** Construction origin is geometry —
  filled, outlined, shelf, hollow. Colour is for status only.
- **No corner radius.** Sharp corners, thin regular Jost.
- **Retrieval and traversal do not call a model.** Exact misses stay exact
  misses; search results stay candidates.
- **Existing marks never move.** Layout settles at load; expansion places new
  marks around what is already standing (`world/relax.ts`, `world/workingSet.ts`).

## New here

Things the World canvases have that the product page had no reason to:

- **Folding a bond open.** A binary tuple is drawn either as the filament
  between its referents or as a plate standing between them with a named spoke
  to each — `foldingOf` / `open` / `collapse` in `workingSet.ts`, offered from
  the reader. The product's edges were binary and unnamed, so there was nothing
  under a line to reveal; here the roles are the whole content of a named typed
  n-ary relation, and a labelled line cannot show them. Semantic zoom, not
  decluttering. An obligation has no second form at any arity.
- **The field, remembered.** `fieldMemory.ts` keeps which marks someone put on
  the field and where they stand, in this browser, keyed by world **and
  revision** — an assertion id means something only within the revision it was
  read from, so a rebuild starts from an empty field rather than a
  plausible-looking old one. The product persisted display *preferences*
  (`product/graphPrefs.ts`), which is the same argument for the same storage;
  what is new is that here the arrangement itself is work worth keeping.
- **A note on element ids.** The plate keeps the assertion id; the filament is
  drawn under `bond:<assertion id>`. G6 keys nodes and edges in one namespace,
  so sharing the id makes `open` reuse the edge's `path` instead of building
  the plate's `rect`.

## Motion: shared, extended, and one thing fixed for both

The motion kernel is **shared, not forked** — `styles/motion.ts`,
`styles/presence.css`, `styles/usePresence.ts`, `styles/Swap.tsx`. World IR
extended it rather than copying it, so what follows lands on the product's
surfaces too. That is intended: this is the visual kernel, and a second copy of
a duration is a second thing that drifts.

Added to the kernel here:

- **`still()` and `STILL_RULES`** — a decision *not* to animate, with its
  reason, as an attribute the stylesheet enforces. See
  `styles/transition_map.md` §6.
- **`staggerWaves`** — arrivals ordered by distance from what they grew out of.
  The product's graph arrived whole; a World field grows one expansion at a
  time, and a ring of new marks should read as a wave front rather than a flash.
- **`useArrivals`** and `.motion-emit` — emit on the appended row only.
- **`motion-swap--fill`** — a swap that fills its parent's column. It
  generalises two bespoke selectors that already existed for
  `.ov__body--flush` and `.traversal-modal`; those stay as they are, because
  changing them would move the frozen surfaces for no gain.

Fixed for both: **`useOutgoing` never mounted the outgoing copy in time**, so
every `Swap` in the product — the graph reader, the logs pane, the traversal
menu, the write timeline — had been a plain emit rather than absorb ∘ emit.
`mounted` is now settled during render. This is a change to how the frozen
lineage looks, and it is the intended behaviour its own docstring describes,
not a retune.

## The design lab, and why it renders the product rather than a picture of it

`WorldLabPage` is a World-only surface: the product page had no equivalent. Its
rule is that **every specimen is the shipping component**, driven by fixtures
from `mockWorldData.ts` rather than by the read plane.

That was already true of the canvases, the tables and the reader panels. It was
not true of three things, and each had drifted:

- The **mark gallery** drew origin geometry by hand in SVG — with a corner
  radius, which the product does not have. It now renders `WorldCanvas` over
  `createSpecimenSet()`: one mark of every construction origin, tuned through
  the same `MarkParams` object the field ships with.
- The **ant gallery** hand-computed `stroke-dasharray`, so it showed a ring
  the product never draws. `SelectionAnts` locks the bead count to *graph-space*
  path length with `pathLength={100}`, which a fixed dasharray cannot
  reproduce. Same canvas, same component; `WorldCanvas` gained an optional
  `ants` prop so the lab can tune the real ring instead of drawing a copy.
- The **show band**, the **shell tokens** and the **speed control** are covered
  under `ShowBand`, `worldChrome.ts` and `scaleMotionPlans` above.

The rule worth keeping: a design surface that can show something the product
cannot is worse than no design surface, because it reports a look that does not
exist. If a specimen needs a knob the component has no prop for, the prop is
the change — not a second drawing.

## Not carried over at all

Named so their absence is a decision on the record rather than an oversight:

- The product's **causal and structural layout algorithms**. They encode a
  binary-edge graph's notion of flow, and a named typed n-ary relation has no
  single direction to lay out along. The field settles with d3 at load instead.
- **Live physics.** d3 runs once, at load. The interactable surface is the
  product's: drag one mark, its bonds follow, nothing else moves.
- The product's **workbench / settings panel** for live DNA tuning. World IR
  reads the constants; it does not offer to retune them per screen.
