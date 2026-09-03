/**
 * Construction — the review surface over one agent's run.
 *
 * Not a pipeline view and not a form. `composer-2.5` already wrote P0–P8; the
 * question this surface answers is not *what should the ontology be* but
 * *do you agree with what it decided, and on what evidence*. The nearest
 * established shapes are a code review and a CI build page, and the docket is
 * the front door for the same reason a review opens on the diff rather than on
 * the repository.
 *
 * Three surfaces (§4): the spine as a narrow rail, the docket as the front
 * door, and one obligation opened into three panes. The rail is last in
 * importance and first on the page for the reason a CI build page puts its
 * stage list there — you glance at it, you do not work in it.
 *
 * Everything reloads from the server after a verdict. The alternative is
 * patching the docket locally, which would mean this page held its own opinion
 * about what a verdict does to the ordering — and the ordering is a claim the
 * artifacts make, not one a client is entitled to.
 */

import { useCallback, useEffect, useState, type CSSProperties } from "react";
import {
  constructionApi,
  type ConstructionOverview,
  type Citation,
  type Docket as DocketData,
  type OpenedObligation,
  type Verdict,
} from "../api/construction";
import {
  chromeCssVariables,
  GRAPH_DNA_CHROME,
  GRAPH_DNA_STATUS,
  statusCssVariables,
  type ThemeMode,
} from "../styles/graphDna";
import { DEFAULT_MOTION_PLANS, motionCssVariables } from "../styles/motion";
import { Swap } from "../styles/Swap";
import { Docket } from "./Docket";
import { ArtifactView } from "./ArtifactView";
import { Obligation } from "./Obligation";
import { Spine } from "./Spine";
import "../styles/presence.css";
import "./ConstructionPage.css";

function storedTheme(): ThemeMode {
  try {
    return localStorage.getItem("graphauthor.productTheme") === "dark"
      ? "dark"
      : "light";
  } catch {
    return "light";
  }
}

/** Who is deciding. Remembered because it is typed once per session and
 * retyping it is friction on the one action this page exists for; kept in the
 * browser because it is a preference, not a credential. */
function storedActor(): string {
  try {
    return localStorage.getItem("graphauthor.adjudicator") ?? "";
  } catch {
    return "";
  }
}

function message(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

export function ConstructionPage() {
  const theme = storedTheme();
  const [overview, setOverview] = useState<ConstructionOverview | null>(null);
  const [docket, setDocket] = useState<DocketData | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [pass, setPass] = useState<string | null>(null);
  const [opened, setOpened] = useState<OpenedObligation | null>(null);
  const [history, setHistory] = useState<Verdict[]>([]);
  const [actor, setActor] = useState<string>(storedActor);
  const [busy, setBusy] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  const [refused, setRefused] = useState<string | null>(null);

  const loadDocket = useCallback(async () => {
    try {
      const [run, list] = await Promise.all([
        constructionApi.overview(),
        constructionApi.docket(),
      ]);
      setOverview(run);
      setDocket(list);
      setProblem(null);
    } catch (error) {
      setProblem(message(error));
    }
  }, []);

  const loadObligation = useCallback(async (id: string) => {
    try {
      const [item, log] = await Promise.all([
        constructionApi.obligation(id),
        constructionApi.history(id),
      ]);
      setOpened(item);
      setHistory(log);
      setRefused(null);
    } catch (error) {
      setRefused(message(error));
    }
  }, []);

  useEffect(() => {
    void loadDocket();
  }, [loadDocket]);

  useEffect(() => {
    if (selected) void loadObligation(selected);
    else setOpened(null);
  }, [selected, loadObligation]);

  useEffect(() => {
    try {
      localStorage.setItem("graphauthor.adjudicator", actor);
    } catch {
      /* a browser that will not remember the name is not a failure */
    }
  }, [actor]);

  const adjudicate = useCallback(
    async (proposal: {
      disposition: string;
      supporting_evidence: Citation[];
      support_claim: string;
    }) => {
      if (!selected) return;
      setBusy(true);
      try {
        await constructionApi.adjudicate({ obligation_id: selected, actor, ...proposal });
        setRefused(null);
        await Promise.all([loadDocket(), loadObligation(selected)]);
      } catch (error) {
        // The server's refusal, verbatim. It names the burden that was not
        // met, and that sentence is the only useful thing to say here.
        setRefused(message(error));
      } finally {
        setBusy(false);
      }
    },
    [selected, actor, loadDocket, loadObligation],
  );

  const revert = useCallback(async () => {
    if (!selected) return;
    setBusy(true);
    try {
      await constructionApi.revert(selected, actor);
      await Promise.all([loadDocket(), loadObligation(selected)]);
    } catch (error) {
      setRefused(message(error));
    } finally {
      setBusy(false);
    }
  }, [selected, actor, loadDocket, loadObligation]);

  const passes = overview?.passes.filter((entry) => entry.present).length ?? 0;

  return (
    <div
      className="construction"
      // Both palettes: chrome for the surface, status for the one thing on it
      // that is allowed to be a colour — whether an obligation blocks a
      // purpose. Everything else here is geometry. The motion spine rides
      // along because timing is design language too: a review surface that
      // settles at its own speed reads as a different product.
      style={
        {
          ...motionCssVariables(DEFAULT_MOTION_PLANS),
          ...chromeCssVariables(GRAPH_DNA_CHROME[theme]),
          ...statusCssVariables(GRAPH_DNA_STATUS[theme]),
        } as CSSProperties
      }
    >
      <header className="construction__bar">
        <b>construction</b>
        <span>{overview ? overview.run : "no run open"}</span>
        <span>
          {overview ? `${passes} of ${overview.passes.length} passes written` : ""}
        </span>
        {/* A run still being written is the normal case, so an unreadable
            artifact is reported as news about the run rather than swallowed. */}
        {overview?.unreadable.length ? (
          <span className="construction__unreadable">
            {overview.unreadable.length} artifact
            {overview.unreadable.length === 1 ? "" : "s"} unreadable
          </span>
        ) : null}
      </header>

      <div className="construction__body">
        <Spine
          passes={overview?.passes ?? []}
          open={docket?.counts.open}
          selected={pass}
          onSelect={setPass}
        />
        {/* The middle column always has a subject — a pass, or the docket you
            came from — so every change here is REPLACED rather than an arrival.
            One `Swap` covers all three of null→id, id→null and A→B. */}
        <Swap
          id={pass ?? "docket"}
          // The slot fills, except when it holds the docket, which is a fixed
          // column. The width lives on `--docket-width`, once.
          className={
            pass
              ? "motion-swap--fill"
              : "motion-swap--fill construction__docket-slot"
          }
        >
        {pass ? (
          <ArtifactView
            pass={pass}
            actor={actor}
            rows={docket?.obligations ?? []}
            onActor={setActor}
            onClose={() => setPass(null)}
            onChanged={loadDocket}
            // §15's provenance case ends here: the answer names a premise, and
            // the premise opens where it can be argued with. Leaving the pass
            // view is the point — the obligation lives on the docket.
            onOpenObligation={(id) => {
              setSelected(id);
              setPass(null);
            }}
          />
        ) : (
          <Docket
            docket={docket}
            selected={selected}
            problem={problem}
            onOpen={(id) => setSelected(id === selected ? null : id)}
          />
        )}
        </Swap>
        {/* The third column belongs to the docket reading; a pass takes the
            whole width, so it is unmounted rather than emptied. What this
            `Swap` is for is obligation A → obligation B, which is a change of
            subject in a column that stays exactly where it is. */}
        {pass ? null : (
        <Swap
          id={opened ? `obligation:${opened.obligation_id}` : "obligation:none"}
          className="motion-swap--fill"
        >
        {opened ? (
          <Obligation
            // Keyed so a second obligation opens as a second reading rather
            // than as the first one's form with new text in it.
            key={opened.obligation_id}
            opened={opened}
            actor={actor}
            history={history}
            busy={busy}
            problem={refused}
            onAdjudicate={adjudicate}
            onRevert={revert}
            onActor={setActor}
          />
        ) : (
          <section className="construction__empty">
            <p>
              {problem
                ? problem
                : "Open an obligation. The top of the docket is what deciding unblocks the most."}
            </p>
          </section>
        )}
        </Swap>
        )}
      </div>
    </div>
  );
}
