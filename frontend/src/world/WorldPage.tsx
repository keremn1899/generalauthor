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
 * Deliberately not built on `ProductShell`. That shell knows about graphs,
 * logs, constructions, an operator plane and a write path — none of which
 * exist here. It reads the same chrome tokens, so it is the same room.
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
import { MARK_DEFAULTS } from "./marks";
import { RelationTable } from "./RelationTable";
import { SchemaCanvas } from "./SchemaCanvas";
import { WorldCanvas, type CanvasSelection } from "./WorldCanvas";
import {
  drop,
  emptySet,
  expand,
  expansionKey,
  fieldSize,
  MAX_FIELD_NODES,
  place,
  seed,
  type WorkingSet,
} from "./workingSet";
import "./WorldPage.css";

function storedTheme(): ThemeMode {
  try {
    return localStorage.getItem("graphauthor.productTheme") === "dark"
      ? "dark"
      : "light";
  } catch {
    return "light";
  }
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
      .slice(0, 12);
  }, [directory, query]);

  return (
    <div className="world__find">
      <input
        value={query}
        placeholder="Find a referent…"
        onChange={(event) => setQuery(event.target.value)}
      />
      {matches.length ? (
        <ul>
          {matches.map((item) => (
            <li key={item.id}>
              <button
                type="button"
                onClick={() => {
                  onPick(item.id, item.label || item.id);
                  setQuery("");
                }}
              >
                <b>{item.label || item.id}</b>
                <span>{item.id}</span>
              </button>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
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
  onTable,
}: {
  assertion: WorldAssertion | null;
  onTable: (relation: string) => void;
}) {
  if (!assertion) return <p className="world__hint">Reading…</p>;
  return (
    <>
      <h2>{assertion.relation}</h2>
      <p className="world__mode">
        {assertion.origin.toLowerCase()} · {assertion.mode.toLowerCase()} · rev{" "}
        {assertion.created_revision}
        {assertion.relation_stale ? " · relation stale" : ""}
      </p>
      <ol className="world__roles">
        {assertion.roles.map((role) => (
          <li key={role.name}>
            <b>{role.name}</b>
            <span>{String(assertion.values[role.name] ?? "—")}</span>
          </li>
        ))}
      </ol>
      {assertion.derivation?.inputs?.length ? (
        <>
          <h3>rests on</h3>
          <ul className="world__inputs">
            {assertion.derivation.inputs.map((input) => (
              <li key={input}>{input}</li>
            ))}
          </ul>
        </>
      ) : null}
      <Grounding assertion={assertion} />
      <button
        type="button"
        className="world__drop"
        onClick={() => onTable(assertion.relation)}
      >
        open {assertion.relation}
      </button>
    </>
  );
}

function ReferentPanel({
  detail,
  set,
  onExpand,
  onTable,
  onDrop,
}: {
  detail: WorldReferent | null;
  set: WorkingSet;
  onExpand: (relation: string, count: number) => void;
  onTable: (relation: string) => void;
  onDrop: () => void;
}) {
  if (!detail) return <p className="world__hint">Reading…</p>;
  const room = MAX_FIELD_NODES - fieldSize(set);
  return (
    <>
      <h2>{detail.label || detail.id}</h2>
      <p className="world__mode">{detail.id}</p>
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
      <h3>expand</h3>
      <ul className="world__expand">
        {detail.relations.map((relation) => {
          const already = set.expanded.has(expansionKey(detail.id, relation.name));
          // The cost is known before anything is drawn, which is what makes a
          // bounded canvas workable rather than a truncation — and what makes
          // it a choice rather than a refusal: a relation too big for the field
          // is exactly the one that belongs in a table (§10), so that is where
          // the button goes instead of going grey.
          const tooMany = relation.count > room;
          return (
            <li key={relation.name}>
              <button
                type="button"
                disabled={already}
                data-table={tooMany ? true : undefined}
                onClick={() =>
                  tooMany
                    ? onTable(relation.name)
                    : onExpand(relation.name, relation.count)
                }
              >
                <b>{relation.name}</b>
                <span>
                  {already ? "on field" : tooMany ? `${relation.count} · table` : relation.count}
                </span>
              </button>
            </li>
          );
        })}
      </ul>
      <button type="button" className="world__drop" onClick={onDrop}>
        take off the field
      </button>
    </>
  );
}

export function WorldPage() {
  const [mode] = useState<ThemeMode>(storedTheme);
  const [overview, setOverview] = useState<WorldOverview | null>(null);
  const [relations, setRelations] = useState<WorldRelation[]>([]);
  const [directory, setDirectory] = useState<Directory>([]);
  const [error, setError] = useState<string | null>(null);

  const [set, setSet] = useState<WorkingSet>(emptySet);
  const [selection, setSelection] = useState<CanvasSelection>(null);
  const [hovered, setHovered] = useState<string | null>(null);
  const [focusedRelation, setFocusedRelation] = useState<string | null>(null);
  const [namedAtRest, setNamedAtRest] = useState(true);
  const [assertion, setAssertion] = useState<WorldAssertion | null>(null);
  const [referent, setReferent] = useState<WorldReferent | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  /**
   * The extension open under the canvas: a relation, and the referent it was
   * opened from when it was opened from one.
   */
  const [table, setTable] = useState<
    { relation: string; subject: { id: string; label: string } | null } | null
  >(null);

  const labels = useRef(new Map<string, string | null>());

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

  // Selection drives one fetch, and only one: a chip reads its assertion, a
  // disc reads its neighborhood costs.
  useEffect(() => {
    setNotice(null);
    if (!selection) {
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

  const onSeed = useCallback((id: string, label: string) => {
    setSet((current) => seed(current, id, label));
    setSelection({ kind: "referent", id });
  }, []);

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
        setSet((current) =>
          expand(current, {
            anchor: selection.id,
            relation,
            mode: schema?.mode ?? "BASE",
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
  const onFocusRow = useCallback((roles: WorldRole[], tuple: WorldTuple) => {
    const relation = table?.relation;
    if (!relation) return;
    const schema = relations.find((item) => item.name === relation);
    setSet((current) =>
      place(current, {
        relation,
        mode: schema?.mode ?? "BASE",
        roles,
        tuple,
        labels: labels.current,
      }),
    );
    setSelection({ kind: "assertion", id: tuple.assertion_id });
  }, [relations, table]);

  /** Assertion ids on the field, so the table can mark what is already placed. */
  const present = useMemo(() => {
    const ids = new Set<string>(set.assertions.keys());
    for (const bond of set.bonds) ids.add(bond.assertion_id);
    return ids;
  }, [set]);

  const onDrop = useCallback(() => {
    if (!selection || selection.kind !== "referent") return;
    setSet((current) => drop(current, selection.id));
    setSelection(null);
  }, [selection]);

  const style = chromeCssVariables(GRAPH_DNA_CHROME[mode]) as CSSProperties;
  const onField = fieldSize(set) > 0;
  const relation = relations.find((item) => item.name === focusedRelation) ?? null;
  const extension = relations.find((item) => item.name === table?.relation) ?? null;

  return (
    <main className="world" style={style} data-mode={mode}>
      <header className="world__bar">
        <span className="world__id">{overview?.world_id ?? "world"}</span>
        <span className="world__rev">{overview ? `rev ${overview.revision}` : ""}</span>
        <Find directory={directory} onPick={onSeed} />
        {onField ? (
          <>
            <span className="world__rev">
              {fieldSize(set)} / {MAX_FIELD_NODES} on field
            </span>
            <button type="button" onClick={() => { setSet(emptySet()); setSelection(null); }}>
              vocabulary
            </button>
          </>
        ) : (
          <button
            type="button"
            data-active={namedAtRest}
            onClick={() => setNamedAtRest((on) => !on)}
          >
            names
          </button>
        )}
      </header>

      {error ? (
        <p className="world__error">
          {error} — is the read plane running?{" "}
          <code>uv run --extra all python scripts/run_world_explorer.py</code>
        </p>
      ) : (
        <div className="world__body">
          {/* Canvas and table are one column, not two tabs: §11's rule is that
              you never choose between them, and a row you select has to land
              somewhere you can see it land. */}
          <div className="world__plane">
            {onField ? (
              <WorldCanvas
                set={set}
                mode={mode}
                params={MARK_DEFAULTS}
                hovered={hovered}
                selection={selection}
                onHover={setHovered}
                onSelect={setSelection}
                onPositions={onPositions}
              />
            ) : (
              <SchemaCanvas
                relations={relations}
                mode={mode}
                namedAtRest={namedAtRest}
                focused={focusedRelation}
                onFocus={setFocusedRelation}
              />
            )}
            {extension && table ? (
              <RelationTable
                key={extension.name}
                relation={extension}
                subject={table.subject}
                present={present}
                onFocus={onFocusRow}
                onWiden={() => setTable({ relation: extension.name, subject: null })}
                onClose={() => setTable(null)}
              />
            ) : null}
          </div>

          <aside className="world__panel">
            {notice ? <p className="world__notice">{notice}</p> : null}
            {onField && selection?.kind === "assertion" ? (
              <AssertionPanel
                assertion={assertion}
                onTable={(name) => setTable({ relation: name, subject: null })}
              />
            ) : onField && selection?.kind === "referent" ? (
              <ReferentPanel
                detail={referent}
                set={set}
                onExpand={onExpand}
                onTable={(name) =>
                  setTable({
                    relation: name,
                    subject: referent
                      ? { id: referent.id, label: referent.label || referent.id }
                      : null,
                  })
                }
                onDrop={onDrop}
              />
            ) : onField ? (
              <p className="world__hint">Click a mark to read it.</p>
            ) : relation ? (
              <>
                <h2>{relation.name}</h2>
                <p className="world__mode">
                  {relation.mode.toLowerCase()} · arity {relation.arity} ·{" "}
                  {relation.count} tuple{relation.count === 1 ? "" : "s"}
                  {relation.stale ? " · stale" : ""}
                </p>
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
                  <>
                    <h3>rests on</h3>
                    <ul className="world__inputs">
                      {relation.derivation.inputs.map((input) => (
                        <li key={input}>{input}</li>
                      ))}
                    </ul>
                  </>
                ) : null}
                <button
                  type="button"
                  className="world__drop"
                  onClick={() => setTable({ relation: relation.name, subject: null })}
                >
                  open extension
                </button>
              </>
            ) : (
              <>
                <h2>Vocabulary</h2>
                {overview ? (
                  <dl className="world__facts">
                    <dt>relations</dt>
                    <dd>{overview.relations}</dd>
                    <dt>referents</dt>
                    <dd>{overview.referents}</dd>
                    <dt>assertions</dt>
                    <dd>{overview.assertions}</dd>
                    {Object.entries(overview.origins).map(([origin, count]) => (
                      <div key={origin} className="world__facts-row">
                        <dt>{origin.toLowerCase()}</dt>
                        <dd>{count}</dd>
                      </div>
                    ))}
                  </dl>
                ) : null}
                {overview?.demand ? (
                  <p className="world__note">
                    <b>{overview.demand.purpose.id}</b> demands{" "}
                    {overview.demand.demanded} case
                    {overview.demand.demanded === 1 ? "" : "s"};{" "}
                    {overview.demand.obligations} unresolved.
                  </p>
                ) : (
                  <p className="world__note">
                    No purpose loaded — unresolved obligations cannot be shown.
                  </p>
                )}
                <h3>relations</h3>
                {/* The canvas names a relation when you hover it, which is the
                    right behaviour for a picture and the wrong one for a list:
                    you cannot scan a canvas for "the big ones", and a relation
                    drawn as a filament has no handle to open its extension
                    from. The index is that handle. */}
                <ul className="world__expand">
                  {relations.map((item) => (
                    <li key={item.name}>
                      <button
                        type="button"
                        onMouseEnter={() => setFocusedRelation(item.name)}
                        onClick={() => setTable({ relation: item.name, subject: null })}
                      >
                        <b>{item.name}</b>
                        <span>{item.count}</span>
                      </button>
                    </li>
                  ))}
                </ul>
              </>
            )}
          </aside>
        </div>
      )}
    </main>
  );
}
