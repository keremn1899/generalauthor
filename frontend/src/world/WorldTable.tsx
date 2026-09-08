/**
 * The world's own catalogue — idle body of the TABLES dock.
 *
 * Overview counts belong in the bar (what this world is). Rows are relations:
 * name, size, scope, mode, construction origin, stale. Clicking one opens that
 * relation's extension in the same panel. The frontier is a sibling subject,
 * not a row, because unresolved is not a property of the world.
 *
 * Scope is a column rather than a canvas mark. WORLD and PURPOSE are what a
 * relation is *for*, which is neither an origin (geometry) nor a status
 * (palette), and the canvas has no free axis left to say it in. A word in a
 * table says it exactly, and a blank says the world recorded no admission —
 * which is different from, and must not be drawn as, WORLD.
 */

import { useEffect, useMemo, useRef, useState } from "react";
import type { WorldOverview, WorldRelation } from "../api/world";
import { still } from "../styles/motion";
import { useRowWindow } from "./rowWindow";
import { chipKind } from "./schemaGraph";
import { TableBar, TableSearch, type TableChrome } from "./tableChrome";
import { useTableWidth, type TableWidth } from "./tableWidth";

// Retained for a future placement-filter control; currently unwired.
const PLACEMENT_FILTER_ENABLED = false;

const ROW_HEIGHT = 26;
const OVERSCAN = 8;
/**
 * The name is the row; everything else qualifies it.
 *
 * Four fixed columns totalling 268px inside a 360px dock left the relation
 * about 42px — every name in the catalogue printed as `chec…`, which is the
 * one thing a catalogue exists to show. The qualifiers hold single short words
 * (`world`, `base`, `mechanical`) and give way proportionally; only the count
 * and the stale mark, which are a number and a five-letter word, stay fixed.
 */
const COLUMNS = {
  wide: "minmax(0, 1.9fr) 44px minmax(0, 0.7fr) minmax(0, 0.7fr) minmax(0, 0.95fr) 40px",
  /**
   * The same six columns, sized for the short words rather than the long ones.
   *
   * The name takes the room the qualifiers give up, because it is the row and
   * they only qualify it. Nothing is dropped: a column removed at one width and
   * back at another is a catalogue that says different things about the same
   * world depending on how wide a panel happens to be.
   */
  narrow: "minmax(0, 2.6fr) 46px minmax(0, 0.62fr) minmax(0, 0.6fr) minmax(0, 0.66fr) 30px",
} satisfies Record<TableWidth, string>;

/**
 * The short vocabulary, and the rule for it.
 *
 * Every one of these is a real abbreviation of a closed vocabulary — the
 * values are `MECHANICAL | SEMANTIC | DERIVED | ADJUDICATED` and
 * `BASE | DERIVED`, so `mech` cannot be mistaken for a different word the way
 * a clipped `mechan…` can be mistaken for nothing at all. The full word stays
 * on the element's `title`, so the long form is always one hover away.
 *
 * `n` for a count is the one that is not an abbreviation but a convention, and
 * it is the right one: the column is a number, and the header only has to say
 * which number.
 */
const SHORT: Record<string, string> = {
  mechanical: "mech",
  semantic: "sem",
  adjudicated: "adjud",
  derived: "deriv",
  purpose: "purp",
};

const HEADINGS = {
  wide: { count: "tuples", construction: "construction", stale: "stale" },
  narrow: { count: "n", construction: "constr.", stale: "stale" },
} satisfies Record<TableWidth, Record<string, string>>;

/** The short form when there is one and the table is narrow; the word itself otherwise. */
function say(word: string, width: TableWidth): string {
  return width === "narrow" ? (SHORT[word] ?? word) : word;
}

export function WorldTable({
  overview,
  relations,
  chrome,
  onOpen,
}: {
  overview: WorldOverview | null;
  relations: WorldRelation[];
  chrome: TableChrome;
  onOpen: (name: string) => void;
}) {
  const [query, setQuery] = useState("");
  const [placement, setPlacement] = useState("all");
  // Placement needs a referent to anchor to (workingSet.place).
  const rows = useMemo(() => relations.filter((item) => {
    const placeable = item.roles.some((role) => role.referent);
    return (!PLACEMENT_FILTER_ENABLED || placement === "all" || placeable === (placement === "placeable"))
      && item.name.toLowerCase().includes(query.trim().toLowerCase());
  }), [relations, query, placement]);
  const frame = useRef<HTMLElement>(null);
  const width = useTableWidth(frame);
  const columns = COLUMNS[width];
  const heading = HEADINGS[width];
  const window_ = useRowWindow(rows.length, ROW_HEIGHT, OVERSCAN);
  const { reset } = window_;
  useEffect(reset, [query, reset]);
  const meta = useMemo(() => {
    if (!overview) return "Reading world";
    const bits = [
      `${overview.relations} relation${overview.relations === 1 ? "" : "s"}`,
      `${overview.referents} referent${overview.referents === 1 ? "" : "s"}`,
      `rev ${overview.revision}`,
    ];
    if (overview.stale.length) bits.push(`${overview.stale.length} stale`);
    return bits.join(" · ");
  }, [overview]);

  return (
    <section
      className="table"
      aria-label="world relations"
      ref={frame}
      data-width={width}
    >
      <TableBar chrome={chrome} meta={meta} />
      <TableSearch value={query} onChange={setQuery} label="Search relations" />
      {PLACEMENT_FILTER_ENABLED && <div className="table__filters">
        <label>Field placement <select aria-label="Field placement" value={placement}
          onChange={(event) => setPlacement(event.target.value)}>
          <option value="all">All relations</option>
          <option value="placeable">Can place on field</option>
          <option value="other">Cannot place on field</option>
        </select></label>
        <span role="status">{rows.length} of {relations.length}</span>
      </div>}
      {!rows.length ? <p className="table__empty">No relations match this search.</p> : null}
      <div className="table__head" style={{ gridTemplateColumns: columns }}>
        <span>relation</span>
        <span title="tuples">{heading.count}</span>
        <span>scope</span>
        <span>mode</span>
        {/* `chipKind` is construction origin (mechanical/semantic/adjudicated),
            not `_world_assertions.origin` (asserted/derived) — bare "origin" sat
            one column from "mode", which can itself read "derived". Same word
            for two axes on one row; see styles/vocabulary.md §4. */}
        <span title="construction origin">{heading.construction}</span>
        <span>{heading.stale}</span>
      </div>
      <div
        className="table__scroll"
        ref={window_.ref}
        onScroll={window_.onScroll}
      >
        <div
          className="table__spacer"
          style={{ height: rows.length * ROW_HEIGHT }}
        >
          {window_.indices.map((index) => {
            const item = rows[index];
            if (!item) return null;
            return (
              <div
                key={item.name}
                className="table__row"
                {...still("rowsNeverFly")}
                data-loaded
                style={{
                  top: index * ROW_HEIGHT,
                  height: ROW_HEIGHT,
                  gridTemplateColumns: columns,
                }}
                role="button"
                tabIndex={0}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    onOpen(item.name);
                  }
                }}
                onClick={() => onOpen(item.name)}
              >
                <span title={item.name}>{item.name}</span>
                <span title={`${item.count}`}>{item.count}</span>
                <span
                  className="table__origin"
                  title={item.scope ? item.scope.toLowerCase() : undefined}
                >
                  {item.scope ? say(item.scope.toLowerCase(), width) : "—"}
                </span>
                <span className="table__origin" title={item.mode.toLowerCase()}>
                  {say(item.mode.toLowerCase(), width)}
                </span>
                <span className="table__origin" title={chipKind(item)}>
                  {say(chipKind(item), width)}
                </span>
                <span className="table__origin">
                  {item.stale ? "stale" : ""}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
