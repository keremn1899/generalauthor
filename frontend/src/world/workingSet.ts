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
 * **The field is bounded by count, not by hope.** `MAX_FIELD_NODES` is the
 * cap, checked before an expansion runs, and the caller is expected to offer
 * the table instead rather than to quietly truncate. What makes this workable
 * is that the cost is known in advance: `/world/referent` returns a count per
 * relation, so the question "what would this cost" is answered before anything
 * is drawn.
 */

import type { WorldRole, WorldTuple } from "../api/world";
import { projectionOf } from "./marks";

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
/** How far apart two plates have to be before they are two plates. */
const PLATE_CLEARANCE = 34;

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

export type FieldBond = {
  assertion_id: string;
  relation: string;
  origin: string;
  mode: string;
  stale: boolean;
  completeness: "COMPLETE" | "INCOMPLETE" | "UNKNOWN" | null;
  source: string;
  target: string;
};

export type WorkingSet = {
  referents: Map<string, FieldReferent>;
  assertions: Map<string, FieldAssertion>;
  demands: Map<string, FieldDemand>;
  bonds: FieldBond[];
  positions: Map<string, Point>;
  /** relation names already expanded from a given referent, so a second click
   *  is a no-op rather than a pile of duplicate marks. */
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
 * Free space around an anchor.
 *
 * Angles are taken in a fixed order and skipped when something already sits
 * near them, so a second expansion of the same referent fans into the gaps the
 * first left rather than landing on top of it. Deterministic: the same
 * expansions in the same order always produce the same picture, which is what
 * makes a canvas something you can return to.
 */
function placeAround(
  positions: Map<string, Point>,
  anchor: Point,
  taken: number,
  index: number,
): Point {
  const slot = taken + index;
  const tier = Math.floor(slot / 8);
  const angle = -Math.PI / 2 + ((slot % 8) * Math.PI * 2) / 8 + tier * 0.4;
  const radius = RING_RADIUS + tier * RING_TIER;
  const at = {
    x: Math.round(anchor.x + Math.cos(angle) * radius),
    y: Math.round(anchor.y + Math.sin(angle) * radius),
  };
  // One nudge if something is already almost exactly there — enough to stop a
  // stack, not enough to pretend this is a layout engine.
  for (const existing of positions.values()) {
    if (Math.hypot(existing.x - at.x, existing.y - at.y) < 60) {
      return { x: at.x + 54, y: at.y + 34 };
    }
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
  if (next.expanded.has(key)) return set;
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
  return next;
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
      ? placeAround(next.positions, { x: 0, y: 0 }, next.referents.size, 0)
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

  if (projection === "bond" && spokes.length === 2) {
    if (!next.bonds.some((bond) => bond.assertion_id === tuple.assertion_id)) {
      next.bonds.push({
        assertion_id: tuple.assertion_id,
        relation: input.relation,
        origin: tuple.origin,
        mode: input.mode,
        stale: input.stale,
        completeness: input.completeness,
        source: spokes[0].id,
        target: spokes[1].id,
      });
    }
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
    next.positions.set(spoke.id, placeAround(next.positions, anchorAt, taken, placed));
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
  // the pair someone opens the frontier to compare. Stepped off each other
  // deterministically, the same one nudge `placeAround` makes, so the two are
  // both readable without pretending this is a layout engine.
  for (let step = 0; step < 6; step += 1) {
    let clash = false;
    for (const existing of next.positions.values()) {
      if (Math.hypot(existing.x - at.x, existing.y - at.y) < PLATE_CLEARANCE) {
        clash = true;
        break;
      }
    }
    if (!clash) break;
    at.x += 26;
    at.y += 22;
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

/** Take a mark and everything that only existed because of it. */
export function drop(set: WorkingSet, id: string): WorkingSet {
  const next = clone(set);
  next.referents.delete(id);
  next.positions.delete(id);
  next.bonds = next.bonds.filter((bond) => bond.source !== id && bond.target !== id);
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
