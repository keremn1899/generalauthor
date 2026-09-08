/**
 * The `/world` read plane, typed.
 *
 * Every shape here is what the World read adapter returns, named once so a
 * surface cannot invent a field the server does not send. Nothing writes:
 * there is no route to write to, and this file imports only `read`.
 */

import { read } from "./plane";

export type RoleKindList = string[];

export type WorldRole = {
  name: string;
  type: string;
  column?: string;
  referent: boolean;
  /** Referent namespaces this role has actually been filled with. */
  kinds?: RoleKindList;
};

export type WorldCompleteness = {
  status: "COMPLETE" | "INCOMPLETE" | "UNKNOWN";
  universe: string | null;
  current: boolean;
  known_gaps: unknown[];
};

export type WorldRelation = {
  name: string;
  description: string | null;
  mode: "BASE" | "DERIVED";
  arity: number;
  referent_arity: number;
  roles: WorldRole[];
  count: number;
  stale: boolean;
  /**
   * Construction origins observed in this relation's tuples.
   *
   * SHOW reads this, not mode: a BASE relation can be SEMANTIC
   * (`acceptable_replacement`) or MECHANICAL (`listing_of`), and collapsing
   * those onto BASE would hide the semantic seam the toggle exists to keep.
   */
  origins: string[];
  /**
   * WORLD or PURPOSE, from the admission sidecar — `null` where none was
   * recorded.
   *
   * Not derivable from anything else here: a PURPOSE relation is an artefact
   * of one purpose's bookkeeping, a WORLD relation is a claim about the world,
   * and nothing about mode, arity or origin separates them. `null` means the
   * world carries no admission document — never assume WORLD, which is the
   * stronger claim.
   */
  scope: "WORLD" | "PURPOSE" | null;
  completeness: WorldCompleteness | null;
  derivation?: { state?: string; inputs: string[] } & Record<string, unknown>;
};

export type WorldOverview = {
  world_id: string;
  revision: number;
  relations: number;
  referents: number;
  assertions: number;
  origins: Record<string, number>;
  stale: string[];
  /** Relations whose completeness receipt exists and is not COMPLETE. */
  incomplete: string[];
  /** Null when no purpose is loaded — see `WorldDemand` for the id/revision. */
  demand: {
    purpose: { id?: string; revision?: number; statement: string };
    obligations: number;
    demanded: number;
  } | null;
};

export type WorldGrounding = {
  kind: string;
  reference: string;
  native_handle?: string;
  native_location?: string;
  provider?: string;
  source_revision?: string;
  construction_method?: string;
  construction_origin?: string;
  detail?: Record<string, unknown>;
  detail_text?: string;
};

export type WorldTuple = {
  assertion_id: string;
  origin: string;
  values: Record<string, unknown>;
};

export type WorldAssertion = WorldTuple & {
  relation: string;
  mode: "BASE" | "DERIVED";
  arity: number;
  roles: WorldRole[];
  assertion_state: string;
  created_revision: number;
  relation_stale: boolean;
  completeness: WorldCompleteness | null;
  grounding: WorldGrounding[];
  derivation?: { inputs: string[] } & Record<string, unknown>;
};

export type WorldReferent = {
  id: string;
  label: string | null;
  grounding: WorldGrounding[];
  fields: {
    relation: string;
    role: string;
    value: unknown;
    assertion_id: string;
    origin: string;
  }[];
  relations: {
    name: string;
    arity: number;
    mode: string;
    stale: boolean;
    count: number;
  }[];
};

export type WorldRows = {
  relation: string;
  mode: "BASE" | "DERIVED";
  stale: boolean;
  total: number;
  offset: number;
  roles: WorldRole[];
  rows: WorldTuple[];
};

/**
 * §8.6. What a relation rests on, and what rests on it.
 *
 * Adjacency rather than a nested tree, because a relation can sit at more than
 * one place in the closure — `part_type` feeds both compatibility relations —
 * and a tree would either duplicate it or drop the second path. The panel
 * draws a tree from this; the closure is what is true.
 */
export type WorldDerivation = {
  relation: string;
  mode: "BASE" | "DERIVED";
  /** relation → the relations it reads, for the whole upward closure. */
  rests_on: Record<string, string[]>;
  /** relation → the relations that read it, for the whole downward closure. */
  supports: Record<string, string[]>;
  nodes: Record<
    string,
    {
      name: string;
      mode: "BASE" | "DERIVED";
      arity: number;
      count: number;
      stale: boolean;
      state: string | null;
    }
  >;
  run: {
    sql: string;
    state: string;
    definition_revision: number;
    last_run_world_revision: number | null;
    output_cardinality: number | null;
    last_error: string;
    /** Each input as it stood when the derivation last ran, beside now. */
    inputs: {
      relation: string;
      declared: boolean;
      version_at_run: number | null;
      count_at_run: number | null;
      version_now: number | null;
      count_now: number | null;
      moved: boolean;
    }[];
  } | null;
};

/**
 * Tuple-level drill-down, and it is candidates rather than lineage.
 *
 * The world records derivation per relation, not per row, so nothing here says
 * which input rows produced this one. What it says is which input tuples
 * mention the same referents, and how many of them each mentions. The
 * derivation's SQL is the recorded truth about how they combine.
 */
export type WorldSupport = {
  assertion_id: string;
  relation: string;
  derived: boolean;
  referents: string[];
  inputs: {
    relation: string;
    mode: "BASE" | "DERIVED";
    stale: boolean;
    count: number;
    matched: number;
    roles: WorldRole[];
    tuples: (WorldTuple & { mentions: number })[];
  }[];
};

/**
 * The unresolved frontier recorded for a World purpose.
 *
 * `rule` is optional because a purpose is prose plus construction state, not a
 * separate obligation compiler.
 * `requirements` is the relation-level summary of what the purpose asked for,
 * alongside any unresolved tuples.
 */
export type WorldDemand = {
  purpose: { id?: string; revision?: number; statement: string };
  rule: string | null;
  demanded: number;
  obligations: {
    relation: string;
    values: Record<string, unknown>;
    demanded_by: Record<string, unknown>;
    state: "ASSERTED" | "UNRESOLVED";
    assertion_id: string | null;
    /** The failure tuple itself, where unresolvedness is world state. */
    record_id?: string;
    /** Why it is unresolved, where the constructor said so. Not a role value. */
    reason?: string | null;
    grounding_ref?: string | null;
  }[];
  requirements?: {
    name: string;
    kind: string;
    relation: string | null;
    note: string;
    failures: number;
  }[];
};

export const worldApi = {
  overview: () => read<WorldOverview>("/world/overview"),
  schema: () =>
    read<{ relations: WorldRelation[] }>("/world/schema").then((r) => r.relations),
  /**
   * The referent directory — bounded, and it says when it is short.
   *
   * The canvas holds this and filters it as you type, which is right until the
   * world is large enough that opening the explorer costs a payload nobody
   * asked for. Past the plane's ceiling `truncated` is true and find has to ask
   * the plane instead of the array in front of it.
   */
  referents: () =>
    read<{
      referents: { id: string; label: string | null }[];
      total: number;
      truncated: boolean;
    }>("/world/referents"),
  /**
   * Ask the plane for referents matching a substring.
   *
   * The counterpart to a short directory. Results are candidates — the plane
   * matched a substring, which is not a claim that any of them is the thing
   * you meant.
   */
  search: (query: string, limit = 10) =>
    read<{
      results: { kind: string; id: string; label: string | null }[];
    }>(
      `/world/search?q=${encodeURIComponent(query)}&limit=${limit}`,
    ).then((r) => r.results),
  /** Labels for ids the directory did not carry. A lookup, not a search. */
  labels: (ids: string[]) =>
    ids.length
      ? read<{ labels: Record<string, string | null> }>(
          `/world/labels?ids=${ids.map(encodeURIComponent).join(",")}`,
        ).then((r) => r.labels)
      : Promise.resolve({} as Record<string, string | null>),
  referent: (id: string) =>
    read<WorldReferent>(`/world/referent?id=${encodeURIComponent(id)}`),
  expand: (id: string, relation: string) =>
    read<{ relation: string; arity: number; roles: WorldRole[]; tuples: WorldTuple[] }>(
      `/world/expand?id=${encodeURIComponent(id)}&relation=${encodeURIComponent(relation)}`,
    ),
  rows: (
    relation: string,
    options: {
      limit?: number;
      offset?: number;
      order?: string | null;
      desc?: boolean;
      /** Narrow the extension to one referent's tuples. */
      subject?: string | null;
    } = {},
  ) => {
    const query = new URLSearchParams({
      relation,
      limit: String(options.limit ?? 200),
      offset: String(options.offset ?? 0),
    });
    // Ordering is the database's, not the page's: a client-side sort would only
    // ever reach the rows already fetched, which for a windowed table is a
    // handful out of thousands.
    if (options.order) query.set("order", options.order);
    if (options.desc) query.set("desc", "1");
    if (options.subject) query.set("subject", options.subject);
    return read<WorldRows>(`/world/rows?${query}`);
  },
  assertion: (id: string) =>
    read<WorldAssertion>(`/world/assertion?id=${encodeURIComponent(id)}`),
  demand: () => read<{ demand: WorldDemand | null }>("/world/demand").then((r) => r.demand),
  derivation: (relation: string) =>
    read<WorldDerivation>(`/world/derivation?relation=${encodeURIComponent(relation)}`),
  support: (id: string) =>
    read<WorldSupport>(`/world/support?id=${encodeURIComponent(id)}`),
};
