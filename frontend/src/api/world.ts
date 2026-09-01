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
  rows: (relation: string, limit = 200, offset = 0) =>
    read<{
      relation: string;
      total: number;
      roles: WorldRole[];
      rows: WorldTuple[];
    }>(
      `/world/rows?relation=${encodeURIComponent(relation)}&limit=${limit}&offset=${offset}`,
    ),
  assertion: (id: string) =>
    read<WorldAssertion>(`/world/assertion?id=${encodeURIComponent(id)}`),
  demand: () => read<{ demand: WorldDemand | null }>("/world/demand").then((r) => r.demand),
};
