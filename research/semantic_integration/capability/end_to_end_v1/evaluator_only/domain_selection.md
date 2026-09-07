# Domain selection — frozen before any host run

**Experiment:** End-to-End Semantic Compilation Capability Probe v1  
**Runtime:** Spike 1 `runtime_v0` frozen (`SPIKE1_RUNTIME_LOOP_SUPPORTED`)  
**Model:** Composer 2.5  
**Frozen at:** 2026-09-06, prior to construction trial T1

This file is evaluator-only. Host and consumer workspaces must not contain it.

## Exclusion

Not used (prior semantic-integration experiments):

```text
BOM
diligence / AXIS D
NPDES / DMR / permit packages
minimal_v0 orders/accounts GM fixture
```

No renamed copies of those corpora.

## Selected domains

| id | Working title | Why eligible |
| --- | --- | --- |
| `harbor_towing` | Municipal harbor towing jobs | Commercial operations evidence; not environmental permitting |
| `seed_grants` | Municipal micro-grant awards | Program administration; not diligence counterparties |
| `makerspace_checkout` | Community workshop tool checkout | Operations/certs/fees; not BOM replacement |

Each folder is newly authored for this probe. None of these files, entity ids, or hidden questions have appeared in prior sealed probes.

## Evidence-shape coverage (required A–E)

| Domain | A mechanical | B prose | C opaque payload | D misleading correlation | E genuine insufficiency |
| --- | --- | --- | --- | --- | --- |
| harbor_towing | job ↔ rate_card ↔ vessel keys | ASST billed as escort; OT after 8h; STBY at 50% | blank `billed_hours`; service codes | vessel display_name `B12` vs berth `B12` | fuel surcharge; B12 after-hours emergency |
| seed_grants | award ↔ disbursements ↔ org | SEED-FAST no match; CORE 20% match | status `S`,`H` | shared EIN + similar legal names | status S meaning; match waiver |
| makerspace_checkout | checkout ↔ tool ↔ member; L1→LASER-A ADR | after-21:00 1.5x; HOLD not extra day | `PENDING` note | member name `Laser A` vs tool `LASER-A` | PENDING meaning; insurance rider |

## Construction design (frozen)

```text
3 domains × 2 isolated trials = 6 construction runs
≤ 3 construction.py attempts per trial
Composer 2.5
no GOLD, no hidden questions, no human correction
```

## WORLD consumer World selection (frozen before scoring)

For each domain, use the **lowest trial index** (`T1` then `T2`) that produced `ACCEPTED`.

Do not pick the “better looking” World after reading gold.

If neither trial is accepted, skip WORLD consumers for that domain and record `NO_ACCEPTED_WORLD`.

## Consumer design (frozen)

```text
3 WORLD + 3 RAW consumers per domain = 18
same 6 hidden questions
WORLD: purpose + accepted World + TaskView/SQL; no raw sources
RAW: purpose + raw folder; no World
```
