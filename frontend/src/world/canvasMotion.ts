/**
 * Element lifecycle for World canvases.
 *
 * A mark enters from a 4% nucleation pin at its authored position and leaves
 * by being absorbed back into it. Edges have no centre to scale around, so
 * they release through opacity. Both consume the shared motion plans.
 *
 * Only identity arriving or leaving is animated. Marks that were already on
 * the field are written directly, because `STILL_RULES.marksNeverMove`: a
 * field that re-poses what is already standing has moved something nobody
 * asked it to move. Drag release is the same rule — the mark stays exactly
 * where the pointer left it, with no settle.
 */

import type { Graph } from "@antv/g6";
import {
  DEFAULT_MOTION_PLANS,
  NODE_BIRTH_PLAN,
  NODE_COLLAPSE_PLAN,
  staggerWaves,
  type MotionPlan,
} from "../styles/motion";

export type CanvasDatum = {
  id: string;
  source?: string;
  target?: string;
  style?: Record<string, unknown>;
};

export type CanvasData = {
  nodes: CanvasDatum[];
  edges: CanvasDatum[];
};

export type CanvasTransition = {
  bornNodes: CanvasDatum[];
  bornEdges: CanvasDatum[];
  diedNodeIds: string[];
  diedEdgeIds: string[];
};

export type CanvasMotionOptions = {
  /** Present in the working set but hidden by an observer filter. */
  retainedNode?: (id: string) => boolean;
  /** Already belonged to the working field before becoming visible again. */
  returningNode?: (id: string) => boolean;
  /** A constraint hidden and restored by the observer rather than admitted. */
  returningEdge?: (id: string) => boolean;
  /** Observer reveal, distinct from massive-node nucleation. */
  revealPlan?: MotionPlan;
  appearancePlan?: MotionPlan;
  /** The small assertion plates carried as edge labels. */
  labelPlan?: MotionPlan;
  /** Retained for callers that want the canonical massive-node plans. */
  stellarNodes?: boolean;
  /** Lab-scaled forms of the same laws, when supplied. */
  birthPlan?: MotionPlan;
  collapsePlan?: MotionPlan;
  releasePlan?: MotionPlan;
  /** Shared-spine time before a newly nucleated body can bind constraints. */
  bindingDelayMs?: number;
  /** Lab-scaled window across an expansion's distance waves. */
  staggerWindowMs?: number;
};

const LIFECYCLE_SCALE = 0.04;

function scaledSize(size: unknown, scale: number): unknown {
  if (typeof size === "number") return size * scale;
  if (
    Array.isArray(size) &&
    size.length === 2 &&
    size.every((part) => typeof part === "number")
  ) {
    return [size[0] * scale, size[1] * scale];
  }
  return size;
}

function nodePose(
  node: CanvasDatum,
  opacity: number,
  scale: number,
): CanvasDatum {
  const size = scaledSize(node.style?.size, scale);
  return {
    ...node,
    style: {
      ...node.style,
      opacity,
      ...(size === undefined ? {} : { size }),
    },
  };
}

function edgeOpacity(edge: CanvasDatum, opacity: number): CanvasDatum {
  return { ...edge, style: { ...edge.style, opacity } };
}

function planOptions(plan: MotionPlan) {
  return {
    duration: plan.durationMs,
    easing: plan.easing.g6,
  };
}

/**
 * The channels a stage is allowed to move, restated because G6 will not.
 *
 * The base theme animates position and colour on update and nothing else —
 * `[{ fields: ['x','y','fill','stroke'] }]` for a node, `sourceNode`,
 * `targetNode` and `stroke` for an edge. Every channel this surface actually
 * writes meaning into is opacity: occlusion is `opacity`, a name arriving is
 * `labelOpacity`, and light is `fillOpacity` and `strokeOpacity`. A stage that
 * does not name them applies them on the next frame instead — the observer's
 * shutter snaps shut rather than closing, and a mark two hops from the pointer
 * flashes rather than lifts.
 *
 * `size` is the other one, and it is mass rather than light: a body absorbed
 * into its 4% nucleation pin has to be seen contracting into it, or the pin is
 * just a smaller body that appeared where the old one was. Unstated, arrival
 * and withdrawal both read as a cut.
 *
 * `setOptions` replaces this block rather than merging into it, so the theme's
 * own fields are restated alongside. Dropping `x`/`y` or `sourceNode`/
 * `targetNode` would let a filament leave the body it is bound to mid-stage,
 * and dropping `stroke` would take the status cross-fade with it.
 */
function nodeUpdateAnimation(plan: MotionPlan) {
  return {
    animation: {
      update: [
        {
          fields: [
            "x",
            "y",
            "size",
            "fill",
            "stroke",
            "opacity",
            "fillOpacity",
            "strokeOpacity",
          ],
          ...planOptions(plan),
        },
      ],
    },
  };
}

function edgeUpdateAnimation(keyPlan: MotionPlan, labelPlan = keyPlan) {
  return {
    animation: {
      update: [
        { fields: ["sourceNode", "targetNode"], ...planOptions(keyPlan) },
        {
          fields: ["opacity", "stroke", "strokeOpacity"],
          shape: "key",
          ...planOptions(keyPlan),
        },
        // A name leaves with the constraint that carried it, on its own plan:
        // a label is read rather than lit, so it states its arrival at `emit`
        // while the filament under it releases at whatever the stage is.
        {
          fields: ["opacity"],
          shape: "label",
          ...planOptions(labelPlan),
        },
      ],
    },
  };
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

function pointOf(datum: CanvasDatum): { x: number; y: number } | null {
  const x = datum.style?.x;
  const y = datum.style?.y;
  if (typeof x !== "number" || typeof y !== "number") return null;
  return { x, y };
}

function centroid(points: { x: number; y: number }[]): { x: number; y: number } | null {
  if (!points.length) return null;
  return {
    x: points.reduce((sum, point) => sum + point.x, 0) / points.length,
    y: points.reduce((sum, point) => sum + point.y, 0) / points.length,
  };
}

/**
 * Where the new matter grew out of.
 *
 * Not passed in, derived: the marks an expansion attaches to are exactly the
 * *existing* endpoints of the arriving edges, and their centroid is the
 * anchor. That keeps the stagger a property of the change rather than of the
 * caller, so it is right for a table row focus and a fold as well as for an
 * expansion. A first load has no such endpoints; then the arrival radiates
 * from the middle of itself, which is the only centre it has.
 */
function anchorOf(
  bornNodes: CanvasDatum[],
  bornEdges: CanvasDatum[],
  standing: Map<string, CanvasDatum>,
): { x: number; y: number } | null {
  const roots: { x: number; y: number }[] = [];
  for (const edge of bornEdges) {
    for (const end of [edge.source, edge.target]) {
      const held = end ? standing.get(end) : undefined;
      const point = held ? pointOf(held) : null;
      if (point) roots.push(point);
    }
  }
  return (
    centroid(roots) ??
    centroid(bornNodes.map(pointOf).filter((point): point is { x: number; y: number } => Boolean(point)))
  );
}

function reducedMotion(): boolean {
  try {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  } catch {
    return false;
  }
}

/**
 * Reconcile data with one authored lifecycle.
 *
 * Existing marks update directly because hover and naming are pointer-direct.
 * Only identity entering or leaving gets an autonomous motion.
 */
export async function transitionCanvasData(
  graph: Graph,
  next: CanvasData,
  cancelled: () => boolean,
  options: CanvasMotionOptions = {},
): Promise<CanvasTransition> {
  const previousNodes = new Set(
    graph.getNodeData().map((node) => String(node.id)),
  );
  const previousEdges = new Set(
    graph.getEdgeData().map((edge) => String(edge.id)),
  );
  const nextNodeIds = new Set(next.nodes.map((node) => node.id));
  const nextEdgeIds = new Set(next.edges.map((edge) => edge.id));
  const bornNodes = next.nodes.filter((node) => !previousNodes.has(node.id));
  const bornEdges = next.edges.filter((edge) => !previousEdges.has(edge.id));
  const diedNodeIds = [...previousNodes].filter((id) => !nextNodeIds.has(id));
  const diedEdgeIds = [...previousEdges].filter((id) => !nextEdgeIds.has(id));

  if (reducedMotion()) {
    if (cancelled() || graph.destroyed) {
      return { bornNodes, bornEdges, diedNodeIds, diedEdgeIds };
    }
    graph.setOptions({ animation: false });
    graph.setData(next as never);
    await graph.draw();
    return { bornNodes, bornEdges, diedNodeIds, diedEdgeIds };
  }

  const departingNodes = diedNodeIds
    .map((id) => graph.getNodeData(id))
    .filter(Boolean)
    .map((node) => node as CanvasDatum);
  const occludedNodes = departingNodes.filter((node) =>
    options.retainedNode?.(node.id),
  );
  const removedNodes = departingNodes.filter((node) =>
    !options.retainedNode?.(node.id),
  );
  const hiddenNodes = occludedNodes.map((node) => nodePose(node, 0, 1));
  const collapsedNodes = removedNodes.map((node) =>
    nodePose(node, 0, LIFECYCLE_SCALE),
  );
  const dyingEdges = diedEdgeIds
    .map((id) => graph.getEdgeData(id))
    .filter(Boolean)
    .map((edge) => edgeOpacity(edge as CanvasDatum, 0));
  const entering: CanvasData = {
    nodes: next.nodes.map((node) =>
      previousNodes.has(node.id)
        ? node
        : nodePose(node, 0, options.returningNode?.(node.id) ? 1 : LIFECYCLE_SCALE),
    ),
    edges: next.edges.map((edge) =>
      previousEdges.has(edge.id) ? edge : edgeOpacity(edge, 0),
    ),
  };
  const returningNodes = bornNodes.filter((node) =>
    options.returningNode?.(node.id),
  );
  const arrivingNodes = bornNodes.filter((node) =>
    !options.returningNode?.(node.id),
  );
  const returningEdges = bornEdges.filter((edge) =>
    options.returningEdge?.(edge.id),
  );
  const arrivingEdges = bornEdges.filter((edge) =>
    !options.returningEdge?.(edge.id),
  );

  /**
   * Every `await` here is a place the canvas can be unmounted under us.
   *
   * `graph.draw()` resolves a frame or more later, and by then the vocabulary
   * toggle may have destroyed the schema canvas — G6 logs "the graph instance
   * has been destroyed" for each call that lands afterwards. The checks after
   * each await were there; the ones *before* the next call were not, so a
   * destroy that happened during an await was caught one statement too late.
   */
  const gone = () => cancelled() || graph.destroyed;
  if (gone()) return { bornNodes, bornEdges, diedNodeIds, diedEdgeIds };

  /**
   * Withdrawal has an order because a constraint cannot remain visibly bound
   * to matter that has already ceased to occupy the field. Release the
   * departing constraints first while their endpoints still stand.
   */
  if (dyingEdges.length || hiddenNodes.length) {
    const releasePlan = options.releasePlan ?? DEFAULT_MOTION_PLANS.absorb;
    graph.setOptions({
      animation: planOptions(releasePlan),
      node: nodeUpdateAnimation(releasePlan),
      edge: edgeUpdateAnimation(releasePlan),
    });
    graph.setData({
      // A filter is one observer shutter: retained matter and its light fade
      // together at full size. Explicitly removed mass stays standing until
      // its constraints have released in this same stage.
      nodes: [...entering.nodes, ...removedNodes, ...hiddenNodes],
      edges: [...entering.edges, ...dyingEdges],
    } as never);
    await graph.draw();
    if (gone()) return { bornNodes, bornEdges, diedNodeIds, diedEdgeIds };
    graph.setOptions({ animation: false });
  }

  /** Only after its constraints have released may a departing mass collapse. */
  if (collapsedNodes.length) {
    const collapsePlan =
      options.collapsePlan ??
      (options.stellarNodes ? NODE_COLLAPSE_PLAN : DEFAULT_MOTION_PLANS.absorb);
    // Its own channels, not the release stage's. `setOptions` leaves the
    // previous `node` block standing, so a collapse that did not state one
    // contracted at whatever plan released the constraints a moment earlier —
    // the mass reading its own withdrawal at the speed of a filament's.
    graph.setOptions({
      animation: planOptions(collapsePlan),
      node: nodeUpdateAnimation(collapsePlan),
    });
    graph.setData({
      nodes: [...entering.nodes, ...collapsedNodes],
      edges: entering.edges,
    } as never);
    await graph.draw();
    if (gone()) return { bornNodes, bornEdges, diedNodeIds, diedEdgeIds };
    graph.setOptions({ animation: false });
  }

  if (gone()) return { bornNodes, bornEdges, diedNodeIds, diedEdgeIds };
  /**
   * Nothing is arriving or leaving, so this pass is only what the marks
   * *look* like — light lifting, a label appearing on a bond a person has
   * reached. Those ease.
   *
   * `marksNeverMove` is not in tension with it: this animates appearance, not
   * position, and a re-layout still cannot happen because none is being
   * asked for. Births and deaths keep their own plans below; only the
   * standing-still case gets `hold`, which is the shortest thing the spine
   * has and the one intended for a change that tracks a person rather than
   * announcing itself.
   */
  const settling =
    !bornNodes.length &&
    !bornEdges.length &&
    !collapsedNodes.length &&
    !dyingEdges.length;
  if (settling) {
    const appearancePlan = options.appearancePlan ?? DEFAULT_MOTION_PLANS.hold;
    const labelPlan = options.labelPlan ?? DEFAULT_MOTION_PLANS.emit;
    graph.setOptions({
      animation: planOptions(appearancePlan),
      node: nodeUpdateAnimation(appearancePlan),
      edge: edgeUpdateAnimation(appearancePlan, labelPlan),
    });
  }
  graph.setData(entering as never);
  await graph.draw();
  if (settling && !graph.destroyed) graph.setOptions({ animation: false });
  if (gone()) return { bornNodes, bornEdges, diedNodeIds, diedEdgeIds };

  /** Occluded matter returns as one field, without replaying nucleation. */
  if (returningNodes.length || returningEdges.length) {
    const returnPlan = options.revealPlan ?? DEFAULT_MOTION_PLANS.emit;
    graph.setOptions({
      animation: planOptions(returnPlan),
      node: nodeUpdateAnimation(returnPlan),
      edge: edgeUpdateAnimation(returnPlan),
    });
    if (returningNodes.length) {
      graph.updateNodeData(returningNodes.map(shown) as never);
    }
    if (returningEdges.length) {
      graph.updateEdgeData(returningEdges.map(shown) as never);
    }
    await graph.draw();
    if (!graph.destroyed) graph.setOptions({ animation: false });
    if (gone()) return { bornNodes, bornEdges, diedNodeIds, diedEdgeIds };
  }

  if (arrivingNodes.length || arrivingEdges.length) {
    const arrivalPlan =
      options.birthPlan ??
      (options.stellarNodes ? NODE_BIRTH_PLAN : DEFAULT_MOTION_PLANS.emit);
    graph.setOptions({
      animation: planOptions(arrivalPlan),
      node: nodeUpdateAnimation(arrivalPlan),
      edge: edgeUpdateAnimation(arrivalPlan),
    });

    const standing = new Map(
      next.nodes.filter((node) => previousNodes.has(node.id)).map((node) => [node.id, node]),
    );
    const anchor = anchorOf(arrivingNodes, arrivingEdges, standing);
    const distance = (node: CanvasDatum) => {
      const point = pointOf(node);
      if (!point || !anchor) return 0;
      return Math.hypot(point.x - anchor.x, point.y - anchor.y);
    };
    const { waves, stepMs } = staggerWaves(arrivingNodes, distance, {
      windowMs: options.staggerWindowMs,
    });
    const waveStepMs = Math.max(
      stepMs,
      arrivingNodes.length
        ? options.bindingDelayMs ?? DEFAULT_MOTION_PLANS.hold.durationMs
        : 0,
    );

    /**
     * An edge is drawn in the wave after the later of its ends.
     *
     * A filament that arrives before the disc it lands on reads as a line to
     * nowhere. Both ends already standing means the edge is the only new
     * thing, so it goes in the first wave with nothing to wait for.
     */
    const waveOfNode = new Map<string, number>();
    waves.forEach((wave, index) => {
      for (const node of wave) waveOfNode.set(node.id, index);
    });
    const waveOfEdge = (edge: CanvasDatum) =>
      Math.max(
        waveOfNode.get(edge.source ?? "") ?? -1,
        waveOfNode.get(edge.target ?? "") ?? -1,
      ) + 1;
    const edgeWaves: CanvasDatum[][] = Array.from(
      // One final wave lets a constraint bind only after its latest arriving
      // endpoint has become present. With no born nodes, a new edge between
      // standing bodies still belongs to the first and only wave.
      { length: waves.length ? waves.length + 1 : 1 },
      () => [],
    );
    for (const edge of arrivingEdges) {
      edgeWaves[Math.min(waveOfEdge(edge), edgeWaves.length - 1)].push(edge);
    }

    /**
     * The waves overlap on purpose, so they are started rather than awaited.
     *
     * Awaiting each draw would serialise the arrival into one full `emit` per
     * wave, and a ring of marks would take a second and a half to land. Each
     * wave touches a disjoint set of elements, so the draws do not contend
     * for the same matter; what the eye gets is a front crossing the new
     * region, which is the thing `stagger` was for.
     */
    const drawn: Promise<unknown>[] = [];
    for (let index = 0; index < edgeWaves.length; index += 1) {
      if (index > 0 && waveStepMs > 0) await sleep(waveStepMs);
      if (gone()) break;
      const nodeWave = waves[index] ?? [];
      if (nodeWave.length) {
        graph.updateNodeData(nodeWave.map(shown) as never);
      }
      const edgeWave = edgeWaves[index];
      if (edgeWave.length) {
        graph.updateEdgeData(edgeWave.map(shown) as never);
      }
      if (nodeWave.length || edgeWave.length) drawn.push(graph.draw());
    }
    await Promise.all(drawn);
    if (!graph.destroyed) graph.setOptions({ animation: false });
  }

  return { bornNodes, bornEdges, diedNodeIds, diedEdgeIds };
}

/** Restore the datum's own opacity — the pose it was authored at. */
function shown(datum: CanvasDatum): CanvasDatum {
  return {
    ...datum,
    style: {
      ...datum.style,
      opacity: (datum.style?.opacity as number | undefined) ?? 1,
    },
  };
}
