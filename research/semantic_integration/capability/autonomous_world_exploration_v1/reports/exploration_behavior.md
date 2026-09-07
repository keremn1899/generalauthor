# Exploration behavior

What Composer 2.5 actually did when dropped into an unfamiliar compiled World with only PURPOSE, WORLD CONTRACT, READ RULES, REVISION, and SQL/Python.

## MEASURED

Task-phase operation flags (fraction of 9 episodes per arm that showed the pattern in truncated shell logs):

| pattern | E0 task | E1 task | E1 orient |
| --- | --- | --- | --- |
| catalog/schema (HEADER, admission, sqlite_master) | 9/9 | 7/9 | 9/9 |
| sample relation rows (`SELECT *` / `LIMIT`) | 3/9 | 3/9 | 1/9 |
| filtered relation read | 9/9 | 8/9 | 7/9 |
| join hypothesis (`JOIN` in shell log) | 0/9 | 1/9 | 5/9 |
| multi-relation SQL | 9/9 | 7/9 | 9/9 |
| aggregate | 0/9 | 1/9 | 4/9 |
| Python exploration (`ConstructionWorld`) | 9/9 | 9/9 | 9/9 |
| grounding inspection | 0/9 | 0/9 | 6/9 |
| failure-state inspection | 7/9 | 2/9 | 9/9 |

`describe()` calls: **0** in both arms’ recorded shells. HEADER.md was read once per phase (`header_rereads` mean 1.0).

Mean task-phase reads/shells: E0 6.4 / 3.8; E1 6.3 / 2.6. E1 orientation: 10.2 reads / 8.0 shells.

Raw-source reads: 0. World hashes unchanged. Isolation leaks: none. Composer 2.5 on every call.

## OBSERVED

The recurring loop is:

1. Read HEADER.md (contract + purpose + read rules).
2. Open `ConstructionWorld` and query PURPOSE failures plus a few WORLD relations.
3. Join in Python or successive SELECTs rather than one big SQL graph.
4. Answer.

E1 orientation notes are selective working maps (purpose, join keys, unresolved list, a few rules inferred from `basis` text). Harbor E1 R1 explicitly wrote WORLD vs PURPOSE row counts, J6 blank `billed_hours` vs J5/J7 B12, and “unresolved ≠ false.” That is useful understanding, not a full dump.

E0 did not wander. Six reads before answers is not pathological search.

Grounding was inspected mainly when E1 was told to orient “including grounding.” E0 almost never opened `_tv_groundings` and still completed factual tasks from relation rows.

## HYPOTHESIS

Ordinary agency, given a compact header and SQL/Python, explores on demand: header → targeted row reads → answers. An explicit orient phase produces nicer notes and more grounding/failure inspection; it does not change the downstream move set much.
