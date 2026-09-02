import type { EdgeKind } from "../../../primitives/edge/types";

export type VerdictState =
  | "CONFORMS"
  | "VIOLATES"
  | "UNGOVERNED"
  | "INSUFFICIENT"
  | null;

export type GapKind = "intended" | "oversight";

export type OrbiterSpec = {
  id: string;
  label: string;
  /** Orbit radius in px from node center */
  radius: number;
  /** Initial angle in degrees */
  angle: number;
  /** Degrees per second when orbiting */
  speed: number;
};

export type TrialMassData = {
  label: string;
  /** 0..1 — high = settled/still centre of mass */
  certainty: number;
  verdict?: VerdictState;
  orbiters?: OrbiterSpec[];
  /** Transient lifecycle for Motion events */
  lifecycle?: "birthing" | "alive" | "dying";
};

export type TrialGapData = {
  kind: GapKind;
  /** Region this gap belongs to (containment pocket id) */
  region: string;
};

export type TrialEdgeData = {
  kind: EdgeKind;
};

export type LensKind = EdgeKind;

/** Force-sim node (positions owned by d3-force, mirrored to React Flow). */
export type SimNode = {
  id: string;
  kind: "mass" | "gap";
  x: number;
  y: number;
  vx?: number;
  vy?: number;
  fx?: number | null;
  fy?: number | null;
  certainty: number;
  massData?: TrialMassData;
  gapData?: TrialGapData;
};

export type SimLink = {
  id: string;
  source: string | SimNode;
  target: string | SimNode;
  kind: EdgeKind;
};

/** Canonical orbit tracks — rings and orbiters share these radii. */
export const ORBIT_TRACKS = [58, 72] as const;
/** Outermost track — used for force padding / field extent. */
export const FIELD_RING_OUTER = ORBIT_TRACKS[ORBIT_TRACKS.length - 1];
export const MASS_NODE_SIZE = 88;
export const MASS_NODE_RADIUS = MASS_NODE_SIZE / 2;

/** Unique sorted radii currently in use (for drawing rings). */
export function activeOrbitRadii(orbiters: { radius: number }[]): number[] {
  return [...new Set(orbiters.map((o) => o.radius))].sort((a, b) => a - b);
}

export function createInitialSimNodes(): SimNode[] {
  return [
    // --- Settled auth/session core ---
    {
      id: "auth",
      kind: "mass",
      x: 280,
      y: 220,
      certainty: 0.95,
      massData: {
        label: "Auth session gate",
        certainty: 0.95,
        verdict: "CONFORMS",
        lifecycle: "alive",
        orbiters: [
          {
            id: "orb-pending",
            label: "pending",
            radius: ORBIT_TRACKS[0],
            angle: 35,
            speed: 22,
          },
        ],
      },
    },
    {
      id: "session",
      kind: "mass",
      x: 420,
      y: 180,
      certainty: 0.9,
      massData: {
        label: "Session store",
        certainty: 0.9,
        verdict: "CONFORMS",
        lifecycle: "alive",
      },
    },
    {
      id: "mutate",
      kind: "mass",
      x: 520,
      y: 280,
      certainty: 0.85,
      massData: {
        label: "Mutate API",
        certainty: 0.85,
        verdict: "VIOLATES",
        lifecycle: "alive",
      },
    },
    {
      id: "audit",
      kind: "mass",
      x: 640,
      y: 200,
      certainty: 0.88,
      massData: {
        label: "Audit log 90d",
        certainty: 0.88,
        verdict: null,
        lifecycle: "alive",
      },
    },
    {
      id: "token",
      kind: "mass",
      x: 200,
      y: 320,
      certainty: 0.7,
      massData: {
        label: "Token refresh",
        certainty: 0.7,
        verdict: "INSUFFICIENT",
        lifecycle: "alive",
      },
    },
    {
      id: "policy",
      kind: "mass",
      x: 360,
      y: 360,
      certainty: 0.92,
      massData: {
        label: "Access policy",
        certainty: 0.92,
        verdict: null,
        lifecycle: "alive",
      },
    },
    // --- Containment pocket: Logging subtree ---
    {
      id: "logging",
      kind: "mass",
      x: 780,
      y: 360,
      certainty: 0.9,
      massData: {
        label: "Logging domain",
        certainty: 0.9,
        verdict: null,
        lifecycle: "alive",
      },
    },
    {
      id: "shipper",
      kind: "mass",
      x: 900,
      y: 300,
      certainty: 0.8,
      massData: {
        label: "Log shipper",
        certainty: 0.8,
        verdict: "CONFORMS",
        lifecycle: "alive",
      },
    },
    {
      id: "retention",
      kind: "mass",
      x: 920,
      y: 420,
      certainty: 0.75,
      massData: {
        label: "Retention rule",
        certainty: 0.75,
        verdict: null,
        lifecycle: "alive",
      },
    },
    {
      id: "pii-scrub",
      kind: "mass",
      x: 820,
      y: 480,
      certainty: 0.55,
      massData: {
        label: "PII scrub",
        certainty: 0.55,
        verdict: "UNGOVERNED",
        lifecycle: "alive",
      },
    },
    {
      id: "draft-rule",
      kind: "mass",
      x: 920,
      y: 360,
      certainty: 0.28,
      massData: {
        label: "Draft retention",
        certainty: 0.28,
        verdict: "INSUFFICIENT",
        lifecycle: "alive",
      },
    },
    // Gaps inside logging containment region (contextual, not scattered)
    {
      id: "gap-intended-logging",
      kind: "gap",
      x: 740,
      y: 440,
      certainty: 1,
      gapData: { kind: "intended", region: "logging" },
    },
    {
      id: "gap-oversight-logging",
      kind: "gap",
      x: 860,
      y: 520,
      certainty: 0.2,
      gapData: { kind: "oversight", region: "logging" },
    },
  ];
}

export function createInitialSimLinks(): SimLink[] {
  return [
    // CONTAINS pocket
    { id: "e-log-ship", source: "logging", target: "shipper", kind: "CONTAINS" },
    { id: "e-log-ret", source: "logging", target: "retention", kind: "CONTAINS" },
    { id: "e-log-pii", source: "logging", target: "pii-scrub", kind: "CONTAINS" },
    { id: "e-log-draft", source: "logging", target: "draft-rule", kind: "CONTAINS" },
    // LEADSTO flow
    { id: "e-auth-sess", source: "auth", target: "session", kind: "LEADSTO" },
    { id: "e-sess-mut", source: "session", target: "mutate", kind: "LEADSTO" },
    { id: "e-mut-audit", source: "mutate", target: "audit", kind: "LEADSTO" },
    // EXPRESSES
    { id: "e-pol-auth", source: "policy", target: "auth", kind: "EXPRESSES" },
    // NEARTO
    { id: "e-tok-sess", source: "token", target: "session", kind: "NEARTO" },
    { id: "e-audit-log", source: "audit", target: "logging", kind: "NEARTO" },
  ];
}
