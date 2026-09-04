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
 * words but the referents' own; hovering a disc names what it touches. A
 * filament is not a hover target — pointing at the line does not name it, does
 * not light it, and does not change the cursor. Selection still names, because
 * that is a choice rather than a pass.
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
import { Graph, type NodeData } from "@antv/g6";
import {
  BOND_LABEL_STACK_GAP,
  bondLabelLayout,
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
import {
  DEFAULT_MOTION_PLANS,
  NODE_BIRTH_PLAN,
  type MotionPlan,
  type MotionPlans,
} from "../styles/motion";
import { g6StateMotion } from "../styles/motionG6";
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
  resolveFocusId,
  useFocusPan,
  type CameraInsets,
} from "./canvasFocus";
import type { WorkingSet } from "./workingSet";
import {
  assertionShown,
  unsettled,
  type ShowState,
} from "./show";
import {
  IDLE_CONTACT,
  contactId,
  transitionContact,
  type ContactEvent,
  type ContactState,
} from "./canvasInteraction";

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
 * The live G6 edge, for a drag that must restation a plate without a draw.
 *
 * `graph.draw()` would re-apply stored node data and snap the mark back under
 * the pointer. The edge already re-strokes on each drag frame (`onframe`);
 * writing the 44px placement onto that same object is what keeps the plate
 * a fixed distance from the rim as the filament shortens.
 */
function liveEdge(
  graph: Graph,
  id: string,
): { parsedAttributes: Record<string, unknown>; onframe: () => void } | null {
  const context = (
    graph as unknown as {
      context?: { element?: { getElement: (id: string) => unknown } };
    }
  ).context;
  const el = context?.element?.getElement(id);
  if (!el || typeof el !== "object") return null;
  const edge = el as {
    parsedAttributes?: Record<string, unknown>;
    onframe?: () => void;
  };
  if (!edge.parsedAttributes || typeof edge.onframe !== "function") return null;
  return { parsedAttributes: edge.parsedAttributes, onframe: edge.onframe };
}

/** Centre a restored field once, after the renderer has its real host size. */
async function centreStandingField(
  graph: Graph,
  ids: string[],
  insets: CameraInsets,
) {
  const [width, height] = graph.getSize();
  const points = ids
    .map((id) => graph.getElementPosition(id))
    .filter((point): point is [number, number, number] => Boolean(point))
    .map((point) => graph.getViewportByCanvas(point));
  if (!width || !height || !points.length) return;
  const minX = Math.min(...points.map((point) => point[0]));
  const maxX = Math.max(...points.map((point) => point[0]));
  const minY = Math.min(...points.map((point) => point[1]));
  const maxY = Math.max(...points.map((point) => point[1]));
  await graph.translateBy(
    [
      (insets.left + width - insets.right - minX - maxX) / 2,
      (insets.top + height - insets.bottom - minY - maxY) / 2,
    ],
    false,
  );
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

/** Competing observer-field treatments kept together for the trial. */
export type SelectionTreatment =
  | "outer-field"
  | "excited-boundary"
  | "hollow";

export type MaterialTuning = {
  /** Off on the shipping surface until the lab trial is adjudicated. */
  contact: boolean;
  /** Resting diameter retained while pointer load is applied. */
  pressScale: number;
};

export const MATERIAL_DEFAULTS: MaterialTuning = {
  contact: false,
  pressScale: 0.96,
};

const CONTACT_STATE = "contact-load";

type ContactSize = number | [number, number] | [number, number, number];

function scaledContactSize(size: unknown, scale: number): ContactSize | undefined {
  if (typeof size === "number") return size * scale;
  if (
    Array.isArray(size) &&
    (size.length === 2 || size.length === 3) &&
    size.every((part) => typeof part === "number")
  ) {
    return size.map((part) => part * scale) as ContactSize;
  }
  return undefined;
}

function reducedMotion(): boolean {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

/**
 * A step load engages directly; removing it releases through the field spring.
 * G6 owns interpolation, while the state machine below owns the causal order.
 */
function contactNodeOptions(plan: MotionPlan, pressScale: number) {
  return {
    style: { cursor: "grab" as const },
    state: {
      [CONTACT_STATE]: {
        size: (datum: NodeData) =>
          scaledContactSize(datum.style?.size, pressScale),
        labelTransform: [
          ["scale", pressScale, pressScale],
        ] as [["scale", number, number]],
      },
    },
    animation: {
      state: [
        g6StateMotion(plan, { fields: ["size"] }),
        g6StateMotion(plan, { shape: "label", fields: ["transform"] }),
      ],
    },
  };
}

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
  animateInitial = false,
  insets,
  ants,
  motion = DEFAULT_MOTION_PLANS,
  material,
  selectionTreatment = "outer-field",
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
  /** The first mark was just requested, rather than restored from memory. */
  animateInitial?: boolean;
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
  /** Shared plans; the lab may slow the same laws for inspection. */
  motion?: MotionPlans;
  /** Trial-only contact mechanics. The product default remains inert. */
  material?: Partial<MaterialTuning>;
  /** How a selected referent binds to the observer field. */
  selectionTreatment?: SelectionTreatment;
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
  const motionRef = useRef(motion);
  motionRef.current = motion;
  const materialTuning = useMemo<MaterialTuning>(
    () => ({ ...MATERIAL_DEFAULTS, ...material }),
    [material],
  );
  const materialRef = useRef(materialTuning);
  materialRef.current = materialTuning;
  const contactRef = useRef<ContactState>(IDLE_CONTACT);
  const [contact, setContact] = useState<ContactState>(IDLE_CONTACT);
  const insetsRef = useRef(insets);
  insetsRef.current = insets;
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
  const paramsRef = useRef(params);
  paramsRef.current = params;
  const bondAnchorRef = useRef<string | null>(null);
  const spokeSubjectRef = useRef<string | null>(null);
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
  /**
   * The last referent the pointer actually entered.
   *
   * Crossing from a disc onto its bond label changes G6's hover subject to
   * the assertion. The plate has to keep the disc it was named from, not
   * whoever happens to be selected elsewhere, and not the midpoint G6 uses
   * when no endpoint is supplied. Selection only wins at rest.
   */
  const labelAnchorRef = useRef<string | null>(null);
  const latchedSelection = useRef<string | null>(null);
  if (selection?.kind === "referent" && latchedSelection.current !== selection.id) {
    latchedSelection.current = selection.id;
    labelAnchorRef.current = selection.id;
  }
  if (hovered && set.referents.has(hovered)) {
    labelAnchorRef.current = hovered;
  }
  const hoverReferent =
    hovered && set.referents.has(hovered) ? hovered : null;
  const selectedReferent =
    selection?.kind === "referent" ? selection.id : null;
  bondAnchorRef.current =
    hoverReferent ?? labelAnchorRef.current ?? selectedReferent;
  spokeSubjectRef.current =
    hovered &&
    (set.referents.has(hovered) ||
      set.assertions.has(hovered) ||
      set.demands.has(hovered))
      ? hovered
      : selection &&
          (selection.kind === "referent" ||
            selection.kind === "assertion" ||
            selection.kind === "demand")
        ? selection.id
        : null;
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
    /**
     * Parallel claims on one filament name each other. Hovering one plate
     * used to unname its neighbour (two hops via the disc), which collapsed
     * the stack and sent the remaining plate onto the line — the jump that
     * read as "back to centre".
     */
    const focus = hovered ?? selection?.id ?? null;
    const origin = focus
      ? set.bonds.find((bond) => bond.assertion_id === focus)
      : undefined;
    if (origin) {
      for (const bond of set.bonds) {
        const same =
          (bond.source === origin.source && bond.target === origin.target) ||
          (bond.source === origin.target && bond.target === origin.source);
        if (same) named.add(bond.assertion_id);
      }
    }
    return named;
  }, [hops, hovered, selection, set]);

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
      return {
        shape: "circle",
        id,
        diameter: params.discDiameter,
        ...(selectionTreatment === "outer-field" ? {} : { clearance: 0 }),
      };
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
  }, [params.discDiameter, selection, selectionTreatment, set, show]);

  const selectionArrivalDelay = useMemo(() => {
    const graph = graphRef.current;
    if (!ready || !selection || !graph || graph.destroyed) return 0;
    return resolveFocusId(graph, selection.id) ? 0 : NODE_BIRTH_PLAN.durationMs;
  }, [ready, selection]);

  const data = useMemo(() => {
    const nodes: unknown[] = [];
    const edges: unknown[] = [];
    const paintFor = (_id: string, overlay = false) =>
      overlay ? provisional : paint;
    const named = (id: string) => Boolean(namedMarks?.has(id));
    const hoverReferent =
      hovered && set.referents.has(hovered) ? hovered : null;
    const selectedReferent =
      selection?.kind === "referent" ? selection.id : null;
    const bondAnchor =
      hoverReferent ?? labelAnchorRef.current ?? selectedReferent;
    const spokeSubject =
      hovered &&
      (set.referents.has(hovered) ||
        set.assertions.has(hovered) ||
        set.demands.has(hovered))
        ? hovered
        : selection &&
            (selection.kind === "referent" ||
              selection.kind === "assertion" ||
              selection.kind === "demand")
          ? selection.id
          : null;
    const at = (id: string, fallback: { x: number; y: number } = { x: 0, y: 0 }) =>
      liveAt(liveRef.current, set.positions, id, fallback);
    const visibleBonds = set.bonds.filter(
      (bond) =>
        set.referents.has(bond.source) &&
        set.referents.has(bond.target) &&
        assertionShown(bond.origin, bond.mode, show),
    );
    /**
     * One stroke per pair of ends. Several claims between the same two
     * referents are still one filament — two wires would invent a geometry
     * the tuples do not have. The plates of those claims share the 44px
     * station and step along the filament's normal so each stays selectable.
     */
    const byEndpoints = new Map<string, typeof visibleBonds>();
    for (const bond of visibleBonds) {
      const key = [bond.source, bond.target].sort().join("\u0000");
      const group = byEndpoints.get(key) ?? [];
      group.push(bond);
      byEndpoints.set(key, group);
    }
    const stackByAssertion = new Map<string, number>();
    const filamentCarrier = new Set<string>();
    for (const unsorted of byEndpoints.values()) {
      const group = [...unsorted].sort((a, b) =>
        `${a.relation}\u0000${a.assertion_id}`.localeCompare(
          `${b.relation}\u0000${b.assertion_id}`,
        ),
      );
      if (group[0]) filamentCarrier.add(group[0].assertion_id);
      const gap = params.chipHeight + BOND_LABEL_STACK_GAP;
      const middle = (group.length - 1) / 2;
      group.forEach((bond, index) => {
        stackByAssertion.set(bond.assertion_id, (index - middle) * gap);
      });
    }

    for (const referent of set.referents.values()) {
      const stored = at(referent.id);
      const node = discNode(
        referent.id,
        stored.x,
        stored.y,
        referent.label,
        paintFor(referent.id),
        params,
      );
      /**
       * Contrast specimen only. It intentionally removes the referent's fill
       * so the trial can test whether that reads as selection or absence.
       * Outer-field and excited-boundary never mutate semantic matter.
       */
      if (
        selectionTreatment === "hollow" &&
        selection?.kind === "referent" &&
        selection.id === referent.id
      ) {
        node.style.fill = paint.canvas;
        node.style.fillOpacity = 1;
        node.style.labelFill = paint.ink;
      }
      nodes.push(node);
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
        const near =
          spokeSubject === spoke.id
            ? "source"
            : spokeSubject === assertion.assertion_id
              ? "target"
              : undefined;
        edges.push(
          spokeEdge(
            `${assertion.assertion_id}:${index}`,
            spoke.id,
            assertion.assertion_id,
            paintFor(assertion.assertion_id, overlay),
            params,
            {
              role: spoke.role,
              showRole: named(assertion.assertion_id),
              labelPlacement: bondLabelLayout(
                at(spoke.id),
                at(assertion.assertion_id),
                near,
                0,
                params,
                params.discDiameter / 2,
                params.chipHeight / 2,
              ).placement,
            },
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
        const near =
          spokeSubject === spoke.id
            ? "source"
            : spokeSubject === demand.key
              ? "target"
              : undefined;
        edges.push(
          spokeEdge(
            `${demand.key}:${index}`,
            spoke.id,
            demand.key,
            paintFor(demand.key),
            params,
            {
              role: spoke.role,
              showRole: named(demand.key),
              dotted: true,
              labelPlacement: bondLabelLayout(
                at(spoke.id),
                at(demand.key),
                near,
                0,
                params,
                params.discDiameter / 2,
                params.chipHeight / 2,
              ).placement,
            },
          ),
        );
      });
    }

    for (const bond of set.bonds) {
      if (!set.referents.has(bond.source) || !set.referents.has(bond.target)) continue;
      if (!assertionShown(bond.origin, bond.mode, show)) continue;
      const overlay = unsettled(bond.stale, bond.completeness);
      const near =
        bondAnchor === bond.source
          ? "source"
          : bondAnchor === bond.target
            ? "target"
            : undefined;
      const layout = bondLabelLayout(
        at(bond.source),
        at(bond.target),
        near,
        stackByAssertion.get(bond.assertion_id) ?? 0,
        params,
      );
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
            labelPlacement: layout.placement,
            labelOffsetX: layout.offsetX,
            labelOffsetY: layout.offsetY,
            carriesFilament: filamentCarrier.has(bond.assertion_id),
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
    selectionTreatment,
    incident,
    namedMarks,
    show,
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
      data: (animateInitial ? { nodes: [], edges: [] } : data) as never,
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
      node: contactNodeOptions(
        motion.hold,
        materialTuning.pressScale,
      ),
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
      relayoutIncidentLabels(id);
    };

    const relayoutIncidentLabels = (nodeId: string) => {
      const current = setRef.current;
      const p = paramsRef.current;
      const at = (id: string) => {
        const here = graph.getElementPosition(id);
        return here
          ? { x: here[0], y: here[1] }
          : liveAt(liveRef.current, current.positions, id);
      };
      const station = (elementId: string, layout: ReturnType<typeof bondLabelLayout>) => {
        const edge = liveEdge(graph, elementId);
        if (!edge) return;
        edge.parsedAttributes.labelPlacement = layout.placement;
        edge.parsedAttributes.labelOffsetX = layout.offsetX;
        edge.parsedAttributes.labelOffsetY = layout.offsetY;
        edge.onframe();
      };
      const visibleBonds = current.bonds.filter(
        (bond) =>
          current.referents.has(bond.source) &&
          current.referents.has(bond.target) &&
          (bond.source === nodeId || bond.target === nodeId),
      );
      const byEndpoints = new Map<string, typeof visibleBonds>();
      for (const bond of visibleBonds) {
        const key = [bond.source, bond.target].sort().join("\u0000");
        const group = byEndpoints.get(key) ?? [];
        group.push(bond);
        byEndpoints.set(key, group);
      }
      const stackByAssertion = new Map<string, number>();
      for (const unsorted of byEndpoints.values()) {
        const group = [...unsorted].sort((a, b) =>
          `${a.relation}\u0000${a.assertion_id}`.localeCompare(
            `${b.relation}\u0000${b.assertion_id}`,
          ),
        );
        const gap = p.chipHeight + BOND_LABEL_STACK_GAP;
        const middle = (group.length - 1) / 2;
        group.forEach((bond, index) => {
          stackByAssertion.set(bond.assertion_id, (index - middle) * gap);
        });
      }
      const bondAnchor = bondAnchorRef.current;
      for (const bond of visibleBonds) {
        const near =
          bondAnchor === bond.source
            ? "source"
            : bondAnchor === bond.target
              ? "target"
              : undefined;
        station(
          bondElementId(bond.assertion_id),
          bondLabelLayout(
            at(bond.source),
            at(bond.target),
            near,
            stackByAssertion.get(bond.assertion_id) ?? 0,
            p,
          ),
        );
      }
      const spokeSubject = spokeSubjectRef.current;
      const stationSpoke = (
        elementId: string,
        fromId: string,
        toId: string,
        subjectId: string,
      ) => {
        const near =
          spokeSubject === fromId
            ? "source"
            : spokeSubject === subjectId
              ? "target"
              : undefined;
        station(
          elementId,
          bondLabelLayout(
            at(fromId),
            at(toId),
            near,
            0,
            p,
            p.discDiameter / 2,
            p.chipHeight / 2,
          ),
        );
      };
      for (const assertion of current.assertions.values()) {
        assertion.spokes.forEach((spoke, index) => {
          if (!current.referents.has(spoke.id)) return;
          if (spoke.id !== nodeId && assertion.assertion_id !== nodeId) return;
          stationSpoke(
            `${assertion.assertion_id}:${index}`,
            spoke.id,
            assertion.assertion_id,
            assertion.assertion_id,
          );
        });
      }
      for (const demand of current.demands.values()) {
        demand.spokes.forEach((spoke, index) => {
          if (!current.referents.has(spoke.id)) return;
          if (spoke.id !== nodeId && demand.key !== nodeId) return;
          stationSpoke(
            `${demand.key}:${index}`,
            spoke.id,
            demand.key,
            demand.key,
          );
        });
      }
    };

    let ignoreClickUntil = 0;
    const publishContact = (event: ContactEvent) => {
      const next = transitionContact(contactRef.current, event);
      if (next === contactRef.current) return next;
      contactRef.current = next;
      setContact(next);
      return next;
    };
    const elementStatesWithoutContact = (id: string) =>
      graph.getElementState(id).filter((state) => state !== CONTACT_STATE);
    const engageContact = (id: string) => {
      if (!materialRef.current.contact || isDecoration(id)) return;
      const next = publishContact({ type: "press", id });
      if (next.phase !== "pressed" || next.id !== id) return;
      graph.setNode(
        contactNodeOptions(
          motionRef.current.hold,
          materialRef.current.pressScale,
        ),
      );
      const states = elementStatesWithoutContact(id);
      void graph
        .setElementState(
          { [id]: [...states, CONTACT_STATE] },
          !reducedMotion(),
        )
        .catch(() => undefined);
      return next;
    };
    const releaseContact = () => {
      const next = publishContact({ type: "release" });
      if (next.phase !== "releasing") return;
      const { id } = next;
      graph.setNode(
        contactNodeOptions(
          motionRef.current.settle,
          materialRef.current.pressScale,
        ),
      );
      void graph
        .setElementState(
          { [id]: elementStatesWithoutContact(id) },
          !reducedMotion(),
        )
        .catch(() => undefined)
        .finally(() => publishContact({ type: "settled", id }));
    };
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
    graph.on("node:pointerleave", () => hovering(null));
    graph.on("node:pointerdown", (event) => {
      const id = subject(idOf(event));
      if (id) engageContact(id);
    });
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
      if (id) {
        publishContact({ type: "drag", id });
        followFurniture(id);
      }
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
      releaseContact();
    });

    // G6 owns picking, but release belongs to the pointer even when it leaves
    // the canvas. A lost release would leave matter compressed indefinitely.
    window.addEventListener("pointerup", releaseContact);
    window.addEventListener("pointercancel", releaseContact);

    void graph
      .render()
      .then(async () => {
        if (graphRef.current !== graph) return;
        if (!animateInitial && data.nodes.length) {
          if (data.nodes.length === 1) await graph.zoomTo(1, { duration: 0 });
        }
        if (graphRef.current === graph) setReady(true);
      })
      .catch((problem: unknown) => {
        if (graphRef.current === graph) console.error(problem);
      });
    // A canvas has no DOM to address, so in development the field graph is
    // reachable for a browser-automated material check. This has its own name:
    // SchemaCanvas also exposes a graph, and a lab may mount both at once.
    if (import.meta.env.DEV) {
      (window as unknown as { __worldFieldGraph?: Graph }).__worldFieldGraph = graph;
    }
    return () => {
      host.removeEventListener("contextmenu", blockMenu);
      window.removeEventListener("pointerup", releaseContact);
      window.removeEventListener("pointercancel", releaseContact);
      graphRef.current = null;
      setReady(false);
      if (
        (window as unknown as { __worldFieldGraph?: Graph }).__worldFieldGraph ===
        graph
      ) {
        delete (window as unknown as { __worldFieldGraph?: Graph })
          .__worldFieldGraph;
      }
      graph.destroy();
    };
    // The graph is created once. Data changes go through the effect below, so
    // an expansion never re-mounts the canvas and never resets the view.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const graph = graphRef.current;
    if (
      !ready ||
      !stageSize.width ||
      !stageSize.height ||
      !graph ||
      draggingRef.current
    ) return;
    let cancelled = false;
    const next = {
      nodes: data.nodes as CanvasDatum[],
      edges: data.edges as CanvasDatum[],
    };

    void (async () => {
      try {
        /**
         * Restored data was already rendered by the constructor. Do not send
         * it through a no-op animated draw before centring: G6 completes that
         * camera-affecting frame after the draw promise and used to undo the
         * vertical half of the centre operation.
         */
        if (!animateInitial && drawnRef.current === 0 && next.nodes.length) {
          drawnRef.current = next.nodes.length;
          if (next.nodes.length === 1) {
            await graph.zoomTo(1, { duration: 0 });
          }
          await centreStandingField(
            graph,
            next.nodes
              .map((node) => node.id)
              .filter((id) => !isDecoration(id)),
            insetsRef.current,
          );
          return;
        }
        await transitionCanvasData(
          graph,
          next,
          () => cancelled || graphRef.current !== graph,
          { stellarNodes: true },
        );
        if (cancelled || graphRef.current !== graph) return;
        const count = next.nodes.length;
        const grew = count > drawnRef.current;
        drawnRef.current = count;
        /* A first seed still needs a unit zoom. Growth from Expand through
           must not pan: new marks appear where they were placed. */
        if (grew && count === 1) {
          await graph.zoomTo(1, { duration: 0 });
        }
      } catch (problem: unknown) {
        if (graphRef.current === graph) console.error(problem);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [animateInitial, data, ready, stageSize.height, stageSize.width]);

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
    <div
      className="world__stage"
      data-contact-phase={contact.phase}
      data-selection-treatment={selectionTreatment}
    >
      <div className="world__surface" ref={hostRef} />
      <SelectionAnts
        graph={ready ? graphRef.current : null}
        target={antTarget}
        clearance={tuning.clearance}
        dotGap={tuning.dotGap}
        lineWidth={tuning.lineWidth}
        speed={tuning.animated ? tuning.speed : 0}
        color={
          antTarget?.shape === "circle" &&
          selectionTreatment === "excited-boundary"
            ? paint.canvas
            : paint.ink
        }
        motion={motion}
        arrivalDelay={selectionArrivalDelay}
        animated={tuning.animated}
        held={contactId(contact) === selection?.id}
      />
    </div>
  );
}
