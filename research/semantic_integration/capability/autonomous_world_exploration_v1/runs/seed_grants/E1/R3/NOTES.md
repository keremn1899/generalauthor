# World notes (v0, schema_revision=46)

## Purpose

Grant-administration packet: remaining award balances, per-award cash-match obligations, and status codes vs a partial office legend. Surface cases where status or match/waiver cannot be classified confidently.

## Scale & access

- Small WORLD: 5 awards, 3 orgs, 2 programs, 2 legend codes, 8 purpose failures.
- Open: `ConstructionWorld.open("world/world.sqlite")`; query via `world.query_semantic(...)` or `world.relation_rows(...)`.
- WORLD vs PURPOSE: all base relations except `purpose_requirement_failure` are WORLD facts; failures are analytical state (PURPOSE scope).

## Entity model (join keys)

| Relation | Key roles | Links |
|---|---|---|
| `award` | `award_id` | → `org_id` → `organization`; `program` → `program_match_rule` |
| `award_remaining_balance` | `award_id` | 1:1 with awards; `award_amount` matches `award.amount` |
| `disbursement` | `award_id` | many per award; sums reconcile to `disbursed_total` |
| `award_match_obligation` | `award_id` | per-award copy of program match rule |
| `award_status_label` | `award_id` | only 3 rows — interpretable awards only |
| `status_legend_entry` | `code` | partial legend (A, C only) |

Programs: **SEED-CORE** (4 awards) requires 20% cash match, waiver possible; **SEED-FAST** (1 award, A-102) no match.

## Balances (clean)

All five awards: `disbursement` sums = `disbursed_total`, and `remaining_balance` = `award_amount − disbursed_total`. Numeric purpose checks pass.

| award | program | remaining | status |
|---|---|---:|---|
| A-101 | SEED-CORE | 15,000 | A (Active) |
| A-102 | SEED-FAST | 0 | A |
| A-103 | SEED-CORE | 0 | C (Closed) |
| A-104 | SEED-CORE | 20,000 | **S** (unknown) |
| A-105 | SEED-CORE | 10,000 | **H** (unknown) |

## Status interpretation gaps

- Legend covers **A** = Active, **C** = Closed only.
- **A-104** (`S`) and **A-105** (`H`): no legend entry, no `award_status_label` row.
- **A-101, A-102, A-103**: labeled and legend-backed.

## Match / waiver unresolved

- `award_match_obligation` mirrors `program_match_rule` for every award (consistent).
- Four **SEED-CORE** awards flagged `seed_core_waiver_unknown`: packet lacks waiver letters; cannot confirm whether 20% match applies or is waived. Affects A-101, A-103, A-104, A-105 (not A-102 — SEED-FAST, no match).
- Obligation rows still say `match_required=yes`; unresolved is epistemic, not a contradiction in WORLD facts.

## Purpose requirements & failures

From `world.purpose.json` — 5 requirement types; 3 produced failures (8 rows):

| requirement | kind | failures |
|---|---|---|
| `remaining_balance_numeric` | NUMERIC | none |
| `award_amount_numeric` | NUMERIC | none |
| `award_status_interpretable` | INTERPRETED (known: A, C) | 2 × UNINTERPRETED (A-104, A-105) |
| `status_code_not_in_legend` | UNRESOLVED | 2 × EXPLICIT_UNRESOLVED (S, H) |
| `seed_core_waiver_unknown` | UNRESOLVED | 4 × EXPLICIT_UNRESOLVED (all SEED-CORE) |

Failure kinds: `UNINTERPRETED` (MECHANICAL origin), `EXPLICIT_UNRESOLVED` (SEMANTIC origin). All `grounding_ref` empty.

## Grounding

- WORLD BASE tuples: 30 SOURCE groundings (one per fact assertion); handles point to packet fragments (`awards.csv`, `disbursements.csv`, `orgs.json`, `program_rules.txt`, `status_fragment.txt`) — no raw sources in workspace.
- PURPOSE failures: 0 SOURCE groundings (expected).
- Origins: 32 MECHANICAL, 6 SEMANTIC assertions overall.

## Data-quality hooks (not failures)

- **ORG-MEADOW** and **ORG-HARBOR** share EIN `81-1111111` — may matter for org-level dedup checks.
- Empty query ≠ established absence (per HEADER read rules).
- Unresolved/unknown does not negate established numeric facts.

## Useful analysis angles

1. Remaining balance by org/program/status (join `award` + `award_remaining_balance` + `organization`).
2. Filter interpretable vs uninterpretable status; cross-walk `purpose_requirement_failure`.
3. SEED-CORE match exposure: obligated awards vs waiver-unknown set.
4. Fully disbursed vs active-with-balance cohorts.
5. Reconcile disbursements to balances (currently consistent — good sanity check).
