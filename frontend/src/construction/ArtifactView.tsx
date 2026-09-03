/**
 * The artifact reading views — constructor spec §8.3–§8.7.
 *
 * These are projections of frozen pass documents, not editors. The sole write
 * is P6's admission proposal, recorded beside the run and made visibly
 * provisional here; it never changes the card's source artifact.
 */

import { useEffect, useMemo, useState } from "react";
import {
  constructionApi,
  type AdmissionProposal,
  type DocketRow,
  type IntakeAccount,
  type PassArtifact,
} from "../api/construction";
import { Swap } from "../styles/Swap";
import { markOf } from "./Docket";
import { Waiting } from "./Waiting";
import { tokenFromLocation } from "../api/plane";

type Json = Record<string, unknown>;

function object(value: unknown): Json {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Json)
    : {};
}

function list(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function hasObjectKey(value: unknown, key: string): boolean {
  if (Array.isArray(value)) return value.some((item) => hasObjectKey(item, key));
  if (!value || typeof value !== "object") return false;
  return Object.entries(value as Json).some(
    ([name, item]) => name === key || hasObjectKey(item, key),
  );
}

function words(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return JSON.stringify(value);
}

function worldHref(relation?: string): string {
  const query = new URLSearchParams();
  const token = tokenFromLocation();
  if (token) query.set("apiToken", token);
  if (relation) query.set("relation", relation);
  const suffix = query.toString();
  return `#/world${suffix ? `?${suffix}` : ""}`;
}

function StringList({ values }: { values: unknown }) {
  const items = list(values);
  if (!items.length) return <p className="artifact__absent">none recorded</p>;
  return (
    <ul className="artifact__list">
      {items.map((item, index) => (
        <li key={`${words(item)}-${index}`}>{words(item)}</li>
      ))}
    </ul>
  );
}

/** A scalar reads as a sentence; a list reads as a list.
 *
 * `words` falls back to `JSON.stringify`, which is the right last resort for a
 * shape nobody anticipated and the wrong first answer for the two shapes these
 * artifacts are mostly made of. P1's roles are the clearest case: a named typed
 * role is the frozen calculus, and rendering it as `[{"name":…,"type":…}]`
 * hands the reviewer the punctuation and makes them do the parsing. */
function Value({ value }: { value: unknown }) {
  if (!Array.isArray(value)) {
    const scalar = value === null || typeof value !== "object";
    if (scalar) return <>{words(value)}</>;
    return (
      <span className="artifact__pairs">
        {Object.entries(object(value)).map(([key, item]) => (
          <span key={key} className="artifact__pair">
            <i>{key.replaceAll("_", " ")}</i>
            <Value value={item} />
          </span>
        ))}
      </span>
    );
  }
  if (!value.length) return <span className="artifact__absent">none recorded</span>;
  // Short scalars — purpose letters, clause kinds — are a set, and a set reads
  // as a run. Bullets are for items long enough to need their own line.
  const terse = value.every(
    (item) => item !== null && typeof item !== "object" && words(item).length <= 32,
  );
  if (terse) {
    return (
      <span className="artifact__terms">
        {value.map((item, index) => (
          <span key={index}>{words(item)}</span>
        ))}
      </span>
    );
  }
  return (
    <ul className="artifact__list">
      {value.map((item, index) => (
        <li key={index}>
          <Value value={item} />
        </li>
      ))}
    </ul>
  );
}

function Field({ name, value }: { name: string; value: unknown }) {
  return (
    <div className="artifact__field">
      <dt>{name.replaceAll("_", " ")}</dt>
      <dd>
        <Value value={value} />
      </dd>
    </div>
  );
}

function JsonFields({ value, omit = [] }: { value: unknown; omit?: string[] }) {
  const document = object(value);
  return (
    <dl className="artifact__fields">
      {Object.entries(document)
        .filter(([key]) => !omit.includes(key))
        .map(([key, item]) => (
          <Field key={key} name={key} value={item} />
        ))}
    </dl>
  );
}

function Brief({ contract }: { contract: Json }) {
  const purposes = object(contract.purposes);
  const [selected, setSelected] = useState(Object.keys(purposes)[0] ?? "");
  const purpose = object(purposes[selected]);

  return (
    <div className="artifact__columns artifact__columns--brief">
      <section className="artifact__column">
        <h3>source purpose</h3>
        <p className="artifact__finding">
          The source purpose file was not copied into P0&apos;s frozen workspace
          snapshot. This run can show the compiled contract, but cannot prove
          from its own artifact whether compilation dropped or invented text.
        </p>
        <p className="artifact__absent">source unavailable in this run</p>
      </section>
      <section className="artifact__column">
        <header className="artifact__columnbar">
          <h3>compiled contract</h3>
          <select value={selected} onChange={(event) => setSelected(event.target.value)}>
            {Object.keys(purposes).map((name) => (
              <option key={name} value={name}>purpose {name}</option>
            ))}
          </select>
        </header>
        <h4>{words(purpose.objective)}</h4>
        <JsonFields value={purpose} omit={["objective"]} />
      </section>
    </div>
  );
}

type VocabularyRelation = Json & {
  name?: string;
  required_by?: string[];
  construction_class?: string;
};

function relationClaims(relations: VocabularyRelation[], purpose: string) {
  return relations.filter((relation) =>
    list(relation.required_by).map(String).includes(purpose),
  );
}

function Vocabulary({ vocabulary, contract }: { vocabulary: Json; contract: Json }) {
  const relations = list(vocabulary.relations).map(object) as VocabularyRelation[];
  const purposes = object(contract.purposes);
  const [filter, setFilter] = useState("");
  const shown = relations.filter((relation) =>
    words(relation.name).toLowerCase().includes(filter.toLowerCase()),
  );

  return (
    <div className="artifact__review">
      <section className="artifact__requirements">
        <header className="artifact__sectionbar">
          <h3>purpose distinctions</h3>
          <span>claim is purpose-level; the artifacts record no finer mapping</span>
        </header>
        {Object.entries(purposes).map(([purposeName, rawPurpose]) => {
          const distinctions = object(object(rawPurpose).required_semantic_distinctions);
          const claims = relationClaims(relations, purposeName);
          return (
            <div className="artifact__purpose" key={purposeName}>
              <h4>purpose {purposeName}</h4>
              {Object.entries(distinctions).flatMap(([kind, entries]) =>
                list(entries).map((entry, index) => (
                  <article
                    className="artifact__distinction"
                    data-missing={!claims.length || undefined}
                    key={`${kind}-${index}`}
                  >
                    <b>{kind.replaceAll("_", " ")}</b>
                    <p>{words(entry)}</p>
                    <span>
                      {claims.length
                        ? `${claims.length} relation${claims.length === 1 ? "" : "s"} claim purpose ${purposeName}`
                        : "no relation claims this purpose"}
                    </span>
                  </article>
                )),
              )}
            </div>
          );
        })}
      </section>

      <section className="artifact__relations">
        <header className="artifact__sectionbar">
          <h3>relations</h3>
          <input
            value={filter}
            onChange={(event) => setFilter(event.target.value)}
            placeholder="find a relation"
            aria-label="find a relation"
          />
        </header>
        {shown.map((relation) => {
          const semantic = relation.construction_class === "SEMANTIC";
          return (
            <article className="relation-card" key={words(relation.name)}>
              <header>
                <h4>{words(relation.name)}</h4>
                <span>{words(relation.construction_class)} · {words(relation.admission)}</span>
              </header>
              <p>{words(relation.meaning)}</p>
              <dl>
                <Field name="roles" value={relation.roles} />
                <Field name="required by" value={relation.required_by} />
                <Field name="grounding contract" value={relation.grounding_contract} />
                <Field name="construction rule" value={relation.construction_rule} />
              </dl>
              {semantic ? (
                <details>
                  <summary>RelationContract</summary>
                  <JsonFields
                    value={relation}
                    omit={[
                      "name", "meaning", "admission", "construction_class",
                      "required_by", "grounding_contract", "construction_rule",
                    ]}
                  />
                </details>
              ) : null}
              <a href={worldHref(words(relation.name))}>
                open extension in World
              </a>
            </article>
          );
        })}
      </section>
    </div>
  );
}

function Intake({ report, intake }: { report: Json; intake: IntakeAccount | null | undefined }) {
  return (
    <div className="artifact__review artifact__review--intake">
      <section>
        <h3>coverage</h3>
        <div className="artifact__metrics">
          {(["referents", "base_tuples", "candidate_tuples"] as const).map((name) => (
            <div key={name}><b>{words(report[name])}</b><span>{name.replaceAll("_", " ")}</span></div>
          ))}
        </div>
        <h3>compiler notes</h3>
        <StringList values={report.notes} />
      </section>
      <section>
        <h3>grounding completeness</h3>
        {intake ? (
          <>
            <p className="artifact__grounding" data-complete={intake.complete || undefined}>
              <b>{intake.grounded} of {intake.base_assertions}</b> BASE assertions have a SOURCE grounding.
            </p>
            {intake.ungrounded.length ? (
              <ul className="artifact__findings">
                {intake.ungrounded.map((item) => (
                  <li key={item.assertion_id}>{item.relation} · {item.assertion_id}</li>
                ))}
              </ul>
            ) : <p className="artifact__absent">no ungrounded BASE tuple found</p>}
            <h3>sources and contribution</h3>
            <p className="artifact__absent">
              The frozen P2 workspace has no source inventory. Contributions
              are countable; a source that contributed nothing is not.
            </p>
            <table className="artifact__table">
              <thead><tr><th>source</th><th>BASE assertions</th></tr></thead>
              <tbody>
                {intake.sources.map((source) => (
                  <tr key={source.source}><td>{source.source}</td><td>{source.assertions}</td></tr>
                ))}
              </tbody>
            </table>
          </>
        ) : (
          <p className="artifact__finding">P2 wrote no readable mechanical World from which to audit grounding.</p>
        )}
      </section>
    </div>
  );
}

type AdmissionRecord = Json & { name?: string; admission?: "WORLD" | "PURPOSE" };

function AdmissionCard({
  record,
  column,
  proposal,
  appearsInOutput,
  actor,
  busy,
  onAdmit,
  onWithdraw,
}: {
  record: AdmissionRecord;
  column: "WORLD" | "PURPOSE";
  proposal: AdmissionProposal | undefined;
  appearsInOutput: boolean;
  actor: string;
  busy: boolean;
  onAdmit: (
    record: AdmissionRecord,
    target: "WORLD" | "PURPOSE",
    reason: string,
    test: string,
  ) => Promise<void>;
  onWithdraw: (record: AdmissionRecord) => Promise<void>;
}) {
  const [editing, setEditing] = useState(false);
  const [reason, setReason] = useState("");
  const [test, setTest] = useState("");
  /* The form and the actions row are one slot with two subjects, so this is
     REPLACED rather than an arrival next to a departure. `Swap` parks the
     outgoing copy absolutely, which is also what keeps the card from doubling
     in height for the length of the change. */
  const name = words(record.name);
  const target = column === "WORLD" ? "PURPOSE" : "WORLD";
  // Named, not merely disabled. A dead button is a puzzle; the obligation
  // surface says which burden is unmet and this one owes the same answer.
  const unmet = !actor.trim()
    ? "a proposal is someone's — name yourself"
    : !reason.trim()
      ? `moving ${name} to ${target} needs a reason`
      : !test.trim()
        ? "record the purpose-independence test you applied"
        : null;
  return (
    <article
      className="admission-card"
      data-finding={column === "WORLD" && appearsInOutput || undefined}
    >
      <header><h4>{name}</h4><span>{words(record.construction_class)}</span></header>
      {proposal ? <p className="admission-card__proposal">proposed by {proposal.actor} · artifact says {words(record.admission)}</p> : null}
      {column === "WORLD" && appearsInOutput ? (
        <p className="artifact__finding">
          Finding: this WORLD relation&apos;s name also appears in a P8 output shape.
        </p>
      ) : null}
      <p>{words(proposal?.reason ?? record.reason)}</p>
      <details><summary>purpose-independence test</summary><p>{words(proposal?.purpose_independence_test ?? record.purpose_independence_test)}</p></details>
      <Swap id={editing ? "editing" : "resting"}>
      {editing ? (
        <div className="admission-card__form">
          <label>
            reason for moving to {target}
            <textarea value={reason} onChange={(event) => setReason(event.target.value)} />
          </label>
          <label>
            purpose-independence test you applied
            <textarea value={test} onChange={(event) => setTest(event.target.value)} />
          </label>
          <div>
            <button
              type="button"
              disabled={Boolean(unmet) || busy}
              onClick={() => void onAdmit(record, target, reason, test)}
            >
              record proposal
            </button>
            <button type="button" disabled={busy} onClick={() => setEditing(false)}>cancel</button>
            {unmet ? <span className="verdict__unmet">{unmet}</span> : null}
          </div>
          {busy ? <Waiting label="proposing" /> : null}
        </div>
      ) : (
        <div className="admission-card__actions">
          <button type="button" disabled={busy || !actor.trim()} onClick={() => setEditing(true)}>
            propose {target}
          </button>
          {proposal ? (
            // §6.4: every intervention has a backward path. Without this one an
            // admission was one-way — P7 and P8 stayed stale for the life of
            // the run, and proposing the artifact's value again would not undo
            // it, because a standing proposal is still an intervention.
            <button type="button" disabled={busy || !actor.trim()} onClick={() => void onWithdraw(record)}>
              withdraw
            </button>
          ) : null}
        </div>
      )}
      </Swap>
    </article>
  );
}

function AdmissionGate({
  document,
  outputs,
  proposals,
  actor,
  busy,
  onAdmit,
  onWithdraw,
}: {
  document: Json;
  outputs: Record<string, unknown>;
  proposals: Record<string, AdmissionProposal>;
  actor: string;
  busy: boolean;
  onAdmit: (
    record: AdmissionRecord,
    target: "WORLD" | "PURPOSE",
    reason: string,
    test: string,
  ) => Promise<void>;
  onWithdraw: (record: AdmissionRecord) => Promise<void>;
}) {
  const relations = list(document.relations).map(object) as AdmissionRecord[];
  const appearsInOutput = (name: string) => hasObjectKey(outputs, name);
  const effective = (record: AdmissionRecord) =>
    proposals[words(record.name)]?.admission ?? record.admission ?? "PURPOSE";

  return (
    <div className="admission-gate">
      {(["WORLD", "PURPOSE"] as const).map((column) => (
        <section key={column}>
          <header><h3>{column}</h3><span>{relations.filter((item) => effective(item) === column).length}</span></header>
          {relations.filter((item) => effective(item) === column).map((record) => {
            const name = words(record.name);
            const proposal = proposals[name];
            return (
              <AdmissionCard
                key={name}
                record={record}
                column={column}
                proposal={proposal}
                appearsInOutput={appearsInOutput(name)}
                actor={actor}
                busy={busy}
                onAdmit={onAdmit}
                onWithdraw={onWithdraw}
              />
            );
          })}
        </section>
      ))}
    </div>
  );
}

function outputRows(document: Json): { label: string; rows: unknown[] } {
  const entry = Object.entries(document).find(([key, value]) => key !== "purpose" && Array.isArray(value));
  return entry ? { label: entry[0], rows: entry[1] as unknown[] } : { label: "rows", rows: [] };
}

/** The premise obligations behind one purpose answer, and who decided each.
 *
 * §15's provenance case: opening a purpose output must reach, in finite
 * clicks, the human verdicts it rests on — and distinguish them from the
 * machine's. A count does neither. The rows come from the docket rather than
 * from P3 because the docket row is the one that carries the standing verdict,
 * and the mark is the docket's own geometry for exactly this distinction. */
function Premises({
  rows,
  onOpen,
}: {
  rows: DocketRow[];
  onOpen: (id: string) => void;
}) {
  if (!rows.length) return <p className="artifact__absent">No premise obligation names this purpose.</p>;
  const human = rows.filter((row) => row.verdict).length;
  return (
    <div className="premises">
      <p className="premises__account">
        {rows.length} premise obligation{rows.length === 1 ? "" : "s"} name this
        purpose{human ? `, ${human} decided by a person` : ", none decided by a person"}.
      </p>
      <ul>
        {rows.map((row) => (
          <li key={row.obligation_id} data-mark={markOf(row)}>
            <button type="button" onClick={() => onOpen(row.obligation_id)}>
              <span className="docket__mark" aria-hidden="true" />
              <b>{row.obligation_id}</b>
              <span>{row.relation ?? "—"}</span>
              {/* Both dispositions, never one in place of the other. §6.4: the
                  machine's judgment stays readable under the human's, because
                  the disagreement is the record worth having. */}
              <span className="premises__disposition">
                {row.verdict
                  ? `${row.verdict.disposition} by ${row.verdict.actor}`
                  : row.disposition ?? "undecided"}
              </span>
              {row.verdict && row.verdict.supersedes ? (
                <span className="premises__superseded">
                  machine said {row.verdict.supersedes}
                </span>
              ) : null}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Answers({
  outputs,
  derivations,
  rows: docketRows,
  onOpenObligation,
}: {
  outputs: Record<string, unknown>;
  derivations: Json;
  rows: DocketRow[];
  onOpenObligation: (id: string) => void;
}) {
  const [selected, setSelected] = useState(Object.keys(outputs)[0] ?? "");
  const document = object(outputs[selected]);
  const rows = outputRows(document);
  const derivation = list(derivations.derivations).map(object).find(
    (item) => words(item.output_relation).toLowerCase() === `purpose_ir/${selected.toLowerCase()}/output.json`,
  );
  const demanded = docketRows.filter((row) =>
    row.required_by.map((value) => value.toUpperCase()).includes(selected.toUpperCase()),
  );

  return (
    <div className="answers">
      <header className="artifact__sectionbar">
        <h3>purpose answer</h3>
        <select value={selected} onChange={(event) => setSelected(event.target.value)}>
          {Object.keys(outputs).map((name) => <option key={name} value={name}>purpose {name.toUpperCase()}</option>)}
        </select>
      </header>
      <div className="answers__account">
        <div><b>{rows.rows.length}</b><span>{rows.label}</span></div>
        <div><b>{demanded.length}</b><span>premise obligations</span></div>
        <div><b>{words(document.purpose)}</b><span>declared shape</span></div>
      </div>
      {rows.rows.length ? (
        <ol className="answer-rows">
          {rows.rows.map((row, index) => (
            <li key={index}>
              <JsonFields value={row} />
              <details>
                <summary>derivation and obligations</summary>
                {derivation ? <JsonFields value={derivation} /> : <p className="artifact__absent">no matching P7 derivation</p>}
                <Premises rows={demanded} onOpen={onOpenObligation} />
                <p className="artifact__absent">The run records relation-level derivation, not row lineage; this is the strongest link the frozen artifacts support.</p>
              </details>
            </li>
          ))}
        </ol>
      ) : (
        <div className="answer-rows__empty">
          <p>This answer contains no rows.</p>
          {derivation ? <JsonFields value={derivation} /> : null}
          <Premises rows={demanded} onOpen={onOpenObligation} />
        </div>
      )}
    </div>
  );
}

export function ArtifactView({
  pass,
  actor,
  rows,
  onActor,
  onClose,
  onChanged,
  onOpenObligation,
}: {
  pass: string;
  actor: string;
  rows: DocketRow[];
  onActor: (actor: string) => void;
  onClose: () => void;
  onChanged: () => Promise<void>;
  onOpenObligation: (id: string) => void;
}) {
  const [artifacts, setArtifacts] = useState<Record<string, PassArtifact>>({});
  const [proposals, setProposals] = useState<Record<string, AdmissionProposal>>({});
  const [problem, setProblem] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const needed = useMemo(() => {
    if (pass === "p1") return ["p0", "p1"];
    if (pass === "p6") return ["p6", "p8"];
    if (pass === "p8") return ["p7", "p8"];
    return [pass];
  }, [pass]);

  useEffect(() => {
    let current = true;
    setArtifacts({});
    setProblem(null);
    void Promise.all([
      Promise.all(needed.map((id) => constructionApi.pass(id))),
      constructionApi.admissions(),
    ]).then(([loaded, admissions]) => {
      if (!current) return;
      setArtifacts(Object.fromEntries(loaded.map((item) => [item.pass, item])));
      setProposals(admissions);
    }).catch((error: unknown) => {
      if (current) setProblem(error instanceof Error ? error.message : String(error));
    });
    return () => { current = false; };
  }, [needed]);

  const admit = async (
    record: AdmissionRecord,
    target: "WORLD" | "PURPOSE",
    reason: string,
    test: string,
  ) => {
    setBusy(true);
    try {
      const proposal = await constructionApi.admit({
        relation: words(record.name),
        admission: target,
        reason,
        purpose_independence_test: test,
        actor,
      });
      setProposals((held) => ({ ...held, [proposal.relation]: proposal }));
      setProblem(null);
      await onChanged();
    } catch (error) {
      setProblem(error instanceof Error ? error.message : String(error));
    } finally {
      setBusy(false);
    }
  };

  const withdraw = async (record: AdmissionRecord) => {
    setBusy(true);
    try {
      const relation = words(record.name);
      await constructionApi.withdraw(relation, actor);
      setProposals((held) => {
        const rest = { ...held };
        delete rest[relation];
        return rest;
      });
      setProblem(null);
      await onChanged();
    } catch (error) {
      setProblem(error instanceof Error ? error.message : String(error));
    } finally {
      setBusy(false);
    }
  };

  const current = artifacts[pass];
  return (
    <section className="artifact" aria-label={`${pass} artifact`}>
      <header className="artifact__bar">
        <div><b>{pass.toUpperCase()}</b><span>{current?.artifact ?? "opening artifact…"}</span></div>
        {pass === "p6" ? (
          <label>
            reviewer
            <input value={actor} onChange={(event) => onActor(event.target.value)} />
          </label>
        ) : null}
        <button type="button" onClick={onClose}>back to docket</button>
      </header>
      {problem ? <p className="artifact__problem">{problem}</p> : null}
      {!current && !problem ? <p className="artifact__loading">Opening the frozen artifact…</p> : null}
      {current ? (
        <div className="artifact__scroll">
          {pass === "p0" ? <Brief contract={object(current.document)} /> : null}
          {pass === "p1" ? <Vocabulary vocabulary={object(current.document)} contract={object(artifacts.p0?.document)} /> : null}
          {pass === "p2" ? <Intake report={object(current.document)} intake={current.intake} /> : null}
          {pass === "p6" ? (
            <AdmissionGate
              document={object(current.document)}
              outputs={artifacts.p8?.items ?? {}}
              proposals={proposals}
              actor={actor}
              busy={busy}
              onAdmit={admit}
              onWithdraw={withdraw}
            />
          ) : null}
          {pass === "p8" ? (
            <Answers
              outputs={current.items ?? {}}
              derivations={object(artifacts.p7?.document)}
              rows={rows}
              onOpenObligation={onOpenObligation}
            />
          ) : null}
          {["p3", "p4", "p5"].includes(pass) ? (
            <div className="artifact__handoff">
              <h3>This artifact is read through the docket.</h3>
              <p>P3 supplies the proposition, P4 its packet, and P5 the machine judgment. Keeping them side by side is the review unit.</p>
              <button type="button" onClick={onClose}>open the docket</button>
            </div>
          ) : null}
          {pass === "p7" ? (
            <div className="artifact__handoff">
              <h3>Derivations are read in the World explorer.</h3>
              <p>The read-side derivation view shows what each relation rests on, what it supports, and whether an input moved.</p>
              <a href={worldHref()}>open World derivations</a>
            </div>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
