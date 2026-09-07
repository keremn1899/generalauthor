# World notes (v0, revision 42)

## Purpose

Answer three questions for a shop tool-checkout domain:

1. Which checkouts are **authorized** (member certification vs tool requirement)?
2. What **fees** apply per checkout (hourly rate, hours, after-hours multiplier, identity remap)?
3. Where does **evidence or interpretation** remain insufficient (note meanings, coverage gaps)?

## Scope split

| Scope | Relations | Role |
|-------|-----------|------|
| **WORLD** | `member_record`, `tool_record`, `tool_identity_remap`, `checkout_record` | Source-grounded facts (MECHANICAL assertions) |
| **PURPOSE** | `checkout_authorization`, `checkout_fee`, `purpose_requirement_failure` | Analytical outputs (ADJUDICATED / SEMANTIC); do not treat as replacements for WORLD facts |

## Entity inventory

- **3 tools**: Laser cutter (`LASER-A`, cert `LASER-1`, $12/hr), CNC mill (`CNC-1`, cert `CNC-1`, $18/hr), Table saw (`SAW-1`, no cert, $4/hr)
- **3 members**: M-17 Jordan Lee (`LASER-1`), M-18 Sam Ortiz (`CNC-1`), M-19 "Laser A" (no certs)
- **1 identity remap**: `L1` → `tool:LASER-A`
- **7 checkouts** (C1–C7), Jul 1–4 2024

## Authorization (6 authorized, 1 unauthorized)

| Checkout | Member | Tool | Status | Basis |
|----------|--------|------|--------|-------|
| C1 | M-17 | LASER-A | authorized | has LASER-1 |
| C2 | M-18 | CNC-1 | authorized | has CNC-1 |
| C3 | M-17 | SAW-1 | authorized | no cert required |
| C4 | M-19 | LASER-A | **unauthorized** | missing LASER-1 |
| C5 | M-18 | CNC-1 | authorized | has CNC-1 |
| C6 | M-17 | L1 | authorized | has LASER-1 (via remap) |
| C7 | M-17 | LASER-A | authorized | has LASER-1 |

Only **C4** fails certification. Fees are still computed for it ($18).

## Fees (all 7 populated)

- Formula evident from rows: `total_fee = hourly_rate × hours × after_hours_multiplier`
- **After-hours (×1.5)**: C4 (out 21:30), C7 (out 21:15). Daytime and 18:00 (C1) stay ×1 → threshold appears to be **21:00**.
- **Identity remap**: C6 lists `tool_id=L1`; `checkout_fee.resolved_tool` = `tool:LASER-A` at $12/hr.
- **Totals**: $184 overall ($166 authorized + $18 unauthorized).

## Unresolved / coverage gaps

- **Explicit failure** (`purpose_requirement_failure`, `EXPLICIT_UNRESOLVED`): checkout **C5** note `PENDING` — meaning undefined under shop rules. Recorded in `purpose_requirement_failure` with `grounding_ref=checkout_id=C5`.
- **C3** note `HOLD` — present in `checkout_record` but **no** corresponding requirement failure; only PENDING is flagged unresolved.
- Purpose spec (`world.purpose.json`) also marks `authorization_status` as INTERPRETED (`authorized`/`unauthorized` known) and `total_fee` as NUMERIC.

## Grounding patterns

- **WORLD BASE**: SOURCE + MECHANICAL origin (e.g. checkout/member/tool tuples).
- **PURPOSE BASE**: ADJUDICATED origin for auth/fee rows; SEMANTIC for requirement failures.
- Use `TaskViewAgentSurface.describe(why={relation, tuple})` for per-tuple grounding; internal `_tv_*` tables are query-restricted.
- `query_semantic` on relations uses **physical column names** (`checkout_id`, not `checkout`); `relation_rows()` maps to role names.

## Read rules (from header)

- Unresolved / insufficient / unknown ≠ false.
- Empty query result = no matching tuple observed, not proven absence.
- Unknown neighbors do not invalidate established propositions unless a dependency says so.

## Access

```python
from research.semantic_integration.runtime_v0.world import ConstructionWorld
world = ConstructionWorld.open("world/world.sqlite")
rows = world.relation_rows("checkout_authorization")
# or world.query_semantic('SELECT ... FROM checkout_fee')
```

Do not modify `world/world.sqlite`.
