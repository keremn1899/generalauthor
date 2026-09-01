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
  GRAPH_DNA_PROVISIONAL_THEME,
  GRAPH_DNA_THEME,
  type ThemeMode,
} from "../styles/graphDna";
// The marks themselves live beside the surface that ships them. This page
// authors their parameters; it does not own how they are drawn, or the board
// and the product would be two drawings that only look alike.
import {
  chipNode,
  discNode,
  filamentEdge,
  MARK_DEFAULTS,
  paintOf,
  shelfNode,
  spokeEdge,
  type MarkParams,
  type Paint,
} from "../world/marks";
import "./AssertionDnaWorkbenchPage.css";

const STORAGE_KEY = "graphauthor.assertionDna";

type ChipParams = MarkParams;

const DEFAULTS: ChipParams = MARK_DEFAULTS;

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
