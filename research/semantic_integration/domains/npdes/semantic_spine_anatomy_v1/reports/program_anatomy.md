# Program anatomy

Research-only. Sealed originals were not modified.

## MEASURED line counts

Physical LOC is Python file length. Semantic LOC is AST-painted declaration of referents, relations, maps, derives, requirement schemas, and explicit unresolved emission. Mechanical/runtime-support is source I/O, profiling, physical normalization, and helpers. Requirement LOC includes schema calls plus instantiation loops. Hole/instance LOC is `purpose.unresolved` sites.

| trial | physical | nonblank | semantic | mechanical | requirement | hole/instance |
| --- | --- | --- | --- | --- | --- | --- |
| T1 | 695 | 657 | 392 | 120 | 138 | 34 |
| T2 | 1015 | 957 | 482 | 140 | 161 | 65 |
| T3 | 804 | 762 | 492 | 122 | 168 | 67 |
| T4 | 660 | 619 | 339 | 77 | 106 | 41 |
| T5 | 652 | 609 | 359 | 78 | 141 | 32 |

Do not equate physical Python size with ontology size. T2 is the longest file because it splits identity into many WORLD relations; T5 is shortest because it derives most PURPOSE relations from three bases.

## MEASURED category paint (nonblank lines)

| trial | SOURCE_IO | SOURCE_PROFILING_OR_EXPLORATION | PHYSICAL_NORMALIZATION | GENERAL_HELPER_OR_CONTROL_FLOW | REFERENT_DECLARATION | RELATION_DECLARATION | GROUNDING_OR_MAPPING | MECHANICAL_DERIVATION | PURPOSE_REQUIREMENT_SCHEMA | PURPOSE_REQUIREMENT_INSTANTIATION | UNRESOLVED_OR_HOLE_EMISSION | REPORTING_DEBUGGING_OR_SERIALIZATION | OTHER |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T1 | 3 | 0 | 106 | 11 | 20 | 173 | 7 | 25 | 133 | 5 | 34 | 0 | 140 |
| T2 | 3 | 0 | 128 | 9 | 17 | 196 | 21 | 44 | 139 | 22 | 65 | 0 | 313 |
| T3 | 3 | 0 | 116 | 3 | 65 | 181 | 6 | 16 | 157 | 11 | 67 | 0 | 137 |
| T4 | 3 | 0 | 67 | 7 | 14 | 166 | 9 | 10 | 99 | 7 | 41 | 2 | 194 |
| T5 | 3 | 0 | 67 | 8 | 17 | 79 | 3 | 93 | 135 | 6 | 32 | 0 | 166 |

## MEASURED AST call-site counts

| trial | referent | relation | map | derive | require_unique | require_materializable | require_interpreted | require_numeric | unresolved | rows | profile | join |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T1 | 4 | 13 | 7 | 6 | 2 | 5 | 10 | 2 | 3 | 2 | 0 | 0 |
| T2 | 11 | 21 | 21 | 4 | 1 | 6 | 11 | 2 | 8 | 2 | 0 | 0 |
| T3 | 39 | 9 | 6 | 3 | 2 | 5 | 13 | 2 | 8 | 2 | 0 | 0 |
| T4 | 8 | 11 | 9 | 2 | 1 | 3 | 8 | 2 | 5 | 2 | 0 | 0 |
| T5 | 10 | 3 | 3 | 5 | 1 | 5 | 12 | 2 | 4 | 2 | 0 | 0 |

## OBSERVED

- Final programs contain almost no leftover `profile`/`join_profile` calls. Source exploration happened in-session and was not committed as the spine.
- `unresolved` call sites are few; spine `requirements` rows balloon when those sites sit inside per-row loops (T2/T3/T4).
- T3 `require_interpreted` count includes a 12-month seasonal loop (one schema, twelve surface names).

## HYPOTHESIS

Most of the 652–1,015 physical lines are not distinct ontology. Semantic-painted LOC is large because relation signatures and `require_*` blocks are verbose; factorized schema counts stay in the teens.
