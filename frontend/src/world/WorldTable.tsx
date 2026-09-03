/**
 * The world's own catalogue — idle body of the TABLES dock.
 *
 * Overview counts belong in the bar (what this world is). Rows are relations:
 * name, size, mode, construction origin, stale. Clicking one opens that
 * relation's extension in the same panel. The frontier is a sibling subject,
 * not a row, because unresolved is not a property of the world.
 */

import { useMemo } from "react";
import type { WorldOverview, WorldRelation } from "../api/world";
import { still } from "../styles/motion";
import { useRowWindow } from "./rowWindow";
import { chipKind } from "./schemaGraph";
import { TableBar, type TableChrome } from "./tableChrome";

const ROW_HEIGHT = 26;
const OVERSCAN = 8;
const COLUMNS = "minmax(0, 1.6fr) 72px 84px minmax(0, 1fr) 72px";

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
  const window_ = useRowWindow(relations.length, ROW_HEIGHT, OVERSCAN);
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
    <section className="table" aria-label="world relations">
      <TableBar chrome={chrome} meta={meta} />
      <div className="table__head" style={{ gridTemplateColumns: COLUMNS }}>
        <span>relation</span>
        <span>tuples</span>
        <span>mode</span>
        <span>origin</span>
        <span>stale</span>
      </div>
      <div
        className="table__scroll"
        ref={window_.ref}
        onScroll={window_.onScroll}
      >
        <div
          className="table__spacer"
          style={{ height: relations.length * ROW_HEIGHT }}
        >
          {window_.indices.map((index) => {
            const item = relations[index];
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
                  gridTemplateColumns: COLUMNS,
                }}
                onClick={() => onOpen(item.name)}
              >
                <span title={item.name}>{item.name}</span>
                <span>{item.count}</span>
                <span className="table__origin">{item.mode.toLowerCase()}</span>
                <span className="table__origin">{chipKind(item)}</span>
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
