/**
 * The unresolved frontier — what a purpose asked of this world and did not get.
 *
 * §8.7 makes semantic demand first-class, and the reason it has to be a surface
 * of its own is that unresolved is not a property of the world. It is the join
 * between an obligation set some purpose generated and what the world asserts,
 * so it cannot be read off a relation's extension, and with no purpose loaded
 * there is no such thing as an unresolved obligation — which is a different
 * statement from there being none.
 *
 * The list is a table because obligations are rows, and it shares the
 * extension's shape, windowing and margin rule so that "a row you can put on
 * the field" means one thing across the product. What it does not share is the
 * paging: an obligation set is one document the read plane already holds, so
 * there is nothing to page and the whole list arrives at once.
 *
 * One rule of tone. Resolved obligations are shown, quietly, because the
 * interesting thing about a frontier is where it has moved; unresolved ones are
 * shown at full strength. Neither is coloured. **Absence is not falsehood** —
 * the world has not denied these tuples, it has said nothing about them — so
 * nothing here is allowed to read as a rejection.
 */

import { useMemo, useState } from "react";
import type { WorldDemand, WorldRelation } from "../api/world";
import { still } from "../styles/motion";
import { useRowWindow } from "./rowWindow";
import { TableBar, type TableChrome } from "./tableChrome";

const ROW_HEIGHT = 26;
const OVERSCAN = 8;
const COLUMNS = "minmax(0, 1.1fr) minmax(0, 2fr) minmax(0, 1fr) 96px";

export type Obligation = WorldDemand["obligations"][number] & { key: string };

export function FrontierTable({
  demand,
  relations,
  problem,
  present,
  chrome,
  onFocus,
}: {
  demand: WorldDemand | null;
  /** The vocabulary, so a tuple prints in role order rather than JSON order. */
  relations: WorldRelation[];
  problem: string | null;
  /** Obligation keys and assertion ids already on the field. */
  present: Set<string>;
  chrome: TableChrome;
  onFocus: (obligation: Obligation) => void;
}) {
  const [resolved, setResolved] = useState(false);

  const all = useMemo<Obligation[]>(
    () =>
      (demand?.obligations ?? []).map((obligation, index) => ({
        ...obligation,
        // Positional, and positional in the *document* rather than in whatever
        // is being shown, so a key means the same obligation whether or not the
        // resolved ones are filtered out. Not `demand:0`, because a trailing
        // `:<digits>` is how this surface marks a role spoke.
        key: `demand#${index}`,
      })),
    [demand],
  );
  const rows = useMemo(
    () => (resolved ? all : all.filter((item) => item.state === "UNRESOLVED")),
    [all, resolved],
  );
  const open = all.filter((item) => item.state === "UNRESOLVED").length;

  const window_ = useRowWindow(rows.length, ROW_HEIGHT, OVERSCAN);
  const order = useMemo(
    () => new Map(relations.map((item) => [item.name, item.roles.map((role) => role.name)])),
    [relations],
  );

  return (
    <section className="table" aria-label="unresolved frontier">
      <TableBar
        chrome={chrome}
        meta={
          demand ? (
            <>
              {open} unresolved of {all.length} obligation
              {all.length === 1 ? "" : "s"} · {demand.purpose.id} rev{" "}
              {demand.purpose.revision}
            </>
          ) : (
            "no purpose loaded"
          )
        }
      >
        <button
          type="button"
          data-active={resolved}
          onClick={() => setResolved((on) => !on)}
        >
          {resolved ? "unresolved only" : "show resolved"}
        </button>
      </TableBar>

      <div className="table__head" style={{ gridTemplateColumns: COLUMNS }}>
        <span>relation</span>
        <span>tuple</span>
        <span>demanded by</span>
        <span>state</span>
      </div>

      {problem ? <p className="table__problem">{problem}</p> : null}
      {demand ? null : (
        <p className="table__problem">
          {problem
            ? ""
            : "No purpose is loaded, so this world has no obligations to be short of."}
        </p>
      )}

      <div className="table__scroll" ref={window_.ref} onScroll={window_.onScroll}>
        <div className="table__spacer" style={{ height: rows.length * ROW_HEIGHT }}>
          {window_.indices.map((index) => {
            const item = rows[index];
            if (!item) return null;
            const placed = present.has(item.key) || Boolean(item.assertion_id && present.has(item.assertion_id));
            return (
              <div
                key={item.key}
                className="table__row"
                {...still("rowsNeverFly")}
                data-loaded
                data-present={placed ? true : undefined}
                data-resolved={item.state === "ASSERTED" ? true : undefined}
                style={{ top: index * ROW_HEIGHT, height: ROW_HEIGHT, gridTemplateColumns: COLUMNS }}
                onClick={() => onFocus(item)}
              >
                <span>{item.relation}</span>
                <span title={tuple(item, order)}>{tuple(item, order)}</span>
                <span className="table__origin">{demandedBy(item.demanded_by)}</span>
                <span className="table__origin">{item.state.toLowerCase()}</span>
              </div>
            );
          })}
        </div>
      </div>

      {demand ? (
        <p className="table__rule" title={demand.rule}>
          {demand.rule}
        </p>
      ) : null}
    </section>
  );
}

/**
 * `X110, X160, indoor_panel` — in role order, namespaces dropped as elsewhere.
 *
 * Role order, not the order the keys happen to arrive in: an obligation's
 * values are a JSON object, and printing `acceptable_replacement` as
 * `indoor_panel, X110, X160` because that is alphabetical would be printing a
 * different tuple.
 */
function tuple(
  item: Obligation,
  order: Map<string, string[]>,
): string {
  const names = order.get(item.relation) ?? Object.keys(item.values);
  return names
    .map((name) => item.values[name])
    .map((value) => {
      const text = String(value);
      const colon = text.indexOf(":");
      return colon > 0 ? text.slice(colon + 1) : text;
    })
    .join(", ");
}

function demandedBy(source: Record<string, unknown>): string {
  const name = source.name ?? source.id ?? source.kind ?? "";
  return source.revision ? `${name} rev ${source.revision}` : String(name);
}
