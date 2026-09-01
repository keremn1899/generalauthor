/**
 * World — the read-side explorer's home.
 *
 * You land on the schema, not on an empty canvas and not on a table. It is the
 * one whole-World view that does not break rule 9: a vocabulary is small no
 * matter how large its extensions, so drawing all of it answers *what kind of
 * world is this?* without ever putting a database on the field.
 *
 * Deliberately not built on `ProductShell`. That shell knows about graphs,
 * logs, constructions, an operator plane and a write path — none of which
 * exist here, and inheriting them would make this surface look like a fourth
 * tab of a product it is not part of. It reads the same chrome tokens, so it
 * is the same room.
 */

import { useCallback, useEffect, useMemo, useRef, useState, type CSSProperties } from "react";
import { Graph } from "@antv/g6";
import {
  worldApi,
  type WorldOverview,
  type WorldRelation,
} from "../api/world";
import {
  chromeCssVariables,
  GRAPH_DNA_CHROME,
  GRAPH_DNA_PROVISIONAL_THEME,
  GRAPH_DNA_THEME,
  type ThemeMode,
} from "../styles/graphDna";
import { MARK_DEFAULTS, paintOf } from "./marks";
import { schemaLayout } from "./schemaGraph";
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

function SchemaCanvas({
  relations,
  mode,
  namedAtRest,
  focused,
  onFocus,
}: {
  relations: WorldRelation[];
  mode: ThemeMode;
  namedAtRest: boolean;
  focused: string | null;
  onFocus: (relation: string | null) => void;
}) {
  const hostRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<Graph | null>(null);

  const paint = useMemo(() => paintOf(GRAPH_DNA_THEME[mode]), [mode]);
  const stalePaint = useMemo(
    () => paintOf(GRAPH_DNA_PROVISIONAL_THEME[mode]),
    [mode],
  );
  const layout = useMemo(
    () =>
      schemaLayout(relations, paint, stalePaint, MARK_DEFAULTS, {
        namedAtRest,
        focused,
      }),
    [relations, paint, stalePaint, namedAtRest, focused],
  );

  useEffect(() => {
    const host = hostRef.current;
    if (!host || !relations.length) return;
    const graph = new Graph({
      container: host,
      data: layout.data as never,
      animation: false,
      autoFit: { type: "view", options: { direction: "both" } },
      padding: 48,
      background: paint.canvas,
      // Pan and zoom, no drag. The schema's arrangement is computed and stable
      // on purpose — a vocabulary you can rearrange is one you cannot learn the
      // shape of — so nodes are read, not moved.
      behaviors: ["zoom-canvas", "drag-canvas"],
    });
    graphRef.current = graph;

    // G6's event type is the union of everything it can emit, so the element
    // id is reached through an unknown rather than asserted into a shape the
    // library does not promise.
    const idOf = (event: unknown): string | null => {
      const target = (event as { target?: { id?: unknown } } | undefined)?.target;
      return typeof target?.id === "string" ? target.id : null;
    };
    graph.on("node:pointerenter", (event) => {
      const id = idOf(event);
      onFocus(id && id.startsWith("rel:") ? id.slice(4) : null);
    });
    graph.on("edge:pointerenter", (event) => {
      const id = idOf(event);
      if (id) onFocus(id.split(":")[0]);
    });
    graph.on("canvas:click", () => onFocus(null));

    void graph.render();
    return () => {
      graphRef.current = null;
      graph.destroy();
    };
  }, [layout, paint.canvas, relations.length, onFocus]);

  return <div className="world__stage" ref={hostRef} style={{ background: paint.canvas }} />;
}

function RelationPanel({
  relations,
  focused,
  overview,
}: {
  relations: WorldRelation[];
  focused: string | null;
  overview: WorldOverview | null;
}) {
  const relation = relations.find((item) => item.name === focused) ?? null;

  if (!relation) {
    return (
      <aside className="world__panel">
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
            <b>{overview.demand.purpose.id}</b> demands {overview.demand.demanded}{" "}
            case{overview.demand.demanded === 1 ? "" : "s"};{" "}
            {overview.demand.obligations} unresolved.
          </p>
        ) : (
          <p className="world__note">
            No purpose loaded — unresolved obligations cannot be shown.
          </p>
        )}
        <p className="world__hint">Hover a relation to read it.</p>
      </aside>
    );
  }

  return (
    <aside className="world__panel">
      <h2>{relation.name}</h2>
      <p className="world__mode">
        {relation.mode.toLowerCase()} · arity {relation.arity} ·{" "}
        {relation.count} tuple{relation.count === 1 ? "" : "s"}
        {relation.stale ? " · stale" : ""}
      </p>
      {relation.description ? (
        <p className="world__note">{relation.description}</p>
      ) : null}
      <ol className="world__roles">
        {relation.roles.map((role) => (
          <li key={role.name}>
            <b>{role.name}</b>
            <span>{role.referent ? (role.kinds?.join(", ") || "referent") : role.type.toLowerCase()}</span>
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
    </aside>
  );
}

export function WorldPage() {
  const [mode] = useState<ThemeMode>(storedTheme);
  const [relations, setRelations] = useState<WorldRelation[]>([]);
  const [overview, setOverview] = useState<WorldOverview | null>(null);
  const [focused, setFocused] = useState<string | null>(null);
  const [namedAtRest, setNamedAtRest] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([worldApi.overview(), worldApi.schema()])
      .then(([summary, schema]) => {
        if (cancelled) return;
        setOverview(summary);
        setRelations(schema);
      })
      .catch((problem: Error) => {
        if (!cancelled) setError(problem.message);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const onFocus = useCallback((relation: string | null) => setFocused(relation), []);
  const style = chromeCssVariables(GRAPH_DNA_CHROME[mode]) as CSSProperties;

  return (
    <main className="world" style={style} data-mode={mode}>
      <header className="world__bar">
        <span className="world__id">{overview?.world_id ?? "world"}</span>
        <span className="world__rev">
          {overview ? `rev ${overview.revision}` : ""}
        </span>
        <button
          type="button"
          data-active={namedAtRest}
          onClick={() => setNamedAtRest((on) => !on)}
        >
          names
        </button>
      </header>
      {error ? (
        <p className="world__error">
          {error} — is the read plane running?{" "}
          <code>uv run --extra all python scripts/run_world_explorer.py</code>
        </p>
      ) : (
        <div className="world__body">
          <SchemaCanvas
            relations={relations}
            mode={mode}
            namedAtRest={namedAtRest}
            focused={focused}
            onFocus={onFocus}
          />
          <RelationPanel relations={relations} focused={focused} overview={overview} />
        </div>
      )}
    </main>
  );
}
