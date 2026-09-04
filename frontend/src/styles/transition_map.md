# Transition map — World IR

What may move, what must not, and why. Companion to `motion.ts`; subordinate to
`world_ir_frontend_spec.md` and `constructor_frontend_spec.md`.

The live product currently has **no motion at all**. `WorldPage.css` (675 lines)
and `ConstructionPage.css` (1277 lines) contain zero `transition`, `animation`
or `@keyframes`. The kernel is imported by eleven files, all of them in the
frozen `product/` lineage; `motionCssVariables` is emitted only by
`product/ProductShell.tsx`. `world/WorldPage.tsx` imports `presence.css` and
uses one borrowed class from it. That is the whole of it.

So this is not a retune. It is a first application, and the useful thing to fix
first is the decision procedure, not the curves.

---

## 0. Two laws

The surfaces obey two, and both are code rather than description. That is the
point: a document is a *second* statement of something, and the second one
drifts. These are the first.

**Gravity — `motion.ts`.** `MotionField` is `{ gravity, travel, absorbPull }`.
`absorb` is constant acceleration from rest, `x(t) = ½at²`, and its
cubic-bezier is not an approximation but the exact quadratic. `emit` is the
time reverse: a body given precisely the escape impulse gravity spends at its
authored home. `settle` is an analytic under-damped spring. Retune the field
and every intent moves together, because they are all consequences of it.

**Light — `light.ts`.** A world is dark until someone looks at it. Pointing at
a mark makes it a source; `luminance` falls off inverse-square from it, over
**graph distance** — hops, not pixels, because the field is a graph and that is
what near means here. Light is opacity, never colour, since colour is status
and geometry is origin. With nothing acted on, every mark is at 1 and the law
changes nothing; that is the difference between a lamp and a vignette.

Two consequences worth stating, because they are otherwise argued about twice:

- **While held, autonomous physics is suspended.** A drag is `hold` — 90ms,
  linear, no easing — because the mark is not moving, you are moving it. A
  gated one-hop trial may let connected neighbours yield quasi-statically to
  that visible load, but no solver or inertia acts on the held mark. On
  release, the held mark is **still**: a settle would take it off the spot the
  person chose.
- **The camera is not matter.** Nothing about pan or zoom obeys either law.
  That disposes of panning, scrolling and zoom together, and explains why
  fit-to-view is the one exception — it moves matter into view because it was
  asked to.

And the invariant the two laws share, which is what makes the surface read as
a place rather than a screensaver:

> **Nothing moves, and nothing is lit, that a person did not cause.**

One exception, `flow`, which is the machine making you wait. An animation with
no originating act is a bug, not a flourish.

`scripts/check_field_laws.py` is the half of this that has teeth: no stylesheet
on a live surface may write a duration of its own, so the spine is the only
place a duration exists. It runs in the pre-commit hook when a live stylesheet
is staged.

---

## 1. The method

Every piece of component state is classified on two axes. The first says what
physically happens to matter on the screen. The second asks whether an
interpolated value would be readable as a claim. A change only earns motion if
the first axis says something moved *and* the second says nothing is lied about
in between.

**Axis 1 — what happens to matter**

| | | intent |
|---|---|---|
| ARRIVES | mounts, enters the frame | `emit` |
| DEPARTS | unmounts, leaves | `absorb` |
| REPLACED | same slot, new subject | `Swap` — absorb ∘ emit |
| MOVES | position changes under release | `settle` |
| CONTINUES | unbounded, indeterminate wait | `flow` |
| TRACKS | follows the pointer this frame | `hold` |
| REMAINS | nothing physical changes | **still** |

**Axis 2 — is the midpoint readable?**

If a person could stop the animation halfway and read a value that is not true,
the change does not animate, whatever axis 1 says. This is the axis that
generates most of the "still" column below, and it is derived from written
rules rather than taste.

**The five intents, as the kernel actually defines them** (`motion.ts:68`):

| intent | ms | curve |
|---|---|---|
| `emit` | 280 | gravity fall, `x(t) = ½at²` — accelerates away |
| `absorb` | 190 | its mirror — decelerates into rest, and shorter, because leaving reads faster than arriving |
| `settle` | 320 | damped oscillator |
| `flow` | 1000 | linear |
| `hold` | 90 | linear |

---

## 2. The seven rules that produce stillness

Each is a quotation from something already decided, not a new position.

1. **"Existing marks never move."** (`workingSet.ts:12`) The field must never
   re-layout under animation. An expansion emits only what is new.
2. **"Meaning is carried structurally, never decoratively."** (CLAUDE.md)
   Construction origin is geometry — filled, outlined, shelf, hollow. Geometry
   never tweens. A mark caught between filled and outlined draws an origin that
   does not exist.
3. **"Colour is for status only."** Status colour may cross-fade, but only at
   `hold` length. Long enough to rest in is long enough to read, and the
   midpoint between certified and stale is neither.
4. **"Windowed rows, fixed height, SQL-side sorting."** A row entering the
   window is not an arrival. Re-sorting is a re-query, not a rearrangement.
   Rows never fly.
5. **"Exact misses stay exact misses; search results stay candidates."** A
   changed result set is a new answer. Animating between two answers draws a
   continuity that the retrieval does not claim.
6. **"Retrieval and traversal do not call a model."** Nothing on the read plane
   is indeterminate, so `flow` is never correct there. It has exactly one
   honest use in the product, in §3.E.
7. **The theme is not a transition.** `mode` changes every colour on every
   surface at once. Tweening it makes the whole product briefly untrue. It
   snaps.

---

## 3. The map

### A — World shell (`WorldPage.tsx`, 21 states)

| state change | axis 1 | intent |
|---|---|---|
| `readerOpen` → true | ARRIVES from the right edge | `emit`, dock-right field |
| `readerOpen` → false | DEPARTS | `absorb` |
| `assertion` / `referent` change with reader open | REPLACED | `Swap` |
| `readerWidth` during drag | TRACKS | `hold` — 0ms in practice; direct |
| `readerWidth` on release | REMAINS | **still** — it is where the person put it |
| `drawer` null → value | ARRIVES | `emit` |
| `drawer` value → null | DEPARTS | `absorb` |
| `drawer` A → B | REPLACED | `Swap` |
| `notice` set / cleared | ARRIVES / DEPARTS | `emit` / `absorb` |
| `error` set | ARRIVES | `emit` |
| `demandProblem` set | ARRIVES | `emit` |
| `hovered`, `hoveredRelation` | TRACKS | `hold` |
| `namedAtRest` toggle | labels in / out | `emit` / `absorb`, at `hold` length |
| `show` filter change | marks join / leave the field | `emit` / `absorb` per mark |
| `focusedRelation` | dims the rest | `hold` cross-fade |
| `overview`, `relations`, `directory`, `demand` first load | ARRIVES | `emit`, once, as one body |
| `query` → `matches` | REPLACED | **still** — rule 5 |
| `mode` | REPLACED wholesale | **still** — rule 7 |

### B — World canvas (`WorldCanvas.tsx`)

| change | axis 1 | intent |
|---|---|---|
| expansion places new marks | ARRIVES | `emit`, **staggered outward from the anchor** |
| every mark already placed | REMAINS | **still** — rule 1, the load-bearing one |
| edge for a new expansion | ARRIVES | `emit`, drawn along its path, after its node lands |
| `drop(id)` | DEPARTS | `absorb` |
| open a binary filament into a plate | CONTINUES through a different projection | paired hand-off: release filament, `emit` plate, then bind spokes — not death + birth |
| collapse a binary plate into a filament | CONTINUES through a different projection | paired hand-off: release spokes, `absorb` plate, then extend filament — not death + birth |
| drag a mark | TRACKS | `hold` |
| drag release | REMAINS | **still** — no settle; a settle would take the mark off the spot the person chose |
| one-hop neighbours under a held mark, gated trial only | TRACKS then MOVES | direct capped axial yield, then `settle` exactly home; control remains fixed |
| hover | TRACKS | `hold` |
| selection ring | ARRIVES on the mark | `emit` on the ring; the mark itself **still** |
| construction-origin geometry | — | **still** — rule 2, always |
| status colour on rebuild | REPLACED | `hold` cross-fade — rule 3 |
| zoom, pan | TRACKS | `hold` |
| fit-to-view | MOVES | `settle` — the one global move that is honest, because it was asked for |

### C — Schema canvas (`SchemaCanvas.tsx`)

Same as B, with one difference that matters: the schema is a whole graph that
arrives at once and nobody hand-built, so a re-layout here moves nothing a
person placed. `settle` is legitimate. This is the only canvas in the product
where that is true.

### D — Tables (`RelationTable.tsx`, `FrontierTable.tsx`, `Docket.tsx`)

| change | intent |
|---|---|
| `order` change | **still** — rule 4 |
| page arrives into the window | **still** — rule 4 |
| `band`, `relation`, `resolved` filter | **still** — rule 5 |
| `problem` set | `emit` |
| first load of `roles` / `total` | `emit`, once, on the table as a whole |
| row hover | `hold` |
| a mark filling / gaining its crown after a verdict | **still** on the geometry; `emit` on the crown, which is an arriving element rather than a changed one |

### E — Construction (`ConstructionPage.tsx`, `ArtifactView.tsx`, `Obligation.tsx`)

| change | axis 1 | intent |
|---|---|---|
| `selected` obligation | REPLACED | `Swap` |
| `pass` null → id | ARRIVES | `emit` |
| `pass` id → null | DEPARTS | `absorb` |
| `pass` A → B | REPLACED | `Swap` |
| `opened` resolves | ARRIVES | `emit` |
| **`busy` true** | CONTINUES | **`flow`** — the only true flow in the product. A verdict POST is bounded but indeterminate, and it is the one place the person is waiting on something that is not a read |
| `problem`, `refused` | ARRIVES | `emit` |
| `history` gains a verdict | ARRIVES, appended | `emit` on the new row only |
| spine pass certified → stale | REPLACED | `hold` cross-fade on colour; the mark's shape **still** |
| `editing` false → true | ARRIVES | `emit` |
| `editing` true → false | DEPARTS | `absorb` |
| `unmet` text changes | REPLACED | `Swap`, at `hold` length |
| `disposition`, `cited` | TRACKS | `hold` |
| `cost` resolves | ARRIVES | `emit` |
| `filter` | REPLACED | **still** — rule 5 |

---

## 4. What the kernel is missing

Less than expected. `usePresence`, `useOutgoing`, `Swap`, `presence.css`
(`--rise`, `--dock-right`, `--fade`) and the G6 adapters all exist and all
generalise. Four gaps:

1. **The variables are never emitted on the live surfaces.** `motionCssVariables`
   is called only in `product/ProductShell.tsx:426`. Until `WorldPage` and
   `ConstructionPage` emit them, no CSS in this map can reference the spine.
   One line each; it is the whole blocker.
2. **No stagger.** An expansion places up to a ring of marks at once. They
   should arrive in radial order from the anchor, not as a flash. The kernel
   has durations and curves but no notion of a sequence.
3. **No G6 emit path in use.** `g6KeyframeMotion` exists and nothing calls it.
   Node birth and edge draw-in on the world canvas need it.
4. **No way to say "still" in code.** Every entry in the still column above is
   a decision someone will otherwise re-litigate by adding a transition that
   looks nice. A named export and a comment convention costs nothing and makes
   the absence deliberate rather than accidental.

## 5. Order of application

Cheapest first, and each step is independently visible:

1. Emit the spine variables on both live shells. Nothing changes yet.
2. Reader, drawer, notice — §3.A's `emit` / `absorb` / `Swap` rows. Pure CSS
   against `presence.css`; the largest felt gain per line in the product.
3. Construction: `busy` → `flow`, pass `Swap`, `editing`, the appended verdict
   row. This is where a person waits, so it is where motion does the most work.
4. Canvas emit + stagger. Needs the stagger primitive first.
5. Status cross-fades at `hold` length, everywhere, last — they are the easiest
   to get wrong and the least missed.

---

## 6. What was applied, and what the application changed about the map

All five steps are in. Three things the map got wrong only became visible once
it was built, and they are recorded here rather than quietly fixed, because a
map that is edited to match the code stops being able to disagree with it.

**The kernel's `Swap` never ran an absorb.** Not a gap in the map — a defect in
`usePresence.ts`. `useOutgoing` settled `mounted` in its mount effect, and
`Swap` clears its own `leaving` in an effect that reads that value; effects run
in hook order within one commit, so the cleanup always saw `false` and dropped
the outgoing copy before it had ever rendered. Every `Swap` in the product —
`GraphWorkspace`, `LogsWorkspace`, `TraversalMenu`, `WriteTimeline` — has been
a plain emit since it was written. `mounted` is now settled during render.

**The spine's pass state is geometry, not colour.** §3.E says *"spine pass
certified → stale — `hold` cross-fade on colour"*. It is not: `.spine__bar`
draws state as filled / half / dashed / struck / dotted. So rule 2 governs and
the correct treatment is **still**, not a cross-fade. The one place in the
product where status really is colour, and really can change under a person,
is `.docket__row[data-blocking]` — that is where §5.5's cross-fade went.

**`editing` is REPLACED, not ARRIVES.** §3.E lists `editing` false→true as an
arrival and true→false as a departure. In `AdmissionCard` the form and the
actions row are one slot with two subjects; treating them as an arrival beside
a departure doubles the card's height for the length of the change. It is a
`Swap`.

### Where each thing lives

| step | where |
|---|---|
| spine variables | `WorldPage.tsx`'s `style`, `ConstructionPage.tsx`'s root |
| reader subject | `Swap` on `readerSubject`, inside `.node-reader` |
| tables subject | `Swap` on `tableSubject`, the TABLES dock's body |
| notice | `usePresence` + `useHeld`, `motion-layer--rise` |
| canvas stagger | `staggerWaves` in `motion.ts`, driven by `canvasMotion.ts` |
| `busy` → `flow` | `construction/Waiting.tsx` |
| appended verdict | `useArrivals` + `.motion-emit` |
| pass / obligation | two `Swap`s in `ConstructionPage.tsx` |
| status cross-fade | `.docket__row`, `hold` length |
| **still** | `still()` + `STILL_RULES` in `motion.ts`, `[data-still]` in `presence.css` |

`still()` writes `data-still="<rule>"` and `presence.css` turns that into
`transition: none` on the element. The citation is therefore load-bearing: a
transition added to a marked element is overridden rather than silently
winning, so the attribute has to be removed to make the thing move. It is on
the table rows (`rowsNeverFly`), the finder's results (`answersDoNotTween`) and
the two origin marks (`meaningIsStructural`).

### Still open

- §3.B's *unpinned neighbours during a local relax* — there is no local relax.
- §3.C's `settle` on the schema canvas — waiting on a layout decision.
- §3.A's `namedAtRest` and `show` per-mark emit/absorb.
