/**
 * The field — a referent and the neighborhood someone grows around it.
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
 * **Selection is marching ants.** The mark the reader is open on is ringed by
 * travelling beads — the product canvas's selection, brought over whole. It
 * replaces a translucent halo, which on a field of discs read as a smudge
 * rather than as a choice, and it generalises: a disc takes a circle, a plate
 * takes a square-cornered box, and a bond — which has no mark of its own — has
 * the beads march along the filament itself.
 *
 * **Focus dims the rest.** Hovering does not just add a name, it takes presence
 * away from everything the named thing does not touch. The lit/dim pair is how
 * the product's canvas answers "what is this connected to" without moving
 * anything.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Graph } from "@antv/g6";
import {
  chipKindOf,
  chipNode,
  discNode,
  filamentEdge,
  isAuthored,
  isDecoration,
  paintOf,
  shelfNode,
  spokeEdge,
  type MarkParams,
  type Paint,
} from "./marks";
import {
  GRAPH_DNA_INTERACTION,
  GRAPH_DNA_PROVISIONAL_THEME,
  GRAPH_DNA_THEME,
  type ThemeMode,
} from "../styles/graphDna";
import { DEFAULT_MOTION_PLANS } from "../styles/motion";
import { SelectionAnts, type AntTarget } from "../styles/SelectionAnts";
import type { WorkingSet } from "./workingSet";
import {
  assertionShown,
  unsettled,
  type ShowState,
} from "./show";

export type CanvasSelection =
  | { kind: "referent"; id: string }
  | { kind: "assertion"; id: string }
  /** An obligation, which has no assertion to read — see §8.7. */
  | { kind: "demand"; id: string }
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
  show,
  onHover,
  onSelect,
  onPositions,
}: {
  set: WorkingSet;
  mode: ThemeMode;
  params: MarkParams;
  hovered: string | null;
  selection: CanvasSelection;
  show: ShowState;
  onHover: (id: string | null) => void;
  onSelect: (selection: CanvasSelection) => void;
  onPositions: (positions: Map<string, { x: number; y: number }>) => void;
}) {
  const hostRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<Graph | null>(null);
  const [stageSize, setStageSize] = useState({ width: 0, height: 0 });
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
  /** Whether the renderer exists yet, so the ants can be handed a live graph. */
  const [ready, setReady] = useState(false);
  const paint = useMemo(() => paintOf(GRAPH_DNA_THEME[mode]), [mode]);
  const provisional = useMemo(
    () => paintOf(GRAPH_DNA_PROVISIONAL_THEME[mode]),
    [mode],
  );
  const dim = useMemo(() => dimmed(paint), [paint]);
  const dimProvisional = useMemo(() => dimmed(provisional), [provisional]);

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
    for (const demand of set.demands.values()) {
      const involved =
        demand.key === active || demand.spokes.some((spoke) => spoke.id === active);
      if (!involved) continue;
      touching.add(demand.key);
      for (const spoke of demand.spokes) touching.add(spoke.id);
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

  /**
   * What the ants trace: the geometry the selected mark already has.
   *
   * Nothing is traced around a mark a filter is hiding — the ants are a mark's
   * outline, and an outline with nothing inside it is a claim that something is
   * there. Selection survives the filter; only its drawing does not.
   */
  const antTarget = useMemo<AntTarget | null>(() => {
    if (!selection) return null;
    const id = selection.id;
    if (set.referents.has(id)) {
      return { shape: "circle", id, diameter: params.discDiameter };
    }
    const assertion = set.assertions.get(id);
    if (assertion) {
      return assertionShown(assertion.origin, assertion.mode, show)
        ? {
            shape: "rect",
            id,
            clearance: GRAPH_DNA_INTERACTION.selectionPlateClearance,
          }
        : null;
    }
    if (set.demands.has(id)) {
      return show.unresolved
        ? {
            shape: "rect",
            id,
            clearance: GRAPH_DNA_INTERACTION.selectionPlateClearance,
          }
        : null;
    }
    const bond = set.bonds.find((edge) => edge.assertion_id === id);
    if (bond && assertionShown(bond.origin, bond.mode, show)) {
      // The filament is the mark. Beads start clear of the discs it runs
      // between, or the selection reads as belonging to one of them.
      return { shape: "line", id, trim: params.discDiameter / 2 };
    }
    return null;
  }, [params.discDiameter, selection, set, show]);

  const data = useMemo(() => {
    const nodes: unknown[] = [];
    const edges: unknown[] = [];
    const loneSeed =
      set.referents.size === 1 &&
      set.assertions.size === 0 &&
      set.demands.size === 0 &&
      set.bonds.length === 0;
    const paintFor = (id: string, overlay = false) => {
      if (overlay) return lit && !lit.has(id) ? dimProvisional : provisional;
      return lit && !lit.has(id) ? dim : paint;
    };
    const named = (id: string) => Boolean(lit?.has(id));

    for (const referent of set.referents.values()) {
      const stored = set.positions.get(referent.id) ?? { x: 0, y: 0 };
      // Give a new seed a real field position instead of distorting the camera
      // with a single-element fit. Once moved, its stored position wins and
      // this convenience disappears.
      const at =
        loneSeed &&
        stored.x === 0 &&
        stored.y === 0 &&
        stageSize.width &&
        stageSize.height
          ? { x: stageSize.width / 2, y: stageSize.height / 2 }
          : stored;
      nodes.push(
        discNode(referent.id, at.x, at.y, referent.label, paintFor(referent.id), params),
      );
    }

    for (const assertion of set.assertions.values()) {
      if (!assertionShown(assertion.origin, assertion.mode, show)) continue;
      const at = set.positions.get(assertion.assertion_id) ?? { x: 0, y: 0 };
      const overlay = unsettled(assertion.stale, assertion.completeness);
      // Authored by a judgment rather than compiled — the constructor's or a
      // person's. Both take the provisional palette when something else on the
      // field is lit, because both are claims someone made.
      const kind = chipKindOf(assertion.origin);
      const chipPaint =
        overlay
          ? paintFor(assertion.assertion_id, true)
          : isAuthored(kind) && lit && !lit.has(assertion.assertion_id)
            ? provisional
            : paintFor(assertion.assertion_id);
      nodes.push(
        chipNode(
          assertion.assertion_id,
          at.x,
          at.y,
          assertion.relation,
          kind,
          chipPaint,
          params,
        ),
      );
      // A shelf beneath says the assertion rests on other relations; a crown
      // above says a person put it there. Both can be true of one chip — a
      // human verdict is still maintained by whatever derives from it — so
      // these are independent tests rather than a chain.
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
      if (kind === "adjudicated") {
        nodes.push(
          shelfNode(
            `crown:${assertion.assertion_id}`,
            at.x,
            at.y,
            assertion.relation,
            chipPaint,
            params,
            "over",
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
            paintFor(assertion.assertion_id, overlay),
            params,
            { role: spoke.role, showRole: named(assertion.assertion_id) },
          ),
        );
      });
    }

    // §8.7 and §9: an obligation is a hollow, dotted chip with dotted spokes —
    // present enough to be found, unfilled because nothing has filled it. It is
    // never drawn as a bond, at any arity: a line between two discs is a claim
    // that they are joined, and the point of this mark is that no such claim
    // has been made.
    for (const demand of set.demands.values()) {
      if (!show.unresolved) continue;
      const at = set.positions.get(demand.key) ?? { x: 0, y: 0 };
      nodes.push(
        chipNode(
          demand.key,
          at.x,
          at.y,
          demand.relation,
          "unresolved",
          paintFor(demand.key),
          params,
        ),
      );
      demand.spokes.forEach((spoke, index) => {
        if (!set.referents.has(spoke.id)) return;
        edges.push(
          spokeEdge(
            `${demand.key}:${index}`,
            spoke.id,
            demand.key,
            paintFor(demand.key),
            params,
            { role: spoke.role, showRole: named(demand.key), dotted: true },
          ),
        );
      });
    }

    for (const bond of set.bonds) {
      if (!set.referents.has(bond.source) || !set.referents.has(bond.target)) continue;
      if (!assertionShown(bond.origin, bond.mode, show)) continue;
      const overlay = unsettled(bond.stale, bond.completeness);
      edges.push(
        filamentEdge(
          bond.assertion_id,
          bond.source,
          bond.target,
          paintFor(bond.assertion_id, overlay),
          params,
          {
            label: bond.relation,
            named: named(bond.assertion_id),
            kind: chipKindOf(bond.origin),
          },
        ),
      );
    }
    return { nodes, edges };
  }, [
    set,
    paint,
    dim,
    provisional,
    dimProvisional,
    params,
    lit,
    show,
    stageSize,
  ]);

  /** Dragged positions belong to the person, so they are read back before use. */
  const harvest = useCallback(() => {
    const graph = graphRef.current;
    if (!graph) return;
    const out = new Map<string, { x: number; y: number }>();
    for (const node of graph.getNodeData()) {
      const id = String(node.id);
      if (isDecoration(id)) continue;
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
      // No `selected` element state. Selection is drawn over the canvas by the
      // ants, so the renderer is not also asked to thicken a line or lay a
      // halo under a disc — two marks for one fact, and the quieter one was
      // the only one anybody read.
      node: { style: { cursor: "grab" } },
      behaviors: ["zoom-canvas", "drag-canvas", "drag-element"],
    });
    graphRef.current = graph;

    const idOf = (event: unknown): string | null => {
      const target = (event as { target?: { id?: unknown } } | undefined)?.target;
      return typeof target?.id === "string" ? target.id : null;
    };
    const subject = (id: string | null) =>
      id && !isDecoration(id) ? id : null;
    /**
     * The mark an element belongs to.
     *
     * A spoke's id is its mark's id with `:index` appended, and cutting at the
     * *first* colon was wrong for everything: an assertion id is already
     * `assertion:<digest>`, so a bond's filament resolved to the literal string
     * "assertion" and hovering or clicking one selected nothing at all. Only
     * the trailing index is a suffix this surface added, so only that is taken
     * off.
     */
    const markOf = (id: string | null) => (id ? id.replace(/:\d+$/, "") : null);

    graph.on("node:pointerenter", (event) => onHover(subject(idOf(event))));
    graph.on("edge:pointerenter", (event) => onHover(markOf(idOf(event))));
    graph.on("node:pointerleave", () => onHover(null));
    graph.on("edge:pointerleave", () => onHover(null));
    graph.on("node:click", (event) => {
      const id = subject(idOf(event));
      if (!id) return;
      const current = setRef.current;
      onSelect(
        current.assertions.has(id)
          ? { kind: "assertion", id }
          : current.demands.has(id)
            ? { kind: "demand", id }
            : { kind: "referent", id },
      );
    });
    graph.on("edge:click", (event) => {
      const id = markOf(idOf(event));
      if (!id) return;
      onSelect(
        setRef.current.demands.has(id)
          ? { kind: "demand", id }
          : { kind: "assertion", id },
      );
    });
    graph.on("canvas:click", () => onSelect(null));
    // Dragging is the one interaction that changes state the model owns, so it
    // is written back rather than left in the renderer to be lost on the next
    // expansion.
    graph.on("afterdragelement", harvest);

    void graph
      .render()
      .then(() => {
        if (graphRef.current === graph) setReady(true);
      })
      .catch((problem: unknown) => {
        if (graphRef.current === graph) console.error(problem);
      });
    // A canvas has no DOM to address, so in development the graph is reachable
    // for driving from the console or a browser-automated check. Synthetic
    // pointer events do not reach the renderer's own picking, which makes this
    // the only way to exercise selection without a human hand on the mouse.
    if (import.meta.env.DEV) {
      (window as unknown as { __worldGraph?: Graph }).__worldGraph = graph;
    }
    return () => {
      graphRef.current = null;
      setReady(false);
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
    void graph
      .draw()
      .then(async () => {
        if (graphRef.current !== graph) return undefined;
        // The *viewport* follows new matter; the marks do not. Growing the
        // field is the one moment the camera should move — otherwise an
        // expansion happens somewhere off screen and reads as nothing having
        // happened — and it is the only moment it does, so an arrangement you
        // made stays where you left it while you read it.
        const grew = count > drawnRef.current;
        drawnRef.current = count;
        if (grew && count === 1) {
          // `fitView` magnifies a single disc to fill the whole stage. A seed
          // is an entry point, not a hero image. Its datum is centred from the
          // measured field height above, so the viewport stays at scale 1.
          await graph.zoomTo(1, { duration: 0 });
        } else if (grew) {
          await graph.fitView();
        }
        return undefined;
      })
      .catch((problem: unknown) => {
        // Same as at mount: a draw in flight when the canvas is torn down is
        // not something to report.
        if (graphRef.current === graph) console.error(problem);
      });
  }, [data]);

  useEffect(() => {
    const graph = graphRef.current;
    if (!graph) return;
    graph.setOptions({ background: paint.canvas });
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
      setStageSize((current) =>
        current.width === host.clientWidth &&
        current.height === host.clientHeight
          ? current
          : { width: host.clientWidth, height: host.clientHeight },
      );
    });
    observer.observe(host);
    return () => observer.disconnect();
  }, []);

  return (
    <div className="world__stage" style={{ background: paint.canvas }}>
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
