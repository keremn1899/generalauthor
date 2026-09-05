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
  `hold` duration. It is compressed because the load was small, not to get out
  of anything's way.
- A click commits selection only after release. Selection must never appear on
  pointer-down.
- Release is not a phase anything else waits on. A pointer that is down owns
  the field, so `pressed` and `dragging` hold the canvas draw lane; `releasing`
  does not. The pointer is already up by then and what is still running is one
  body relaxing a load on its own two shapes — a transform the renderer leaves
  alone across a redraw. Serializing the observer's aperture behind the body's
  viscoelastic return made one act answer at the speed of the slower of two
  unrelated causes.
- Crossing the drag threshold changes contact into manipulation. Drag release
  does not manufacture selection.
- Pointer cancellation releases the load without selection.
- An existing selection pauses its circulation while its matter is held.
- Keyboard or table selection has no invented contact phase; its observer
  field binds directly.

### The observer's cache is a copy, and never writes back

Where a mark *is* has two accounts during a gesture, and they disagree by
design. The store holds where the person last put it; the renderer's live cache
holds where the pointer has it now. The cache is ahead of the store for the
length of the drag and behind it at every other moment, and one rule keeps that
from becoming corruption:

- **The cache is a copy, never the store's own map.** Aliasing them makes every
  drag tick an unannounced write into `WorkingSet.positions` — no `onPositions`,
  no new map, so nothing downstream can see it happened, and any comparison of
  the set against its own previous positions is a map compared with itself. The
  same law the unbuilt physics gate below states as *a transient neighbour pose
  never becomes a `WorkingSet.positions` value* applies first to the drag that
  already exists.
- **A place that cannot be read is not a place.** A renderer answering
  `[null, null]` for an element whose transform will not resolve is saying it
  does not know, and rounding that produces `NaN` — a position nothing can draw,
  hit-test or lay out from, written over the good copy and kept across reloads.
  It is refused at the harvest and again at the read, so a store that already
  holds one heals instead of staying broken.
- **A frame held out for a gesture is restated before it is drawn.** A frame
  built mid-drag — a filter toggled with the other hand — carries the position
  the mark had when it was built. Flushed as-is on release it puts the mark
  back there and the next frame corrects it: a yank and a return, for a change
  that was never about position. Only the dragged mark and its furniture can be
  stale, so only those are restated, from the cache the harvest has just made
  authoritative.

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

Hover lifts resting material toward full opacity with the shared light law,
over `hold`. Labels retain their text while opacity transitions over `emit`;
invisible labels do not intercept pointer input.

Both of those are opacity, and so is occlusion, which is why every transition
stage has to name the opacity channels explicitly. The renderer's own defaults
animate position and colour and nothing else, so a stage that leaves them
unstated applies them on the next frame: light snaps instead of falling off,
and the observer's shutter cuts instead of closing.

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

## Grouped labels and the open arrangement comparison

A filament that carries several assertions has three states, not two:

```text
at rest              nothing
looked at            "3 assertions"
opened               the claims themselves
```

At rest a filament says nothing, as every filament does. Looked at — an
endpoint hovered or selected — a group says how many claims it carries, because
one line standing for three of them is a lie by omission. Opened, it says what
they are.

The step into the third state is the count itself, and it requires the endpoint
**selected** rather than merely hovered: reaching for the count means leaving
the disc, and under hover alone the thing being reached for is gone before the
pointer arrives. So the count is a hit target only while an endpoint is
selected, and never while it is invisible. Once opened the group stays opened
while it is still being looked at — closing on the count's own `pointerleave`
would be a door that only stays open while you hold it, and the first thing the
pointer does after opening is move onto the claims it revealed.

The count is shown exactly when the names are not, so the two move as one
`emit` and the filament is never unnamed or named twice. It also stands exactly
where they will: the count takes the same 44px station off the acted-on rim
that the plates use, and tracks the same anchor. Pinned to the geometric
midpoint instead, the two halves of the fade happened in two places, which
reads as one thing dying while others are born elsewhere.

The opened stack is capped. Opening an unbounded stack does not make it
readable, it only defers the same problem to the pointer, so past
`BOND_LABEL_STACK_MAX` the filament shows what it can and the count stops being
a stand-in: it becomes `+N more`, standing at the end of the stack, saying the
one thing the plates cannot say for themselves — that they are not all of them.
The rest are in the reader, which is already open, because opening the group
required selecting an endpoint.

The count takes no plate. A plate is where construction origin lives, and a
summary spanning several origins that wore any one of them would assert a
further thing nothing constructed — so it is the knockout alone, square, in
the muted ink the lens labels use. It is furniture, not matter: it is not lit,
it is not a hit target, and the assertions underneath stay the only things a
person can take hold of. Touch expands the group by selecting an endpoint;
every revealed assertion remains independently selectable.

Selectable requires readable, and the stack that reveals them runs along the
filament's normal. A plate is thin the way it is tall and wide the way it is
long, so the step between two of them is a property of that direction, not a
fixed height: on a vertical filament — where the normal is horizontal — a step
of one plate height drew three relation names through each other.

Expansion continues to place new matter in free slots around its requested
subject and pin existing matter during the one-shot relaxation. Its geometry
communicates proximity to the request, not semantic cause or hierarchy.

## Arrangement — two named actions, no automatic relayout

A field's shape is a history of clicks. Expansion authored every position on a
person's behalf and nothing ever tidies, so twenty minutes of exploring leaves
a picture of the order things were asked for rather than of the question being
asked. Dragging one mark at a time is the only recourse the surface offered.

Two actions answer that, and neither is a layout engine:

**Gather** takes the marks joined to the selected subject and puts them around
it. It is not a second placement model — it is *arrival, run again*: the same
bodies, the same links, the same one-shot solver, with the pins moved so that
one subject's neighbours are free instead of the marks that just arrived. A
field arranged this way settles exactly as it would have if those neighbours
had been expanded from the subject in the first place, which is what keeps
there from being two answers to where a mark belongs. The subject is pinned —
the arrangement is *around* it — and matter not joined to it does not move at
all. That containment is the whole safety argument: the blast radius is the
thing the person named.

**Separate** is the same solver with the links taken away. Collision alone,
from where everything already is: a body overlapping nothing feels nothing and
does not move, so total displacement is bounded by the depth of the overlaps
and nothing is rearranged that was not already sitting on something. Keeping
the links would have made it a relayout of the whole field, which is a
different and far larger thing to ask for.

Both suspend `existing marks never move`, which is why both are things a person
clicks and neither ever happens on its own. Each records what it displaced and
offers to put it back, for exactly as long as the field it belongs to lasts:
once matter has arrived or left, those positions are no longer a state the
field was ever in, and offering to restore them would be offering a lie. The
moved marks travel with `settle` — a body finding a new rest — not the
pointer-direct `hold` every other standing update uses, and the canvas is told
which frame is the exception rather than inferring it, because a mark that
moves for any other reason is a bug and a canvas that guessed could not tell
the two apart.

They do not compose into a third thing. Gather can leave an overlap it was not
asked about; separate can leave a neighbour across the field. Two jobs, two
predictable blast radii — a single action that did both would have neither.

Directed layouts belong specifically to a derivation view, where causal
direction is actually known. Nothing here enables automatic relayout.

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
