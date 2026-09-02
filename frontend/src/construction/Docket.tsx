/**
 * The docket — §8.1, the front door.
 *
 * One row per obligation, and the ordering is the server's. It is not a view
 * preference: "what does deciding this unblock" is a claim about the run,
 * read from P7's blocking premises against P3's demands, and a client that
 * re-sorted by arrival would be quietly disagreeing with the artifacts.
 *
 * Three lines per row, because a three-second decision needs three things:
 * what is being asked, what it holds up, and **the machine's own reason for
 * declining**. That last line is the whole design. A docket that made you open
 * an item to learn why it was declined would be a list of 81 identical rows.
 *
 * Nothing here is a status colour except status. Whether a person or the
 * machine decided is geometry — an outlined mark, a filled one, a rule above
 * it — because a construction origin encoded as colour is a fact that
 * disappears the first time the palette is retuned.
 */

import { useMemo, useState } from "react";
import type { Docket as DocketData, DocketRow } from "../api/construction";
import { useRowWindow } from "../world/rowWindow";

const ROW_HEIGHT = 62;

type Band = "blocking" | "open" | "all";

/** How the row's mark is drawn: who decided, not what was decided. */
export function markOf(row: DocketRow): "adjudicated" | "machine" | "undecided" {
  if (row.verdict) return "adjudicated";
  return row.disposition ? "machine" : "undecided";
}

function tuple(row: DocketRow): string {
  const values = row.values ?? {};
  const printed = Object.values(values).map((value) =>
    typeof value === "string" ? value : JSON.stringify(value),
  );
  return `${row.relation ?? "—"}(${printed.join(", ")})`;
}

/** What this obligation holds up, in one clause. */
function held(row: DocketRow): string {
  const { purposes, relations, blocking } = row.blocks;
  if (blocking) {
    return `blocks purpose ${purposes.join(", ")}`;
  }
  // A decided row's lists stay populated — they say what it *would* hold up —
  // so reporting them here would read as an outstanding claim on the world.
  if (!row.open) return "decided";
  return relations.length ? `holds ${relations.join(", ")}` : "non-blocking";
}

export function Docket({
  docket,
  selected,
  problem,
  onOpen,
}: {
  docket: DocketData | null;
  selected: string | null;
  problem: string | null;
  onOpen: (obligation_id: string) => void;
}) {
  const [band, setBand] = useState<Band>("open");
  const [relation, setRelation] = useState<string>("");

  const relations = useMemo(() => {
    const seen = new Set<string>();
    for (const row of docket?.obligations ?? []) {
      if (row.relation) seen.add(row.relation);
    }
    return [...seen].sort();
  }, [docket]);

  const rows = useMemo(() => {
    const all = docket?.obligations ?? [];
    return all.filter((row) => {
      if (relation && row.relation !== relation) return false;
      if (band === "blocking") return row.blocks.blocking;
      if (band === "open") return row.open;
      return true;
    });
  }, [docket, band, relation]);

  const window_ = useRowWindow(rows.length, ROW_HEIGHT, 6);
  const counts = docket?.counts;

  return (
    <section className="docket" aria-label="docket">
      <header className="docket__bar">
        <b>docket</b>
        <span>
          {counts
            ? `${counts.open} open · ${counts.decided} decided · ${counts.blocking} blocking a purpose`
            : "—"}
        </span>
      </header>

      <div className="docket__filters">
        {(["blocking", "open", "all"] as Band[]).map((option) => (
          <button
            key={option}
            type="button"
            data-active={band === option}
            onClick={() => setBand(option)}
          >
            {option}
          </button>
        ))}
        <select
          value={relation}
          onChange={(event) => setRelation(event.target.value)}
          aria-label="filter by relation"
        >
          <option value="">every relation</option>
          {relations.map((name) => (
            <option key={name} value={name}>
              {name}
            </option>
          ))}
        </select>
      </div>

      {problem ? <p className="docket__problem">{problem}</p> : null}

      <div className="docket__scroll" ref={window_.ref} onScroll={window_.onScroll}>
        <div className="docket__spacer" style={{ height: rows.length * ROW_HEIGHT }}>
          {window_.indices.map((index) => {
            const row = rows[index];
            if (!row) return null;
            const disposition = row.verdict?.disposition ?? row.disposition ?? "undecided";
            return (
              <button
                key={row.obligation_id}
                type="button"
                className="docket__row"
                style={{ top: index * ROW_HEIGHT, height: ROW_HEIGHT }}
                data-mark={markOf(row)}
                data-blocking={row.blocks.blocking || undefined}
                data-open={row.open || undefined}
                data-selected={row.obligation_id === selected || undefined}
                onClick={() => onOpen(row.obligation_id)}
              >
                <span className="docket__mark" aria-hidden="true" />
                <span className="docket__title">{tuple(row)}</span>
                <span className="docket__facts">
                  {disposition} · {held(row)} · {row.observations} observation
                  {row.observations === 1 ? "" : "s"}
                  {row.verdict ? ` · ${row.verdict.actor}` : ""}
                </span>
                {/* The machine's sentence, in its own words and in quotes,
                    because it is a quotation and not the surface's summary. */}
                <span className="docket__reason">
                  {row.rationale ? `“${row.rationale}”` : "no rationale recorded"}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {rows.length === 0 && !problem ? (
        <p className="docket__problem">
          Nothing in this band. The obligations are still there — the filter is
          hiding them.
        </p>
      ) : null}
    </section>
  );
}
