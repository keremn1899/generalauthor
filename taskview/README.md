# TaskView vertical prototype

This package is a deliberately isolated SQLite prototype. It does not modify or
wrap Graphauthor's graph product.

The semantic plane is composed of ordinary typed SQL tables—one table per named
relation. The `_tv_*` tables hold the system plane: thin referents, relation
schemas, assertion identity and grounding, derivation definitions and inputs,
view/relation revisions, and completeness receipts.

The implemented logical schema is:

```text
TaskView(view identity, task-spec reference, revision)
Referent(stable identity, optional label, grounding)
NamedRelation(name, description, ordered typed roles, BASE | DERIVED)
ActiveAssertion(tuple, ASSERTED | DERIVED)
Derivation(output relation, raw read-only SQL, declared inputs, receipt)
Completeness(target relation, named universe, COMPLETE | INCOMPLETE | UNKNOWN)
```

`Assertion` is bookkeeping around a relation tuple, not another semantic kind.
Scope is represented through ordinary relations in the worked example.

## Frozen v0 doctrine

Rows present in semantic relation tables are active assertions that ordinary SQL
and derivations may use. Retraction removes the row. Uncertainty is represented
explicitly as accepted semantic state (`unresolved_scope`, `contradiction`, and
similar task relations), not as a mixed-status tuple hidden in bookkeeping.

Referents are thin identities. Semantics live in named typed n-ary relations.
BASE tuples are explicit; DERIVED tuples are materialized only by deterministic
raw SQL whose declared inputs are checked at runtime. Grounding and revisions
stay in `_tv_*` tables. Completeness is local to a target relation, named
universe, and current input versions; absence is authoritative only for a
current successful `COMPLETE` result. Dependency changes make downstream
derivations stale. There is no graph layer, query DSL, planner, semantic
inference, confidence calculus, or universal ontology.

The migration fixture in `migration_example.py` demonstrates unary, binary and
four-role relations, grounded explicit assertions, materialized SQL derivations,
derived-relation reuse, an exhaustive empty result, an unknown boundary result,
and stale/rerun behavior.

## TaskView v0.1 agent surface

The first experiment exposes exactly four operation categories through
`TaskViewAgentSurface`:

```text
describe
query_sql
assertion(action = ASSERT | RETRACT)
rerun
```

`describe` may inspect the grounding of one named tuple on demand. `query_sql`
is read-only and can access declared semantic relation tables but not `_tv_*`
bookkeeping. `assertion` addresses tuples by semantic role values. `rerun`
materializes one registered SQL derivation with an explicit completeness claim.

The v0.1 consumption-surface revision keeps those same four operation
categories, but changes only their presentation and input ergonomics:

- `describe()` returns a compact relation catalog. Bare role names in the
  catalog are `REFERENT` roles; non-default role types are written as
  `name:TYPE`. Current is the default relation state; only non-current states
  are serialized in the catalog.
- `describe(relation="name")` returns details for one relation, including its
  full role/physical-column mapping and any local derivation/completeness
  detail. It does not return the rest of the TaskView.
- `describe(why={"relation": ..., "tuple": ...})` remains the targeted tuple
  grounding path and returns no catalog dump.
- `query_sql` accepts ordinary `SELECT *`; hidden `_assertion_id` columns are
  stripped from wildcard results and explicit hidden-ID references remain
  rejected. Writes, multiple statements, pragmas, and `_tv_*` access remain
  blocked.
- `assertion` accepts either semantic role names or their unambiguous physical
  column aliases (for example `service`/`service_id` and `test`/`test_id`).

This is a consumption-surface change only. It does not change the semantic
model, ontology, relation declarations, derivation SQL, assertion/retraction
meaning, staleness, or completeness rules.

Relation declaration and referent creation are deliberately excluded. The first
experiment freezes its schemas and referent universe so it tests maintenance and
reuse of a TaskView rather than simultaneous ontology invention.
