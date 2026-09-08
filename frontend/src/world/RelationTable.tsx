/**
 * A relation's extension, as a table.
 *
 * §11: do not choose between graph and table. The canvas holds neighborhoods —
 * a few dozen marks someone arranged to think with — and the table holds
 * extensions, which at this world's largest relation is thousands of tuples and
 * at a real one will be more. They are two projections of one relation state,
 * and the seam between them is a row: selecting one places its tuple on the
 * field, and a tuple already on the field is marked in the margin here. That is
 * the whole of the two-way binding, and it is enough.
 *
 * **Windowed, and paged from SQL.** Only the rows in view are in the DOM, and
 * only the pages the window has touched are in memory. The scroller is sized to
 * `total * ROW_HEIGHT` from the count the server already knows, so the bar is
 * honest about the size of the relation before a single row has arrived, and
 * scrolling to the middle of a ten-thousand-row relation fetches one page
 * rather than ten thousand rows. Rows not yet loaded draw as ruled blanks: the
 * table's shape never jumps as pages land.
 *
 * **Sorting is the database's.** Changing the order discards the buffer and
 * re-asks, because a sort applied to the pages you happen to hold is not a
 * sort. SQLite orders the largest relation here in well under a millisecond.
 *
 * No table library. What a grid needs is a fixed row height, a spacer, and a
 * slice — thirty lines that we control the type of — and what a library would
 * add on top is a second set of opinions about focus, keyboard and styling to
 * fight with the design language.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { worldApi, type WorldRelation, type WorldRole, type WorldTuple } from "../api/world";
import { still } from "../styles/motion";
import { ProblemNotice } from "./ProblemNotice";
import { useRowWindow } from "./rowWindow";
import { shortenIdentifier, useTableWidth } from "./tableWidth";
import { TableBar, type TableChrome } from "./tableChrome";

/** Fixed, because a windowed table needs to know where a row is without asking. */
const ROW_HEIGHT = 26;
const PAGE = 200;
/** Rows drawn above and below the viewport, so a fast scroll is not a white gap. */
const OVERSCAN = 8;

type Order = { role: string; desc: boolean } | null;

export function RelationTable({
  relation,
  subject,
  present,
  onFocus,
  onWiden,
  onDerivation,
  chrome,
}: {
  relation: WorldRelation;
  /**
   * The referent this extension was opened from, if it was opened from one.
   *
   * A referent's panel offers a relation by *its* count — "offered_by 608" —
   * so a table that then showed the relation's whole 1,208 would be answering
   * a question nobody asked. The server narrows and counts; the header says
   * which of the two things you are looking at.
   */
  subject?: { id: string; label: string } | null;
  /** Assertion ids already on the field, so a row can say it is there. */
  present: Set<string>;
  onFocus: (roles: WorldRole[], tuple: WorldTuple) => void;
  /** Drop the subject and read the whole extension. */
  onWiden: () => void;
  /** §8.6, from where you are actually standing when you want it. */
  onDerivation: () => void;
  chrome: TableChrome;
}) {
  const [order, setOrder] = useState<Order>(null);
  const [total, setTotal] = useState(subject ? 0 : relation.count);
  const [roles, setRoles] = useState<WorldRole[]>(relation.roles);
  const [pages, setPages] = useState<Map<number, WorldTuple[]>>(new Map());
  const [problem, setProblem] = useState<string | null>(null);
  const frame = useRef<HTMLElement>(null);
  const width = useTableWidth(frame);
  const window_ = useRowWindow(total, ROW_HEIGHT, OVERSCAN);
  const { first, last, reset } = window_;
  /** Pages already asked for, so a scroll does not re-ask on every frame. */
  const asked = useRef(new Set<number>());

  /**
   * What the buffer currently holds rows *of*.
   *
   * A page index only means something under one relation in one order, so this
   * is what a landing response is checked against — and it is the whole reason
   * the fetch below has no cleanup. Cancelling in-flight pages when the effect
   * re-runs looks right and is wrong here, because the effect re-runs on every
   * scroll: the first page was being discarded the instant the ResizeObserver
   * reported the real height, and since `asked` already held the index it was
   * never requested again. The table came up empty above whatever page you
   * scrolled to. A response is stale only when the thing it is a page of has
   * changed, which is exactly this key.
   */
  const buffer = `${relation.name}\u0000${subject?.id ?? ""}\u0000${order?.role ?? ""}\u0000${order?.desc ?? false}`;
  const bufferRef = useRef(buffer);
  const live = useRef(true);
  useEffect(() => {
    live.current = true;
    return () => {
      live.current = false;
    };
  }, []);

  // A new relation or a new order is a new table: the buffer cannot survive
  // either, since a page index means nothing once the ordering under it moves.
  useEffect(() => {
    bufferRef.current = buffer;
    asked.current = new Set();
    setPages(new Map());
    setProblem(null);
    reset();
  }, [buffer, reset]);

  // Fetch whatever page the window is standing on, and no other. `asked` is a
  // ref rather than state because wanting a page and holding it are different
  // facts, and only the second one should redraw anything.
  useEffect(() => {
    const wanted = new Set<number>();
    // A subject-narrowed table does not know its size until the first page
    // answers — the window is empty because `total` is zero, not because there
    // is nothing to read — so page zero is always worth one ask.
    if (!asked.current.has(0) && (!total || first === 0)) wanted.add(0);
    for (let page = Math.floor(first / PAGE); page <= Math.floor((last - 1) / PAGE); page += 1) {
      if (page >= 0 && !asked.current.has(page)) wanted.add(page);
    }
    if (!wanted.size) return;
    const asOf = buffer;
    const current = () => live.current && bufferRef.current === asOf;
    for (const page of wanted) {
      asked.current.add(page);
      worldApi
        .rows(relation.name, {
          limit: PAGE,
          offset: page * PAGE,
          order: order?.role ?? null,
          desc: order?.desc,
          subject: subject?.id ?? null,
        })
        .then((answer) => {
          if (!current()) return;
          setTotal(answer.total);
          setRoles(answer.roles);
          setPages((held) => new Map(held).set(page, answer.rows));
        })
        .catch((failure: Error) => {
          if (!current()) return;
          // Forgotten rather than remembered as asked, so scrolling back over
          // a page that failed retries it instead of leaving a permanent hole.
          asked.current.delete(page);
          setProblem(failure.message);
        });
    }
  }, [relation.name, subject, order, buffer, first, last, total]);

  const rowAt = useCallback(
    (index: number): WorldTuple | null =>
      pages.get(Math.floor(index / PAGE))?.[index % PAGE] ?? null,
    [pages],
  );

  const columns = useMemo(
    () => `${roles.map(() => "minmax(0, 1fr)").join(" ")} 84px`,
    [roles],
  );

  return (
    <section
      className="table"
      aria-label={`${relation.name} extension`}
      ref={frame}
      data-width={width}
    >
      <TableBar
        chrome={chrome}
        title={relation.name}
        meta={
          <>
            {total} tuple{total === 1 ? "" : "s"}
            {subject ? ` of ${subject.label}` : ""} · {relation.mode.toLowerCase()}
            {/* Printed only when the world recorded it. An absent admission
                document is not a claim of WORLD scope, and filling one in here
                would make the stronger claim on the world's behalf. */}
            {relation.scope ? ` · ${relation.scope.toLowerCase()}` : ""}
            {relation.stale ? " · stale" : ""}
            {relation.completeness && relation.completeness.status !== "COMPLETE"
              ? ` · ${relation.completeness.status.toLowerCase()}`
              : ""}
          </>
        }
      >
        {subject ? (
          <button type="button" onClick={onWiden}>
            whole relation
          </button>
        ) : null}
        {order ? (
          <button type="button" onClick={() => setOrder(null)}>
            unsort
          </button>
        ) : null}
        <button type="button" onClick={onDerivation}>
          dependencies
        </button>
      </TableBar>

      <div className="table__head" style={{ gridTemplateColumns: columns }}>
        {roles.map((role) => (
          <button
            key={role.name}
            type="button"
            data-sorted={order?.role === role.name ? (order.desc ? "desc" : "asc") : undefined}
            onClick={() =>
              setOrder((current) =>
                current?.role === role.name && !current.desc
                  ? { role: role.name, desc: true }
                  : current?.role === role.name
                    ? null
                    : { role: role.name, desc: false },
              )
            }
            title={role.name}
          >
            {width === "narrow" ? shortenIdentifier(role.name) : role.name}
            {order?.role === role.name ? (order.desc ? " ↓" : " ↑") : ""}
          </button>
        ))}
        <span>origin</span>
      </div>

      {problem ? <ProblemNotice message={problem} title="Unable to load relation" /> : null}

      <div className="table__scroll" ref={window_.ref} onScroll={window_.onScroll}>
        <div className="table__spacer" style={{ height: total * ROW_HEIGHT }}>
          {window_.indices.map((index) => {
            const tuple = rowAt(index);
            return (
              <div
                key={index}
                className="table__row"
                {...still("rowsNeverFly")}
                data-loaded={tuple ? true : undefined}
                data-present={tuple && present.has(tuple.assertion_id) ? true : undefined}
                style={{
                  top: index * ROW_HEIGHT,
                  height: ROW_HEIGHT,
                  gridTemplateColumns: columns,
                }}
                onClick={tuple ? () => onFocus(roles, tuple) : undefined}
              >
                {tuple
                  ? roles.map((role) => (
                      <span key={role.name} title={String(tuple.values[role.name] ?? "")}>
                        {display(tuple.values[role.name], role.referent)}
                      </span>
                    ))
                  : roles.map((role) => <span key={role.name} />)}
                <span className="table__origin">
                  {tuple ? tuple.origin.toLowerCase() : ""}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

/**
 * A cell.
 *
 * Referent ids arrive namespaced — `part:X160` — and the namespace repeats down
 * the whole column, so it is dropped from the referent columns and kept on the
 * cell's title, because an id you cannot read out of the table is an id you
 * cannot ask the rest of the product about. A scalar is printed as it is: a
 * colon inside a scalar is part of the value.
 */
function display(value: unknown, referent: boolean): string {
  if (value === null || value === undefined) return "—";
  const text = String(value);
  if (!referent) return text;
  const colon = text.indexOf(":");
  return colon > 0 ? text.slice(colon + 1) : text;
}
