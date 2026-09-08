/**
 * The vocabulary canvas — §7.1.
 *
 * Lifted out of `WorldPage` when the field arrived beside it: two canvases in
 * one component is how one of them ends up with the other's behaviours. Its
 * first arrangement is deterministic, but it is still a thinking surface:
 * marks can be moved and their positions survive label and selection changes.
 *
 * Selection is the field's, which is the product canvas's: marching ants on the
 * mark's own outline. A relation that stands on the field is a plate and takes
 * a box; one that collapsed onto a bond has the beads run along the filament.
 * The two canvases share the component so they cannot come to disagree about
 * what being selected looks like.
 */

import { useEffect, useMemo, useRef, useState } from "react";
import { Graph } from "@antv/g6";
import type { WorldRelation } from "../api/world";
import {
  GRAPH_DNA_FOCUS,
  GRAPH_DNA_INTERACTION,
  GRAPH_DNA_THEME,
  type GraphDnaTheme,
  type ThemeMode,
} from "../styles/graphDna";
import { DEFAULT_MOTION_PLANS } from "../styles/motion";
import { SelectionAnts, type AntTarget } from "../styles/SelectionAnts";
import { labelUnderPointer } from "./labelPick";
import { furnitureOf, isDecoration, MARK_DEFAULTS, paintOf } from "./marks";
import { ensureWorldFilamentRegistered } from "./filaments";
import { observeHostSize } from "./canvasHost";
import {
  reducedMotion,
  restyleCanvasData,
  transitionCanvasData,
  type CanvasData,
  type CanvasDatum,
} from "./canvasMotion";
import { useFocusPan, type CameraInsets } from "./canvasFocus";
import { relationsByKind, schemaLayout } from "./schemaGraph";

const FOCUS_THEME: GraphDnaTheme = {
  surface: GRAPH_DNA_FOCUS.field,
  canvas: GRAPH_DNA_FOCUS.field,
  filament: GRAPH_DNA_FOCUS.lit,
  node: GRAPH_DNA_FOCUS.lit,
  nodeLabel: GRAPH_DNA_FOCUS.litLabel,
  chip: GRAPH_DNA_FOCUS.chip,
  lensLabel: GRAPH_DNA_FOCUS.lensLabel,
  bondLabel: GRAPH_DNA_FOCUS.bondLabel,
};

export function SchemaCanvas({
  relations,
  mode,
  namedAtRest,
  active,
  selected,
  inverted = false,
  focusId = null,
  focusToken = 0,
  insets,
  onHover,
  onSelect,
}: {
  relations: WorldRelation[];
  mode: ThemeMode;
  namedAtRest: boolean;
  /** Hover only changes what the canvas names. */
  active: string | null;
  /** Click chooses what the reader opens. */
  selected: string | null;
  /** Vocabulary as a focus room — inverted field, same marks. */
  inverted?: boolean;
  /** A table-named relation to fly to. Canvas clicks do not set this. */
  focusId?: string | null;
  focusToken?: number;
  insets: CameraInsets;
  onHover: (relation: string | null) => void;
  onSelect: (relation: string | null) => void;
}) {
  const hostRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<Graph | null>(null);
  const insetsRef = useRef(insets);
  insetsRef.current = insets;
  const focusIdRef = useRef(focusId);
  focusIdRef.current = focusId;
  const [ready, setReady] = useState(false);
  const fittedRef = useRef(false);
  /**
   * The kind disc the pointer is on, if any.
   *
   * Local, and not lifted to the page, because it changes nothing the page
   * knows: the reader still opens relations, the table still lists them. All
   * this decides is which names this canvas draws — a drawing concern, kept
   * where the drawing is.
   */
  const [hoveredKind, setHoveredKind] = useState<string | null>(null);
  const [positions, setPositions] = useState(
    () => new Map<string, { x: number; y: number }>(),
  );
  const liveRef = useRef(positions);
  const draggingRef = useRef(false);
  /**
   * The last frame this canvas authored, so a repaint can be told from a
   * lifecycle. `restyleCanvasData` compares against it; without it every
   * hover would go down the lifecycle path — see the effect below.
   */
  const authoredRef = useRef<CanvasData | null>(null);
  const onHoverRef = useRef(onHover);
  const onSelectRef = useRef(onSelect);
  onHoverRef.current = onHover;
  onSelectRef.current = onSelect;

  const paint = useMemo(
    () => paintOf(inverted ? FOCUS_THEME : GRAPH_DNA_THEME[mode]),
    [inverted, mode],
  );
  const byKind = useMemo(() => relationsByKind(relations), [relations]);
  const lit = useMemo(() => {
    const standing = hoveredKind ? byKind.get(hoveredKind) : null;
    return standing ? new Set(standing) : undefined;
  }, [byKind, hoveredKind]);
  const base = useMemo(
    () =>
      schemaLayout(relations, paint, paint, MARK_DEFAULTS, {
        namedAtRest,
        focused: active,
        lit,
      }),
    [relations, paint, namedAtRest, active, lit],
  );
  const data = useMemo(
    () => ({
      ...base.data,
      nodes: (base.data.nodes as Array<{
        id?: string;
        style?: Record<string, unknown>;
      }>).map((node) => {
        const at = node.id
          ? (liveRef.current.get(node.id) ?? positions.get(node.id))
          : null;
        // The selected plate hands its border to the ants, which trace exactly
        // where the stroke was. Leaving it on would put a solid rectangle
        // under the dotted one — the pair this change exists to remove.
        //
        // And it opens, on the field's rule: selection withdraws a mark's fill
        // into its marching boundary whatever the mark is. An authored
        // relation was the one plate on this canvas that stayed solid when
        // looked at, which made the vocabulary answer selection differently
        // from the field showing the same relation's tuples.
        const ringed = node.id === `rel:${selected}`;
        if (!at && !ringed) return node;
        return {
          ...node,
          style: {
            ...node.style,
            ...(at ? { x: at.x, y: at.y } : null),
            ...(ringed
              ? {
                  lineWidth: 0,
                  fill: paint.canvas,
                  fillOpacity: 1,
                  labelFill: paint.ink,
                }
              : null),
          },
        };
      }),
    }),
    [base.data, paint, positions, selected],
  );

  /**
   * Frame the ring, once, and only when there is a frame to do it in.
   *
   * `fittedRef` is set on success rather than on attempt: the point of the
   * flag is that the camera is established once, and a fit that ran against a
   * zero-sized stage established nothing.
   */
  const fit = async (graph: Graph) => {
    if (fittedRef.current || focusIdRef.current) return;
    const [width, height] = graph.getSize();
    if (!(width > 1 && height > 1)) return;
    if (!graph.getNodeData().length) return;
    const settle = DEFAULT_MOTION_PLANS.settle;
    fittedRef.current = true;
    await graph.fitView(undefined, {
      duration: settle.durationMs,
      easing: settle.easing.g6,
    });
  };

  const relationOf = (id: string | null): string | null => {
    if (!id || id.startsWith("kind:") || isDecoration(id)) return null;
    if (id.startsWith("rel:")) return id.slice(4);
    return id.split(":")[0] || null;
  };

  /**
   * A relation is a plate if it has one, and a filament if it does not.
   *
   * The same question `schemaLayout` already answered by which element it
   * emitted, asked of the drawing rather than re-derived from arity — so a
   * relation that changes projection cannot end up ringed as the shape it is
   * no longer drawn as.
   */
  const antTarget = useMemo<AntTarget | null>(() => {
    if (!selected) return null;
    const plate = `rel:${selected}`;
    const standing = (base.data.nodes as Array<{ id?: string }>).some(
      (node) => node.id === plate,
    );
    return standing
      ? { shape: "rect", id: plate }
      : { shape: "edge-label", id: selected, text: selected };
  }, [base.data.nodes, selected]);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    // The vocabulary draws the same marks the field does, and G6 resolves an
    // edge's type as it builds it. Registration is global and idempotent.
    ensureWorldFilamentRegistered();
    const graph = new Graph({
      container: host,
      data: data as never,
      animation: false,
      autoFit: { type: "view", options: { direction: "both" } },
      padding: 48,
      background: "transparent",
      // Selection is the ants, over the canvas — see `WorldCanvas`. No halo
      // under the plate and no thickened filament: one fact, one mark.
      node: { style: { cursor: "grab" } },
      edge: { style: { cursor: "default" } },
      behaviors: [
        "zoom-canvas",
        {
          type: "drag-canvas",
          enable: (event: { targetType?: string }) => event.targetType === "canvas",
        },
        {
          type: "drag-element",
          key: "drag-element",
          dropEffect: "none",
          animation: false,
          enable: (event: unknown) => {
            const id = (event as { target?: { id?: unknown } })?.target?.id;
            return typeof id === "string" && !isDecoration(id);
          },
        },
      ],
    });

    const idOf = (event: unknown): string | null => {
      const target = (event as { target?: { id?: unknown } } | undefined)?.target;
      return typeof target?.id === "string" ? target.id : null;
    };
    const harvest = () => {
      const next = new Map<string, { x: number; y: number }>();
      for (const node of graph.getNodeData()) {
        const id = String(node.id);
        const at = graph.getElementPosition(id);
        if (at) next.set(id, { x: Math.round(at[0]), y: Math.round(at[1]) });
      }
      liveRef.current = next;
      setPositions(next);
    };
    const followFurniture = (id: string) => {
      const position = graph.getElementPosition(id);
      if (!position) return;
      liveRef.current.set(id, { x: position[0], y: position[1] });
      const present = new Set(graph.getNodeData().map((node) => String(node.id)));
      const offset = MARK_DEFAULTS.chipHeight / 2 + MARK_DEFAULTS.shelfGap;
      const moved: Record<string, [number, number]> = {};
      for (const furniture of furnitureOf(id)) {
        if (!present.has(furniture)) continue;
        moved[furniture] = [
          position[0],
          furniture.startsWith("crown:")
            ? position[1] - offset
            : position[1] + offset,
        ];
      }
      if (Object.keys(moved).length) void graph.translateElementTo(moved, false);
    };

    /**
     * Leaving a disc is not the same as having stopped looking at it.
     *
     * A kind's names appear beside it, so reading one means moving off the
     * disc towards the name — and clearing on `pointerleave` takes the answer
     * away on the way to it. The field solved this once already: stand down
     * after the same interval a name takes to arrive, and let arriving
     * anywhere cancel it. Crossing from a disc onto one of its names keeps the
     * light where it was.
     */
    let standDown: number | undefined;
    const arrive = () => {
      window.clearTimeout(standDown);
      standDown = undefined;
    };
    graph.on("node:pointerenter", (event) => {
      if (draggingRef.current) return;
      arrive();
      const id = idOf(event);
      // A kind names what stands on it; a relation names itself. Two different
      // answers to "what is the person looking at", and only the second is a
      // subject the reader could open, which is why only the second is lifted.
      setHoveredKind(id && id.startsWith("kind:") ? id.slice(5) : null);
      onHoverRef.current(relationOf(id));
    });
    graph.on("edge:pointerenter", () => {
      if (!draggingRef.current) arrive();
    });
    graph.on("node:pointerleave", () => {
      if (draggingRef.current) return;
      arrive();
      standDown = window.setTimeout(() => {
        standDown = undefined;
        setHoveredKind(null);
        onHoverRef.current(null);
      }, DEFAULT_MOTION_PLANS.emit.durationMs);
    });
    graph.on("node:click", (event) => {
      const relation = relationOf(idOf(event));
      if (relation) onSelectRef.current(relation);
    });
    graph.on("edge:click", (event) => {
      const relation = relationOf(idOf(event));
      if (relation) onSelectRef.current(relation);
    });
    /**
     * A binary relation is drawn as the name on a filament and nothing else.
     *
     * No plate, so no node to click — and G6 does not deliver clicks on these
     * labels, which left `source_scope_claim` and every other base binary
     * openable from the catalogue and not from the drawing of it. `labelPick`
     * is the same canvas-space hit test the field uses; the handler above stays
     * for the case where G6 does route the event.
     *
     * Only relation names. A spoke's role name is not a relation and has the
     * relation's own plate sitting at the end of it.
     */
    const reachableLabel = (id: string) => !id.includes(":");
    /**
     * The click that follows the press this handler already answered.
     *
     * Swallowing the `pointerdown` does not swallow the `click`: the browser
     * still dispatches one, G6's picker still fails to find the label under
     * it, and what it does find is the canvas — which is the gesture for
     * "nothing here", so the selection this press just made would be undone by
     * the release of the same press. Capture on the host beats the listener G6
     * has on its own canvas.
     *
     * Decided by *where* the click landed, not by how long ago the press was.
     * A time window was the first attempt and it is the wrong instrument: it
     * makes a slow click and a quick one two different gestures, which is a
     * distinction nobody makes on purpose and a bug nobody can describe.
     */
    const swallowLabelClick = (event: MouseEvent) => {
      if (
        !labelUnderPointer(graph, event.clientX, event.clientY, reachableLabel)
      ) {
        return;
      }
      event.stopPropagation();
      event.preventDefault();
    };
    /**
     * Whether the press this release belongs to landed on a name.
     *
     * G6's "click on nothing" does not come from the DOM `click` — swallowing
     * that was not enough, and the reader opened on the press and closed again
     * on the release. Whatever @antv/g derives its click from, it arrives as
     * `canvas:click`, so the answer is given there: every press through this
     * host records whether it hit a reachable label, and the release that
     * follows a hit is not "nothing here".
     *
     * Recorded on *every* press, hit or miss, so it is never stale — a press
     * on empty canvas clears it on the way in.
     */
    let pressedLabel = false;
    const clickLabel = (event: PointerEvent) => {
      if (draggingRef.current) return;
      const hit = labelUnderPointer(
        graph,
        event.clientX,
        event.clientY,
        reachableLabel,
      );
      pressedLabel = Boolean(hit);
      if (!hit) return;
      event.stopPropagation();
      event.preventDefault();
      onSelectRef.current(hit);
    };
    host.addEventListener("pointerdown", clickLabel, true);
    host.addEventListener("click", swallowLabelClick, true);
    graph.on("canvas:click", () => {
      if (pressedLabel) return;
      onSelectRef.current(null);
    });
    graph.on("node:dragstart", (event) => {
      draggingRef.current = true;
      const id = idOf(event);
      if (id && !isDecoration(id)) followFurniture(id);
    });
    graph.on("node:drag", (event) => {
      const id = idOf(event);
      if (id && !isDecoration(id)) followFurniture(id);
    });
    graph.on("node:dragend", (event) => {
      const id = idOf(event);
      if (id && !isDecoration(id)) followFurniture(id);
      draggingRef.current = false;
      harvest();
    });

    graphRef.current = graph;
    // The frame the graph was built from. Without it the first hover has
    // nothing to diff against and falls to the lifecycle path.
    authoredRef.current = {
      nodes: data.nodes as CanvasDatum[],
      edges: data.edges as CanvasDatum[],
    };
    // Unmounting mid-render is not a failure. Placing the first thing on the
    // field replaces this canvas with the field's, and G6 rejects whatever draw
    // was in flight with "the graph instance has been destroyed" — a real
    // error, reported, only if this graph is still the current one.
    void graph
      .render()
      .then(() => {
        if (graphRef.current === graph) setReady(true);
      })
      .catch((problem: unknown) => {
        if (graphRef.current === graph) console.error(problem);
      });
    // Its own development-only name. A check aimed at the field should land on
    // the vocabulary canvas, not on whichever canvas rendered last.
    if (import.meta.env.DEV) {
      (window as unknown as { __worldVocabulary?: Graph }).__worldVocabulary = graph;
    }
    return () => {
      window.clearTimeout(standDown);
      host.removeEventListener("pointerdown", clickLabel, true);
      host.removeEventListener("click", swallowLabelClick, true);
      graphRef.current = null;
      authoredRef.current = null;
      setReady(false);
      if (
        (window as unknown as { __worldVocabulary?: Graph }).__worldVocabulary ===
        graph
      ) {
        delete (window as unknown as { __worldVocabulary?: Graph })
          .__worldVocabulary;
      }
      graph.destroy();
    };
    // The graph is created once. Data changes below preserve viewport and
    // manually arranged positions.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const graph = graphRef.current;
    if (!graph || draggingRef.current) return;
    let cancelled = false;
    const next = {
      nodes: data.nodes as CanvasDatum[],
      edges: data.edges as CanvasDatum[],
    };
    /**
     * Hovering a relation is a repaint, and it must not go through the
     * lifecycle.
     *
     * Nothing arrives, nothing leaves and nothing is anywhere new when a
     * relation lights its role names — the same pointer-direct case the field
     * canvas has always sent to `restyleCanvasData`. Sending it to
     * `transitionCanvasData` instead let G6 own the label fade, and G6 will
     * happily run two fades on one plate: hover on authors the name, hover off
     * authors it away thirty milliseconds later, and the abandoned fade
     * finishes last and writes *its* end value back. The plate is then opaque
     * while the data says it is transparent, and because G6 diffs authored
     * data against authored data, nothing afterwards ever writes it again.
     *
     * A role plate is painted in the canvas colour, so what that leaves on
     * screen is a gap bitten out of the filament where the name used to be —
     * for the life of the page, and only when the pointer moved quickly enough
     * to overlap the two fades.
     *
     * `fadeLabel` is the interlock: it cancels the fade already running on a
     * shape before starting the next one. The field canvas has had it all
     * along. This is the same canvas asking the same question, so it takes the
     * same path, and falls through to the lifecycle when the frame is
     * genuinely more than paint.
     */
    if (
      restyleCanvasData(graph, authoredRef.current, next, {
        // A name arriving is a body leaving its home. Absent under reduced
        // motion, which lands it outright — `restyleCanvasData` says so.
        labelPlan: reducedMotion() ? undefined : DEFAULT_MOTION_PLANS.emit,
      })
    ) {
      authoredRef.current = next;
      return;
    }
    authoredRef.current = next;
    void (async () => {
      try {
        await transitionCanvasData(
          graph,
          next,
          () => cancelled || graphRef.current !== graph,
        );
        if (cancelled || graphRef.current !== graph) return;
        // Establish the vocabulary's camera once. A SHOW change is a lens over
        // the same map and must not reframe whatever remains.
        //
        // Not against a viewport with no size in it. This canvas is built
        // while it may still be parked behind the field, and a fit computed
        // against nothing spends the one fit there is and leaves the ring
        // sitting at the origin with one disc showing — the whole vocabulary
        // present and all but invisible. The resize observer below finishes
        // the job when the stage is actually given room.
        await fit(graph);
      } catch (problem: unknown) {
        if (graphRef.current === graph) console.error(problem);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [data]);

  // A renderer sized once is sized wrong the moment anything else on the page
  // takes room. The camera is left alone — resizing is not new matter, and
  // vocabulary then clear must return to the same view, not a fresh fit.
  //
  // Unless the fit never happened. A stage that had no room when the ring was
  // drawn has room now, and this is the first moment the fit could have meant
  // anything — so it is taken here rather than never.
  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    return observeHostSize(host, (width, height) => {
      const graph = graphRef.current;
      if (!graph) return;
      graph.resize(width, height);
      if (!fittedRef.current) void fit(graph);
    });
  }, []);

  useFocusPan(graphRef, ready, focusId, focusToken, insetsRef);

  return (
    <div className="world__stage">
      <div className="world__surface" ref={hostRef} />
      <SelectionAnts
        graph={ready ? graphRef.current : null}
        target={antTarget}
        clearance={GRAPH_DNA_INTERACTION.selectionClearance}
        dotGap={GRAPH_DNA_INTERACTION.selectionDotGap}
        lineWidth={GRAPH_DNA_INTERACTION.selectionLine}
        speed={
          GRAPH_DNA_INTERACTION.selectionMotion
            ? GRAPH_DNA_INTERACTION.selectionSpeed
            : 0
        }
        color={paint.ink}
        motion={DEFAULT_MOTION_PLANS}
        animated={GRAPH_DNA_INTERACTION.selectionMotion}
      />
    </div>
  );
}
