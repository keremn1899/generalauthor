/**
 * The transitions, on a bench.
 *
 * The motion tab plots the five curves; the component studio shows the marks.
 * Neither lets you watch a *transition happen*, which is the thing you are
 * actually tuning. Each specimen here is driven by the shipping primitive —
 * `Swap`, `presence.css`'s layers, `useArrivals`, `Waiting` — so what you are
 * timing is what the product will do.
 *
 * The bench also states the invariant it is built to demonstrate: every
 * specimen has a button, because **nothing moves that a person did not cause**.
 * The one exception is `flow`, and it is the machine making you wait.
 */

import { useState } from "react";
import { Swap } from "../styles/Swap";
import { useArrivals, usePresence } from "../styles/usePresence";
import { Waiting } from "../construction/Waiting";
import { STILL_RULES, type StillRule } from "../styles/motion";

const SUBJECTS = ["temperature_compatible", "eligible_part", "acceptable_replacement"];

export function LabTransitions() {
  const [subject, setSubject] = useState(0);
  const [noticeOn, setNoticeOn] = useState(false);
  const [rows, setRows] = useState<string[]>(["confirmed · j.mercer", "rejected · a.olu"]);
  const [waiting, setWaiting] = useState(false);
  const notice = usePresence(noticeOn);
  const arrived = useArrivals(rows, (row, index) => `${index}:${row}`);

  return (
    <div className="lab-bench">
      <section className="lab-bench__case">
        <header>
          <h4>Swap — a subject replaced</h4>
          <button type="button" onClick={() => setSubject((n) => (n + 1) % SUBJECTS.length)}>
            next subject
          </button>
        </header>
        <p className="lab-bench__note">
          The slot stays; what is in it is exchanged. Absorb ∘ emit — the
          outgoing copy is parked absolutely so the incoming one is not fighting
          a stacked twin.
        </p>
        <div className="lab-bench__stage">
          <Swap id={SUBJECTS[subject]}>
            <article className="lab-bench__card">
              <b>{SUBJECTS[subject]}</b>
              <span>derived · revision 16298</span>
            </article>
          </Swap>
        </div>
      </section>

      <section className="lab-bench__case">
        <header>
          <h4>Emit / absorb — a layer arriving</h4>
          <button type="button" onClick={() => setNoticeOn((on) => !on)}>
            {noticeOn ? "dismiss" : "raise a notice"}
          </button>
        </header>
        <p className="lab-bench__note">
          Rises by the field&apos;s travel — 8.6px — under the emit curve, and
          leaves faster than it came, because departing reads faster than
          arriving.
        </p>
        <div className="lab-bench__stage">
          {notice.mounted ? (
            <p
              className={`world__notice motion-layer motion-layer--rise${
                notice.shown ? " is-in" : ""
              }`}
            >
              eligible_part has 1211 tuples — more than the field holds.
            </p>
          ) : null}
        </div>
      </section>

      <section className="lab-bench__case">
        <header>
          <h4>Emit on the new row only</h4>
          <button
            type="button"
            onClick={() => setRows((r) => [...r, `confirmed · ${r.length}`])}
          >
            record a verdict
          </button>
        </header>
        <p className="lab-bench__note">
          The lines above it did not just happen. Animating them would restate
          the record every time someone decides something.
        </p>
        <div className="lab-bench__stage">
          <ol className="verdict__history">
            {rows.map((row, index) => (
              <li
                key={`${index}:${row}`}
                className={arrived.has(`${index}:${row}`) ? "motion-emit" : undefined}
              >
                {row}
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section className="lab-bench__case">
        <header>
          <h4>Flow — the only one</h4>
          <button type="button" onClick={() => setWaiting((w) => !w)}>
            {waiting ? "stop" : "record"}
          </button>
        </header>
        <p className="lab-bench__note">
          Bounded but indeterminate, so it is linear and says nothing about how
          far along it is. Nothing on the read plane qualifies — retrieval does
          not call a model — which is why this is the product&apos;s one flow.
        </p>
        <div className="lab-bench__stage">
          {waiting ? <Waiting label="recording" /> : null}
        </div>
      </section>

      <section className="lab-bench__case lab-bench__case--wide">
        <header>
          <h4>Still — what does not move, and why</h4>
        </header>
        <p className="lab-bench__note">
          The negative space, read from `STILL_RULES` rather than restated.
          `still(rule)` writes the citation onto the element and
          `presence.css` turns it into `transition: none`, so a transition added
          later is overridden rather than silently winning.
        </p>
        <dl className="lab-bench__rules">
          {(Object.keys(STILL_RULES) as StillRule[]).map((rule) => (
            <div key={rule}>
              <dt>{rule}</dt>
              <dd>{STILL_RULES[rule]}</dd>
            </div>
          ))}
        </dl>
      </section>
    </div>
  );
}
