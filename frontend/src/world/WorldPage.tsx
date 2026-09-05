/**
 * World — the read-side explorer.
 *
 * Two modes over one design language. You land on the **vocabulary**: the
 * schema graph, the only whole-World view rule 9 allows, answering *what kind
 * of world is this?* before you have anything to search for. Finding a referent
 * moves you to the **field**, where a neighborhood is grown one expansion at a
 * time and never rendered whole.
 *
 * Search is client-side against every referent, loaded once. At the largest
 * world we have that is 3,118 rows in about three milliseconds, so a request
 * per keystroke would be slower than holding the list — and a search that
 * cannot be out of date is one less thing to reason about.
 *
 * Deliberately not wrapped in `ProductShell`. That shell knows about graphs,
 * logs, constructions, an operator plane and a write path — none of which
 * exist here. Chrome is imported from that page: the same classes, the same
 * overlay, finder, reader and instrument. Where a World fact has no Graph
 * equivalent, WorldPage.css keeps the remainder.
 */

import {
  useCallback,
  useEffect,
  useId,
  useMemo,
  useReducer,
  useRef,
  useState,
} from "react";
import {
  worldApi,
  type WorldAssertion,
  type WorldDemand,
  type WorldOverview,
  type WorldReferent,
  type WorldRelation,
  type WorldRole,
  type WorldTuple,
} from "../api/world";
import { type ThemeMode } from "../styles/graphDna";
import {
  DEFAULT_MOTION_PLANS,
  still,
  type MotionPlans,
} from "../styles/motion";
import type { LightField } from "../styles/light";
import { ShowBand } from "./ShowBand";
import {
  TABLES_HANDLE_RESERVE,
  TABLES_WIDTH_DEFAULT,
  worldCameraInsets,
  worldChromeDockVars,
  worldShellStyle,
} from "./worldChrome";
import { DerivationView } from "./DerivationView";
import {
  expansionRequestReducer,
  expansionViewState,
  type ExpansionRequests,
} from "./expansionMachine";
import { FrontierTable, type Obligation } from "./FrontierTable";
import { MARK_DEFAULTS, type MarkParams } from "./marks";
import { RelationTable } from "./RelationTable";
import { SchemaCanvas } from "./SchemaCanvas";
import { fieldGraph } from "./hops";
import { readField, writeField } from "./fieldMemory";
import { chipKind } from "./schemaGraph";
import type { TableChrome } from "./tableChrome";
import { WorldTable } from "./WorldTable";
import {
  WorldCanvas,
  type AntTuning,
  type CanvasSelection,
  type MaterialTuning,
  type SelectionTreatment,
} from "./WorldCanvas";
import type { CameraInsets } from "./canvasFocus";
import {
  arrange,
  collapse,
  retractExpansion,
  dropMark,
  emptySet,
  expand,
  expansionKey,
  fieldSize,
  foldingOf,
  MAX_FIELD_NODES,
  open as openBond,
  place,
  placeDemand,
  seed,
  type Arrangement,
  type Point,
  type WorkingSet,
} from "./workingSet";
import { OverlayPanel } from "../product/OverlayPanel";
import { chromeClass } from "../product/overlayChrome";
import { Swap } from "../styles/Swap";
import { useHeld, usePresence } from "../styles/usePresence";
import { useSequencedSwap } from "../styles/useSequencedSwap";
import { PanelClose } from "./panelChrome";
import {
  readStoredPanelSize,
  storePanelSize,
} from "../product/ResizableDivider";
import "../styles/presence.css";
import {
  SHOW_DEFAULT,
  assertionShown,
  relationShown,
  reveal,
  type ShowState,
} from "./show";
import "./WorldPage.css";
import "../product/ProductShell.css";
import "../product/NodeFinder.css";
import "../product/NodeReaderPanel.css";
import "../product/GraphWorkspace.css";
import "../product/OverlayPanel.css";
import "../product/overlayChrome.css";

export function readStoredWorldTheme(): ThemeMode {
  try {
    return localStorage.getItem("graphauthor.productTheme") === "dark"
      ? "dark"
      : "light";
  } catch {
    return "light";
  }
}

export function conditionOf(
  stale: boolean,
  completeness: { status: string; universe: string | null } | null,
): string {
  const bits: string[] = [];
  if (stale) bits.push("stale");
  if (completeness && completeness.status !== "COMPLETE") {
    bits.push(
      completeness.universe
        ? `${completeness.status.toLowerCase()} over ${completeness.universe}`
        : completeness.status.toLowerCase(),
    );
  }
  return bits.length ? ` · ${bits.join(" · ")}` : "";
}

export type Directory = { id: string; label: string | null }[];

export function Find({
  directory,
  onPick,
}: {
  directory: Directory;
  onPick: (id: string, label: string) => void;
}) {
  const [query, setQuery] = useState("");
  const [focused, setFocused] = useState(false);
  const [active, setActive] = useState(0);
  const rootRef = useRef<HTMLDivElement | null>(null);
  const listId = useId();
  const matches = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return [];
    return directory
      .filter(
        (item) =>
          item.id.toLowerCase().includes(needle) ||
          (item.label ?? "").toLowerCase().includes(needle),
      )
      .slice(0, 10);
  }, [directory, query]);
  const open = focused && Boolean(query.trim());
  const presence = usePresence(open);

  useEffect(() => setActive(0), [query]);

  useEffect(() => {
    if (!open) return;
    const closeOutside = (event: PointerEvent) => {
      if (rootRef.current?.contains(event.target as Node)) return;
      setFocused(false);
      rootRef.current?.querySelector("input")?.blur();
    };
    document.addEventListener("pointerdown", closeOutside, true);
    return () => document.removeEventListener("pointerdown", closeOutside, true);
  }, [open]);

  const pick = (item: Directory[number]) => {
    onPick(item.id, item.label || item.id);
    setQuery("");
    setFocused(false);
    rootRef.current?.querySelector("input")?.blur();
  };

  return (
    <div className="nodefind" ref={rootRef}>
      <input
        className="nodefind__input"
        type="text"
        role="combobox"
        aria-expanded={open}
        aria-controls={listId}
        aria-autocomplete="list"
        aria-activedescendant={
          open && matches[active] ? `${listId}-${active}` : undefined
        }
        value={query}
        placeholder="find..."
        onChange={(event) => {
          setQuery(event.target.value);
          setFocused(true);
        }}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        onKeyDown={(event) => {
          if (event.key === "Escape") {
            event.preventDefault();
            event.stopPropagation();
            setQuery("");
            setFocused(false);
            event.currentTarget.blur();
            return;
          }
          if (!matches.length) return;
          if (event.key === "ArrowDown") {
            event.preventDefault();
            setActive((index) => (index + 1) % matches.length);
          } else if (event.key === "ArrowUp") {
            event.preventDefault();
            setActive(
              (index) => (index - 1 + matches.length) % matches.length,
            );
          } else if (event.key === "Enter") {
            event.preventDefault();
            const item = matches[active];
            if (item) pick(item);
          }
        }}
      />
      {presence.mounted ? (
        <ul
          id={listId}
          role="listbox"
          className={`nodefind__list motion-layer motion-layer--fade${presence.shown ? " is-in" : ""}`}
        >
          {/* The list arrives and departs; what is *in* it does not tween.
              Typing another character is a new answer, and animating between
              two answers draws a continuity retrieval does not claim. */}
          {matches.length ? (
            matches.map((item, index) => (
              <li
                key={item.id}
                id={`${listId}-${index}`}
                role="option"
                aria-selected={index === active}
                {...still("answersDoNotTween")}
                className={
                  index === active
                    ? "nodefind__row nodefind__row--active"
                    : "nodefind__row"
                }
                onMouseDown={(event) => {
                  event.preventDefault();
                  pick(item);
                }}
                onMouseEnter={() => setActive(index)}
              >
                <span className="nodefind__label">{item.label || item.id}</span>
                <span className="nodefind__anchor">{item.id}</span>
              </li>
            ))
          ) : (
            <li className="nodefind__row nodefind__row--empty">
              no matches in this search
            </li>
          )}
        </ul>
      ) : null}
    </div>
  );
}

export function ReaderHeader({
  title,
  kind,
  meta,
  onClose,
}: {
  title: string;
  kind?: string;
  meta?: string;
  onClose?: () => void;
}) {
  return (
    <header className="world-reader__header">
      <div className="world-reader__heading">
        <h2>{title}</h2>
        {meta ? <p>{meta}</p> : null}
      </div>
      {kind ? <span className="node-reader__kind">{kind}</span> : null}
      {onClose ? <PanelClose onClose={onClose} /> : null}
    </header>
  );
}

export function Grounding({ assertion }: { assertion: WorldAssertion }) {
  const sources = assertion.grounding.filter((item) => item.kind === "SOURCE");
  const world = assertion.grounding.find((item) => item.kind === "WORLD");
  return (
    <>
      <h3>grounded by</h3>
      {sources.length ? (
        <ul className="world__grounding">
          {sources.map((item) => (
            <li key={item.reference}>
              <b>{item.native_handle}</b>
              <span>{item.native_location}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="world__note">No source grounding recorded.</p>
      )}
      {world?.construction_method ? (
        <p className="world__note">method · {world.construction_method}</p>
      ) : null}
    </>
  );
}

export function AssertionPanel({
  assertion,
  folding,
  onFold,
  onTable,
  onDerivation,
  onRemove,
  onClose,
}: {
  assertion: WorldAssertion | null;
  /** Which way this tuple's second drawing lies, or null if it has none. */
  folding: "open" | "collapse" | null;
  onFold: () => void;
  onTable: (relation: string) => void;
  onDerivation: (relation: string, assertion: string | null) => void;
  onRemove: () => void;
  onClose: () => void;
}) {
  if (!assertion) {
    return (
      <article className="world-reader__article">
        <ReaderHeader title="Reading assertion" onClose={onClose} />
        <div className="world-reader__content">
          <p className="world__hint">Loading its roles and grounding…</p>
        </div>
      </article>
    );
  }
  const state = conditionOf(
    assertion.relation_stale,
    assertion.completeness,
  ).replace(/^ · /, "");
  return (
    <article className="world-reader__article">
      <ReaderHeader
        title={assertion.relation}
        kind={assertion.origin.toLowerCase()}
        meta={`${assertion.mode.toLowerCase()} · revision ${assertion.created_revision}${state ? ` · ${state}` : ""}`}
        onClose={onClose}
      />
      <div className="world-reader__content">
        <ol className="world__roles">
          {assertion.roles.map((role) => (
            <li key={role.name}>
              <b>{role.name}</b>
              <span>{String(assertion.values[role.name] ?? "—")}</span>
            </li>
          ))}
        </ol>
        {assertion.derivation?.inputs?.length ? (
          <section className="world-reader__section">
            <h3>Rests on</h3>
            <ul className="world__inputs">
              {assertion.derivation.inputs.map((input) => (
                <li key={input}>{input}</li>
              ))}
            </ul>
          </section>
        ) : null}
        <section className="world-reader__section">
          <Grounding assertion={assertion} />
        </section>
      </div>
      <footer className="world-reader__actions">
        {folding ? (
          <button type="button" className="node-reader__link" onClick={onFold}>
            {folding === "open" ? "Open on the field" : "Fold onto the line"}
          </button>
        ) : null}
        <button
          type="button"
          className="node-reader__link"
          onClick={() =>
            onDerivation(assertion.relation, assertion.assertion_id)
          }
        >
          {assertion.mode === "DERIVED"
            ? "Why this tuple"
            : "What depends on this"}
        </button>
        <button
          type="button"
          className="node-reader__link"
          onClick={() => onTable(assertion.relation)}
        >
          Open extension
        </button>
        <button type="button" className="node-reader__link" onClick={onRemove}>
          Take off the field
        </button>
      </footer>
    </article>
  );
}

/**
 * §8.7, the unresolved inspector.
 *
 * The one thing this panel must never do is read as a denial. A missing
 * positive assertion is not a false one — the world has not been asked, or has
 * been asked and could not answer — so the state line says what is absent, the
 * evidence line says what is not recorded, and neither is dressed as a result.
 * §16: no write path, no action, no "resolve this" button. This product reads.
 */
export function DemandPanel({
  obligation,
  demand,
  roles,
  onTable,
  onRemove,
  onClose,
}: {
  obligation: Obligation | null;
  demand: WorldDemand | null;
  /** Role order, since an obligation's values are a JSON object. */
  roles: string[];
  onTable: (relation: string) => void;
  onRemove: () => void;
  onClose: () => void;
}) {
  if (!obligation) {
    return (
      <article className="world-reader__article">
        <ReaderHeader title="Reading obligation" onClose={onClose} />
        <div className="world-reader__content">
          <p className="world__hint">Loading the demanded tuple…</p>
        </div>
      </article>
    );
  }
  const by = obligation.demanded_by as { name?: string; revision?: number };
  return (
    <article className="world-reader__article">
      <ReaderHeader
        title={obligation.relation}
        kind={obligation.state.toLowerCase()}
        meta="Demanded tuple"
        onClose={onClose}
      />
      <div className="world-reader__content">
        <ol className="world__roles">
          {(roles.length ? roles : Object.keys(obligation.values)).map(
            (role) => (
              <li key={role}>
                <b>{role}</b>
                <span>{String(obligation.values[role] ?? "—")}</span>
              </li>
            ),
          )}
        </ol>
        <section className="world-reader__section">
          <h3>State</h3>
          <p className="world__note">
            {obligation.state === "UNRESOLVED"
              ? "No positive assertion. This world is silent about the tuple; it does not deny it."
              : "Asserted by this world."}
          </p>
        </section>
        <section className="world-reader__section">
          <h3>Demanded by</h3>
          <p className="world__note">
            {by.name ?? demand?.purpose.id}
            {by.revision ? ` · revision ${by.revision}` : ""}
          </p>
          {demand?.purpose.statement ? (
            <p className="world__note">{demand.purpose.statement}</p>
          ) : null}
        </section>
        {demand?.rule ? (
          <section className="world-reader__section">
            <h3>Why it exists</h3>
            <p className="world__note">{demand.rule}</p>
          </section>
        ) : null}
      </div>
      <footer className="world-reader__actions">
        <button
          type="button"
          className="node-reader__link"
          onClick={() => onTable(obligation.relation)}
        >
          Open extension
        </button>
        <button type="button" className="node-reader__link" onClick={onRemove}>
          Take off the field
        </button>
      </footer>
    </article>
  );
}

export function ReferentPanel({
  detail,
  set,
  requests,
  onExpand,
  onRetract,
  onTable,
  onDrop,
  onGather,
  onClose,
}: {
  detail: WorldReferent | null;
  set: WorkingSet;
  requests: ExpansionRequests;
  onExpand: (relation: string, count: number) => void;
  onRetract: (relation: string) => void;
  onTable: (relation: string) => void;
  onDrop: () => void;
  /** Null when nothing on the field is joined to this referent yet. */
  onGather: (() => void) | null;
  onClose: () => void;
}) {
  if (!detail) {
    return (
      <article className="world-reader__article">
        <ReaderHeader title="Reading referent" onClose={onClose} />
        <div className="world-reader__content">
          <p className="world__hint">Loading fields and possible expansions…</p>
        </div>
      </article>
    );
  }
  const room = MAX_FIELD_NODES - fieldSize(set);
  return (
    <article className="world-reader__article">
      <ReaderHeader
        title={detail.label || detail.id}
        kind={detail.id.split(":", 1)[0]}
        meta={detail.id}
        onClose={onClose}
      />
      <div className="world-reader__content">
        {detail.fields.length ? (
          <ol className="world__roles">
            {detail.fields.map((field) => (
              <li key={field.assertion_id}>
                <b>{field.relation}</b>
                <span>{String(field.value)}</span>
              </li>
            ))}
          </ol>
        ) : null}
        <section className="world-reader__section world-reader__section--list">
          <h3>Expand through</h3>
          <ul className="gm__list">
            {detail.relations.map((relation) => {
              const key = expansionKey(detail.id, relation.name);
              const state = expansionViewState({
                set,
                referentId: detail.id,
                relation: relation.name,
                count: relation.count,
                room,
                request: requests.get(key),
              });
              const already = state.value === "on-field";
              const loading = state.value === "loading";
              const tooMany = state.value === "table";
              return (
                <li key={relation.name}>
                  <button
                    type="button"
                    className={already ? "is-selected" : undefined}
                    disabled={loading}
                    aria-busy={loading || undefined}
                    data-table={tooMany ? true : undefined}
                    onClick={() =>
                      already
                        ? onRetract(relation.name)
                        : tooMany
                        ? onTable(relation.name)
                        : onExpand(relation.name, relation.count)
                    }
                  >
                    <span className="gm__list-name">{relation.name}</span>
                    <span className="gm__list-meta">
                      {already
                        ? "take off"
                        : loading
                          ? "loading"
                          : tooMany
                            ? `${relation.count} · table`
                            : state.value === "failed"
                              ? "retry"
                              : relation.count}
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        </section>
      </div>
      <footer className="world-reader__actions">
        {onGather ? (
          <button type="button" className="node-reader__link" onClick={onGather}>
            Gather its neighbours
          </button>
        ) : null}
        <button type="button" className="node-reader__link" onClick={onDrop}>
          Take off the field
        </button>
      </footer>
    </article>
  );
}

const READER_WIDTH_KEY = "graphauthor.worldReaderWidth";
const TABLES_WIDTH_KEY = "graphauthor.worldFrontierWidth";

type TableView =
  | { kind: "world" }
  | { kind: "frontier" }
  | {
      kind: "relation";
      relation: string;
      subject: { id: string; label: string } | null;
    }
  | { kind: "derivation"; relation: string; assertion: string | null };

/** A seam from construction's vocabulary card to this relation's extension.
 * Hash routing owns the path, so its query lives in the hash as well. */
function linkedRelationFromHash(): string | null {
  const hash = window.location.hash;
  const query = hash.includes("?") ? hash.slice(hash.indexOf("?") + 1) : "";
  return new URLSearchParams(query).get("relation");
}

/**
 * Optional instruments for a full-system lab.
 *
 * The page still owns all World data and interaction state. The lab is only
 * allowed to tune how the real canvas expresses that state, which prevents a
 * fixture sandbox from becoming a second, less capable World application.
 */
export type WorldPageTuning = {
  params?: MarkParams;
  ants?: Partial<AntTuning>;
  motion?: MotionPlans;
  material?: Partial<MaterialTuning>;
  selectionTreatment?: SelectionTreatment;
  light?: Partial<LightField>;
};

export type WorldPageProps = {
  tuning?: WorldPageTuning;
  /** Replaces the recursive LAB link with a way back to the product surface. */
  lab?: boolean;
  /** The lab controls appearance outside the page so its instruments agree. */
  mode?: ThemeMode;
  onModeChange?: (mode: ThemeMode) => void;
};

export function WorldPage({
  tuning,
  lab = false,
  mode: controlledMode,
  onModeChange,
}: WorldPageProps = {}) {
  const motion = tuning?.motion ?? DEFAULT_MOTION_PLANS;
  const [localMode, setLocalMode] = useState<ThemeMode>(readStoredWorldTheme);
  const mode = controlledMode ?? localMode;
  const [motionReady, setMotionReady] = useState(false);
  const [overview, setOverview] = useState<WorldOverview | null>(null);
  const [relations, setRelations] = useState<WorldRelation[]>([]);
  const [directory, setDirectory] = useState<Directory>([]);
  const [error, setError] = useState<string | null>(null);

  const [set, setSet] = useState<WorkingSet>(emptySet);
  /**
   * What the last arrangement displaced, so it can be put back.
   *
   * One level, and only until the field itself changes. Arrangement is the one
   * action that overwrites placement a person may have made by hand, so it does
   * not get to be silent; but once matter has arrived or left, the positions it
   * displaced are no longer a state the field was ever in, and offering to
   * restore them would be offering a lie.
   */
  const [arrangeUndo, setArrangeUndo] = useState<{
    label: string;
    positions: Map<string, Point>;
  } | null>(null);
  const [arrangeToken, setArrangeToken] = useState(0);
  const [expansionRequests, dispatchExpansion] = useReducer(
    expansionRequestReducer,
    new Map(),
  );
  const [selection, setSelection] = useState<CanvasSelection>(null);
  const [hovered, setHovered] = useState<string | null>(null);
  const [hoveredRelation, setHoveredRelation] = useState<string | null>(null);
  const [focusedRelation, setFocusedRelation] = useState<string | null>(null);
  const [namedAtRest, setNamedAtRest] = useState(false);
  const [show, setShow] = useState<ShowState>(SHOW_DEFAULT);
  const [readerOpen, setReaderOpen] = useState(false);
  const [readerWidth, setReaderWidth] = useState(() =>
    readStoredPanelSize(READER_WIDTH_KEY, 320),
  );
  const [tablesOpen, setTablesOpen] = useState(false);
  const [tablesWidth, setTablesWidth] = useState(() =>
    readStoredPanelSize(TABLES_WIDTH_KEY, TABLES_WIDTH_DEFAULT),
  );
  const [assertion, setAssertion] = useState<WorldAssertion | null>(null);
  const [referent, setReferent] = useState<WorldReferent | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  /**
   * What is open on the left overlay. World is the idle catalogue; frontier
   * and a relation are subjects you switch to. Closing the handle parks it;
   * opening it again is the same reading.
   */
  const [table, setTable] = useState<TableView>({ kind: "world" });
  const [demand, setDemand] = useState<WorldDemand | null>(null);
  const [demandProblem, setDemandProblem] = useState<string | null>(null);
  /**
   * Vocabulary as a focus room: the field stays, parked, until Clear.
   *
   * Emptying the working set was a one-way trip. This is the product's focus
   * mode used for a different subject — the schema rather than a lit node —
   * so the neighborhood is still there when you come back.
   */
  const [vocabularyFocus, setVocabularyFocus] = useState(false);
  /**
   * What is *drawn*, which lags the intent by one absorb.
   *
   * Vocabulary focus inverts the whole surface, so the field and the
   * vocabulary have no shared ground to cross over — see `useSequencedSwap`.
   * `vocabularyFocus` stays the thing a person asked for; `focusView.value` is
   * what is on screen, and every visual read below uses it.
   */
  const focusView = useSequencedSwap(vocabularyFocus, motion);
  const focusDrawn = focusView.value;
  /**
   * A mark a table named, distinct from canvas selection.
   *
   * Clicking the field already has the mark under the pointer. A row does not,
   * and the same row clicked twice still has to fly — so the token changes even
   * when the id does not.
   */
  const [focus, setFocus] = useState<{ id: string; token: number } | null>(
    null,
  );
  const revealMark = useCallback((id: string) => {
    setFocus({ id, token: performance.now() });
  }, []);

  const labels = useRef(new Map<string, string | null>());
  const linkedRelation = useRef(linkedRelationFromHash());
  /**
   * Whether the stored field has been looked for yet.
   *
   * The world arrives one render after the page does, so there is a window in
   * which the field is legitimately empty and not yet known to be. Writing
   * during it would store that emptiness over the field someone left behind —
   * so nothing is written until the restore has been attempted.
   */
  const restored = useRef(false);
  /** Synchronous duplicate guard; reducer state becomes visible next render. */
  const expansionsInFlight = useRef(new Map<string, number>());
  /** Invalidates a response that lands after its field has been cleared. */
  const expansionGeneration = useRef(0);
  /** A selected mark stays present while its ants collapse into it. */
  const pendingRemovals = useRef(new Map<string, number>());

  useEffect(
    () => () => {
      for (const timer of pendingRemovals.current.values()) {
        window.clearTimeout(timer);
      }
      pendingRemovals.current.clear();
    },
    [],
  );

  useEffect(() => {
    const frame = requestAnimationFrame(() => setMotionReady(true));
    return () => cancelAnimationFrame(frame);
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem("graphauthor.productTheme", mode);
    } catch {
      /* private mode */
    }
  }, [mode]);

  /**
   * Put back the field this browser last held for this world.
   *
   * Only onto an empty canvas, and only once: someone who arrived through a
   * link and has already started building keeps what they built. A revision
   * this browser has no field for restores nothing, which is the intended
   * answer after a rebuild.
   */
  useEffect(() => {
    if (!overview || restored.current) return;
    restored.current = true;
    const stored = readField(overview.world_id, overview.revision);
    if (stored) setSet((current) => (fieldSize(current) ? current : stored));
  }, [overview]);

  /** Keep the stored field level with the one on screen. */
  useEffect(() => {
    if (!overview || !restored.current) return;
    writeField(overview.world_id, overview.revision, set);
  }, [overview, set]);

  const onReaderWidth = useCallback((width: number) => {
    setReaderWidth(width);
    storePanelSize(READER_WIDTH_KEY, width);
  }, []);

  const showTable = useCallback((view: TableView) => {
    setTable(view);
    setTablesOpen(true);
  }, []);

  const collapseTables = useCallback(() => {
    setTablesOpen(false);
  }, []);

  const onTablesWidth = useCallback((width: number) => {
    setTablesWidth(width);
    storePanelSize(TABLES_WIDTH_KEY, width);
  }, []);

  const tableChrome = useMemo<TableChrome>(
    () => ({
      current:
        table.kind === "world" || table.kind === "frontier"
          ? table.kind
          : "other",
      hasFrontier: Boolean(overview?.demand),
      onWorld: () => showTable({ kind: "world" }),
      onFrontier: () => showTable({ kind: "frontier" }),
      onClose: collapseTables,
    }),
    [collapseTables, overview?.demand, showTable, table.kind],
  );

  useEffect(() => {
    let cancelled = false;
    Promise.all([worldApi.overview(), worldApi.schema(), worldApi.referents()])
      .then(([summary, schema, all]) => {
        if (cancelled) return;
        setOverview(summary);
        setRelations(schema);
        setDirectory(all);
        labels.current = new Map(all.map((item) => [item.id, item.label]));
      })
      .catch((problem: Error) => {
        if (!cancelled) setError(problem.message);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const name = linkedRelation.current;
    if (!name || !relations.length) return;
    linkedRelation.current = null;
    if (!relations.some((relation) => relation.name === name)) {
      // The notice lives inside the reader, and this effect runs on arrival
      // with the reader shut — so the miss has to open it or the seam fails
      // silently. A link from construction naming a relation this world does
      // not have is the normal case when the run and the world are different
      // domains, not an edge one.
      setNotice(`${name} is not in this world's vocabulary.`);
      setReaderOpen(true);
      return;
    }
    setFocusedRelation(name);
    setReaderOpen(true);
    setTable({ kind: "relation", relation: name, subject: null });
    setTablesOpen(true);
  }, [relations]);

  // Selection drives one fetch, and only one: a chip reads its assertion, a
  // disc reads its neighborhood costs.
  useEffect(() => {
    setNotice(null);
    if (!selection) {
      setAssertion(null);
      setReferent(null);
      return;
    }
    if (selection.kind === "demand") {
      // Nothing to read: an obligation is not in the world, so there is no
      // record of it to fetch. The frontier document already holds it.
      setAssertion(null);
      setReferent(null);
      return;
    }
    let cancelled = false;
    if (selection.kind === "assertion") {
      setAssertion(null);
      worldApi
        .assertion(selection.id)
        .then((found) => !cancelled && setAssertion(found))
        .catch((problem: Error) => !cancelled && setNotice(problem.message));
    } else {
      setReferent(null);
      worldApi
        .referent(selection.id)
        .then((found) => !cancelled && setReferent(found))
        .catch((problem: Error) => !cancelled && setNotice(problem.message));
    }
    return () => {
      cancelled = true;
    };
  }, [selection]);

  const chooseFieldMark = useCallback((next: CanvasSelection) => {
    setSelection(next);
    setReaderOpen(Boolean(next));
  }, []);

  const chooseSchemaRelation = useCallback((name: string | null) => {
    setFocusedRelation(name);
    setReaderOpen(Boolean(name));
  }, []);

  const onSeed = useCallback((id: string, label: string) => {
    setSet((current) => seed(current, id, label));
    chooseFieldMark({ kind: "referent", id });
    revealMark(id);
  }, [chooseFieldMark, revealMark]);

  // Canvas find operates on the visible working field. An empty field still
  // needs a seed; only that initial search uses the world's directory.
  const fieldDirectory = useMemo<Directory>(() => [
    ...Array.from(set.referents.values(), ({ id, label }) => ({ id, label })),
    ...Array.from(set.assertions.values())
      .filter((item) => assertionShown(item.origin, item.mode, show))
      .map((item) => ({ id: item.assertion_id, label: item.relation })),
    ...set.bonds
      .filter((item) => set.referents.has(item.source) &&
        set.referents.has(item.target) && assertionShown(item.origin, item.mode, show))
      .map((item) => ({ id: item.assertion_id, label: item.relation })),
    ...(show.unresolved
      ? Array.from(set.demands.values(), (item) => ({ id: item.key, label: item.relation }))
      : []),
  ], [set, show]);

  const onFind = useCallback((id: string, label: string) => {
    if (!set.referents.size && !set.assertions.size && !set.demands.size && !set.bonds.length) {
      onSeed(id, label);
      return;
    }
    chooseFieldMark({
      kind: set.referents.has(id) ? "referent" : set.demands.has(id) ? "demand" : "assertion",
      id,
    });
    revealMark(id);
  }, [onSeed, chooseFieldMark, revealMark, set]);

  const onExpand = useCallback(
    async (relation: string, count: number) => {
      if (!selection || selection.kind !== "referent") return;
      const anchor = selection.id;
      const key = expansionKey(anchor, relation);
      if (expansionsInFlight.current.has(key)) return;
      if (count > MAX_FIELD_NODES - fieldSize(set)) {
        setNotice(`${relation} has ${count} tuples — more than the field holds.`);
        return;
      }
      const schema = relations.find((item) => item.name === relation);
      const generation = expansionGeneration.current;
      expansionsInFlight.current.set(key, generation);
      dispatchExpansion({ type: "start", key });
      try {
        const expansion = await worldApi.expand(anchor, relation);
        if (generation !== expansionGeneration.current) return;
        if (schema) setShow((current) => reveal(schema, current));
        setSet((current) =>
          current.referents.has(anchor)
            ? expand(current, {
                anchor,
                relation,
                mode: schema?.mode ?? "BASE",
                stale: schema?.stale ?? false,
                completeness: schema?.completeness?.status ?? null,
                roles: expansion.roles,
                tuples: expansion.tuples,
                labels: labels.current,
              })
            : current,
        );
        dispatchExpansion({ type: "succeed", key });
      } catch (problem) {
        if (generation === expansionGeneration.current) {
          const message = (problem as Error).message;
          setNotice(message);
          dispatchExpansion({ type: "fail", key, message });
        }
      } finally {
        if (expansionsInFlight.current.get(key) === generation) {
          expansionsInFlight.current.delete(key);
        }
      }
    },
    [relations, selection, set],
  );

  const onRetract = useCallback(
    (relation: string) => {
      if (!selection || selection.kind !== "referent") return;
      setSet((current) => retractExpansion(current, selection.id, relation));
    },
    [selection],
  );

  const onPositions = useCallback((positions: Map<string, { x: number; y: number }>) => {
    setSet((current) => ({ ...current, positions: new Map([...current.positions, ...positions]) }));
  }, []);

  /**
   * A row focuses its graph projection (§11).
   *
   * The tuple lands beside whichever of its referents is already on the field,
   * and the assertion it belongs to becomes the selection — so picking a row
   * out of a ten-thousand-row extension answers *where does this sit* on the
   * canvas and *what is it made of* in the panel at once. From the vocabulary
   * this is also how a field starts: the first row placed seeds it.
   */
  /**
   * A row, onto the field. The seam of §11, and it is the same seam wherever
   * the row came from — an extension, or an input tuple offered as candidate
   * support for a derived one — so the relation is passed rather than read off
   * whichever table happens to be open.
   */
  const placeTuple = useCallback(
    (relation: string, roles: WorldRole[], tuple: WorldTuple) => {
      const schema = relations.find((item) => item.name === relation);
      if (schema) setShow((current) => reveal(schema, current));
      setSet((current) =>
        place(current, {
          relation,
          mode: schema?.mode ?? "BASE",
          stale: schema?.stale ?? false,
          completeness: schema?.completeness?.status ?? null,
          roles,
          tuple,
          labels: labels.current,
        }),
      );
      chooseFieldMark({ kind: "assertion", id: tuple.assertion_id });
      revealMark(tuple.assertion_id);
    },
    [chooseFieldMark, relations, revealMark],
  );

  const onFocusRow = useCallback((roles: WorldRole[], tuple: WorldTuple) => {
    if (table?.kind !== "relation") return;
    placeTuple(table.relation, roles, tuple);
  }, [placeTuple, table]);

  /**
   * The obligation set, read once and only when it is asked for.
   *
   * Not part of the opening fetch: resolving every obligation against the world
   * is work nobody has asked for until they open the frontier, and the overview
   * already carries the counts the vocabulary panel prints.
   */
  useEffect(() => {
    if (table?.kind !== "frontier" || demand) return;
    let cancelled = false;
    worldApi
      .demand()
      .then((found) => !cancelled && setDemand(found))
      .catch((problem: Error) => !cancelled && setDemandProblem(problem.message));
    return () => {
      cancelled = true;
    };
  }, [demand, table]);

  /** Obligations by the key the field knows them under. */
  const obligations = useMemo(() => {
    const out = new Map<string, Obligation>();
    (demand?.obligations ?? []).forEach((obligation, index) =>
      out.set(`demand#${index}`, { ...obligation, key: `demand#${index}` }),
    );
    return out;
  }, [demand]);

  /**
   * An obligation is put on the field (§8.7).
   *
   * Unresolved, it lands as a hollow chip: there is no assertion to read, so
   * the mark *is* the obligation. Resolved, it is an ordinary assertion and is
   * drawn as one — the frontier's own record of it is a claim about what a
   * purpose wanted, not a second kind of tuple — so the assertion is read and
   * placed exactly as a table row would place it.
   */
  const onFocusObligation = useCallback(
    async (obligation: Obligation) => {
      const schema = relations.find((item) => item.name === obligation.relation);
      if (!schema) {
        setNotice(`${obligation.relation} is not in this world's vocabulary.`);
        return;
      }
      if (obligation.state === "ASSERTED" && obligation.assertion_id) {
        try {
          const found = await worldApi.assertion(obligation.assertion_id);
          setShow((current) => reveal(schema, current));
          setSet((current) =>
            place(current, {
              relation: found.relation,
              mode: found.mode,
              stale: found.relation_stale,
              completeness: found.completeness?.status ?? null,
              roles: found.roles,
              tuple: {
                assertion_id: obligation.assertion_id as string,
                origin: found.origin,
                values: found.values,
              },
              labels: labels.current,
            }),
          );
          chooseFieldMark({
            kind: "assertion",
            id: obligation.assertion_id,
          });
          revealMark(obligation.assertion_id);
        } catch (problem) {
          setNotice((problem as Error).message);
        }
        return;
      }
      setShow((current) => ({ ...current, unresolved: true }));
      setSet((current) =>
        placeDemand(current, {
          key: obligation.key,
          relation: obligation.relation,
          roles: schema.roles,
          values: obligation.values,
          labels: labels.current,
        }),
      );
      chooseFieldMark({ kind: "demand", id: obligation.key });
      revealMark(obligation.key);
    },
    [chooseFieldMark, relations, revealMark],
  );

  /** What is already on the field, so a row can say so — see §11. */
  const present = useMemo(() => {
    const ids = new Set<string>(set.assertions.keys());
    for (const bond of set.bonds) ids.add(bond.assertion_id);
    for (const key of set.demands.keys()) ids.add(key);
    return ids;
  }, [set]);

  /**
   * Whether the open assertion has a second drawing, and which way.
   *
   * Asked of the field rather than of the tuple: the same assertion is
   * foldable when it is standing on the field and nothing at all when it is
   * only a row in a table, because there is no line to open.
   */
  const folding = useMemo(
    () =>
      selection?.kind === "assertion" ? foldingOf(set, selection.id) : null,
    [selection, set],
  );

  /**
   * Redraw one tuple in its other form.
   *
   * No refetch and no re-layout: both forms are already on the field, and the
   * plate lands on the line's own midpoint. The reader does not change either
   * — it was showing the tuple's roles all along, which is the argument for
   * the feature: opening puts on the field what the panel already knew.
   */
  const onFold = useCallback(() => {
    if (!selection || selection.kind !== "assertion") return;
    const id = selection.id;
    setSet((current) =>
      foldingOf(current, id) === "open" ? openBond(current, id) : collapse(current, id),
    );
  }, [selection]);

  const removeMark = useCallback(
    (mark: NonNullable<CanvasSelection>) => {
      if (pendingRemovals.current.has(mark.id)) return;
      if (mark.kind === "referent") {
        expansionGeneration.current += 1;
        expansionsInFlight.current.clear();
        dispatchExpansion({ type: "reset" });
      }
      const finish = () => {
        pendingRemovals.current.delete(mark.id);
        setSet((current) => dropMark(current, mark.id));
      };
      const reduced = window.matchMedia(
        "(prefers-reduced-motion: reduce)",
      ).matches;
      const wasSelected = selection?.id === mark.id;
      if (reduced) {
        setSelection((current) => (current?.id === mark.id ? null : current));
        setReaderOpen((open) => (wasSelected ? false : open));
        finish();
        return;
      }

      const collapseRing = () => {
        // First the fast ring contracts. Only after it has handed the outline
        // back does the slower node mass begin its own absorption in G6.
        setSelection((current) => (current?.id === mark.id ? null : current));
        const timer = window.setTimeout(
          finish,
          motion.absorb.durationMs,
        );
        pendingRemovals.current.set(mark.id, timer);
      };

      if (wasSelected) {
        setReaderOpen(false);
        collapseRing();
        return;
      }

      // A direct right-click may not have selected the node first. Give it a
      // ring long enough to resolve, then run the same ring → mass sequence;
      // otherwise only previously selected nodes would get the stated death.
      setSelection(mark);
      const timer = window.setTimeout(
        collapseRing,
        motion.emit.durationMs,
      );
      pendingRemovals.current.set(mark.id, timer);
    },
    [motion.absorb.durationMs, motion.emit.durationMs, selection],
  );

  const onRemove = useCallback(() => {
    if (!selection) return;
    removeMark(selection);
  }, [removeMark, selection]);

  /**
   * Arrangement: the two ways a person may re-place matter already standing.
   *
   * Both suspend `existing marks never move`, so both are things someone
   * clicked, both record what they displaced, and neither happens on its own.
   * `arrangeToken` is what tells the canvas this frame is the exception, so
   * the marks that move do it with `settle` — a body finding a new rest —
   * rather than the pointer-direct `hold` every other standing update uses.
   */
  const applyArrange = useCallback(
    (request: Arrangement, label: string) => {
      const next = arrange(set, request);
      if (next === set) return;
      const displaced = new Map<string, Point>();
      for (const [id, was] of set.positions) {
        const now = next.positions.get(id);
        if (now && (now.x !== was.x || now.y !== was.y)) displaced.set(id, was);
      }
      if (!displaced.size) return;
      setArrangeUndo({ label, positions: displaced });
      setArrangeToken((token) => token + 1);
      setSet(next);
    },
    [set],
  );

  const fieldNeighbours = useMemo(() => fieldGraph(set), [set]);
  const canGather = useCallback(
    (id: string) => Boolean(fieldNeighbours.get(id)?.size),
    [fieldNeighbours],
  );
  const onGather = useCallback(
    (id: string) => applyArrange({ kind: "gather", subject: id }, "gather"),
    [applyArrange],
  );
  const onSeparate = useCallback(
    () => applyArrange({ kind: "separate" }, "separate"),
    [applyArrange],
  );
  const onUndoArrange = useCallback(() => {
    if (!arrangeUndo) return;
    const restore = arrangeUndo.positions;
    setArrangeToken((token) => token + 1);
    setSet((current) => ({
      ...current,
      positions: new Map([...current.positions, ...restore]),
    }));
    setArrangeUndo(null);
  }, [arrangeUndo]);

  /**
   * An undo survives only while the field it belongs to does.
   *
   * Keyed on membership rather than on positions, because an arrangement
   * changes positions and must not clear its own undo the moment it lands.
   */
  const fieldMembership = `${set.referents.size}:${set.assertions.size}:${set.demands.size}:${set.bonds.length}`;
  useEffect(() => {
    setArrangeUndo(null);
  }, [fieldMembership]);

  const clearField = useCallback(() => {
    for (const timer of pendingRemovals.current.values()) {
      window.clearTimeout(timer);
    }
    pendingRemovals.current.clear();
    expansionGeneration.current += 1;
    expansionsInFlight.current.clear();
    dispatchExpansion({ type: "reset" });
    setSet(emptySet());
    setSelection(null);
    setHovered(null);
    setReaderOpen(false);
  }, []);

  const enterVocabulary = useCallback(() => {
    setVocabularyFocus(true);
    setReaderOpen(false);
  }, []);

  const leaveVocabulary = useCallback(() => {
    setVocabularyFocus(false);
    setReaderOpen(Boolean(selection));
  }, [selection]);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape" && vocabularyFocus) {
        event.preventDefault();
        leaveVocabulary();
        return;
      }
      if (event.key !== "Backspace" && event.key !== "Delete") return;
      const target = event.target as HTMLElement | null;
      if (target?.closest("input, textarea, [contenteditable='true']")) return;
      if (!selection || vocabularyFocus) return;
      event.preventDefault();
      onRemove();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [leaveVocabulary, onRemove, selection, vocabularyFocus]);

  const visibleRelations = useMemo(
    () => relations.filter((item) => relationShown(item, show)),
    [relations, show],
  );
  /**
   * Chrome, matter, focus and the motion spine, on the one element everything
   * below inherits from. `worldChrome.ts` owns the composition so the design
   * lab emits exactly the same tokens.
   */
  const style = {
    ...worldShellStyle(mode, { focus: focusDrawn, motion }),
    ...worldChromeDockVars({ tablesWidth, readerWidth }),
  };
  const onField = fieldSize(set) > 0;
  const relation = relations.find((item) => item.name === focusedRelation) ?? null;
  /**
   * The reader's subject, as one token.
   *
   * A subject change while the dock is already out is a REPLACED, not an
   * arrival: the column stays where it is and its contents are exchanged. The
   * token is what `Swap` compares, so it has to name the *subject* rather than
   * the panel — two referents in a row are two subjects through one panel.
   */
  const readerSubject = onField && selection
    ? `${selection.kind}:${selection.id}`
    : relation
      ? `relation:${relation.name}`
      : "reader:empty";
  /**
   * The notice is a thing that arrives and leaves, so it does both.
   *
   * `useHeld` keeps the text while the absorb runs — without it the strip
   * empties on the frame it is told to go, and what you see is a blank bar
   * fading rather than the message leaving.
   */
  const noticePresence = usePresence(Boolean(notice));
  const noticeHeld = useHeld(notice, noticePresence.mounted);
  const activeRelation = hoveredRelation ?? focusedRelation;
  const extension =
    table?.kind === "relation"
      ? relations.find((item) => item.name === table.relation) ?? null
      : null;
  /** The same, for the TABLES dock. A derivation is keyed by what it is of. */
  const tableSubject =
    table.kind === "relation"
      ? `relation:${table.relation}`
      : table.kind === "derivation"
        ? `derivation:${table.relation}\u0000${table.assertion ?? ""}`
        : table.kind;
  const cameraInsets = useMemo<CameraInsets>(
    () =>
      worldCameraInsets({
        focus: focusDrawn,
        tablesOpen,
        tablesWidth,
        readerOpen,
        readerWidth,
      }),
    [
      readerOpen,
      readerWidth,
      tablesOpen,
      tablesWidth,
      focusDrawn,
    ],
  );

  return (
    <main
      className={`product-shell world${mode === "dark" ? " is-dark" : ""}${focusDrawn ? " is-focus" : ""}${motionReady ? " is-motion-ready" : ""}`}
      style={style}
      data-mode={mode}
    >
      <header className={chromeClass("product-shell__top")}>
        <div className="product-shell__bar">
          <span className="product-shell__workspace">
            {overview?.world_id ?? "world"}
          </span>
          <span className="product-shell__local">
            {overview ? `rev ${overview.revision}` : ""}
          </span>
          {onField ? (
            <button
              type="button"
              className="product-shell__local world__occupancy"
              title="Clear the field"
              aria-label={`Clear field, ${fieldSize(set)} of ${MAX_FIELD_NODES} on field`}
              onClick={clearField}
            >
              <span className="world__occupancy-count">
                {fieldSize(set)}/{MAX_FIELD_NODES} on field
              </span>
              <span className="world__occupancy-clear" aria-hidden="true">
                clear
              </span>
            </button>
          ) : null}
          <div className="product-shell__utils">
            <a
              href={lab ? "#/world" : "#/world-lab"}
              className="product-shell__lab-link"
              title={lab ? "Open World" : "Open World Design & Motion Lab"}
            >
              {lab ? "WORLD" : "LAB"}
            </a>
            <button
              type="button"
              className="product-shell__theme"
              onClick={() => {
                const next = mode === "light" ? "dark" : "light";
                if (onModeChange) onModeChange(next);
                else setLocalMode(next);
              }}
              aria-label={`Use ${mode === "light" ? "dark" : "light"} appearance`}
            >
              {mode === "light" ? "dark" : "light"}
            </button>
          </div>
        </div>
      </header>

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
                onWidthChange={onTablesWidth}
                minWidth={280}
                maxWidth={640}
                reserve={focusDrawn ? 0 : readerOpen ? readerWidth : 0}
                flush
              >
                <Swap id={tableSubject} className="motion-swap--fill">
                  {table.kind === "world" ? (
                    <WorldTable
                      overview={overview}
                      relations={relations}
                      chrome={tableChrome}
                      onOpen={(name) => {
                        const schema = relations.find(
                          (item) => item.name === name,
                        );
                        if (schema) setShow((current) => reveal(schema, current));
                        setFocusedRelation(name);
                        revealMark(name);
                        showTable({
                          kind: "relation",
                          relation: name,
                          subject: null,
                        });
                      }}
                    />
                  ) : table.kind === "frontier" ? (
                    <FrontierTable
                      demand={demand}
                      relations={relations}
                      problem={demandProblem}
                      present={present}
                      chrome={tableChrome}
                      onFocus={onFocusObligation}
                    />
                  ) : extension && table.kind === "relation" ? (
                    <RelationTable
                      key={extension.name}
                      relation={extension}
                      subject={table.subject}
                      present={present}
                      onFocus={onFocusRow}
                      onWiden={() =>
                        showTable({
                          kind: "relation",
                          relation: extension.name,
                          subject: null,
                        })
                      }
                      onDerivation={() =>
                        showTable({
                          kind: "derivation",
                          relation: extension.name,
                          assertion: null,
                        })
                      }
                      chrome={tableChrome}
                    />
                  ) : table.kind === "derivation" ? (
                    <DerivationView
                      key={`${table.relation}\u0000${table.assertion ?? ""}`}
                      relation={table.relation}
                      assertionId={table.assertion}
                      present={present}
                      onOpen={(name) =>
                        showTable({
                          kind: "derivation",
                          relation: name,
                          assertion: null,
                        })
                      }
                      onTable={(name) =>
                        showTable({
                          kind: "relation",
                          relation: name,
                          subject: null,
                        })
                      }
                      onFocus={placeTuple}
                      chrome={tableChrome}
                    />
                  ) : null}
                </Swap>
              </OverlayPanel>
              {/* The plane is the slot the two views share. It absorbs the
                  one that is leaving, the palette flips while it is dark, and
                  it emits the one that arrives — `useSequencedSwap`. */}
              <div
                className={`gm__stage world__plane motion-layer motion-layer--fade${
                  focusView.shown ? " is-in" : ""
                }`}
              >
                {error ? (
                  <p className="world__error">
                    {error} — is the read plane running?{" "}
                    <code>
                      uv run --extra all python scripts/run_world_explorer.py
                    </code>
                  </p>
                ) : (
                  <>
                    {onField ? (
                      <div
                        className={`world__layer${focusDrawn ? " is-parked" : ""}`}
                      >
                        <WorldCanvas
                          set={set}
                          mode={mode}
                          params={tuning?.params ?? MARK_DEFAULTS}
                          hovered={hovered}
                          selection={selection}
                          show={show}
                          focusId={focus?.id ?? null}
                          focusToken={focus?.token ?? 0}
                          arrangeToken={arrangeToken}
                          animateInitial={Boolean(selection)}
                          insets={cameraInsets}
                          ants={tuning?.ants}
                          motion={motion}
                          material={tuning?.material}
                          selectionTreatment={tuning?.selectionTreatment}
                          light={tuning?.light}
                          onHover={setHovered}
                          onSelect={chooseFieldMark}
                          onPositions={onPositions}
                          onRemove={removeMark}
                        />
                      </div>
                    ) : null}
                    {/* Both canvases stay mounted, and the one that is not in
                        view is parked rather than unmounted. Unmounting it
                        destroyed a G6 graph on every focus toggle, which
                        raced its own in-flight draw ("the graph instance has
                        been destroyed") and meant the vocabulary had to be
                        rebuilt before it could be shown — during the gap the
                        swap leaves for exactly that. A vocabulary is bounded
                        by the world's relations, not its field, so the
                        second graph is cheap to simply keep. */}
                    <div
                      className={`world__layer${
                        onField && !focusDrawn ? " is-parked" : ""
                      }`}
                    >
                        <SchemaCanvas
                          relations={visibleRelations}
                          mode={mode}
                          namedAtRest={namedAtRest}
                          inverted={focusDrawn}
                          active={activeRelation}
                          selected={focusedRelation}
                          focusId={focus?.id ?? null}
                          focusToken={focus?.token ?? 0}
                          insets={cameraInsets}
                          onHover={setHoveredRelation}
                          onSelect={chooseSchemaRelation}
                        />
                    </div>
                  </>
                )}
              </div>

            <OverlayPanel
              id="world-reader"
              side="right"
              title="World reader"
              open={readerOpen}
              onToggle={setReaderOpen}
              handle={false}
              width={readerWidth}
              onWidthChange={onReaderWidth}
              reserve={
                focusDrawn
                  ? 0
                  : tablesOpen
                    ? tablesWidth
                    : TABLES_HANDLE_RESERVE
              }
              flush
            >
              <div className="node-reader">
                {noticePresence.mounted ? (
                  <p
                    className={`world__notice motion-layer motion-layer--rise${
                      noticePresence.shown ? " is-in" : ""
                    }`}
                  >
                    {noticeHeld}
                  </p>
                ) : null}
                <Swap id={readerSubject} className="motion-swap--fill">
                  {onField && selection?.kind === "demand" ? (
                    <DemandPanel
                      obligation={obligations.get(selection.id) ?? null}
                      demand={demand}
                      roles={
                        relations
                          .find(
                            (item) =>
                              item.name ===
                              obligations.get(selection.id)?.relation,
                          )
                          ?.roles.map((role) => role.name) ?? []
                      }
                      onTable={(name) =>
                        showTable({
                          kind: "relation",
                          relation: name,
                          subject: null,
                        })
                      }
                      onRemove={onRemove}
                      onClose={() => setReaderOpen(false)}
                    />
                  ) : onField && selection?.kind === "assertion" ? (
                    <AssertionPanel
                      assertion={assertion}
                      folding={folding}
                      onFold={onFold}
                      onTable={(name) =>
                        showTable({
                          kind: "relation",
                          relation: name,
                          subject: null,
                        })
                      }
                      onDerivation={(name, id) =>
                        showTable({
                          kind: "derivation",
                          relation: name,
                          assertion: id,
                        })
                      }
                      onRemove={onRemove}
                      onClose={() => setReaderOpen(false)}
                    />
                  ) : onField && selection?.kind === "referent" ? (
                    <ReferentPanel
                      detail={referent}
                      set={set}
                      requests={expansionRequests}
                      onExpand={onExpand}
                      onRetract={onRetract}
                      onTable={(name) =>
                        showTable({
                          kind: "relation",
                          relation: name,
                          subject: referent
                            ? {
                                id: referent.id,
                                label: referent.label || referent.id,
                              }
                            : null,
                        })
                      }
                      onDrop={onRemove}
                      onGather={
                        selection && canGather(selection.id)
                          ? () => onGather(selection.id)
                          : null
                      }
                      onClose={() => setReaderOpen(false)}
                    />
                  ) : relation ? (
                    <article className="world-reader__article">
                      <ReaderHeader
                        title={relation.name}
                        kind={
                          // A relation the machine built reads by its mode; one
                          // someone decided reads by who decided it.
                          chipKind(relation) === "mechanical"
                            ? relation.mode.toLowerCase()
                            : chipKind(relation)
                        }
                        meta={`${relation.count} tuple${relation.count === 1 ? "" : "s"} · ${relation.arity} roles${conditionOf(relation.stale, relation.completeness)}`}
                        onClose={() => setReaderOpen(false)}
                      />
                      <div className="world-reader__content">
                        {relation.description ? (
                          <p className="world-reader__description">
                            {relation.description}
                          </p>
                        ) : null}
                        <ol className="world__roles">
                          {relation.roles.map((role) => (
                            <li key={role.name}>
                              <b>{role.name}</b>
                              <span>
                                {role.referent
                                  ? role.kinds?.join(", ") || "referent"
                                  : role.type.toLowerCase()}
                              </span>
                            </li>
                          ))}
                        </ol>
                        {relation.derivation?.inputs?.length ? (
                          <section className="world-reader__section">
                            <h3>Rests on</h3>
                            <ul className="world__inputs">
                              {relation.derivation.inputs.map((input) => (
                                <li key={input}>{input}</li>
                              ))}
                            </ul>
                          </section>
                        ) : null}
                      </div>
                      <footer className="world-reader__actions">
                        <button
                          type="button"
                          className="node-reader__link"
                          onClick={() =>
                            showTable({
                              kind: "relation",
                              relation: relation.name,
                              subject: null,
                            })
                          }
                        >
                          Open extension
                        </button>
                        <button
                          type="button"
                          className="node-reader__link"
                          onClick={() =>
                            showTable({
                              kind: "derivation",
                              relation: relation.name,
                              assertion: null,
                            })
                          }
                        >
                          Dependencies
                        </button>
                      </footer>
                    </article>
                  ) : (
                    <article className="world-reader__article">
                      <ReaderHeader
                        title="Reader"
                        meta="Select a mark on the field"
                        onClose={() => setReaderOpen(false)}
                      />
                      <div className="world-reader__content">
                        <p className="world__hint">
                          A referent, assertion, or relation names what this
                          column is about. The world catalogue and the frontier
                          live in Tables.
                        </p>
                      </div>
                    </article>
                  )}
                </Swap>
              </div>
            </OverlayPanel>
            </div>
            </div>
          </div>
        </div>
      </div>

      <div className="product-shell__instrument" aria-label="Surface controls">
        <div className={chromeClass("instrument")}>
          <div className="gm__choosing">
            <div className="instrument__group" role="group" aria-label="find">
              <Find
                directory={set.referents.size || set.assertions.size || set.demands.size || set.bonds.length ? fieldDirectory : directory}
                onPick={onFind}
              />
            </div>
          </div>
          <ShowBand
            show={show}
            onShow={setShow}
            names={
              !onField || focusDrawn
                ? { on: namedAtRest, onToggle: () => setNamedAtRest((on) => !on) }
                : undefined
            }
          />
          {!focusDrawn && onField ? (
            <div
              className="instrument__group"
              role="group"
              aria-label="Arrange the field"
            >
              <button
                type="button"
                onClick={onSeparate}
                title="Push apart only what is sitting on top of something else"
              >
                separate
              </button>
              {arrangeUndo ? (
                <button
                  type="button"
                  onClick={onUndoArrange}
                  title={`Put back what ${arrangeUndo.label} displaced`}
                >
                  undo {arrangeUndo.label}
                </button>
              ) : null}
            </div>
          ) : null}
          {focusDrawn ? (
            <div className="instrument__group" role="group" aria-label="Clear focus">
              <button type="button" onClick={leaveVocabulary}>
                clear
              </button>
            </div>
          ) : onField ? (
            <div className="instrument__group" role="group" aria-label="Field">
              <button type="button" onClick={enterVocabulary}>
                vocabulary
              </button>
            </div>
          ) : null}
        </div>
      </div>
    </main>
  );
}
