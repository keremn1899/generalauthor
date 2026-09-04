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
 * **Focus only names.** Hover and selection reveal the labels belonging to the
 * subject without fading unrelated matter. This matches the product canvas and
 * keeps scanning the wider neighborhood possible while a relation is named.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Graph } from "@antv/g6";
import {
  chipKindOf,
  chipNode,
  discNode,
  filamentEdge,
  furnitureOf,
  isDecoration,
  paintOf,
  shelfNode,
  spokeEdge,
  type MarkParams,
} from "./marks";
import {
  GRAPH_DNA_INTERACTION,
  GRAPH_DNA_PROVISIONAL_THEME,
  GRAPH_DNA_THEME,
  type ThemeMode,
} from "../styles/graphDna";
import { DEFAULT_MOTION_PLANS } from "../styles/motion";
import {
  DEFAULT_LIGHT_FIELD,
  lift,
  NAMING_HOPS,
  reflected,
  type LightField,
} from "../styles/light";
import { hopsFrom } from "./hops";
import { SelectionAnts, type AntTarget } from "../styles/SelectionAnts";
import { observeHostSize } from "./canvasHost";
import { transitionCanvasData, type CanvasDatum } from "./canvasMotion";
import {
  useFocusPan,
  type CameraInsets,
} from "./canvasFocus";
import type { WorkingSet } from "./workingSet";
import {
  assertionShown,
  unsettled,
  type ShowState,
} from "./show";

/**
 * The element id a bond's filament is drawn under.
 *
 * A tuple that folds is the same assertion in two drawings, but G6 keys nodes
 * and edges in **one** namespace, so the plate and the filament cannot share
 * the assertion's id: on `open`, G6 sees an element by that id already in the
 * scene and keeps the edge's `path` rather than building the plate's `rect`.
 * The plate keeps the assertion id — it is the form the shelf, the crown and
 * the spokes all hang off — and the filament is namespaced. Everything the
 * reader deals in is still the assertion id; `subjectOfBond` is where the
 * drawing's id turns back into the tuple's.
 */
function bondElementId(assertionId: string): string {
  return `bond:${assertionId}`;
}

/**
 * The mark an element belongs to.
 *
 * Three suffixes and prefixes this surface adds on its own: a spoke carries
 * its index (`demand#0:1`), a filament is namespaced (`bond:…`), and furniture
 * hangs off its chip (`shelf:…`, `crown:…`). None of them are marks a reader
 * deals in, so anything asking *what is this part of* — a click, a hover, or
 * how much light falls on it — goes through here.
 */
export function markOfElement(elementId: string): string {
  const withoutIndex = elementId.replace(/:\d+$/, "");
  const withoutBond = subjectOfBond(withoutIndex);
  return isDecoration(withoutBond)
    ? withoutBond.slice(withoutBond.indexOf(":") + 1)
    : withoutBond;
}

function subjectOfBond(elementId: string): string {
  return elementId.startsWith("bond:") ? elementId.slice(5) : elementId;
}

function liveAt(
  live: Map<string, { x: number; y: number }>,
  stored: Map<string, { x: number; y: number }>,
  id: string,
  fallback: { x: number; y: number } = { x: 0, y: 0 },
) {
  return live.get(id) ?? stored.get(id) ?? fallback;
}

/**
 * Shift the camera just enough that new matter is on screen.
 *
 * Existing marks stay where they were put. `fitView` would reframe the whole
 * neighborhood, which is a translation of everything the person already
 * arranged even when their graph coordinates have not moved.
 */
async function panToReveal(
  graph: Graph,
  ids: string[],
  insets: CameraInsets,
) {
  if (!ids.length) return;
  const [width, height] = graph.getSize();
  if (!width || !height) return;
  const padLeft = insets.left;
  const padRight = insets.right;
  const padTop = insets.top;
  const padBottom = insets.bottom;
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  for (const id of ids) {
    const position = graph.getElementPosition(id);
    if (!position) continue;
    const view = graph.getViewportByCanvas(position);
    minX = Math.min(minX, view[0]);
    minY = Math.min(minY, view[1]);
    maxX = Math.max(maxX, view[0]);
    maxY = Math.max(maxY, view[1]);
  }
  if (!Number.isFinite(minX)) return;
  let dx = 0;
  let dy = 0;
  if (maxX - minX > width - padLeft - padRight) {
    dx = (padLeft + width - padRight) / 2 - (minX + maxX) / 2;
  } else if (minX < padLeft) {
    dx = padLeft - minX;
  } else if (maxX > width - padRight) {
    dx = width - padRight - maxX;
  }
  if (maxY - minY > height - padTop - padBottom) {
    dy = (padTop + height - padBottom) / 2 - (minY + maxY) / 2;
  } else if (minY < padTop) {
    dy = padTop - minY;
  } else if (maxY > height - padBottom) {
    dy = height - padBottom - maxY;
  }
  if (dx || dy) await graph.translateBy([dx, dy], false);
}

/** What a selection ring is drawn with. The DNA is the product's answer. */
export type AntTuning = {
  clearance: number;
  dotGap: number;
  lineWidth: number;
  speed: number;
  animated: boolean;
};

export const ANT_DEFAULTS: AntTuning = {
  clearance: GRAPH_DNA_INTERACTION.selectionClearance,
  dotGap: GRAPH_DNA_INTERACTION.selectionDotGap,
  lineWidth: GRAPH_DNA_INTERACTION.selectionLine,
  speed: GRAPH_DNA_INTERACTION.selectionSpeed,
  animated: GRAPH_DNA_INTERACTION.selectionMotion,
};

export type CanvasSelection =
  | { kind: "referent"; id: string }
  | { kind: "assertion"; id: string }
  /** An obligation, which has no assertion to read — see §8.7. */
  | { kind: "demand"; id: string }
  | null;

export function WorldCanvas({
  set,
  mode,
  params,
  hovered,
  selection,
  show,
  focusId = null,
  focusToken = 0,
  insets,
  ants,
  light,
  onHover,
  onSelect,
  onPositions,
  onRemove,
}: {
  set: WorkingSet;
  mode: ThemeMode;
  params: MarkParams;
  hovered: string | null;
  selection: CanvasSelection;
  show: ShowState;
  /** A table-named mark to fly to. Canvas clicks do not set this. */
  focusId?: string | null;
  focusToken?: number;
  insets: CameraInsets;
  /**
   * The selection ring's tuning, for a surface that exists to tune it.
   *
   * Defaults to the DNA, which is what the product ships. It is a prop rather
   * than a second set of constants so the design lab drives the *same*
   * component the field draws: hand-drawn ant specimens had already grown
   * their own dash arithmetic and stopped matching what a selection looks
   * like.
   */
  ants?: Partial<AntTuning>;
  /**
   * The light field's tuning, for a surface that exists to tune it.
   *
   * Defaults to the kernel's. Two numbers — how far light reaches, and how
   * much of the world remains readable where it does not.
   */
  light?: Partial<LightField>;
  onHover: (id: string | null) => void;
  onSelect: (selection: CanvasSelection) => void;
  onPositions: (positions: Map<string, { x: number; y: number }>) => void;
  /** Right-click takes a mark off the field. */
  onRemove: (selection: NonNullable<CanvasSelection>) => void;
}) {
  const hostRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<Graph | null>(null);
  const insetsRef = useRef(insets);
  insetsRef.current = insets;
  const focusIdRef = useRef(focusId);
  focusIdRef.current = focusId;
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
  const onHoverRef = useRef(onHover);
  const onSelectRef = useRef(onSelect);
  const onRemoveRef = useRef(onRemove);
  onHoverRef.current = onHover;
  onSelectRef.current = onSelect;
  onRemoveRef.current = onRemove;
  /**
   * Positions the renderer currently has, including a drag in flight.
   *
   * Hover rebuilds the element data (to name a bond) and used to read
   * `set.positions`, which is a render behind the pointer. That is the snap
   * back. This map is written on every drag tick so a redraw mid-gesture keeps
   * the mark under the hand.
   */
  const liveRef = useRef(set.positions);
  const draggingRef = useRef(false);
  /** Whether the renderer exists yet, so the ants can be handed a live graph. */
  const [ready, setReady] = useState(false);
  const paint = useMemo(() => paintOf(GRAPH_DNA_THEME[mode]), [mode]);
  const tuning = useMemo<AntTuning>(
    () => ({ ...ANT_DEFAULTS, ...ants }),
    [ants],
  );
  const provisional = useMemo(
    () => paintOf(GRAPH_DNA_PROVISIONAL_THEME[mode]),
    [mode],
  );

  /**
   * The light on the field.
   *
   * One source — what the pointer is on, or failing that what is selected —
   * and `luminance` falls off from it through the graph. Hover outranks
   * selection because the pointer is the more recent act, and light follows
   * acts.
   *
   * With nothing acted on there is no source, every mark is at 1, and the law
   * changes nothing. That is deliberate: this is a lamp, not a vignette.
   */
  const lightField = useMemo(
    () => ({ ...DEFAULT_LIGHT_FIELD, ...light }),
    [light],
  );

  /**
   * Graph distance from whatever a person is acting on.
   *
   * Hover outranks selection because the pointer is the more recent act. With
   * nothing acted on there is no source and the two things below — naming and
   * light — both stand down, which is the resting state of the field.
   */
  const hops = useMemo(() => {
    const source = hovered ?? (selection ? selection.id : null);
    return source ? hopsFrom(set, source) : null;
  }, [hovered, selection, set]);

  /**
   * How much light reaches an element.
   *
   * Furniture takes the light of the chip it hangs off, and a spoke the light
   * of the plate it belongs to — otherwise the rule under a derived plate
   * lifts out of step with the plate it is part of.
   */
  const incident = useMemo(() => {
    if (!hops) return null;
    return (elementId: string) => {
      const mark = markOfElement(elementId);
      return lift(hops.has(mark) ? (hops.get(mark) as number) : null, lightField);
    };
  }, [hops, lightField]);

  /**
   * Which marks name themselves: the one you touched, and what it is joined to.
   *
   * A plain hop count, not a light threshold. Reading naming off the light
   * made retuning the falloff silently change which labels appear, and they
   * are different questions — see `NAMING_HOPS`.
   */
  const namedMarks = useMemo(() => {
    if (!hops) return null;
    const named = new Set<string>();
    for (const [mark, distance] of hops) {
      if (distance <= NAMING_HOPS) named.add(mark);
    }
    return named;
  }, [hops]);

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
        ? { shape: "rect", id }
        : null;
    }
    // An obligation's plate is the one that is dotted already, so its ants take
    // over the pattern rather than morphing into it.
    if (set.demands.has(id)) {
      return show.unresolved ? { shape: "rect", id, dotted: true } : null;
    }
    const bond = set.bonds.find((edge) => edge.assertion_id === id);
    if (bond && assertionShown(bond.origin, bond.mode, show)) {
      return {
        shape: "edge-label",
        id: bondElementId(id),
        text: bond.relation,
      };
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
    const paintFor = (_id: string, overlay = false) =>
      overlay ? provisional : paint;
    const named = (id: string) => Boolean(namedMarks?.has(id));
    /** The mark a person is on, which is what a bond's label leans toward. */
    const acted = hovered ?? (selection ? selection.id : null);
    const at = (id: string, fallback: { x: number; y: number } = { x: 0, y: 0 }) =>
      liveAt(liveRef.current, set.positions, id, fallback);

    for (const referent of set.referents.values()) {
      const stored = at(referent.id);
      // Give a new seed a real field position instead of distorting the camera
      // with a single-element fit. Once moved, its stored position wins and
      // this convenience disappears.
      const placed =
        loneSeed &&
        stored.x === 0 &&
        stored.y === 0 &&
        stageSize.width &&
        stageSize.height
          ? { x: stageSize.width / 2, y: stageSize.height / 2 }
          : stored;
      nodes.push(
        discNode(referent.id, placed.x, placed.y, referent.label, paintFor(referent.id), params),
      );
    }

    for (const assertion of set.assertions.values()) {
      if (!assertionShown(assertion.origin, assertion.mode, show)) continue;
      const atChip = at(assertion.assertion_id);
      const overlay = unsettled(assertion.stale, assertion.completeness);
      const kind = chipKindOf(assertion.origin);
      const chipPaint = paintFor(assertion.assertion_id, overlay);
      nodes.push(
        chipNode(
          assertion.assertion_id,
          atChip.x,
          atChip.y,
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
            atChip.x,
            atChip.y,
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
            atChip.x,
            atChip.y,
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
      const atDemand = at(demand.key);
      nodes.push(
        chipNode(
          demand.key,
          atDemand.x,
          atDemand.y,
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
          bondElementId(bond.assertion_id),
          bond.source,
          bond.target,
          paintFor(bond.assertion_id, overlay),
          params,
          {
            label: bond.relation,
            named: named(bond.assertion_id),
            kind: chipKindOf(bond.origin),
            lean:
              acted === bond.source
                ? "source"
                : acted === bond.target
                  ? "target"
                  : undefined,
          },
        ),
      );
    }
    /**
     * Light applied last, over everything the marks authored.
     *
     * Reflected rather than replaced: a filament authored quiet stays quieter
     * than the disc beside it, because illumination scales what a thing is
     * instead of overwriting it. With no source `incident` is null and this
     * loop does not run, so at rest the field draws exactly as it did before
     * there was a law.
     */
    if (incident) {
      /**
       * Each mark reflects on the channels it is made of, and never on
       * `opacity`.
       *
       * `opacity` is presence — the channel birth and absorption own, and the
       * one G6 composites into the label group. Lighting it would light the
       * names too, and a name is not lit, it is read. So a disc reflects on
       * its fill, an outlined plate on its stroke, a filament on its stroke,
       * and every one of them keeps its label at the strength it was stated
       * at. See `discNode` and `spokeEdge`.
       *
       * A channel absent from the datum is not lit into existence: a hollow
       * plate has `fillOpacity: 0` on purpose, and `reflected` leaves a zero
       * where it found one — nothing is what an obligation is made of.
       */
      const reflect = (
        mark: { id: string; style?: Record<string, unknown> },
        channels: readonly ("fillOpacity" | "strokeOpacity")[],
      ) => {
        if (!mark.style) return;
        const incidentHere = incident(mark.id);
        for (const channel of channels) {
          const albedo = mark.style[channel] as number | undefined;
          if (albedo === undefined || albedo === 0) continue;
          mark.style[channel] = reflected(albedo, incidentHere);
        }
      };
      for (const node of nodes as { id: string; style?: Record<string, unknown> }[]) {
        reflect(node, ["fillOpacity", "strokeOpacity"]);
      }
      for (const edge of edges as { id: string; style?: Record<string, unknown> }[]) {
        reflect(edge, ["strokeOpacity"]);
      }
    }
    /**
     * The selected plate hands its border to the ants.
     *
     * Two rectangles is what the ants used to draw, and dropping the standoff
     * alone would only have stacked them: a solid border with beads sitting on
     * it is still a solid border. So the plate's own stroke goes, the ants
     * arrive solid in exactly its place, and what a person sees is one border
     * that becomes dotted. It comes straight back on deselect, and it never
     * tweens — `meaningIsStructural`; the width is a fact about construction
     * origin, and a plate caught between outlined and not draws an origin that
     * does not exist.
     */
    if (antTarget && antTarget.shape === "rect") {
      const plate = (nodes as { id: string; style?: Record<string, unknown> }[]).find(
        (node) => node.id === antTarget.id,
      );
      if (plate?.style) plate.style.lineWidth = 0;
    }
    return { nodes, edges };
  }, [
    set,
    paint,
    provisional,
    params,
    antTarget,
    hovered,
    selection,
    incident,
    namedMarks,
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
    if (!out.size) return;
    liveRef.current = new Map([...liveRef.current, ...out]);
    onPositions(out);
  }, [onPositions]);

  useEffect(() => {
    if (!draggingRef.current) liveRef.current = set.positions;
  }, [set.positions]);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    const blockMenu = (event: Event) => event.preventDefault();
    host.addEventListener("contextmenu", blockMenu);
    const graph = new Graph({
      container: host,
      data: data as never,
      animation: false,
      padding: 60,
      // Transparent on purpose. G6's `setOptions({ background })` stores the
      // colour but never paints it, so an opaque field set at mount stuck
      // through every theme flip. The live field is `--matter-canvas` on the
      // stage, the same path the product canvas uses.
      background: "transparent",
      // No `selected` element state. Selection is drawn over the canvas by the
      // ants, so the renderer is not also asked to thicken a line or lay a
      // halo under a disc — two marks for one fact, and the quieter one was
      // the only one anybody read.
      node: { style: { cursor: "grab" } },
      behaviors: [
        "zoom-canvas",
        {
          type: "drag-canvas",
          enable: (event: { targetType?: string }) => event.targetType === "canvas",
        },
        {
          type: "drag-element",
          key: "drag-element",
          // Product nodes are not combo containers. G6's default `move`
          // effect refreshes combo data on every pointer event, which is pure
          // bookkeeping here and makes the held object trail the pointer.
          dropEffect: "none",
          animation: false,
          enable: (event: unknown) => {
            const id = (event as { target?: { id?: unknown } })?.target?.id;
            return typeof id === "string" && !isDecoration(id);
          },
        },
      ],
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
    const markOf = (id: string | null) => (id ? markOfElement(id) : null);

    const followFurniture = (id: string) => {
      const position = graph.getElementPosition(id);
      if (!position) return;
      liveRef.current.set(id, { x: position[0], y: position[1] });
      const present = new Set(graph.getNodeData().map((node) => String(node.id)));
      const offset = params.chipHeight / 2 + params.shelfGap;
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
      if (Object.keys(moved).length) {
        void graph.translateElementTo(moved, false);
      }
    };

    let ignoreClickUntil = 0;
    const hovering = (id: string | null) => {
      if (draggingRef.current) return;
      onHoverRef.current(id);
    };
    const pickNode = (id: string): NonNullable<CanvasSelection> => {
      const current = setRef.current;
      if (current.assertions.has(id)) return { kind: "assertion", id };
      if (current.demands.has(id)) return { kind: "demand", id };
      return { kind: "referent", id };
    };
    const pickEdge = (id: string): NonNullable<CanvasSelection> =>
      setRef.current.demands.has(id)
        ? { kind: "demand", id }
        : { kind: "assertion", id };
    const swallowMenu = (event: unknown) => {
      const e = event as {
        preventDefault?: () => void;
        nativeEvent?: Event;
      };
      e.preventDefault?.();
      e.nativeEvent?.preventDefault?.();
    };

    graph.on("node:pointerenter", (event) => hovering(subject(idOf(event))));
    graph.on("edge:pointerenter", (event) => hovering(markOf(idOf(event))));
    graph.on("node:pointerleave", () => hovering(null));
    graph.on("edge:pointerleave", () => hovering(null));
    graph.on("node:click", (event) => {
      if (performance.now() < ignoreClickUntil) return;
      const id = subject(idOf(event));
      if (!id) return;
      onSelectRef.current(pickNode(id));
    });
    graph.on("edge:click", (event) => {
      if (performance.now() < ignoreClickUntil) return;
      const id = markOf(idOf(event));
      if (!id) return;
      onSelectRef.current(pickEdge(id));
    });
    graph.on("canvas:click", () => {
      if (performance.now() < ignoreClickUntil) return;
      onSelectRef.current(null);
    });
    graph.on("node:contextmenu", (event) => {
      swallowMenu(event);
      const id = subject(idOf(event));
      if (id) onRemoveRef.current(pickNode(id));
    });
    graph.on("edge:contextmenu", (event) => {
      swallowMenu(event);
      const id = markOf(idOf(event));
      if (id) onRemoveRef.current(pickEdge(id));
    });
    graph.on("node:dragstart", (event) => {
      draggingRef.current = true;
      const id = subject(idOf(event));
      if (id) followFurniture(id);
    });
    graph.on("node:drag", (event) => {
      const id = subject(idOf(event));
      if (id) followFurniture(id);
    });
    // Dragging is the one interaction that changes state the model owns, so it
    // is written back rather than left in the renderer to be lost on the next
    // expansion. The product canvas also swallows the click that fires after
    // a real drag, or the reader opens on a mark you were only moving.
    graph.on("node:dragend", (event) => {
      const id = subject(idOf(event));
      if (id) followFurniture(id);
      draggingRef.current = false;
      ignoreClickUntil = performance.now() + 240;
      harvest();
    });

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
      host.removeEventListener("contextmenu", blockMenu);
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
    if (!graph || draggingRef.current) return;
    let cancelled = false;
    const next = {
      nodes: data.nodes as CanvasDatum[],
      edges: data.edges as CanvasDatum[],
    };

    void (async () => {
      try {
        const transition = await transitionCanvasData(
          graph,
          next,
          () => cancelled || graphRef.current !== graph,
        );
        if (cancelled || graphRef.current !== graph) return;
        const count = next.nodes.length;
        const grew = count > drawnRef.current;
        drawnRef.current = count;
        if (grew && count === 1) {
          await graph.zoomTo(1, { duration: 0 });
        } else if (grew && !focusIdRef.current) {
          const reveal = transition.bornNodes
            .map((node) => node.id)
            .filter((id) => !isDecoration(id));
          await panToReveal(graph, reveal, insetsRef.current);
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
  // takes room. The camera is left alone — resizing is not new matter.
  // Panel drags are the exception: the CSS grid follows the pointer, but G6
  // waits for pointer-up. Redrawing every move is both expensive and the
  // jitter. Existing marks stay put; there is no fitView here.
  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    return observeHostSize(host, (width, height) => {
      const graph = graphRef.current;
      if (!graph) return;
      graph.resize(width, height);
      setStageSize((current) =>
        current.width === width && current.height === height
          ? current
          : { width, height },
      );
    });
  }, []);

  useFocusPan(graphRef, ready, focusId, focusToken, insetsRef);

  return (
    <div className="world__stage">
      <div className="world__surface" ref={hostRef} />
      <SelectionAnts
        graph={ready ? graphRef.current : null}
        target={antTarget}
        clearance={tuning.clearance}
        dotGap={tuning.dotGap}
        lineWidth={tuning.lineWidth}
        speed={tuning.animated ? tuning.speed : 0}
        color={paint.ink}
        motion={DEFAULT_MOTION_PLANS}
        animated={tuning.animated}
      />
    </div>
  );
}
