# Programming results (Part B)

Each episode received three hidden tasks (relational, graph-shaped, mixed) against one frozen T1 World. 2 agents × 2 arms × 3 domains = 12 episodes, 36 task scores. No rebuild, no mutation, no raw sources.

## MEASURED

| arm | CORRECT | PARTIAL | INCORRECT | UNSUPPORTED_CLOSURE | n |
| --- | --- | --- | --- | --- | --- |
| A0 | 18 | 0 | 0 | 0 | 18 |
| A1 | 18 | 0 | 0 | 0 | 18 |

All 12 episodes answered P1, P2, and P3 from the same sqlite. Post-run World hashes match the freeze.

### Per domain (both arms)

| domain | P1 relational | P2 graph-shaped | P3 mixed |
| --- | --- | --- | --- |
| harbor_towing | 4/4 vessel charge totals 1200 / 2280 / 720 | 4/4 V-BAY → {J2,J5} → {B4,B12} | 4/4 B12 jobs J5,J7; established sum 0 listed **separately** from insufficient_evidence |
| seed_grants | 4/4 remaining by org 15000 / 10000 / 20000 | 4/4 A-101 → ORG-MEADOW → {A-101,A-103} + disbursements | 4/4 Active remaining 15000; unresolved sibling **A-105** only (not A-104) |
| makerspace_checkout | 4/4 authorized fees LASER-A 54, CNC-1 108, SAW-1 4 | 4/4 M-17 → {C1,C3,C6,C7} tools {LASER-A, SAW-1} with L1 remap | 4/4 CNC-1 fees 108 **including** C5; PENDING listed separately |

### Dominant mechanism (descriptive)

From submitted `code` across 36 tasks:

| mechanism (scorer) | count |
| --- | --- |
| SQL_MULTI_RELATION | 26 |
| MIXED_SQL_PYTHON | 10 |
| SQL_RECURSIVE | 0 |
| PYTHON_GRAPH | 0 |
| MODEL_SIDE_COMPOSITION | 0 |

29/36 task codes contain SQL `JOIN`. 8 contain `WITH` (non-recursive). 0 recursive CTEs. 0 NetworkX. Graph-shaped P2 was implemented as ordinary joins / filters over referent columns.

## OBSERVED

Harbor P3 agents wrote an established-charge sum of 0 **and** an explicit `billing_not_established` list. That is mixed-program discipline the Part A yes/no consumers lacked: 0 is the empty established sum, not “J7 is not an emergency.”

Seed P3 agents distinguished A-105 (sibling of Active A-102) from A-104 (uninterpreted, but not on the Active-award org chain). Remaining 10000 on A-105 was not folded into the Active total.

Makerspace P3 kept C5’s established fee 54 in the authorized sum while reporting PENDING as EXPLICIT_UNRESOLVED. That is the opposite of proposition contamination.

A0 vs A1 programming accuracy is tied (perfect). The contract was not required for these computational tasks.

## HYPOTHESIS

`PROGRAMMABLE_WORLD_SUPPORTED`. Ordinary SQL + Python over thin referents and n-ary relations is enough for relational aggregation, multi-relation traversal, and mixed programs that keep unresolved separate from zero. A native graph query language is not justified by this pack.
