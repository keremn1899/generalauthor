/**
 * The `/construction` plane, typed.
 *
 * What `world_explorer.construction` reads out of one frozen constructor run,
 * and the two routes that append a human verdict beside it. Unlike `world.ts`
 * this file imports `send`, and that is the honest signal: this is the surface
 * where writes exist.
 *
 * The writes go to a ledger, never to a pass artifact and never to a compiled
 * world. A verdict is an input to the next build.
 */

import { read, send } from "./plane";

export type Citation = { source_path: string; location: string };

export type Observation = Citation & {
  excerpt?: string;
  [key: string]: unknown;
};

/** What P4 assembled for one obligation. Absent when P4 wrote no packet —
 * which is a different fact from an empty one, and only one of them is the
 * constructor's failure. */
export type Packet = {
  obligation_id?: string;
  selected_observations?: Observation[];
  selection_rationale?: string;
  known_missing_information?: string;
  [key: string]: unknown;
};

/** P5's judgment. `original_disposition` and `verification_result` are the
 * constructor's own audit of itself, and the pair that most often explains a
 * decline: it proposed a closure and its verifier would not support it. */
export type Judgment = {
  disposition?: string;
  rationale?: string;
  support_claim?: string;
  supporting_evidence?: Observation[];
  original_disposition?: string;
  verification_result?: string;
  [key: string]: unknown;
};

export type Verdict = {
  kind: "ADJUDICATION" | "REVERT";
  obligation_id: string;
  disposition?: string;
  supporting_evidence?: Citation[];
  support_claim?: string;
  /** The machine disposition this overturns. Superseded, never overwritten. */
  supersedes?: string | null;
  reverts?: string | null;
  actor: string;
  at: string;
};

/** What an obligation holds up. The lists say what it *would* hold up; the
 * flag says whether it is holding it up now. */
export type Blocks = {
  purposes: string[];
  relations: string[];
  blocking: boolean;
};

export type DocketRow = {
  obligation_id: string;
  relation: string | null;
  values: Record<string, unknown> | null;
  why_demanded: string | null;
  required_by: string[];
  state: string | null;
  /** The machine's disposition. Stays on the row under a human verdict. */
  disposition: string | null;
  rationale: string | null;
  verification: string | null;
  observations: number;
  known_missing_information: string | null;
  verdict: Verdict | null;
  open: boolean;
  blocks: Blocks;
};

export type Docket = {
  obligations: DocketRow[];
  counts: { total: number; open: number; decided: number; blocking: number };
};

export type OpenedObligation = {
  obligation_id: string;
  proposition: {
    relation: string | null;
    values: Record<string, unknown> | null;
    why_demanded: string | null;
    required_by: string[];
    state: string | null;
  };
  packet: Packet | null;
  judgment: Judgment | null;
  blocks: Blocks;
  verdict: Verdict | null;
};

export type PassEntry = {
  pass: string;
  artifact: string;
  present: boolean;
  ran: boolean;
  agent: {
    model: string | null;
    returncode: number | null;
    timed_out: boolean | null;
    finished_at: string | null;
  } | null;
  items?: number;
};

export type ConstructionOverview = {
  run: string;
  path: string;
  passes: PassEntry[];
  counts: {
    obligations?: number;
    dispositions?: Record<string, number>;
    open?: number;
    decided?: number;
    blocking?: number;
  };
  /** Artifacts present but unreadable. A run mid-flight, not a fault. */
  unreadable: string[];
};

export const constructionApi = {
  overview: () => read<ConstructionOverview>("/construction"),
  docket: () => read<Docket>("/construction/docket"),
  obligation: (id: string) =>
    read<OpenedObligation>(
      `/construction/obligation?id=${encodeURIComponent(id)}`,
    ),
  pass: (id: string) =>
    read<{ pass: string; artifact: string; document?: unknown; items?: Record<string, unknown> }>(
      `/construction/pass?id=${encodeURIComponent(id)}`,
    ),
  history: (id: string) =>
    read<{ history: Verdict[] }>(
      `/construction/history?id=${encodeURIComponent(id)}`,
    ).then((r) => r.history),

  /**
   * Record one adjudication.
   *
   * The burdens are the server's — a closing verdict without a citation and a
   * support_claim is refused there, not here. This function does not
   * pre-check them, deliberately: a client-side copy of a rule is a rule with
   * two versions, and the one that matters is the one behind the route.
   */
  adjudicate: (proposal: {
    obligation_id: string;
    disposition: string;
    supporting_evidence: Citation[];
    support_claim: string;
    actor: string;
  }) => send<Verdict>("/construction/verdict", proposal),

  revert: (obligation_id: string, actor: string) =>
    send<Verdict>("/construction/revert", { obligation_id, actor }),
};
