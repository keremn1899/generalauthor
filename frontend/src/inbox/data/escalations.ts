import type { EscalationHandoff } from "../types";

export function createInitialEscalations(): EscalationHandoff[] {
  const seed: EscalationHandoff[] = [
    {
      id: "esc-1",
      ungovernedPredicate: "pii.scrub.required_before_ship",
      question:
        "Must PII be scrubbed before any log shipper leaves the logging containment?",
      provenance: {
        actor: "agent.policy-check",
        source: "CI gate · shipper deploy",
        askedAt: "2026-07-13T14:02:00Z",
      },
      graphRegionId: "logging",
      createdAt: "2026-07-13T14:02:00Z",
      status: "open",
    },
    {
      id: "esc-2",
      ungovernedPredicate: "session.token.rotation_max_age",
      question: "What is the maximum age before a session token must rotate?",
      provenance: {
        actor: "agent.runtime",
        source: "Auth session gate query",
        askedAt: "2026-07-13T15:41:00Z",
      },
      graphRegionId: "session",
      createdAt: "2026-07-13T15:41:00Z",
      status: "open",
    },
    {
      id: "esc-3",
      ungovernedPredicate: "audit.mutate.retention_days",
      question:
        "How long must mutate API audit records be retained after write?",
      provenance: {
        actor: "agent.compliance",
        source: "Nightly sweep",
        askedAt: "2026-07-12T09:10:00Z",
      },
      graphRegionId: "audit",
      createdAt: "2026-07-12T09:10:00Z",
      status: "open",
    },
    {
      id: "esc-4",
      ungovernedPredicate: "logging.region.unclassified_events",
      question:
        "Are unclassified log events intentionally left ungoverned in this pocket?",
      provenance: {
        actor: "agent.gap-finder",
        source: "Containment scan · logging",
        askedAt: "2026-07-11T18:22:00Z",
      },
      graphRegionId: "logging",
      createdAt: "2026-07-11T18:22:00Z",
      status: "open",
    },
  ];
  return seed.sort(
    (a, b) =>
      new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime(),
  );
}
