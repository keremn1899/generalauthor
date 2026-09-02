# Isolated A/B replication: RAW sources vs compiled World IR

Experiment `bom-llm-world-programming-v3`.
Manifest fingerprint: `sha256:b88da582b1f1a4477c47d444caf5f12945649501f340e4e6ae70906e0e1404f4`.
Predecessor: `bom-llm-world-programming-v2` (aborted: nested `cursor-agent --sandbox enabled` cannot start inside bwrap).
Provider/model calls: **40**. No further inference after this report.

Primary metric: the saved program executes in a clean copy of its condition environment, and canonical JSON matches the frozen expected artifact from `research/semantic_integration/domains/bom/world_programming/expected/`.

The strongest supportable claim from the preregistered analysis is:

> Under this frozen BOM programming benchmark, physical bwrap isolation, and `gpt-5.6-sol-high` / `cursor-agent-bwrap-isolated-workspace-agent-v3`, programming against compiled World IR produced **18/20** exact task successes versus **0/20** against raw sources. Wilson 95% intervals do not overlap. A two-sided Fisher exact test on the 2×2 table is *p* ≈ 3.4×10⁻⁹. Isolation held: **0/40** successful repository Reads.

Task C was deferred until this A/B isolation-held signal existed. It is not in this campaign.

---

## Protocol (frozen before inference)

| Item | Value |
|---|---|
| Model | `gpt-5.6-sol-high` (stream-json reports `GPT-5.6 Sol 272K High`) |
| Adapter | `cursor-agent-bwrap-isolated-workspace-agent-v3` |
| Agent mode | default agent (write + shell); not ask mode |
| Flags | `--print --output-format stream-json --force --trust --sandbox disabled --workspace` |
| Isolation | `bwrap` bind `/` then tmpfs over the git repo, `/tmp/world-experiment/<id>` siblings, and `~/.cursor/projects` |
| Live workspaces | `/tmp/world-experiment/bom-llm-world-programming-v3/<uuid>/` |
| Temperature | not exposed by CLI |
| Budget | 600 s wall-clock per trial, identical RAW/WORLD |
| Replication | 2 tasks × 2 conditions × 10 trials = 40 (preregistered; not changed) |
| `open_world()` | reads stored TaskView `view_id` from `world.sqlite` (not hardcoded) |
| Timeouts | 0 |
| Execution failures | 0 |
| Isolation preflight ok | 40/40 |
| Isolation leak runs | 0 |

The frozen human benchmark was not modified. Expected outputs were used only in the scorer. World relations, obligations, indoor `acceptable_replacement(part:X110, part:X160, context:indoor_panel)` remaining `UNRESOLVED`, C0/C1/C2, and expected JSON were not changed to improve WORLD.

v1 used the same prompts and expected artifacts for A/B. v1 isolation did not hold. This campaign is the isolation-held replication, not a new task design.

---

## 1. Exact task success (primary)

### Intent-to-treat (all 40 preregistered runs)

| Condition | Pass | Rate | Wilson 95% |
|---|---:|---:|---|
| RAW | 0/20 | 0.0% | [0.00, 0.16] |
| WORLD | 18/20 | 90.0% | [0.70, 0.97] |

WORLD increased exact success. The intervals do not overlap. Isolation held, so ITT is also the clean-read result. There is no post-hoc contamination subset.

### Per task

| Cell | Pass | Rate | Wilson 95% |
|---|---:|---:|---|
| `raw:analysis_a` | 0/10 | 0% | [0.00, 0.28] |
| `raw:analysis_b` | 0/10 | 0% | [0.00, 0.28] |
| `world:analysis_a` | 8/10 | 80% | [0.49, 0.94] |
| `world:analysis_b` | 10/10 | 100% | [0.72, 1.00] |

Per-cell Fisher two-sided: A *p* ≈ 7.1×10⁻⁴; B *p* ≈ 1.1×10⁻⁵.

---

## Isolation (preregistered; held)

v1 `--sandbox enabled` plus `--workspace` did not hide the parent git repository. 11/30 v1 trials Read human solutions, expected artifacts, other trials, or harness files.

This campaign:

- live workspaces under `/tmp`, not under the repo;
- bwrap tmpfs over the repo, sibling live trials, and Cursor project indexes;
- nested Cursor sandbox **disabled** (v2 abort);
- preflight must fail to list the repo, read expected/human solutions, or see sibling canaries;
- leak detector: successful `Read` of a path under the repository.

**0/40** trials have `isolation_leaks`. **40/40** preflights ok. **0** `leaks_before` workspace copies. Audit: `scoring/isolation_audit.json`.

Because isolation held, there is no clean-read sensitivity analysis. ITT is the result.

---

## 2–3. Semantic error categories

Classifier output (failed runs only):

| Class | Count | Where |
|---|---:|---|
| `CONTEXT_MATCHING` | 10 | RAW A 001–008, 010; RAW B 003 |
| `SEMANTIC_ACCEPTANCE` | 12 | RAW A 009; RAW B 001–002, 004–010; WORLD A 001–002 |
| `UNKNOWN_AS_FALSE` | 0 | — |
| `SQL_OR_PYTHON` | 0 | — |

### RAW A — demanded context never constructed (9/10)

Nine RAW A programs executed and wrote valid `replacement_state` JSON. They emitted only the candidate/context pairs written as `Candidate:` records in `engineering_notes.md` (outdoor enclosure, high-vibration cabinet). They never produced `context:indoor_panel`.

The indoor case is demanded by BOM-B plus the X110/X160 candidate pair, not by a positive note. RAW programs treated notes as the case generator. That is source-schema / context-construction, scored as `CONTEXT_MATCHING`.

They did not label indoor as false; they omitted it.

### RAW A trial 009 — indoor constructed, wrong label

This trial did emit indoor X110/X160 for BOM-B. It labeled it `not_established` / `NOT_KNOWN` rather than `unresolved`. Scored `SEMANTIC_ACCEPTANCE`. Outdoor X110/X160 in the same payload is incorrectly `unresolved` while the notes-backed outdoor case should be accepted.

### RAW B — label, not false (9/10); one omission

Nine RAW B indoor objects used `semantic_state: "not_established"` while listing `semantic_acceptance` under `leaves_viability_uncertain` and leaving `prevents_viability` empty. They did not treat missing acceptance as a failed qualification. The frozen expected label is `unresolved`.

Trial 003 omitted indoor entirely (`CONTEXT_MATCHING`), same notes-as-case-generator pattern as RAW A.

Trial 009's first indoor case is X160/X100 `not_established`. X110 indoor is also `not_established` in the same payload. The classifier looks at the first indoor case.

### WORLD A — 8/10 exact; two cartesian/join failures

Trials 003–010 pass. Indoor X110/X160 is `unresolved` / `UNRESOLVED`, `mechanical_state: suitable`, `bom_items: [bom:BOM-B]`.

Trials 001–002 expand candidate pairs × contexts. The first indoor object is R210/R200 `not_established` with `bom_items: [BOM-B, BOM-D]` and `mechanical_state: unsuitable`. The X110/X160 indoor object in the same payload remains `UNRESOLVED` (correct epistemic class) but `mechanical_state` is `unsuitable` and `bom_items` includes `bom:BOM-D`. BOM-D is an indoor connector, not the same part type. The classifier looks at the first indoor case: `SEMANTIC_ACCEPTANCE`.

That is an LLM join/case-set error over already-compiled relations, not CSV parsing, and not treating unknown as false.

### WORLD B — 10/10

All ten trials distinguished preventing constraints from uncertain semantic acceptance using compiled compatibility relations and obligations. Indoor X110/X160 is `unresolved`. No human-solution Reads (isolation held).

---

## 4. Acquisition and source-schema reasoning

Median tool metrics (provider stream-json `tool_call started` events):

| | RAW | WORLD |
|---|---:|---:|
| tool calls | 12 | 14 |
| shell calls | 1.5 | 4 |
| reads | 6 | 5 |
| python executions (guess from shell) | 1 | 4 |

WORLD did **not** reduce tool-call count. Median `csv.DictReader` in final code: RAW **1**, WORLD **0**. Median source-schema field literals: RAW **10**, WORLD **2.5**. Median World relation references: RAW **4.5** (string collisions such as `part_type`), WORLD **8**. Median SQL statement literals: RAW **0**, WORLD **0** (WORLD programs used the Python surface; 8/20 contain any SQL literal, 4/20 call `query_semantic`, 18/20 call `relation_rows`). Median `inspect_tuple` calls: RAW **0**, WORLD **0.5** (10/20 programs). All 20 WORLD programs call `open_world()` and read `obligations`.

Interpretation: WORLD reduced *source-column* reasoning inside the saved program. It did not reduce *interaction* count. WORLD interaction is schema introspection plus ordinary Python over compiled relations. The v1 `open_world()` view-id mismatch is gone; that cost is not in this campaign.

---

## 5. Tokens, tools, iterations

Provider-reported medians:

| | RAW | WORLD |
|---|---:|---:|
| input tokens | 22.5 | 27 |
| output tokens | 4263 | 4560.5 |
| total | 4285.5 | 4596.5 |

**Do not interpret these as session cost.** Input counts in the 20–30 range cannot be full-context usage for an agent that reads files. The stream-json `result.usage` field is treated as incomplete. H4 (WORLD cheaper in tokens) is **not measured**.

On the incomplete output-token field and on tool calls, WORLD is not cheaper. Median nonempty LOC is slightly lower for WORLD (143.5 vs 152.5).

---

## 6. Where effort went

### RAW

Preparation/reconciliation: CSV/`DictReader`, notes regex, identifier prefixing, manufacturer-to-BOM joins, reconstructing mechanical suitability from voltage/temperature/type columns. Analysis was mostly “cases = note candidates,” which is why indoor vanished in 9/10 RAW A trials and 1/10 RAW B trials. When indoor was constructed, the missing-acceptance label was `not_established` rather than `unresolved`.

### WORLD

Introspection (`WORLD_API.md`, `describe`, `relation_rows`), obligations, completeness receipts, `inspect_tuple` for provenance. Analysis was “join compiled relations, then classify from asserted tuples vs obligations.” Failures were cartesian pair×context expansion and a type-mismatched BOM join, not CSV parsing.

Ordinary Python was sufficient. No query language was added. SQL literals were optional, not required.

---

## 7. Python/SQL sufficient?

**MEASURED:** every WORLD program executed. All 20 call `open_world()`. 18/20 use `relation_rows`; 10/20 use `inspect_tuple`; 20/20 read obligations. No extra language was introduced.

**OBSERVED:** `open_world()` opened the fixture without a hardcoded view-id workaround. That v1 WORLD-specific cost is not present here.

---

## 8. Provenance subtest (task A, scored separately)

`support` present: **20/20** task A runs (rate 1.0). Presence only; locators were not required to match a gold evidence set.

RAW `support` cites workspace source paths (`sources/engineering_notes.md`, `manufacturer.csv`, `bom.csv`). WORLD `support` uses `inspect_tuple` grounding where called, and otherwise compiled-relation / obligation citations. That is World provenance, not a raw-file open in the WORLD workspace.

---

## 9. UNRESOLVED vs false

`unknown_as_false_count`: **0**.

Indoor X110/X160 was never scored as rejected/false. RAW A usually omitted the case. RAW A 009 and RAW B used `not_established` rather than `unresolved`. WORLD A failures kept indoor X110 as `UNRESOLVED` beside extra cartesian cases.

`ADJUDICATED_FALSE` remains unrepresentable. The frozen benchmark does not require it.

---

## 10. Semantic compilation vs “just SQL / cleaner tables”

Cannot be fully separated: WORLD also ships obligation state and completeness receipts, not only tuples.

Evidence that the WORLD win is not only “data is tabular”:

- RAW A had tabular BOM + manufacturer CSV and still never constructed indoor as a demanded case in 9/10 trials. WORLD A successes used `candidate_replacement` × deployment context plus `obligations` for missing `acceptable_replacement`.
- WORLD B 10/10, with isolation held, distinguished preventing constraints from uncertain semantic acceptance using compiled compatibility relations and obligations.
- RAW B 0/10 under isolation. v1 ITT RAW B was 3/5 with a contaminated filesystem. The isolation-held RAW failure is the missing-acceptance *label* (`not_established` vs `unresolved`) plus one omitted indoor case, not identifier-reconciliation (task C, deferred).

A WORLD loss mode that is *not* compilation: trials 001–002 are LLM join/case-set errors over already-compiled relations.

---

## 11. Untested

- Task C (deferred; identifier reconciliation)
- Other domains and larger worlds
- Construction cost of the World (C1/C2) vs programming savings
- LLM-authored ontology / construction
- Other models (this cell is `gpt-5.6-sol-high` only)
- Full session token accounting
- Line-level PREP/ANALYSIS/OUTPUT fractions (AST diagnostics only)
- Representing `ADJUDICATED_FALSE`

---

## 12. Second domain?

**HYPOTHESIS, now unblocked by isolation:** yes, as a separate campaign. This A/B cell produced a WORLD advantage that is not explained by reading human solutions. The signal is task A (RAW 0/10 vs WORLD 8/10) and task B (RAW 0/10 vs WORLD 10/10). RAW fails on case construction and on naming missing acceptance; WORLD fails on ordinary join/case-set mistakes.

Do not start a second domain inside this campaign. Task C remains deferred until someone decides it is worth an isolated C cell.

New programming tests should freeze `composer-2.5` unless a protocol is already locked to another model.

---

## Hypotheses

| Hypothesis | ITT | Notes |
|---|---|---|
| H1 correctness | Supported | 18/20 vs 0/20; non-overlapping CIs; Fisher *p* ≈ 3.4×10⁻⁹; isolation held |
| H2 semantic errors | Supported for this fixture | RAW A context omission; RAW B `not_established`; WORLD A cartesian/join; `UNKNOWN_AS_FALSE` was 0 in both arms |
| H3 acquisition burden | Mixed | Source-schema literals and `DictReader` fell; tool calls did not |
| H4 model effort | Not supported / not measured | Incomplete token fields; WORLD medians similar or higher |
| H5 code structure | Observed | WORLD relations/obligations vs RAW parsers; LOC slightly smaller for WORLD |

---

## Conclusions

### MEASURED

- RAW exact success **0/20**; WORLD **18/20**.
- Per-task ITT: RAW A 0/10, RAW B 0/10; WORLD A 8/10, WORLD B 10/10.
- Failure classes: `CONTEXT_MATCHING` 10, `SEMANTIC_ACCEPTANCE` 12.
- `UNRESOLVED` → false count: **0**.
- Task A `support` present on all 20 runs.
- Isolation leak runs: **0**. Preflight ok: **40/40**.
- All 40 saved programs executed; 0 timeouts.

### OBSERVED

- Physical isolation (bwrap tmpfs, live dirs under `/tmp`, Cursor sandbox disabled) held. v1 isolation did not.
- RAW A consistently generated cases from notes rather than from BOM contexts of a candidate pair (9/10 omitted indoor).
- RAW B constructed indoor but named missing acceptance `not_established` (9/10).
- WORLD A 8/10 recovered the indoor UNRESOLVED case from compiled relations plus obligations. The two WORLD losses are cartesian expansion / type-mismatched BOM join.
- WORLD B 10/10. `open_world()` opened the stored view without a view-id workaround.

### HYPOTHESIS

- WORLD helps when the hard part is constructing demanded cases and keeping missing acceptance distinct from false, given compiled relations plus obligations.
- That does not imply construction cost is justified, other domains benefit, or Python/SQL is the right long-term interface.
- A second domain is now a live question. Task C is still a separate isolated cell, not a follow-on inside this report.

---

## Stop

All 40 preregistered runs completed. Isolation held. The frozen scorer produced ITT scores. This report answers the preregistered questions. The World kernel, expected outputs, indoor obligation, C0/C1/C2, and operational frontier were not modified to improve WORLD performance.
