/**
 * The spine — §5, and the rail of §4.
 *
 * Nine passes, their state, and what an intervention costs. Narrow,
 * persistent, secondary: it is a CI build page's stage list, and §3 is
 * explicit that the stage list is never the front door. The docket is.
 *
 * **State is reported, never conferred.** §5 gives four states and three of
 * them are structural — an absent artifact is FAILED, an intervention standing
 * upstream is STALE, an input that moved under a pass is PROVISIONAL. The
 * fourth, CERTIFIED, is the scorers' word, and where no scorer has spoken this
 * rail says `unscored` rather than filling in the blank. A spine that inferred
 * certification from a green tick would be the front end certifying passes,
 * which is the one thing §5 forbids it.
 *
 * State is carried by weight and rule, never by colour (§9): a filled bar is
 * certified, a hollow one unscored, a dashed one stale, a struck one failed.
 * The three status colours belong to the queue.
 *
 * Opening a pass states the cost of intervening there **before** anything is
 * triggered — which passes re-run, which survive, and how long it took last
 * time — and opens the corresponding frozen artifact in the body.
 */

import { useEffect, useState } from "react";
import { constructionApi, type Cost, type PassEntry } from "../api/construction";

/** The word for a state, including the one that is an absence. */
function stateWord(entry: PassEntry): string {
  if (!entry.ran) return "not run";
  if (entry.state) return entry.state.toLowerCase();
  return entry.scored === false ? "not passed" : "unscored";
}

/** Minutes, because a cost statement in seconds is a number nobody weighs. */
function duration(seconds: number | null): string {
  if (seconds === null) return "unmeasured";
  if (seconds < 90) return `${Math.round(seconds)}s`;
  return `about ${Math.round(seconds / 60)} min`;
}

function CostStatement({ cost }: { cost: Cost }) {
  return (
    <dl className="cost">
      <div>
        <dt>re-runs</dt>
        <dd>
          {cost.invalidates.length
            ? cost.invalidates.join(", ").toUpperCase()
            : "nothing downstream"}
        </dd>
      </div>
      <div>
        <dt>preserves</dt>
        <dd>
          {cost.preserves.join(", ").toUpperCase()}
          {/* The derivation program is authored, not derived. An adjudication
              recomputes P7's outputs and leaves its script alone, and saying so
              is the difference between a cheap intervention and one that reads
              as though it rewrites the pipeline. */}
          {cost.preserves_program ? ", and P7's derivation program" : ""}
        </dd>
      </div>
      <div>
        <dt>costs</dt>
        <dd>
          {duration(cost.seconds)}
          {cost.unmeasured.length ? ` · ${cost.unmeasured.length} unmeasured` : ""}
        </dd>
      </div>
    </dl>
  );
}

export function Spine({
  passes,
  open,
  selected,
  onSelect,
}: {
  passes: PassEntry[];
  /** Obligations still open. The one count worth carrying on the rail, because
   * P5 is where the measured failure is (§4's `P5 ⚠ 81`). */
  open: number | undefined;
  selected: string | null;
  onSelect: (pass: string | null) => void;
}) {
  const [cost, setCost] = useState<Cost | null>(null);

  useEffect(() => {
    if (!selected) {
      setCost(null);
      return;
    }
    let current = true;
    void constructionApi
      .cost(selected)
      .then((answer) => {
        if (current) setCost(answer);
      })
      .catch(() => {
        if (current) setCost(null);
      });
    return () => {
      current = false;
    };
  }, [selected]);

  return (
    <nav className="spine" aria-label="passes">
      <h2>spine</h2>
      <ol>
        {passes.map((entry) => {
          const chosen = entry.pass === selected;
          return (
            <li key={entry.pass}>
              <button
                type="button"
                className="spine__pass"
                data-state={entry.state ?? (entry.ran ? "unscored" : "absent")}
                data-selected={chosen || undefined}
                aria-expanded={chosen}
                onClick={() => onSelect(chosen ? null : entry.pass)}
              >
                <span className="spine__bar" aria-hidden="true" />
                <span className="spine__id">{entry.pass.toUpperCase()}</span>
                <span className="spine__state">{stateWord(entry)}</span>
                {entry.pass === "p5" && open ? (
                  <span className="spine__count">{open}</span>
                ) : null}
              </button>
              {chosen ? (
                <div className="spine__open">
                  {/* §2's third column. A stage list with no questions on it is
                      a progress bar, and §3 says this is not one. */}
                  <p className="spine__question">{entry.question}</p>
                  {entry.because.map((line) => (
                    <p key={line} className="spine__because">
                      {line}
                    </p>
                  ))}
                  <p className="spine__artifact">
                    {entry.artifact}
                    {entry.items !== undefined ? ` · ${entry.items} items` : ""}
                    {entry.seconds !== null ? ` · took ${duration(entry.seconds)}` : ""}
                  </p>
                  {cost && cost.at === entry.pass ? (
                    <>
                      <p className="spine__intervention">
                        {cost.intervention
                          ? `intervening here is an ${cost.intervention}`
                          : "no intervention is defined at this pass"}
                      </p>
                      <CostStatement cost={cost} />
                    </>
                  ) : null}
                </div>
              ) : null}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
