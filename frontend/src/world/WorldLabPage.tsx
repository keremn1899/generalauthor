/**
 * World Design & Motion Lab — interactive design surface and motion inspector.
 *
 * Provides a dedicated space to:
 * 1. Test and director-control every transition (panel sliding, canvas emit/absorb,
 *    ant ring arrival/departure, camera pans, vocabulary focus, speed scaling).
 * 2. Inspect and design every individual component from the main page in isolation
 *    (marks, marching ants, overlay panels, tables, reader cards, instrument band).
 * 3. Inspect and compare the Motion DNA curves (emit, absorb, settle, flow, hold).
 */

import { useCallback, useMemo, useState } from "react";
import { type ThemeMode } from "../styles/graphDna";
import { scaleMotionPlans, type MotionIntent } from "../styles/motion";
import {
  DEFAULT_LIGHT_FIELD,
  luminance,
  type LightField,
} from "../styles/light";
import { worldCameraInsets, worldShellStyle } from "./worldChrome";
import {
  MARK_DEFAULTS,
  type MarkParams,
} from "./marks";
import { SHOW_DEFAULT, type ShowState } from "./show";
import { ShowBand } from "./ShowBand";
import {
  emptySet,
  fieldSize,
  place,
  dropMark,
  type WorkingSet,
} from "./workingSet";
import {
  ANT_DEFAULTS,
  WorldCanvas,
  type CanvasSelection,
} from "./WorldCanvas";
import { SchemaCanvas } from "./SchemaCanvas";
import { Spine } from "../construction/Spine";
import { Docket } from "../construction/Docket";
import { LabTransitions } from "./LabTransitions";
import { OverlayPanel } from "../product/OverlayPanel";
import { chromeClass } from "../product/overlayChrome";
import { WorldTable } from "./WorldTable";
import { FrontierTable } from "./FrontierTable";
import { RelationTable } from "./RelationTable";
import { DerivationView } from "./DerivationView";
import { type TableChrome } from "./tableChrome";
import {
  Find,
  AssertionPanel,
  DemandPanel,
  ReferentPanel,
} from "./WorldPage";
import {
  createMockWorkingSet,
  createSpecimenSet,
  MOCK_ASSERTION_DERIVED,
  MOCK_ASSERTION_MECHANICAL,
  MOCK_DEMAND,
  MOCK_DIRECTORY,
  MOCK_DOCKET,
  MOCK_OBLIGATION,
  MOCK_PASSES,
  MOCK_OVERVIEW,
  MOCK_REFERENT,
  MOCK_RELATIONS,
} from "./mockWorldData";
import type { CameraInsets } from "./canvasFocus";
import type { WorldRole, WorldTuple } from "../api/world";
import "./WorldLabPage.css";
import "../construction/ConstructionPage.css";
import "./WorldPage.css";
import "../product/ProductShell.css";
import "../product/NodeFinder.css";
import "../product/NodeReaderPanel.css";
import "../product/GraphWorkspace.css";
import "../product/OverlayPanel.css";
import "../product/overlayChrome.css";

/**
 * Every layer on. The product hides `mechanical` by default — the spec's
 * useful default, and the right one for a field someone is reading — but a
 * gallery of origins that is missing one is not a gallery of origins.
 */
const SPECIMEN_SHOW: ShowState = {
  semantic: true,
  adjudicated: true,
  derived: true,
  mechanical: true,
  unresolved: true,
};

/** The specimen field has no docks over it, so it frames on the plain pad. */
const SPECIMEN_INSETS: CameraInsets = {
  left: 48,
  right: 48,
  top: 48,
  bottom: 48,
};

export type LabTab = "sandbox" | "components" | "motion";
export type ComponentSection =
  | "marks"
  | "ants"
  | "panels"
  | "tables"
  | "reader"
  | "instrument"
  | "construction"
  | "transitions";

const SPEED_OPTIONS = [1, 0.5, 0.25, 0.1] as const;

export function WorldLabPage() {
  const [labTab, setLabTab] = useState<LabTab>("sandbox");
  const [componentSection, setComponentSection] =
    useState<ComponentSection>("marks");
  const [mode, setMode] = useState<ThemeMode>("light");
  const [speedFactor, setSpeedFactor] = useState<number>(1);

  /**
   * The product's spine, slowed for inspection — not a second spine.
   *
   * `scaleMotionPlans` lives in the kernel because the numbers it scales are
   * the kernel's. Restating 280/190/320/1000/90 here would mean this surface
   * could show timings the product does not have, which is the one thing a
   * design surface must never do.
   */
  const motionPlans = useMemo(
    () => scaleMotionPlans(speedFactor),
    [speedFactor],
  );

  // Shared state for the full composite Sandbox
  const [set, setSet] = useState<WorkingSet>(createMockWorkingSet);
  const [selection, setSelection] = useState<CanvasSelection>({
    kind: "assertion",
    id: "assertion:temp_c300_bom_d",
  });
  const [hovered, setHovered] = useState<string | null>(null);
  const [hoveredRelation, setHoveredRelation] = useState<string | null>(null);
  const [focusedRelation, setFocusedRelation] = useState<string | null>(null);
  const [vocabularyFocus, setVocabularyFocus] = useState(false);
  const [namedAtRest, setNamedAtRest] = useState(false);
  const [show, setShow] = useState<ShowState>(SHOW_DEFAULT);
  const [tablesOpen, setTablesOpen] = useState(true);
  const [tablesWidth, setTablesWidth] = useState(360);
  const [readerOpen, setReaderOpen] = useState(true);
  const [readerWidth, setReaderWidth] = useState(320);
  const [activeTable, setActiveTable] = useState<"world" | "frontier" | "relation">("world");
  const [tableRelation, setTableRelation] = useState<string>("temperature_compatible");
  const [focus, setFocus] = useState<{ id: string; token: number } | null>(null);
  const [demoTableKind, setDemoTableKind] = useState<"world" | "frontier" | "relation" | "derivation">("world");
  const [demoPass, setDemoPass] = useState<string | null>(null);
  const [demoObligation, setDemoObligation] = useState<string | null>("ob:supply_c303");

  // Mark tuner parameters in Components studio
  const [markKnobs, setMarkKnobs] = useState<MarkParams>({
    ...MARK_DEFAULTS,
  });

  // Ant tuner parameters in Components studio. Seeded from the DNA rather
  // than from remembered numbers, so the studio opens on what ships.
  const [antClearance, setAntClearance] = useState(ANT_DEFAULTS.clearance);
  const [antDotGap, setAntDotGap] = useState(ANT_DEFAULTS.dotGap);
  const [antLineWidth, setAntLineWidth] = useState(ANT_DEFAULTS.lineWidth);
  const [antSpeed, setAntSpeed] = useState(ANT_DEFAULTS.speed);
  const [antAnimated, setAntAnimated] = useState(ANT_DEFAULTS.animated);
  const antTuning = useMemo(
    () => ({
      clearance: antClearance,
      dotGap: antDotGap,
      lineWidth: antLineWidth,
      speed: antSpeed,
      animated: antAnimated,
    }),
    [antAnimated, antClearance, antDotGap, antLineWidth, antSpeed],
  );

  /**
   * The light field. Two numbers: how far light reaches through the graph,
   * and how much of the world stays readable where it does not.
   */
  const [lightField, setLightField] = useState<LightField>(DEFAULT_LIGHT_FIELD);

  /**
   * The specimen field: one mark of every construction origin, plus the three
   * geometries the selection ring traces. Its own set and its own selection,
   * so poking at a specimen does not disturb the sandbox next door.
   */
  const [specimenSet] = useState<WorkingSet>(createSpecimenSet);
  const [specimenSelection, setSpecimenSelection] = useState<CanvasSelection>({
    kind: "assertion",
    id: "specimen:adjudicated",
  });

  // Motion curves interactive scrub progress (0 to 1)
  const [motionScrub, setMotionScrub] = useState(0.5);

  /**
   * The same tokens the World page puts on its root, with the lab's spine.
   *
   * Composed by `worldChrome.ts` rather than restated here. What made this
   * worth extracting is that the lab is the surface people will tune the
   * design *on*: a lab whose chrome has drifted from the product's reports a
   * look the product does not have, which is worse than having no lab.
   */
  const style = useMemo(
    () => worldShellStyle(mode, { focus: vocabularyFocus, motion: motionPlans }),
    [mode, motionPlans, vocabularyFocus],
  );

  const cameraInsets = useMemo<CameraInsets>(
    () =>
      worldCameraInsets({
        focus: vocabularyFocus,
        tablesOpen,
        tablesWidth,
        readerOpen,
        readerWidth,
      }),
    [readerOpen, readerWidth, tablesOpen, tablesWidth, vocabularyFocus],
  );

  const tableChrome = useMemo<TableChrome>(
    () => ({
      current: activeTable === "relation" ? "other" : activeTable,
      hasFrontier: true,
      onWorld: () => setActiveTable("world"),
      onFrontier: () => setActiveTable("frontier"),
      onClose: () => setTablesOpen(false),
    }),
    [activeTable],
  );

  const onPositions = useCallback(
    (positions: Map<string, { x: number; y: number }>) => {
      setSet((curr) => ({
        ...curr,
        positions: new Map([...curr.positions, ...positions]),
      }));
    },
    [],
  );

  const onRemove = useCallback(() => {
    if (!selection) return;
    setSet((curr) => dropMark(curr, selection.id));
    setSelection(null);
  }, [selection]);

  // Actions for the Motion Director
  const spawnNode = () => {
    const id = `part:P${Math.floor(Math.random() * 900) + 100}`;
    const label = `Transceiver ${id.slice(5)}`;
    const roles: WorldRole[] = [
      { name: "part", type: "REFERENT", referent: true, kinds: ["part"] },
      { name: "bom_item", type: "REFERENT", referent: true, kinds: ["bom"] },
    ];
    const tuple: WorldTuple = {
      assertion_id: `assertion:temp_${id}`,
      origin: "DERIVED",
      values: { part: id, bom_item: "bom:BOM-D" },
    };
    const labels = new Map([
      [id, label],
      ["bom:BOM-D", "BOM-D"],
    ]);
    setSet((curr) =>
      place(curr, {
        relation: "temperature_compatible",
        mode: "DERIVED",
        stale: false,
        completeness: "COMPLETE",
        roles,
        tuple,
        labels,
      }),
    );
    setSelection({ kind: "assertion", id: tuple.assertion_id });
  };

  const despawnNode = () => {
    const assertionIds = Array.from(set.assertions.keys());
    if (assertionIds.length) {
      const dropId = assertionIds[assertionIds.length - 1];
      setSet((curr) => dropMark(curr, dropId));
      if (selection?.id === dropId) setSelection(null);
      return;
    }
    const bond = set.bonds[set.bonds.length - 1];
    if (bond) {
      setSet((curr) => dropMark(curr, bond.assertion_id));
      if (selection?.id === bond.assertion_id) setSelection(null);
      return;
    }
    const referentIds = Array.from(set.referents.keys());
    if (referentIds.length) {
      const dropId = referentIds[referentIds.length - 1];
      setSet((curr) => dropMark(curr, dropId));
      if (selection?.id === dropId) setSelection(null);
    }
  };

  const resetCluster = () => {
    setSet(createMockWorkingSet());
    setSelection({ kind: "assertion", id: "assertion:temp_c300_bom_d" });
  };

  const clearField = () => {
    setSet(emptySet());
    setSelection(null);
  };

  return (
    <main
      className={`product-shell world world-lab${mode === "dark" ? " is-dark" : ""}${vocabularyFocus ? " is-focus" : ""}`}
      style={style}
      data-mode={mode}
    >
      <div className="lab-split">

        {/* ── LEFT: stage / canvas area ──────────────────────────────────────── */}
        <div className="lab-stage">
          {labTab === "sandbox" ? (
            <>
              {/* Live World Shell inside the stage */}
              <div className="product-shell__body">
                <div className="product-shell__scenes">
                  <div className="product-shell__scene is-in">
                    <div className="gm gm--product">
                      <div className="gm__main">
                        <OverlayPanel
                          id="world-tables"
                          side="left"
                          title="Tables"
                          open={tablesOpen}
                          onToggle={setTablesOpen}
                          handleWhen="closed"
                          width={tablesWidth}
                          onWidthChange={setTablesWidth}
                          minWidth={280}
                          maxWidth={520}
                          reserve={readerOpen ? readerWidth : 0}
                          flush
                        >
                          {activeTable === "world" ? (
                            <WorldTable
                              overview={MOCK_OVERVIEW}
                              relations={MOCK_RELATIONS}
                              chrome={tableChrome}
                              onOpen={(name) => {
                                setTableRelation(name);
                                setActiveTable("relation");
                              }}
                            />
                          ) : activeTable === "frontier" ? (
                            <FrontierTable
                              demand={MOCK_DEMAND}
                              relations={MOCK_RELATIONS}
                              problem={null}
                              present={new Set(["assertion:temp_c300_bom_d"])}
                              chrome={tableChrome}
                              onFocus={(obl) => setSelection({ kind: "demand", id: obl.key })}
                            />
                          ) : (
                            <RelationTable
                              relation={MOCK_RELATIONS.find((r) => r.name === tableRelation) ?? MOCK_RELATIONS[0]}
                              present={new Set(["assertion:temp_c300_bom_d"])}
                              onFocus={() => {}}
                              onWiden={() => setActiveTable("world")}
                              onDerivation={() => {}}
                              chrome={tableChrome}
                            />
                          )}
                        </OverlayPanel>

                        <div className="gm__stage world__plane">
                          {fieldSize(set) > 0 ? (
                            <div className={`world__layer${vocabularyFocus ? " is-parked" : ""}`}>
                              <WorldCanvas
                                set={set}
                                mode={mode}
                                params={markKnobs}
                                hovered={hovered}
                                selection={selection}
                                show={show}
                                focusId={vocabularyFocus ? null : focus?.id ?? null}
                                focusToken={focus?.token ?? 0}
                                insets={cameraInsets}
                                light={lightField}
                                onHover={setHovered}
                                onSelect={setSelection}
                                onPositions={onPositions}
                                onRemove={onRemove}
                              />
                            </div>
                          ) : null}
                          {fieldSize(set) === 0 || vocabularyFocus ? (
                            <div className="world__layer">
                              <SchemaCanvas
                                relations={MOCK_RELATIONS}
                                mode={mode}
                                namedAtRest={namedAtRest}
                                inverted={vocabularyFocus}
                                active={hoveredRelation ?? focusedRelation}
                                selected={focusedRelation}
                                focusId={focus?.id ?? null}
                                focusToken={focus?.token ?? 0}
                                insets={cameraInsets}
                                onHover={setHoveredRelation}
                                onSelect={setFocusedRelation}
                              />
                            </div>
                          ) : null}
                        </div>

                        <OverlayPanel
                          id="world-reader"
                          side="right"
                          title="World reader"
                          open={readerOpen}
                          onToggle={setReaderOpen}
                          handle={false}
                          width={readerWidth}
                          onWidthChange={setReaderWidth}
                          reserve={tablesOpen ? tablesWidth : 34}
                          flush
                        >
                          <div className="world-reader">
                            {selection?.kind === "assertion" ? (
                              <AssertionPanel
                                assertion={MOCK_ASSERTION_DERIVED}
                                folding="open"
                                onFold={() => {}}
                                onTable={(rel) => { setTableRelation(rel); setActiveTable("relation"); setTablesOpen(true); }}
                                onDerivation={() => {}}
                                onRemove={onRemove}
                                onClose={() => setReaderOpen(false)}
                              />
                            ) : selection?.kind === "demand" ? (
                              <DemandPanel
                                obligation={MOCK_OBLIGATION}
                                demand={MOCK_DEMAND}
                                roles={["new_part", "old_part", "context"]}
                                onTable={(rel) => { setTableRelation(rel); setActiveTable("relation"); setTablesOpen(true); }}
                                onRemove={onRemove}
                                onClose={() => setReaderOpen(false)}
                              />
                            ) : (
                              <ReferentPanel
                                detail={MOCK_REFERENT}
                                set={set}
                                requests={new Map()}
                                onExpand={() => {}}
                                onTable={(rel) => { setTableRelation(rel); setActiveTable("relation"); setTablesOpen(true); }}
                                onDrop={onRemove}
                                onClose={() => setReaderOpen(false)}
                              />
                            )}
                          </div>
                        </OverlayPanel>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              {/* Instrument bar inside stage */}
              <div className="product-shell__instrument" aria-label="Surface controls">
                <div className={chromeClass("instrument")}>
                  <div className="gm__choosing">
                    <div className="instrument__group" role="group" aria-label="Find a referent">
                      <Find
                        directory={MOCK_DIRECTORY}
                        onPick={(id, label) => {
                          setSet((curr) => place(curr, {
                            relation: "lifecycle", mode: "BASE", stale: false, completeness: null,
                            roles: [
                              { name: "part", type: "REFERENT", referent: true, kinds: ["part"] },
                              { name: "status", type: "TEXT", referent: false },
                            ],
                            tuple: { assertion_id: `assertion:life_${id}`, origin: "MECHANICAL", values: { part: id, status: "active" } },
                            labels: new Map([[id, label]]),
                          }));
                          setSelection({ kind: "referent", id });
                        }}
                      />
                    </div>
                  </div>
                  <ShowBand
                    show={show}
                    onShow={setShow}
                    names={{
                      on: namedAtRest,
                      onToggle: () => setNamedAtRest((on) => !on),
                    }}
                  />
                  <div className="instrument__group" role="group" aria-label="Field">
                    {selection ? <button type="button" onClick={onRemove}>remove</button> : null}
                    <button type="button" onClick={() => setVocabularyFocus((f) => !f)}>
                      {vocabularyFocus ? "field" : "vocabulary"}
                    </button>
                  </div>
                </div>
              </div>
            </>
          ) : labTab === "components" ? (
            /* Component stage: scrollable gallery of specimens */
            <div className="lab-component-stage">
              {componentSection === "marks" ? (
                <div className="lab-full-stage">
                  {/* Not a drawing of the marks — the marks. Origin geometry
                      is the read side's load-bearing rule, and a gallery that
                      restates it in SVG is a second opinion about what the
                      product looks like. The knobs below drive `MarkParams`,
                      which is the same object `WorldCanvas` ships with. */}
                  <WorldCanvas
                    set={specimenSet}
                    mode={mode}
                    params={markKnobs}
                    hovered={null}
                    selection={specimenSelection}
                    show={SPECIMEN_SHOW}
                    insets={SPECIMEN_INSETS}
                    ants={antTuning}
                    light={lightField}
                    onHover={() => {}}
                    onSelect={setSpecimenSelection}
                    onPositions={() => {}}
                    onRemove={() => {}}
                  />
                </div>
              ) : componentSection === "ants" ? (
                <div className="lab-full-stage">
                  {/* The three geometries the ring traces, drawn by the real
                      `SelectionAnts` through the real canvas: a disc, a
                      standing plate, and a filament trimmed clear of its two
                      ends. The bead count is locked to graph-space path
                      length, which is the part a hand-drawn dasharray cannot
                      reproduce — pick a mark and watch the count hold as you
                      zoom. */}
                  <WorldCanvas
                    set={specimenSet}
                    mode={mode}
                    params={markKnobs}
                    hovered={null}
                    selection={specimenSelection}
                    show={SPECIMEN_SHOW}
                    insets={SPECIMEN_INSETS}
                    ants={antTuning}
                    light={lightField}
                    onHover={() => {}}
                    onSelect={setSpecimenSelection}
                    onPositions={() => {}}
                    onRemove={() => {}}
                  />
                </div>
              ) : componentSection === "tables" ? (
                <div className="lab-full-stage">
                  {demoTableKind === "world" ? (
                    <WorldTable overview={MOCK_OVERVIEW} relations={MOCK_RELATIONS} chrome={tableChrome} onOpen={() => setDemoTableKind("relation")} />
                  ) : demoTableKind === "frontier" ? (
                    <FrontierTable demand={MOCK_DEMAND} relations={MOCK_RELATIONS} problem={null} present={new Set(["assertion:temp_c300_bom_d"])} chrome={tableChrome} onFocus={() => {}} />
                  ) : demoTableKind === "relation" ? (
                    <RelationTable relation={MOCK_RELATIONS[0]} present={new Set(["assertion:temp_c300_bom_d"])} onFocus={() => {}} onWiden={() => setDemoTableKind("world")} onDerivation={() => setDemoTableKind("derivation")} chrome={tableChrome} />
                  ) : (
                    <DerivationView relation="temperature_compatible" assertionId="assertion:temp_c300_bom_d" present={new Set(["assertion:temp_c300_bom_d"])} onOpen={() => {}} onTable={() => setDemoTableKind("relation")} onFocus={() => {}} chrome={tableChrome} />
                  )}
                </div>
              ) : componentSection === "reader" ? (
                <div className="reader-specimen-container">
                  <div className="reader-specimen-card">
                    <h4>Assertion — Derived</h4>
                    <AssertionPanel assertion={MOCK_ASSERTION_DERIVED} folding="open" onFold={() => {}} onTable={() => {}} onDerivation={() => {}} onRemove={() => {}} onClose={() => {}} />
                  </div>
                  <div className="reader-specimen-card">
                    <h4>Assertion — Mechanical</h4>
                    <AssertionPanel assertion={MOCK_ASSERTION_MECHANICAL} folding="open" onFold={() => {}} onTable={() => {}} onDerivation={() => {}} onRemove={() => {}} onClose={() => {}} />
                  </div>
                  <div className="reader-specimen-card">
                    <h4>Referent</h4>
                    <ReferentPanel detail={MOCK_REFERENT} set={set} requests={new Map()} onExpand={() => {}} onTable={() => {}} onDrop={() => {}} onClose={() => {}} />
                  </div>
                  <div className="reader-specimen-card">
                    <h4>Obligation</h4>
                    <DemandPanel obligation={MOCK_OBLIGATION} demand={MOCK_DEMAND} roles={["new_part", "old_part", "context"]} onTable={() => {}} onRemove={() => {}} onClose={() => {}} />
                  </div>
                </div>
              ) : componentSection === "construction" ? (
                <div className="lab-construction-demo">
                  <Spine passes={MOCK_PASSES} open={MOCK_DOCKET.counts.open} selected={demoPass} onSelect={setDemoPass} />
                  <Docket docket={MOCK_DOCKET} selected={demoObligation} problem={null} onOpen={setDemoObligation} />
                </div>
              ) : componentSection === "transitions" ? (
                <LabTransitions />
              ) : componentSection === "instrument" ? (
                <div className="lab-instrument-demo">
                  <div className={chromeClass("instrument")}>
                    <div className="gm__choosing">
                      <div className="instrument__group" role="group" aria-label="Find a referent">
                        <Find directory={MOCK_DIRECTORY} onPick={() => {}} />
                      </div>
                    </div>
                    <ShowBand show={show} onShow={setShow} />
                  </div>
                </div>
              ) : (
                /* panels */
                <div className="lab-full-stage" style={{ position: "relative" }}>
                  <OverlayPanel id="lab-panel-left" side="left" title="Tables Panel Specimen" open={true} onToggle={() => {}} width={300} onWidthChange={() => {}} minWidth={220} maxWidth={420}>
                    <div style={{ padding: "1rem" }}>
                      <p className="lab-body" style={{ color: "var(--ink-muted)" }}>Windowed list rows live inside this body. Drag the right edge to resize without triggering a canvas redraw.</p>
                    </div>
                  </OverlayPanel>
                </div>
              )}
            </div>
          ) : (
            /* Motion DNA stage: curve graphs */
            <div className="lab-motion-stage">
              <div className="motion-plans-grid">
                {(["emit", "absorb", "settle", "flow", "hold"] as MotionIntent[]).map((intent) => {
                  const plan = motionPlans[intent];
                  const progress = motionScrub;
                  const sampled = plan.sample(progress * plan.durationMs);
                  return (
                    <div key={intent} className="motion-plan-card">
                      <header className="motion-card-header">
                        <h4>{intent.toUpperCase()}</h4>
                        <span className="motion-badge">{plan.durationMs}ms</span>
                      </header>
                      <p className="motion-css-code">{plan.easing.css}</p>
                      <div className="motion-curve-graph">
                        <svg width="100%" height="120" viewBox="0 0 220 120" preserveAspectRatio="none">
                          <line x1="20" y1="100" x2="200" y2="100" stroke="var(--rule)" />
                          <line x1="20" y1="20" x2="20" y2="100" stroke="var(--rule)" />
                          <path
                            d={(() => {
                              const pts: string[] = [];
                              for (let i = 0; i <= 40; i++) {
                                const u = i / 40;
                                const x = 20 + u * 180;
                                const y = 100 - plan.easing.sample(u) * 80;
                                pts.push(`${i === 0 ? "M" : "L"} ${x} ${y}`);
                              }
                              return pts.join(" ");
                            })()}
                            fill="none" stroke="var(--ink)" strokeWidth="2"
                          />
                          <circle cx={20 + progress * 180} cy={100 - sampled * 80} r="4" fill="var(--attention, #e54d2e)" />
                        </svg>
                      </div>
                      <div className="motion-runner-track">
                        <div className="motion-runner-bead" style={{ transform: `translateX(${sampled * 160}px) scale(${0.86 + sampled * 0.14})`, opacity: 0.2 + sampled * 0.8 }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* ── RIGHT: fixed scrollable controls panel ─────────────────────────── */}
        <aside className="lab-controls" aria-label="Lab controls">

          <div className="ctrl-section">
            <span className="ctrl-label">VIEW</span>
            <nav className="ctrl-group ctrl-group--stack" aria-label="Lab views">
              <button
                type="button"
                data-active={labTab === "sandbox"}
                onClick={() => setLabTab("sandbox")}
              >
                Sandbox & Director
              </button>
              <button
                type="button"
                data-active={labTab === "components"}
                onClick={() => setLabTab("components")}
              >
                Component Studio
              </button>
              <button
                type="button"
                data-active={labTab === "motion"}
                onClick={() => setLabTab("motion")}
              >
                Motion DNA
              </button>
            </nav>
          </div>

          <div className="ctrl-section">
            <span className="ctrl-label">SPEED</span>
            <div className="ctrl-group">
              {SPEED_OPTIONS.map((speed) => (
                <button
                  key={speed}
                  type="button"
                  data-active={speedFactor === speed}
                  onClick={() => setSpeedFactor(speed)}
                >
                  {speed}×
                </button>
              ))}
            </div>
          </div>

          <div className="ctrl-section">
            <span className="ctrl-label">SURFACE</span>
            <div className="ctrl-group">
              <button
                type="button"
                onClick={() => setMode((m) => (m === "light" ? "dark" : "light"))}
              >
                {mode === "light" ? "Dark" : "Light"}
              </button>
              <a href="#/world" className="ctrl-link">← World</a>
            </div>
          </div>

          <div className="ctrl-section">
            <span className="ctrl-label">LIGHT</span>
            {/* The law, plotted. A number for `falloff` means nothing on its
                own; the fifth bar going dark is the thing you are choosing. */}
            <div className="light-ladder" aria-hidden>
              {[0, 1, 2, 3, 4, 5].map((hops) => (
                <div key={hops} className="light-ladder__step">
                  <span
                    className="light-ladder__mark"
                    style={{ opacity: luminance(hops, lightField) }}
                  />
                  <b>{hops}</b>
                </div>
              ))}
            </div>
            <div className="ctrl-sliders">
              <label>
                <span>Falloff — {lightField.falloff.toFixed(1)} hops</span>
                <input
                  type="range"
                  min={0.4}
                  max={4}
                  step={0.1}
                  value={lightField.falloff}
                  onChange={(e) =>
                    setLightField((f) => ({ ...f, falloff: Number(e.target.value) }))
                  }
                />
              </label>
              <label>
                <span>Ambient — {lightField.ambient.toFixed(2)}</span>
                <input
                  type="range"
                  min={0}
                  max={0.9}
                  step={0.01}
                  value={lightField.ambient}
                  onChange={(e) =>
                    setLightField((f) => ({ ...f, ambient: Number(e.target.value) }))
                  }
                />
              </label>
            </div>
          </div>
          {labTab === "sandbox" ? (<>

            <div className="ctrl-section">
              <span className="ctrl-label">CANVAS</span>
              <div className="ctrl-group">
                <button type="button" onClick={spawnNode}>+ Node (Emit)</button>
                <button type="button" onClick={despawnNode}>− Node (Absorb)</button>
                <button type="button" onClick={resetCluster}>Reset cluster</button>
                <button type="button" onClick={clearField}>Clear field</button>
                <button type="button" data-active={vocabularyFocus} onClick={() => setVocabularyFocus((f) => !f)}>
                  {vocabularyFocus ? "Field zoom" : "Schema zoom"}
                </button>
              </div>
            </div>

            <div className="ctrl-section">
              <span className="ctrl-label">CAMERA</span>
              <div className="ctrl-group">
                <button type="button" onClick={() => setFocus({ id: "part:C300", token: Date.now() })}>Pan → part:C300</button>
                <button type="button" onClick={() => setFocus({ id: "bom:BOM-D", token: Date.now() })}>Pan → BOM-D</button>
              </div>
            </div>

            <div className="ctrl-section">
              <span className="ctrl-label">SELECTION</span>
              <div className="ctrl-group">
                <button type="button" onClick={() => setSelection({ kind: "referent", id: "part:C300" })}>Disc (part:C300)</button>
                <button type="button" onClick={() => setSelection({ kind: "assertion", id: "assertion:req_temp_bom_d" })}>Plate (req_temp)</button>
                <button type="button" onClick={() => setSelection({ kind: "assertion", id: "assertion:temp_c300_bom_d" })}>Edge label</button>
                <button type="button" onClick={() => setSelection(null)}>Clear selection</button>
              </div>
            </div>

            <div className="ctrl-section">
              <span className="ctrl-label">PANELS</span>
              <div className="ctrl-group">
                <button type="button" data-active={tablesOpen} onClick={() => setTablesOpen((o) => !o)}>
                  {tablesOpen ? "Close Tables" : "Open Tables"}
                </button>
                <button type="button" data-active={readerOpen} onClick={() => setReaderOpen((o) => !o)}>
                  {readerOpen ? "Close Reader" : "Open Reader"}
                </button>
              </div>
              <div className="ctrl-sliders">
                <label><span>Tables width — {tablesWidth}px</span>
                  <input type="range" min={260} max={520} value={tablesWidth} onChange={(e) => setTablesWidth(Number(e.target.value))} />
                </label>
                <label><span>Reader width — {readerWidth}px</span>
                  <input type="range" min={260} max={520} value={readerWidth} onChange={(e) => setReaderWidth(Number(e.target.value))} />
                </label>
              </div>
            </div>

          </>) : labTab === "components" ? (<>

            <div className="ctrl-section">
              <span className="ctrl-label">COMPONENT</span>
              <div className="ctrl-group ctrl-group--stack">
                {(["marks", "ants", "panels", "tables", "reader", "instrument", "construction", "transitions"] as ComponentSection[]).map((s) => (
                  <button key={s} type="button" data-active={componentSection === s} onClick={() => setComponentSection(s)}>
                    {s === "marks" ? "Marks & Plates" : s === "ants" ? "Marching Ants" : s === "panels" ? "Overlay Panels" : s === "tables" ? "Tables & Data" : s === "reader" ? "Reader Cards" : s === "instrument" ? "Instrument" : s === "construction" ? "Spine & Docket" : "Transitions"}
                  </button>
                ))}
              </div>
            </div>

            {componentSection === "marks" ? (
              <div className="ctrl-section">
                <span className="ctrl-label">GEOMETRY</span>
                <div className="ctrl-sliders">
                  <label><span>Disc diameter — {markKnobs.discDiameter}px</span>
                    <input type="range" min={36} max={120} value={markKnobs.discDiameter} onChange={(e) => setMarkKnobs((k) => ({ ...k, discDiameter: Number(e.target.value) }))} />
                  </label>
                  <label><span>Chip height — {markKnobs.chipHeight}px</span>
                    <input type="range" min={12} max={32} value={markKnobs.chipHeight} onChange={(e) => setMarkKnobs((k) => ({ ...k, chipHeight: Number(e.target.value) }))} />
                  </label>
                  <label><span>Edge width — {markKnobs.edgeWidth}px</span>
                    <input type="range" min={1} max={4} step={0.5} value={markKnobs.edgeWidth} onChange={(e) => setMarkKnobs((k) => ({ ...k, edgeWidth: Number(e.target.value) }))} />
                  </label>
                  <label className="ctrl-checkbox"><span>Mechanical outline</span>
                    <input type="checkbox" checked={markKnobs.mechanicalOutline} onChange={(e) => setMarkKnobs((k) => ({ ...k, mechanicalOutline: e.target.checked }))} />
                  </label>
                </div>
              </div>
            ) : componentSection === "ants" ? (
              <div className="ctrl-section">
                <span className="ctrl-label">ANT RING</span>
                <div className="ctrl-sliders">
                  <label><span>Clearance — {antClearance}px</span>
                    <input type="range" min={1} max={20} value={antClearance} onChange={(e) => setAntClearance(Number(e.target.value))} />
                  </label>
                  <label><span>Dot gap — {antDotGap}px</span>
                    <input type="range" min={2} max={10} step={0.5} value={antDotGap} onChange={(e) => setAntDotGap(Number(e.target.value))} />
                  </label>
                  <label><span>Stroke width — {antLineWidth}px</span>
                    <input type="range" min={1} max={3} step={0.5} value={antLineWidth} onChange={(e) => setAntLineWidth(Number(e.target.value))} />
                  </label>
                  <label><span>Speed — {antSpeed}px/s</span>
                    <input type="range" min={0} max={24} value={antSpeed} onChange={(e) => setAntSpeed(Number(e.target.value))} />
                  </label>
                  <label className="ctrl-checkbox"><span>Animated</span>
                    <input type="checkbox" checked={antAnimated} onChange={(e) => setAntAnimated(e.target.checked)} />
                  </label>
                </div>
              </div>
            ) : componentSection === "tables" ? (
              <div className="ctrl-section">
                <span className="ctrl-label">TABLE VIEW</span>
                <div className="ctrl-group ctrl-group--stack">
                  {(["world", "frontier", "relation", "derivation"] as const).map((k) => (
                    <button key={k} type="button" data-active={demoTableKind === k} onClick={() => setDemoTableKind(k)}>
                      {k === "world" ? "World catalog" : k === "frontier" ? "Frontier demand" : k === "relation" ? "Relation extension" : "Derivation deps"}
                    </button>
                  ))}
                </div>
              </div>
            ) : null}

          </>) : (<>

            {/* Motion DNA controls */}
            <div className="ctrl-section">
              <span className="ctrl-label">SCRUB</span>
              <div className="ctrl-sliders">
                <label><span>Progress — {Math.round(motionScrub * 100)}%</span>
                  <input type="range" min={0} max={1} step={0.01} value={motionScrub} onChange={(e) => setMotionScrub(Number(e.target.value))} />
                </label>
              </div>
            </div>

            <div className="ctrl-section">
              <span className="ctrl-label">ABOUT</span>
              <p className="ctrl-prose">
                Curves are asymmetric: emit uses an outward escape impulse (out-quad),
                absorb uses inward acceleration (in-quad). The scrubber shows where the
                bead sits at any fraction of the duration.
              </p>
            </div>

          </>)}

        </aside>
      </div>
    </main>
  );
}
