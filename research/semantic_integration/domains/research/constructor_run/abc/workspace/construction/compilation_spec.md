# Compilation specification

## Purpose-driven vocabulary

Relations were discovered from purposes A (outcome traceability), B (study reconciliation), and C (reanalysis readiness). The smallest reusable vocabulary separates mechanical source compilation (WORLD) from analytical judgments (PURPOSE) and derived purpose rows (DERIVED).

## Construction phases

### C0 — referents

Thin referents for each registry study (`registry:<id>`), publication (`publication:<id>`), and dataset (`dataset:<id>`). No global canonical merge.

### C1 — mechanical compilation

Parse `sources/study_registry.csv`, `sources/publications.json`, `sources/datasets.csv`, and supplement codebooks. Emit exact-ID links, protocol codes, counts, outcome wordings, variables, and deterministic identity candidates.

### C2 — semantic frontier

Bounded obligations for:

- study identity between registry, publication, and dataset records (especially NORTHWIND ambiguity)
- outcome correspondence where identity is established but wording or endpoint semantics differ (HELIOS)
- variable sufficiency for registered primary outcomes (AURORA, PINE)

### C3 — grounded resolution

Apply ACCEPT / REJECT / UNRESOLVED with evidence packets. No closed-world negatives for missing links.

### C4 — derivation

SQL derivations produce `purpose_a_study`, `purpose_b_link`, and `purpose_c_study`. JSON exports read only from World.

## World vs Purpose

| Relation | Admission | Rationale |
|----------|-----------|-----------|
| registered_primary_outcome | WORLD | Source fact independent of analytical question |
| publication_reported_primary | WORLD | Source fact |
| publication_stated_registry_id | WORLD | Exact field correspondence |
| dataset_stated_registry_link | WORLD | Exact field correspondence |
| dataset/publication protocol and counts | WORLD | Source facts |
| dataset_variable | WORLD | Codebook fact |
| identity_candidate | WORLD | Mechanical candidate, not a judgment |
| outcome_correspondence_candidate | WORLD | Mechanical pairing from links |
| study_identity_judgment | PURPOSE | Depends on reconciliation policy |
| outcome_correspondence_judgment | PURPOSE | Depends on traceability question |
| variable_sufficiency_judgment | PURPOSE | Depends on reanalysis readiness question |
| purpose_* rows | PURPOSE | Requested decision outputs |
