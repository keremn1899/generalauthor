# Construction IR (research-only)

The host agent authors `program.json`. The host compiles it. The agent does **not** emit trigger instances or domain-specific trigger rules.

## Semantic calculus (frozen)

```text
REFERENT thin; identity keys only
NAMED TYPED N-ARY RELATION roles are named and typed
DERIVATION maintained, per-relation
```

World vs purpose: a requirement is purpose-relative. Base/derived relations should remain meaningful if the current purpose disappeared.

## File

Write exactly one JSON object to `program.json`.

Forbidden keys (compile error): `triggers`, `trigger_rules`, `gold`, `expected`, `families`.

Do not write `IF <parameter> THEN emit <named semantic family>`.

## Schema

```json
{
  "referents": [
    {"name": "Measurement", "key": ["permit_id", "outfall", "parameter_code", "period_end"]}
  ],
  "maps": [
    {
      "id": "map_dmr",
      "source": "dmr_measurements.csv",
      "referent": "Measurement",
      "fields": {"permit_id": "EXTERNAL_PERMIT_NMBR", "period_end": "MONITORING_PERIOD_END_DATE"}
    }
  ],
  "relations": [
    {
      "name": "measurement",
      "kind": "base",
      "map": "map_dmr",
      "roles": [
        {"name": "measurement", "type": "REFERENT", "field": "_referent", "of": "Measurement"},
        {"name": "permit_id", "type": "TEXT", "field": "permit_id"},
        {"name": "period_end", "type": "TEXT", "field": "period_end"}
      ]
    },
    {
      "name": "candidate_limit",
      "kind": "derived",
      "from": ["measurement", "limit_row"],
      "roles": [
        {"name": "measurement", "type": "REFERENT", "from_role": "measurement.measurement"},
        {"name": "limit", "type": "REFERENT", "from_role": "limit_row.limit"}
      ],
      "match": [
        {"left": "measurement.permit_id", "right": "limit_row.permit_id"}
      ],
      "where": [
        {
          "op": "interval_contains",
          "point": "measurement.period_end",
          "begin": "limit_row.begin_date",
          "end": "limit_row.end_date"
        }
      ]
    }
  ],
  "requirements": [
    {
      "id": "applicable_limit",
      "purpose": ["A"],
      "over": "candidate_limit",
      "group_by": ["measurement"],
      "cardinality": "ONE",
      "require_numeric": ["limit_value"],
      "require_interpreted_code": {"field": "nodi_code", "known": [""]}
    }
  ]
}
```

`source` must be one of:

- `dmr_measurements.csv`
- `permit_limits.csv`
- `document_inventory.json`

`document_inventory.json` is a JSON array of objects with mechanically visible keys: `path`, `filename`, `document_kind`, `permit`, `bytes`, `sha256`. There is no document text.

Role types: `REFERENT`, `TEXT`, `INTEGER`, `REAL`, `BOOLEAN`.

`kind`: `base` (from a map) or `derived` (join).

`cardinality`: `ONE` | `ZERO_OR_ONE` | `AT_LEAST_ONE`.

Special field `_referent` is the map-created referent id.

Dates in these CSVs are `MM/DD/YYYY`. The compiler parses them for `interval_contains`.

`where.op` allowed: `interval_contains`, `eq`, `neq`, `not_empty`.

## Generic diagnostics (compiler-emitted)

The runtime may emit only:

```text
CARDINALITY_UNDERSATISFIED
CARDINALITY_OVERSATISFIED
NO_MATERIALIZABLE_PATH
MULTIPLE_CANDIDATES
UNINTERPRETED_REQUIRED_CODE
COMPARISON_OPERATOR_REQUIRED
CONFLICTING_APPLICABLE_RELATIONS
UNBOUND_CORRESPONDENCE
```

These are compiler diagnostics, not World relation families. Do not author them as tuples.

## Compile loop

The host runs the compiler. You receive `diagnostics.json` with syntax/bind errors, row counts, unbound roles, cardinality diagnostics, and trigger counts. You may revise `program.json`. Maximum 3 compile/repair iterations. Stop when the program is structurally valid (schema + source maps bind) even if diagnostics remain.

Do not read files outside this workspace. Do not look for gold answers. They are not here.
