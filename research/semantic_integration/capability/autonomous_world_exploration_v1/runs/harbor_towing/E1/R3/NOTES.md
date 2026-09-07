# Harbor Tow Billing — Working Notes

## Purpose

Decide which towing jobs are billable, at what rate, and for how much; flag jobs where evidence is too thin for a confident charge. Seven jobs (J1–J7), four billable, three `insufficient_evidence`. Confident total: **$4,200**.

## Relation Layers

| Scope | Relations | Role |
|-------|-----------|------|
| **WORLD** | `tow_job`, `vessel`, `rate_card`, `berth_restriction` | Source facts (jobs, fleet, published rates, berth rules) |
| **PURPOSE** | `billing_outcome`, `billable_hours`, `effective_rate`, `job_charge`, `purpose_requirement_failure` | Adjudicated billing state and open gaps |

`job` referent (`job:J*`) is the join key across PURPOSE relations and `tow_job`. `vessel_id` in `tow_job` is plain TEXT (`V-NORTH`, etc.), not a referent — matches `vessel` rows by stripping the `vessel:` prefix.

## Service Conditions (embedded in `basis` / `reason` fields)

Rules are not a separate relation; they appear only in adjudicated text:

- **§1** — Use named `rate_card` rate for the job's `service_code` (TOW → $240/hr).
- **§2** — Vessel-day overtime: hours beyond 8 in a calendar day at **1.5×** base rate. Applies to **J2** (V-BAY, 9 h on 2024-06-03 → $1,920 + $360 = $2,280).
- **§3** — STBY billed at **50%** of rate-card STBY rate. **J3** → $120/hr.
- **§4** — ASST jobs bill at the **ESCORT** rate-card row. **J4** → $180/hr (not the ASST row's $240).
- **§5** — Blank `billed_hours` cannot be inferred from clock time (`start_time`/`end_time`).

`minimum_hours` on `rate_card` is present but not invoked in any established charge (e.g. J7 has 1.5 h billed vs 2 h minimum, but is blocked earlier).

## Berth Restriction

One rule: **B12** — commercial towing after 18:00 requires a documented emergency (`berth_restriction`). No emergency log on file.

- **J5** — B12, 19:00–21:00 → `insufficient_evidence`
- **J7** — B12, 20:00–21:30 → `insufficient_evidence`

## Job Outcomes

| Job | Status | Charge | Key logic |
|-----|--------|--------|-----------|
| J1 | billable | $960 | 4 h × $240 TOW |
| J2 | billable | $2,280 | 9 h TOW + §2 overtime (V-BAY day > 8 h) |
| J3 | billable | $240 | 2 h STBY × $120 (§3) |
| J4 | billable | $720 | 4 h ASST × $180 ESCORT rate (§4) |
| J5 | insufficient_evidence | — | B12 after-hours, no emergency doc |
| J6 | insufficient_evidence | — | `billed_hours` blank (§5); comment "same as last week" |
| J7 | insufficient_evidence | — | B12 after-hours, no emergency doc |

No `not_billable` outcomes in this World — only `billable` and `insufficient_evidence`.

Billable jobs have aligned tuples in `billable_hours`, `effective_rate`, and `job_charge`. Insufficient jobs have `billing_outcome` only; the other three PURPOSE relations are empty for them.

## Unresolved / Requirement State

`purpose_requirement_failure` records two kinds of gap:

**EXPLICIT_UNRESOLVED** — substantive evidence holes (3 rows):
- `berth_b12_after_hours` → J5, J7 (grounding: `berth_notice.txt`)
- `blank_billed_hours` → J6 (grounding: `jobs.csv`)

**NOT_ESTABLISHED** — schema-level requirements not formally closed (3 rows):
- `one_outcome_per_job`, `billing_status_known`, `charge_amount_numeric`

The data appears to satisfy the latter (7 jobs → 7 unique outcomes; known status values; numeric charges on billable jobs), but the requirements are recorded as not established. Treat as audit incompleteness, not a data violation.

## Grounding & Origins

- **WORLD** assertions: `MECHANICAL` construction origin + `SOURCE` grounding (`jobs.csv`, `vessels.csv`, `rate_card.csv`, `berth_notice.txt`). No raw files in workspace — only grounding refs in SQLite.
- **PURPOSE** assertions: `ADJUDICATED` origin (semantic judgment on service conditions). Grounding is `WORLD: origin:ADJUDICATED` without source pointers.
- Sidecar `world.sqlite.origins.json` maps assertion IDs → construction origin (ADJUDICATED / MECHANICAL / SEMANTIC).

Inspect per-tuple grounding via `taskview.inspect_tuple(relation, {role: value, ...})` using **semantic role names** (`job`, not `job_id`).

## Read Rules (from HEADER)

- Unresolved / insufficient ≠ false.
- Empty query result ≠ established absence.
- PURPOSE state does not override WORLD facts.
- Unknown neighbors don't invalidate established propositions unless a dependency says so.

## Querying

```python
from research.semantic_integration.runtime_v0.world import ConstructionWorld
world = ConstructionWorld.open("world/world.sqlite")
world.relation_rows("billing_outcome")          # role-named dicts
world.query_semantic("SELECT ...")              # SQL on physical column names (job_id, etc.)
```

`view_id=v0`, `schema_revision=50`. Do not modify the World.
