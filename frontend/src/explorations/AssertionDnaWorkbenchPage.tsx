/**
 * Assertion DNA — authoring the second mark.
 *
 * The map has one mark today: a disc, which is a referent. World IR needs a
 * second, because a named n-ary relation tuple is not a thing the world can
 * name — it is a claim *about* things it can name — and drawing it as another
 * disc would make `acceptable_replacement(X110, X160, outdoor_enclosure)` read
 * as a fourth part.
 *
 * The second mark is the chip: the relation label that already appears on a lit
 * filament, standing on its own. This board exists to decide its geometry
 * before any product surface draws one, in the same place and for the same
 * reason the Graph DNA workbench decides the disc's — a look authored on the
 * page that ships is a look that drifts the first time a second surface copies
 * it. Everything here reads `GRAPH_DNA_CHIP`, and the panel prints back a block
 * to paste into it.
 *
 * Six specimens, because six things have to be true at once:
 *
 *   1-2  a collapsed binary chip is *the edge label*, not a lookalike
 *   3    a shelf cannot live on an edge label, so DERIVED promotes the plate
 *   4    three roles, none of them discarded, none of them a direction
 *   5    the shape of an assertion with nothing in it — unresolved, not false
 *   6    a stale relation is the provisional palette, not a badge
 */

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type CSSProperties,
} from "react";
import { Graph, type GraphData } from "@antv/g6";
import {
  chromeCssVariables,
  GRAPH_DNA_CHIP,
  GRAPH_DNA_CHROME,
  GRAPH_DNA_GEOMETRY,
  GRAPH_DNA_PROVISIONAL_THEME,
  GRAPH_DNA_THEME,
  radixValue,
  type GraphDnaTheme,
  type ThemeMode,
} from "../styles/graphDna";
import { FONT_SANS_FAMILY } from "../styles/typography";
import "./AssertionDnaWorkbenchPage.css";

const STORAGE_KEY = "graphauthor.assertionDna";

type ChipParams = typeof GRAPH_DNA_CHIP & {
  /** Read from `GRAPH_DNA_GEOMETRY`; adjustable here because the chip is only
   *  ever judged against the disc it sits next to. */
  discDiameter: number;
  edgeWidth: number;
  edgeOpacity: number;
  dottedGap: number;
  /**
   * Whether a mechanical chip carries its own outline.
   *
   * On a filament the chip needs none — the line it interrupts is what holds
   * it. Detached on the field it may need one, or it floats. This is the
   * question the board is here to answer, so it is a knob rather than a value.
   */
  mechanicalOutline: boolean;
};

const DEFAULTS: ChipParams = {
  ...GRAPH_DNA_CHIP,
  discDiameter: GRAPH_DNA_GEOMETRY.nodeDiameter,
  edgeWidth: GRAPH_DNA_GEOMETRY.edgeWidth,
  edgeOpacity: GRAPH_DNA_GEOMETRY.edgeOpacity,
  dottedGap: GRAPH_DNA_GEOMETRY.dottedGap,
  mechanicalOutline: false,
};

function readParams(): ChipParams {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULTS;
    return { ...DEFAULTS, ...(JSON.parse(raw) as Partial<ChipParams>) };
  } catch {
    return DEFAULTS;
  }
}

function writeParams(params: ChipParams) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(params));
  } catch {
    /* a lab that cannot persist is still a lab */
  }
}

/** The DNA palette, resolved to paint. */
type Paint = {
  canvas: string;
  ink: string;
  field: string;
  chip: string;
  muted: string;
};

function paintOf(theme: GraphDnaTheme): Paint {
  return {
    canvas: radixValue(theme.canvas),
    ink: radixValue(theme.node),
    field: radixValue(theme.nodeLabel),
    chip: radixValue(theme.chip),
    muted: radixValue(theme.lensLabel),
  };
}

/**
 * Chip width comes from the word in it.
 *
 * Measured rather than estimated: relation names in this world run from
 * `used_in` to `acceptable_replacement`, and a fixed plate wide enough for the
 * second is a lie about the first.
 */
let measurer: CanvasRenderingContext2D | null = null;
function metricsOf(text: string, size: number, weight: number): TextMetrics | null {
  if (!measurer) {
    measurer = document.createElement("canvas").getContext("2d");
  }
  if (!measurer) return null;
  // The weight has to be the one that will be drawn. Measuring at 600 and
  // painting at 400 gives every plate a few pixels of padding it did not ask
  // for, on one side, which reads as a centring bug rather than as a width.
  measurer.font = `${weight} ${size}px ${FONT_SANS_FAMILY}`;
  return measurer.measureText(text);
}

function textWidth(text: string, size: number, weight: number): number {
  return metricsOf(text, size, weight)?.width ?? text.length * size * 0.6;
}

/**
 * How far the word's ink sits off the anchor G6 centres it on.
 *
 * G6 draws a centred label on the font's baseline box, which is not where the
 * word looks like it is. `acceptable_replacement` has an underscore below the
 * baseline and no descender-free cap line above it, so the box's middle sits
 * above the ink's middle and the name rides high in a 10px plate — most
 * visibly at small sizes, which is exactly the size this chip is.
 *
 * Correcting from the glyphs themselves rather than from a hand-tuned constant:
 * `actualBoundingBox*` is the real inked extent of *this* string in *this*
 * face, so a relation name with no descender and one with an underscore each
 * come out centred, and neither needs its own magic number.
 */
function opticalNudge(text: string, size: number, weight: number): number {
  const m = metricsOf(text, size, weight);
  if (!m) return 0;
  const ascent = m.actualBoundingBoxAscent;
  const descent = m.actualBoundingBoxDescent;
  if (!Number.isFinite(ascent) || !Number.isFinite(descent)) return 0;
  return (ascent - descent) / 2;
}

function chipWidth(text: string, p: ChipParams): number {
  return Math.round(
    textWidth(text, p.chipLabelSize, p.chipLabelWeight) + p.chipPaddingX * 2,
  );
}

/**
 * The weight the product canvas actually draws node labels at.
 *
 * Not 600. `ProductGraphCanvas` ships `labelFontWeight ?? 400`, and Jost at 400
 * is already the sharp geometric face the map is built on — the board opened
 * one step heavy on every label and read as a different product.
 */
const DISC_LABEL_WEIGHT = 400;

type ChipKind = "mechanical" | "semantic" | "unresolved";

function discNode(id: string, x: number, y: number, label: string, paint: Paint, p: ChipParams) {
  return {
    id,
    type: "circle",
    style: {
      x,
      y,
      size: p.discDiameter,
      fill: paint.ink,
      stroke: paint.ink,
      lineWidth: GRAPH_DNA_GEOMETRY.nodeLine,
      labelText: label,
      labelPlacement: "center" as const,
      labelFill: paint.field,
      labelFontFamily: FONT_SANS_FAMILY,
      labelFontSize: GRAPH_DNA_GEOMETRY.labelSize,
      labelFontWeight: DISC_LABEL_WEIGHT,
      labelLineHeight: GRAPH_DNA_GEOMETRY.labelSize * GRAPH_DNA_GEOMETRY.labelLineHeight,
      labelOffsetY: GRAPH_DNA_GEOMETRY.labelBaselineNudge,
      labelWordWrap: true,
      labelMaxWidth: p.discDiameter * (GRAPH_DNA_GEOMETRY.labelMaxWidth / 100),
      labelMaxLines: GRAPH_DNA_GEOMETRY.labelMaxLines,
      labelTextOverflow: "ellipsis" as const,
    },
  };
}

/** The plate. One tuple of one relation, standing on the field. */
function chipNode(
  id: string,
  x: number,
  y: number,
  text: string,
  kind: ChipKind,
  paint: Paint,
  p: ChipParams,
) {
  const filled = kind === "semantic";
  const outlined = kind === "unresolved" || (kind === "mechanical" && p.mechanicalOutline);
  return {
    id,
    type: "rect",
    style: {
      x,
      y,
      size: [chipWidth(text, p), p.chipHeight] as [number, number],
      radius: p.chipRadius,
      // A knockout, not a card: the plate is the field exactly, so filaments
      // running under it stop being read rather than being covered by a
      // second colour.
      fill: filled ? paint.ink : paint.chip,
      fillOpacity: kind === "unresolved" ? 0 : 1,
      stroke: paint.ink,
      lineWidth: outlined ? p.chipLine : 0,
      lineDash: kind === "unresolved" ? ([0, p.dottedGap] as [number, number]) : undefined,
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
 * The shelf under a derived chip.
 *
 * A separate element rather than part of the plate, because the plate is a
 * `rect` and a second rule is a second shape. In the product this becomes one
 * custom node so the two can never be placed apart; here they are two so the
 * gap between them is a knob.
 */
function shelfNode(id: string, x: number, y: number, text: string, paint: Paint, p: ChipParams) {
  // From the word, not from the plate: a shelf the width of the box reads as a
  // second edge of the box. The width of the name plus a little air reads as
  // the name resting on something.
  const width =
    textWidth(text, p.chipLabelSize, p.chipLabelWeight) + p.shelfOverhang * 2;
  return {
    id,
    type: "rect",
    style: {
      x,
      y: y + p.chipHeight / 2 + p.shelfGap,
      size: [Math.max(4, Math.round(width)), p.shelfLine] as [number, number],
      radius: 0,
      fill: paint.ink,
      lineWidth: 0,
      labelText: "",
    },
  };
}

type SpokeOptions = {
  role?: string;
  dotted?: boolean;
  showRole: boolean;
};

/** A referent filling a role in an assertion. */
function spokeEdge(
  id: string,
  source: string,
  target: string,
  paint: Paint,
  p: ChipParams,
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
function filamentEdge(
  id: string,
  source: string,
  target: string,
  paint: Paint,
  p: ChipParams,
  options: { label?: string; named: boolean; semantic?: boolean },
) {
  const named = options.named && Boolean(options.label);
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
      // The plate on a filament is the same plate, so it is centred the same
      // way. Letting the edge label fall back to G6's own placement is how the
      // collapsed and detached forms stop being one object.
      labelOffsetY:
        opticalNudge(options.label ?? "", p.chipLabelSize, p.chipLabelWeight) +
        p.chipLabelNudge,
      labelFill: options.semantic ? paint.field : paint.ink,
      // See `spokeEdge`: the plate and the word on it are their own strength.
      // A semantic chip inheriting a 0.5 filament came out as grey-on-grey and
      // stopped being the same object as the plate an n-ary tuple stands on,
      // which is the whole claim this board is here to make.
      labelOpacity: 1,
      labelBackground: named,
      labelBackgroundOpacity: 1,
      labelBackgroundFill: options.semantic ? paint.ink : paint.chip,
      labelBackgroundLineWidth: 0,
      labelBackgroundRadius: p.chipRadius,
      labelPadding: [p.chipPaddingY, p.chipPaddingX] as [number, number],
      labelAutoRotate: false,
      labelPlacement: 0.5,
    },
  };
}

type Specimen = {
  id: string;
  title: string;
  note: string;
  provisional?: boolean;
  build: (paint: Paint, p: ChipParams, focused: boolean) => GraphData;
};

const BINARY_LEFT = { x: 90, y: 110 };
const BINARY_RIGHT = { x: 400, y: 110 };
const TERNARY_CHIP = { x: 245, y: 46 };
const TERNARY_ROLES = [
  { x: 70, y: 175 },
  { x: 245, y: 190 },
  { x: 420, y: 175 },
];

const SPECIMENS: Specimen[] = [
  {
    id: "binary-mechanical",
    title: "Binary · mechanical",
    note:
      "The chip is the edge label. Nothing is added to draw an assertion that " +
      "happens to have two roles — it is named on focus and quiet at rest.",
    build: (paint, p, focused) => ({
      nodes: [
        discNode("listing", BINARY_LEFT.x, BINARY_LEFT.y, "ABC-829", paint, p),
        discNode("part", BINARY_RIGHT.x, BINARY_RIGHT.y, "X160", paint, p),
      ],
      edges: [
        filamentEdge("e", "listing", "part", paint, p, {
          label: "listing_of",
          named: focused || p.namedAtRest,
        }),
      ],
    }),
  },
  {
    id: "binary-semantic",
    title: "Binary · semantic",
    note:
      "Same plate, filled with ink. Weight comes from fill, and an authored " +
      "assertion is the one that cost something to make.",
    build: (paint, p, focused) => ({
      nodes: [
        discNode("new", BINARY_LEFT.x, BINARY_LEFT.y, "X110", paint, p),
        discNode("old", BINARY_RIGHT.x, BINARY_RIGHT.y, "X160", paint, p),
      ],
      edges: [
        filamentEdge("e", "new", "old", paint, p, {
          label: "acceptable_replacement",
          named: focused || p.namedAtRest,
          semantic: true,
        }),
      ],
    }),
  },
  {
    id: "binary-derived",
    title: "Binary · derived",
    note:
      "A shelf cannot sit under an edge label, so a derived binary promotes " +
      "its chip to a plate on the line. The shelf is what you pull to open " +
      "the inputs it rests on.",
    build: (paint, p) => {
      const mid = {
        x: (BINARY_LEFT.x + BINARY_RIGHT.x) / 2,
        y: (BINARY_LEFT.y + BINARY_RIGHT.y) / 2,
      };
      return {
        nodes: [
          discNode("part", BINARY_LEFT.x, BINARY_LEFT.y, "R200", paint, p),
          discNode("bom", BINARY_RIGHT.x, BINARY_RIGHT.y, "BOM-A", paint, p),
          chipNode("chip", mid.x, mid.y, "eligible_part", "mechanical", paint, p),
          shelfNode("shelf", mid.x, mid.y, "eligible_part", paint, p),
        ],
        edges: [
          filamentEdge("l", "part", "chip", paint, p, { named: false }),
          filamentEdge("r", "chip", "bom", paint, p, { named: false }),
        ],
      };
    },
  },
  {
    id: "ternary-semantic",
    title: "Ternary · semantic",
    note:
      "Three roles, none discarded. No arrowheads: role identity replaces " +
      "direction, and a spoke cannot be 'forward' when there are three of them.",
    build: (paint, p, focused) => ({
      nodes: [
        chipNode(
          "chip",
          TERNARY_CHIP.x,
          TERNARY_CHIP.y,
          "acceptable_replacement",
          "semantic",
          paint,
          p,
        ),
        discNode("new", TERNARY_ROLES[0].x, TERNARY_ROLES[0].y, "X110", paint, p),
        discNode("old", TERNARY_ROLES[1].x, TERNARY_ROLES[1].y, "X160", paint, p),
        discNode("ctx", TERNARY_ROLES[2].x, TERNARY_ROLES[2].y, "outdoor enclosure", paint, p),
      ],
      edges: [
        spokeEdge("s1", "new", "chip", paint, p, { role: "new_part", showRole: focused }),
        spokeEdge("s2", "old", "chip", paint, p, { role: "old_part", showRole: focused }),
        spokeEdge("s3", "ctx", "chip", paint, p, { role: "context", showRole: focused }),
      ],
    }),
  },
  {
    id: "ternary-unresolved",
    title: "Ternary · unresolved",
    note:
      "The outline of an assertion with nothing in it. The world was asked " +
      "this and has not answered — which is not the same as answering no.",
    build: (paint, p, focused) => ({
      nodes: [
        chipNode(
          "chip",
          TERNARY_CHIP.x,
          TERNARY_CHIP.y,
          "acceptable_replacement",
          "unresolved",
          paint,
          p,
        ),
        discNode("new", TERNARY_ROLES[0].x, TERNARY_ROLES[0].y, "X110", paint, p),
        discNode("old", TERNARY_ROLES[1].x, TERNARY_ROLES[1].y, "X160", paint, p),
        discNode("ctx", TERNARY_ROLES[2].x, TERNARY_ROLES[2].y, "indoor panel", paint, p),
      ],
      edges: [
        spokeEdge("s1", "new", "chip", paint, p, {
          role: "new_part",
          dotted: true,
          showRole: focused,
        }),
        spokeEdge("s2", "old", "chip", paint, p, {
          role: "old_part",
          dotted: true,
          showRole: focused,
        }),
        spokeEdge("s3", "ctx", "chip", paint, p, {
          role: "context",
          dotted: true,
          showRole: focused,
        }),
      ],
    }),
  },
  {
    id: "ternary-stale",
    title: "Ternary · stale relation",
    note:
      "The same assertion in the provisional palette. Staleness is a property " +
      "of a whole relation in the store, so it dims a family rather than " +
      "badging one tuple.",
    provisional: true,
    build: (paint, p, focused) => ({
      nodes: [
        chipNode(
          "chip",
          TERNARY_CHIP.x,
          TERNARY_CHIP.y,
          "acceptable_replacement",
          "semantic",
          paint,
          p,
        ),
        discNode("new", TERNARY_ROLES[0].x, TERNARY_ROLES[0].y, "R210", paint, p),
        discNode("old", TERNARY_ROLES[1].x, TERNARY_ROLES[1].y, "R200", paint, p),
        discNode("ctx", TERNARY_ROLES[2].x, TERNARY_ROLES[2].y, "high vibration", paint, p),
      ],
      edges: [
        spokeEdge("s1", "new", "chip", paint, p, { role: "new_part", showRole: focused }),
        spokeEdge("s2", "old", "chip", paint, p, { role: "old_part", showRole: focused }),
        spokeEdge("s3", "ctx", "chip", paint, p, { role: "context", showRole: focused }),
      ],
    }),
  },
];

function SpecimenCard({
  specimen,
  params,
  mode,
  focused,
}: {
  specimen: Specimen;
  params: ChipParams;
  mode: ThemeMode;
  focused: boolean;
}) {
  const hostRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<Graph | null>(null);

  const theme = specimen.provisional
    ? GRAPH_DNA_PROVISIONAL_THEME[mode]
    : GRAPH_DNA_THEME[mode];
  const paint = useMemo(() => paintOf(theme), [theme]);
  const data = useMemo(
    () => specimen.build(paint, params, focused),
    [specimen, paint, params, focused],
  );

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    const graph = new Graph({
      container: host,
      data,
      animation: false,
      autoFit: { type: "view", options: { direction: "both" } },
      padding: 16,
      behaviors: [],
      background: paint.canvas,
    });
    graphRef.current = graph;
    void graph.render();
    return () => {
      graphRef.current = null;
      graph.destroy();
    };
    // Rebuilt whole rather than patched: a specimen board is six elements, and
    // a `setData` path that silently keeps a stale style is the one bug this
    // page cannot afford — it would be indistinguishable from a design result.
  }, [data, paint.canvas]);

  return (
    <figure className="assertion-dna__card">
      <div
        className="assertion-dna__stage"
        ref={hostRef}
        style={{ background: paint.canvas }}
      />
      <figcaption>
        <b>{specimen.title}</b>
        <span>{specimen.note}</span>
      </figcaption>
    </figure>
  );
}

type NumberKnob = {
  key: keyof ChipParams;
  label: string;
  min: number;
  max: number;
  step: number;
};

const KNOBS: { group: string; knobs: NumberKnob[] }[] = [
  {
    group: "Plate",
    knobs: [
      { key: "chipHeight", label: "height", min: 10, max: 32, step: 1 },
      { key: "chipPaddingX", label: "padding x", min: 0, max: 16, step: 0.5 },
      { key: "chipPaddingY", label: "padding y", min: 0, max: 10, step: 0.5 },
      { key: "chipRadius", label: "radius", min: 0, max: 12, step: 0.5 },
      { key: "chipLabelSize", label: "label", min: 6, max: 16, step: 0.5 },
      { key: "chipLabelWeight", label: "weight", min: 200, max: 600, step: 100 },
      { key: "chipLine", label: "outline", min: 0, max: 3, step: 0.25 },
      { key: "chipLabelNudge", label: "nudge", min: -3, max: 3, step: 0.25 },
    ],
  },
  {
    group: "Shelf",
    knobs: [
      { key: "shelfGap", label: "gap", min: 0, max: 12, step: 0.5 },
      { key: "shelfLine", label: "weight", min: 0.25, max: 4, step: 0.25 },
      { key: "shelfOverhang", label: "overhang", min: 0, max: 12, step: 0.5 },
    ],
  },
  {
    group: "Role spoke",
    knobs: [
      { key: "roleSpokeWidth", label: "width", min: 0.25, max: 3, step: 0.25 },
      { key: "roleSpokeOpacity", label: "opacity", min: 0.05, max: 1, step: 0.05 },
      { key: "roleLabelSize", label: "role label", min: 5, max: 14, step: 0.5 },
      { key: "roleLabelWeight", label: "role weight", min: 200, max: 600, step: 100 },
      { key: "roleLabelAt", label: "role at", min: 0.15, max: 0.85, step: 0.05 },
    ],
  },
  {
    group: "Field",
    knobs: [
      { key: "discDiameter", label: "disc", min: 40, max: 140, step: 2 },
      { key: "edgeWidth", label: "filament", min: 0.25, max: 3, step: 0.25 },
      { key: "edgeOpacity", label: "filament opacity", min: 0.05, max: 1, step: 0.05 },
      { key: "dottedGap", label: "dotted gap", min: 2, max: 14, step: 0.5 },
    ],
  },
];

export function AssertionDnaWorkbenchPage() {
  const [params, setParams] = useState<ChipParams>(readParams);
  const [mode, setMode] = useState<ThemeMode>("light");
  const [focused, setFocused] = useState(false);

  useEffect(() => writeParams(params), [params]);

  const set = useCallback(<K extends keyof ChipParams>(key: K, value: ChipParams[K]) => {
    setParams((prev) => ({ ...prev, [key]: value }));
  }, []);

  const chrome = mode === "light" ? GRAPH_DNA_CHROME.light : GRAPH_DNA_CHROME.dark;
  const style = chromeCssVariables(chrome) as CSSProperties;

  const dnaBlock = useMemo(() => {
    const keys = Object.keys(GRAPH_DNA_CHIP) as (keyof typeof GRAPH_DNA_CHIP)[];
    const body = keys
      .map((key) => `  ${key}: ${JSON.stringify(params[key])},`)
      .join("\n");
    return `export const GRAPH_DNA_CHIP = {\n${body}\n};`;
  }, [params]);

  return (
    <main className="assertion-dna" style={style} data-mode={mode}>
      <header className="assertion-dna__header">
        <p>Workshop</p>
        <h1>Assertion DNA</h1>
        <span>
          The second mark. A disc is a referent; a chip is one tuple of one named
          relation. Authored here, read from <code>GRAPH_DNA_CHIP</code>.
        </span>
      </header>

      <div className="assertion-dna__body">
        <section className="assertion-dna__board">
          {SPECIMENS.map((specimen) => (
            <SpecimenCard
              key={specimen.id}
              specimen={specimen}
              params={params}
              mode={mode}
              focused={focused}
            />
          ))}
        </section>

        <aside className="assertion-dna__panel">
          <div className="assertion-dna__states">
            <button
              type="button"
              data-active={!focused}
              onClick={() => setFocused(false)}
            >
              At rest
            </button>
            <button
              type="button"
              data-active={focused}
              onClick={() => setFocused(true)}
            >
              Focused
            </button>
            <button
              type="button"
              data-active={mode === "dark"}
              onClick={() => setMode(mode === "dark" ? "light" : "dark")}
            >
              {mode === "dark" ? "Dark" : "Light"}
            </button>
          </div>

          <label className="assertion-dna__toggle">
            <input
              type="checkbox"
              checked={params.namedAtRest}
              onChange={(event) => set("namedAtRest", event.target.checked)}
            />
            <span>
              named at rest
              <em>schema zoom names every chip; referent zoom stays quiet</em>
            </span>
          </label>

          <label className="assertion-dna__toggle">
            <input
              type="checkbox"
              checked={params.mechanicalOutline}
              onChange={(event) => set("mechanicalOutline", event.target.checked)}
            />
            <span>
              mechanical outline
              <em>a detached knockout may need an edge to sit on the field</em>
            </span>
          </label>

          {KNOBS.map((group) => (
            <fieldset key={group.group}>
              <legend>{group.group}</legend>
              {group.knobs.map((knob) => (
                <label key={String(knob.key)} className="assertion-dna__knob">
                  <span>{knob.label}</span>
                  <input
                    type="range"
                    min={knob.min}
                    max={knob.max}
                    step={knob.step}
                    value={Number(params[knob.key])}
                    onChange={(event) =>
                      set(knob.key, Number(event.target.value) as ChipParams[typeof knob.key])
                    }
                  />
                  <b>{Number(params[knob.key])}</b>
                </label>
              ))}
            </fieldset>
          ))}

          <button
            type="button"
            className="assertion-dna__reset"
            onClick={() => setParams(DEFAULTS)}
          >
            Reset to DNA
          </button>

          <pre className="assertion-dna__block">{dnaBlock}</pre>
        </aside>
      </div>
    </main>
  );
}
