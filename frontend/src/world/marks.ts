/**
 * How World IR matter is drawn — one source, for every surface that draws it.
 *
 * Two marks. A **disc** is a referent: something the world can name. A **chip**
 * is an assertion: one tuple of one named relation. A chip on a filament is a
 * binary tuple collapsed onto the bond it makes; the same chip standing on the
 * field with a spoke per role is a tuple that has more roles than a line can
 * carry. They are the same plate in two positions, and that is the whole claim
 * — so they are built here by the same function rather than by two surfaces
 * that happen to agree.
 *
 * This module exists because the assertion board authored these marks and the
 * schema canvas draws them, and a copy in each is exactly the drift
 * `graphDna.ts` was written to stop. Geometry comes from `GRAPH_DNA_CHIP`;
 * paint comes from the theme the caller is in, so a stale relation can be
 * handed the provisional palette without this module knowing what stale means.
 */

import { GRAPH_DNA_CHIP, GRAPH_DNA_GEOMETRY, radixValue } from "../styles/graphDna";
import type { GraphDnaTheme } from "../styles/graphDna";
import { FONT_SANS_FAMILY } from "../styles/typography";
import { WORLD_FILAMENT_EDGE } from "./filaments";

/**
 * The weight the product canvas draws node labels at.
 *
 * Not 600. `ProductGraphCanvas` ships `labelFontWeight ?? 400`, and Jost at 400
 * is already the sharp geometric face the map is built on.
 */
export const DISC_LABEL_WEIGHT = 400;

export type MarkParams = typeof GRAPH_DNA_CHIP & {
  discDiameter: number;
  edgeWidth: number;
  edgeOpacity: number;
  /** What a node rests at, so light has room. See `GRAPH_DNA_GEOMETRY`. */
  nodeAlbedo: number;
  dottedGap: number;
  /**
   * Whether a mechanical chip carries its own outline.
   *
   * On a filament the chip needs none — the line it interrupts is what holds
   * it. Detached on the field it may need one, or it floats.
   */
  mechanicalOutline: boolean;
};

export const MARK_DEFAULTS: MarkParams = {
  ...GRAPH_DNA_CHIP,
  discDiameter: GRAPH_DNA_GEOMETRY.nodeDiameter,
  edgeWidth: GRAPH_DNA_GEOMETRY.edgeWidth,
  edgeOpacity: GRAPH_DNA_GEOMETRY.edgeOpacity,
  nodeAlbedo: GRAPH_DNA_GEOMETRY.nodeAlbedo,
  dottedGap: GRAPH_DNA_GEOMETRY.dottedGap,
  mechanicalOutline: true,
};

/** The DNA palette, resolved to paint. */
export type Paint = {
  canvas: string;
  ink: string;
  field: string;
  chip: string;
  muted: string;
};

export function paintOf(theme: GraphDnaTheme): Paint {
  return {
    canvas: radixValue(theme.canvas),
    ink: radixValue(theme.node),
    field: radixValue(theme.nodeLabel),
    chip: radixValue(theme.chip),
    muted: radixValue(theme.lensLabel),
  };
}

let measurer: CanvasRenderingContext2D | null = null;

function metricsOf(text: string, size: number, weight: number): TextMetrics | null {
  if (!measurer) {
    measurer = document.createElement("canvas").getContext("2d");
  }
  if (!measurer) return null;
  // The weight has to be the one that will be drawn. Measuring at one weight
  // and painting at another gives every plate a few pixels of padding it did
  // not ask for, on one side, which reads as a centring bug rather than a width.
  measurer.font = `${weight} ${size}px ${FONT_SANS_FAMILY}`;
  return measurer.measureText(text);
}

/**
 * Chip width comes from the word in it.
 *
 * Measured rather than estimated: relation names in this world run from
 * `used_in` to `acceptable_replacement`, and a fixed plate wide enough for the
 * second is a lie about the first.
 */
export function textWidth(text: string, size: number, weight: number): number {
  return metricsOf(text, size, weight)?.width ?? text.length * size * 0.6;
}

/*
 * There was an `opticalNudge` here, and it was the miscentring rather than the
 * cure for it.
 *
 * The theory was that a label is placed on the font's baseline box, whose
 * middle sits above the ink's middle, so a name with a descender rides high in
 * a 10px plate and wants pushing down by `(ascent - descent) / 2`. Measured on
 * four plates at once, the ink's centre came out below the rect's centre by
 * *exactly* the offset applied — 1.5 for `requires_temperature`, 2.0 for
 * `candidate_replacement`, `eligible_part` and `viable_replacement`. Residual
 * equal to the correction means the correction is the whole error: G6 already
 * centres the label's ink box on the node, and every plate in the product was
 * being shoved 1.5–2px down a 10px plate, a sixth of its height.
 *
 * Distinguishing "centres the ink" from "centres the em box" matters, because
 * the second would still need a correction: for Jost at 7px the two differ by
 * 0.5px. A residual of exactly the offset, with no 0.5 left over, says it is
 * the ink.
 *
 * `chipLabelNudge` stays. It is the human residue, and it is 0.
 */

export function chipWidth(text: string, p: MarkParams): number {
  return Math.round(
    textWidth(text, p.chipLabelSize, p.chipLabelWeight) + p.chipPaddingX * 2,
  );
}

export type ChipKind =
  | "mechanical"
  | "semantic"
  | "unresolved"
  | "adjudicated";

/**
 * Which mark a relation gets, decided by how many of its roles are referents.
 *
 * Arity alone is the wrong question. `temperature_range(part, minimum_c,
 * maximum_c)` is a ternary, but two of its roles are numbers — it is one part
 * carrying a compound value, not three things meeting. What decides the
 * projection is how many referents are in the tuple: two make a bond, more
 * make a meeting, one makes a property of a single thing.
 */
export function projectionOf(arity: number, referentArity: number) {
  if (referentArity >= 3) return "assertion" as const;
  if (referentArity === 2) return "bond" as const;
  if (referentArity === 1 && arity === 2) return "field" as const;
  return "property" as const;
}

export function discNode(
  id: string,
  x: number,
  y: number,
  label: string,
  paint: Paint,
  p: MarkParams,
) {
  return {
    id,
    type: "circle",
    style: {
      x,
      y,
      size: p.discDiameter,
      // Presence, not brightness — see `spokeEdge` for the same split on a
      // line. A disc's material is its fill, and it rests below full so the
      // light law has somewhere to take it. Sending `opacity` down instead
      // would take the label with it: a name is not lit, it is read.
      opacity: 1,
      fill: paint.ink,
      fillOpacity: p.nodeAlbedo,
      /**
       * No stroke. A referent is a mass, not an outline.
       *
       * It used to carry `stroke: paint.ink` at `nodeLine` — the same colour
       * as the fill, so at rest it was invisible and cost nothing. Below full
       * opacity it stopped being invisible: a canvas paints fill and stroke as
       * two operations, and a stroke straddling the fill's edge composites
       * twice over its inner half, so any dimming grew a darker rim on every
       * disc. A border that can only ever be the fill colour is not a border.
       */
      lineWidth: 0,
      labelText: label,
      labelPlacement: "center" as const,
      // Contact scales the already-laid-out name with its body. Keeping a
      // canonical identity transform prevents G6 from inventing a transform
      // origin on the first pressed frame and changing line breaks mid-load.
      labelTransform: [["scale", 1, 1]] as [["scale", number, number]],
      labelTransformOrigin: "0px 0px",
      labelFill: paint.field,
      labelFontFamily: FONT_SANS_FAMILY,
      labelFontSize: GRAPH_DNA_GEOMETRY.labelSize,
      labelFontWeight: DISC_LABEL_WEIGHT,
      labelLineHeight:
        GRAPH_DNA_GEOMETRY.labelSize * GRAPH_DNA_GEOMETRY.labelLineHeight,
      labelOffsetY: GRAPH_DNA_GEOMETRY.labelBaselineNudge,
      labelWordWrap: true,
      labelMaxWidth: p.discDiameter * (GRAPH_DNA_GEOMETRY.labelMaxWidth / 100),
      labelMaxLines: GRAPH_DNA_GEOMETRY.labelMaxLines,
      labelTextOverflow: "ellipsis" as const,
    },
  };
}

/**
 * The plate a construction origin gets.
 *
 * `unresolved` is not reachable from here: it is a state of a claim, not an
 * account of who made it, so it is applied by whoever knows that — never by
 * reading an origin.
 */
export function chipKindOf(origin: string): ChipKind {
  if (origin === "ADJUDICATED") return "adjudicated";
  if (origin === "SEMANTIC") return "semantic";
  return "mechanical";
}

/**
 * Whether a plate is filled rather than outlined.
 *
 * Filled means a person authored the claim — the constructor for SEMANTIC, a
 * human for ADJUDICATED — and the two forms the plate can take, standing on
 * the field and riding a filament, both ask here so they cannot drift into
 * disagreeing about the same tuple.
 */
export function isAuthored(kind: ChipKind | undefined): boolean {
  return kind === "semantic" || kind === "adjudicated";
}

/** The plate. One tuple of one relation, standing on the field. */
export function chipNode(
  id: string,
  x: number,
  y: number,
  text: string,
  kind: ChipKind,
  paint: Paint,
  p: MarkParams,
) {
  const filled = isAuthored(kind);
  const outlined =
    kind === "unresolved" || (kind === "mechanical" && p.mechanicalOutline);
  return {
    id,
    type: "rect",
    style: {
      x,
      y,
      size: [chipWidth(text, p), p.chipHeight] as [number, number],
      radius: p.chipRadius,
      opacity: 1,
      // A knockout, not a card: the plate is the field exactly, so filaments
      // running under it stop being read rather than being covered by a
      // second colour.
      fill: filled ? paint.ink : paint.chip,
      // Hollow stays hollow; everything else rests at the albedo. Both
      // channels, because an outlined plate carries its meaning in the stroke
      // and lighting only the fill would leave it dark while its neighbours
      // brightened.
      fillOpacity: kind === "unresolved" ? 0 : p.nodeAlbedo,
      stroke: paint.ink,
      strokeOpacity: p.nodeAlbedo,
      lineWidth: outlined ? p.chipLine : 0,
      lineDash:
        kind === "unresolved" ? ([0, p.dottedGap] as [number, number]) : undefined,
      lineCap: "round" as const,
      labelText: text,
      labelPlacement: "center" as const,
      labelTransform: [["scale", 1, 1]] as [["scale", number, number]],
      labelTransformOrigin: "0px 0px",
      labelFill: filled ? paint.field : paint.ink,
      labelFontFamily: FONT_SANS_FAMILY,
      labelFontSize: p.chipLabelSize,
      labelFontWeight: p.chipLabelWeight,
      labelOffsetY: p.chipLabelNudge,
    },
  };
}

/**
 * Which side of the chip a rule sits on, and therefore what it means.
 *
 * `under` is the derived shelf: this rests on something. `over` is the
 * adjudicated crown: someone stood over this. The two are deliberately the
 * same shape mirrored, because they are the same claim about a chip pointed
 * in opposite directions — one names what the assertion leans on, the other
 * names who put it there.
 */
export type RuleSide = "under" | "over";

/**
 * Nodes that draw a mark's state rather than being a mark.
 *
 * The derived shelf and the adjudicated crown are separate nodes because a
 * rect cannot carry a second rule, but neither is a thing on the field: they
 * have no position of their own to harvest and nothing to select. Every guard
 * that cares — reading dragged positions back, resolving a click to a subject,
 * refusing a drag — asks this rather than testing prefixes, so the next piece
 * of chip furniture is one line here instead of a bug in whichever site was
 * missed. It lives beside `shelfNode` because that is what emits them.
 */
const DECORATION = /^(shelf|crown):/;

export function isDecoration(id: string): boolean {
  return DECORATION.test(id);
}

/** Shelf and crown hanging off a chip, keyed from the chip's own id. */
export function furnitureOf(id: string): string[] {
  return [`shelf:${id}`, `crown:${id}`];
}

/**
 * The rule under a derived chip, or over an adjudicated one.
 *
 * Measured from the word, not from the plate: a rule the width of the box
 * reads as a second edge of the box, where the width of the name plus a little
 * air reads as the name resting on — or being held down by — something.
 *
 * A separate element rather than part of the plate, because the plate is a
 * `rect` and a second rule is a second shape. Both surfaces and both sides
 * place it through this function, so a shelf and a crown can only ever be
 * apart by the gap they are given.
 */
export function shelfNode(
  id: string,
  x: number,
  y: number,
  text: string,
  paint: Paint,
  p: MarkParams,
  side: RuleSide = "under",
) {
  const width =
    textWidth(text, p.chipLabelSize, p.chipLabelWeight) + p.shelfOverhang * 2;
  const offset = p.chipHeight / 2 + p.shelfGap;
  return {
    id,
    type: "rect",
    style: {
      x,
      y: side === "under" ? y + offset : y - offset,
      size: [Math.max(4, Math.round(width)), p.shelfLine] as [number, number],
      radius: 0,
      opacity: 1,
      fill: paint.ink,
      lineWidth: 0,
      labelText: "",
      // Furniture is not a mark. It sits on the chip and would swallow the
      // drag that belongs to the plate underneath.
      pointerEvents: "none" as const,
    },
  };
}

export type SpokeOptions = {
  role?: string;
  dotted?: boolean;
  showRole: boolean;
  /** Placement along the spoke, 0 at the referent. */
  labelPlacement?: number;
};

/** A referent filling a role in an assertion. */
export function spokeEdge(
  id: string,
  source: string,
  target: string,
  paint: Paint,
  p: MarkParams,
  options: SpokeOptions,
) {
  return {
    id,
    type: WORLD_FILAMENT_EDGE,
    source,
    target,
    style: {
      stroke: paint.ink,
      lineWidth: p.roleSpokeWidth,
      // Two channels, and the split is the point.
      //
      // `opacity` is presence: 0 while the spoke is being born or absorbed,
      // 1 once it is here, and nothing else touches it. `strokeOpacity` is
      // what the line is made of — quiet, because a role spoke is scaffolding
      // — and it is the channel light reflects off.
      //
      // They were one channel until the light law had something to say. G6
      // composites element opacity into the label group, so a spoke drawn at
      // 0.5 drew its name at 0.5 too: grey on grey. The old fix was to send
      // the whole spoke to full strength the moment it was named, which read
      // well and cost the law its subject — the falloff had nothing left to
      // act on, and a spoke you pointed at doubled instead of brightening.
      // Dimming the stroke alone leaves the name at the strength stated below.
      opacity: 1,
      strokeOpacity: p.roleSpokeOpacity,
      lineCap: "round" as const,
      lineDash: options.dotted ? ([0, p.dottedGap] as [number, number]) : undefined,
      // G6 draws edges after nodes, so a spoke through a disc sits on top of
      // it. The stroke must not steal the drag; the role plate still takes
      // the pointer when it is named.
      pointerEvents: "none" as const,
      labelPointerEvents: options.showRole ? "auto" as const : "none" as const,
      labelText: options.role ?? "",
      labelFontFamily: FONT_SANS_FAMILY,
      labelFontSize: p.roleLabelSize,
      labelFontWeight: p.roleLabelWeight,
      labelFill: paint.ink,
      // Stated, not inherited — and now actually so. A label left to take the
      // edge's opacity is a name drawn at the strength of the line under it,
      // which is backwards: the filament is quiet so the name can be read
      // over it.
      labelOpacity: options.showRole ? 1 : 0,
      labelBackground: true,
      labelBackgroundOpacity: options.showRole ? 1 : 0,
      labelBackgroundFill: paint.chip,
      labelBackgroundLineWidth: 0,
      labelBackgroundRadius: p.chipRadius,
      labelPadding: [p.chipPaddingY, p.chipPaddingX] as [number, number],
      labelAutoRotate: false,
      // Same as a bond: G6's BaseEdge default is 4px of unstated X, which
      // shoved every role name off the spoke and made two of them look like
      // they were fighting the plate rather than sitting on their own lines.
      labelOffsetX: 0,
      labelOffsetY: 0,
      labelPlacement: options.labelPlacement ?? p.roleLabelAt,
    },
  };
}

/**
 * How far a bond's plate sits from the rim of the referent that named it.
 *
 * This is the product canvas's old, measured value. It is a distance rather
 * than a percentage: a named bond must not drift toward the midpoint merely
 * because somebody dragged its other end farther away. It is held against the
 * rim the renderer actually clips to — see `rimDistance` — because a share of
 * an assumed length is a percentage again, wearing a distance's clothes.
 */
export const BOND_LABEL_ALONG_PX = 44;

/**
 * The same station for a spoke, which has far less room to hold it in.
 *
 * A bond runs disc to disc and its air is measured in hundreds of pixels; a
 * spoke runs from a disc to the plate standing beside it, and measured across
 * a populated field every one of its 66 spokes had a rim gap between 11 and
 * 73px — median 50. A 44px station does not fit *any* of them, so a role name
 * asked for one fell back to the midpoint every time, which is a ratio, which
 * is the thing this constant exists to avoid.
 *
 * 16px clears the disc's rim and still fits the gap outright on nine spokes in
 * ten. It is a distance for the same reason 44 is.
 */
export const SPOKE_LABEL_ALONG_PX = 16;

/**
 * Air between stacked plates that share a filament, in graph pixels.
 *
 * Two, not four. A plate is ten tall and carries seven-pixel text, so four
 * made the step 14 — twice the type size, which no one sets leading at. The
 * stack read as a list of separate things rather than one filament's names.
 */
export const BOND_LABEL_STACK_GAP = 2;

/**
 * How many of a group's plates the filament will carry.
 *
 * The count exists because a stack of names is not readable at rest; opening it
 * does not make an unbounded stack readable either, it only defers the same
 * problem to the pointer. Past this many, the filament says how many it is not
 * showing and the reader carries the rest — the reader is already open, because
 * opening the group requires having selected an endpoint.
 */
export const BOND_LABEL_STACK_MAX = 4;

/**
 * The step from one plate to the next when a filament carries several names.
 *
 * Screen-Y, one plate height plus its air, and nothing else. Two axis-aligned
 * boxes of equal height separated by more than that height in Y cannot
 * overlap, whatever their widths and whatever the filament is doing — so this
 * is both provably safe and the shortest step that is.
 *
 * It replaced a stack along the filament's own normal, which was the intuitive
 * answer and was wrong twice. A normal has to clear by plate *width* when it
 * turns horizontal, which on a near-vertical filament flung a pair of names 85
 * pixels apart — measured on this field. And a normal turns as its mark is
 * dragged, so the offsets moved under a stack that was supposed to be still.
 * Constant offsets make the whole stack rigid: the station travels, the plates
 * ride it, and nothing inside the group moves relative to anything else.
 *
 * What it costs: on a steep filament a Y offset slides a plate *along* the
 * line, so a stacked plate sits up to one step nearer or further from the rim
 * than the station it was given. Every rule that spreads plates at all pays
 * some version of that, and one plate height is the least any of them pays.
 */
export function bondLabelStep(p: MarkParams): { x: number; y: number } {
  return { x: 0, y: p.chipHeight + BOND_LABEL_STACK_GAP };
}

export type BondLabelLayout = {
  placement: number;
  offsetX: number;
  offsetY: number;
};

/**
 * Unit perpendicular of a filament, locked so +offset is screen-up.
 *
 * Without the lock, reversing source/target flipped the stack and a pair of
 * plates would swap sides the moment someone hovered the other disc.
 */
export function stableFilamentNormal(
  source: { x: number; y: number },
  target: { x: number; y: number },
): { x: number; y: number } {
  const dx = target.x - source.x;
  const dy = target.y - source.y;
  const len = Math.hypot(dx, dy);
  if (!(len > 1)) return { x: 0, y: -1 };
  let nx = -dy / len;
  let ny = dx / len;
  if (ny > 0 || (ny === 0 && nx < 0)) {
    nx = -nx;
    ny = -ny;
  }
  return { x: nx, y: ny };
}

/**
 * Where a mark's rim is, as the renderer will actually clip to it.
 *
 * `labelPlacement` is a share of the *drawn* stroke, and the drawn stroke runs
 * rim to rim, so turning a distance into a share requires knowing where those
 * rims are. Assuming a radius is what made the distance drift: a plate is only
 * `chipHeight / 2` from its centre when the stroke arrives vertically, and up
 * to `chipWidth / 2` when it arrives along the plate, so a mark orbiting one
 * moved its own name while nothing about the station had changed.
 */
export type MarkRim =
  | { shape: "disc"; radius: number }
  | { shape: "plate"; halfWidth: number; halfHeight: number };

export function discRim(p: MarkParams): MarkRim {
  return { shape: "disc", radius: p.discDiameter / 2 };
}

export function plateRim(text: string, p: MarkParams): MarkRim {
  return {
    shape: "plate",
    halfWidth: chipWidth(text, p) / 2,
    halfHeight: p.chipHeight / 2,
  };
}

/**
 * How far the rim is from the centre, along one direction.
 *
 * G6 clips an edge at the node's bounding box, so a rectangle's rim is
 * whichever of its two half-extents the ray leaves through first. Measured
 * against the running canvas: a 32×10 plate clips at 5px vertically and 16px
 * horizontally, which is exactly this.
 */
export function rimDistance(rim: MarkRim, dx: number, dy: number): number {
  if (rim.shape === "disc") return rim.radius;
  const len = Math.hypot(dx, dy);
  if (!(len > 1e-6)) return rim.halfHeight;
  const cos = Math.abs(dx) / len;
  const sin = Math.abs(dy) / len;
  const byWidth = cos > 1e-6 ? rim.halfWidth / cos : Number.POSITIVE_INFINITY;
  const byHeight = sin > 1e-6 ? rim.halfHeight / sin : Number.POSITIVE_INFINITY;
  return Math.min(byWidth, byHeight);
}

/** The drawn stroke's length: centre to centre, less both rims. */
function filamentLength(
  source: { x: number; y: number },
  target: { x: number; y: number },
  fromRim: MarkRim,
  toRim: MarkRim,
): number {
  const dx = target.x - source.x;
  const dy = target.y - source.y;
  const centres = Math.hypot(dx, dy);
  return Math.max(
    0,
    centres - rimDistance(fromRim, dx, dy) - rimDistance(toRim, dx, dy),
  );
}

/**
 * The station, in pixels from the rim that named it.
 *
 * `BOND_LABEL_ALONG_PX` unconditionally, with one geometric guard: a plate
 * cannot stand farther out than the midpoint or it would cross to the other
 * mark's side, and on a filament shorter than twice the station the midpoint
 * *is* the only station both ends can agree on. The two agree exactly at
 * `2 × BOND_LABEL_ALONG_PX`, so the guard engages without a step.
 *
 * There used to be a `filament * 0.45` cap here and it was the bug: it took
 * hold at a rim gap of 98px rather than 88px, and between those it made the
 * distance a *percentage*. Measured on the running canvas, dragging one end of
 * a bond in from 210px of air to 6px slid its name from 44px off the rim to
 * 2.7px — the plate crawling down its own filament as the mark moved.
 */
export function bondLabelAlong(
  source: { x: number; y: number },
  target: { x: number; y: number },
  p: MarkParams,
  fromRim: MarkRim = discRim(p),
  toRim: MarkRim = discRim(p),
  station = BOND_LABEL_ALONG_PX,
): number {
  const filament = filamentLength(source, target, fromRim, toRim);
  return filament > 1 ? Math.min(station, filament / 2) : 0;
}

export function bondLabelPlacement(
  source: { x: number; y: number },
  target: { x: number; y: number },
  near: "source" | "target" | undefined,
  p: MarkParams,
  fromRim: MarkRim = discRim(p),
  toRim: MarkRim = discRim(p),
  station = BOND_LABEL_ALONG_PX,
): number {
  if (!near) return 0.5;
  const filament = filamentLength(source, target, fromRim, toRim);
  if (!(filament > 1)) return 0.5;
  const along = bondLabelAlong(source, target, p, fromRim, toRim, station);
  return near === "source" ? along / filament : 1 - along / filament;
}

/**
 * Where a bond's plate sits: a fixed distance from the acted-on rim, plus
 * whatever shift its place in a stack of claims earns it.
 *
 * G6's `labelOffsetX/Y` are graph-space and are not rotated into the edge, so
 * the shift arrives already resolved into those two numbers — see
 * `bondLabelStep`, which decides how far and along what.
 *
 * The rims are the caller's to state. A spoke ends on a plate, and a plate
 * handed `discRim` — or its own height as a radius — puts its name somewhere
 * that depends on the angle the stroke arrives at.
 */
export function bondLabelLayout(
  source: { x: number; y: number },
  target: { x: number; y: number },
  near: "source" | "target" | undefined,
  stack: { x: number; y: number },
  p: MarkParams,
  fromRim: MarkRim = discRim(p),
  toRim: MarkRim = discRim(p),
  station = BOND_LABEL_ALONG_PX,
): BondLabelLayout {
  const placement = bondLabelPlacement(
    source,
    target,
    near,
    p,
    fromRim,
    toRim,
    station,
  );
  const nudge = p.chipLabelNudge;
  return { placement, offsetX: stack.x, offsetY: stack.y + nudge };
}

/** A plain filament, with or without its name showing. */
export function filamentEdge(
  id: string,
  source: string,
  target: string,
  paint: Paint,
  p: MarkParams,
  options: {
    label?: string;
    named: boolean;
    kind?: ChipKind;
    /** Placement derived from a fixed physical distance, after clipping. */
    labelPlacement?: number;
    /** Graph-space shift of the plate, from `bondLabelLayout`. */
    labelOffsetX?: number;
    labelOffsetY?: number;
    /** Parallel claims share one physical filament instead of darkening it. */
    carriesFilament?: boolean;
  },
) {
  const named = options.named && Boolean(options.label);
  // A bond's plate is the same plate, so it fills on the same rule. What it
  // cannot carry is furniture: a label background has no side to hang a shelf
  // or a crown from, so a derived or adjudicated binary is drawn detached —
  // see `schemaGraph`, which takes exactly that exception.
  const filled = isAuthored(options.kind);
  const plateWidth = options.label ? chipWidth(options.label, p) : 0;
  const carries = options.carriesFilament !== false;
  return {
    id,
    type: WORLD_FILAMENT_EDGE,
    source,
    target,
    style: {
      stroke: paint.ink,
      lineWidth: carries ? p.edgeWidth : 0,
      // See `spokeEdge` for why these are two channels: presence, then
      // material. A bond is quiet for the same reason a spoke is, and its
      // name is legible for the same reason.
      opacity: 1,
      strokeOpacity: carries ? p.edgeOpacity : 0,
      // G6's theme adds 2px of hit padding. A ghost filament that still
      // catches the pointer steals clicks from the plate sitting beside it.
      increasedLineWidthForHitTesting: carries ? 2 : 0,
      lineCap: "round" as const,
      // Same create-order problem as a spoke: the filament is drawn through
      // the disc, on top of it. The line is not a grab target; the plate is.
      pointerEvents: "none" as const,
      labelPointerEvents: named ? "auto" as const : "none" as const,
      labelCursor: named ? ("pointer" as const) : undefined,
      labelText: options.label ?? "",
      labelFontFamily: FONT_SANS_FAMILY,
      labelFontSize: p.chipLabelSize,
      labelFontWeight: p.chipLabelWeight,
      labelFill: filled ? paint.field : paint.ink,
      labelOffsetX: options.labelOffsetX ?? 0,
      labelOffsetY: options.labelOffsetY ?? p.chipLabelNudge,
      labelOpacity: named ? 1 : 0,
      labelBackground: true,
      labelBackgroundOpacity: named ? 1 : 0,
      labelBackgroundFill: filled ? paint.ink : paint.chip,
      labelBackgroundLineWidth: 0,
      labelBackgroundRadius: p.chipRadius,
      // Stated as the standing plate's size, not grown from the glyph box.
      // G6's label background otherwise paints an 8px rule around a 7px
      // word, and selection tracing a 10px chip around that is the box
      // that never quite sat on the plate.
      labelBackgroundWidth: plateWidth,
      labelBackgroundHeight: p.chipHeight,
      labelPadding: [p.chipPaddingY, p.chipPaddingX] as [number, number],
      labelAutoRotate: false,
      labelPlacement: options.labelPlacement ?? 0.5,
    },
  };
}

/**
 * How many claims a filament carries — said by the observer, not by the world.
 *
 * Parallel assertions share one physical filament, so at rest their plates are
 * a stack of names for a line that has no name of its own. The count stands in
 * for them until someone looks, and the whole difficulty is that it must not be
 * mistaken for one of them.
 *
 * So it is not a plate. A plate is where construction origin lives — filled for
 * SEMANTIC and ADJUDICATED, knocked out for MECHANICAL — and a summary spanning
 * four origins that wore any one of them would be asserting a fifth thing that
 * nothing constructed. What is left is the knockout alone, square, so the
 * filament stops being read under the words without a card appearing where a
 * claim would be. Furniture is never a hit target either: the assertions
 * underneath stay the only things a person can take hold of.
 *
 * Its ink is a name's ink. Muting it was reading furniture as *quieter*, which
 * is a light claim, and light here means proximity to what a person acted on —
 * so a count standing exactly where its claims will stand, at the same moment,
 * was drawn dimmer than them for a reason nothing in the field could name. The
 * count is not a name because it has no plate, which is structure, and
 * structure is what carries meaning here. Legibility is not the axis it is
 * allowed to differ on.
 */
export function summaryEdge(
  id: string,
  source: string,
  target: string,
  paint: Paint,
  p: MarkParams,
  options: {
    label: string;
    shown: boolean;
    /**
     * Whether the pointer can reach it.
     *
     * Only while the count is visible. The caller keeps it visible for a
     * selected endpoint, and also while a hovered endpoint is being read, so
     * the pointer can move from the disc onto the count and open the claims.
     */
    interactive?: boolean;
    /** The station the claims it stands in for will use. */
    placement?: number;
    offsetX?: number;
    offsetY?: number;
  },
) {
  return {
    id,
    type: WORLD_FILAMENT_EDGE,
    source,
    target,
    style: {
      // No filament of its own: the group's carrier already drew the one line
      // these claims share, and a second stroke would invent a second link.
      stroke: paint.ink,
      lineWidth: 0,
      opacity: 1,
      strokeOpacity: 0,
      increasedLineWidthForHitTesting: 0,
      pointerEvents: "none" as const,
      // An invisible label never intercepts the pointer, whatever the caller
      // asked for: a hit region with nothing drawn in it is a claim that
      // something is there.
      labelPointerEvents:
        options.interactive && options.shown ? ("auto" as const) : ("none" as const),
      // G6 renders the label background as a child shape. Give that shape the
      // same hit-test policy so the visible count can open its bundle.
      labelBackgroundPointerEvents:
        options.interactive && options.shown ? ("auto" as const) : ("none" as const),
      labelText: options.label,
      labelFontFamily: FONT_SANS_FAMILY,
      labelFontSize: p.chipLabelSize,
      labelFontWeight: p.chipLabelWeight,
      labelFill: paint.ink,
      labelCursor: options.interactive ? ("pointer" as const) : undefined,
      labelOffsetX: options.offsetX ?? 0,
      labelOffsetY: options.offsetY ?? p.chipLabelNudge,
      labelOpacity: options.shown ? 1 : 0,
      labelBackground: true,
      labelBackgroundOpacity: options.shown ? 1 : 0,
      labelBackgroundFill: paint.chip,
      labelBackgroundLineWidth: 0,
      labelBackgroundRadius: 0,
      labelBackgroundWidth: chipWidth(options.label, p),
      labelBackgroundHeight: p.chipHeight,
      labelPadding: [p.chipPaddingY, p.chipPaddingX] as [number, number],
      labelAutoRotate: false,
      labelPlacement: options.placement ?? 0.5,
    },
  };
}
