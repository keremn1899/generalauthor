# World notes

## Purpose

Adjudicate **tool-shop checkouts**: which are authorized under cert rules, what fees apply (including tool-identity remaps and after-hours), and where evidence is insufficient. Seven checkouts (C1–C7), three members, three tools.

## Access

```python
from research.semantic_integration.runtime_v0.world import ConstructionWorld
world = ConstructionWorld.open("world/world.sqlite")
world.query_semantic("SELECT ...")   # SQL over relation tables
world.relation_rows("checkout_record")  # role-named dicts
```

`query_semantic` uses **physical column names** (`checkout_id`, `member_id`, `resolved_tool_id`, …), not role names. Join on referent IDs (`checkout:C1`, `member:M-17`, `tool:LASER-A`).

## Relations

| Relation | Scope | Origin | Rows | Role |
|----------|-------|--------|------|------|
| `member_record` | WORLD | MECHANICAL | 3 | member, name, certs |
| `tool_record` | WORLD | MECHANICAL | 3 | tool, name, cert_required, hourly_fee |
| `checkout_record` | WORLD | MECHANICAL | 7 | checkout, member, tool_id, times, note, hours_marked |
| `tool_identity_remap` | WORLD | MECHANICAL | 1 | from_tool_id → to_tool (L1 → tool:LASER-A, from adr.txt) |
| `checkout_authorization` | PURPOSE | ADJUDICATED | 7 | checkout, status, basis |
| `checkout_fee` | PURPOSE | ADJUDICATED | 7 | checkout, resolved_tool, rate, hours, multiplier, total_fee |
| `purpose_requirement_failure` | PURPOSE | SEMANTIC | 1 | unresolved/evidence gaps |

WORLD tuples are SOURCE-grounded (csv/adr files referenced in grounding, not available here). PURPOSE tuples are adjudicated analytical output — do not treat as raw facts.

## Entity sketch

**Members:** M-17 Jordan Lee (LASER-1), M-18 Sam Ortiz (CNC-1), M-19 Laser A (no certs).

**Tools:** LASER-A laser cutter ($12/h, needs LASER-1), CNC-1 mill ($18/h, CNC-1), SAW-1 table saw ($4/h, no cert).

**Join path:** `checkout_record.member_id` → `member_record`; `checkout_fee.resolved_tool_id` → `tool_record`. `checkout_record.tool_id` is a short code; fee resolution uses `tool_identity_remap` when needed (only C6: L1 → LASER-A).

## Rules (as encoded)

**Authorization:** `authorized` if member cert matches `cert_required`, or cert_required is empty. One `unauthorized`: **C4** (M-19, no cert, LASER-A needs LASER-1). Six authorized.

**Fees:** `total_fee = hourly_rate × hours × after_hours_multiplier`. Hours match `hours_marked` (and elapsed out→in time). After-hours multiplier **1.5** when checkout starts at hour ≥ 21 (C4, C7); otherwise 1. C1 starts 18:00 → regular rate.

**Unauthorized still has a fee row** (C4 = $18.0) — authorization and billing are separate PURPOSE relations.

## Unresolved / evidence gaps

- **C5 note `PENDING`:** explicit `purpose_requirement_failure` (`EXPLICIT_UNRESOLVED`) — shop rules do not define PENDING. Checkout otherwise authorized and billed normally.
- **C3 note `HOLD`:** no failure recorded; meaning undefined but not flagged unresolved.
- Per read rules: empty query ≠ established absence; unknown neighbors don't invalidate established facts.

## Grounding

- WORLD: SOURCE + WORLD origin metadata per assertion.
- PURPOSE: WORLD grounding with `origin:ADJUDICATED` (no source file).
- Source handles in grounding: `members.csv`, `tools.csv`, `checkouts.csv`, `adr.txt`.

## Useful aggregates

- Total fees (all 7): $184.0; authorized only: $166.0.
- After-hours checkouts: C4 ($18), C7 ($18).
- Identity remap affects: C6 only.

## Schema revision

view_id=v0, schema_revision=42.
