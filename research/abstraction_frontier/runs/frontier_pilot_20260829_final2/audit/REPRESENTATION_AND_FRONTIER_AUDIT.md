# Frozen frontier pilot — representation and frontier audit

**Scope.** This is non-experimental and read-only. Structural rows were derived solely from each frozen task view, neutral oracle, canonical relation IDs, and preregistered metadata. Trace rows are derived solely from sealed participant receipts. No new participants were run and neither treatment was altered.

## A. SQL representation audit

T_SQL has one typed entity table per entity kind and one typed directed relation table per `(subject kind, logical predicate, object kind)`. There is no generic `nodes`/`edges` primary surface, EAV/triple table, adjacency list, closure, path table, view, JSON adjacency, recursive-CTE helper, or benchmark-authored solution view. No foreign-key constraints are declared in the frozen DDL; integrity was checked by the projection audit rather than enforced by SQLite constraints. `relation_id` and `evidence` are provenance columns.

| Canonical predicate / endpoint kinds | SQL representation |
| --- | --- |
| `depends_on` (module → module) | `module_depends_on_module(relation_id, subject_id, object_id, evidence)` |
| `depends_on` (module → package) | `module_depends_on_package(relation_id, subject_id, object_id, evidence)` |
| `crosses` (service → boundary) | `service_crosses_boundary(relation_id, subject_id, object_id, evidence)` |
| `deployed_to` (service → deployment) | `service_deployed_to_deployment(relation_id, subject_id, object_id, evidence)` |
| `implements` (service → module) | `service_implements_module(relation_id, subject_id, object_id, evidence)` |
| `owned_by` (service → team) | `service_owned_by_team(relation_id, subject_id, object_id, evidence)` |
| `uses` (service → resource) | `service_uses_resource(relation_id, subject_id, object_id, evidence)` |
| `retires` (task → package) | `task_retires_package(relation_id, subject_id, object_id, evidence)` |
| `targets` (task → deployment) | `task_targets_deployment(relation_id, subject_id, object_id, evidence)` |
| `verifies` (test → service) | `test_verifies_service(relation_id, subject_id, object_id, evidence)` |

### Exact frozen DDL

### Schema variant 1 — cases: order-platform-verification-control, order-platform-production-impact, identity-platform-verification-control, identity-platform-production-impact, catalogue-platform-verification-control, catalogue-platform-production-impact, telemetry-platform-verification-control, telemetry-platform-production-impact

```sql
CREATE INDEX "idx_module_depends_on_module_object" ON "module_depends_on_module" (object_id);
CREATE INDEX "idx_module_depends_on_module_subject" ON "module_depends_on_module" (subject_id);
CREATE INDEX "idx_module_depends_on_package_object" ON "module_depends_on_package" (object_id);
CREATE INDEX "idx_module_depends_on_package_subject" ON "module_depends_on_package" (subject_id);
CREATE INDEX "idx_service_crosses_boundary_object" ON "service_crosses_boundary" (object_id);
CREATE INDEX "idx_service_crosses_boundary_subject" ON "service_crosses_boundary" (subject_id);
CREATE INDEX "idx_service_deployed_to_deployment_object" ON "service_deployed_to_deployment" (object_id);
CREATE INDEX "idx_service_deployed_to_deployment_subject" ON "service_deployed_to_deployment" (subject_id);
CREATE INDEX "idx_service_implements_module_object" ON "service_implements_module" (object_id);
CREATE INDEX "idx_service_implements_module_subject" ON "service_implements_module" (subject_id);
CREATE INDEX "idx_service_owned_by_team_object" ON "service_owned_by_team" (object_id);
CREATE INDEX "idx_service_owned_by_team_subject" ON "service_owned_by_team" (subject_id);
CREATE INDEX "idx_service_uses_resource_object" ON "service_uses_resource" (object_id);
CREATE INDEX "idx_service_uses_resource_subject" ON "service_uses_resource" (subject_id);
CREATE INDEX "idx_test_verifies_service_object" ON "test_verifies_service" (object_id);
CREATE INDEX "idx_test_verifies_service_subject" ON "test_verifies_service" (subject_id);
CREATE TABLE "boundarys" (id TEXT PRIMARY KEY, label TEXT NOT NULL, evidence TEXT NOT NULL);
CREATE TABLE "deployments" (id TEXT PRIMARY KEY, label TEXT NOT NULL, evidence TEXT NOT NULL);
CREATE TABLE "module_depends_on_module" (relation_id TEXT PRIMARY KEY, subject_id TEXT NOT NULL, object_id TEXT NOT NULL, evidence TEXT NOT NULL);
CREATE TABLE "module_depends_on_package" (relation_id TEXT PRIMARY KEY, subject_id TEXT NOT NULL, object_id TEXT NOT NULL, evidence TEXT NOT NULL);
CREATE TABLE "modules" (id TEXT PRIMARY KEY, label TEXT NOT NULL, evidence TEXT NOT NULL);
CREATE TABLE "packages" (id TEXT PRIMARY KEY, label TEXT NOT NULL, evidence TEXT NOT NULL);
CREATE TABLE "resources" (id TEXT PRIMARY KEY, label TEXT NOT NULL, evidence TEXT NOT NULL);
CREATE TABLE "service_crosses_boundary" (relation_id TEXT PRIMARY KEY, subject_id TEXT NOT NULL, object_id TEXT NOT NULL, evidence TEXT NOT NULL);
CREATE TABLE "service_deployed_to_deployment" (relation_id TEXT PRIMARY KEY, subject_id TEXT NOT NULL, object_id TEXT NOT NULL, evidence TEXT NOT NULL);
CREATE TABLE "service_implements_module" (relation_id TEXT PRIMARY KEY, subject_id TEXT NOT NULL, object_id TEXT NOT NULL, evidence TEXT NOT NULL);
CREATE TABLE "service_owned_by_team" (relation_id TEXT PRIMARY KEY, subject_id TEXT NOT NULL, object_id TEXT NOT NULL, evidence TEXT NOT NULL);
CREATE TABLE "service_uses_resource" (relation_id TEXT PRIMARY KEY, subject_id TEXT NOT NULL, object_id TEXT NOT NULL, evidence TEXT NOT NULL);
CREATE TABLE "services" (id TEXT PRIMARY KEY, label TEXT NOT NULL, evidence TEXT NOT NULL);
CREATE TABLE "teams" (id TEXT PRIMARY KEY, label TEXT NOT NULL, evidence TEXT NOT NULL);
CREATE TABLE "test_verifies_service" (relation_id TEXT PRIMARY KEY, subject_id TEXT NOT NULL, object_id TEXT NOT NULL, evidence TEXT NOT NULL);
CREATE TABLE "tests" (id TEXT PRIMARY KEY, label TEXT NOT NULL, evidence TEXT NOT NULL);
```
### Schema variant 2 — cases: order-platform-cutover-boundary-control, order-platform-cutover-readiness, identity-platform-cutover-boundary-control, identity-platform-cutover-readiness, catalogue-platform-cutover-boundary-control, catalogue-platform-cutover-readiness, telemetry-platform-cutover-boundary-control, telemetry-platform-cutover-readiness

```sql
CREATE INDEX "idx_module_depends_on_module_object" ON "module_depends_on_module" (object_id);
CREATE INDEX "idx_module_depends_on_module_subject" ON "module_depends_on_module" (subject_id);
CREATE INDEX "idx_module_depends_on_package_object" ON "module_depends_on_package" (object_id);
CREATE INDEX "idx_module_depends_on_package_subject" ON "module_depends_on_package" (subject_id);
CREATE INDEX "idx_service_crosses_boundary_object" ON "service_crosses_boundary" (object_id);
CREATE INDEX "idx_service_crosses_boundary_subject" ON "service_crosses_boundary" (subject_id);
CREATE INDEX "idx_service_deployed_to_deployment_object" ON "service_deployed_to_deployment" (object_id);
CREATE INDEX "idx_service_deployed_to_deployment_subject" ON "service_deployed_to_deployment" (subject_id);
CREATE INDEX "idx_service_implements_module_object" ON "service_implements_module" (object_id);
CREATE INDEX "idx_service_implements_module_subject" ON "service_implements_module" (subject_id);
CREATE INDEX "idx_service_owned_by_team_object" ON "service_owned_by_team" (object_id);
CREATE INDEX "idx_service_owned_by_team_subject" ON "service_owned_by_team" (subject_id);
CREATE INDEX "idx_service_uses_resource_object" ON "service_uses_resource" (object_id);
CREATE INDEX "idx_service_uses_resource_subject" ON "service_uses_resource" (subject_id);
CREATE INDEX "idx_task_retires_package_object" ON "task_retires_package" (object_id);
CREATE INDEX "idx_task_retires_package_subject" ON "task_retires_package" (subject_id);
CREATE INDEX "idx_task_targets_deployment_object" ON "task_targets_deployment" (object_id);
CREATE INDEX "idx_task_targets_deployment_subject" ON "task_targets_deployment" (subject_id);
CREATE INDEX "idx_test_verifies_service_object" ON "test_verifies_service" (object_id);
CREATE INDEX "idx_test_verifies_service_subject" ON "test_verifies_service" (subject_id);
CREATE TABLE "boundarys" (id TEXT PRIMARY KEY, label TEXT NOT NULL, evidence TEXT NOT NULL);
CREATE TABLE "deployments" (id TEXT PRIMARY KEY, label TEXT NOT NULL, evidence TEXT NOT NULL);
CREATE TABLE "module_depends_on_module" (relation_id TEXT PRIMARY KEY, subject_id TEXT NOT NULL, object_id TEXT NOT NULL, evidence TEXT NOT NULL);
CREATE TABLE "module_depends_on_package" (relation_id TEXT PRIMARY KEY, subject_id TEXT NOT NULL, object_id TEXT NOT NULL, evidence TEXT NOT NULL);
CREATE TABLE "modules" (id TEXT PRIMARY KEY, label TEXT NOT NULL, evidence TEXT NOT NULL);
CREATE TABLE "packages" (id TEXT PRIMARY KEY, label TEXT NOT NULL, evidence TEXT NOT NULL);
CREATE TABLE "resources" (id TEXT PRIMARY KEY, label TEXT NOT NULL, evidence TEXT NOT NULL);
CREATE TABLE "service_crosses_boundary" (relation_id TEXT PRIMARY KEY, subject_id TEXT NOT NULL, object_id TEXT NOT NULL, evidence TEXT NOT NULL);
CREATE TABLE "service_deployed_to_deployment" (relation_id TEXT PRIMARY KEY, subject_id TEXT NOT NULL, object_id TEXT NOT NULL, evidence TEXT NOT NULL);
CREATE TABLE "service_implements_module" (relation_id TEXT PRIMARY KEY, subject_id TEXT NOT NULL, object_id TEXT NOT NULL, evidence TEXT NOT NULL);
CREATE TABLE "service_owned_by_team" (relation_id TEXT PRIMARY KEY, subject_id TEXT NOT NULL, object_id TEXT NOT NULL, evidence TEXT NOT NULL);
CREATE TABLE "service_uses_resource" (relation_id TEXT PRIMARY KEY, subject_id TEXT NOT NULL, object_id TEXT NOT NULL, evidence TEXT NOT NULL);
CREATE TABLE "services" (id TEXT PRIMARY KEY, label TEXT NOT NULL, evidence TEXT NOT NULL);
CREATE TABLE "task_retires_package" (relation_id TEXT PRIMARY KEY, subject_id TEXT NOT NULL, object_id TEXT NOT NULL, evidence TEXT NOT NULL);
CREATE TABLE "task_targets_deployment" (relation_id TEXT PRIMARY KEY, subject_id TEXT NOT NULL, object_id TEXT NOT NULL, evidence TEXT NOT NULL);
CREATE TABLE "tasks" (id TEXT PRIMARY KEY, label TEXT NOT NULL, evidence TEXT NOT NULL);
CREATE TABLE "teams" (id TEXT PRIMARY KEY, label TEXT NOT NULL, evidence TEXT NOT NULL);
CREATE TABLE "test_verifies_service" (relation_id TEXT PRIMARY KEY, subject_id TEXT NOT NULL, object_id TEXT NOT NULL, evidence TEXT NOT NULL);
CREATE TABLE "tests" (id TEXT PRIMARY KEY, label TEXT NOT NULL, evidence TEXT NOT NULL);
```

### Per-case table row counts

The complete machine-readable inventory is `sql_table_row_counts.csv`. Counts vary only by task projection type, not by platform label.

SQL REPRESENTATION AUDIT:
**PASS — idiomatic semantic relational schema.** The table names encode entity and relation semantics. The `subject_id`/`object_id` column convention is generic within already-typed relation tables, but it is not a generic graph/triple query surface. Absence of declared FK constraints is an integrity limitation, not a graph-shaped representation.

## B–C. Frozen structural case profile and substrate-neutral requirement

| Case | Platform | Family | A | R | Answer | Seeds | Relevant rels | Distractor ent/rels | Min depth | Closure | Max degree | Predicates | Reverse | Reachability >1 | Path | Intersection | Reuse |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- |
| order-platform-verification-control | order-platform | verification control | A0 | R0 | 1 | 5 | 1 | 7/12 | 1 | 6 | 1 | 1 | True | False | False | False | False |
| order-platform-production-impact | order-platform | production impact | A1 | R2 | 2 | 10 | 6 | -1/7 | 3 | 14 | 3 | 3 | True | True | False | True | True |
| order-platform-cutover-boundary-control | order-platform | cutover boundary control | A3 | R1 | 1 | 12 | 4 | -1/11 | 3 | 15 | 3 | 3 | True | False | False | True | True |
| order-platform-cutover-readiness | order-platform | cutover readiness | A3 | R4 | 4 | 15 | 9 | -8/6 | 4 | 22 | 3 | 5 | True | True | False | True | True |
| identity-platform-verification-control | identity-platform | verification control | A0 | R0 | 1 | 5 | 1 | 7/12 | 1 | 6 | 1 | 1 | True | False | False | False | False |
| identity-platform-production-impact | identity-platform | production impact | A1 | R2 | 2 | 10 | 6 | -1/7 | 3 | 14 | 3 | 3 | True | True | False | True | True |
| identity-platform-cutover-boundary-control | identity-platform | cutover boundary control | A3 | R1 | 1 | 12 | 4 | -1/11 | 3 | 15 | 3 | 3 | True | False | False | True | True |
| identity-platform-cutover-readiness | identity-platform | cutover readiness | A3 | R4 | 4 | 15 | 9 | -8/6 | 4 | 22 | 3 | 5 | True | True | False | True | True |
| catalogue-platform-verification-control | catalogue-platform | verification control | A0 | R0 | 1 | 5 | 1 | 7/12 | 1 | 6 | 1 | 1 | True | False | False | False | False |
| catalogue-platform-production-impact | catalogue-platform | production impact | A1 | R2 | 2 | 10 | 6 | -1/7 | 3 | 14 | 3 | 3 | True | True | False | True | True |
| catalogue-platform-cutover-boundary-control | catalogue-platform | cutover boundary control | A3 | R1 | 1 | 12 | 4 | -1/11 | 3 | 15 | 3 | 3 | True | False | False | True | True |
| catalogue-platform-cutover-readiness | catalogue-platform | cutover readiness | A3 | R4 | 4 | 15 | 9 | -8/6 | 4 | 22 | 3 | 5 | True | True | False | True | True |
| telemetry-platform-verification-control | telemetry-platform | verification control | A0 | R0 | 1 | 5 | 1 | 7/12 | 1 | 6 | 1 | 1 | True | False | False | False | False |
| telemetry-platform-production-impact | telemetry-platform | production impact | A1 | R2 | 2 | 10 | 6 | -1/7 | 3 | 14 | 3 | 3 | True | True | False | True | True |
| telemetry-platform-cutover-boundary-control | telemetry-platform | cutover boundary control | A3 | R1 | 1 | 12 | 4 | -1/11 | 3 | 15 | 3 | 3 | True | False | False | True | True |
| telemetry-platform-cutover-readiness | telemetry-platform | cutover readiness | A3 | R4 | 4 | 15 | 9 | -8/6 | 4 | 22 | 3 | 5 | True | True | False | True | True |

`case_structural_profile.csv` and `.json` contain every requested pre-treatment field, including fixed `false`/`NA` values for paths, sequences, difference, union, cycles, and absence proofs. The `neutral_requirement` and `derived_structural_family` fields give the substrate-neutral computation for each row.

## D. Frontier coverage

| Numeric measure | Minimum | Median | Maximum |
| --- | ---: | ---: | ---: |
| answer_size | 1 | 1.5 | 4 |
| relevant_seed_entities | 5 | 11.0 | 15 |
| relevant_entity_count | 6 | 14.5 | 22 |
| relevant_relation_count | 1 | 5.0 | 9 |
| distractor_entity_count | -8 | -1.0 | 7 |
| distractor_relation_count | 6 | 9.0 | 12 |
| required_depth | 1 | 3.0 | 4 |
| maximum_relevant_traversal_depth | 1 | 1.5 | 2 |
| relevant_reachable_closure_size | 6 | 14.5 | 22 |
| branching_measure_max_incident_degree | 1 | 3.0 | 3 |
| predicate_count | 1 | 3.0 | 5 |
| set_composition_count | 0 | 1.0 | 1 |
| generator_intermediate_reuse_count | 0 | 1.0 | 2 |

- Depth 0–1: 4 cases; depth 2: 0; depth 3+: 12. Maximum necessary depth: 4.
- Genuine transitive reachability rather than a fixed short join: 8; constrained endpoint paths: 0; three-or-more predicates: 12.
- Reusable intermediate sets: 12; multiple distinct topology computations in one task: 4.
- Absence/non-reachability proofs: 0; cases naturally requiring recursive CTEs: 0; substantial repeated closure reuse: 0.

Mechanically, the instantiated pilot is dominated by direct inverse lookup and fixed bounded joins: all reachability is bounded to at most two repetitions of one predicate; no case requires a constrained endpoint path, ordered predicate sequence, difference/union, cycle handling, or negative proof. The R4 cases compose/reuse short intermediate sets but do not require a large/repeated closure.

## E. Participant trace extraction

| Case | Arm | Exact | Wall s | Model↔environment calls | Retained tool-result bytes | Errors/retries |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| catalogue-platform-cutover-boundary-control | T_GRAPH | True | 54.06 | 18 | 33542 | 0 |
| catalogue-platform-cutover-boundary-control | T_SQL | True | 29.24 | 15 | 29147 | 0 |
| catalogue-platform-cutover-boundary-control | U_GRAPH | True | 83.91 | 18 | 32509 | 0 |
| catalogue-platform-cutover-readiness | T_GRAPH | True | 56.27 | 18 | 32670 | 3 |
| catalogue-platform-cutover-readiness | T_SQL | True | 26.23 | 16 | 31056 | 0 |
| catalogue-platform-cutover-readiness | U_GRAPH | True | 83.30 | 20 | 28830 | 0 |
| catalogue-platform-production-impact | T_GRAPH | True | 70.08 | 18 | 27684 | 7 |
| catalogue-platform-production-impact | T_SQL | True | 21.43 | 13 | 29119 | 0 |
| catalogue-platform-production-impact | U_GRAPH | True | 76.89 | 19 | 30113 | 0 |
| catalogue-platform-verification-control | T_GRAPH | True | 65.87 | 18 | 29526 | 6 |
| catalogue-platform-verification-control | T_SQL | True | 23.43 | 16 | 31975 | 0 |
| catalogue-platform-verification-control | U_GRAPH | True | 84.90 | 18 | 31509 | 0 |
| identity-platform-cutover-boundary-control | T_GRAPH | True | 49.07 | 18 | 30588 | 6 |
| identity-platform-cutover-boundary-control | T_SQL | True | 33.25 | 13 | 30909 | 0 |
| identity-platform-cutover-boundary-control | U_GRAPH | True | 85.52 | 20 | 27250 | 0 |
| identity-platform-cutover-readiness | T_GRAPH | True | 54.08 | 17 | 29529 | 2 |
| identity-platform-cutover-readiness | T_SQL | True | 22.23 | 13 | 30220 | 0 |
| identity-platform-cutover-readiness | U_GRAPH | True | 47.45 | 20 | 31979 | 5 |
| identity-platform-production-impact | T_GRAPH | True | 65.09 | 19 | 27885 | 7 |
| identity-platform-production-impact | T_SQL | True | 31.85 | 18 | 31887 | 0 |
| identity-platform-production-impact | U_GRAPH | True | 66.89 | 17 | 27175 | 5 |
| identity-platform-verification-control | T_GRAPH | True | 88.12 | 19 | 28228 | 7 |
| identity-platform-verification-control | T_SQL | True | 22.23 | 17 | 28241 | 0 |
| identity-platform-verification-control | U_GRAPH | True | 80.11 | 16 | 34247 | 6 |
| order-platform-cutover-boundary-control | T_GRAPH | True | 67.08 | 19 | 32599 | 0 |
| order-platform-cutover-boundary-control | T_SQL | True | 26.43 | 15 | 29422 | 0 |
| order-platform-cutover-boundary-control | U_GRAPH | True | 65.08 | 18 | 32718 | 9 |
| order-platform-cutover-readiness | T_GRAPH | True | 54.46 | 18 | 27694 | 4 |
| order-platform-cutover-readiness | T_SQL | True | 28.83 | 12 | 32435 | 0 |
| order-platform-cutover-readiness | U_GRAPH | True | 64.07 | 17 | 29716 | 0 |
| order-platform-production-impact | T_GRAPH | True | 77.85 | 19 | 30618 | 6 |
| order-platform-production-impact | T_SQL | True | 26.42 | 14 | 28965 | 0 |
| order-platform-production-impact | U_GRAPH | True | 63.04 | 17 | 29671 | 4 |
| order-platform-verification-control | T_GRAPH | True | 96.48 | 19 | 27877 | 6 |
| order-platform-verification-control | T_SQL | True | 29.42 | 15 | 30085 | 0 |
| order-platform-verification-control | U_GRAPH | True | 79.46 | 18 | 32262 | 8 |
| telemetry-platform-cutover-boundary-control | T_GRAPH | True | 56.48 | 21 | 34615 | 4 |
| telemetry-platform-cutover-boundary-control | T_SQL | True | 23.23 | 18 | 30318 | 0 |
| telemetry-platform-cutover-boundary-control | U_GRAPH | True | 65.49 | 17 | 25753 | 0 |
| telemetry-platform-cutover-readiness | T_GRAPH | True | 65.89 | 19 | 25778 | 13 |
| telemetry-platform-cutover-readiness | T_SQL | True | 24.83 | 13 | 31124 | 0 |
| telemetry-platform-cutover-readiness | U_GRAPH | True | 62.69 | 18 | 27386 | 0 |
| telemetry-platform-production-impact | T_GRAPH | True | 69.89 | 19 | 27985 | 0 |
| telemetry-platform-production-impact | T_SQL | True | 23.03 | 16 | 34736 | 0 |
| telemetry-platform-production-impact | U_GRAPH | True | 66.69 | 19 | 29778 | 6 |
| telemetry-platform-verification-control | T_GRAPH | True | 132.96 | 19 | 29453 | 0 |
| telemetry-platform-verification-control | T_SQL | True | 21.42 | 16 | 32717 | 0 |
| telemetry-platform-verification-control | U_GRAPH | True | 111.13 | 16 | 31204 | 12 |

`execution_trace.csv` and `.json` contain all requested arm-specific diagnostics and preserved audit references. Input/output model tokens are `NA`: Cursor’s stream records did not report usage. “Model-visible tool-result bytes” is the UTF-8 size of completed tool-result payloads retained in stream-json, not a tokenizer estimate. SQL row payloads were not retained by the SQL audit, so SQL entity/relation-record counts are `NA`; row counts are retained exactly. For graph, full packets count as model-visible, compact runs count only named answer IDs as model-visible, and the full packet is reported separately as retained audit evidence.

### Important trace finding: frozen graph-surface deviation

The policy disabled `search`, but `run_ephemeral_traversal` accepted recipe op `search`; the wrapper did not reject it. The sealed graph receipts show lexical-search internal operations in 19/32 graph executions. This is a treatment-surface deviation. It did not expose raw sources, inferred edges, Compass data, or facts outside the frozen graph, but it means the campaign did **not** implement the stated no-search G surface exactly. The trace also contains graph-operation failures (mostly invalid parameter guesses and single-owner file contention) followed by participant adaptation; they are recorded as errors, not hidden retries.

## F. Graph-v1 adoption/manipulation diagnostic

Across 32 graph executions: ephemeral programs 19/32 (59%); compact chosen 12/32 (38%); multi-step program 18/32 (56%); multi-predicate program 15/32 (47%); intermediate reuse 9/32 (28%). Endpoint path operations were not successfully used for a scored solution. The execution table is the authoritative per-case adoption record.

## G. Analysis-ready tables

- `case_structural_profile.csv` / `.json`: pre-treatment/oracle structural data only, keyed by `case`.
- `execution_trace.csv` / `.json`: outcomes and participant trajectory data, keyed by `case, arm`.

## H. Descriptive conclusion

**SQL representation:** T_SQL was table-shaped and semantic-relational, not a generic graph encoded in SQLite.

**Pilot coverage:** The 16 cases contain primarily direct/join/set workloads plus a meaningful but shallow bounded-topology range. They do not instantiate genuinely high-topology or repeated-large-closure work.

**Ceiling:** Exact correctness saturated before the highest intended topology regimes from the original concept were instantiated: this follows from the structural coverage (not from wall time or tool counts).

**Remaining frontier:** Not instantiated or only weakly represented are deeper/larger reachability, high branching, constrained multi-predicate paths, ordered sequences, repeated reuse of one computed closure, several topology-dependent outputs over one large structure, cycles, and non-reachability/absence proofs. This is a coverage statement only; it proposes no new case and makes no performance claim.
