# World API (research-only)

Import `world_api.py` in this workspace. This is not the product TaskView kernel. Do not add a semantic primitive.

```python
from world_api import World, Purpose
from source import Source, parse_date, interval_contains

src = Source("sources")
world = World()
purpose = Purpose(world)
```

Optional entrypoint the host will call if present:

```python
def construct(source, world, purpose):
    ...
```

## Commit meaning

```text
world.referent(kind, key_dict, grounding=None) -> id
world.relation(name, [(role, TYPE), ...], mode="WORLD"|"PURPOSE", derived=False, description="")
world.map(relation, rows, grounding=None)
world.derive(name, rows, roles=..., inputs=..., grounding=None, mode="WORLD")
```

`TYPE` is one of `REFERENT`, `TEXT`, `INTEGER`, `REAL`, `BOOLEAN`.

`mode="PURPOSE"` for propositions that would change meaning if the current purpose disappeared.

## Purpose requirements (holes come from these)

```text
purpose.require_unique(name, per=role or [roles], candidates=relation, purpose=["A"], cardinality="ONE")
purpose.require_materializable(name, relation=..., purpose=...)
purpose.require_interpreted(name, relation=..., field=..., known=[""], purpose=..., per=None)
purpose.require_numeric(name, relation=..., field=..., purpose=..., per=None)
purpose.unresolved(name, subject=..., relation=..., reason=..., purpose=..., grounding=...)
```

There is no `trigger()` API. Do not persist uninterpreted comment/code text as World truth.

Failed requirements emit generic holes:

```text
CARDINALITY_OVERSATISFIED
CARDINALITY_UNDERSATISFIED
MULTIPLE_CANDIDATES
NO_MATERIALIZABLE_PATH
UNINTERPRETED
COMPARISON_OPERATOR_REQUIRED
EXPLICIT_UNRESOLVED
```

These are diagnostics, not domain families.

## Source helpers (no domain meaning)

```text
src.tables()
src.fields(table)
src.n_rows(table)
src.profile(table, field)
src.distinct_values(table, field)
src.key_candidates(table)
src.value_overlap((table, field), (table, field))
src.join(left, right, on=[(left_field, right_field), ...])
src.join_profile(...)
src.document_inventory()
parse_date(value)          # MM/DD/YYYY or ISO; mechanical
interval_contains(point, begin, end)
```

Dates in the CSVs are `MM/DD/YYYY`. Helpers report counts, overlaps, and values. They do not name semantic roles.
