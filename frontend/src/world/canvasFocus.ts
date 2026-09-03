/**
 * Bring a mark into the visible remainder of the field.
 *
 * The product canvas flies with zoom (`flyCameraTo`). World pans only: the
 * neighborhood is already at the scale someone grew it to, and a table row
 * naming a mark that is already on the field should not re-frame the rest.
 *
 * The destination is the centre of what the overlays leave, not the centre of
 * the G6 host. Tables and the reader sit *over* the canvas rather than shrinking
 * it, so a fit to the host would land the mark under a panel.
 */

import { useEffect, useRef, type RefObject } from "react";
import type { Graph } from "@antv/g6";
import { DEFAULT_MOTION_PLANS, type MotionPlan } from "../styles/motion";

export type CameraInsets = {
  left: number;
  right: number;
  top: number;
  bottom: number;
};

const flights = new WeakMap<Graph, () => void>();

export function cancelPan(graph: Graph) {
  flights.get(graph)?.();
}

function hasNode(graph: Graph, id: string): boolean {
  try {
    return Boolean(graph.getNodeData(id));
  } catch {
    return false;
  }
}

function hasEdge(graph: Graph, id: string): boolean {
  try {
    return Boolean(graph.getEdgeData(id));
  } catch {
    return false;
  }
}

/**
 * The drawing's id for a mark the tables know by assertion, obligation, or
 * relation name. A binary assertion is `bond:<id>`; a schema plate is `rel:<name>`;
 * a filament keeps the relation name as its edge id.
 */
export function resolveFocusId(graph: Graph, id: string): string | null {
  if (hasNode(graph, id)) return id;
  if (!id.startsWith("rel:") && hasNode(graph, `rel:${id}`)) return `rel:${id}`;
  if (!id.startsWith("bond:") && hasEdge(graph, `bond:${id}`)) return `bond:${id}`;
  if (hasEdge(graph, id)) return id;
  return null;
}

function canvasPoint(graph: Graph, id: string): [number, number] | null {
  const position = graph.getElementPosition(id);
  if (position) return [position[0], position[1]];
  const edge = graph.getEdgeData(id);
  if (!edge) return null;
  const from = graph.getElementPosition(String(edge.source));
  const to = graph.getElementPosition(String(edge.target));
  if (!from || !to) return null;
  return [(from[0] + to[0]) / 2, (from[1] + to[1]) / 2];
}

function reducedMotion(): boolean {
  try {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  } catch {
    return false;
  }
}

export async function panToElement(
  graph: Graph,
  id: string,
  insets: CameraInsets,
  plan: MotionPlan = DEFAULT_MOTION_PLANS.settle,
): Promise<void> {
  const resolved = resolveFocusId(graph, id);
  if (!resolved) return;
  const target = canvasPoint(graph, resolved);
  if (!target) return;
  const [width, height] = graph.getSize();
  if (!width || !height) return;

  const visibleLeft = insets.left;
  const visibleRight = width - insets.right;
  const visibleTop = insets.top;
  const visibleBottom = height - insets.bottom;
  if (visibleRight - visibleLeft < 48 || visibleBottom - visibleTop < 48) return;

  const destX = (visibleLeft + visibleRight) / 2;
  const destY = (visibleTop + visibleBottom) / 2;
  const start = graph.getViewportByCanvas(target);
  const travelled = Math.hypot(destX - start[0], destY - start[1]);
  if (travelled < 2) return;

  cancelPan(graph);

  const cut = reducedMotion() || plan.durationMs <= 1;
  if (cut) {
    const now = graph.getViewportByCanvas(target);
    await graph.translateBy([destX - now[0], destY - now[1]], false);
    return;
  }

  await new Promise<void>((resolve) => {
    let frame = 0;
    let cancelled = false;
    const started = performance.now();
    const cancel = () => {
      cancelled = true;
      if (frame) cancelAnimationFrame(frame);
      resolve();
    };
    flights.set(graph, cancel);

    const step = () => {
      frame = 0;
      if (cancelled || graph.destroyed) {
        resolve();
        return;
      }
      const elapsed = performance.now() - started;
      const progress = Math.min(1, elapsed / plan.durationMs);
      const eased = plan.easing.sample(progress);
      const wantX = start[0] + (destX - start[0]) * eased;
      const wantY = start[1] + (destY - start[1]) * eased;
      const now = graph.getViewportByCanvas(target);
      const dx = wantX - now[0];
      const dy = wantY - now[1];
      if (dx || dy) {
        void graph.translateBy([dx, dy], false);
      }
      if (progress >= 1) {
        flights.delete(graph);
        resolve();
        return;
      }
      frame = requestAnimationFrame(step);
    };

    frame = requestAnimationFrame(step);
  });
}

/**
 * Fly to a mark after the renderer has it. Table placement often selects in
 * the same tick the tuple is folded in, so the first look can miss.
 */
export function useFocusPan(
  graphRef: RefObject<Graph | null>,
  ready: boolean,
  focusId: string | null | undefined,
  focusToken: number,
  insetsRef: RefObject<CameraInsets>,
) {
  const tokenRef = useRef(focusToken);
  useEffect(() => {
    if (!focusId || !focusToken) return;
    const graph = graphRef.current;
    if (!ready || !graph || graph.destroyed) return;
    tokenRef.current = focusToken;
    let cancelled = false;

    const present = (): string | null =>
      graph.destroyed ? null : resolveFocusId(graph, focusId);

    const run = async () => {
      let id = present();
      if (!id) {
        id = await new Promise<string | null>((resolve) => {
          let frames = 0;
          const finish = (found: string | null) => {
            graph.off("afterdraw", onDraw);
            resolve(found);
          };
          const onDraw = () => {
            const found = present();
            if (found) finish(found);
          };
          graph.on("afterdraw", onDraw);
          const tick = () => {
            if (cancelled || graph.destroyed) {
              finish(null);
              return;
            }
            const found = present();
            if (found) {
              finish(found);
              return;
            }
            frames += 1;
            if (frames > 45) {
              finish(null);
              return;
            }
            requestAnimationFrame(tick);
          };
          requestAnimationFrame(tick);
        });
      }
      if (cancelled || !id || tokenRef.current !== focusToken) return;
      await panToElement(graph, id, insetsRef.current);
    };

    void run();
    return () => {
      cancelled = true;
    };
  }, [focusId, focusToken, graphRef, insetsRef, ready]);
}
