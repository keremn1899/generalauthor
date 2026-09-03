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

/**
 * How far the word's ink sits off the anchor a centred label is drawn on.
 *
 * A label is placed on the font's baseline box, which is not where the word
 * looks like it is: `acceptable_replacement` has an underscore below the
 * baseline, so the box's middle sits above the ink's middle and the name rides
 * high in a 10px plate — most visibly at small sizes, which is the size this
 * chip is. Corrected from the glyphs themselves rather than a hand-tuned
 * constant, so a name with a descender and one without both come out centred.
 */
export function opticalNudge(text: string, size: number, weight: number): number {
  const m = metricsOf(text, size, weight);
  if (!m) return 0;
  const ascent = m.actualBoundingBoxAscent;
  const descent = m.actualBoundingBoxDescent;
  if (!Number.isFinite(ascent) || !Number.isFinite(descent)) return 0;
  return (ascent - descent) / 2;
}

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
      opacity: 1,
      fill: paint.ink,
      stroke: paint.ink,
      lineWidth: GRAPH_DNA_GEOMETRY.nodeLine,
      labelText: label,
      labelPlacement: "center" as const,
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
      fillOpacity: kind === "unresolved" ? 0 : 1,
      stroke: paint.ink,
      lineWidth: outlined ? p.chipLine : 0,
      lineDash:
        kind === "unresolved" ? ([0, p.dottedGap] as [number, number]) : undefined,
      lineCap: "round" as const,
      labelText: text,
      labelPlacement: "center" as const,
      labelFill: filled ? paint.field : paint.ink,
      labelFontFamily: FONT_SANS_FAMILY,
      labelFontSize: p.chipLabelSize,
      labelFontWeight: p.chipLabelWeight,
      labelOffsetY:
        opticalNudge(text, p.chipLabelSize, p.chipLabelWeight) + p.chipLabelNudge,
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
    },
  };
}

export type SpokeOptions = {
  role?: string;
  dotted?: boolean;
  showRole: boolean;
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
    source,
    target,
    style: {
      stroke: paint.ink,
      lineWidth: p.roleSpokeWidth,
      // A named bond is a lit bond. G6 applies the element's opacity to the
      // label group as well, so a chip on a 0.5 filament comes out grey on
      // grey — and the fix is not to fight the inheritance but to accept what
      // it is telling us: you are looking at this spoke, so it should be at
      // full strength while you are.
      opacity: options.showRole ? 1 : p.roleSpokeOpacity,
      lineCap: "round" as const,
      lineDash: options.dotted ? ([0, p.dottedGap] as [number, number]) : undefined,
      labelText: options.showRole ? (options.role ?? "") : "",
      labelFontFamily: FONT_SANS_FAMILY,
      labelFontSize: p.roleLabelSize,
      labelFontWeight: p.roleLabelWeight,
      labelFill: paint.ink,
      // Stated, not inherited. A label left to take the edge's opacity is a
      // name drawn at the strength of the line under it, which is backwards:
      // the filament is quiet so the name can be read over it.
      labelOpacity: 1,
      labelBackground: true,
      labelBackgroundOpacity: 1,
      labelBackgroundFill: paint.chip,
      labelBackgroundLineWidth: 0,
      labelBackgroundRadius: p.chipRadius,
      labelPadding: [p.chipPaddingY, p.chipPaddingX] as [number, number],
      labelAutoRotate: false,
      labelPlacement: p.roleLabelAt,
    },
  };
}

/** A plain filament, with or without its name showing. */
export function filamentEdge(
  id: string,
  source: string,
  target: string,
  paint: Paint,
  p: MarkParams,
  options: { label?: string; named: boolean; kind?: ChipKind },
) {
  const named = options.named && Boolean(options.label);
  // A bond's plate is the same plate, so it fills on the same rule. What it
  // cannot carry is furniture: a label background has no side to hang a shelf
  // or a crown from, so a derived or adjudicated binary is drawn detached —
  // see `schemaGraph`, which takes exactly that exception.
  const filled = isAuthored(options.kind);
  return {
    id,
    source,
    target,
    style: {
      stroke: paint.ink,
      lineWidth: p.edgeWidth,
      // See `spokeEdge`: naming a bond lights it.
      opacity: named ? 1 : p.edgeOpacity,
      lineCap: "round" as const,
      labelText: named ? options.label : "",
      labelFontFamily: FONT_SANS_FAMILY,
      labelFontSize: p.chipLabelSize,
      labelFontWeight: p.chipLabelWeight,
      labelFill: filled ? paint.field : paint.ink,
      // The plate on a filament is the same plate, so it is centred the same
      // way. Letting the edge label fall back to the renderer's own placement
      // is how the collapsed and detached forms stop being one object.
      labelOffsetY:
        opticalNudge(options.label ?? "", p.chipLabelSize, p.chipLabelWeight) +
        p.chipLabelNudge,
      labelOpacity: 1,
      labelBackground: named,
      labelBackgroundOpacity: 1,
      labelBackgroundFill: filled ? paint.ink : paint.chip,
      labelBackgroundLineWidth: 0,
      labelBackgroundRadius: p.chipRadius,
      labelPadding: [p.chipPaddingY, p.chipPaddingX] as [number, number],
      labelAutoRotate: false,
      labelPlacement: 0.5,
    },
  };
}
