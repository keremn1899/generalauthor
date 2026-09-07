# World notes (v0, schema_revision=42)

## Purpose

Shop tool-checkout domain: decide **authorization** (cert-gated tool use), **fees** (hourly rate × hours × after-hours multiplier, with tool-ID remapping), and flag **insufficiently evidenced** note semantics. Analytical outputs live in PURPOSE relations; operational facts in WORLD relations.

## Relation map

| Relation | Scope | Rows | Role |
|---|---|---:|---|
| `member_record` | WORLD | 3 | member name + comma-free cert string |
| `tool_record` | WORLD | 3 | tool name, `cert_required`, `hourly_fee` |
| `checkout_record` | WORLD | 7 | checkout events: member, bare `tool_id`, times, `note`, `hours_marked` |
| `tool_identity_remap` | WORLD | 1 | legacy ID → tool referent (`L1` → `tool:LASER-A`) |
| `checkout_authorization` | PURPOSE | 7 | per-checkout `status` (`authorized` \| `unauthorized`) + `basis` |
| `checkout_fee` | PURPOSE | 7 | resolved tool, rate, hours, multiplier, `total_fee` |
| `purpose_requirement_failure` | PURPOSE | 1 | explicit coverage/unresolved marker |

No derived relations. Completeness receipts are null on all relations.

## Entities (compact)

**Members:** M-17 Jordan Lee (LASER-1); M-18 Sam Ortiz (CNC-1); M-19 "Laser A" (no certs).

**Tools:** LASER-A laser cutter (LASER-1 cert, $12/hr); CNC-1 mill (CNC-1 cert, $18/hr); SAW-1 table saw (no cert, $4/hr).

**Checkouts C1–C7** (2024-07-01..04). Notable cases:
- **C4** — M-19 + LASER-A → **unauthorized** (missing LASER-1); fee still computed ($18, 1.5× after-hours).
- **C6** — `tool_id=L1` resolves via remap to LASER-A; authorized (M-17 has LASER-1).
- **C3** — note `HOLD` (no failure recorded).
- **C5** — note `PENDING` → **EXPLICIT_UNRESOLVED** (shop rules do not define PENDING).

## Rules inferred from populated PURPOSE rows

**Authorization:** If tool `cert_required` is empty → authorized. Else member `certs` must contain that cert string. Matches all 7 adjudicated rows.

**Fees:** `total_fee = hourly_rate(resolved_tool) × hours_marked × after_hours_multiplier`. Tool resolution: direct `tool:{tool_id}` or remap lookup. Verified for all rows; **grand total $184.00**.

**After-hours:** Multiplier **1.5** when checkout `out_time` hour ≥ 21 (C4 21:30, C7 21:15). Multiplier **1** otherwise (incl. C1 at 18:00).

## Unresolved / evidential state

- One `purpose_requirement_failure`: requirement `checkout_note_meaning`, kind `EXPLICIT_UNRESOLVED`, subject C5 / note PENDING. Origin **SEMANTIC** (explicit flag, not inferred absence).
- PURPOSE auth/fees: origin **ADJUDICATED** (no SOURCE grounding).
- WORLD tuples: origin **MECHANICAL** with **SOURCE** grounding to compiled file handles (`members.csv`, `tools.csv`, `checkouts.csv`, `adr.txt`). Raw sources not present in workspace; grounding refs exist for provenance checks.

**Read rules (from header):** unresolved ≠ false; empty query ≠ established absence; PURPOSE does not override WORLD facts; inspect grounding when evidence status matters.

## Query tips

- Semantic role names (`checkout`, `member`, `tool`) via `relation_rows()`; SQL uses physical columns (`checkout_id`, `member_id`, …).
- Join checkouts → auth/fees on `checkout_id`.
- `checkout_record.tool_id` is bare (`LASER-A`, `L1`); `checkout_fee.resolved_tool_id` is referent form (`tool:LASER-A`).

## Analysis hooks

- Authorization audit (C4 violation; cert matrix).
- Fee rollups by member, tool, day; after-hours uplift (C4, C7).
- Identity-remap impact (C6 would fail resolution without `tool_identity_remap`).
- Unauthorized-but-billed question (C4).
- Coverage gap on checkout notes (PENDING unresolved; HOLD present but not flagged).
- Cross-check PURPOSE vs recomputing from WORLD + inferred rules.
