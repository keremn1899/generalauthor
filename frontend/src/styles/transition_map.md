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
| drag a mark | TRACKS | `hold` |
| drag release | REMAINS | **still** — no settle; a settle would take the mark off the spot the person chose |
| unpinned neighbours during a local relax | MOVES | `settle` (see the layout note) |
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
