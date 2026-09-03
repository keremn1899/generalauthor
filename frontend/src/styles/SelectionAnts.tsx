/**
 * Marching ants — the selection mark, carried over from the product canvas.
 *
 * The ancestor is `explorations/SelectionAntRing`, which the frozen product
 * graph still uses. Everything load-bearing about it is kept: a screen-space
 * SVG driven by graph-space coordinates, so the beads stay crisp through pan,
 * zoom and drag; a bead count locked to the *graph-space* path length, so mid
 * zoom keeps the same dotted look; a count that drops rather than letting beads
 * fuse, so the mark is never a solid outline; and arrival and departure on the
 * kernel's own `emit` and `absorb`, because a selection that fades in is a
 * thing that *became* selected where one that blinks is indistinguishable from
 * a redraw.
 *
 * What is new is that World IR has three kinds of mark and the ring only knew
 * one. A referent is a disc, so it takes a circle. An assertion standing on the
 * field is a plate, so it takes a rectangle with square corners — a rounded one
 * would be the only radius on the map. A binary assertion has no mark of its
 * own at all: it *is* the filament between two discs, so the beads march along
 * that line. In each case the ants trace the geometry the mark already has
 * rather than a shape imposed on it, which is the whole reason this reads as
 * selection and a halo reads as a smudge.
 *
 * That generalisation is why this is a second component rather than a prop on
 * the first. The ring draws a `<circle>`, and the product's stylesheet animates
 * `.gdna__ant-ring circle` by that element name; a path can express all three
 * shapes, and swapping the element would silently stop the frozen product's
 * beads from marching. The two are kept apart deliberately — see
 * `world/carryover.md`.
 */

import { useEffect, useRef, useState } from "react";
import type { Graph } from "@antv/g6";
import { motionPoseKeyframes, type MotionPlans } from "./motion";
import { useMotion } from "./useMotion";
import { chipWidth, MARK_DEFAULTS } from "../world/marks";
import "./selectionAnts.css";

/**
 * What to draw around, named by the mark's own geometry.
 *
 * The caller says which shape because only the caller knows what the mark
 * means: a disc is a circle because a referent is a mass, not because it
 * happens to measure square. Size comes from the renderer — a plate is as wide
 * as the word in it, and asking the graph is how the ants stay correct when
 * that word changes.
 */
/**
 * `clearance` is the air between the mark's edge and the beads, and it is per
 * target because one number cannot serve both marks: eleven units off a disc is
 * a quarter of its radius, and eleven off a plate ten units tall is more air
 * than plate. A mark is ringed at its own scale or the ring stops being its.
 */
export type AntTarget =
  | { shape: "circle"; id: string; diameter: number; clearance?: number }
  | { shape: "rect"; id: string; clearance?: number }
  | {
      shape: "edge-label";
      id: string;
      text?: string;
      trim?: number;
      clearance?: number;
    }
  /** An edge: `trim` is how much of each end is inside the mark it leaves. */
  | { shape: "line"; id: string; trim: number; clearance?: number };

type Traced = { d: string; screenLength: number; graphLength: number };

function trace(
  graph: Graph,
  target: AntTarget,
  clearance: number,
): Traced | null {
  const zoom = Math.max(0.05, graph.getZoom() || 1);
  const gap = (target.clearance ?? clearance) * zoom;
  const at = (id: string) => {
    const point = graph.getElementPosition(id);
    if (!point) return null;
    const view = graph.getViewportByCanvas(point);
    return { x: view[0], y: view[1] };
  };

  if (target.shape === "circle") {
    const centre = at(target.id);
    if (!centre) return null;
    const r = (target.diameter / 2) * zoom + gap;
    // Two half-arcs rather than a `<circle>`: one element has to be able to be
    // all three shapes, or the dash pattern and the march would each need a
    // per-shape branch in CSS as well as here.
    const d =
      `M ${centre.x - r} ${centre.y}` +
      ` A ${r} ${r} 0 1 0 ${centre.x + r} ${centre.y}` +
      ` A ${r} ${r} 0 1 0 ${centre.x - r} ${centre.y} Z`;
    const screenLength = 2 * Math.PI * r;
    return { d, screenLength, graphLength: screenLength / zoom };
  }

  if (target.shape === "rect") {
    const box = graph.getElementRenderBounds(target.id);
    if (!box) return null;
    const a = graph.getViewportByCanvas([box.min[0], box.min[1]]);
    const b = graph.getViewportByCanvas([box.max[0], box.max[1]]);
    const x0 = Math.min(a[0], b[0]) - gap;
    const x1 = Math.max(a[0], b[0]) + gap;
    const y0 = Math.min(a[1], b[1]) - gap;
    const y1 = Math.max(a[1], b[1]) + gap;
    const d = `M ${x0} ${y0} H ${x1} V ${y1} H ${x0} Z`;
    const screenLength = 2 * (x1 - x0 + (y1 - y0));
    return { d, screenLength, graphLength: screenLength / zoom };
  }

  if (target.shape === "edge-label") {
    const edge = graph.getEdgeData(target.id);
    if (!edge) return null;
    const from = at(String(edge.source));
    const to = at(String(edge.target));
    if (!from || !to) return null;
    const text =
      target.text ||
      (typeof edge.style?.labelText === "string" ? edge.style.labelText : "") ||
      "";
    if (text) {
      const midX = (from.x + to.x) / 2;
      const midY = (from.y + to.y) / 2;
      const plateWidth = chipWidth(text, MARK_DEFAULTS) * zoom;
      const plateHeight = MARK_DEFAULTS.chipHeight * zoom;
      const x0 = midX - plateWidth / 2 - gap;
      const x1 = midX + plateWidth / 2 + gap;
      const y0 = midY - plateHeight / 2 - gap;
      const y1 = midY + plateHeight / 2 + gap;
      const d = `M ${x0} ${y0} H ${x1} V ${y1} H ${x0} Z`;
      const screenLength = 2 * (x1 - x0 + (y1 - y0));
      return { d, screenLength, graphLength: screenLength / zoom };
    }
  }

  const edge = graph.getEdgeData(target.id);
  if (!edge) return null;
  const from = at(String(edge.source));
  const to = at(String(edge.target));
  if (!from || !to) return null;
  const span = Math.hypot(to.x - from.x, to.y - from.y);
  const trim =
    target.shape === "line"
      ? target.trim
      : (target.trim ?? MARK_DEFAULTS.discDiameter / 2);
  const inset = trim * zoom + gap;
  // A filament shorter than the two discs it joins has no free length to march
  // along, and beads drawn on it would sit inside the marks. Nothing is drawn
  // rather than something wrong; the lit palette still says what is selected.
  if (span <= inset * 2 + 8) return null;
  const ux = (to.x - from.x) / span;
  const uy = (to.y - from.y) / span;
  const x0 = from.x + ux * inset;
  const y0 = from.y + uy * inset;
  const x1 = to.x - ux * inset;
  const y1 = to.y - uy * inset;
  const screenLength = span - inset * 2;
  return {
    d: `M ${x0} ${y0} L ${x1} ${y1}`,
    screenLength,
    graphLength: screenLength / zoom,
  };
}

export function SelectionAnts({
  graph,
  target,
  clearance,
  dotGap,
  lineWidth,
  speed,
  color,
  motion,
  animated = true,
}: {
  graph: Graph | null;
  target: AntTarget | null;
  /** Default air between the mark's edge and the beads, in graph units. */
  clearance: number;
  /** Bead spacing along the path, in graph units. */
  dotGap: number;
  lineWidth: number;
  /** Screen pixels per second the beads travel; 0 holds them still. */
  speed: number;
  color: string;
  motion: MotionPlans;
  animated?: boolean;
}) {
  const [drawn, setDrawn] = useState<AntTarget | null>(target);
  const [arrival, setArrival] = useState(0);
  const held = useRef<AntTarget | null>(target);
  const pathRef = useRef<SVGPathElement | null>(null);
  const lifecycle = useMotion<SVGPathElement>();
  // The identity of what is selected, so the effects below fire when the
  // selection changes and not on every render of the canvas around them.
  const key = target ? JSON.stringify(target) : null;

  useEffect(() => {
    if (target) {
      held.current = target;
      setDrawn(target);
      setArrival((run) => run + 1);
      return;
    }
    if (!held.current) return;
    if (!animated) {
      held.current = null;
      setDrawn(null);
      return;
    }
    const leaving = lifecycle.play(
      motionPoseKeyframes({ scale: 1, opacity: 1 }, { scale: 0.86, opacity: 0 }),
      motion.absorb,
      {
        fill: "forwards",
        onFinish: () => {
          held.current = null;
          setDrawn(null);
        },
      },
    );
    if (!leaving) {
      held.current = null;
      setDrawn(null);
    }
    // `key` stands for `target`: the object is rebuilt every render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [animated, key, lifecycle, motion.absorb]);

  useEffect(() => {
    if (!animated || !arrival || !key || !drawn) return;
    lifecycle.play(
      motionPoseKeyframes({ scale: 0.86, opacity: 0 }, { scale: 1, opacity: 1 }),
      motion.emit,
      { fill: "both" },
    );
  }, [animated, arrival, drawn, key, lifecycle, motion.emit]);

  useEffect(() => {
    const path = pathRef.current;
    if (!graph || graph.destroyed || !drawn || !path) return;

    let frame = 0;
    let misses = 0;
    const update = () => {
      if (graph.destroyed) return;
      let traced: Traced | null = null;
      try {
        traced = trace(graph, drawn, clearance);
      } catch {
        traced = null;
      }
      if (!traced) {
        path.style.visibility = "hidden";
        // Placement often selects before the mark has been drawn. afterdraw
        // will retry; a few frames cover the gap when that event has already
        // fired with the node still missing.
        if (misses < 12) {
          misses += 1;
          frame = requestAnimationFrame(() => {
            frame = 0;
            update();
          });
        }
        return;
      }
      misses = 0;
      // Beads are counted on the path as it exists in the world, not as it is
      // currently magnified, so zooming moves the ants closer together on
      // screen without ever re-spacing them. The screen length only decides
      // when they would fuse.
      const wanted = Math.max(
        1,
        Math.round(traced.graphLength / Math.max(0.01, dotGap)),
      );
      const fits = Math.max(3, Math.floor(traced.screenLength / (lineWidth + 1)));
      const beads = Math.min(wanted, fits);
      const cycle =
        speed <= 0 ? 0 : Math.max(0.25, traced.screenLength / speed);
      path.setAttribute("d", traced.d);
      path.setAttribute("stroke-dasharray", `0 ${100 / beads}`);
      path.style.setProperty("--ants-cycle", cycle > 0 ? `${cycle}s` : "0s");
      path.style.visibility = "visible";
    };

    const schedule = () => {
      if (document.documentElement.classList.contains("is-panel-resizing")) {
        return;
      }
      if (frame) return;
      frame = requestAnimationFrame(() => {
        frame = 0;
        update();
      });
    };

    // Marching pauses while a mark is in hand. A selection ring travelling on
    // something the pointer is already moving is two motions describing one
    // event, and the drag is the one the person is causing.
    const grip = (grabbed: boolean) => () => {
      path.classList.toggle("is-held", grabbed);
    };
    const grab = grip(true);
    const release = grip(false);

    const observer = new ResizeObserver(schedule);
    const container = graph.getCanvas().getContainer();
    if (container) observer.observe(container);
    graph.on("node:dragstart", grab);
    graph.on("node:dragend", release);
    graph.on("node:drag", schedule);
    graph.on("aftertransform", schedule);
    graph.on("afterdraw", schedule);
    const classes = new MutationObserver(() => {
      if (document.documentElement.classList.contains("is-panel-resizing")) {
        return;
      }
      schedule();
    });
    classes.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["class"],
    });
    update();

    return () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
      classes.disconnect();
      graph.off("node:dragstart", grab);
      graph.off("node:dragend", release);
      graph.off("node:drag", schedule);
      graph.off("aftertransform", schedule);
      graph.off("afterdraw", schedule);
    };
  }, [clearance, dotGap, drawn, graph, lineWidth, speed]);

  if (!drawn) return null;

  return (
    <svg className="ants" style={{ color }} aria-hidden="true">
      <path
        ref={(element) => {
          pathRef.current = element;
          lifecycle.ref.current = element;
        }}
        className={speed <= 0 ? "ants__mark is-still" : "ants__mark"}
        d=""
        pathLength={100}
        fill="none"
        stroke="currentColor"
        strokeWidth={lineWidth}
        strokeLinecap="round"
        strokeDasharray="0 5"
        style={{ visibility: "hidden" }}
      />
    </svg>
  );
}
