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
  GRAPH_DNA_PROVISIONAL_THEME,
  GRAPH_DNA_THEME,
  type GraphDnaTheme,
  type ThemeMode,
} from "../styles/graphDna";
import { DEFAULT_MOTION_PLANS } from "../styles/motion";
import { SelectionAnts, type AntTarget } from "../styles/SelectionAnts";
import { furnitureOf, isDecoration, MARK_DEFAULTS, paintOf } from "./marks";
import { ensureWorldFilamentRegistered } from "./filaments";
import { observeHostSize } from "./canvasHost";
import { transitionCanvasData, type CanvasDatum } from "./canvasMotion";
import { useFocusPan, type CameraInsets } from "./canvasFocus";
import { schemaLayout } from "./schemaGraph";

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
  const [positions, setPositions] = useState(
    () => new Map<string, { x: number; y: number }>(),
  );
  const liveRef = useRef(positions);
  const draggingRef = useRef(false);
  const onHoverRef = useRef(onHover);
  const onSelectRef = useRef(onSelect);
  onHoverRef.current = onHover;
  onSelectRef.current = onSelect;

  const paint = useMemo(
    () => paintOf(inverted ? FOCUS_THEME : GRAPH_DNA_THEME[mode]),
    [inverted, mode],
  );
  const stalePaint = useMemo(
    () => paintOf(GRAPH_DNA_PROVISIONAL_THEME[mode]),
    [mode],
  );
  const base = useMemo(
    () =>
      schemaLayout(relations, paint, stalePaint, MARK_DEFAULTS, {
        namedAtRest,
        focused: active,
      }),
    [relations, paint, stalePaint, namedAtRest, active],
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
        const ringed = node.id === `rel:${selected}`;
        if (!at && !ringed) return node;
        return {
          ...node,
          style: {
            ...node.style,
            ...(at ? { x: at.x, y: at.y } : null),
            ...(ringed ? { lineWidth: 0 } : null),
          },
        };
      }),
    }),
    [base.data, positions, selected],
  );

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

    graph.on("node:pointerenter", (event) => {
      if (draggingRef.current) return;
      onHoverRef.current(relationOf(idOf(event)));
    });
    graph.on("node:pointerleave", () => {
      if (!draggingRef.current) onHoverRef.current(null);
    });
    graph.on("node:click", (event) => {
      const relation = relationOf(idOf(event));
      if (relation) onSelectRef.current(relation);
    });
    graph.on("edge:click", (event) => {
      const relation = relationOf(idOf(event));
      if (relation) onSelectRef.current(relation);
    });
    graph.on("canvas:click", () => onSelectRef.current(null));
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
    if (import.meta.env.DEV) {
      (window as unknown as { __worldGraph?: Graph }).__worldGraph = graph;
    }
    return () => {
      graphRef.current = null;
      setReady(false);
      if (
        (window as unknown as { __worldGraph?: Graph }).__worldGraph === graph
      ) {
        delete (window as unknown as { __worldGraph?: Graph }).__worldGraph;
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
        if (!fittedRef.current && next.nodes.length && !focusIdRef.current) {
          fittedRef.current = true;
          const settle = DEFAULT_MOTION_PLANS.settle;
          await graph.fitView(undefined, {
            duration: settle.durationMs,
            easing: settle.easing.g6,
          });
        }
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
  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    return observeHostSize(host, (width, height) => {
      const graph = graphRef.current;
      if (!graph) return;
      graph.resize(width, height);
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
