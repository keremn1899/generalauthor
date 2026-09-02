/**
 * The vocabulary canvas — §7.1.
 *
 * Lifted out of `WorldPage` when the field arrived beside it: two canvases in
 * one component is how one of them ends up with the other's behaviours. Its
 * first arrangement is deterministic, but it is still a thinking surface:
 * marks can be moved and their positions survive label and selection changes.
 */

import { useEffect, useMemo, useRef, useState } from "react";
import { Graph } from "@antv/g6";
import type { WorldRelation } from "../api/world";
import {
  GRAPH_DNA_PROVISIONAL_THEME,
  GRAPH_DNA_THEME,
  type ThemeMode,
} from "../styles/graphDna";
import { isDecoration, MARK_DEFAULTS, paintOf } from "./marks";
import { schemaLayout } from "./schemaGraph";

export function SchemaCanvas({
  relations,
  mode,
  namedAtRest,
  active,
  selected,
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
  onHover: (relation: string | null) => void;
  onSelect: (relation: string | null) => void;
}) {
  const hostRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<Graph | null>(null);
  const drawnSizeRef = useRef(0);
  const [positions, setPositions] = useState(
    () => new Map<string, { x: number; y: number }>(),
  );
  const onHoverRef = useRef(onHover);
  const onSelectRef = useRef(onSelect);
  const selectedRef = useRef(selected);
  onHoverRef.current = onHover;
  onSelectRef.current = onSelect;
  selectedRef.current = selected;

  const paint = useMemo(() => paintOf(GRAPH_DNA_THEME[mode]), [mode]);
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
        const at = node.id ? positions.get(node.id) : null;
        return at
          ? { ...node, style: { ...node.style, x: at.x, y: at.y } }
          : node;
      }),
    }),
    [base.data, positions],
  );

  const relationOf = (id: string | null): string | null => {
    if (!id || id.startsWith("kind:") || isDecoration(id)) return null;
    if (id.startsWith("rel:")) return id.slice(4);
    return id.split(":")[0] || null;
  };

  const applySelection = () => {
    const graph = graphRef.current;
    if (!graph || graph.destroyed || drawnSizeRef.current === 0) return;
    const chosen = selectedRef.current;
    const states: Record<string, string[]> = {};
    const chosenHasNode = graph
      .getNodeData()
      .some((node) => relationOf(String(node.id)) === chosen);
    for (const node of graph.getNodeData()) {
      const id = String(node.id);
      states[id] =
        chosen && relationOf(id) === chosen ? ["selected"] : [];
    }
    for (const edge of graph.getEdgeData()) {
      const id = String(edge.id);
      states[id] =
        chosen && !chosenHasNode && relationOf(id) === chosen
          ? ["selected"]
          : [];
    }
    void graph.setElementState(states, false).catch(() => {});
  };

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    const graph = new Graph({
      container: host,
      data: data as never,
      animation: false,
      autoFit: { type: "view", options: { direction: "both" } },
      padding: 48,
      background: paint.canvas,
      node: {
        style: { cursor: "grab" },
        state: {
          selected: {
            halo: true,
            haloLineWidth: 9,
            haloStroke: paint.ink,
            haloStrokeOpacity: 0.16,
          },
        },
      },
      edge: {
        state: {
          selected: {
            lineWidth: Math.max(1.5, MARK_DEFAULTS.edgeWidth * 1.8),
            opacity: 1,
          },
        },
      },
      behaviors: [
        "zoom-canvas",
        "drag-canvas",
        {
          type: "drag-element",
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
    graph.on("node:pointerenter", (event) => {
      onHoverRef.current(relationOf(idOf(event)));
    });
    graph.on("edge:pointerenter", (event) => {
      onHoverRef.current(relationOf(idOf(event)));
    });
    graph.on("node:pointerleave", () => onHoverRef.current(null));
    graph.on("edge:pointerleave", () => onHoverRef.current(null));
    graph.on("node:click", (event) => {
      const relation = relationOf(idOf(event));
      if (relation) onSelectRef.current(relation);
    });
    graph.on("edge:click", (event) => {
      const relation = relationOf(idOf(event));
      if (relation) onSelectRef.current(relation);
    });
    graph.on("canvas:click", () => onSelectRef.current(null));
    graph.on("afterdragelement", () => {
      const next = new Map<string, { x: number; y: number }>();
      for (const node of graph.getNodeData()) {
        const id = String(node.id);
        const at = graph.getElementPosition(id);
        if (at) next.set(id, { x: Math.round(at[0]), y: Math.round(at[1]) });
      }
      setPositions(next);
    });

    graphRef.current = graph;
    // Unmounting mid-render is not a failure. Placing the first thing on the
    // field replaces this canvas with the field's, and G6 rejects whatever draw
    // was in flight with "the graph instance has been destroyed" — a real
    // error, reported, only if this graph is still the current one.
    void graph.render().catch((problem: unknown) => {
      if (graphRef.current === graph) console.error(problem);
    });
    if (import.meta.env.DEV) {
      (window as unknown as { __worldGraph?: Graph }).__worldGraph = graph;
    }
    return () => {
      graphRef.current = null;
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
    if (!graph) return;
    const size = data.nodes.length + data.edges.length;
    graph.setData(data as never);
    void graph
      .draw()
      .then(async () => {
        if (graphRef.current !== graph) return;
        if (size !== drawnSizeRef.current) {
          drawnSizeRef.current = size;
          await graph.fitView();
        }
        applySelection();
      })
      .catch((problem: unknown) => {
        if (graphRef.current === graph) console.error(problem);
      });
  }, [data]);

  useEffect(() => {
    applySelection();
  }, [selected]);

  useEffect(() => {
    const graph = graphRef.current;
    if (!graph) return;
    graph.setOptions({ background: paint.canvas });
    graph.setNode({
      style: { cursor: "grab" },
      state: {
        selected: {
          halo: true,
          haloLineWidth: 9,
          haloStroke: paint.ink,
          haloStrokeOpacity: 0.16,
        },
      },
    });
  }, [paint.canvas, paint.ink]);

  // The vocabulary refits when its stage changes size — unlike the field, it
  // has no arrangement to preserve, so following the container is the whole of
  // the correct behaviour.
  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    const observer = new ResizeObserver(() => {
      const graph = graphRef.current;
      if (!graph || !host.clientWidth || !host.clientHeight) return;
      graph.resize(host.clientWidth, host.clientHeight);
      void graph.fitView().catch((problem: unknown) => {
        if (graphRef.current === graph) console.error(problem);
      });
    });
    observer.observe(host);
    return () => observer.disconnect();
  }, []);

  return <div className="world__stage" ref={hostRef} style={{ background: paint.canvas }} />;
}
