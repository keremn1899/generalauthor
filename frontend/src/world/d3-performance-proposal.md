# Proposal: use D3 efficiently in the front end

Status: the World live-field portion is implemented; renderer migration and
the currently unrouted legacy `FieldPage` remain proposals. This is based on
[the Opus performance report](./performance.md) and measurements of the actual
`drift.ts` tuning.

## Implemented in the World lab

The live World field follows the efficient split this proposal recommends, and
it is deliberately narrower than a general force layout. Its unit is a
**session of physics**: a press, a drag, a release, and a settle.

**Press frees everything and fixes one thing.** Every standing mark becomes a
free body at the start of every session — no mark carries a pin from an earlier
one, none is exempt from collision, and the same forces apply to all of them.
The exception is the mark under the pointer, which is fixed to the pointer.
Positions are re-read from the renderer at that moment, which is the one moment
nothing else is moving them; that is what keeps the solver's picture and the
drawn picture from diverging over a long sitting.

**A hold runs at constant energy.** `holdEnergy` is both the alpha and the alpha
target, so the field is as lively on the fifth second of a drag as on the first,
with no decay schedule under the hand.

**Release settles; it does not pause.** The alpha target drops to zero and the
decay is *solved from* `settleMs`, so the tail is a duration a person can feel
rather than a rate: alpha falls from the hold energy to a rest threshold over
`settleMs / 16.7` frames and then d3's timer stops itself. Damping rises for the
tail so its last frames are momentum running out rather than motion cut. The one
thing a release may not do is move the mark just placed — it stays fixed where
the pointer left it, through the settle and through the quiet afterwards, until
the next press hands it back to the field with everything else.

**Nothing else ever starts it.** A redraw marks the body set stale; the next
press pays for the rebuild. No reheat on new matter, no timer behind a field
nobody is touching, and a field at rest costs zero.

The renderer path per tick:

- D3 owns a mutable body map; a tick passes that map directly to the canvas and
  allocates no cloned position snapshot.
- Bodies whose position moved less than a quarter-pixel are dropped before
  anything downstream sees them.
- Marks and their crowns and shelves go to the renderer in **one**
  `translateElementTo` for the whole tick, with the standing-id set resolved
  once for the batch. The previous shape — a `followFurniture` call per moved
  body — was one renderer write and one topology scan per mark.
- Incident bond plates are laid out once for the complete moved set, so an edge
  whose two ends both moved is stationed once.
- Hover, naming and other appearance-only frames neither rebuild nor start D3.

The controls are grouped in `DRIFT_TUNING` in `drift.ts` and exposed as World
Lab sliders: collision reserve, collision passes, link strength, held energy,
settle time and velocity decay.

### Measured solver cost

Node 22, seven runs, median, 60 ticks with the shipped link and collision
forces, on a spanning tree with about 1.3 links per body and every body free.
These numbers cover D3 only; G6 position updates and browser paint are separate.

| Bodies | Passes | Solver per tick |
|---:|---:|---:|
| 20 | 3 | 0.031ms |
| 100 | 2 | 0.218ms |
| 100 | 3 | 0.313ms |
| 150 | 2 | 0.412ms |
| 150 | 3 | 0.591ms |

Collision dominates, at roughly O(passes × bodies × log bodies) per tick,
because each pass traverses a spatial index over every body — including any
fixed one, which is what makes it a collider rather than an exemption. Three
passes cost about 45% more than two at 150 bodies, and that is the right place
to spend: a pass that leaves marks overlapping has not done the only job
collision has.

The solver is the smaller half of a frame either way. The renderer writes that
follow every moved mark are the larger half, which is why the per-tick path
above is one batched write rather than one per body.

## Recommendation

Keep D3 as a headless layout engine and keep G6 as the World renderer. D3-force
does not need to own SVG or Canvas rendering; its most efficient role here is
to mutate simulation positions, while one frame scheduler publishes those
positions to the renderer. The expensive path identified by Opus is G6's
field-wide animated structural draw, not the force calculation itself.

The highest-value optimization is therefore:

1. Let the simulation keep mutable nodes in a ref.
2. Do not clone every node on every D3 tick.
3. Coalesce simulation ticks into at most one UI publication per
   `requestAnimationFrame`.
4. Keep hover, light, labels, drag-following, and spread on direct restyle/
   element-update paths; reserve structural G6 draws for actual topology or
   lifecycle changes.

## What the current measurements imply

The report measured roughly 70 G6 elements for 19 marks. The important costs
were:

- appearance-only restyle: about 0.2ms per changed element, with no fixed floor;
- animated structural draw: about 110ms plus roughly 2.5ms per field element;
- React `data` memo rebuild: about 36ms at 70 elements;
- `planSpread`: quadratic in one selected mark's neighbour count, but with a
  small bounded input;
- `relax.ts`: a few milliseconds, once per expansion, outside the renderer.

This means reducing D3 tick frequency alone will not solve the measured G6
cliff. A tick must not trigger `setData`/`draw`, and a hover must not rebuild
the entire renderer data model.

## Proposed D3 integration

### 1. Keep simulation state mutable and private

`d3-force` mutates the node objects it owns. Store those objects in the solver,
and expose either the simulation's node array or a small position snapshot only
when the view needs one. Avoid this current hot-path shape:

```ts
onTick(simNodes.map((node) => ({ ...node })));
```

For the legacy React Flow implementation, prefer a ref-backed pending flag and
read `x`, `y`, `vx`, and `vy` when the scheduled frame is published. If React
state is still needed by React Flow,
build one `Map<id, position>` per published frame and update both consumers
from that same snapshot; do not build a map once for each consumer.

### 2. Publish at the display rate, not the simulation rate

The simulation may tick more often than the browser can paint. Use one
`requestAnimationFrame` callback to coalesce ticks:

```ts
let framePending = false;

simulation.on("tick", () => {
  if (framePending) return;
  framePending = true;
  requestAnimationFrame(() => {
    framePending = false;
    publishPositions(simulation.nodes());
  });
});
```

For the World renderer, `publishPositions` should update only the elements
whose positions changed and should not call `graph.draw()` for appearance-only
work. For React Flow, it should be the only per-frame state publication.

If React becomes the bottleneck, keep the simulation and the mutable position
buffer outside React entirely, and use React state only for settled positions,
selection, and structural changes.

### 3. Reheat only for real causes

Create forces once. Call `simulation.nodes(...)` and replace link force links
only when the node/link topology changes; both operations reinitialize force
internals. For dragging, use `fx`/`fy`, update the dragged node directly, and
use `alphaTarget` plus `restart()` while the drag is active.

D3's own drag example drops the target at drag end and lets the simulation cool
naturally. The World field does not, and the difference is a product decision
rather than a performance one: a cooling tail keeps solving after the person
has let go, which means the mark can come to rest somewhere other than where
they put it. Here release stops the target and solves the decay
from a settle time instead, so the tail is short, bounded and felt as a
duration — and the released mark is held out of it.

Do not reheat for hover, label expansion, light changes, or a spread restyle.
Those are renderer appearance changes and should remain on the cheap direct
update path measured by Opus.

### 4. Tune forces for the actual graph

The many-body force already uses a Barnes–Hut quadtree. Set a finite
`distanceMax` when distant nodes do not need to influence one another; this is
the most direct force-level reduction for a local field. Keep strength and
radius accessors stable, since D3 caches them until the force is reinitialized.

Use the collision force only where overlap prevention is needed. Avoid adding
duplicate proximity forces or repeatedly rebuilding quadtrees in application
code. For nearby interaction/picking, use a quadtree or the renderer's spatial
index rather than scanning every mark.

Alpha schedules are worth costing in ticks — a decay of `d` runs about
`ceil(log(alphaMin) / log(1 - d))` of them, which is how a settling tail turns
into hundreds of ticks nobody asked for. The World field inverts the question:
constant alpha while held, and on release a decay solved backwards from the
settle time it wants.

### 5. Move static or large solves off the main thread

For a settled layout, call `simulation.stop()` and run a bounded number of
manual `tick()` calls. For larger graphs, move that solve to a Web Worker and
send back compact position buffers. The main thread should then perform one
structural placement/update, not receive hundreds of React updates.

The worker path is most useful for initial layout and large expansions. It is
not the first fix for the current small World field, where G6's draw floor is
the dominant measured cost.

### 6. Preserve the G6 rendering split

Use G6 partial data updates only for elements whose identity or structural data
changed. Keep the existing direct restyle path for hover and selection. If the
field eventually exceeds the current renderer's budget, benchmark G6 WebGL or
a hybrid Canvas/WebGL layer, but treat labels and pointer hit areas as a
separate requirement; moving the renderer does not automatically make text
interaction cheap.

## Implementation phases if the field grows

**Phase 0 — instrumentation.** Separate D3 force time, snapshot construction,
React commit time, and G6 paint/draw time. Track ticks per interaction,
published frames, changed elements, and long tasks.

**Phase 1 — low-risk hot-path reduction.** Remove per-tick node cloning,
coalesce ticks with one `requestAnimationFrame`, and share one position map
between consumers. Keep the existing force semantics and visual tuning.

**Phase 2 — scale only if measurements require it.** Cache adjacency/BFS
results, split the data memo into stable structure plus appearance overlays,
use finite many-body distance, and move static solves to a worker. Add viewport
culling or relation aggregation only when the visible element count is the
limiting factor.

**Phase 3 — renderer benchmark.** Compare current G6 Canvas with G6 WebGL or a
hybrid renderer using the same interaction contract. Promote a renderer change
only if it improves measured structural draws without regressing labels,
selection, edge expansion, or accessibility.

## Guardrails and acceptance criteria

- No hover or label expansion may call a field-wide animated draw.
- A D3 tick may publish at most once per animation frame.
- The solver runs only from a press until its settle ends; nothing else may
  start it.
- A released mark stays exactly where it was released, through the settle and
  until the next press, at every tuning.
- Every mark is a free body at the start of every session, and every mark
  collides.
- Topology changes may reinitialize forces; appearance changes may not.
- Selected-node spread must remain visible while an unrelated node moves.
- A selected node's labels remain named when the pointer leaves it.
- The count label must be a hit target while visible and open its assertion list.
- Any optimization must be checked against long tasks and interaction latency,
  not only total simulation time.

## References

- [D3 force simulation API](https://d3js.org/d3-force/simulation)
- [D3 many-body force and Barnes–Hut tuning](https://d3js.org/d3-force/many-body)
- [D3 quadtree](https://d3js.org/d3-quadtree)
- [G6 data update API](https://g6.antv.antgroup.com/en/api/data)
- [G6 renderer options](https://g6.antv.antgroup.com/en/manual/further-reading/renderer)
- [G6 layout and worker/GPU options](https://g6.antv.antgroup.com/en/manual/layout/overview)
