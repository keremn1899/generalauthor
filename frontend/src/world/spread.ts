/**
 * A selected mark spreads its own strokes so their names can be read.
 *
 * Every bond and spoke a mark carries stations its plate a fixed distance out
 * from that mark's rim — `BOND_LABEL_ALONG_PX`, the same station for all of
 * them, because a name must not drift toward the midpoint merely because
 * somebody dragged the other end further away. The consequence is that two
 * neighbours a few degrees apart put two plates in the same place. At rest
 * that costs nothing: nothing is named. Selecting the mark names all of them
 * at once, which is exactly when the pile appears, and a pile of names is not
 * an answer.
 *
 * So the selection spreads them. Each stroke leaves the mark on its own angle,
 * pushed off its neighbours until there is a minimum arc between them, and its
 * plate rides out to the station on that new angle. The names occupy an arc
 * instead of a point.
 *
 * Four properties keep it a spread rather than a rearrangement, and all four
 * are the product canvas's, ported whole:
 *
 * **Circular order is kept.** Strokes are pushed apart in the order they
 * already stand in, so the fan is the neighbourhood as it was, opened up — not
 * a different neighbourhood with the same members.
 *
 * **Each stroke is clamped.** No stroke leaves its own angle by more than
 * `SPREAD_MAX_DEFLECT`, so a crowded mark fans in place instead of eating the
 * circle, and the direction a neighbour lies in stays true.
 *
 * **The far end never moves.** Only the held end's angle changes. What is
 * joined to what is not up for negotiation.
 *
 * **It is a rest pose.** A mark being dragged would re-solve every frame,
 * which is both expensive and unreadable, so the field snaps back to its
 * chords until the pointer lets go.
 *
 * This is presentation and nothing else. No tuple, position or label station
 * is touched: `filaments.ts` holds each elbow in the renderer, and letting go
 * of the mark puts every stroke back on the line it was always drawn as.
 */

import type { Graph } from "@antv/g6";
import {
  BOND_LABEL_ALONG_PX,
  BOND_LABEL_STACK_GAP,
  chipWidth,
  rimDistance,
  type MarkParams,
  type MarkRim,
} from "./marks";
import {
  clearFilamentFans,
  updateFilamentFans,
  type FilamentFanPatch,
} from "./filaments";
import type { MotionPlan, MotionPlans } from "../styles/motion";

type Point = { x: number; y: number };

/**
 * Never more than this, whatever the plates ask: past it the fan is a fiction.
 *
 * There is deliberately no matching floor. A floor answers "these two overlap"
 * with a fixed arc, so a pair a degree from clearing is opened as far as a
 * pair sitting exactly on top of each other, and the fan reads as having an
 * opinion about the neighbourhood rather than a job in it. What two plates
 * need is a measurable quantity; the room they need to be *comfortable* is
 * already in their half-extents as `BOND_LABEL_STACK_GAP`. Asking for exactly
 * that and no more is what keeps this minimal.
 */
const SPREAD_MAX_ARC = 0.9;
/**
 * How far a stroke may leave the angle its neighbour gives it, in radians.
 *
 * The direction a neighbour lies in is information the drawing is asserting,
 * and every radian of deflection is a small lie told to make a name legible.
 * 0.4 is about 23°: enough to unstack a crowded pair, small enough that the
 * neighbour is still where the fan says it is.
 */
const SPREAD_MAX_DEFLECT = 0.4;
/**
 * Below this much plate travel there is nothing to see, so nothing is moved.
 *
 * In pixels rather than radians, because an angle is not a visible quantity:
 * the same small rotation moves a plate stationed far out several pixels and
 * one stationed close in none at all. Held as an angle this threshold refused
 * the cheapest fixes there are — a pair a degree from clearing, which is
 * exactly the case a minimal spread should be best at — while still allowing
 * that angle on a stroke where it did less.
 */
const SPREAD_SKIP_PX = 1;

export type FanWaypoint = {
  angle: number;
  along: number;
  fromSource: boolean;
  /** How far this stroke was moved, so a stroke already clear stays still. */
  deflect: number;
};

/* ------------------------------------------------------------------ *
 * Geometry
 * ------------------------------------------------------------------ */

function wrapAngle(angle: number) {
  return Math.atan2(Math.sin(angle), Math.cos(angle));
}

/** What one stroke brings to the spacing: its bearing and the plate it carries. */
type Spoke = {
  angle: number;
  /** Half-extents of the plate at its station, plus the air it wants. */
  halfWidth: number;
  halfHeight: number;
  /** Distance from the mark's centre to that station. */
  station: number;
};

/**
 * How far apart two adjacent strokes have to stand.
 *
 * Not a constant, because the thing being separated is not a stroke — it is a
 * plate, and a plate is a wide, short, *unrotated* box. Two names stacked one
 * above the other clear at a shallow angle; the same two names side by side
 * need four times as much, and a single number has to be wrong for one of
 * those cases.
 *
 * So the question is asked of the two stations themselves rather than of an
 * idealised arc through them. They rarely sit at the same radius — the station
 * is capped against each filament's own length, so a stroke to a near
 * neighbour carries its name closer in — and on an arc that assumption is the
 * whole answer: it puts the separation where the geometry does not. Measuring
 * the offset that is actually there, and asking which axis could clear it,
 * costs a cosine and is true of the drawing.
 *
 * Zero means *these two are already readable* — not that they are touching.
 * The floor applies to a pair that has to move, so a demand is never answered
 * with a nudge too small to see; the cap applies because a plate wide enough
 * to want more than `SPREAD_MAX_ARC` cannot be fixed by fanning, and trying
 * would draw a neighbour somewhere it is not.
 */
function requiredArc(
  angleA: number,
  angleB: number,
  a: Spoke,
  b: Spoke,
): number {
  const dx = Math.cos(angleB) * b.station - Math.cos(angleA) * a.station;
  const dy = Math.sin(angleB) * b.station - Math.sin(angleA) * a.station;
  const apart = Math.hypot(dx, dy);
  if (!(apart > 0.001)) {
    // Exactly coincident, so there is no offset to measure and no direction to
    // measure it along. Ask the plates instead: the arc that puts this much
    // clearance between two boxes at this radius is the clearance over the
    // radius, which is the same small-angle statement the branch below makes
    // once there is a direction to make it in.
    const station = Math.max(1, (a.station + b.station) / 2);
    return Math.min(SPREAD_MAX_ARC, (a.halfWidth + b.halfWidth) / station);
  }
  const alongX = Math.abs(dx) / apart;
  const alongY = Math.abs(dy) / apart;
  const byWidth =
    alongX > 0.05 ? (a.halfWidth + b.halfWidth) / alongX : Infinity;
  const byHeight =
    alongY > 0.05 ? (a.halfHeight + b.halfHeight) / alongY : Infinity;
  // Either axis clearing is enough: two boxes that miss each other sideways
  // are readable whether or not they also miss each other vertically.
  const needed = Math.min(byWidth, byHeight);
  if (!Number.isFinite(needed) || apart >= needed) return 0;
  let gap = angleB - angleA;
  if (gap < 0) gap += Math.PI * 2;
  /**
   * Distance grows with the gap, near enough proportionally over the small
   * corrections a pass makes, so this is the step — and the relaxation is what
   * makes it exact. `needed / apart` is barely over 1 for a pair that almost
   * clears, which is the whole point: they are asked to open by almost
   * nothing.
   *
   * Scaling a gap cannot open one that is already closed, though, and two
   * neighbours can lie on the same bearing at different distances: their
   * plates are stationed at different radii, so they are genuinely apart and
   * genuinely overlapping, with no angle between them to scale. That pair gets
   * the small-angle clearance instead, purely to break it out of the
   * collinear case — one iteration later there is a gap to measure and the
   * proportional form takes over, so the arc it settles at is still the least
   * one that clears.
   */
  const station = Math.max(1, (a.station + b.station) / 2);
  const step =
    gap > 0.02 ? gap * (needed / apart) : (a.halfWidth + b.halfWidth) / station;
  return Math.min(SPREAD_MAX_ARC, step);
}

/**
 * Local angular spacing: keep circular order, push neighbours apart by what
 * their plates need, then clamp each stroke so a bundle fans in place rather
 * than eating the circle.
 */
function spreadAngles(spokes: Spoke[], maxDeflect: number): number[] {
  const count = spokes.length;
  const result = spokes.map((spoke) => spoke.angle);
  if (count < 2) return result;
  const order = spokes
    .map((spoke, index) => ({ angle: wrapAngle(spoke.angle), index }))
    .sort((a, b) => a.angle - b.angle);
  const current = order.map((entry) => entry.angle);
  /**
   * Relaxation, not a closed form: each pass asks every adjacent pair how much
   * arc its plates need *at the angles they now hold*, then re-clamps every
   * stroke to its own bearing, and the two constraints settle against each
   * other.
   *
   * Every pair's push is collected before any of them is applied. Applying
   * them one at a time — the product canvas does, and can, because a single
   * small arc for every pair is symmetric — means the pair processed last
   * closes the gap the pair processed first had just opened, and a demand that
   * depends on *direction* is not symmetric: the two pairs want different
   * arcs, so the pass ends wherever it happened to stop rather than where the
   * plates asked to be.
   */
  const push = new Array<number>(count).fill(0);
  for (let iter = 0; iter < 48; iter += 1) {
    push.fill(0);
    for (let i = 0; i < count; i += 1) {
      const next = (i + 1) % count;
      let gap = current[next] - current[i];
      if (next === 0) gap += Math.PI * 2;
      const minDelta = requiredArc(
        current[i],
        current[i] + gap,
        spokes[order[i].index],
        spokes[order[next].index],
      );
      if (gap >= minDelta) continue;
      const need = (minDelta - gap) / 2;
      push[i] -= need;
      push[next] += need;
    }
    for (let i = 0; i < count; i += 1) current[i] += push[i];
    for (let i = 0; i < count; i += 1) {
      const original = order[i].angle;
      const delta = Math.max(
        -maxDeflect,
        Math.min(maxDeflect, wrapAngle(current[i] - original)),
      );
      current[i] = original + delta;
    }
  }
  for (let i = 0; i < count; i += 1) result[order[i].index] = current[i];
  return result;
}

/* ------------------------------------------------------------------ *
 * Reading the field
 * ------------------------------------------------------------------ */

function positionOf(graph: Graph, id: string): Point | null {
  try {
    const at = graph.getElementPosition(id);
    if (!at || !Number.isFinite(at[0]) || !Number.isFinite(at[1])) return null;
    return { x: at[0], y: at[1] };
  } catch {
    return null;
  }
}

/**
 * G6 throws for an id it does not hold rather than answering nothing, and a
 * selection routinely names a mark the canvas has not drawn yet — the reader
 * opens on it while the frame carrying it is still in the draw lane. Asking is
 * the check.
 */
function standingNode(graph: Graph, id: string) {
  try {
    return graph.getNodeData(id) ?? null;
  } catch {
    return null;
  }
}

/**
 * Where a stroke's rim is, which is where its plate is measured from.
 *
 * The same rim `bondLabelLayout` is handed when it stations a resting name.
 * The two have to agree or the fanned plate would sit at a different distance
 * than the resting one, and the spread would read as the names jumping
 * outward — so this reads the mark's drawn size and hands back the shape,
 * leaving `rimDistance` to say how far that rim is along a given bearing.
 */
function rimOf(graph: Graph, id: string, params: MarkParams): MarkRim {
  const size = standingNode(graph, id)?.style?.size;
  if (typeof size === "number") return { shape: "disc", radius: size / 2 };
  if (
    Array.isArray(size) &&
    size.length >= 2 &&
    typeof size[0] === "number" &&
    typeof size[1] === "number"
  ) {
    return {
      shape: "plate",
      halfWidth: size[0] / 2,
      halfHeight: size[1] / 2,
    };
  }
  return { shape: "disc", radius: params.discDiameter / 2 };
}

/**
 * How wide the plate this stroke carries is drawn.
 *
 * Its own text when it has one — the mark is about to name everything it
 * touches, so a name that is not showing yet is still a name that will be.
 *
 * Zero when it carries none, and that is a real answer rather than a missing
 * one: a stroke with no plate has nothing to keep clear of anything, so it
 * takes no part in the spread. It used to claim a plate's height anyway, on
 * the reasoning that a bare line crossing a name is also worth avoiding — but
 * a plate is drawn on its own opaque ground and covers the line it crosses, so
 * that bought nothing and spent deflection on strokes with nothing to say.
 */
function plateWidth(
  style: Record<string, unknown> | undefined,
  params: MarkParams,
): number {
  const text = style?.labelText;
  return typeof text === "string" && text ? chipWidth(text, params) : 0;
}

/**
 * The angle each of the held mark's strokes leaves on, once spread.
 *
 * Strokes to the *same* neighbour are one group with one angle. Several claims
 * between the same two referents are drawn on one filament — the first strokes
 * it, the rest ride it with their plates stacked along its normal, and the
 * observer's count rides it too. Spreading them individually would fan one
 * line into several and invent a geometry the tuples do not have.
 */
export function planSpread(
  graph: Graph,
  heldId: string,
  params: MarkParams,
): Map<string, FanWaypoint> {
  const out = new Map<string, FanWaypoint>();
  const held = positionOf(graph, heldId);
  if (!held) return out;
  const heldRim = rimOf(graph, heldId, params);

  const groups = new Map<
    string,
    {
      members: { id: string; fromSource: boolean }[];
      angle: number;
      along: number;
      /**
       * The held mark's own rim on this bearing. A disc's is the same in every
       * direction; a held plate's is not, and a fan that used one number for
       * all of them would start its strokes inside the mark on some bearings
       * and outside it on others.
       */
      heldRadius: number;
      /** The widest name this stroke will carry, which is what has to clear. */
      plate: number;
    }
  >();
  for (const edge of graph.getRelatedEdgesData(heldId)) {
    const fromSource = String(edge.source) === heldId;
    const otherId = fromSource ? String(edge.target) : String(edge.source);
    const member = { id: String(edge.id), fromSource };
    const plate = plateWidth(edge.style as Record<string, unknown> | undefined, params);
    const standing = groups.get(otherId);
    if (standing) {
      standing.members.push(member);
      standing.plate = Math.max(standing.plate, plate);
      continue;
    }
    const other = positionOf(graph, otherId);
    if (!other) continue;
    const dx = other.x - held.x;
    const dy = other.y - held.y;
    const centres = Math.hypot(dx, dy);
    const heldRadius = rimDistance(heldRim, dx, dy);
    const filament =
      centres - heldRadius - rimDistance(rimOf(graph, otherId, params), dx, dy);
    // Nothing to fan along: the two marks are all but touching, and an elbow
    // between them would be a corner with no stroke on either side of it.
    if (!(filament > 4)) continue;
    groups.set(otherId, {
      members: [member],
      angle: Math.atan2(dy, dx),
      // The same station `bondLabelAlong` gives the resting plate, so the
      // spread moves a name sideways and never outward.
      along: Math.min(BOND_LABEL_ALONG_PX, filament / 2),
      heldRadius,
      plate,
    });
  }
  /**
   * Only the strokes carrying a name are in the fan.
   *
   * The fan exists to stop two names sitting on each other, so a stroke with
   * no name neither asks for room nor has to give any, and one that is never
   * moved is one whose neighbour is still exactly where the drawing says. With
   * fewer strokes competing the rest also settle nearer their true bearings,
   * so this makes the spread smaller twice over.
   */
  const keys = [...groups.keys()].filter((key) => groups.get(key)!.plate > 0);
  if (keys.length < 2) return out;

  const spread = spreadAngles(
    keys.map((key) => {
      const group = groups.get(key)!;
      return {
        angle: group.angle,
        halfWidth: (group.plate + BOND_LABEL_STACK_GAP) / 2,
        halfHeight: (params.chipHeight + BOND_LABEL_STACK_GAP) / 2,
        station: group.heldRadius + group.along,
      };
    }),
    SPREAD_MAX_DEFLECT,
  );
  for (let i = 0; i < keys.length; i += 1) {
    const group = groups.get(keys[i])!;
    const angle = spread[i];
    const deflect = Math.abs(wrapAngle(angle - group.angle));
    if (deflect * (group.heldRadius + group.along) < SPREAD_SKIP_PX) continue;
    for (const member of group.members) {
      out.set(member.id, {
        angle,
        along: group.along,
        fromSource: member.fromSource,
        deflect,
      });
    }
  }
  return out;
}

/* ------------------------------------------------------------------ *
 * The field
 * ------------------------------------------------------------------ */

export type SpreadField = {
  /** State what is held. `null` puts every stroke back on its chord. */
  commit: (heldId: string | null) => void;
  /** A pointer owns the field: drop the fan until it lets go. */
  suspend: () => void;
  dispose: () => void;
};

export function createSpreadField(options: {
  graph: Graph;
  params: () => MarkParams;
  motion: () => MotionPlans;
  enabled: () => boolean;
  reduced: () => boolean;
}): SpreadField {
  const { graph } = options;
  let frame = 0;
  const amounts = new Map<string, number>();
  const anims = new Map<
    string,
    { from: number; to: number; started: number; plan: MotionPlan }
  >();
  const standing = new Set<string>();
  const targets = new Map<string, FanWaypoint>();

  const apply = () => {
    if (graph.destroyed) return;
    const ids = new Set([
      ...amounts.keys(),
      ...anims.keys(),
      ...standing,
      ...targets.keys(),
    ]);
    if (!ids.size) return;
    const patches: FilamentFanPatch[] = [];
    for (const id of ids) {
      const amount = amounts.get(id) ?? 0;
      const target = targets.get(id);
      if (amount < 0.02 && !standing.has(id)) {
        amounts.delete(id);
        targets.delete(id);
      }
      patches.push({
        id,
        amount,
        angle: target?.angle ?? 0,
        along: target?.along ?? 0,
        fromSource: target?.fromSource ?? true,
      });
    }
    updateFilamentFans(graph, patches);
  };

  const forget = () => {
    if (frame) {
      cancelAnimationFrame(frame);
      frame = 0;
    }
    anims.clear();
    standing.clear();
    amounts.clear();
    targets.clear();
  };

  const snapOff = () => {
    forget();
    if (!graph.destroyed) clearFilamentFans(graph);
  };

  const tick = (now: number) => {
    frame = 0;
    let running = false;
    for (const [id, anim] of anims) {
      const value =
        anim.from + (anim.to - anim.from) * anim.plan.sample(now - anim.started);
      if (now - anim.started >= anim.plan.durationMs) {
        amounts.set(id, anim.to);
        anims.delete(id);
        if (anim.to < 0.02) amounts.delete(id);
      } else {
        amounts.set(id, value);
        running = true;
      }
    }
    apply();
    if (running && !graph.destroyed) frame = requestAnimationFrame(tick);
  };

  const aim = (id: string, to: number) => {
    const from = amounts.get(id) ?? 0;
    if (Math.abs(from - to) < 0.02 && !anims.has(id)) {
      amounts.set(id, to);
      if (to < 0.02) amounts.delete(id);
      return;
    }
    if (options.reduced()) {
      anims.delete(id);
      if (to < 0.02) amounts.delete(id);
      else amounts.set(id, to);
      return;
    }
    const plans = options.motion();
    anims.set(id, {
      from,
      to,
      started: performance.now(),
      // A stroke opening out is matter leaving its rest and returning to it,
      // so it takes the same two curves everything else on this canvas does —
      // and the lab slowing the spine slows this with it.
      plan: to > from ? plans.emit : plans.absorb,
    });
  };

  const commit = (heldId: string | null) => {
    if (graph.destroyed) return;
    if (!options.enabled()) {
      if (amounts.size || targets.size || standing.size) snapOff();
      return;
    }
    const next =
      heldId && standingNode(graph, heldId)
        ? planSpread(graph, heldId, options.params())
        : new Map<string, FanWaypoint>();
    standing.clear();
    for (const [id, waypoint] of next) {
      standing.add(id);
      targets.set(id, waypoint);
      aim(id, 1);
    }
    for (const id of [...targets.keys()]) {
      if (!next.has(id)) aim(id, 0);
    }
    apply();
    if (options.reduced()) return;
    if (!frame && anims.size) frame = requestAnimationFrame(tick);
  };

  return { commit, suspend: snapOff, dispose: forget };
}
