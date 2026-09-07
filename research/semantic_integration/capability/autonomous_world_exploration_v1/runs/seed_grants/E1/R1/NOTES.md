# World notes

## Purpose
Grant-portfolio packet: remaining award balances, applicable cash-match rules, interpretable statuses via office legend, and explicit flags where the packet is insufficient (unknown waivers, unknown status codes).

## Entity graph (join keys)
- `organization` ← `award.org_id`
- `award.award_id` → `disbursement`, `award_remaining_balance`, `award_match_obligation`, `award_status_label`
- `award.program` → `program_match_rule.program`
- `award.status_code` → `status_legend_entry.code` (partial legend only)

3 orgs, 5 awards, 5 disbursements. All BASE relations; no derivations.

## Programs & match
| Program    | match_required | rate | waiver_possible |
|------------|----------------|------|-----------------|
| SEED-CORE  | yes            | 0.20 | yes             |
| SEED-FAST  | no             | 0    | no              |

Per-award `award_match_obligation` mirrors `program_match_rule`. SEED-CORE match on **remaining** balance (not disbursed): A-101 $3k, A-104 $4k, A-105 $2k; A-103 closed ($0).

## Balances (award_remaining_balance)
| award | remaining | disbursed | notes                          |
|-------|-----------|-----------|--------------------------------|
| A-101 | 15,000    | 35,000    | 2 disbursements; sum reconciles |
| A-102 | 0         | 20,000    | fully disbursed (SEED-FAST)    |
| A-103 | 0         | 15,000    | closed                         |
| A-104 | 20,000    | 10,000    | 1 disbursement                 |
| A-105 | 10,000    | 0         | no disbursement rows           |

`award.amount` = `award_remaining_balance.award_amount` throughout. Portfolio remaining: **45,000**.

## Status interpretation
Legend (`status_legend_entry`): **A** = Active, **C** = Closed only.

| award | code | interpretable? | award_status_label |
|-------|------|----------------|--------------------|
| A-101 | A    | yes (legend)   | Active             |
| A-102 | A    | yes            | Active             |
| A-103 | C    | yes            | Closed             |
| A-104 | S    | **no**         | absent             |
| A-105 | H    | **no**         | absent             |

`award_status_label` exists only for A-101–A-103; redundant with legend where present.

## Unresolved / purpose failures (`purpose_requirement_failure`, PURPOSE scope)
Not false; do not override WORLD facts.

| requirement              | kind                 | awards affected | mechanism        |
|--------------------------|----------------------|-----------------|------------------|
| `award_status_interpretable` | UNINTERPRETED    | A-104 (S), A-105 (H) | MECHANICAL check vs known {A,C} |
| `status_code_not_in_legend`  | EXPLICIT_UNRESOLVED | A-104, A-105 | SEMANTIC; partial legend |
| `seed_core_waiver_unknown`   | EXPLICIT_UNRESOLVED | A-101, A-103, A-104, A-105 | SEMANTIC; no waiver letters in packet |

Numeric requirements (`remaining_balance_numeric`, `award_amount_numeric`) pass — all values parse as numeric TEXT.

## Grounding
WORLD BASE tuples are SOURCE-grounded (MECHANICAL construction). Source handles: `orgs.json`, `awards.csv`, `disbursements.csv`, `program_rules.txt`, `status_fragment.txt`. Purpose failures have empty `grounding_ref`; SEMANTIC-origin failures are author-declared unresolved, not source-backed.

## Oddities worth noting
- ORG-MEADOW and ORG-HARBOR share EIN `81-1111111` (distinct org_ids).
- A-102 is the sole SEED-FAST award; no match/waiver exposure.
- Empty query result ≠ established absence (per read rules).

## Query pattern
```python
from research.semantic_integration.runtime_v0.world import ConstructionWorld
world = ConstructionWorld.open("world/world.sqlite")
world.query_semantic("SELECT ...")  # joins across relation tables
```
