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

import { useMemo, useState } from "react";
import { type ThemeMode } from "../styles/graphDna";
import { scaleMotionPlans, type MotionIntent } from "../styles/motion";
import {
  DEFAULT_LIGHT_FIELD,
  lift,
  reflected,
  type LightField,
} from "../styles/light";
import { worldShellStyle } from "./worldChrome";
import {
  MARK_DEFAULTS,
  type MarkParams,
} from "./marks";
import { SHOW_DEFAULT, type ShowState } from "./show";
import { ShowBand } from "./ShowBand";
import { type WorkingSet } from "./workingSet";
import {
  ANT_DEFAULTS,
  MATERIAL_DEFAULTS,
  WorldCanvas,
  type CanvasSelection,
  type MaterialTuning,
  type SelectionTreatment,
} from "./WorldCanvas";
import { Spine } from "../construction/Spine";
import { Docket } from "../construction/Docket";
import { LabTransitions } from "./LabTransitions";
import { OverlayPanel } from "../product/OverlayPanel";
import { chromeClass } from "../product/overlayChrome";
import { WorldTable } from "./WorldTable";
import { FrontierTable } from "./FrontierTable";
import { RelationTable } from "./RelationTable";
import { DerivationView } from "./DerivationView";
import { LabRange, LabToggle } from "./labControls";
import { type TableChrome } from "./tableChrome";
import {
  Find,
  AssertionPanel,
  DemandPanel,
  ReferentPanel,
  WorldPage,
  readStoredWorldTheme,
  type WorldPageTuning,
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
  const [mode, setMode] = useState<ThemeMode>(readStoredWorldTheme);
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

  // Fixtures remain only for isolated component specimens. The sandbox below
  // is the real WorldPage and owns its own live working set.
  const [mockSet] = useState<WorkingSet>(createMockWorkingSet);
  const [show, setShow] = useState<ShowState>(SHOW_DEFAULT);
  const [activeTable, setActiveTable] = useState<"world" | "frontier" | "relation">("world");
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
  const [selectionTreatment, setSelectionTreatment] =
    useState<SelectionTreatment>("outer-field");
  const [contactEnabled, setContactEnabled] = useState(true);
  const [pressScale, setPressScale] = useState(MATERIAL_DEFAULTS.pressScale);
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
  const materialTuning = useMemo<MaterialTuning>(
    () => ({ contact: contactEnabled, pressScale }),
    [contactEnabled, pressScale],
  );

  /**
   * The light field. Two numbers: how far light reaches through the graph,
   * and how much of the world stays readable where it does not.
   */
  const [lightField, setLightField] = useState<LightField>(DEFAULT_LIGHT_FIELD);
  const worldTuning = useMemo<WorldPageTuning>(
    () => ({
      params: markKnobs,
      ants: antTuning,
      motion: motionPlans,
      material: materialTuning,
      selectionTreatment,
      light: lightField,
    }),
    [
      antTuning,
      lightField,
      markKnobs,
      materialTuning,
      motionPlans,
      selectionTreatment,
    ],
  );

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
    () => worldShellStyle(mode, { motion: motionPlans }),
    [mode, motionPlans],
  );

  const tableChrome = useMemo<TableChrome>(
    () => ({
      current: activeTable === "relation" ? "other" : activeTable,
      hasFrontier: true,
      onWorld: () => setActiveTable("world"),
      onFrontier: () => setActiveTable("frontier"),
      onClose: () => {},
    }),
    [activeTable],
  );

  return (
    <main
      className={`product-shell world world-lab${mode === "dark" ? " is-dark" : ""}`}
      style={style}
      data-mode={mode}
    >
      <div className="lab-split">

        {/* ── LEFT: stage / canvas area ──────────────────────────────────────── */}
        <div className="lab-stage">
          {labTab === "sandbox" ? (
            <WorldPage
              tuning={worldTuning}
              lab
              mode={mode}
              onModeChange={setMode}
            />
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
                    motion={motionPlans}
                    material={materialTuning}
                    selectionTreatment={selectionTreatment}
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
                    motion={motionPlans}
                    material={materialTuning}
                    selectionTreatment={selectionTreatment}
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
                    <ReferentPanel detail={MOCK_REFERENT} set={mockSet} requests={new Map()} onExpand={() => {}} onRetract={() => {}} onTable={() => {}} onDrop={() => {}} onClose={() => {}} />
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
                      <div className="instrument__group" role="group" aria-label="find">
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
            {/* The law, plotted on a quiet mark — one that rests at 0.45,
                because a mark already at 1 is exactly what this law leaves
                alone and would plot as a flat row of identical bars. The
                right-hand bar is the unlit rest, which nothing dims below. */}
            <div className="light-ladder" aria-hidden>
              {[0, 1, 2, 3, 4, 5, null].map((hops) => (
                <div key={hops ?? "rest"} className="light-ladder__step">
                  <span
                    className="light-ladder__mark"
                    style={{ opacity: reflected(0.45, lift(hops, lightField)) }}
                  />
                  <b>{hops ?? "\u221e"}</b>
                </div>
              ))}
            </div>
            <div className="ctrl-sliders">
              <LabRange
                label={`Falloff — ${lightField.falloff.toFixed(1)} hops`}
                min={0.4}
                max={4}
                step={0.1}
                value={lightField.falloff}
                onChange={(falloff) => setLightField((f) => ({ ...f, falloff }))}
              />
              <LabRange
                label={`Lift — ${lightField.lift.toFixed(2)}`}
                min={0}
                max={1}
                step={0.01}
                value={lightField.lift}
                onChange={(lift) => setLightField((f) => ({ ...f, lift }))}
              />
            </div>
          </div>
          {labTab === "sandbox" ? (<>

            <div className="ctrl-section">
              <span className="ctrl-label">CAUSAL MATERIAL</span>
              <p className="ctrl-prose">
                Press applies load. Release settles the body; selection binds
                only after the click is committed.
              </p>
              <div className="ctrl-group ctrl-group--stack">
                {(
                  [
                    ["outer-field", "Outer field · control"],
                    ["excited-boundary", "Excited boundary"],
                    ["hollow", "Hollow · contrast"],
                  ] as const
                ).map(([treatment, label]) => (
                  <button
                    key={treatment}
                    type="button"
                    data-active={selectionTreatment === treatment}
                    onClick={() => setSelectionTreatment(treatment)}
                  >
                    {label}
                  </button>
                ))}
              </div>
              <div className="ctrl-sliders">
                <LabToggle
                  label="Contact response"
                  checked={contactEnabled}
                  onChange={setContactEnabled}
                />
                <LabRange
                  label={`Held size — ${Math.round(pressScale * 100)}%`}
                  min={90}
                  max={100}
                  value={Math.round(pressScale * 100)}
                  onChange={(value) => setPressScale(value / 100)}
                />
              </div>
            </div>

            <div className="ctrl-section">
              <span className="ctrl-label">FULL SYSTEM</span>
              <p className="ctrl-prose">
                This is the real World surface. Use its finder, tables and
                reader to seed any referent, grow or retract neighborhoods,
                fold assertions, inspect derivations and remove matter.
              </p>
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
                  <LabRange label={`Disc diameter — ${markKnobs.discDiameter}px`} min={36} max={120} value={markKnobs.discDiameter} onChange={(discDiameter) => setMarkKnobs((k) => ({ ...k, discDiameter }))} />
                  <LabRange label={`Chip height — ${markKnobs.chipHeight}px`} min={12} max={32} value={markKnobs.chipHeight} onChange={(chipHeight) => setMarkKnobs((k) => ({ ...k, chipHeight }))} />
                  <LabRange label={`Edge width — ${markKnobs.edgeWidth}px`} min={1} max={4} step={0.5} value={markKnobs.edgeWidth} onChange={(edgeWidth) => setMarkKnobs((k) => ({ ...k, edgeWidth }))} />
                  <LabToggle label="Mechanical outline" checked={markKnobs.mechanicalOutline} onChange={(mechanicalOutline) => setMarkKnobs((k) => ({ ...k, mechanicalOutline }))} />
                </div>
              </div>
            ) : componentSection === "ants" ? (
              <div className="ctrl-section">
                <span className="ctrl-label">ANT RING</span>
                <div className="ctrl-sliders">
                  <LabRange label={`Clearance — ${antClearance}px`} min={1} max={20} value={antClearance} onChange={setAntClearance} />
                  <LabRange label={`Dot gap — ${antDotGap}px`} min={2} max={10} step={0.5} value={antDotGap} onChange={setAntDotGap} />
                  <LabRange label={`Stroke width — ${antLineWidth}px`} min={1} max={3} step={0.5} value={antLineWidth} onChange={setAntLineWidth} />
                  <LabRange label={`Speed — ${antSpeed}px/s`} min={0} max={24} value={antSpeed} onChange={setAntSpeed} />
                  <LabToggle label="Animated" checked={antAnimated} onChange={setAntAnimated} />
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
                <LabRange label={`Progress — ${Math.round(motionScrub * 100)}%`} min={0} max={1} step={0.01} value={motionScrub} onChange={setMotionScrub} />
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
