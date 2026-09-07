# Harbor towing billing World — working notes

## Purpose

Decide which towing jobs are billable at which rates under harbor service conditions, and flag jobs where evidence is too thin for a confident charge. Analytical state lives in PURPOSE relations; source facts in WORLD relations.

## Access

```python
from research.semantic_integration.runtime_v0.world import ConstructionWorld
world = ConstructionWorld.open("world/world.sqlite")
world.relation_rows("tow_job")          # role names (job, berth, …)
world.query_semantic("SELECT …")        # SQL uses physical columns (job_id, not job)
```

Grounding: `TaskViewAgentSurface(world.taskview).describe(why={"relation": r, "tuple": row})`.

Read rules (HEADER): `insufficient_evidence` ≠ “not billable”; empty query result ≠ proven absence; inspect grounding when evidential status matters.

## Relation layers

| Scope | Relations | Origin | Grounding |
|-------|-----------|--------|-----------|
| WORLD | `tow_job`, `vessel`, `rate_card`, `berth_restriction` | MECHANICAL | SOURCE (file handles + revisions) |
| PURPOSE | `billing_outcome`, `billable_hours`, `effective_rate`, `job_charge` | ADJUDICATED | construction judgment, cites service_conditions §n in `basis`/`reason` |
| PURPOSE | `purpose_requirement_failure` | SEMANTIC (explicit unresolved) or MECHANICAL (NOT_ESTABLISHED) | see below |

All relations are BASE (no DERIVED). `view_id=v0`, `schema_revision=50`.

## Entity graph

- **Jobs** `job:J1`–`job:J7` — hub referent; join key is `job_id` / role `job`.
- **Vessels** `vessel:V-NORTH`, `V-BAY`, `V-REEF` — linked from `tow_job.vessel_id` (text id, not a formal FK).
- **Rates** — `rate_card` keyed by `service_code` (TOW/STBY/ASST/ESCORT); `effective_rate` is per-job after conditions.
- **Berth rule** — one row: B12 restricts commercial towing after 18:00 unless documented emergency.

## Job inventory (7 rows)

| Job | Berth | Svc | Billed hrs | Outcome | Charge |
|-----|-------|-----|------------|---------|--------|
| J1 | B4 | TOW | 4 | billable | 960 |
| J2 | B4 | TOW | 9 | billable | 2280 |
| J3 | B7 | STBY | 2 | billable | 240 |
| J4 | B9 | ASST | 4 | billable | 720 |
| J5 | B12 | TOW | 2 | insufficient_evidence | — |
| J6 | B4 | TOW | *(blank)* | insufficient_evidence | — |
| J7 | B12 | TOW | 1.5 | insufficient_evidence | — |

No `not_billable` outcomes in the World. Billable jobs have full PURPOSE chain (`billable_hours`, `effective_rate`, `job_charge`, `billing_outcome`); blocked jobs have outcome only.

## Service conditions (encoded in PURPOSE `basis`/`reason`)

1. **§1** — Use named `rate_card` rate for the job’s service code (TOW → 240/hr).
2. **§2** — Overtime: when a vessel’s same-day total billed hours > 8, excess at 1.5× (J2: V-BAY 9h → 8×240 + 1×360 = 2280).
3. **§3** — STBY billed at 50% of rate_card STBY rate (J3: 120/hr).
4. **§4** — ASST jobs use ESCORT rate_card row (J4: 180/hr, not ASST 240).
5. **§5** — Blank `billed_hours` does not establish billable quantity; clock duration alone is insufficient (J6).

`rate_card.minimum_hours` exists but is not cited in any adjudicated charge in this World.

## Unresolved / insufficient evidence

Three explicit SEMANTIC failures (`purpose_requirement_failure`, `EXPLICIT_UNRESOLVED`):

- **berth_b12_after_hours** — J5 (19:00–21:00) and J7 (20:00–21:30) at B12; restriction applies, no emergency log (`grounding_ref`: berth_notice.txt).
- **blank_billed_hours** — J6; comment “same as last week” does not substitute (§5).

Matching `billing_outcome.status = insufficient_evidence` with aligned reasons. No charge/hours/rate tuples for these jobs.

## Purpose requirement failures (meta)

Three `NOT_ESTABLISHED` rows on PURPOSE relations (`one_outcome_per_job`, `billing_status_known`, `charge_amount_numeric`): mechanical validators cannot run against PURPOSE-scoped relations, so uniqueness/interpretation/numeric checks defer to ADJUDICATED assertions. These are audit receipts, not per-job defects.

## Query patterns

```sql
-- Full billing picture (physical column names)
SELECT tow_job.job_id, tow_job.berth, tow_job.service_code, tow_job.billed_hours,
       billing_outcome.status, billing_outcome.reason,
       billable_hours.hours, effective_rate.rate_per_hour, job_charge.charge
FROM tow_job
LEFT JOIN billing_outcome ON billing_outcome.job_id = tow_job.job_id
LEFT JOIN billable_hours ON billable_hours.job_id = tow_job.job_id
LEFT JOIN effective_rate ON effective_rate.job_id = tow_job.job_id
LEFT JOIN job_charge ON job_charge.job_id = tow_job.job_id
ORDER BY tow_job.job_id;
```

Filter `billing_outcome.status`, join `vessel` indirectly via `tow_job.vessel_id`, or aggregate charges on billable subset only.

## Analysis angles

- Revenue rollups and rate-condition breakdown (§1–§4).
- Evidence gaps vs berth/time rules (§5, B12 restriction).
- Cross-check adjudicated charges against hours × effective_rate.
- Vessel-day overtime grouping (§2 needs same vessel + date).
- Grounding provenance: WORLD tuples trace to source files; PURPOSE tuples to ADJUDICATED judgment.
