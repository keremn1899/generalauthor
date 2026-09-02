import type { EdgeKind } from "../../shared/edges/types";

export type ConceptData = {
  label: string;
  /** Transient lifecycle for Motion events */
  lifecycle?: "birthing" | "alive" | "dying";
  /** Quiet geometric mark until read/dismissed */
  unread?: boolean;
  /** Pulse token — increment to fire a one-shot write pulse */
  pulseToken?: number;
};

export type FieldEdgeData = {
  kind: EdgeKind;
  /** Optional relation weight → stroke thickness */
  weight?: number;
  label?: string;
};

export type SimNode = {
  id: string;
  x: number;
  y: number;
  vx?: number;
  vy?: number;
  fx?: number | null;
  fy?: number | null;
  concept: ConceptData;
};

export type SimLink = {
  id: string;
  source: string | SimNode;
  target: string | SimNode;
  kind: EdgeKind;
  weight?: number;
  label?: string;
};

export const CONCEPT_NODE_SIZE = 88;
export const CONCEPT_NODE_RADIUS = CONCEPT_NODE_SIZE / 2;

/** Concept graph only — no gaps, verdicts, or orbiters. */
export function createInitialFieldNodes(): SimNode[] {
  return [
    {
      id: "auth",
      x: 280,
      y: 220,
      concept: { label: "Auth session gate", lifecycle: "alive" },
    },
    {
      id: "session",
      x: 480,
      y: 220,
      concept: { label: "Session", lifecycle: "alive" },
    },
    {
      id: "mutate",
      x: 680,
      y: 220,
      concept: { label: "Mutate API", lifecycle: "alive" },
    },
    {
      id: "audit",
      x: 880,
      y: 220,
      concept: { label: "Audit trail", lifecycle: "alive" },
    },
    {
      id: "token",
      x: 480,
      y: 80,
      concept: { label: "Token store", lifecycle: "alive" },
    },
    {
      id: "policy",
      x: 200,
      y: 80,
      concept: { label: "Access policy", lifecycle: "alive" },
    },
    {
      id: "logging",
      x: 720,
      y: 420,
      concept: { label: "Logging", lifecycle: "alive" },
    },
    {
      id: "shipper",
      x: 560,
      y: 520,
      concept: { label: "Log shipper", lifecycle: "alive" },
    },
    {
      id: "retention",
      x: 720,
      y: 560,
      concept: { label: "Retention rule", lifecycle: "alive" },
    },
    {
      id: "pii-scrub",
      x: 880,
      y: 520,
      concept: { label: "PII scrub", lifecycle: "alive" },
    },
  ];
}

export function createInitialFieldLinks(): SimLink[] {
  return [
    { id: "e-log-ship", source: "logging", target: "shipper", kind: "CONTAINS" },
    { id: "e-log-ret", source: "logging", target: "retention", kind: "CONTAINS" },
    { id: "e-log-pii", source: "logging", target: "pii-scrub", kind: "CONTAINS" },
    { id: "e-auth-sess", source: "auth", target: "session", kind: "LEADSTO" },
    { id: "e-sess-mut", source: "session", target: "mutate", kind: "LEADSTO" },
    { id: "e-mut-audit", source: "mutate", target: "audit", kind: "LEADSTO" },
    { id: "e-pol-auth", source: "policy", target: "auth", kind: "EXPRESSES" },
    { id: "e-tok-sess", source: "token", target: "session", kind: "NEARTO" },
    { id: "e-audit-log", source: "audit", target: "logging", kind: "NEARTO" },
  ];
}
