/**
 * The field — a referent and the neighborhood someone grew around it.
 *
 * §7.2, and the mode the product actually lives in. What the schema canvas does
 * for vocabulary this does for instances, in the same two marks: discs are
 * referents, chips are assertions, and a bond is a chip that has a line to ride.
 *
 * Three behaviours are deliberate rather than defaults.
 *
 * **Marks are draggable.** A neighborhood is something a person arranges to
 * think with, so nodes are moved by hand and stay where they are put — dragged
 * positions are read back out of the renderer before any rebuild, so growing
 * the field never undoes the arrangement.
 *
 * **Naming lights the bond.** At rest the field is discs and filaments and no
 * words but the referents' own; hovering a mark names what it touches. That is
 * the ambient map's rule, and it is what keeps a neighborhood from reading as a
 * diagram — as well as the mechanical reason a chip is legible at all, since a
 * label takes the opacity of the element it belongs to.
 *
 * **Focus dims the rest.** Hovering does not just add a name, it takes presence
 * away from everything the named thing does not touch. The lit/dim pair is how
 * the product's canvas answers "what is this connected to" without moving
 * anything.
 */

import { useCallback, useEffect, useMemo, useRef } from "react";
import { Graph } from "@antv/g6";
import {
  chipNode,
  discNode,
  filamentEdge,
  paintOf,
  shelfNode,
  spokeEdge,
  type MarkParams,
  type Paint,
} from "./marks";
import {
  GRAPH_DNA_PROVISIONAL_THEME,
  GRAPH_DNA_THEME,
  type ThemeMode,
} from "../styles/graphDna";
import type { WorkingSet } from "./workingSet";

export type CanvasSelection =
  | { kind: "referent"; id: string }
  | { kind: "assertion"; id: string }
  | null;

/**
 * A palette one step down, for matter the pointer is not on.
 *
 * Dimming by opacity would fade the labels and any state drawn over the top
 * with it, which inverts the emphasis — the same reason the provisional theme
 * is a palette rather than an alpha. Here the dim is the theme's own muted ink,
 * so a lit mark is the only full-strength thing on the field.
 */
function dimmed(paint: Paint): Paint {
  return { ...paint, ink: paint.muted };
}

export function WorldCanvas({
  set,
  mode,
  params,
  hovered,
  selection,
  onHover,
  onSelect,
  onPositions,
}: {
  set: WorkingSet;
  mode: ThemeMode;
  params: MarkParams;
  hovered: string | null;
  selection: CanvasSelection;
  onHover: (id: string | null) => void;
  onSelect: (selection: CanvasSelection) => void;
  onPositions: (positions: Map<string, { x: number; y: number }>) => void;
}) {
  const hostRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<Graph | null>(null);
  /** Marks on the field last time we drew, so growth can be noticed. */
  const drawnRef = useRef(0);
  /**
   * The current working set, for handlers registered once at mount.
   *
   * The renderer's listeners are attached when the canvas is created and never
   * again — re-registering them on every expansion is how a canvas ends up
   * firing a click five times. That means their closure is the *first* render's,
   * where the field is empty, so asking `set.assertions.has(id)` inside one
   * always answered no and every chip click was routed as a referent. Read
   * through a ref instead, which is the only part of the state a handler needs
   * to be current about.
   */
  const setRef = useRef(set);
  setRef.current = set;
  const paint = useMemo(() => paintOf(GRAPH_DNA_THEME[mode]), [mode]);
  const stale = useMemo(() => paintOf(GRAPH_DNA_PROVISIONAL_THEME[mode]), [mode]);
  const dim = useMemo(() => dimmed(paint), [paint]);

  /** Which ids the pointer's subject touches, including itself. */
  const lit = useMemo(() => {
    const active = hovered ?? (selection ? selection.id : null);
    if (!active) return null;
    const touching = new Set<string>([active]);
    for (const assertion of set.assertions.values()) {
      const involved =
        assertion.assertion_id === active ||
        assertion.spokes.some((spoke) => spoke.id === active);
      if (!involved) continue;
      touching.add(assertion.assertion_id);
      for (const spoke of assertion.spokes) touching.add(spoke.id);
    }
    for (const bond of set.bonds) {
      if (bond.source !== active && bond.target !== active && bond.assertion_id !== active) {
        continue;
      }
      touching.add(bond.source);
      touching.add(bond.target);
      touching.add(bond.assertion_id);
    }
    return touching;
  }, [hovered, selection, set]);

  const data = useMemo(() => {
    const nodes: unknown[] = [];
    const edges: unknown[] = [];
    const paintFor = (id: string) => (lit && !lit.has(id) ? dim : paint);
    const named = (id: string) => Boolean(lit?.has(id));

    for (const referent of set.referents.values()) {
      const at = set.positions.get(referent.id) ?? { x: 0, y: 0 };
      nodes.push(
        discNode(referent.id, at.x, at.y, referent.label, paintFor(referent.id), params),
      );
    }

    for (const assertion of set.assertions.values()) {
      const at = set.positions.get(assertion.assertion_id) ?? { x: 0, y: 0 };
      const chipPaint =
        assertion.origin === "SEMANTIC" && lit && !lit.has(assertion.assertion_id)
          ? stale
          : paintFor(assertion.assertion_id);
      nodes.push(
        chipNode(
          assertion.assertion_id,
          at.x,
          at.y,
          assertion.relation,
          assertion.origin === "SEMANTIC" ? "semantic" : "mechanical",
          chipPaint,
          params,
        ),
      );
      if (assertion.mode === "DERIVED") {
        nodes.push(
          shelfNode(
            `shelf:${assertion.assertion_id}`,
            at.x,
            at.y,
            assertion.relation,
            chipPaint,
            params,
          ),
        );
      }
      assertion.spokes.forEach((spoke, index) => {
        if (!set.referents.has(spoke.id)) return;
        edges.push(
          spokeEdge(
            `${assertion.assertion_id}:${index}`,
            spoke.id,
            assertion.assertion_id,
            paintFor(assertion.assertion_id),
            params,
            { role: spoke.role, showRole: named(assertion.assertion_id) },
          ),
        );
      });
    }

    for (const bond of set.bonds) {
      if (!set.referents.has(bond.source) || !set.referents.has(bond.target)) continue;
      edges.push(
        filamentEdge(
          bond.assertion_id,
          bond.source,
          bond.target,
          paintFor(bond.assertion_id),
          params,
          {
            label: bond.relation,
            named: named(bond.assertion_id),
            semantic: bond.origin === "SEMANTIC",
          },
        ),
      );
    }
    return { nodes, edges };
  }, [set, paint, dim, stale, params, lit]);

  /** Dragged positions belong to the person, so they are read back before use. */
  const harvest = useCallback(() => {
    const graph = graphRef.current;
    if (!graph) return;
    const out = new Map<string, { x: number; y: number }>();
    for (const node of graph.getNodeData()) {
      const id = String(node.id);
      if (id.startsWith("shelf:")) continue;
      const position = graph.getElementPosition(id);
      if (position) out.set(id, { x: Math.round(position[0]), y: Math.round(position[1]) });
    }
    if (out.size) onPositions(out);
  }, [onPositions]);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    const graph = new Graph({
      container: host,
      data: data as never,
      animation: false,
      padding: 60,
      background: paint.canvas,
      behaviors: ["zoom-canvas", "drag-canvas", "drag-element"],
    });
    graphRef.current = graph;

    const idOf = (event: unknown): string | null => {
      const target = (event as { target?: { id?: unknown } } | undefined)?.target;
      return typeof target?.id === "string" ? target.id : null;
    };
    const subject = (id: string | null) =>
      id && !id.startsWith("shelf:") ? id : null;

    graph.on("node:pointerenter", (event) => onHover(subject(idOf(event))));
    graph.on("edge:pointerenter", (event) => {
      const id = idOf(event);
      onHover(id ? id.split(":")[0] : null);
    });
    graph.on("node:pointerleave", () => onHover(null));
    graph.on("edge:pointerleave", () => onHover(null));
    graph.on("node:click", (event) => {
      const id = subject(idOf(event));
      if (!id) return;
      onSelect(
        setRef.current.assertions.has(id)
          ? { kind: "assertion", id }
          : { kind: "referent", id },
      );
    });
    graph.on("edge:click", (event) => {
      const id = idOf(event);
      if (id) onSelect({ kind: "assertion", id: id.split(":")[0] });
    });
    graph.on("canvas:click", () => onSelect(null));
    // Dragging is the one interaction that changes state the model owns, so it
    // is written back rather than left in the renderer to be lost on the next
    // expansion.
    graph.on("afterdragelement", harvest);

    void graph.render();
    // A canvas has no DOM to address, so in development the graph is reachable
    // for driving from the console or a browser-automated check. Synthetic
    // pointer events do not reach the renderer's own picking, which makes this
    // the only way to exercise selection without a human hand on the mouse.
    if (import.meta.env.DEV) {
      (window as unknown as { __worldGraph?: Graph }).__worldGraph = graph;
    }
    return () => {
      graphRef.current = null;
      graph.destroy();
    };
    // The graph is created once. Data changes go through the effect below, so
    // an expansion never re-mounts the canvas and never resets the view.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const graph = graphRef.current;
    if (!graph) return;
    const count = (data.nodes as unknown[]).length;
    graph.setData(data as never);
    void graph.draw().then(() => {
      // The *viewport* follows new matter; the marks do not. Growing the field
      // is the one moment the camera should move — otherwise an expansion
      // happens somewhere off screen and reads as nothing having happened —
      // and it is the only moment it does, so an arrangement you made stays
      // where you left it while you read it.
      if (count > drawnRef.current) void graph.fitView();
      drawnRef.current = count;
    });
  }, [data]);

  useEffect(() => {
    const graph = graphRef.current;
    if (graph) graph.setOptions({ background: paint.canvas });
  }, [paint.canvas]);

  // A renderer sized once is sized wrong the moment anything else on the page
  // takes room: opening the extension drawer halves the stage, and a graph that
  // does not hear about it keeps drawing at the old size, which reads as the
  // field having gone blank. The camera is left alone — resizing is not new
  // matter, so it is not a reason to move what someone arranged.
  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    const observer = new ResizeObserver(() => {
      const graph = graphRef.current;
      if (!graph || !host.clientWidth || !host.clientHeight) return;
      graph.resize(host.clientWidth, host.clientHeight);
    });
    observer.observe(host);
    return () => observer.disconnect();
  }, []);

  return (
    <div
      className="world__stage"
      ref={hostRef}
      style={{ background: paint.canvas }}
    />
  );
}
