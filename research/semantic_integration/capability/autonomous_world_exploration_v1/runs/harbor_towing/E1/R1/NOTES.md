# Working notes — harbor towing billing World

## Purpose

Decide which tow jobs are billable, at what effective hourly rate (after harbor service conditions), and what charge applies. Flag jobs where evidence is too thin for a confident amount. View `v0`, schema revision 50.

## Shape (small, fixed)

| Layer | Relations | Rows |
|-------|-----------|------|
| WORLD (source facts) | `tow_job`, `vessel`, `rate_card`, `berth_restriction` | 7 / 3 / 4 / 1 |
| PURPOSE (billing state) | `billing_outcome`, `billable_hours`, `effective_rate`, `job_charge`, `purpose_requirement_failure` | 7 / 4 / 4 / 4 / 6 |

Seven jobs (`job:J1`–`job:J7`), three tugs, four rate-card codes (`TOW`, `STBY`, `ASST`, `ESCORT`). One berth rule: **B12** — no commercial towing after 18:00 except a documented emergency.

## Entity keys & joins

- Job referent: `job_id` = `job:J{n}` (role name `job` in `relation_rows()`).
- Vessel: `tow_job.vessel_id` is bare id (`V-NORTH`); `vessel.vessel_id` is referent (`vessel:V-NORTH`). Join: `vessel.vessel_id = 'vessel:' || tow_job.vessel_id`.
- All PURPOSE rows keyed by `job_id`. Billable pipeline exists only where `billing_outcome.status = 'billable'` (4 jobs); insufficient jobs have outcome only—no hours/rate/charge tuples.

## Billing logic (from `basis` / `reason`, not a separate rules relation)

Service conditions cited in adjudicated rows:

1. **§1** — `effective_rate` = `rate_card` rate for job's `service_code` (J1, J2: TOW @ 240).
2. **§2** — Overtime: when a **vessel's same-day total** billed hours > 8, excess at 1.5× base (J2: V-BAY 9h → 8×240 + 1×360 = 2280).
3. **§3** — `STBY` billed at **50%** of card rate (J3: 120/hr, not 240).
4. **§4** — `ASST` jobs use the **`ESCORT`** rate row (J4: 180/hr, not 240).
5. **§5** — Blank `billed_hours` is **not** an established billable quantity; clock span alone does not substitute (J6).

`rate_card.minimum_hours` is present but **not applied** in current charges (e.g. J3 has 2h billed, STBY min 1h — no bump evident).

## Outcomes by job

| Job | Status | Charge | Blocker / note |
|-----|--------|--------|----------------|
| J1 | billable | 960 | straight TOW 4h |
| J2 | billable | 2280 | overtime (§2) |
| J3 | billable | 240 | STBY half-rate (§3) |
| J4 | billable | 720 | ASST→ESCORT (§4) |
| J5 | insufficient_evidence | — | B12 TOW 19:00–21:00, no emergency log |
| J6 | insufficient_evidence | — | empty `billed_hours` (§5) |
| J7 | insufficient_evidence | — | B12 TOW 20:00–21:30, no emergency log |

**Total established charges: 4200.** No `not_billable` rows in this World.

## Unresolved & requirement failures

`purpose_requirement_failure` records two kinds:

- **EXPLICIT_UNRESOLVED** (MECHANICAL): `berth_b12_after_hours` → J5, J7; `blank_billed_hours` → J6. These align with `billing_outcome` insufficient reasons.
- **NOT_ESTABLISHED** (SEMANTIC): formal checks on `one_outcome_per_job`, `billing_status_known`, `charge_amount_numeric` — requirement satisfaction not recorded, though data rows exist. Do not treat as data absence.

Per HEADER: unresolved ≠ false; empty query ≠ established absence.

## Grounding & provenance

- **WORLD BASE** assertions: dual **SOURCE** (file handles in groundings) + **WORLD** grounding. Construction origin **MECHANICAL** (loaded from tabular/notice inputs).
- **PURPOSE** assertions: **WORLD** grounding only; construction origin **ADJUDICATED** (human/semantic billing judgments). No raw sources in workspace — inspect `basis`, `reason`, `grounding_ref` on failures when evidential status matters.
- `purpose_requirement_failure` mixes MECHANICAL (explicit gaps) and SEMANTIC (unverified constraints).

## Query patterns

```python
from research.semantic_integration.runtime_v0.world import ConstructionWorld
world = ConstructionWorld.open("world/world.sqlite")
world.relation_rows("billing_outcome")          # semantic role names
world.query_semantic("SELECT ... FROM tow_job") # physical columns (job_id, ...)
```

Protected `_tv_*` tables: use `sqlite3` read-only for referents/groundings if needed; `query_semantic` blocks some columns.

Useful join for full picture:

```sql
SELECT t.job_id, bo.status, bh.hours, er.rate_per_hour, jc.charge, bo.reason
FROM tow_job t
LEFT JOIN billing_outcome bo ON t.job_id = bo.job_id
LEFT JOIN billable_hours bh ON t.job_id = bh.job_id
LEFT JOIN effective_rate er ON t.job_id = er.job_id
LEFT JOIN job_charge jc ON t.job_id = jc.job_id
ORDER BY t.job_id
```

## Analysis angles this World supports

- Revenue rollups / per-vessel or per-berth totals (billable subset only).
- Rate-rule coverage: which service codes appear, which conditions (§2–§4) fired.
- Evidence-gap reporting via `insufficient_evidence` + `purpose_requirement_failure`.
- Sensitivity: what J5/J6/J7 would need (emergency doc, billed hours) before billing tuples could be asserted.
- Constraint validation: whether NOT_ESTABLISHED requirements should be re-run or satisfied.
