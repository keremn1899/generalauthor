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
  useMemo,
  useRef,
  useState,
  type CSSProperties,
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
import {
  chromeCssVariables,
  GRAPH_DNA_CHROME,
  type ThemeMode,
} from "../styles/graphDna";
import { DerivationView } from "./DerivationView";
import { FrontierTable, type Obligation } from "./FrontierTable";
import { MARK_DEFAULTS } from "./marks";
import { RelationTable } from "./RelationTable";
import { SchemaCanvas } from "./SchemaCanvas";
import { chipKind } from "./schemaGraph";
import { WorldCanvas, type CanvasSelection } from "./WorldCanvas";
import {
  collapse,
  drop,
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
  type WorkingSet,
} from "./workingSet";
import { OverlayPanel } from "../product/OverlayPanel";
import { chromeClass } from "../product/overlayChrome";
import {
  readStoredPanelSize,
  storePanelSize,
} from "../product/ResizableDivider";
import "../styles/presence.css";
import {
  SHOW_DEFAULT,
  SHOW_LAYERS,
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

function storedTheme(): ThemeMode {
  try {
    return localStorage.getItem("graphauthor.productTheme") === "dark"
      ? "dark"
      : "light";
  } catch {
    return "light";
  }
}

function conditionOf(
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

type Directory = { id: string; label: string | null }[];

function Find({
  directory,
  onPick,
}: {
  directory: Directory;
  onPick: (id: string, label: string) => void;
}) {
  const [query, setQuery] = useState("");
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

  return (
    <div className="nodefind">
      <input
        className="nodefind__input"
        value={query}
        placeholder="Find a referent…"
        onChange={(event) => setQuery(event.target.value)}
      />
      {matches.length ? (
        <ul className="nodefind__list">
          {matches.map((item) => (
            <li
              key={item.id}
              className="nodefind__row"
              onMouseDown={(event) => {
                event.preventDefault();
                onPick(item.id, item.label || item.id);
                setQuery("");
              }}
            >
              <span className="nodefind__label">{item.label || item.id}</span>
              <span className="nodefind__anchor">{item.id}</span>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}

function ReaderHeader({
  title,
  kind,
  meta,
  onClose,
}: {
  title: string;
  kind?: string;
  meta?: string;
  onClose: () => void;
}) {
  return (
    <header className="world-reader__header">
      <div className="world-reader__heading">
        <h2>{title}</h2>
        {meta ? <p>{meta}</p> : null}
      </div>
      {kind ? <span className="node-reader__kind">{kind}</span> : null}
      <button
        type="button"
        className="world-reader__close"
        onClick={onClose}
      >
        Close
      </button>
    </header>
  );
}

function Grounding({ assertion }: { assertion: WorldAssertion }) {
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

function AssertionPanel({
  assertion,
  folding,
  onFold,
  onTable,
  onDerivation,
  onClose,
}: {
  assertion: WorldAssertion | null;
  /** Which way this tuple's second drawing lies, or null if it has none. */
  folding: "open" | "collapse" | null;
  onFold: () => void;
  onTable: (relation: string) => void;
  onDerivation: (relation: string, assertion: string | null) => void;
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
function DemandPanel({
  obligation,
  demand,
  roles,
  onTable,
  onClose,
}: {
  obligation: Obligation | null;
  demand: WorldDemand | null;
  /** Role order, since an obligation's values are a JSON object. */
  roles: string[];
  onTable: (relation: string) => void;
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
      </footer>
    </article>
  );
}

function ReferentPanel({
  detail,
  set,
  onExpand,
  onTable,
  onDrop,
  onClose,
}: {
  detail: WorldReferent | null;
  set: WorkingSet;
  onExpand: (relation: string, count: number) => void;
  onTable: (relation: string) => void;
  onDrop: () => void;
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
              const already = set.expanded.has(
                expansionKey(detail.id, relation.name),
              );
              const tooMany = relation.count > room;
              return (
                <li key={relation.name}>
                  <button
                    type="button"
                    className={already ? "is-selected" : undefined}
                    disabled={already}
                    data-table={tooMany ? true : undefined}
                    onClick={() =>
                      tooMany
                        ? onTable(relation.name)
                        : onExpand(relation.name, relation.count)
                    }
                  >
                    <span className="gm__list-name">{relation.name}</span>
                    <span className="gm__list-meta">
                      {already
                        ? "on field"
                        : tooMany
                          ? `${relation.count} · table`
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
        <button type="button" className="node-reader__link" onClick={onDrop}>
          Take off the field
        </button>
      </footer>
    </article>
  );
}

const READER_WIDTH_KEY = "graphauthor.worldReaderWidth";

/** A seam from construction's vocabulary card to this relation's extension.
 * Hash routing owns the path, so its query lives in the hash as well. */
function linkedRelationFromHash(): string | null {
  const hash = window.location.hash;
  const query = hash.includes("?") ? hash.slice(hash.indexOf("?") + 1) : "";
  return new URLSearchParams(query).get("relation");
}

export function WorldPage() {
  const [mode, setMode] = useState<ThemeMode>(storedTheme);
  const [overview, setOverview] = useState<WorldOverview | null>(null);
  const [relations, setRelations] = useState<WorldRelation[]>([]);
  const [directory, setDirectory] = useState<Directory>([]);
  const [error, setError] = useState<string | null>(null);

  const [set, setSet] = useState<WorkingSet>(emptySet);
  const [selection, setSelection] = useState<CanvasSelection>(null);
  const [hovered, setHovered] = useState<string | null>(null);
  const [hoveredRelation, setHoveredRelation] = useState<string | null>(null);
  const [focusedRelation, setFocusedRelation] = useState<string | null>(null);
  const [namedAtRest, setNamedAtRest] = useState(true);
  const [show, setShow] = useState<ShowState>(SHOW_DEFAULT);
  const [readerOpen, setReaderOpen] = useState(false);
  const [readerWidth, setReaderWidth] = useState(() =>
    readStoredPanelSize(READER_WIDTH_KEY, 320),
  );
  const [assertion, setAssertion] = useState<WorldAssertion | null>(null);
  const [referent, setReferent] = useState<WorldReferent | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  /**
   * What is open under the canvas. One slot, because the drawer answers one
   * question at a time: an extension — a relation, and the referent it was
   * opened from when it was opened from one — or the frontier.
   */
  const [drawer, setDrawer] = useState<
    | { kind: "relation"; relation: string; subject: { id: string; label: string } | null }
    | { kind: "frontier" }
    /**
     * §8.6. Opened on a relation, and carrying the tuple it was opened from
     * when there was one — the closure is a fact about the relation, the
     * candidate support is a question about one row, and both belong to the
     * same reading.
     */
    | { kind: "derivation"; relation: string; assertion: string | null }
    | null
  >(null);
  const [demand, setDemand] = useState<WorldDemand | null>(null);
  const [demandProblem, setDemandProblem] = useState<string | null>(null);

  const labels = useRef(new Map<string, string | null>());
  const linkedRelation = useRef(linkedRelationFromHash());

  useEffect(() => {
    try {
      localStorage.setItem("graphauthor.productTheme", mode);
    } catch {
      /* private mode */
    }
  }, [mode]);

  const onReaderWidth = useCallback((width: number) => {
    setReaderWidth(width);
    storePanelSize(READER_WIDTH_KEY, width);
  }, []);

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
    setDrawer({ kind: "relation", relation: name, subject: null });
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
  }, [chooseFieldMark]);

  const onExpand = useCallback(
    async (relation: string, count: number) => {
      if (!selection || selection.kind !== "referent") return;
      if (count > MAX_FIELD_NODES - fieldSize(set)) {
        setNotice(`${relation} has ${count} tuples — more than the field holds.`);
        return;
      }
      const schema = relations.find((item) => item.name === relation);
      try {
        const expansion = await worldApi.expand(selection.id, relation);
        if (schema) setShow((current) => reveal(schema, current));
        setSet((current) =>
          expand(current, {
            anchor: selection.id,
            relation,
            mode: schema?.mode ?? "BASE",
            stale: schema?.stale ?? false,
            completeness: schema?.completeness?.status ?? null,
            roles: expansion.roles,
            tuples: expansion.tuples,
            labels: labels.current,
          }),
        );
      } catch (problem) {
        setNotice((problem as Error).message);
      }
    },
    [relations, selection, set],
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
   * whichever drawer happens to be open.
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
    },
    [chooseFieldMark, relations],
  );

  const onFocusRow = useCallback((roles: WorldRole[], tuple: WorldTuple) => {
    if (drawer?.kind !== "relation") return;
    placeTuple(drawer.relation, roles, tuple);
  }, [drawer, placeTuple]);

  /**
   * The obligation set, read once and only when it is asked for.
   *
   * Not part of the opening fetch: resolving every obligation against the world
   * is work nobody has asked for until they open the frontier, and the overview
   * already carries the counts the vocabulary panel prints.
   */
  useEffect(() => {
    if (drawer?.kind !== "frontier" || demand) return;
    let cancelled = false;
    worldApi
      .demand()
      .then((found) => !cancelled && setDemand(found))
      .catch((problem: Error) => !cancelled && setDemandProblem(problem.message));
    return () => {
      cancelled = true;
    };
  }, [drawer, demand]);

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
    },
    [chooseFieldMark, relations],
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

  const onDrop = useCallback(() => {
    if (!selection || selection.kind !== "referent") return;
    setSet((current) => drop(current, selection.id));
    chooseFieldMark(null);
  }, [chooseFieldMark, selection]);

  const visibleRelations = useMemo(
    () => relations.filter((item) => relationShown(item, show)),
    [relations, show],
  );
  const style = chromeCssVariables(GRAPH_DNA_CHROME[mode]) as CSSProperties;
  const onField = fieldSize(set) > 0;
  const relation = relations.find((item) => item.name === focusedRelation) ?? null;
  const activeRelation = hoveredRelation ?? focusedRelation;
  const extension =
    drawer?.kind === "relation"
      ? relations.find((item) => item.name === drawer.relation) ?? null
      : null;

  return (
    <main
      className={`product-shell world${mode === "dark" ? " is-dark" : ""}`}
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
          <div className="product-shell__utils">
            <button
              type="button"
              className="product-shell__theme"
              onClick={() =>
                setMode((value) => (value === "light" ? "dark" : "light"))
              }
              aria-label={`Use ${mode === "light" ? "dark" : "light"} appearance`}
            >
              {mode === "light" ? "Dark" : "Light"}
            </button>
          </div>
        </div>
      </header>

      <div className="product-shell__body">
        <div className="product-shell__scenes">
          <div className="product-shell__scene is-in">
            <div className="gm gm--product">
            <div className="gm__main">
              {/* Canvas and table are one column, not two tabs: §11's rule is
                  that you never choose between them, and a row you select has
                  to land somewhere you can see it land. */}
              <div className="gm__stage world__plane">
                {error ? (
                  <p className="world__error">
                    {error} — is the read plane running?{" "}
                    <code>
                      uv run --extra all python scripts/run_world_explorer.py
                    </code>
                  </p>
                ) : onField ? (
                  <WorldCanvas
                    set={set}
                    mode={mode}
                    params={MARK_DEFAULTS}
                    hovered={hovered}
                    selection={selection}
                    show={show}
                    onHover={setHovered}
                    onSelect={chooseFieldMark}
                    onPositions={onPositions}
                  />
                ) : (
                  <SchemaCanvas
                    relations={visibleRelations}
                    mode={mode}
                    namedAtRest={namedAtRest}
                    active={activeRelation}
                    selected={focusedRelation}
                    onHover={setHoveredRelation}
                    onSelect={chooseSchemaRelation}
                  />
                )}
                {extension && drawer?.kind === "relation" ? (
                  <RelationTable
                    key={extension.name}
                    relation={extension}
                    subject={drawer.subject}
                    present={present}
                    onFocus={onFocusRow}
                    onWiden={() =>
                      setDrawer({
                        kind: "relation",
                        relation: extension.name,
                        subject: null,
                      })
                    }
                    onDerivation={() =>
                      setDrawer({
                        kind: "derivation",
                        relation: extension.name,
                        assertion: null,
                      })
                    }
                    onClose={() => setDrawer(null)}
                  />
                ) : drawer?.kind === "derivation" ? (
                  <DerivationView
                    key={`${drawer.relation}\u0000${drawer.assertion ?? ""}`}
                    relation={drawer.relation}
                    assertionId={drawer.assertion}
                    present={present}
                    onOpen={(name) =>
                      setDrawer({
                        kind: "derivation",
                        relation: name,
                        assertion: null,
                      })
                    }
                    onTable={(name) =>
                      setDrawer({
                        kind: "relation",
                        relation: name,
                        subject: null,
                      })
                    }
                    onFocus={placeTuple}
                    onClose={() => setDrawer(null)}
                  />
                ) : drawer?.kind === "frontier" ? (
                  <FrontierTable
                    demand={demand}
                    relations={relations}
                    problem={demandProblem}
                    present={present}
                    onFocus={onFocusObligation}
                    onClose={() => setDrawer(null)}
                  />
                ) : null}
              </div>
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
              flush
            >
              <div className="node-reader">
                {notice ? <p className="world__notice">{notice}</p> : null}
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
                      setDrawer({
                        kind: "relation",
                        relation: name,
                        subject: null,
                      })
                    }
                    onClose={() => setReaderOpen(false)}
                  />
                ) : onField && selection?.kind === "assertion" ? (
                  <AssertionPanel
                    assertion={assertion}
                    folding={folding}
                    onFold={onFold}
                    onTable={(name) =>
                      setDrawer({
                        kind: "relation",
                        relation: name,
                        subject: null,
                      })
                    }
                    onDerivation={(name, id) =>
                      setDrawer({
                        kind: "derivation",
                        relation: name,
                        assertion: id,
                      })
                    }
                    onClose={() => setReaderOpen(false)}
                  />
                ) : onField && selection?.kind === "referent" ? (
                  <ReferentPanel
                    detail={referent}
                    set={set}
                    onExpand={onExpand}
                    onTable={(name) =>
                      setDrawer({
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
                    onDrop={onDrop}
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
                          setDrawer({
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
                          setDrawer({
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
                      title="World overview"
                      kind="vocabulary"
                      meta={
                        overview
                          ? `${overview.relations} relations · revision ${overview.revision}`
                          : "Reading world"
                      }
                      onClose={() => setReaderOpen(false)}
                    />
                    <div className="world-reader__content">
                      {overview ? (
                        <dl className="world__facts">
                          <div>
                            <dt>Referents</dt>
                            <dd>{overview.referents}</dd>
                          </div>
                          <div>
                            <dt>Assertions</dt>
                            <dd>{overview.assertions}</dd>
                          </div>
                          {Object.entries(overview.origins).map(
                            ([origin, count]) => (
                              <div key={origin}>
                                <dt>{origin.toLowerCase()}</dt>
                                <dd>{count}</dd>
                              </div>
                            ),
                          )}
                          {overview.stale.length ? (
                            <div>
                              <dt>Stale</dt>
                              <dd>{overview.stale.length}</dd>
                            </div>
                          ) : null}
                          {overview.incomplete?.length ? (
                            <div>
                              <dt>Incomplete</dt>
                              <dd>{overview.incomplete.length}</dd>
                            </div>
                          ) : null}
                        </dl>
                      ) : null}
                      {overview?.demand ? (
                        <button
                          type="button"
                          className="world-reader__demand"
                          onClick={() => setDrawer({ kind: "frontier" })}
                        >
                          <span>{overview.demand.purpose.id}</span>
                          <span>
                            {overview.demand.obligations} unresolved of{" "}
                            {overview.demand.demanded}
                          </span>
                        </button>
                      ) : null}
                      <section className="world-reader__section world-reader__section--list">
                        <h3>Relations</h3>
                        <ul className="gm__list">
                          {relations.map((item) => (
                            <li key={item.name}>
                              <button
                                type="button"
                                onClick={() =>
                                  setDrawer({
                                    kind: "relation",
                                    relation: item.name,
                                    subject: null,
                                  })
                                }
                              >
                                <span className="gm__list-name">
                                  {item.name}
                                </span>
                                <span className="gm__list-meta">
                                  {item.count}
                                </span>
                              </button>
                            </li>
                          ))}
                        </ul>
                      </section>
                    </div>
                  </article>
                )}
              </div>
            </OverlayPanel>
            </div>
          </div>
        </div>
      </div>

      <div className="product-shell__instrument" aria-label="Surface controls">
        <div className={chromeClass("instrument")}>
          <div className="instrument__group" role="group" aria-label="Find a referent">
            <Find directory={directory} onPick={onSeed} />
          </div>
          <div className="instrument__group" role="group" aria-label="Show">
            {SHOW_LAYERS.map((layer) => (
              <button
                key={layer}
                type="button"
                aria-pressed={show[layer]}
                onClick={() =>
                  setShow((current) => ({ ...current, [layer]: !current[layer] }))
                }
              >
                {layer}
              </button>
            ))}
          </div>
          <div className="instrument__group" role="group" aria-label="View">
            {overview?.demand ? (
              <button
                type="button"
                aria-pressed={drawer?.kind === "frontier"}
                onClick={() =>
                  setDrawer((current) =>
                    current?.kind === "frontier" ? null : { kind: "frontier" },
                  )
                }
              >
                frontier
              </button>
            ) : null}
            {onField ? (
              <button
                type="button"
                onClick={() => {
                  setSet(emptySet());
                  chooseFieldMark(null);
                }}
              >
                vocabulary
              </button>
            ) : (
              <button
                type="button"
                aria-pressed={namedAtRest}
                onClick={() => setNamedAtRest((on) => !on)}
              >
                names
              </button>
            )}
            <button
              type="button"
              aria-pressed={
                readerOpen && selection === null && focusedRelation === null
              }
              onClick={() => {
                setSelection(null);
                setFocusedRelation(null);
                setReaderOpen((open) =>
                  selection === null && focusedRelation === null ? !open : true,
                );
              }}
            >
              overview
            </button>
          </div>
          {onField ? (
            <div
              className="instrument__readings"
              role="status"
              aria-label="Field occupancy"
            >
              {fieldSize(set)} / {MAX_FIELD_NODES} on field
            </div>
          ) : null}
        </div>
      </div>
    </main>
  );
}
