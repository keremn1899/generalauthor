/**
 * A live field, for the lab: links slacken, neighbours yield, nothing wanders.
 *
 * `relax.ts` is the product's settling — one pass over newly arrived matter,
 * no renderer attached, over before anybody sees it. This is the other thing
 * you might want from the same solver: wake it under a held mark, so that mark
 * tugs what it is joined to and the neighbourhood gives a little instead of
 * standing rigid. It is more fun. It is also a surface that moves marks
 * nobody touched, which is why it lives behind a lab switch and is off unless
 * somebody asks for it.
 *
 * ## The shape of one session
 *
 * A session of physics is a press, a drag and a release, and the field's whole
 * life is inside it.
 *
 * **Press frees everything and fixes one thing.** Every standing mark becomes a
 * free body: none is carrying a pin from an earlier session, none is quietly
 * exempt from collision, and the same forces apply to all of them. The one
 * exception is the mark under the pointer, which is fixed to the pointer,
 * because that is what direct manipulation means.
 *
 * **A hold runs at constant energy.** `holdEnergy` is both the alpha and the
 * alpha target, so there is no decay schedule to reason about under the hand:
 * the field is exactly as lively on the fifth second of a drag as on the first.
 *
 * **Release settles; it does not pause.** The alpha target drops to zero and
 * the decay is solved from `settleMs`, so the field spends a few tens of frames
 * coming to rest and then d3's own timer stops. Damping rises for the tail, so
 * the last frames are motion dying rather than motion cut. What a release must
 * never do is move the mark you just placed: it stays fixed where the pointer
 * left it, through the settle and through the quiet after it. That fix lasts
 * exactly until the next press, which frees it along with everything else.
 *
 * **Nothing else ever starts it.** A redraw marks the body set stale and the
 * next press pays for the rebuild. No reheat on new matter, no timer behind a
 * field nobody is touching, and a field at rest costs zero. It is also why the
 * solver may read positions straight out of the renderer when a press arrives:
 * that is the one moment nothing else is moving them.
 *
 * ## The forces
 *
 * The character is `glide-loose` from the old field's presets: link-only slack,
 * connected neighbours yield, unrelated marks stay still.
 *
 * **Links and collision only.** No `manyBody`, so a mark never feels one it is
 * not joined to; no `center`, so the neighbourhood does not creep toward the
 * middle of the viewport every time it grows. Those are the two forces whose
 * reach is bounded by construction, and they are the same two `relax.ts`
 * allows itself, for the same reason.
 *
 * **A link is slack, not a spring.** Strength 0.07 over a 260px rest length:
 * far enough below d3's default that a dragged mark pulls its neighbours along
 * rather than snapping them to a radius. There is no elasticity to feel,
 * because elasticity is the field having an opinion about where a mark *ought*
 * to be, and it does not get one.
 *
 * **Collision is hard.** Strength 1 over three passes with a radius reserve, so
 * marks do not visibly overlap — and every body is subject to it, the fixed one
 * included. A fixed body pushes and is not pushed; it is never exempt.
 *
 * Positions are written straight to the elements, never through `setData`: a
 * tick is a position change on standing marks, which is the case a full redraw
 * charges a whole field of animation set-up to express. See `canvasMotion.ts`.
 */

import {
  forceCollide,
  forceLink,
  forceSimulation,
  type Simulation,
  type SimulationLinkDatum,
  type SimulationNodeDatum,
} from "d3-force";
import type { Graph } from "@antv/g6";

export type DriftTuning = {
  linkDistance: number;
  linkStrength: number;
  collidePadding: number;
  collideIterations: number;
  velocityDecay: number;
  /** Alpha held constant while a mark is under the pointer. */
  holdEnergy: number;
  /** How long the field takes to come to rest after the pointer lets go. */
  settleMs: number;
};

/**
 * Link-only slack. The important cost/feel controls are surfaced in World Lab.
 *
 * Three collision passes are three quadtree traversals per tick — the largest
 * solver term, and the one worth spending on, because a pass that leaves marks
 * overlapping did not do the only job collision has. The 12px radius reserve
 * absorbs the soft residual between passes.
 */
export const DRIFT_TUNING: DriftTuning = {
  linkDistance: 260,
  linkStrength: 0.07,
  collidePadding: 12,
  collideIterations: 3,
  velocityDecay: 0.5,
  holdEnergy: 0.2,
  settleMs: 260,
};

/**
 * The alpha the field is called settled at, and the frame a settle is counted
 * in. Both live here rather than in the tuning because they are the units a
 * settle is *expressed* in, not choices about how it feels. What a person tunes
 * is how long it takes, and `settleMs` says that in milliseconds.
 */
const REST_ALPHA = 0.015;
const FRAME_MS = 1000 / 60;

type Body = SimulationNodeDatum & {
  id: string;
  radius: number;
  x: number;
  y: number;
};
type Link = SimulationLinkDatum<Body>;

export type DriftField = {
  /** Topology or placement changed: the body set is stale, rebuild it lazily. */
  sync: () => void;
  /** A pointer owns this mark now: free the field and start the clock. */
  hold: (id: string) => void;
  /** Where the pointer has it, this frame. */
  drag: (id: string, x: number, y: number) => void;
  /** The pointer let go: settle, leaving this mark where it was put. */
  drop: (id: string) => void;
  setEnabled: (on: boolean) => void;
  dispose: () => void;
};

/** Furniture rides its mark and plates ride their spokes; neither is a body. */
function isFurniture(id: string) {
  return id.startsWith("crown:") || id.startsWith("shelf:");
}

function radiusOf(graph: Graph, id: string): number {
  try {
    const size = graph.getNodeData(id)?.style?.size;
    if (typeof size === "number") return size / 2;
    if (Array.isArray(size) && typeof size[0] === "number") {
      return Math.max(size[0], Number(size[1] ?? size[0])) / 2;
    }
  } catch {
    /* not standing yet */
  }
  return 45;
}

export function createDriftField(options: {
  graph: Graph;
  enabled: () => boolean;
  tuning?: () => Partial<DriftTuning>;
  /** Where the canvas keeps the positions it will redraw from. */
  publish: (moved: ReadonlyMap<string, { x: number; y: number }>) => void;
}): DriftField {
  const { graph, publish } = options;
  let sim: Simulation<Body, Link> | null = null;
  let bodies = new Map<string, Body>();
  /** The mark under the pointer, or the one the last release left in place. */
  let fixed: string | null = null;
  let held: string | null = null;
  let stale = true;
  let disposed = false;

  const tuning = (): DriftTuning => ({
    ...DRIFT_TUNING,
    ...options.tuning?.(),
  });

  const stop = () => {
    sim?.stop();
    sim = null;
    stale = true;
  };

  const write = () => {
    if (disposed || graph.destroyed) return;
    // D3 retains this map for the life of the topology. The canvas consumes it
    // synchronously, so a tick allocates no snapshot objects or map.
    if (bodies.size) publish(bodies);
  };

  const positionOf = (id: string): [number, number] | null => {
    const at = graph.destroyed ? null : graph.getElementPosition(id);
    return at && Number.isFinite(at[0]) && Number.isFinite(at[1])
      ? [at[0], at[1]]
      : null;
  };

  /**
   * Take the renderer's word for where everything is, and release every body.
   *
   * The renderer is the only authority on position: a mark may have been
   * re-placed by an arrangement, rounded on its way through the store, or moved
   * by a drag this solver never saw. Reading it back at the start of every
   * session is what keeps the physics the same physics each time, rather than
   * something that drifts away from the picture by whatever the last session
   * happened to leave behind.
   */
  const refresh = () => {
    for (const body of bodies.values()) {
      const at = positionOf(body.id);
      if (at) {
        body.x = at[0];
        body.y = at[1];
      }
      body.radius = radiusOf(graph, body.id);
      body.vx = 0;
      body.vy = 0;
      body.fx = null;
      body.fy = null;
    }
    fixed = null;
  };

  const build = () => {
    if (disposed || graph.destroyed) return;
    const next = new Map<string, Body>();
    for (const node of graph.getNodeData()) {
      const id = String(node.id);
      if (isFurniture(id)) continue;
      const at = positionOf(id);
      const body: Body = bodies.get(id) ?? {
        id,
        x: at?.[0] ?? 0,
        y: at?.[1] ?? 0,
        radius: 45,
      };
      next.set(id, body);
    }
    bodies = next;
    refresh();

    const links: Link[] = [];
    const joined = new Set<string>();
    for (const edge of graph.getEdgeData()) {
      const source = bodies.get(String(edge.source));
      const target = bodies.get(String(edge.target));
      if (!source || !target || source === target) continue;
      // Parallel assertions and their summary edge are one physical
      // relationship. Counting each renderer edge as another spring both
      // multiplies work and makes that pair artificially rigid.
      const key =
        source.id < target.id
          ? `${source.id}|${target.id}`
          : `${target.id}|${source.id}`;
      if (joined.has(key)) continue;
      joined.add(key);
      links.push({ source, target });
    }

    const tune = tuning();
    sim?.stop();
    sim = forceSimulation<Body, Link>([...bodies.values()])
      .force(
        "link",
        forceLink<Body, Link>(links)
          .id((body) => body.id)
          .distance(tune.linkDistance)
          .strength(tune.linkStrength),
      )
      .force(
        "collide",
        forceCollide<Body>()
          .radius((body) => body.radius + tune.collidePadding)
          .strength(1)
          .iterations(Math.max(1, Math.round(tune.collideIterations))),
      )
      .alphaMin(REST_ALPHA)
      .alphaTarget(0)
      .alpha(0)
      .stop()
      .on("tick", write);
    stale = false;
  };

  /** Fix one body where it stands, releasing whatever was fixed before it. */
  const fix = (id: string, at?: { x: number; y: number }) => {
    if (fixed && fixed !== id) {
      const previous = bodies.get(fixed);
      if (previous) {
        previous.fx = null;
        previous.fy = null;
      }
    }
    fixed = id;
    const body = bodies.get(id);
    if (!body) return;
    body.fx = at?.x ?? body.x;
    body.fy = at?.y ?? body.y;
  };

  return {
    sync() {
      if (disposed) return;
      // Nothing wakes on a redraw. The next press pays for the rebuild, which
      // is also the only moment the positions it reads are the ones on screen.
      stale = true;
      if (!held) sim?.stop();
    },
    hold(id) {
      if (disposed || !options.enabled()) return;
      // Pointer-down and G6's drag-start both announce the same hand. The
      // second must not re-read the field mid-gesture: this mark is already
      // the one that is fixed, and the session is already running.
      if (held === id && sim) return;
      if (!sim || stale) build();
      else refresh();
      const body = bodies.get(id);
      if (!body || !sim) return;
      held = id;
      // `refresh` has already released every body, the one the last release
      // left standing included. A session opens with the field entirely free
      // and exactly one thing fixed: the mark in the hand.
      fix(id);
      const tune = tuning();
      sim
        .velocityDecay(tune.velocityDecay)
        // Constant energy under the hand: nothing to schedule, and nothing
        // that quietly runs down while a person is still working.
        .alphaDecay(0)
        .alphaTarget(tune.holdEnergy)
        .alpha(tune.holdEnergy)
        .restart();
    },
    drag(id, x, y) {
      if (disposed || !options.enabled() || held !== id) return;
      const body = bodies.get(id);
      if (!body) return;
      body.fx = x;
      body.fy = y;
    },
    drop(id) {
      // Pointer-up and G6's drag-end can describe the same release. Only the
      // active hand may settle the field, so that pair stays idempotent.
      if (disposed || held !== id) return;
      held = null;
      const body = bodies.get(id);
      const at =
        body?.fx != null && body.fy != null
          ? { x: body.fx, y: body.fy }
          : (() => {
              const point = positionOf(id);
              return point ? { x: point[0], y: point[1] } : null;
            })();
      // The mark stays exactly where the pointer left it — through the settle
      // and through the quiet after it. Nothing about link length is allowed
      // to walk it back; the next press is what hands it to the field again.
      if (at && body) {
        body.x = at.x;
        body.y = at.y;
        body.vx = 0;
        body.vy = 0;
      }
      fix(id, at ?? undefined);
      if (!sim) return;
      const tune = tuning();
      const from = Math.max(sim.alpha(), tune.holdEnergy);
      const ticks = Math.max(1, Math.round(tune.settleMs / FRAME_MS));
      sim
        .alphaTarget(0)
        // Solve the decay from the time asked for: alpha falls from `from` to
        // the rest threshold over `ticks` frames, and then d3's timer stops on
        // its own. A settle is a duration a person can feel, not a rate.
        .alphaDecay(1 - Math.pow(REST_ALPHA / from, 1 / ticks))
        .alpha(from)
        // Damp the tail harder than the hold, so the end of it is momentum
        // running out rather than a frame where motion stopped.
        .velocityDecay(Math.min(0.92, tune.velocityDecay + 0.2))
        .restart();
    },
    setEnabled(on) {
      if (disposed) return;
      held = null;
      fixed = null;
      stop();
      if (!on) bodies = new Map();
    },
    dispose() {
      disposed = true;
      stop();
      bodies = new Map();
    },
  };
}
