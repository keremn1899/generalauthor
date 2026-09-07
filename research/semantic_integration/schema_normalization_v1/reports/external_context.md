# External context — Probe B (not scoring)

What is already known:
- Schema matching and mapping: correspondences between heterogeneous schemas.
- Mediated schemas / global-as-view / local-as-view: a stable consumer schema over sources.
- Data exchange (Clio): generate transformations from correspondences.
- Ontology alignment and model management: morphisms between models, composition, invertibility.

What differs:
- Constructors author both the physical schema and machine-readable relation contracts (roles, dispositions, algebra).
- The consumer programs are frozen purpose projectors, so the oracle is behavioral equivalence, not string similarity of relation names.
- Epistemic dispositions (SAME / DISTINCT / UNRESOLVED with candidate identity) must survive representation change.
- We forbid using constructor relation names as the matching key.

What we borrow:
- Metamorphic tests: Program(Normalize(W)) == Program(Normalize(M(W))).
- Distinguish rename/orientation (should be mechanical) from decomposition (needs derivation contracts).
- False-positive mappings under irrelevant noise are first-class, as in schema-matching precision.
