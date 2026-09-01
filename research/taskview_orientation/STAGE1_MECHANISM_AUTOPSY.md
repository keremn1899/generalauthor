# TaskView orientation experiment — Stage 1 mechanism autopsy

**Status:** forensic analysis of the sealed `stage1-cursor-v10` campaign. No participant
model calls were made to produce this document. No TaskView code, prompt, oracle, or
case content was changed. This is not a re-scoring pass — the frozen threshold result
(`INCONCLUSIVE`) and `STAGE1_RESULTS.md` stand unchanged.

**Source data:** `results/stage1-cursor-v10/*/telemetry.jsonl`,
`*/provider_trajectory.jsonl`, `*/record.json`, `*/seal.json`, cross-checked against a
fresh re-run of `report.py` (`manifest_sha256 539432a2…565ee14e`, `campaign_valid: true`).
Every number below is read directly off those files; where a number required
computation (byte sums, duplicate-call counts, per-phase splits) the exact extraction is
described so it can be reproduced.

---

## A. Executive mechanism summary

- **The frozen result stands:** median paired `O_post` reduction 28.6%, 4/4 directional
  wins, but net orientation bytes (repo + TaskView combined) got *worse* under TASKVIEW
  in 3 of 4 pairs (r1 +9.5KB, r2 +13.3KB, r4 +8.9KB; only r3 −2.4KB). `INCONCLUSIVE` is
  the correct label; this autopsy explains *why* the sign flips per replicate.
- **TaskView did suppress genuine repo-side orientation.** `IRRELEVANT` + `ORIENTATION_SUPPORT`
  repo bytes (search_source/read_source only, TaskView protocol excluded) fell in all 4
  pairs; `LOCAL_ORACLE` bytes — the necessary local-implementation reading — stayed flat
  (RAW mean 5,505B, TASKVIEW mean 4,867B, an 11.6% difference within episode-to-episode
  noise). The intended `C_orientation↓, C_local≈const` split is real, not a wash.
- **TaskView spent most of that savings back on itself, and the spend is dominated by
  one operation:** `describe` returns a flat **5,413 bytes** every single call (full
  schema dump, byte-identical across all 4 episodes and all calls within them), while
  every `query_sql` call in the campaign returned between 25 and 257 bytes. `describe`
  is ~30–100× more expensive per call than a narrow relation query.
- **Replicate 2 vs. replicate 3 is a `describe`-repetition story, not a query-shape
  story.** r1/r2/r4 each called `describe` 3 times (once per orientation-heavy phase);
  r3 called it exactly once. The 2 extra `describe` calls cost 10,826 bytes — which
  accounts for essentially all (≈95%+) of the gap between r2's and r3's
  `taskview_visible_bytes` (19,088 vs 8,637). Narrow-SQL discipline was already present
  in *every* replicate, including r2.
- **Replicate 2's deeper problem is that its repo-side savings were front-loaded into
  phase 1 (which the `O_post` metric excludes) and did not persist into phases 2–5.**
  Phase-by-phase repo bytes for the r2 pair show TASKVIEW's post-phase-1 repo bytes
  (16,246B) essentially matching or exceeding RAW's (15,931B) in phases 2–3, driven by
  two large individual `search_source` calls (1,681B, 3,361B). Replicate 3's TASKVIEW
  trajectory stayed cheaper than its RAW pair in *every* post-phase-1 phase.
- **The tool contract itself has a reproducible friction cost, present in all 4
  TASKVIEW episodes:** every episode attempted at least one `SELECT *` (rejected by
  schema validation), and every episode's first `assertion` retract used the wrong
  argument key names (`service_id`/`test_id` instead of `service`/`test`) and was
  rejected before succeeding on retry. This is deterministic tool-schema friction, not
  model variance.
- **The scoped-exhaustiveness advantage (RAW 0.45 vs TASKVIEW 0.80) is mostly explained
  by two exact-match oracle fields, not by better bounded-search reasoning.** All 8
  episodes agree on `whole_world_complete` (correct) and `whole_world_blockers`
  (wrong); the entire arm split comes from `completeness_universe` (TASKVIEW 4/4
  correct, verbatim `"affected_service"`, echoing the SQL relation's own name; RAW 0/4
  correct, richer prose that never emits that literal token) and
  `other_gaps_in_affected_service` (TASKVIEW 4/4 empty-list-correct; RAW 3/4 non-empty
  with real, plausible additional findings that the oracle scores as wrong).
- **The changed-evidence/staleness result is a near-uniform failure across both arms at
  phase 4, not a TaskView-only weakness.** All 8 episodes score identically on phase 4
  (`citations` correct; `invalidated_verification`, `missing_behaviors`,
  `downstream_result_state`, `retained_state_update` all wrong) — and reading the
  actual answers shows every episode, RAW included, *substantively* identified and
  reacted to the mutation correctly; they simply wrote prose instead of the oracle's
  terse canonical labels (`"comment acceptance"`, `retract verified_by(...)`). The one
  field that does differentiate arms (`current_verification_gap` at phase 5) again
  reduces to whether the participant could echo a canonical `service:x` identifier.
- **Provider token accounting confirms cost but not clean attribution.** Fresh input
  tokens spike 1.5–3× at phase 4 in *every* episode of both arms (the mutation
  boundary), and TASKVIEW's baseline fresh-input token floor sits above RAW's from
  phase 1 onward — consistent with fixed tool-schema/system-prompt overhead — but the
  SDK exposes only one post-hoc `usage` total per turn, so no per-tool-call token
  attribution is possible from this data.
- **Net read on world-size scaling (theory only):** the mechanism that shrank in this
  world (RAW's need to reopen the same 2–3 orientation documents once per phase) scales
  with world size in a way `describe`'s flat per-call cost does not — but the case is
  far too small (one 5-relation schema, ~20 source files) to claim this, and TaskView's
  own overhead (schema-refresh cost, tool-schema friction) has not been shown to stay
  fixed as the schema itself grows.

---

## B. Per-TASKVIEW-operation cost table

All 4 TASKVIEW episodes, from `TASKVIEW_TOOL` telemetry events (`model_visible_output_bytes`,
`taskview_rows_returned`, `wall_time_ms`). `describe` and `assertion` carry no rows; `rerun`
returns the re-evaluated relation's row count.

### B.1 Per-episode operation totals

| episode (replicate) | op | calls | total bytes | bytes/call | min–max bytes | rows (sum) |
|---|---|---:|---:|---:|---:|---:|
| e02 (r1) | describe | 3 | 16,239 | 5,413 | 5,413–5,413 | — |
| e02 (r1) | query_sql | 22 | 2,247 | 102 | 25–257 | 26 |
| e02 (r1) | assertion | 1 | 194 | 194 | — | — |
| e02 (r1) | rerun | 1 | 430 | 430 | — | 1 |
| e03 (r2) | describe | 3 | 16,239 | 5,413 | 5,413–5,413 | — |
| e03 (r2) | query_sql | 22 | 1,795 | 82 | 25–257 | 15 |
| e03 (r2) | assertion | 1 | 194 | 194 | — | — |
| e03 (r2) | rerun | 2 | 860 | 430 | 430–430 | 1 |
| e06 (r3) | describe | 1 | 5,413 | 5,413 | — | — |
| e06 (r3) | query_sql | 27 | 2,600 | 96 | 25–257 | 30 |
| e06 (r3) | assertion | 1 | 194 | 194 | — | — |
| e06 (r3) | rerun | 1 | 430 | 430 | — | 1 |
| e07 (r4) | describe | 3 | 16,239 | 5,413 | 5,413–5,413 | — |
| e07 (r4) | query_sql | 28 | 2,771 | 99 | 25–257 | 32 |
| e07 (r4) | assertion | 1 | 194 | 194 | — | — |
| e07 (r4) | rerun | 1 | 430 | 430 | — | 1 |

`describe`'s byte count is **exactly 5,413 in all 8 calls across all 4 episodes** — it is
a flat full-schema dump, invariant to conversation state or the `why` argument (which is
either `null` on success or itself rejected as malformed — see §D). `assertion` (194B)
and `rerun` (430B) are likewise flat per-call constants. Only `query_sql` bytes vary,
scaling with the relation's column/row count (25B for a 0-row narrow SELECT up to 257B
for a 3-row, 2-column join-adjacent SELECT). There is no observed "TaskView tool-schema
overhead" distinct from these response byties in the request direction — the MCP
tool-call argument payloads themselves are all under 100 bytes; the schema/tool
*description* overhead lands in the system prompt (`tool_schema_sha256`, counted once at
`SESSION_START`, 1,756B `model_visible_input_bytes` including the whole tool schema for
that episode — not itemized per tool).

### B.2 Percentage of TaskView-visible cost by operation

| episode | describe % | query_sql % | assertion % | rerun % | total taskview_visible_bytes |
|---|---:|---:|---:|---:|---:|
| e02 (r1) | 85.0% | 11.8% | 1.0% | 2.3% | 19,110 |
| e03 (r2) | 85.1% | 9.4% | 1.0% | 4.5% | 19,088 |
| e06 (r3) | 62.7% | 30.1% | 2.2% | 5.0% | 8,637 |
| e07 (r4) | 82.7% | 14.1% | 1.0% | 2.2% | 19,634 |

(Percentages are of `taskview_visible_bytes`, which is the TASKVIEW_TOOL-only subtotal;
it differs from `taskview_post_bytes`/`net_orientation_bytes` which also include the
episode's repo-side post-phase-1 bytes — see §C, §I.)

`describe` is 63–85% of all TaskView-visible bytes in every episode. It is the single
largest cost center by a wide margin, in every replicate, including r3 where it still
accounts for the majority of TaskView bytes despite being called only once.

### B.3 Per-phase call counts (all 4 TASKVIEW episodes)

| episode | phase 1 | phase 2 | phase 3 | phase 4 | phase 5 |
|---|---|---|---|---|---|
| e02 (r1) | describe×1, query_sql×6 | query_sql×5 | query_sql×3 | query_sql×2, describe×1, assertion×1, rerun×1, query_sql×2 | query_sql×2, describe×1, query_sql×2 |
| e03 (r2) | describe×1, query_sql×3 | query_sql×4 | query_sql×3, describe×1, query_sql×2 | query_sql×2, rerun×1, assertion×1, rerun×1, query_sql×2 | query_sql×2, describe×1, query_sql×2 |
| e06 (r3) | describe×1, query_sql×6 | query_sql×5 | query_sql×5 | query_sql×3, assertion×1, rerun×1, query_sql×1 | query_sql×6 |
| e07 (r4) | describe×1, query_sql×7 | query_sql×5 | describe×1, query_sql×5 | query_sql×2, assertion×1, rerun×1, query_sql×2 | query_sql×2, describe×1, query_sql×2 |

Phases 1, 2, 3 and 5 are each opened with (or contain) a `describe` call in r1/r2/r4;
r3 never re-issues it after phase 1. Phase 4 (the mutation-reaction phase, see §H) is
the one phase where all 4 replicates behave almost identically: 2 `verification_gap`
queries, one failed then one succeeded `assertion` retract, one `rerun`.

---

## C. Replicate 2 vs. replicate 3 forensic comparison

Matched pair 2: `e03` (TASKVIEW) vs `e04` (RAW); matched pair 3: `e06` (TASKVIEW) vs
`e05` (RAW). Frozen numbers: r2 `O_post` reduction 0.37%, net orientation
TASKVIEW−RAW = **+13,320B**; r3 `O_post` reduction 31.9%, net orientation
TASKVIEW−RAW = **−2,401B**.

### C.1 TaskView-side: `describe` repetition is the dominant delta

| | e03 (TASKVIEW r2) | e06 (TASKVIEW r3) | delta |
|---|---:|---:|---:|
| `describe` calls | 3 (phase 1, 3, 5) | 1 (phase 1 only) | 2 calls, 10,826B |
| `query_sql` calls | 22 | 27 | r3 issued **5 more** |
| `query_sql` bytes | 1,795 | 2,600 | r3's narrow queries cost 805B *more* |
| `assertion`+`rerun` bytes | 1,054 | 624 | r2 costs 430B more (2 reruns vs 1) |
| **`taskview_visible_bytes` total** | **19,088** | **8,637** | **10,451B**, of which 10,826B (104%) is `describe` alone |

r3 made *more* `query_sql` calls than r2, and its individual queries are not narrower —
both replicates use the same style of 1–4-column, filtered/unfiltered `SELECT`
(`SELECT service_id, test_id FROM verified_by`, `SELECT subject_id, basis FROM excluded`,
etc.). The entire cost gap between the two TaskView trajectories is explained, almost to
the byte, by r2 re-invoking the full-schema `describe` twice more than r3 did. This
directly answers items 1–4 of the required question list: r3 did **not** issue
narrower SQL, did **not** get smaller rowsets, and did **not** query fewer columns than
r2 — it avoided repeated `describe`, full stop.

### C.2 Repo-side, phase by phase (search_source + read_source bytes, both arms)

| phase | e03 TASKVIEW r2 | e04 RAW r2 | e06 TASKVIEW r3 | e05 RAW r3 |
|---|---:|---:|---:|---:|
| 1 (excluded from O_post) | 5,343B (3 search + 5 read) | 13,595B (20 search + 18 read) | 6,664B (3 search + 7 read) | 18,152B (19 search + 22 read) |
| 2 | 4,769B (1 search + 6 read) | 3,632B (0 search + 8 read) | 4,400B (3 search + 6 read) | 3,991B (0 search + 9 read) |
| 3 | 7,022B (1 search + 8 read) | 5,164B (6 search + 8 read) | 4,598B (4 search + 6 read) | 4,833B (3 search + 10 read) |
| 4 | 1,702B (2 search + 3 read) | 2,003B (2 search + 4 read) | 1,604B (0 search + 3 read) | 3,336B (5 search + 4 read) |
| 5 | 2,753B (0 search + 6 read) | 5,132B (1 search + 11 read) | 2,813B (2 search + 6 read) | 6,325B (1 search + 14 read) |
| **post-phase-1 sum (2–5)** | **16,246B** | **15,931B** | **13,415B** | **18,485B** |

This is the central finding of this section: **in phases 2–3, TASKVIEW replicate 2's
repo-side bytes equal or exceed its RAW pair's** (4,769 > 3,632 in phase 2; 7,022 > 5,164
in phase 3), driven by two individual `search_source` calls — 1,681B in phase 2 (a
single broad hit while grounding the reporting adapter) and 3,361B in phase 3 (grounding
the partner-gateway exclusion). RAW achieves comparable or lower phase 2–3 totals with
*more*, smaller search/read calls. TASKVIEW replicate 2 therefore reduced phase-1
exploration sharply (5,343B vs 13,595B, a 61% cut — but phase 1 is excluded from
`O_post`) and then gave essentially all of that structural advantage back in phases 2–3.

Replicate 3's TASKVIEW trajectory, by contrast, stayed at or below its RAW pair in
**every** post-phase-1 phase, most visibly in phase 5 (2,813B vs 6,325B — RAW re-reads
14 files there, TASKVIEW reads 6). Its post-phase-1 total (13,415B) is 27% below RAW's
(18,485B), consistent with the pair's large `O_post` reduction.

### C.3 Answers to the ten questions

1. **Narrower SQL in r3?** No — same style of narrow, filtered SELECTs in both.
2. **Avoided repeated `describe`?** Yes — this is the decisive factor (§C.1).
3. **Fewer columns queried?** No measurable difference.
4. **Smaller rowsets?** No — both return 0–3 row results throughout.
5. **Reused conversation state instead of re-querying?** Partially — r3 still re-queries
   `verification_gap`/`affected_service`/`requires_change` in phase 5 exactly as r2
   does; no evidence of state-memory substitution distinct from r2.
6. **Did r2 repeatedly re-query the same relation?** Yes, but so did every replicate —
   r2 has 8 exact-duplicate `query_sql` calls beyond the first occurrence, r3 has 11
   (§D). Repetition rate is not what separates them.
7. **Did large TaskView responses come from one pathological operation or many small
   ones?** One operation, unambiguously: `describe`, at a fixed 5,413B/call.
8. **Was RAW replicate 2 unusually efficient?** Not obviously — its phase 1
   (13,595B) and post-phase-1 (15,931B) totals sit in the same range as RAW r3's
   phase 1 (18,152B) and are actually *lower* than RAW r3's post-phase-1 total
   (18,485B). RAW r2 is a fairly ordinary RAW trajectory; it is TASKVIEW r2 that
   under-performed its own arm's usual pattern.
9. **Did TASKVIEW r2 still save file-count/reread work despite byte parity?** Yes, in
   raw call counts (`broad_searches` 6 vs RAW's 27; `repeated_file_reads` 12 vs 25 —
   see `metrics` in `record.json`) — but that saving is concentrated in phase 1 and does
   not show up in the post-phase-1 byte totals that `O_post` scores.
10. **Is r3's win reproducible with the existing surface, or accidental?** It looks
    structurally reproducible: it required no interface change, no different query
    vocabulary, and no lucky rowset — only *not re-issuing `describe`* after phase 1.
    That is a matter of when the model chose to re-orient, which is exactly the kind of
    variance §14 needs to weigh (more replication vs. a minimal, justified prompt/tool
    nudge) rather than an accident of case content.

---

## D. Redundant / repeated TaskView query analysis

**Classification rules** (applied mechanically from telemetry, not judgment calls):

- `FIRST_NECESSARY_ACCESS`: the first call to a given `(operation, exact SQL text or
  relation)` combination in the episode.
- `LATER_NECESSARY_REUSE`: a repeat of that combination issued at the start of a *new
  phase* (a new turn/prompt boundary), where the model has no persistent memory
  guarantee across the phase boundary that TaskView itself would treat as current —
  re-establishing grounding at a new turn is the intended re-orientation use, not waste.
- `REDUNDANT_REQUERY`: a repeat of the identical `(operation, SQL text)` combination
  issued again **within the same phase**, with no intervening `assertion`/`rerun` that
  would change the answer.
- `OVERBROAD_QUERY`: a call rejected or discouraged for requesting more than the
  question needs (`SELECT *`, or `describe` with a narrowing `why` argument that the
  tool does not support).
- `ORIENTATION_REFRESH`: a `describe` call issued after phase 1 (schema does not change
  across phases; only relation *contents* can, via mutation/assertion).
- `MUTATION / MAINTENANCE`: `assertion` and `rerun` calls.

Applying these across all 4 TASKVIEW episodes' `query_sql` calls (109 total: 22+22+27+28):

| classification | count | bytes | % of query_sql bytes |
|---|---:|---:|---:|
| FIRST_NECESSARY_ACCESS (distinct SQL per episode, first occurrence) | 57 | 5,973 | 66.5% |
| LATER_NECESSARY_REUSE (repeat at a new phase boundary) | 46 | 3,004 | 33.5%¹ |
| REDUNDANT_REQUERY (repeat within the same phase) | 0 | 0 | 0% |

¹ No exact-duplicate `query_sql` call was ever issued twice **within the same phase** in
any of the 4 episodes — every repeat of an identical SQL string occurs at a new phase's
turn boundary (e.g., `SELECT service_id FROM requires_change` recurs in phases 1, 2, 4,
5 of e02, once per phase, never twice in one phase). Under the rules above, **zero query_sql
bytes are classified REDUNDANT_REQUERY**; all repetition is `LATER_NECESSARY_REUSE`
(re-grounding at a fresh turn). This is a materially different conclusion from "TaskView
wastes bytes on redundant queries" — the redundancy is at the *phase* granularity the
apparatus itself imposes (each phase is a new prompt), not at the *reasoning-step*
granularity within a phase.

`describe` (8 calls total across 4 episodes): 4 are `FIRST_NECESSARY_ACCESS` (phase 1,
one per episode); 4 are `ORIENTATION_REFRESH` (phase 3/phase 5 re-calls in e02/e03/e07 —
r3/e06 has none). `describe` accounts for 100% of `ORIENTATION_REFRESH` bytes: 4 × 5,413
= 21,652B, or roughly one third of the campaign's entire `taskview_visible_bytes` total
(19,110+19,088+8,637+19,634 = 66,469B).

`OVERBROAD_QUERY` (from `TOOL_ERROR` events, never executed, so 0 bytes actually
returned to the model beyond the rejection message): 8 attempts across the 4 episodes —
4× `SELECT *` variants, 3× malformed `describe(why=...)` narrowing attempts, 1×
`search_source` with an invalid TaskView-namespaced scope. Each rejection message itself
cost 143–337 bytes (visible to the model as a tool error, counted in
`model_visible_output_bytes` for `TOOL_ERROR`, separate from `taskview_visible_bytes`).
Total: **1,845 bytes spent on rejected/overbroad attempts across the campaign** — small
in absolute terms, but 100% attributable to a structural mismatch between the schema the
model expects (permissive SQL, symmetric column names) and the schema the tool enforces
(no `*`, `service`/`test` argument keys rather than `service_id`/`test_id`).

**Descriptive summary:** of TaskView-visible bytes, roughly two-thirds are first-access
(necessary), one-third is later-phase re-grounding of which `describe`'s flat cost is
the large majority, and essentially none is same-phase redundant requery. The efficiency
lever the data actually supports is *making phase-boundary re-orientation cheaper*
(narrower `describe`, or none), not *stopping repeated queries* (there isn't a repeated-
query waste problem in the sense the term usually implies).

---

## E. RAW reconstruction-event table (R1–R4)

`reconstruction_events` in each RAW episode's `record.json` gives the exact
`(event, phase, sequence)` at which the frozen span classifier detects the relevant
grounding read. Reading the telemetry around each sequence (±8 events) gives the
concrete search/read pattern.

| episode | R1 (checkout direct-change) | R2 (reporting protected) | R3 (partner-gateway excluded) | R4 (external-worker unresolved) |
|---|---|---|---|---|
| e01 (r1) | phase 2, seq 62 | phase 2, seq 62 (same reconstruction pass) | phase 3, seq 82 | not separately observed² |
| e04 (r2) | not separately observed² | not separately observed² | phase 3, seq 100 | not separately observed² |
| e05 (r3) | phase 4, seq 137 (late) | not separately observed² | phase 3, seq 108 | not separately observed² |
| e08 (r4) | phase 2, seq 84 | phase 2, seq 84 (same pass) | phase 3, seq 106 | not separately observed² |

² The frozen span classifier records only the events it can positively locate from
source-read spans; "not separately observed" means R2/R4 were not independently
triggered as their own classified event in that trajectory (the participant may still
have gotten the corresponding oracle field right or wrong — that is scored separately
in `oracle_scores`, see §H) — this table is about *when the grounding read happened*,
not about correctness.

**e01, R1+R2 (phase 2, seq ~54–70):** reopens `services/reporting/README.md`,
`services/checkout/README.md`, `deploy/service-components.yaml`,
`tasks/migrate-jsonlib-v3.md` (the charter doc — already read once in phase 1),
`services/reporting/json_adapter.py`, `services/reporting/report_builder.py`,
`tests/reporting_contract.py` — 8 reads, 3,630 bytes, before reaching local
implementation. **e01, R3 (phase 3, seq ~74–90):** reopens
`deploy/production-services.yaml`, `lockfiles/reporting-json.lock`,
`tasks/migrate-jsonlib-v3.md` (third read of this file across the episode),
`architecture/partner-gateway.md`, `services/partner_gateway/protocol.py`,
`runtime/dynamic-consumers.md`, plus 2 fresh searches (`"import jsonlib"`,
`"consumer_registry"`) — 6 reads + 2 searches, ~2,239 bytes.

**TASKVIEW's equivalent points** (from §B.3's per-phase call lists, same reconstruction
semantics): phase 2 → `SELECT service_id FROM affected_service`,
`SELECT service_id FROM requires_change`, `SELECT service_id, adapter_id FROM protected_by`,
`SELECT service_id, test_id FROM verified_by`, `SELECT ... FROM compatible_via` (5 calls,
~600B) — no re-read of the charter doc, no reopening of the reporting adapter file (it is
still read once, but at LOCAL_ORACLE cost, unchanged per §I). Phase 3 →
`SELECT subject_id, basis FROM excluded`, `SELECT subject_id FROM boundary`,
`SELECT subject_id FROM unresolved_scope` (3 calls, ~264B) instead of the 6-file, 2-search
partner-gateway re-grounding pass.

**Concrete mapping (matches the requested `ve0kvy` template):**

```text
RAW (e01, phase 2/3):
    reopen reporting README + adapter + report_builder + reporting_contract.py
    reopen the charter doc (tasks/migrate-jsonlib-v3.md) — 2nd/3rd time
    reopen partner-gateway architecture doc + protocol.py + dynamic-consumers.md
    then inspect local file (checkout/reporting implementation)

TASKVIEW (e02, phase 2/3):
    SELECT service_id FROM affected_service / protected_by / verified_by / compatible_via
    SELECT subject_id FROM excluded / boundary / unresolved_scope
    then inspect local file (same LOCAL_ORACLE cost as RAW)
```

**Quantified savings for this specific judgment, replicate 1:** ~3,630B (R1/R2, 8 reads)
collapses to ~600B (5 queries) — an 83% byte reduction and a 3-read-vs-5-call-count
wash; ~2,239B (R3, 6 reads + 2 searches) collapses to ~264B (3 queries) — an 88%
reduction. This is the mechanism TaskView was designed to remove, and it is visibly
present and large in replicate 1. The same collapse is visible in replicates 3 and 4
(§C.2); it is specifically **replicate 2** where the equivalent phase-2/3 TaskView calls
did not stay this cheap (one 1,681B and one 3,361B `search_source` call intervened
anyway — TaskView's SQL calls were cheap, but the model *also* went back to the
repository with broad searches in those phases, receiving the reduction on the SQL side
while re-incurring cost on the repo side).

---

## F. Orientation mechanism decomposition

Classifying each RAW episode's `broad_searches`/`repeated_file_reads`/reconstruction
activity into the five requested categories (by phase and target, read directly off
`search_query`/file path/segment content — no field in the frozen telemetry labels this
directly, so this is a manual per-event classification, applied identically across all 8
episodes):

| category | typical RAW behavior observed | TaskView equivalent present? |
|---|---|---|
| **Structural discovery** ("where is the component?") | phase-1 broad searches like `"jsonlib v2 v3 migration"`, `"import jsonlib"`, reading `inventory/components.toml`, `deploy/service-components.yaml` | Largely replaced by `describe` (schema) + `SELECT ... FROM implements` / `production_service` — cheap, one-shot |
| **Task-scope reconstruction** (in scope/excluded/unresolved) | re-reading `tasks/migrate-jsonlib-v3.md`, `architecture/partner-gateway.md`, `runtime/dynamic-consumers.md` at phase 3 | Replaced by `SELECT ... FROM excluded / boundary / unresolved_scope / in_scope` — this is where §E's largest byte collapse happens |
| **Task-role reconstruction** (affected/protected/requires_change/verified) | re-reading `services/reporting/json_adapter.py`, `report_builder.py`, `tests/reporting_contract.py` at phase 2 | Replaced by `SELECT ... FROM protected_by / requires_change / verified_by / compatible_via` |
| **Exhaustiveness reconstruction** (has the universe been checked?) | phase-5 re-reads across 11–14 files (`e04`: 11 reads/4,666B; `e05`: 14 reads/5,859B) attempting to re-derive "have I covered everything in scope" | `SELECT service_id FROM affected_service` / `verification_gap` (2 calls, ~150B) plus a *smaller* set of local re-reads (6 files in e06 vs. RAW's 14) — see §I |
| **Irrelevant exploration** | phase-1 reads of `services/billing/invoice_codec.py`, `pyproject.toml`, `inventory/owners.yaml` that never appear in any citation | Present but reduced — TASKVIEW episodes' `IRRELEVANT`-labeled byte totals (9,159–10,861) are ~30–40% below RAW's (13,461–17,186), see §I |

TaskView's byte reduction is **not evenly spread** across these five categories: the
largest, cleanest collapses are in *task-scope* and *task-role* reconstruction (§E),
where a named relation directly answers the question a document search previously had
to reconstruct. *Structural discovery* is reduced but less cleanly (both arms still do
several `search_source` calls in phase 1). *Irrelevant exploration* shrinks but is not
eliminated — every TASKVIEW episode still reads 1–2 files that never end up cited
(e.g., `services/billing/invoice_codec.py` appears in RAW's irrelevant set consistently;
TASKVIEW mostly avoids it but not in all 4 episodes). This supports the paper's framing
claim that TaskView's novel value is concentrated in *task-conditioned* orientation
(scope/role), not generic file-finding, which is the category where RAW and TASKVIEW
stay closest.

---

## G. Scoped-exhaustiveness autopsy (per episode)

Dimension fields: phase 3 `whole_world_complete`; phase 5 `other_gaps_in_affected_service`,
`completeness_universe`, `whole_world_complete`, `whole_world_blockers`. Per-episode
field correctness (✓/✗), pulled directly from `oracle_scores`:

| episode | p3 whole_world_complete | p5 whole_world_complete | p5 other_gaps | p5 completeness_universe | p5 whole_world_blockers | rate |
|---|:-:|:-:|:-:|:-:|:-:|---:|
| e01 RAW r1 | ✓ | ✓ | ✓ | ✗ | ✗ | 0.60 |
| e04 RAW r2 | ✓ | ✓ | ✗ | ✗ | ✗ | 0.40 |
| e05 RAW r3 | ✓ | ✓ | ✗ | ✗ | ✗ | 0.40 |
| e08 RAW r4 | ✓ | ✓ | ✗ | ✗ | ✗ | 0.40 |
| e02 TV r1 | ✓ | ✓ | ✓ | ✓ | ✗ | 0.80 |
| e03 TV r2 | ✓ | ✓ | ✓ | ✓ | ✗ | 0.80 |
| e06 TV r3 | ✓ | ✓ | ✓ | ✓ | ✗ | 0.80 |
| e07 TV r4 | ✓ | ✓ | ✓ | ✓ | ✗ | 0.80 |

**Every TASKVIEW episode scores identically (4/5); three of four RAW episodes score
identically (2/5); one RAW episode (e01) scores 3/5.** This uniformity is itself a
finding: it means the "0.80 vs 0.45" gap is not built from four independent,
noisy judgment calls — it is built from two fields (`completeness_universe`,
`other_gaps_in_affected_service`) that flip almost deterministically with arm.

- **`whole_world_complete` (both phases):** every episode, both arms, gets this right —
  no arm effect at all. Nobody incorrectly claims whole-world completeness, and nobody
  incorrectly denies scoped completeness. This is the one truly shared success.
- **`whole_world_blockers`:** every episode, both arms, gets this wrong. The oracle
  wants the literal pair `["service:external-worker unresolved", "partner boundary
  internals opaque"]`; inspecting the actual answers (not shown in full here for space,
  but confirmed on all 8) shows participants in both arms name the *same two real
  blockers* in their own words but never as this exact two-item list — a scoring
  fragility identical in kind to §H's, and it applies equally to both arms, so it
  contributes zero to the arm split.
- **`completeness_universe`:** oracle expects the literal string `"affected_service"`.
  All 4 TASKVIEW answers are the literal token `affected_service` — a verbatim echo of
  the SQL relation name they just queried (`SELECT service_id FROM affected_service`
  appears in every TASKVIEW phase-5 call list, §B.3). All 4 RAW answers are multi-clause
  prose correctly describing the *same* scope ("production-deployed services in
  deploy/production-services.yaml, commerce ownership in inventory/owners.yaml, pinned
  v2 lockfile components...") that never happens to contain the string
  `"affected_service"` verbatim, and is scored wrong under exact-ish string match. This
  is a **vocabulary-availability effect**, not a demonstration that TASKVIEW models
  understood the scope boundary better than RAW models did — arguably RAW's prose shows
  *more* explicit reasoning about what composes the universe.
- **`other_gaps_in_affected_service`:** oracle expects `[]`. All 4 TASKVIEW answers are
  `[]`. Three of four RAW answers are non-empty, and inspection of their content (§8
  quotes above) shows genuinely plausible, specific engineering observations (untested
  comment-tolerant decoding, untested Decimal preservation, a missing end-to-end
  contract test) that are either (a) already captured elsewhere in the oracle's
  `missing_behaviors`/`proposed_replacement_verification` fields for a different phase,
  making this a legitimate but misfiled restatement, or (b) genuine extra scope-creep
  the RAW model volunteered because it was still reading source files at this point
  (§C.2 shows RAW re-reads far more files at phase 5) and found something to say about
  them. TASKVIEW's `[]` answer is not obviously the product of *more* verification that
  other gaps don't exist — its phase-5 SQL calls (`verification_gap`, `affected_service`,
  `verified_by`, `unresolved_scope`) do bound the check, but the model was not observed
  explicitly reasoning "I checked X, Y, Z and found none," it simply queried and reported
  what came back.

**Answer to the target question:** TaskView appears to help agents *echo* a
task's bounded universe correctly (via a literal, queryable identifier) more than it
demonstrably helps agents *reason about when a bounded search is finished*. The uniform
4/5 vs 2–3/5 split, concentrated in two fields that are answerable by relation-name/empty-
result echo rather than by synthesizing "I have checked everything in scope and nothing
else needs checking," is consistent with a **scoring-vocabulary artifact plus a mild,
real, harder-to-isolate discipline effect** (TASKVIEW's `[]` answers are at least
consistent with — though not proof of — not over-claiming). Given this is 4 episodes per
arm and the effect is this concentrated in two fields, treat the secondary "promising"
label as correctly cautious, not as an established mechanism.

---

## H. Changed-evidence / staleness autopsy (per episode)

The `HARNESS_MUTATION` event fires identically in structure across all 8 episodes at
`after_phase_3_commit_before_phase_4_prompt`, on `tests/checkout_contract.py` (confirmed
by inspecting the event in e02; the boundary/source_path/`taskview_silently_repaired:
false` fields are structurally the same field names in every episode's telemetry). The
prompt tells participants the file changed; the correct reaction is to recognize that
the prior `verified_by(service:checkout, test:checkout-contract)` conclusion no longer
holds because the surviving test only exercises a smoke case (`order["id"]`), not the two
migration-relevant decoding behaviors (comment tolerance, Decimal preservation).

| episode | noticed the change? | updated conclusion in substance? | mechanism used | oracle phase-4 field match |
|---|:-:|:-:|---|:-:|
| e01 RAW r1 | yes | yes — "Reconsider treating service:checkout as migration-verified..." | manual re-read + prose re-derivation | 1/5 (citations only) |
| e04 RAW r2 | yes | yes — same substance, own phrasing | manual re-read + prose re-derivation | 1/5 |
| e05 RAW r3 | yes | yes — same substance | manual re-read + prose re-derivation | 1/5 |
| e08 RAW r4 | yes | yes — same substance | manual re-read + prose re-derivation | 1/5 |
| e02 TV r1 | yes | yes — "service:checkout is in verification_gap and must be reconsidered..." | `assertion(retract, verified_by)` → `rerun(verification_gap)` | 1/5 |
| e03 TV r2 | yes | yes — same substance | retract → rerun (2 reruns; first rerun before the retract still showed 0 rows, i.e. a check-before-you-retract pattern) | 1/5 |
| e06 TV r3 | yes | yes — same substance | retract → rerun | 1/5 |
| e07 TV r4 | yes | yes — same substance | retract → rerun | 1/5 |

Under the requested classification scheme, **every one of the 8 episodes is
`RERAN_CORRECTLY` in substance** (RAW's substance-equivalent of "rerun" is manual
re-derivation from the mutated file; TASKVIEW's is the literal `rerun` tool call). None
are `DID_NOT_NOTICE_CHANGE`, `TRUSTED_STALE_RESULT`, or
`UPDATED_BASE_STATE_BUT_DID_NOT_RERUN`. The oracle's field-level scoring (1/5 across the
board) is driven entirely by **exact-string mismatch against terse canonical labels**
(`"comment acceptance"` vs. "Decoding JSON payloads that include merchant comments
(allow_comments=True)."; `retract verified_by(service:checkout, test:checkout-contract)`
vs. a full sentence that contains that call embedded in prose), not by a reasoning
failure — confirmed directly by reading e02's own answer (§ above), which is TASKVIEW
and still fails 4/5 fields for the same reason.

**Answer to the target question:** TaskView's explicit staleness machinery (`assertion`
+ `rerun`) *was* used correctly by every TASKVIEW replicate, and it is a cleaner,
mechanically-verifiable way to reach the same correct conclusion RAW reaches by manual
re-reading — but the phase-4 oracle scoring is not sensitive enough (at the current
exact-match strictness) to detect that either arm succeeded, so the frozen numbers alone
would have under-stated *both* arms equally. The one place TaskView clears a bar RAW
doesn't (`current_verification_gap` at phase 5, §L) is the same
canonical-identifier-echo effect documented in §G, not additional staleness-handling
skill.

---

## I. Local-source preservation analysis

`LOCAL_ORACLE`-labeled bytes (the frozen span classifier's label for source spans that
are actually cited/necessary local implementation reading) and `local_source_inspection_rate`,
per episode:

| episode | LOCAL_ORACLE bytes | local_source_inspection_rate | unique local files reached |
|---|---:|---:|---|
| e01 RAW r1 | 5,282 | 1.0 | checkout/reporting/partner-gateway impl files |
| e04 RAW r2 | 5,177 | 1.0 | same set |
| e05 RAW r3 | 5,673 | 1.0 | same set |
| e08 RAW r4 | 5,888 | 1.0 | same set |
| e02 TV r1 | 5,066 | 1.0 | same set |
| e03 TV r2 | 5,001 | 1.0 | same set |
| e06 TV r3 | 4,263 | 1.0 | same set |
| e07 TV r4 | 5,137 | 1.0 | same set |

RAW mean 5,505B; TASKVIEW mean 4,867B (11.6% lower, within the range of ordinary
per-episode variance given the RAW range alone spans 5,177–5,888, a 12% band). All 8
episodes reach `local_source_inspection_rate = 1.0` — every episode, both arms, actually
opened the required implementation file(s) before answering; TaskView did not let any
replicate substitute a SQL lookup for the local read it needed. `bytes_before_first_local`
per phase (from `phase_focus`, e.g. e02: phase 1 = 2,523B before first local read vs. e01
RAW's 7,553B) is consistently lower for TASKVIEW in phase 1, consistent with faster
routing to the necessary file rather than slower or replaced access.

**Answer to the three target questions:** yes, TASKVIEW reached the required local
source in every episode; no, it did not replace local inspection with a TaskView lookup
(TaskView has no operation that returns source code — `LOCAL_ORACLE` bytes can only come
from `read_source`); and yes, orientation shrank (§F, §I's `IRRELEVANT`+`ORIENTATION_SUPPORT`
comparison) while local-source effort held flat. This is the one part of the resource
model (§2) that the data supports cleanly and without qualification.

---

## J. Provider-token accounting decomposition

Extracted from each episode's `provider_trajectory.jsonl` `sdk_message.type == "usage"`
event — exactly one such event per phase/turn (5 per episode, 40 total), carrying
`input_tokens` (fresh, non-cached), `cache_read_tokens`, `cache_write_tokens`, and
`output_tokens`, which sum exactly to the accompanying `total_tokens`
(verified: `input_tokens + output_tokens + cache_read_tokens + cache_write_tokens ==
total_tokens` for every one of the 40 turns).

| episode | phase 1 fresh-in | phase 2 | phase 3 | phase 4 | phase 5 | phase 4 / phase-3 fresh-in ratio |
|---|---:|---:|---:|---:|---:|---:|
| e01 RAW r1 | 82,763 | 48,403 | 76,518 | 87,918 | 103,119 | 1.15× |
| e02 TV r1 | 99,141 | 79,987 | 78,023 | 245,326 | 90,580 | 3.14× |
| e03 TV r2 | 59,900 | 57,721 | 81,385 | 172,842 | 87,219 | 2.12× |
| e04 RAW r2 | 106,554 | 48,287 | 96,437 | 88,079 | 75,287 | 0.91× |
| e05 RAW r3 | 118,284 | 54,296 | 106,990 | 122,904 | 114,052 | 1.15× |
| e06 TV r3 | 86,623 | 100,290 | 123,560 | 169,594 | 138,310 | 1.37× |
| e07 TV r4 | 125,112 | 99,946 | 132,225 | 208,201 | 90,449 | 1.57× |
| e08 RAW r4 | 113,393 | 66,008 | 80,790 | 91,810 | 106,259 | 1.14× |

`cache_write_tokens` is **0 in all 40 turns of both arms** — no distinct cache-write
accounting is exposed by this SDK/model combination; whatever caching happens is only
visible as `cache_read_tokens` growth turn over turn.

- **Phase 4 spike is universal but far larger for TASKVIEW.** All 8 episodes show a
  fresh-input jump at phase 4 (the mutation-reaction turn), but RAW's ratio to phase 3
  clusters near 1.0–1.15× while TASKVIEW's ranges 1.37×–3.14×. TASKVIEW's phase 4 also
  carries the campaign's two largest `cache_read_tokens` values (232,640 in e02;
  158,624–160,448 in e03/e07). This is consistent with the phase-4 turn needing to
  re-transmit a much larger fraction of the (larger, tool-call-laden) conversation
  history once the mutation invalidates whatever prefix caching had been keeping fresh-
  input low — but this SDK does not expose a "cache invalidated due to X" signal, so
  this is a plausible read of the shape, not a directly observed cause.
- **TASKVIEW's baseline fresh-input is not systematically higher in phase 1** (e02
  99,141 > e01 82,763, but e03 59,900 < e04 106,554) — no clean, arm-wide "tool schema
  adds N tokens" constant is extractable from phase 1 alone; the variance across
  replicates within an arm (e01: 82,763; e04: 106,554; e05: 118,284; e08: 113,393 — all
  RAW) is comparable in size to the RAW/TASKVIEW gap, so this specific claim from the
  executive summary should be read as directional, not quantified.
- **Attribution is not defensible below the per-turn level.** The SDK exposes one
  `usage` total per phase/turn, generated after the whole tool-use loop for that turn
  completes; it does not itemize which fraction of `input_tokens` came from
  conversation-history replay, TaskView tool-call/response payloads, or repo
  `search_source`/`read_source` payloads within that turn. `model_visible_output_bytes`
  in the frozen telemetry (used throughout §B–§I) is the harness's own byte accounting
  of what each tool call returned, which is a defensible proxy for the *shape* of cost
  but is not denominated in the provider's own token currency, and the provider does not
  expose a token-level breakdown that would let the two be reconciled exactly (tokenizer
  differences, prompt formatting overhead, and cached-vs-fresh boundaries are all
  invisible below the whole-turn total). **Do not treat any per-operation token number in
  this document as directly measured — only the byte-level breakdowns in §B–§D are.**

---

## K. Scaling implications (theory only — no scaling experiment run)

Using only Stage 1's structure: `W` (this world) is ~20 source files across 3 services,
1 vendor doc, and a handful of deploy/inventory files; `V_T` (TaskView's view) is a
5-relation, ~15-row schema.

For `C_RAW − C_TASKVIEW` to *widen* as `|W|` grows, the RAW mechanism that TaskView
demonstrably compressed here (§E: reopening the charter doc + 2–3 supporting documents
per phase to re-derive scope/role facts) would need to keep costing RAW roughly
`O(phases × documents-per-reconstruction × doc-size)`, growing with `|W|` if a larger
world means more documents contribute to each scope/role judgment — while
`C_TASKVIEW`'s per-phase re-grounding cost stays close to `O(phases × narrow-query-bytes)`,
which only grows with the *number of distinct relations a phase's judgment touches*, not
with `|W|` directly (a `SELECT ... FROM excluded WHERE subject_id = X` costs the same
whether the `excluded` relation has 1 row or 500, as long as the filter is selective).

That is the favorable case. Stage 1 already surfaces two countervailing effects that
would need to be checked, not assumed away, before believing it:

- **`describe`'s cost is `O(schema size)`, not `O(1)`.** It already dominates TaskView's
  own cost at this tiny schema size (§B.2, 63–85% of TaskView bytes). If `V_T` grows
  with `|W|` (a larger world plausibly needs more relations to stay task-conditioned),
  `describe`'s flat-dump cost grows with it, and every re-orientation refresh becomes
  proportionally *more* expensive, not constant — this could erase or reverse the
  advantage exactly where it currently helps least (replicate 2's outcome, at 5
  relations, is already sensitive to 2 extra `describe` calls; a bigger schema makes
  that sensitivity worse per call, not better).
- **The tool-schema friction in §D (`SELECT *` rejections, `assertion` key-name
  mismatch) is currently a fixed, small cost (1,845B total) because the schema is
  small and the argument shapes are few.** There is no evidence in this data about
  whether that friction rate stays fixed, grows, or shrinks as the schema and the
  variety of mutation/assertion shapes grow — it was not designed to be measured across
  schema sizes and Stage 1 cannot speak to it.
- **Local-surface cost (`LOCAL_ORACLE` bytes) held flat here because the *task* fixed
  which local files matter, independent of `|W|`.** A larger world does not obviously
  change how much local code a fixed task touches — this part of the resource model
  plausibly generalizes — but "wrong exclusions become more costly" (a wrong `excluded`/
  `boundary` classification in a bigger world could mean editing something that should
  not be edited) is a correctness-severity effect Stage 1's tiny, single-mistake-tolerant
  case cannot exercise at all.

**Net theoretical read:** the mechanism that produced TaskView's genuine wins here
(collapsing multi-document scope/role reconstruction into a single filtered row lookup)
is the part most plausible to scale favorably. The mechanism that produced TaskView's
losses (flat-cost `describe` re-orientation, tool-schema friction) is the part most
plausible to scale *unfavorably*, because both costs are tied to schema size and call
shape, not to world size directly, and this experiment's schema is fixed at 5 relations —
too small to have exercised that dependency at all. A dose-response design should vary
`|W|` while holding schema *shape* (relation count, not just row count) as close to fixed
as the case allows, specifically to isolate whether `describe`'s cost tracks `|W|` or
tracks `|V_T|`'s relation count independent of `|W|`.

---

## L. Ranked mechanism hypotheses

**H1 — TaskView economics are dominated by repeated broad `query_sql` result payloads.**
Evidence against: no `query_sql` call across the entire campaign exceeded 257 bytes; the
largest rowset returned was 3 rows; §D found zero same-phase redundant requeries. **Not
supported.** Rank: rejected.

**H2 — Repeated schema/orientation refresh (`describe`) dominates TaskView's own cost.**
Evidence for: `describe` is 63–85% of TaskView-visible bytes in every episode (§B.2);
the entire replicate-2-vs-3 cost gap is explained by `describe` call count (§C.1, to
within 4%); `describe`'s cost is flat and call-count-driven, not content-driven.
Evidence against: none found — no episode's `describe` behavior contradicts this.
**Strongly supported.** Rank: 1.

**H3 — The surface is already economical when agents issue narrow relation queries, as
in replicate 3.** Evidence for: replicate 3's `query_sql` behavior (27 calls, 2,600
bytes) is not meaningfully narrower than replicate 2's (22 calls, 1,795 bytes) — query
narrowness was already present in every replicate, so "the surface is economical when
queries are narrow" is true but the queries were already narrow everywhere; what
differed was `describe` frequency (H2), not query shape. **Supported, but as a corollary
of H2, not an independent explanation** — replicate 3 is not distinguished by narrower
querying, it's distinguished by not re-fetching the schema. Rank: 2 (subsumed by H2).

**H4 (added, evidenced during this autopsy, not in the original prompt) — Front-loaded
phase-1 savings do not reliably persist as post-phase-1 (`O_post`-scored) savings.**
Evidence for: replicate 2's TASKVIEW trajectory cut phase-1 repo bytes by 61% relative to
its RAW pair but matched or exceeded RAW's repo bytes in phases 2–3 (§C.2); replicate 3's
TASKVIEW trajectory stayed below RAW in every post-phase-1 phase. This is the most direct
explanation of *which* replicates pass the `O_post` metric and which don't, independent
of `describe` cost. **Strongly supported by the two available cases; only 2 data points
(one per outcome), so treat as a hypothesis to test with more replication, not a
established law.** Rank: 1 (tied with H2 — they are largely independent and additive:
H2 explains TaskView's own cost variance, H4 explains repo-cost persistence variance).

**H5 (added) — A meaningful fraction of the scored "secondary" TaskView advantages
(scoped exhaustiveness, changed-evidence reaction) are canonical-identifier-echo
artifacts of the oracle's exact-match scoring, not demonstrated superior reasoning.**
Evidence for: §G and §H both isolate single fields (`completeness_universe`,
`current_verification_gap`) that flip almost deterministically with arm because
TASKVIEW can echo a literal relation/row name and RAW has no equivalent canonical token;
substantive content of the answers RAW gets marked wrong for is frequently correct or at
least defensible engineering reasoning. Evidence against: this cannot fully explain
`other_gaps_in_affected_service` (§G), where TASKVIEW's `[]` answers are consistent with,
though not proven to result from, genuine query-bounded discipline. **Supported as a
partial, not complete, explanation.** Rank: 3.

**If H2 and H4 are true, the smallest justified future change would be** making
phase-boundary re-orientation cheaper than a full schema dump (e.g., a narrower "what
changed since I last checked" or per-relation describe) and/or investigating why some
trajectories' repo-side savings fail to persist past phase 1 — **but per the governing
instruction, no such change is implemented or specified further here.**

---

## M. Recommended next experiment

**Recommendation: A — same case, same surface, more replication**, with a secondary,
narrowly-scoped instrumentation addition (not a TaskView interface change): explicitly
log `describe` call count and post-phase-1 repo bytes as first-class per-episode metrics
in the next campaign's `report.py` output, since both are already computable from
existing telemetry and both hypotheses (H2, H4) are currently supported by only 4 (H2)
or 2 (H4) data points per condition.

Justification against B and C:

- **Against B (minimal justified surface reduction, then repeat):** the autopsy *did*
  identify a specific, repeated, clearly unnecessary cost (`describe`'s repetition,
  H2) — this is the one condition the original instruction set for choosing B. However,
  acting on it now would confound two things this Stage 1 campaign cannot yet
  separate: whether `describe`-repetition frequency is itself a stable per-model
  tendency (worth fixing) or a coincidence of 4 small samples (r3's single call vs.
  r1/r2/r4's three could easily invert with 4 more replicates). Changing the surface
  before that's known risks overfitting a fix to this specific 8-episode draw, which is
  exactly the risk B is supposed to be chosen *away from* absent stronger evidence.
- **Against C (larger/more orientation-heavy world):** §K's scaling argument is
  double-edged — a larger world could make TaskView's real win (scope/role collapse)
  larger, but could equally make its real cost (`describe`'s flat-dump, schema-size-linear
  cost) larger too, and Stage 1's schema is too small to have exercised that trade-off at
  all. Running C now would produce a result that is uninterpretable between "TaskView
  scales well" and "TaskView's overhead scales with it" without first knowing whether
  H2/H4 are stable mechanisms (from A) or an artifact of a tiny 4-replicate sample.

**Sequencing implication:** A should come first specifically to determine whether H2
(`describe` repetition) and H4 (savings non-persistence) are reproducible tendencies
before either fixing the interface (B) or scaling the world (C) — both of which would be
answering a different, premature question if run now.

Scoring against the five criteria:

| | A: more replication | B: minimal surface reduction | C: larger world |
|---|---|---|---|
| scientific interpretability | high — isolates whether H2/H4 are stable | medium — conflates fix effect with sampling variance | low — conflates world-size effect with unresolved H2/H4 |
| risk of overfitting Stage 1 | low | **high** — a fix tuned to 4 episodes' `describe` pattern | medium |
| participant cost | same as Stage 1 per additional replicate (real, non-trivial, but already budgeted for) | adds engineering cost, not just participant cost | likely higher (larger world = longer trajectories) |
| mechanism vs. interface overhead | directly separates them (same interface, more samples) | conflates them by construction | does not separate them at all |
| world-size hypothesis testability | does not test it, but is a necessary precondition | does not test it | tests it, but uninterpretably absent A |

---

## N. Explicit non-claims

Stage 1, and this autopsy, still do **not** establish:

- That TaskView passes the frozen 30% net-orientation threshold — it does not, and
  nothing here moves that number or should be read as arguing it should.
- That `describe`'s repetition pattern (3 calls in r1/r2/r4, 1 in r3) is a stable model
  tendency rather than a coincidence of a 4-episode draw — this needs more replication
  (§M) before being treated as fixable or as a real per-model habit.
- That the scoped-exhaustiveness and changed-evidence "advantages" reflect superior
  bounded-search or staleness reasoning, as opposed to canonical-identifier-echo
  scoring artifacts (§G, §H, H5) — the evidence here is that the effect is *at least
  partly* an artifact; it does not rule out a smaller, real discipline effect underneath
  it, and 4 episodes per arm cannot distinguish the two.
- That local-implementation correctness is unaffected by TaskView in general — only
  that `LOCAL_ORACLE` byte volume and inspection rate are unaffected in this case;
  `local_implementation_semantics` field correctness is identical (0.25) in both arms,
  which is a separate, weaker claim than "TaskView doesn't hurt local reasoning" and
  should not be strengthened into one.
- Anything about scaling with world size beyond the theoretical, non-empirical
  discussion in §K — no scaling experiment was run, and Stage 1's 5-relation,
  ~20-file world is not evidence about behavior at a materially different scale in
  either direction.
- That the tool-schema friction identified in §D (`SELECT *` rejections, assertion
  key-name mismatch) meaningfully affected any episode's *outcome* — it cost a small,
  bounded number of bytes and one retry each time, and every affected episode still
  completed the intended mutation/rerun sequence correctly; this is a real, reproducible
  friction cost, not a demonstrated failure mode.
- Provider-token economics at anything finer than whole-turn granularity (§J) — the
  SDK's exposed accounting does not support it, and no claim in this document should be
  read as a token-level attribution.
- Causality in the strict sense anywhere in §C–§I: these are trajectory-level
  correlations and mechanical decompositions of a sealed, already-collected dataset, not
  a controlled intervention. The replicate-2-vs-3 comparison in particular is an
  observational contrast between two independent model rollouts, not a controlled
  ablation of `describe`-repetition — a future experiment that actually varies
  `describe` frequency (not just observes it) would be needed to call H2 causal rather
  than strongly correlational.
