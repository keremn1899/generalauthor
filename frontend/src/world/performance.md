# How the World canvas scales, and what to target next

Measured on `#/world-lab`, Chrome, a real compiled world, September 2026. Every
number here came from the running surface rather than from reading the code —
where a figure is an estimate it says so.

The unit throughout is **elements**: one G6 node or edge. A field of 19 marks
carries about 70 elements once furniture, plates, spokes and bundles are
counted, so element count runs roughly 3–4× the mark count a reader would
describe. Numbers below are quoted against elements for that reason.

---

## The short version

| Path | Scales with | Shape | Cost |
|---|---|---|---|
| Hover / naming / light | elements **changed** | linear, no floor | ~0.2ms each |
| Birth / death / arrangement | **all** elements on the field | linear + fixed floor | ~110ms + ~2.5ms each |
| Plain redraw, no animation | all elements | linear | ~0.2ms each |
| React `data` memo | all elements | linear | ~36ms at 70 |
| `hopsFrom` BFS | marks + bonds | linear | small |
| `planSpread` | (selected mark's named neighbours)² | **quadratic**, tiny input | negligible |
| `relax.ts` settle | bodies × ticks | ~linearithmic, once | a few ms |
| Read plane (`:8139`) | relations, not world size | flat | 2–8ms/route |

Nothing here is exponential. The one quadratic term is bounded by a single
mark's degree and never by the field.

---

## The floor is the thing

The single most important fact about this surface's performance is that
**G6 charges for animation per element on the whole field, whether or not that
element changed.**

Measured on a live 70-element field, median of five, identical data each time:

| Elements actually changed | Cost |
|---|---|
| 0 (byte-identical frame) | 190ms |
| 2 | 181ms |
| 6 | 174ms |
| 70 (everything) | 171ms |

It is flat. `setData` itself is 3–5ms; a draw with no animation declared is
23ms. The remaining ~160ms is Web Animations set-up, and it is spent whether
there is anything to animate or not.

It is also flat in the *number of fields* declared — one animated field costs
the same as eight (131ms either way), so trimming the field lists in
`canvasMotion.ts` buys nothing. What it scales with is elements × declared
blocks:

| Elements | Animated draw | Plain draw |
|---|---|---|
| 26 | 97ms | 7ms |
| 56 | 151ms | 16ms |
| 86 | 210ms | 22ms |
| 116 | 311ms | 22ms |
| 176 | 455ms | 41ms |
| 236 | 605ms | 36ms |

Linear, ~2.5ms per element, on a fixed floor of roughly 110ms. That floor is
why a field of 25 marks felt like a cliff: every hover paid it.

## Why hover no longer pays it

`restyleCanvasData` in `canvasMotion.ts` takes any frame that changes only how
standing marks *look* — no births, no deaths, nothing moved — and applies it by
writing to the elements directly, with no `setData` and no `graph.draw()`.

| | Before | After |
|---|---|---|
| `setData` / `draw` per hover | 1 / 1 | **0 / 0** |
| Long tasks over 8 hovers | 16 | **0** |
| Blocked main thread per hover | 176ms | **0ms** |

Its worst case — restyling every element on the field — measures 7ms at 26
elements and 46ms at 236: **~0.2ms per element with no floor**, against
97–605ms for the same work through a draw. A real hover changes a fraction of
that.

The drag path already worked this way (`followFurniture` writes
`parsedAttributes` and calls `onframe`), which is why dragging never showed the
problem: 40 pointer moves, zero long tasks.

---

## The remaining terms, in the order they will bite

**1. Structural draws — linear, ~110ms floor + ~2.5ms/element.** Births,
deaths and arrangements still go through `transitionCanvasData`. A death is two
sequential stages (constraints release, then the mass collapses), so it pays
the floor twice. This is now the dominant cost on the surface.

*If we need to target it:* declare update animations only for the elements
actually entering or leaving, rather than field-wide `node`/`edge` blocks. The
staging in `transitionCanvasData` is a design rule and should survive; what
should not is that a two-mark death sets up animations for two hundred
elements.

**2. The `data` memo — linear, ~36ms at 70 elements.** It rebuilds every node
and edge on every hover, because `hovered`, `incident` and `namedMarks` are in
its dependencies. Harmless while the draw cost dwarfed it; it is now the
largest remaining per-hover term.

*If we need to target it:* split the memo so light and naming are applied over
a cached set of built marks rather than rebuilt into them.

**3. `hopsFrom` — linear in marks + bonds, per hover.** `fieldGraph` rebuilds
the adjacency map and runs a BFS on every hover. The comment in `hops.ts` says
this is cheaper than remembering the answer, which was true at a few dozen
marks. It is a memo away from free if that stops being true.

**4. `planSpread` — quadratic in one mark's degree.** 48 relaxation passes over
every adjacent pair, so O(48·k²) where k is the number of *named* neighbour
groups on the selected mark. k is a handful — the largest mark in the test
world has 9 — and this runs on selection only, never on hover. Only worth
looking at if a mark with fifty named neighbours ever becomes normal.

**5. `relax.ts` — once per expansion, no renderer attached.** Bodies × fixed
tick count, with collision on a quadtree. Milliseconds, and it does not tick
while anyone is looking.

**6. `drift.ts` — lab only, off by default.** Same per-tick cost as `relax`,
but ticking until alpha decays. Writes positions through the cheap path, never
`setData`.

**7. The read plane is not involved.** Every route measured 2–8ms and none of
them is in the hover path at all: `overview` 8ms, `schema` 8ms, `referent` 5ms,
`expand` 5ms. `referent()` runs one counting query per relation — linear in
relations (20), independent of world size. If the front end feels slow, the
backend is not why.

---

## How to re-measure

The A/B that produced the table above, run in the page console: patch
`graph.setData` and `graph.draw` to time themselves, install a `longtask`
`PerformanceObserver`, then drive hovers with
`graph.emit('node:pointerenter', { target: { id } })`. Synthetic `PointerEvent`s
dispatched at the canvas do **not** reach G6's picking and will silently
measure nothing.

Two traps worth naming, both of which cost an hour here:

- Leaving `graph.setOptions({ animation: false })` behind from a previous
  experiment makes everything afterwards look fast.
- Diffing a frame against `graph.getNodeData()` is not the same as diffing it
  against what the canvas authored: G6 writes its own `zIndex` into every
  stored datum during a draw.

---

## Re-measured at 376 elements, September 2026

The table above was taken on a 70-element field. Driving `#/world-lab` against
`bomS100` up to **127 marks / 376 elements** — roughly five times the original
field — says which of the "remaining terms" actually bit and which did not.

### The restyle lane held; the restyle itself did not stay free

| | 70 elements | 334 | 376 |
|---|---|---|---|
| `setData` / `draw` per hover | 0 / 0 | **0 / 0** | **0 / 0** |
| Frame gap, median | ~17ms | 16.7ms | 27.2ms |
| Frame gap, p90 | — | 57.3ms | 99.2ms |
| Stalls over one frame | — | 30 of 30 hovers | 33 of 93 frames |

Architecturally nothing regressed: five times the field and still not one
`setData` and not one `draw` on the hover path. What grew is the restyle's own
linear term. At ~0.2ms per element it was invisible at 70 and is a dropped
frame at 376.

### Where it goes, and it is not our code

A CPU profile over ten hovers, by self time:

```text
455ms  internalUpdateElement   @antv/g
354ms  syncHierarchy           @antv/g
278ms  render                  @antv/g
218ms  tick2                   @antv/g
  9ms  WorldCanvas.tsx
  8ms  filaments.ts
```

The `data` memo — named in §2 above as the next term to bite — does not appear
in the profile at all. Neither does `hopsFrom`. The cost is G's scene graph
propagating attribute writes, and it is therefore a function of **how many
elements we ask it to write**, nothing else.

### How many elements we ask it to write

Per hover, on a 376-element field: **279 elements rewritten, 74% of the
field.** Light with a 1.6-hop falloff on a densely connected field reaches
almost everything, so nearly every hover is the restyle's worst case.

Of those 279, between 21% and 51% change by **less than one 8-bit opacity
step** — a write the display cannot show. On the sparser 334-element field it
was 130 of 256 elements, over half.

*If we need to target it,* in order of leverage:

1. **Quantise the lit value.** `styleDelta` compares with `Object.is`, so a
   reflection differing in the fourth decimal counts as a change. Snapping
   `reflected` to a 1/255 grid drops those writes at the source and costs
   nothing visible, because it is below what the screen can draw.
2. **Cut the falloff off.** Past some hop count the reflection is under a
   step anyway; not emitting it at all keeps whole neighbourhoods out of the
   restyle set rather than out of one channel of it.

Both shrink the *set*, which is the only term left. Neither touches the law:
what is lit and how brightly is unchanged; what stops is writing differences
nobody can see.

### Dragging is still the cheap path

60 drag ticks on the highest-degree mark on the field (38 incident edges, 337
elements): median frame gap **17.1ms**, p90 26.6ms, four dropped frames in 130,
zero `setData`, zero `draw`. `relayoutIncidentLabels` is bounded by one mark's
degree and does not scan the field.

The rim-aware station added in the same pass costs 0.02ms per full pass over
63 spokes — `measureText` on a relation name, and it does not register.

## The label fade, put back on the cheap lane

The restyle lane bought its speed by not drawing, and G6's update animation is
a property of a draw — so taking the lane silently dropped the one transition
this surface changes most often: a name arriving or leaving as the pointer
moves. Names cut in and out.

They fade again, and not by giving the draw back. `fadeLabel` in
`canvasMotion.ts` asks the label shape itself for the animation, so the cost is
one `shape.animate()` per label whose opacity actually changed, rather than one
animation per element on the field whether it changed or not.

| | Through a draw | Through the shape |
|---|---|---|
| Animations built per hover | one per element (236) | one per changed label |
| Floor | ~110ms | none |

A running fade is cancelled and resumed from what the eye is currently seeing
(`liveOpacity` reads the shape *before* `update` writes the destination), so a
pointer crossing several marks in a second produces a continuous opacity, not a
sequence of snaps back to the last settled frame.

Two things about G6's label that this had to learn the hard way, both of which
only show up when a fade is *interrupted*:

- A label is a composite — a text and the plate behind it — and animating the
  composite's opacity cascades to both only while it runs. Cancel it and the
  text is re-driven while the plate is abandoned wherever the cancelled
  animation left it. What stayed on the field was a background-coloured
  rectangle lying across the filament: a gap in a stroke that was whole
  underneath, cleared only by the next full draw. Each part is driven
  explicitly now.
- While an animation stands on a part, reading its opacity back gives the
  animated value, not the destination — so a fade that asked the shape where it
  had just been sent was told "where you already are" and declined to move. The
  destination comes from the frame's delta (`partDestination`); only the
  starting value comes from the shape, because that is the one the eye is
  actually looking at.
