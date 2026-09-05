# Causal material field — trial constitution

Status: trial. The shipping World canvas remains the control until the lab
comparisons below are adjudicated.

The trial runs inside the real World surface. The lab may tune canvas
expression, but `WorldPage` continues to own API data, field memory, tables,
search, selection, expansion, folding and removal. A reduced fixture sandbox
is not an acceptable proxy for judging interaction laws.

## Aim

The canvas should feel like a small coherent world, not like a diagram with
decorative easing. Its character comes from stable laws:

```text
cause -> load or impulse -> local response -> dissipation -> rest
```

Universe-inspired means lawful, causal and continuous. It does not mean a
space skin, idle wandering, stars, nebulae or ornamental orbit.

## Constitution

- **Matter** is a referent disc or assertion plate.
- **Constraints** are filaments and spokes. They may communicate connection,
  never an unsupported relation strength or direction.
- **The field** carries light, collision and bounded propagation.
- **The observer** is the pointer, selection and camera. Selection belongs to
  the observer. It may temporarily change a body's optical presentation, but
  must not overwrite its semantic geometry or construction origin.
- Rest is the default. Nothing moves without a visible cause.
- A mark may respond to a local cause, but its authored rest position is
  conserved. A directly manipulated mark may acquire a new authored rest.
- Restored matter does not replay arrival. Filtered matter is occluded, not
  destroyed, and does not replay arrival when restored.
- Construction origin remains geometry. Motion cannot tween one origin into
  another or use hollowing as a durable semantic state.
- Persistent motion requires a persistent visible state. Selection
  circulation may persist while selection persists; it stops when selection
  ends. Reduced motion leaves a stationary segmented mark.
- The camera is a reference frame, not matter. Pan and zoom do not impart
  force to the field.

## Contact and selection

Contact is a viscoelastic load. The interaction state machine is:

```text
idle -> pressed -> releasing -> idle
                \-> dragging -> releasing -> idle
```

- Pointer-down compresses a body. The initial trial uses 96% of its resting
  size and the shared `hold` plan.
- Pointer-up removes the load with the `settle` curve compressed to the shared
  `hold` duration. The small contact deformation must not delay selection by
  a full positional spring.
- A click commits selection only after release. Selection must never appear on
  pointer-down.
- Crossing the drag threshold changes contact into manipulation. Drag release
  does not manufacture selection.
- Pointer cancellation releases the load without selection.
- An existing selection pauses its circulation while its matter is held.
- Keyboard or table selection has no invented contact phase; its observer
  field binds directly.

## Selection comparison

The lab retains all three treatments against the same shipping component.
Hollow is now the leading trial, while the shipped outer ring remains the
reversible control:

1. **Hollow aperture (leading trial).** On committed selection, the disc's
   material evacuates optically into its boundary and the ants occupy that
   boundary. The body has not been removed: its stable geometry, name and
   incident constraints remain. Deselection condenses the fill back. This is
   an observer aperture into matter, not a deletion or a semantic hollow.
2. **Outer field (control).** The existing ants stand off a filled disc. It is
   retained unchanged until the aperture reading survives use in the full
   surface.
3. **Excited boundary (alternate).** The disc remains filled and the ants run
   on its material boundary.

Filled assertion plates also use the aperture, preserving their label, shelf
and crown. Their ants remain the plate border; filaments keep line selection.

Hover lifts resting material toward full opacity with the shared light law.
Labels retain their text while opacity transitions over `hold`; invisible
labels do not intercept pointer input.

Canvas find searches visible referents, assertions and demands in the working
field. An empty field uses the directory to choose its first seed. A populated
field never silently expands through find. Broader discovery belongs in tables.

## Arrival and withdrawal

Arrival means admission to the observer's working field, not semantic
creation. A body nucleates at its final authored position, becomes legible,
then its constraints bind no earlier than one shared `hold` after it. Expansion
groups propagate in graph-distance waves from the requested anchor. The lab's
speed control stretches the nucleation, binding interval and wave window
together; it never changes their causal order.

Withdrawal means leaving observation, not destruction of the World entity:

```text
observer field releases -> constraints release -> body contracts -> remnant leaves
```

Filtering is occlusion: retained bodies fade at full size and return at that
same size and authored position. Only removal from the working set contracts
mass. The two cases share the serialized lifecycle lane.

Constraint release completes before body contraction begins. A new data frame
may arrive during either phase, but the serialized canvas lane finishes the
current physical episode and then reconciles to the newest waiting state; it
never overlaps two global scene mutations.

Folding a binary filament into a plate is neither birth nor death. It should
eventually conserve one assertion's identity while its projection changes.

## Open comparison — grouped labels and explicit arrangement

For multiple assertions sharing a filament, trial one compact assertion count
at rest, expanding the individual labels on hover or focus. The count must not
masquerade as one representative assertion, and touch needs a persistent
expand action. Keep every assertion independently selectable. This comparison
is pending; current individual labels now fade without replacing their text.

Expansion continues to place new matter in free slots around its requested
subject and pin existing matter during the one-shot relaxation. Its geometry
communicates proximity to the request, not semantic cause or hierarchy.

The next layout comparison should be an explicit **arrange around selection**
action: one-hop referents around the chosen subject, assertion plates between
their participants, and unrelated components kept separate. A second useful
action is **separate overlaps**, conserving positions as far as possible. Both
need a preview/undo story before implementation because arrangement is authored
work. Directed layouts belong specifically to a derivation view, where causal
direction is actually known. These proposals do not enable automatic relayout.

## Physics decision — a local elastic episode, not a live layout

### What the earlier trials established

The repository contains three different things that were all once called
physics. They should not be revived as though they were one unfinished system:

- `field/physics/useForceLayout.ts` and `forceConfig.ts` are a global fluid.
  Charge, centring, a slow alpha decay and reheating after structural changes
  deliberately keep the whole field breathing. That is incompatible with
  authored rests, local causality and spatial memory.
- `explorations/lab/G6SeedLabPage.tsx` proved that a renderer-owned live
  simulation also creates a second lifecycle authority. Birth, death and drag
  needed a membership refresh, a mutation mutex and drag-deferred removal to
  avoid orphaned hot simulations and missing-node tick floods. Those fixes are
  useful evidence, not a reason to bring that ownership problem into World.
- `explorations/lab/G6LensLabPage.tsx` found the sound physical ingredient:
  uniform links plus stronger springs to captured homes, with no charge or
  centre and an alpha target of zero. But it applies to the whole graph and
  pulls the manipulated mark back to its old anchor. World says that a direct
  drag authors a new rest, so the useful ingredient has to be bounded more
  tightly.

World already has the placement solver it needs. `world/relax.ts` runs
headlessly to convergence once, with old matter pinned, to clear newly arrived
matter. It is deterministic and produces positions, not animation. Interaction
physics must not replace it, re-run it on drag, or introduce another layout.

### Why have interaction physics at all

Pleasantness is not enough to justify motion. A local yield earns its place if
it makes three true properties of the field perceptible:

1. **Constraint topology.** Moving one body loads only the filaments and
   spokes incident to it. A yielding endpoint confirms which visible
   connection is mechanically local without suggesting that the rest of the
   World was disturbed.
2. **Authored rest.** A neighbour can deflect under a visible load and return
   exactly home. The contrast makes the directly manipulated body's new rest
   legible as an authored change rather than layout drift.
3. **Occupied space.** Yield stops at contact instead of pushing unrelated
   matter away. A crowded pocket therefore feels stiff while the arrangement
   remains conserved.

The response does **not** encode semantic strength, confidence, causality,
direction or cardinality. Every eligible constraint has the same mechanical
compliance. Graph topology determines *where* a response may occur, never
*what the relation means*.

### Physical analogy and response law

The challenger is a small elastic linkage mounted to a substrate. Every body
has an authored home. A held body is kinematic — the pointer positions it
directly — while each directly connected body has a compliant mount to its
home. Filaments transmit axial strain like pin-jointed links: pulling or
compressing along a link can yield its other endpoint; moving across a link
mostly changes the link's angle and does not make the endpoint follow sideways.

At drag start, capture the held body's home, every eligible one-hop body's
home, and the rest axis of each incident constraint. Deduplicate parallel
constraints by endpoint: two assertions over the same pair must not imply a
stronger physical relation. For held displacement
`d`, rest-axis unit vector `a`, uniform coupling `k`, and cap `c`, the first
trial target is:

```text
axial strain        s = dot(d, a)
neighbour deflection  = a * clamp(k * s, -c, c)
```

Use one shared `k`; begin with `c = 8` graph pixels inside the already agreed
6–12 pixel trial range. If that target would intersect standing matter, reduce
the deflection along the same axis until it clears. Do not resolve contact by
pushing a second-hop or unrelated body. Degenerate zero-length constraints do
not yield.

This is a quasi-static response while held, not a numerical simulation:

- compute only the held body's incident material endpoints, `O(degree)`, once
  per animation frame;
- write the held body exactly under the pointer and transient neighbour poses
  directly to G6; do not publish transient neighbours to React state or field
  memory;
- decorations travel with their owning body and edges restroke from their live
  endpoints;
- on release, the held body's last valid position becomes its new authored
  rest, while yielded neighbours use the shared `settle` plan to return to the
  homes captured at drag start;
- on pointer cancellation, keep the held body at its last valid direct pose —
  the input stream ended, but the field must not invent a jump — and return
  only the yielded neighbours;
- after settling, snap neighbour coordinates exactly to their captured homes
  and end the episode. No timer, alpha or simulation survives at rest.

Reduced motion retains direct manipulation and disables neighbour yield. It is
the control response rather than a shortened autonomous settle.

### Ownership and concurrency gate

Implement this, if the comparison is approved, as a small pure
`localYield.ts` response function plus an episode owned by `WorldCanvas` — not
as a d3 layout and not as a G6 force behaviour. The existing serialized canvas
lane remains the single structural lifecycle authority:

- data frames received during drag or neighbour return are coalesced to the
  newest frame and drawn after the episode;
- disappearance of an eligible neighbour simply removes it from the episode;
- a transient neighbour pose never becomes a `WorkingSet.positions` value;
- the episode restores its transient writes before a queued structural draw;
- no per-frame `graph.draw()`, layout restart or React position update is
  allowed.

The full World lab must retain a named **fixed-neighbour control** beside a
named **local axial yield** challenger. Do not add raw force, alpha or damping
knobs: they would reopen models this decision has already rejected. The only
useful comparison controls are response off/on and, if perception demands it,
the bounded displacement cap.

The challenger may proceed only when an automated or instrumented stress run
shows all of the following:

- only one-hop material endpoints move, by no more than the configured cap;
- every yielded endpoint returns within 0.25 graph pixels of its exact home;
- the held body has no additional pointer lag and keeps its released position;
- no transient neighbour coordinate is persisted;
- selection ants, connected labels and furniture follow live geometry;
- expand, retract, fold, delete and a new drag arriving during an episode
  reconcile to the newest requested state without a stuck pose;
- reduced motion, touch cancellation and the 150-mark field preserve the same
  interaction distinctions.

Until that gate passes, fixed neighbours remain the product behaviour.

## Projection decision — conserve the assertion through fold and unfold

A binary assertion has one semantic identity and two drawings. Today G6 must
name those drawings differently — node `<assertion id>` and edge
`bond:<assertion id>` — so the generic canvas diff reports a death and a birth.
That renderer fact is not the event. Folding is an observer changing the
projection of matter already present:

```text
filament <-> assertion carrier <-> plate and spokes
```

Before generic lifecycle classification, pair these changes by semantic key:

- `bond:X` departing while node `X` and its spokes arrive is **open X**;
- node `X` and its spokes departing while `bond:X` arrives is **collapse X**.

Remove paired elements from the ordinary birth/death sets and give the pair
one projection episode. `markOfElement` already supplies the required
element-to-assertion identity mapping; the classifier should make that mapping
explicit rather than infer it from timing.

### The carrier and the hand-off

Geometry must not tween through a false construction origin, so this is a
hand-off rather than a line-to-rectangle morph. A temporary, non-interactive
carrier preserves the assertion's relation label and selection identity while
G6 changes element type:

**Open:**

1. Capture the filament label station and the plate's authored destination.
2. The filament releases into the carrier; the carrier may travel between
   those stations with `settle` when collision made `plateAt` choose a nearby
   clear position.
3. Admit the plate around the carrier with `emit`.
4. Bind its spokes no earlier than one shared `hold` after the plate is
   materially present.

**Collapse:**

1. Release the spokes while the plate and carrier still stand.
2. Withdraw the plate boundary into the carrier with `absorb`.
3. If needed, carry the assertion label to the new filament station.
4. Extend the filament from that carrier only after the plate has ceased to be
   the active projection.

At every intermediate frame there is one readable assertion label and never
both complete projections. The carrier is renderer scaffolding, not a third
semantic mark, and is never stored in the working set.

Logical selection remains `{ kind: "assertion", id: X }` throughout. Visual
ants transfer from the source path to the carrier boundary and then to the
destination path; the reader stays open on the same assertion. A carrier is
not a hit target. A second fold request, deletion or data frame is coalesced by
the same serialized canvas lane and reconciled after the current hand-off, so
an interrupted projection cannot orphan its selection or leave both forms.

Reduced motion performs the same paired classification and swaps projections
atomically with selection preserved. It must not fall back to generic death
and birth.

Projection motion may proceed after the classifier is covered by pure tests
for open, collapse, ordinary birth/death and rapid reversal, and a rendered
trial establishes:

- one assertion identity and one readable label at every frame;
- no ordinary node nucleation/collapse for a projection change;
- constraints bind only to a materially present projection;
- final G6 node/edge ids exactly match the requested data;
- selection and reader continuity survive open, collapse and reversal;
- the serialized lane remains the only authority over structural mutations.

## Acceptance

- Press, click, drag, selection, arrival and withdrawal read as different acts
  without explanatory copy.
- Drag never accidentally selects; cancel never selects.
- Semantic geometry remains readable at every intermediate frame.
- Nothing changes position without an evident local cause.
- Any neighbour displacement is capped and reversible.
- Projection changes preserve one assertion identity and never read as
  destruction followed by creation.
- Interrupted or reversed animations leave no stuck compression or orphaned
  selection field.
- Interaction-driven canvas updates are serialized; a frame received during
  drag is applied after release rather than discarded.
- Touch, keyboard and reduced-motion paths retain the same state distinctions.
- The 150-mark field limit remains responsive.
