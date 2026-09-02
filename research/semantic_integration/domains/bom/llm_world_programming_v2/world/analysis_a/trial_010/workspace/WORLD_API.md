# World programming interface

This workspace contains a compiled semantic World, not the original source files.

## Open

```python
from world_surface import open_world, relation_rows

world = open_world()
```

`open_world()` opens the World stored in `world.sqlite`.

Run Python as:

```text
PYTHONPATH=. python3 analysis.py
```

## Introspection

- `world.describe()` — relations, roles, modes, row counts, completeness
- `world.describe_text()` — compact text description
- `world.relation_schema(name)` — roles for one relation
- `world.stale_relations()`
- `world.is_stale(name)`
- `world.latest_completeness(name)` — completeness receipt for a derived relation

## Query

- `world.query(sql, parameters=())` — read-only SQL, including inspection tables
- `world.query_semantic(sql, parameters=())` — SQL restricted to declared semantic relations
- `relation_rows(world, name)` — all tuples of one relation without hidden assertion ids

## Provenance

- `world.inspect_tuple(relation, values)` — origin and grounding pointers for one tuple

Grounding pointers may name source handles. Source file bodies are not in this workspace.

## Unresolved semantic demand

- `world.obligations()` — semantic obligations: judgments a declared purpose requires that are not currently established as World tuples

Absence of a tuple is not automatically false. A completeness receipt may justify treating a missing derived tuple as a negative result for that derivation; it does not turn missing semantic judgments into false.

## Close

```python
world.close()
```
