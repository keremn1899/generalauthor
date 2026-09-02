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
 * Two surfaces, one column each: the docket (§8.1) and one obligation opened
 * into three panes (§8.2). The spine — pass state and what a verdict costs to
 * rebuild — is §14 step 4 and is deliberately absent rather than stubbed: a
 * pass state this page invented would be worse than one it does not show.
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
import { Docket } from "./Docket";
import { Obligation } from "./Obligation";
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
      // purpose. Everything else here is geometry.
      style={
        {
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
        <Docket
          docket={docket}
          selected={selected}
          problem={problem}
          onOpen={(id) => setSelected(id === selected ? null : id)}
        />
        {opened ? (
          <Obligation
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
      </div>
    </div>
  );
}
