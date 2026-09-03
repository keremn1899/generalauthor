/**
 * The working set — what is currently on the field.
 *
 * The canvas is not a view of the World. It is a subgraph a person built by
 * asking for things, one expansion at a time, and this module is that
 * construction: which referents and assertions are on the field, where they
 * sit, and what it would cost to add more. Rule 9 lives here — the World is
 * never rendered, only what someone asked for.
 *
 * Two rules the rest of the surface depends on.
 *
 * **Existing marks never move.** Expanding places only what is new, ringed
 * around the mark it came from. A canvas that re-lays-out on every expansion
 * destroys the thing expansion is for: you looked away for a second and the
 * part you were reading is somewhere else. This is the same argument, and the
 * same shape, as `proposalPositions` in the product graph — a proposed node is
 * ringed around what it would attach to, because that placement is a statement
 * about what it connects to.
 *
 * `settle` takes the slack out of each fold afterwards — see `relax` — but it
 * is given the old marks as pins rather than asked to leave them alone, so the
 * rule holds by construction and not by care.
 *
 * **The field is bounded by count, not by hope.** `MAX_FIELD_NODES` is the
 * cap, checked before an expansion runs, and the caller is expected to offer
 * the table instead rather than to quietly truncate. What makes this workable
 * is that the cost is known in advance: `/world/referent` returns a count per
 * relation, so the question "what would this cost" is answered before anything
 * is drawn.
 */

import type { WorldRole, WorldTuple } from "../api/world";
import { projectionOf } from "./marks";
import { relax, type RelaxBody, type RelaxLink } from "./relax";

/**
 * How much matter the field will hold.
 *
 * Not a rendering limit — G6 draws thousands. It is a reading limit: past
 * roughly this many marks a neighborhood stops being a thing you can hold in
 * your head, which is the only reason to be looking at a graph rather than a
 * table.
 */
export const MAX_FIELD_NODES = 150;

/** Where new matter lands relative to what it came from. */
const RING_RADIUS = 190;
const RING_TIER = 120;
const CHIP_INSET = 0.55;
/**
 * What each kind of mark keeps around itself while the field settles.
 *
 * d3 separates two bodies by the sum of their radii, so these three numbers
 * are really the three clearances the field needs, expressed once each: two
 * discs end up 104 apart — inside the ring's own chord, which is 145 at eight
 * slots to a tier, so settling never collapses the fan that placed them — a
 * plate stays 70 from a disc centre, which is 25 clear of its edge, and two
 * plates stay 36 apart, which is the gap two chips need to read as two.
 */
const DISC_BODY = 52;
const PLATE_BODY = 18;
/** How far a plate wants to sit from each mark it joins. */
const SPOKE_LENGTH = 110;

export type Point = { x: number; y: number };

export type FieldReferent = {
  id: string;
  label: string;
  /** The referent this one arrived beside, if it was not the seed. */
  via?: string;
};

export type FieldAssertion = {
  assertion_id: string;
  relation: string;
  origin: string;
  mode: string;
  stale: boolean;
  completeness: "COMPLETE" | "INCOMPLETE" | "UNKNOWN" | null;
  /** Referent role values, in role order. */
  spokes: { role: string; id: string }[];
  /** Scalar role values, which stay off the field and in the inspector. */
  scalars: { role: string; value: unknown }[];
};

/**
 * An obligation on the field: a tuple a purpose asked for and the world does
 * not assert (§8.7).
 *
 * It has no assertion id because there is no assertion — that is the whole
 * content of the mark — so it is keyed by the relation and its values, which is
 * the only identity an unresolved thing has.
 */
export type FieldDemand = {
  key: string;
  relation: string;
  spokes: { role: string; id: string }[];
  scalars: { role: string; value: unknown }[];
};

/**
 * A binary tuple drawn as the line it makes.
 *
 * It carries its roles and scalars even though a filament draws neither. A
 * bond is not a different kind of thing from a plate — it is the same tuple
 * folded onto the line between its two referents — and `open` unfolds it in
 * place. Keeping the folded form complete is what makes that a change of
 * drawing rather than a refetch.
 */
export type FieldBond = {
  assertion_id: string;
  relation: string;
  origin: string;
  mode: string;
  stale: boolean;
  completeness: "COMPLETE" | "INCOMPLETE" | "UNKNOWN" | null;
  source: string;
  target: string;
  /** Referent role values in role order — the spokes the open form would have. */
  spokes: { role: string; id: string }[];
  /** Scalar role values, which the filament has nowhere to put. */
  scalars: { role: string; value: unknown }[];
};

export type WorkingSet = {
  referents: Map<string, FieldReferent>;
  assertions: Map<string, FieldAssertion>;
  demands: Map<string, FieldDemand>;
  bonds: FieldBond[];
  positions: Map<string, Point>;
  /** Expansions that completed, including empty expansions. This is completion
   *  provenance, not the source of truth for whether their tuples are still on
   *  the field; `expansionOnField` derives that from the material itself. */
  expanded: Set<string>;
};

export function emptySet(): WorkingSet {
  return {
    referents: new Map(),
    assertions: new Map(),
    demands: new Map(),
    bonds: [],
    positions: new Map(),
    expanded: new Set(),
  };
}

export function fieldSize(set: WorkingSet): number {
  return set.referents.size + set.assertions.size + set.demands.size;
}

export function expansionKey(referentId: string, relation: string): string {
  return `${referentId}\u0000${relation}`;
}

/** How many positive tuples of this relation involving this referent stand here. */
export function expansionTupleCount(
  set: WorkingSet,
  referentId: string,
  relation: string,
): number {
  const ids = new Set<string>();
  for (const assertion of set.assertions.values()) {
    if (
      assertion.relation === relation &&
      assertion.spokes.some((spoke) => spoke.id === referentId)
    ) {
      ids.add(assertion.assertion_id);
    }
  }
  for (const bond of set.bonds) {
    if (
      bond.relation === relation &&
      bond.spokes.some((spoke) => spoke.id === referentId)
    ) {
      ids.add(bond.assertion_id);
    }
  }
  return ids.size;
}

/**
 * Whether expanding this relation would add any tuple matter.
 *
 * Presence is derived from the field rather than from the route by which a
 * tuple arrived. A row focus or an expansion from the tuple's other referent
 * can put exactly the same assertion here, and the panel must still say "on
 * field". The completion record matters only for a legitimately empty
 * expansion, where there is no material from which to derive the answer.
 */
export function expansionOnField(
  set: WorkingSet,
  referentId: string,
  relation: string,
  expectedCount: number,
): boolean {
  if (expectedCount === 0) {
    return set.expanded.has(expansionKey(referentId, relation));
  }
  return expansionTupleCount(set, referentId, relation) >= expectedCount;
}

/** Put the first referent on an empty field, at the middle. */
export function seed(set: WorkingSet, id: string, label: string): WorkingSet {
  const next = clone(set);
  next.referents.set(id, { id, label });
  next.positions.set(id, { x: 0, y: 0 });
  return next;
}

function clone(set: WorkingSet): WorkingSet {
  return {
    referents: new Map(set.referents),
    assertions: new Map(set.assertions),
    demands: new Map(set.demands),
    bonds: [...set.bonds],
    positions: new Map(set.positions),
    expanded: new Set(set.expanded),
  };
}

/**
 * How much room a mark of each kind needs around its centre.
 *
 * Read off `DISC_BODY` and `PLATE_BODY`, which is what makes placement and
 * settling agree about what "clear" means: a slot placement accepts is a slot
 * the settle has no reason to push anything out of.
 */
function bodyRadius(next: WorkingSet, id: string): number {
  return next.referents.has(id) ? DISC_BODY : PLATE_BODY;
}

/** Whether a mark of this size could sit here without landing on anything. */
function isClear(next: WorkingSet, at: Point, radius: number, ignore?: string): boolean {
  for (const [id, existing] of next.positions) {
    if (id === ignore) continue;
    const apart = Math.hypot(existing.x - at.x, existing.y - at.y);
    if (apart < radius + bodyRadius(next, id)) return false;
  }
  return true;
}

/**
 * How far the search will go before it gives up and takes the last slot.
 *
 * Eight tiers, which at `RING_TIER` apart is further out than a field capped
 * at `MAX_FIELD_NODES` can fill.
 */
const PROBES = 64;

/**
 * Free space around an anchor.
 *
 * Angles are taken in a fixed order and skipped when something already sits
 * near them, so a second expansion of the same referent fans into the gaps the
 * first left rather than landing on top of it. Deterministic: the same
 * expansions in the same order always produce the same picture, which is what
 * makes a canvas something you can return to.
 *
 * The skipping has to happen here rather than be left to the settle, because
 * pushing marks apart cannot get one *out* of somewhere it should not have
 * been put. A disc dropped into a pocket of marks that surround it is pushed
 * equally from every side and stays exactly where it landed — a stable place
 * to be, and the wrong one. Collision opens a gap; it does not find a door.
 * So the slot has to be free before anything is placed in it.
 */
function placeAround(
  next: WorkingSet,
  anchor: Point,
  taken: number,
  index: number,
): Point {
  let at = { x: anchor.x, y: anchor.y };
  for (let probe = 0; probe < PROBES; probe += 1) {
    const slot = taken + index + probe;
    const tier = Math.floor(slot / 8);
    const angle = -Math.PI / 2 + ((slot % 8) * Math.PI * 2) / 8 + tier * 0.4;
    const radius = RING_RADIUS + tier * RING_TIER;
    at = {
      x: Math.round(anchor.x + Math.cos(angle) * radius),
      y: Math.round(anchor.y + Math.sin(angle) * radius),
    };
    if (isClear(next, at, DISC_BODY)) return at;
  }
  return at;
}

export type ExpansionInput = {
  anchor: string;
  relation: string;
  mode: string;
  stale: boolean;
  completeness: "COMPLETE" | "INCOMPLETE" | "UNKNOWN" | null;
  roles: WorldRole[];
  tuples: WorldTuple[];
  /** Labels for referents that may not be on the field yet. */
  labels: Map<string, string | null>;
};

/** Fold every tuple of one relation, as read from one referent, into the field. */
export function expand(set: WorkingSet, input: ExpansionInput): WorkingSet {
  const next = clone(set);
  const key = expansionKey(input.anchor, input.relation);
  // `expanded` records that a request once completed; it cannot prove its
  // material is still present after a related referent was dropped. Only skip
  // when every tuple returned by this request still has one of its two field
  // drawings.
  const materialComplete = input.tuples.every(
    (tuple) =>
      next.assertions.has(tuple.assertion_id) ||
      next.bonds.some((bond) => bond.assertion_id === tuple.assertion_id),
  );
  if (next.expanded.has(key) && materialComplete) return set;
  next.expanded.add(key);

  const taken = countAround(set, input.anchor);
  let placed = 0;
  for (const tuple of input.tuples) {
    placed = fold(next, {
      anchor: input.anchor,
      relation: input.relation,
      mode: input.mode,
      stale: input.stale,
      completeness: input.completeness,
      roles: input.roles,
      tuple,
      labels: input.labels,
    }, taken, placed);
  }
  settle(set, next);
  return next;
}

export type PlacementInput = {
  relation: string;
  mode: string;
  stale: boolean;
  completeness: "COMPLETE" | "INCOMPLETE" | "UNKNOWN" | null;
  roles: WorldRole[];
  tuple: WorldTuple;
  labels: Map<string, string | null>;
};

/**
 * Put one tuple on the field — a table row focusing its graph projection.
 *
 * §11: the table and the canvas are two projections of one relation state, so
 * selecting a row has to be able to say *show me this one*. The anchor is a
 * referent from the tuple that is already on the field when there is one, which
 * is what makes picking a row out of a table land the tuple beside the
 * neighborhood you were already reading rather than somewhere else on the
 * canvas. With an empty field the first referent takes the middle and the rest
 * fan around it, exactly as a seed would.
 */
export function place(set: WorkingSet, input: PlacementInput): WorkingSet {
  const next = clone(set);
  const spokes = input.roles
    .filter((role) => role.referent)
    .map((role) => String(input.tuple.values[role.name]));
  const anchor = anchorFor(next, spokes, input.labels);
  if (!anchor) return set;

  fold(next, { ...input, anchor }, countAround(set, anchor), 0);
  settle(set, next);
  return next;
}

export type DemandPlacement = {
  /** The obligation's identity, since an unresolved tuple has no assertion id. */
  key: string;
  relation: string;
  roles: WorldRole[];
  values: Record<string, unknown>;
  labels: Map<string, string | null>;
};

/**
 * Put one unresolved obligation on the field (§8.7, §9).
 *
 * An obligation is drawn as a standing hollow chip with a dotted spoke per
 * role, at every arity — it never collapses onto a bond the way a binary
 * assertion does, and that is deliberate rather than a shortcut. A bond is a
 * line between two referents saying they are joined; there is no such line to
 * draw here, because nothing has been asserted. Drawing one and marking it
 * somehow would be the front end implying a connection the world has not made,
 * which is the same error as implying falsehood from absence.
 */
export function placeDemand(set: WorkingSet, input: DemandPlacement): WorkingSet {
  if (set.demands.has(input.key)) return set;
  const next = clone(set);
  const referentRoles = input.roles.filter((role) => role.referent);
  const spokes = referentRoles.map((role) => ({
    role: role.name,
    id: String(input.values[role.name]),
  }));
  const anchor = anchorFor(next, spokes.map((spoke) => spoke.id), input.labels);
  if (!anchor) return set;
  const anchorAt = next.positions.get(anchor) ?? { x: 0, y: 0 };

  attach(next, spokes, anchor, anchorAt, countAround(set, anchor), 0, input.labels);
  next.demands.set(input.key, {
    key: input.key,
    relation: input.relation,
    spokes,
    scalars: input.roles
      .filter((role) => !role.referent)
      .map((role) => ({ role: role.name, value: input.values[role.name] })),
  });
  next.positions.set(input.key, plateAt(next, anchorAt, spokes));
  settle(set, next);
  return next;
}

/**
 * Take the slack out of what just arrived, and nothing else.
 *
 * Placement stays where it was — new marks are fanned onto a ring around what
 * they came from, which is a statement about where they belong. What the fan
 * cannot do is know whether the slot it chose was already occupied by material
 * from some earlier expansion, and the one-nudge answer in `placeAround` was
 * only ever meant to stop a stack, not to resolve a crowd.
 *
 * So: one headless settling pass, every mark already on the field held exactly
 * where it is, and only the referents that arrived in this fold free to move.
 * Because the solver is given the pins rather than trusted to respect them,
 * `existing marks never move` holds by construction — including for a disc a
 * person dragged, which by the next expansion is simply something already on
 * the field.
 *
 * Plates are not bodies. A plate sits between the marks it joins, so it is
 * recomputed from its spokes afterwards, and only where a spoke actually
 * moved: a plate whose referents all stayed put is a mark already on the field
 * like any other.
 */
function settle(before: WorkingSet, next: WorkingSet): void {
  const arrived = new Set<string>();
  const held = (id: string) => !arrived.has(id);
  for (const id of next.referents.keys()) {
    if (!before.referents.has(id)) arrived.add(id);
  }
  for (const id of next.assertions.keys()) {
    if (!before.assertions.has(id)) arrived.add(id);
  }
  for (const id of next.demands.keys()) {
    if (!before.demands.has(id)) arrived.add(id);
  }
  if (!arrived.size) return;

  const bodies: RelaxBody[] = [];
  const body = (id: string, radius: number) => {
    const at = next.positions.get(id);
    if (at) bodies.push({ id, x: at.x, y: at.y, pinned: held(id), radius });
  };
  for (const id of next.referents.keys()) body(id, DISC_BODY);
  for (const id of next.assertions.keys()) body(id, PLATE_BODY);
  for (const id of next.demands.keys()) body(id, PLATE_BODY);

  // What the field says is joined. A bond is already a line between two
  // referents. A plate is joined to each mark it gathers, which is both what
  // holds it between them and what carries its referents toward each other —
  // so there is no separate pull between co-participants to add.
  const links: RelaxLink[] = [];
  for (const bond of next.bonds) {
    links.push({ source: bond.source, target: bond.target, distance: RING_RADIUS });
  }
  const spokesOf = (id: string, spokes: { id: string }[]) => {
    for (const spoke of spokes) {
      links.push({ source: id, target: spoke.id, distance: SPOKE_LENGTH });
    }
  };
  for (const [id, assertion] of next.assertions) spokesOf(id, assertion.spokes);
  for (const [id, demand] of next.demands) spokesOf(id, demand.spokes);

  for (const [id, at] of relax(bodies, links)) next.positions.set(id, at);
}

/**
 * Which mark this tuple hangs off.
 *
 * A referent already on the field when there is one, so a tuple picked out of a
 * list lands beside the neighborhood being read rather than somewhere else on
 * the canvas. With nothing to hang off, the first referent takes the middle of
 * an empty field or a free slot on a busy one, exactly as a seed would.
 */
function anchorFor(
  next: WorkingSet,
  spokes: string[],
  labels: Map<string, string | null>,
): string | null {
  const present = spokes.find((id) => next.referents.has(id));
  if (present) return present;
  const first = spokes[0];
  if (!first) return null;
  next.referents.set(first, { id: first, label: labels.get(first) ?? first });
  next.positions.set(
    first,
    next.positions.size
      ? placeAround(next, { x: 0, y: 0 }, next.referents.size, 0)
      : { x: 0, y: 0 },
  );
  return first;
}

/**
 * Fold one tuple into the field, returning how many marks it placed.
 *
 * The projection decision is the same one the schema canvas makes, from the
 * same function: a tuple with two referents becomes a bond, one with three or
 * more becomes a plate with a spoke per role, and a tuple carrying one referent
 * plus scalars becomes a plate too — it is a property of one thing, and it has
 * an assertion behind it worth opening.
 */
function fold(
  next: WorkingSet,
  input: PlacementInput & { anchor: string },
  taken: number,
  placed: number,
): number {
  const anchorAt = next.positions.get(input.anchor) ?? { x: 0, y: 0 };
  const referentRoles = input.roles.filter((role) => role.referent);
  const scalarRoles = input.roles.filter((role) => !role.referent);
  const projection = projectionOf(input.roles.length, referentRoles.length);
  const tuple = input.tuple;

  const spokes = referentRoles.map((role) => ({
    role: role.name,
    id: String(tuple.values[role.name]),
  }));
  const scalars = scalarRoles.map((role) => ({
    role: role.name,
    value: tuple.values[role.name],
  }));

  placed = attach(next, spokes, input.anchor, anchorAt, taken, placed, input.labels);

  // Already standing, in either form. A second fold would overwrite the record
  // and recompute its position, which is `existing marks never move` broken by
  // the one path that is allowed to add marks. This is also what lets a bond
  // stay open across later expansions: its plate is not a bond any more, so the
  // `bonds` check alone would not have found it.
  if (
    next.assertions.has(tuple.assertion_id) ||
    next.bonds.some((bond) => bond.assertion_id === tuple.assertion_id)
  ) {
    return placed;
  }

  if (projection === "bond" && spokes.length === 2) {
    next.bonds.push({
      assertion_id: tuple.assertion_id,
      relation: input.relation,
      origin: tuple.origin,
      mode: input.mode,
      stale: input.stale,
      completeness: input.completeness,
      source: spokes[0].id,
      target: spokes[1].id,
      spokes,
      scalars,
    });
    return placed;
  }

  next.assertions.set(tuple.assertion_id, {
    assertion_id: tuple.assertion_id,
    relation: input.relation,
    origin: tuple.origin,
    mode: input.mode,
    stale: input.stale,
    completeness: input.completeness,
    spokes,
    scalars,
  });
  next.positions.set(tuple.assertion_id, plateAt(next, anchorAt, spokes));
  return placed;
}

/**
 * Bring a tuple's referents onto the field, returning how many were new.
 *
 * Every referent in the tuple joins, including the ones that were already there
 * — a tuple whose partners are all present adds its plate and no discs, which
 * is how a neighborhood closes up on itself instead of growing a second copy of
 * what you can already see.
 */
function attach(
  next: WorkingSet,
  spokes: { role: string; id: string }[],
  anchor: string,
  anchorAt: Point,
  taken: number,
  placed: number,
  labels?: Map<string, string | null>,
): number {
  for (const spoke of spokes) {
    if (next.referents.has(spoke.id)) continue;
    next.referents.set(spoke.id, {
      id: spoke.id,
      label: labels?.get(spoke.id) ?? spoke.id,
      via: anchor,
    });
    next.positions.set(spoke.id, placeAround(next, anchorAt, taken, placed));
    placed += 1;
  }
  return placed;
}

/**
 * Where a plate sits: between the marks it joins, pulled in from their centroid
 * so its spokes read as short and its name does not land on a disc.
 */
function plateAt(
  next: WorkingSet,
  anchorAt: Point,
  spokes: { id: string }[],
): Point {
  const points = spokes
    .map((spoke) => next.positions.get(spoke.id))
    .filter((point): point is Point => Boolean(point));
  const centre = points.length
    ? {
        x: points.reduce((sum, p) => sum + p.x, 0) / points.length,
        y: points.reduce((sum, p) => sum + p.y, 0) / points.length,
      }
    : anchorAt;
  const at = {
    x: Math.round(anchorAt.x + (centre.x - anchorAt.x) * CHIP_INSET),
    y: Math.round(anchorAt.y + (centre.y - anchorAt.y) * CHIP_INSET),
  };
  // Two tuples over nearly the same referents land in nearly the same place —
  // an obligation and the assertion that would answer it, say, which is exactly
  // the pair someone opens the frontier to compare. Stepped off each other by
  // the same rule the discs are placed by: walk out from where the plate wants
  // to be until the spot is actually free. The path is a phyllotaxis spiral, so
  // it covers the ring evenly instead of running off in one diagonal, and it is
  // the same path every time.
  if (isClear(next, at, PLATE_BODY)) return at;
  const golden = Math.PI * (3 - Math.sqrt(5));
  for (let probe = 1; probe <= PROBES; probe += 1) {
    const radius = 26 * Math.sqrt(probe);
    const angle = probe * golden;
    const stepped = {
      x: Math.round(at.x + Math.cos(angle) * radius),
      y: Math.round(at.y + Math.sin(angle) * radius),
    };
    if (isClear(next, stepped, PLATE_BODY)) return stepped;
  }
  return at;
}

/** How many marks already sit around this one, so the next fan starts clear. */
function countAround(set: WorkingSet, anchor: string): number {
  let count = 0;
  for (const referent of set.referents.values()) {
    if (referent.via === anchor) count += 1;
  }
  return count;
}

/**
 * Whether a mark on the field has a second form, and which way it would go.
 *
 * A binary assertion is drawn two ways: as the filament between its referents,
 * or as a plate standing between them with a named spoke to each. Both are the
 * same tuple. The line is the reading where the relation is the connection; the
 * plate is the reading where the relation is a thing that has roles — and roles
 * are precisely what a named typed n-ary relation adds and what a labelled line
 * cannot show. So this is semantic zoom and not decluttering: opening a bond
 * reveals `part` and `bom_item`, and any scalar the line had nowhere to put.
 *
 * Two things deliberately have no second form.
 *
 * An assertion with three or more referents has no line to fold onto, so it is
 * only ever a plate. And an **obligation never collapses onto a bond at any
 * arity** — a line between two discs asserts that they are joined, and the
 * entire content of an unresolved mark is that no such claim has been made.
 * That is why this reads the field's own collections rather than arity: a
 * demand is not in either of them.
 */
export function foldingOf(
  set: WorkingSet,
  id: string,
): "open" | "collapse" | null {
  if (set.bonds.some((bond) => bond.assertion_id === id)) return "open";
  const assertion = set.assertions.get(id);
  if (assertion && assertion.spokes.length === 2) return "collapse";
  return null;
}

/**
 * Unfold a bond into the plate it is.
 *
 * The plate lands on the midpoint of the line it replaces, so the line appears
 * to open rather than to be swapped for something elsewhere, and neither disc
 * moves — this changes how a tuple is drawn and nothing about where the field
 * stands. `plateAt` still probes outward if the midpoint is already occupied,
 * by the same phyllotaxis walk every other plate is placed with.
 */
export function open(set: WorkingSet, assertionId: string): WorkingSet {
  const bond = set.bonds.find((edge) => edge.assertion_id === assertionId);
  if (!bond) return set;
  const next = clone(set);
  next.bonds = next.bonds.filter((edge) => edge.assertion_id !== assertionId);
  next.assertions.set(assertionId, {
    assertion_id: bond.assertion_id,
    relation: bond.relation,
    origin: bond.origin,
    mode: bond.mode,
    stale: bond.stale,
    completeness: bond.completeness,
    spokes: bond.spokes,
    scalars: bond.scalars,
  });
  const ends = [bond.source, bond.target]
    .map((id) => next.positions.get(id))
    .filter((point): point is Point => Boolean(point));
  const middle = ends.length
    ? {
        x: ends.reduce((sum, p) => sum + p.x, 0) / ends.length,
        y: ends.reduce((sum, p) => sum + p.y, 0) / ends.length,
      }
    : { x: 0, y: 0 };
  next.positions.set(assertionId, plateAt(next, middle, bond.spokes));
  return next;
}

/** Fold a two-referent plate back onto the line between its referents. */
export function collapse(set: WorkingSet, assertionId: string): WorkingSet {
  const assertion = set.assertions.get(assertionId);
  if (!assertion || assertion.spokes.length !== 2) return set;
  const next = clone(set);
  next.assertions.delete(assertionId);
  next.positions.delete(assertionId);
  next.bonds.push({
    assertion_id: assertion.assertion_id,
    relation: assertion.relation,
    origin: assertion.origin,
    mode: assertion.mode,
    stale: assertion.stale,
    completeness: assertion.completeness,
    source: assertion.spokes[0].id,
    target: assertion.spokes[1].id,
    spokes: assertion.spokes,
    scalars: assertion.scalars,
  });
  return next;
}

/** Take a mark and everything that only existed because of it. */
export function drop(set: WorkingSet, id: string): WorkingSet {
  const next = clone(set);
  next.referents.delete(id);
  next.positions.delete(id);
  next.bonds = next.bonds.filter(
    (bond) => bond.source !== id && bond.target !== id,
  );
  for (const [assertionId, assertion] of next.assertions) {
    if (assertion.spokes.some((spoke) => spoke.id === id)) {
      next.assertions.delete(assertionId);
      next.positions.delete(assertionId);
    }
  }
  for (const [key, demand] of next.demands) {
    if (demand.spokes.some((spoke) => spoke.id === id)) {
      next.demands.delete(key);
      next.positions.delete(key);
    }
  }
  for (const key of [...next.expanded]) {
    if (key.startsWith(`${id}\u0000`)) next.expanded.delete(key);
  }
  return next;
}

/**
 * Take a mark off the field.
 *
 * A referent still takes everything that only existed because of it. An
 * assertion, bond, or obligation leaves on its own — the discs it joined stay,
 * which is what makes Delete a small verb rather than a neighbourhood wipe.
 */
export function dropMark(set: WorkingSet, id: string): WorkingSet {
  if (set.referents.has(id)) return drop(set, id);
  const next = clone(set);
  next.assertions.delete(id);
  next.demands.delete(id);
  next.positions.delete(id);
  next.bonds = next.bonds.filter((bond) => bond.assertion_id !== id);
  return next;
}
