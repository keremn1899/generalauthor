/**
 * One obligation, opened — §8.2. Three panes, no navigation between them.
 *
 * The proposition, the packet, the judgment. They are side by side rather than
 * stacked or tabbed because the decision is a comparison: what was asked,
 * against what was found, against what was concluded. A person who has to
 * navigate to see the second thing is a person deciding from memory.
 *
 * Two rules do most of the work here.
 *
 * **Evidence is cited by selection.** The citations are checkboxes over the
 * packet's own observations and there is no free-text location field, so a
 * verdict cannot rest on something the constructor never assembled. That is
 * enforced server-side; what this file does is make the enforced thing the
 * only visible affordance.
 *
 * **The burdens do not relax for a human.** A closing verdict needs at least
 * one citation and a support_claim. The form states the requirement and
 * disables the button — but it does not *enforce* it, and the difference
 * matters: the rule lives in `verdicts.py`, and this is a legible restatement
 * of it, not a second copy that could disagree.
 *
 * `known_missing_information` is given the same weight as what was found. It
 * is the constructor's own account of why it might be wrong, and burying it
 * would make the packet read as more complete than it is.
 *
 * **The cost is stated before the act, never after** (§5). An adjudication is
 * the cheap intervention — P0–P4 survive it and so does P7's derivation
 * program — and a person who cannot see that will hesitate over the one move
 * the measured failure actually needs. Recording still triggers nothing: it
 * stages a proposal, the spine goes stale, and running is a separate and
 * deliberate act (§11).
 */

import { useEffect, useMemo, useState } from "react";
import { constructionApi } from "../api/construction";
import { useArrivals } from "../styles/usePresence";
import { Waiting } from "./Waiting";
import type {
  Citation,
  Cost,
  OpenedObligation,
  Verdict,
} from "../api/construction";

/** The verdicts a person may record, in the order the burden changes: the
 * closing ones first, then the one that upholds a decline. */
const VERDICTS = [
  "SAME_ENTITY",
  "DISTINCT",
  "ACCEPT",
  "REJECT",
  "PRESENT",
  "ABSENT",
  "UNRESOLVED",
] as const;

/** The ones that carry the burden. Widened to `string` deliberately: the
 * set is asked about whatever is currently chosen, which may be nothing. */
const CLOSING: ReadonlySet<string> = new Set<string>(
  VERDICTS.filter((name) => name !== "UNRESOLVED"),
);

function key(citation: Citation): string {
  return `${citation.source_path}\0${citation.location}`;
}

/** The ledger stores UTC ISO, which is the right thing to store and the wrong
 * thing to read. Rendered in local time, and left exactly as stored if a
 * browser will not parse it: a timestamp is evidence, and a prettier invented
 * one would be worse than an ugly true one. */
function when(at: string): string {
  const moment = new Date(at);
  return Number.isNaN(moment.getTime()) ? at : moment.toLocaleString();
}

/** A cost in minutes. Seconds are a number nobody weighs. */
function costWords(cost: Cost): string {
  if (cost.seconds === null) return "unmeasured";
  return cost.seconds < 90
    ? `about ${Math.round(cost.seconds)}s`
    : `about ${Math.round(cost.seconds / 60)} min`;
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="pane__field">
      <dt>{label}</dt>
      <dd>{children ?? "—"}</dd>
    </div>
  );
}

export function Obligation({
  opened,
  actor,
  history,
  busy,
  problem,
  onAdjudicate,
  onRevert,
  onActor,
}: {
  opened: OpenedObligation;
  actor: string;
  history: Verdict[];
  busy: boolean;
  problem: string | null;
  onAdjudicate: (proposal: {
    disposition: string;
    supporting_evidence: Citation[];
    support_claim: string;
  }) => void;
  onRevert: () => void;
  onActor: (actor: string) => void;
}) {
  const [disposition, setDisposition] = useState<string>("");
  const [cited, setCited] = useState<Set<string>>(new Set());
  const [claim, setClaim] = useState("");

  // A new obligation is a new decision. Carrying a half-typed claim across
  // would be the one bug in this file that could file evidence against the
  // wrong proposition.
  useEffect(() => {
    setDisposition("");
    setCited(new Set());
    setClaim("");
  }, [opened.obligation_id]);

  const observations = opened.packet?.selected_observations ?? [];
  const citations = useMemo(
    () =>
      observations
        .filter((observation) => cited.has(key(observation)))
        .map((observation) => ({
          source_path: observation.source_path,
          location: observation.location,
        })),
    [observations, cited],
  );

  const closing = CLOSING.has(disposition);
  /* A recorded verdict is appended to a record already on screen, so only
     the new line arrives. The ones above it did not just happen. */
  const arrived = useArrivals(history, (entry, index) => `${entry.at}:${index}`);
  const unmet = !disposition
    ? "choose a verdict"
    : closing && citations.length === 0
      ? `${disposition} needs at least one cited location`
      : closing && !claim.trim()
        ? `${disposition} needs a claim: what the cited evidence establishes`
        : !actor.trim()
          ? "a verdict is someone's — name yourself"
          : null;

  const machine = opened.judgment;
  const standing = opened.verdict;

  // Fetched once for the surface, not per keystroke: the cost of adjudicating
  // is a fact about the run, the same for every obligation, and it does not
  // move while someone is choosing a verdict.
  const [cost, setCost] = useState<Cost | null>(null);
  useEffect(() => {
    let current = true;
    void constructionApi
      .cost("p5")
      .then((answer) => current && setCost(answer))
      .catch(() => current && setCost(null));
    return () => {
      current = false;
    };
  }, []);

  return (
    <section className="obligation" aria-label={opened.obligation_id}>
      <header className="obligation__bar">
        <b>{opened.obligation_id}</b>
        <span>
          {opened.proposition.relation} ·{" "}
          {opened.blocks.blocking
            ? `blocks purpose ${opened.blocks.purposes.join(", ")}`
            : opened.blocks.relations.length
              ? `holds ${opened.blocks.relations.join(", ")}`
              : "non-blocking"}
        </span>
      </header>

      <div className="obligation__panes">
        {/* -- the proposition ------------------------------------------- */}
        <article className="pane">
          <h3>the proposition</h3>
          <dl>
            <Field label="relation">{opened.proposition.relation}</Field>
            <Field label="values">
              <ul className="pane__values">
                {Object.entries(opened.proposition.values ?? {}).map(([role, value]) => (
                  <li key={role}>
                    <i>{role}</i>
                    <span>{typeof value === "string" ? value : JSON.stringify(value)}</span>
                  </li>
                ))}
              </ul>
            </Field>
            <Field label="why demanded">{opened.proposition.why_demanded}</Field>
            <Field label="required by">
              {opened.proposition.required_by.join(", ") || "—"}
            </Field>
            <Field label="current state">{opened.proposition.state}</Field>
          </dl>
        </article>

        {/* -- the packet ------------------------------------------------ */}
        <article className="pane">
          <h3>the packet</h3>
          {opened.packet ? (
            <>
              <ul className="pane__observations">
                {observations.map((observation) => {
                  const id = key(observation);
                  return (
                    <li key={id}>
                      <label>
                        <input
                          type="checkbox"
                          checked={cited.has(id)}
                          onChange={(event) =>
                            setCited((previous) => {
                              const next = new Set(previous);
                              if (event.target.checked) next.add(id);
                              else next.delete(id);
                              return next;
                            })
                          }
                        />
                        <b>
                          {observation.source_path}:{observation.location}
                        </b>
                      </label>
                      {observation.excerpt ? <q>{observation.excerpt}</q> : null}
                    </li>
                  );
                })}
                {observations.length === 0 ? (
                  <li className="pane__empty">
                    The packet selected no observations. That is the
                    constructor's account, not a gap in this view.
                  </li>
                ) : null}
              </ul>
              <dl>
                <Field label="selection rationale">
                  {opened.packet.selection_rationale}
                </Field>
              </dl>
              {/* Not a footnote. This is the constructor saying what it knows
                  it did not have. */}
              <p className="pane__missing">
                <i>known missing</i>
                {opened.packet.known_missing_information ?? "nothing recorded"}
              </p>
            </>
          ) : (
            <p className="pane__empty">
              P4 assembled no packet for this obligation. No evidence was
              gathered — which is a different fact from evidence that found
              nothing, and there is nothing here a verdict could cite.
            </p>
          )}
        </article>

        {/* -- the judgment ---------------------------------------------- */}
        <article className="pane">
          <h3>the judgment</h3>
          <dl>
            <Field label="machine">{machine?.disposition ?? "undecided"}</Field>
            {machine?.original_disposition &&
            machine.original_disposition !== machine.disposition ? (
              // The constructor's audit of itself: it proposed a closure and
              // its own verifier would not support it. This pair is the most
              // common shape of the under-closure this docket exists for.
              <Field label="downgraded from">
                {machine.original_disposition} · verifier said{" "}
                {machine.verification_result ?? "—"}
              </Field>
            ) : null}
            <Field label="rationale">{machine?.rationale}</Field>
          </dl>

          {standing ? (
            <div className="verdict verdict--standing" data-mark="adjudicated">
              <h4>your verdict</h4>
              <p className="verdict__what">
                <b>{standing.disposition}</b>
                {standing.supersedes ? ` · supersedes ${standing.supersedes}` : null}
              </p>
              <p>{standing.support_claim}</p>
              <ul className="verdict__cites">
                {(standing.supporting_evidence ?? []).map((citation) => (
                  <li key={key(citation)}>
                    {citation.source_path}:{citation.location}
                  </li>
                ))}
              </ul>
              <p className="verdict__who">
                {standing.actor} · {when(standing.at)}
              </p>
              <button type="button" onClick={onRevert} disabled={busy}>
                revert
              </button>
              {busy ? <Waiting label="withdrawing" /> : null}
            </div>
          ) : (
            <div className="verdict">
              <h4>your verdict</h4>
              <div className="verdict__choices">
                {VERDICTS.map((name) => (
                  <button
                    key={name}
                    type="button"
                    data-active={disposition === name}
                    onClick={() => setDisposition(disposition === name ? "" : name)}
                  >
                    {name}
                  </button>
                ))}
              </div>
              <label className="verdict__claim">
                <span>support claim</span>
                <textarea
                  value={claim}
                  rows={3}
                  placeholder="What do the cited locations establish?"
                  onChange={(event) => setClaim(event.target.value)}
                />
              </label>
              <label className="verdict__actor">
                <span>actor</span>
                <input
                  value={actor}
                  onChange={(event) => onActor(event.target.value)}
                  placeholder="who is deciding"
                />
              </label>
              <p className="verdict__cited">
                {citations.length
                  ? `citing ${citations.map((c) => `${c.source_path}:${c.location}`).join(", ")}`
                  : "citing nothing — select locations in the packet"}
              </p>
              {/* Before the button, not after it. §11: this stages a
                  proposal and re-runs nothing — what it costs is what a
                  rebuild would cost, and that is the number worth knowing
                  while the verdict is still a draft. */}
              {cost ? (
                <p className="verdict__cost">
                  Recording stages a proposal and re-runs nothing. A rebuild
                  from here restages {cost.invalidates.join(", ").toUpperCase()}{" "}
                  — {costWords(cost)} — and preserves{" "}
                  {cost.preserves.join(", ").toUpperCase()}
                  {cost.preserves_program ? " and P7's derivation program" : ""}.
                </p>
              ) : null}
              <div className="verdict__commit">
                <button
                  type="button"
                  disabled={Boolean(unmet) || busy}
                  onClick={() =>
                    onAdjudicate({
                      disposition,
                      supporting_evidence: citations,
                      support_claim: claim,
                    })
                  }
                >
                  record
                </button>
                {unmet ? <span className="verdict__unmet">{unmet}</span> : null}
              </div>
              {busy ? <Waiting label="recording" /> : null}
              {problem ? <p className="verdict__problem">{problem}</p> : null}
            </div>
          )}

          {history.length > 1 || (history.length === 1 && !standing) ? (
            // Every verdict ever recorded here, reverted ones included. §6.4:
            // there are no silent edits, so the withdrawn ones are part of the
            // record rather than an embarrassment to hide.
            <ol className="verdict__history">
              {history.map((entry, index) => (
                <li
                  key={`${entry.at}:${index}`}
                  className={arrived.has(`${entry.at}:${index}`) ? "motion-emit" : undefined}
                >
                  {entry.kind === "REVERT"
                    ? `reverted ${entry.reverts}`
                    : entry.disposition}{" "}
                  · {entry.actor} · {when(entry.at)}
                </li>
              ))}
            </ol>
          ) : null}
        </article>
      </div>
    </section>
  );
}
