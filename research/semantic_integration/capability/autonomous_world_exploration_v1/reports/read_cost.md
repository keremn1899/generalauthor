# Read cost

## MEASURED

Compact header sizes (constructor contract, no rows):

| domain | HEADER.md bytes |
| --- | --- |
| harbor_towing | 2432 |
| seed_grants | 2226 |
| makerspace_checkout | ~2.1–2.4k (empty constructor meanings on most relations) |

E0 initial context (header + ACCESS + TASKS + AGENT): ~3.6–3.8 KB.  
E1 orientation context (header + ACCESS + AGENT): ~3.4 KB; TASKS added only in phase 2.

| arm / phase | mean reads | mean shells | HEADER rereads | `describe()` | selects (shell log) | grounding inspections |
| --- | --- | --- | --- | --- | --- | --- |
| E0 task | 6.4 | 3.8 | 1.0 | 0 | 4.1 | 0 |
| E1 orient | 10.2 | 8.0 | 1.0 | 0 | 5.1 | 3.1 |
| E1 task | 6.3 | 2.6 | 1.0 | 0 | 3.0 | 0 |

Seed/makerspace WORLD CONTRACT meanings were often `(none provided)`. Agents did not compensate with extra `describe()` calls; they queried rows using relation names from the header.

State before first correct downstream result: not instrumented per-answer. Episode-level E0 ~6 reads before `answers.json` is consistent with “header + a handful of queries,” not exhaustive scan.

## OBSERVED

The compact header substituted for schema rediscovery (`describe()` = 0). Cost of E1 is an extra orientation pass (~10 reads), not a smaller later task pass (task reads stay ~6).

Missing from the header that agents filled by querying: row contents, join key formatting (`job:J1` vs `J1`, `V-NORTH` vs `vessel:V-NORTH`), which PURPOSE rows exist per job.

## HYPOTHESIS

PURPOSE + CONTRACT + READ RULES + REVISION is sufficient initial context for this World size. Orientation remains “read some rows,” which is ordinary SQL, not a missing product summary. Do not add preloaded samples on this evidence.
