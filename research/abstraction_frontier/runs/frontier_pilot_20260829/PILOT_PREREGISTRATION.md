# Frozen-View Abstraction × Relational Frontier — Pilot preregistration

This is a frontier-identification pilot, not an effect-size estimate. Construction quality is outside scope. Gates 1–7 were completed before this manifest; no participant outcome informed selection.

- Model: Cursor Composer 2.5 via cursor-agent CLI
- Arms: T_SQL, T_GRAPH, U_GRAPH
- Episode timeout: 240 seconds; no within-episode retry
- Graph surface: describe, lookup, expand, path, run_ephemeral_traversal
- T_SQL/T_GRAPH semantic parity is required per case; U_GRAPH is the independently constructed maximal reusable view.
- Exact correctness and valid execution are primary. Interaction counts, model-visible payload, tokens where the client reports them, and wall time are telemetry.

| Case | World | A | R | Named answer sets |
| --- | --- | --- | --- | --- |
| order-platform-verification-control | order-platform | A0 | R0 | suites |
| order-platform-production-impact | order-platform | A1 | R2 | affected |
| order-platform-cutover-readiness | order-platform | A3 | R4 | affected, covered |
| identity-platform-verification-control | identity-platform | A0 | R0 | suites |
| identity-platform-production-impact | identity-platform | A1 | R2 | affected |
| identity-platform-cutover-readiness | identity-platform | A3 | R4 | affected, covered |
| catalogue-platform-verification-control | catalogue-platform | A0 | R0 | suites |
| catalogue-platform-production-impact | catalogue-platform | A1 | R2 | affected |
| catalogue-platform-cutover-readiness | catalogue-platform | A3 | R4 | affected, covered |
| telemetry-platform-verification-control | telemetry-platform | A0 | R0 | suites |
| telemetry-platform-production-impact | telemetry-platform | A1 | R2 | affected |
| telemetry-platform-cutover-readiness | telemetry-platform | A3 | R4 | affected, covered |

Frozen-input SHA-256: `PILOT_MANIFEST.json` is `1950547e3b112b4bb799297e01ecb88dd64acb857ec5d9d013f357665f333d7a`. Per-artifact hashes are in `FROZEN_INPUT_HASHES.json`.
