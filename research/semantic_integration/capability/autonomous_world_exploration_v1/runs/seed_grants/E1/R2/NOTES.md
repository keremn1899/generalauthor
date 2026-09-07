# World notes

## Purpose

Grant-award packet analysis: remaining balances, cash-match obligations, status interpretability from a partial office legend. Surface cases where the packet cannot confidently classify status or match rules (especially SEED-CORE waivers).

## Scale

5 awards · 3 orgs · 2 programs · 5 disbursements · 8 purpose failures. Small, deliberately incomplete dataset.

## Entity graph

```
organization ──org_id──▶ award ──award_id──▶ disbursement
                              ├── award_remaining_balance
                              ├── award_match_obligation
                              └── award_status_label (sparse)
program_match_rule ◀──program── award
status_legend_entry  (lookup by status_code; partial)
```

Join hub: `award_id`. Program rules propagate to per-award obligations via `program`.

## Programs & match rules

| Program   | Match required | Rate | Waiver possible |
|-----------|---------------|------|-----------------|
| SEED-CORE | yes           | 0.20 | yes             |
| SEED-FAST | no            | 0    | no              |

`award_match_obligation` mirrors `program_match_rule` per award. Obligation facts are present; **whether a waiver is actually on file is not**.

## Balances (internally consistent)

`award_remaining_balance` agrees with `award.amount` and sum of `disbursement` rows. All amounts stored as TEXT; treat as numeric in analysis.

| Award | Remaining | Notes                          |
|-------|-----------|--------------------------------|
| A-101 | 15,000    | 2 disbursements                |
| A-102 | 0         | SEED-FAST, fully disbursed     |
| A-103 | 0         | Closed                         |
| A-104 | 20,000    | 1 disbursement                 |
| A-105 | 10,000    | **no disbursement rows**       |

## Status legend gap

Legend covers only **A → Active**, **C → Closed** (from `status_fragment.txt`).

| Award | Code | Label row | Interpretable? |
|-------|------|-----------|----------------|
| A-101 | A    | Active    | yes            |
| A-102 | A    | Active    | yes            |
| A-103 | C    | Closed    | yes            |
| A-104 | S    | —         | **no**         |
| A-105 | H    | —         | **no**         |

Missing label row ≠ code is invalid; it means the legend is insufficient.

## Unresolved / purpose failures (8 rows)

PURPOSE relation `purpose_requirement_failure` — analytical state, not WORLD fact.

| Requirement                  | Kind                  | Affected                          |
|-----------------------------|-----------------------|-----------------------------------|
| `award_status_interpretable`| UNINTERPRETED         | A-104 (S), A-105 (H)              |
| `status_code_not_in_legend` | EXPLICIT_UNRESOLVED   | A-104 (S), A-105 (H)              |
| `seed_core_waiver_unknown`  | EXPLICIT_UNRESOLVED   | A-101, A-103, A-104, A-105 (all SEED-CORE) |

Waiver note: SEED-CORE requires 20% cash match unless a written waiver is on file; packet lacks waiver letters. Applies even when match obligation is otherwise recorded.

## Other observations

- **Duplicate EIN** `81-1111111`: ORG-MEADOW and ORG-HARBOR share it — may matter for org-level dedup.
- **Ridge Arts** (ORG-RIDGE) holds A-102 (SEED-FAST) and A-105 (SEED-CORE, undisbursed).
- All WORLD tuples are ASSERTED with SOURCE grounding (file refs: `awards.csv`, `disbursements.csv`, `orgs.json`, `program_rules.txt`, `status_fragment.txt`). Construction origins split MECHANICAL vs SEMANTIC in `world.sqlite.origins.json`.

## Read rules (apply in analysis)

- Unresolved / unknown / uninterpreted is **not** false.
- Empty query result = no tuple observed, **not** established absence.
- PURPOSE failures supplement but do not override direct WORLD facts.
- Unknown neighbors do not invalidate established facts unless a dependency says so.

## Access

```python
from research.semantic_integration.runtime_v0.world import ConstructionWorld
world = ConstructionWorld.open("world/world.sqlite")
rows = world.query_semantic("SELECT ...")
```

`view_id=v0`, `schema_revision=46`. Do not modify the World.
