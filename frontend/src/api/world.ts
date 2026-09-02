/**
 * The `/world` read plane, typed.
 *
 * Every shape here is what `world_explorer.adapter` returns, named once so a
 * surface cannot invent a field the server does not send. Nothing writes:
 * there is no route to write to.
 */

export type RoleKindList = string[];

export type WorldRole = {
  name: string;
  type: string;
  column?: string;
  referent: boolean;
  /** Referent namespaces this role has actually been filled with. */
  kinds?: RoleKindList;
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
  completeness: Record<string, unknown> | null;
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
  demand: {
    purpose: { id: string; revision: number; statement: string };
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
    last_run_view_revision: number | null;
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

export type WorldDemand = {
  purpose: { id: string; revision: number; statement: string };
  rule: string;
  demanded: number;
  obligations: {
    relation: string;
    values: Record<string, unknown>;
    demanded_by: Record<string, unknown>;
    state: "ASSERTED" | "UNRESOLVED";
    assertion_id: string | null;
  }[];
};

/**
 * The token, read from the URL the way the rest of the product reads it.
 *
 * `#/world?apiToken=devtoken` — same habit as the operator plane, so one dev
 * server and one bookmark serve both while both exist.
 */
function tokenFromLocation(): string | null {
  const hash = window.location.hash;
  const query = hash.includes("?") ? hash.slice(hash.indexOf("?") + 1) : "";
  const params = new URLSearchParams(query || window.location.search);
  return params.get("apiToken");
}

async function read<T>(path: string): Promise<T> {
  const token = tokenFromLocation();
  const response = await fetch(path, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!response.ok) {
    let detail = `${response.status}`;
    try {
      detail = ((await response.json()) as { error?: string }).error ?? detail;
    } catch {
      /* a body that is not JSON is still a failure worth reporting */
    }
    throw new Error(detail);
  }
  return (await response.json()) as T;
}

export const worldApi = {
  overview: () => read<WorldOverview>("/world/overview"),
  schema: () =>
    read<{ relations: WorldRelation[] }>("/world/schema").then((r) => r.relations),
  referents: () =>
    read<{ referents: { id: string; label: string | null }[] }>(
      "/world/referents",
    ).then((r) => r.referents),
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
