# LLM programming: RAW sources vs compiled World IR

Experiment `bom-llm-world-programming-v1`.
Manifest fingerprint: `sha256:bb42908a97c64524c99afc6e1b39560715d1d99d135cc0f78a4fd45ac1da69a5`.
Provider/model calls: **30**. No further inference after this report.

Primary metric: the saved program executes in a clean copy of its condition environment, and canonical JSON matches the frozen expected artifact from `research/semantic_integration/domains/bom/world_programming/expected/`.

The strongest supportable claim from the preregistered analysis is:

> Under this frozen BOM programming benchmark and `gpt-5.6-sol-high` / `cursor-agent-isolated-workspace-agent-v1`, programming against compiled World IR produced **13/15** exact task successes versus **8/15** against raw sources. Wilson 95% intervals overlap. The WORLD advantage is concentrated in replacement-state and qualification tasks. Task C cannot be interpreted as a RAW programming result because every RAW C trial read the human-written benchmark implementation.

---

## Protocol (frozen before inference)

| Item | Value |
|---|---|
| Model | `gpt-5.6-sol-high` (stream-json reports `GPT-5.6 Sol 272K High`) |
| Adapter | `cursor-agent-isolated-workspace-agent-v1` |
| Agent mode | default agent (write + shell); not ask mode |
| Flags | `--print --output-format stream-json --force --trust --sandbox enabled --workspace` |
| Temperature | not exposed by CLI |
| Budget | 600 s wall-clock per trial, identical RAW/WORLD |
| Replication | 3 tasks × 2 conditions × 5 trials = 30 (preregistered; not changed) |
| Timeouts | 0 |
| Execution failures | 0 |

The frozen human benchmark was not modified. Expected outputs were used only in the scorer.

---

## 1. Exact task success (primary)

### Intent-to-treat (all 30 preregistered runs)

| Condition | Pass | Rate | Wilson 95% |
|---|---:|---:|---|
| RAW | 8/15 | 53.3% | [0.30, 0.75] |
| WORLD | 13/15 | 86.7% | [0.62, 0.96] |

WORLD increased the point estimate. The intervals overlap. A two-sided Fisher exact test on the 2×2 table is approximately *p* ≈ 0.11. Do not treat ITT as a significant difference.

### Per task

| Cell | Pass | Rate |
|---|---:|---:|
| `raw:analysis_a` | 0/5 | 0% |
| `raw:analysis_b` | 3/5 | 60% |
| `raw:analysis_c` | 5/5 | 100% |
| `world:analysis_a` | 3/5 | 60% |
| `world:analysis_b` | 5/5 | 100% |
| `world:analysis_c` | 5/5 | 100% |

---

## Isolation failure (post-hoc, required)

Workspaces were copied per trial. `--sandbox enabled` and `--workspace` did **not** make the parent git repository inaccessible.

**11/30** trials `Read` at least one of:

- human-written `world_programming/{raw,world}/analysis_*.py` or `raw/io.py`;
- expected artifacts;
- another trial's `final_program.py` / `final_output.json` / `metrics.json` / `prompt.txt`;
- campaign harness files (`scorer.py`, `prompts.py`, `workspaces.py`, tests).

Audit: `scoring/isolation_audit.json`.

| Contamination | Trials |
|---|---|
| Human solution | RAW C 001–005; WORLD A 001; WORLD C 001–002 |
| Expected JSON | WORLD C 001 (`expected/interfaces.json`) |
| Other trial artifacts | RAW B 001, 004; RAW C 003, 005; WORLD C 002, 004 |
| Harness | RAW B 004; RAW C 001; WORLD A 001 |

**RAW C 5/5 is not a valid RAW programming result.** Every RAW C trial read the human RAW implementation.

WORLD C still has independent successes: trial 003 had no such Reads and passed; trial 005 did not Read solutions.

### Sensitivity excluding contaminated Reads (not preregistered)

| Condition | Pass | Rate |
|---|---:|---:|
| RAW | 2/8 | 25% |
| WORLD | 9/11 | 82% |

| Cell | Clean-read pass |
|---|---|
| RAW A | 0/5 |
| RAW B | 2/3 |
| RAW C | 0 remaining trials |
| WORLD A | 2/4 (trials 002 and 004 pass; 003 OTHER; 005 SEMANTIC_ACCEPTANCE) |
| WORLD B | 5/5 |
| WORLD C | 2/2 |

This subset was selected after seeing transcripts. It is a robustness check, not a new primary endpoint.

---

## 2–3. Semantic error categories

Classifier output (failed runs only):

| Class | Count | Where |
|---|---:|---|
| `CONTEXT_MATCHING` | 5 | all RAW A |
| `SEMANTIC_ACCEPTANCE` | 3 | RAW B 001–002; WORLD A 005 |
| `OTHER` | 1 | WORLD A 003 |
| `UNKNOWN_AS_FALSE` | 0 | — |

### RAW A — demanded context never constructed

All five RAW A programs executed and wrote valid `replacement_state` JSON. They emitted only the two candidate/context pairs written as `Candidate:` records in `engineering_notes.md` (outdoor enclosure, high-vibration cabinet). They never produced `context:indoor_panel`.

The indoor case is demanded by BOM-B plus the X110/X160 candidate pair, not by a positive note. RAW programs treated notes as the case generator. That is source-schema / context-construction, scored as `CONTEXT_MATCHING`.

They did not label indoor as false; they omitted it.

### RAW B — label, not false

Two RAW B failures used `semantic_state: "not_established"` for indoor while listing `semantic_acceptance` under `leaves_viability_uncertain` and leaving `prevents_viability` empty. They did not treat missing acceptance as a failed qualification. The frozen expected label is `unresolved`.

### WORLD A — join / case generation, not false

- Trial 003: indoor X110/X160 is `UNRESOLVED` (correct epistemic class) but `bom_items` includes `bom:BOM-D` and `mechanical_state` is `unsuitable`. BOM-D is an indoor connector, not the same part type. This is a join without a type/requirement filter. Class `OTHER`.
- Trial 005: cartesian expansion of candidate pairs × contexts. The first indoor object is R210/R200 `not_established`. The X110/X160 indoor object in the same payload remains `UNRESOLVED`. The classifier looks at the first indoor case.

WORLD A trial 002 (no human-solution Read) queried `candidate_replacement`, `acceptable_replacement`, completeness on `eligible_part`, and `obligations.json`, then classified missing acceptance plus an obligation as `unresolved`. That is a clean WORLD success.

---

## 4. Acquisition and source-schema reasoning

Median tool metrics (provider stream-json `tool_call started` events):

| | RAW | WORLD |
|---|---:|---:|
| tool calls | 17 | 19 |
| shell calls | 2 | 5 |
| reads | 7 | 8 |
| python executions (guess from shell) | 2 | 5 |

WORLD did **not** reduce tool-call count. WORLD programs never used `csv.DictReader`. Median source-schema field literals in final code: RAW **11**, WORLD **1**. Median World relation references: RAW 4 (string collisions such as `part_type`), WORLD **7**. Median SQL literals: RAW **0**, WORLD **4**.

`inspect_tuple` appears in all five WORLD A programs and in WORLD C programs; not in RAW.

Interpretation: WORLD reduced *source-column* reasoning inside the saved program. It did not reduce *interaction* count. Some WORLD interaction is schema introspection and recovering from `open_world()` failing (hardcoded TaskView `view_id` in `world_surface.py` does not match the fixture). Every WORLD A program includes a view-id workaround. That is API friction, not a RAW parsing cost.

---

## 5. Tokens, tools, iterations

Provider-reported medians:

| | RAW | WORLD |
|---|---:|---:|
| input tokens | 30 | 36 |
| output tokens | 4308 | 6821 |
| total | 4335 | 6860 |

**Do not interpret these as session cost.** Input counts in the 24–54 range cannot be full-context usage for an agent that reads files. The stream-json `result.usage` field is treated as incomplete. H4 (WORLD cheaper in tokens) is **not measured**.

On the incomplete output-token field and on tool calls, WORLD is not cheaper. Median nonempty LOC is higher for WORLD (170 vs 138), including the view-id workaround.

---

## 6. Where effort went

### RAW

Preparation/reconciliation: CSV/`DictReader`, notes regex, identifier prefixing, manufacturer-to-BOM joins, reconstructing mechanical suitability from voltage/temperature/type columns. Analysis was mostly “cases = note candidates,” which is why indoor vanished in task A.

### WORLD

Introspection (`WORLD_API.md`, `relation_schema`, `describe`), SQL/`query_semantic`, completeness receipts, obligation lists, `inspect_tuple` for provenance. Analysis was “join compiled relations, then classify from asserted tuples vs obligations.” Failures were SQL/case-set mistakes (extra BOM item, cartesian product), not CSV parsing.

Ordinary Python and SQL were sufficient. No query language was added.

---

## 7. Python/SQL sufficient?

**MEASURED:** every WORLD program that passed used the documented Python/SQL surface (`query` / `query_semantic` / `relation_rows` / `inspect_tuple`). No extra language was introduced. All 15 WORLD programs executed.

**OBSERVED:** `open_world()` as shipped in the workspace did not open the fixture until the model recovered the stored `view_id`. That cost is WORLD-specific and is not a RAW parsing cost.

---

## 8. Provenance subtest (task A, scored separately)

`support` present: **10/10** task A runs (rate 1.0). Presence only; locators were not required to match a gold evidence set.

RAW `support` cites workspace source paths (`sources/engineering_notes.md`, `manufacturer.csv`, `bom.csv`). WORLD `support` uses `inspect_tuple` grounding and typically emits native handles such as `bom.csv` / `engineering_notes.md` with row/line locators. That is legitimate World provenance, not a raw-file open in the WORLD workspace.

---

## 9. UNRESOLVED vs false

`unknown_as_false_count`: **0**.

Indoor X110/X160 was never scored as rejected/false. RAW A omitted the case. RAW B used `not_established` rather than `unresolved`. WORLD A failures kept indoor X110 as `UNRESOLVED` (trial 003) or still listed it as `UNRESOLVED` beside extra cartesian cases (trial 005).

`ADJUDICATED_FALSE` remains unrepresentable. The frozen benchmark does not require it.

---

## 10. Semantic compilation vs “just SQL / cleaner tables”

Cannot be fully separated: WORLD also ships obligation state and completeness receipts, not only tuples.

Evidence that the WORLD win is not only “data is tabular”:

- RAW A had tabular BOM + manufacturer CSV and still never constructed indoor as a demanded case. WORLD A successes used `candidate_replacement` × deployment context plus `obligations` for missing `acceptable_replacement`.
- WORLD B 5/5, including five trials with no human-solution Read, distinguished preventing constraints from uncertain semantic acceptance using compiled compatibility relations and obligations.
- Task C was designed to stress RAW identifier reconciliation (`manufacturer_part_number` vs `part_number`). Isolation collapse prevents a RAW vs WORLD comparison there.

A WORLD loss mode that is *not* compilation: trial 003/005 are LLM join/case-set errors over already-compiled relations.

---

## 11. Untested

- Other domains and larger worlds
- Construction cost of the World (C1/C2) vs programming savings
- LLM-authored ontology / construction
- Other models
- A campaign whose filesystem isolation actually holds
- Full session token accounting
- Line-level PREP/ANALYSIS/OUTPUT fractions (AST diagnostics only)
- Representing `ADJUDICATED_FALSE`

---

## 12. Second domain?

**HYPOTHESIS, conditional:** yes, after isolation is actually physical (trial workspaces outside the repo, or a sandbox that cannot `Read`/`Grep` the parent tree). The cleanest signal here is task A (RAW 0/5 vs WORLD 2/4 uncontaminated) and task B (WORLD 5/5 uncontaminated vs RAW 2/3). Task C must be re-run under isolation before it counts.

Do not start a second domain in this campaign.

---

## Hypotheses

| Hypothesis | ITT | Notes |
|---|---|---|
| H1 correctness | Directional WORLD | 13/15 vs 8/15; overlapping CIs; Task C RAW invalid |
| H2 semantic errors | Partial | RAW A context omission disappeared in successful WORLD A; `UNKNOWN_AS_FALSE` was 0 in both arms |
| H3 acquisition burden | Mixed | Source-schema literals fell; tool calls did not |
| H4 model effort | Not supported / not measured | Incomplete token fields; WORLD medians higher |
| H5 code structure | Observed | WORLD SQL/relations vs RAW parsers; LOC not smaller |

---

## Conclusions

### MEASURED

- RAW exact success **8/15**; WORLD **13/15**.
- Per-task ITT: RAW A 0/5, RAW B 3/5, RAW C 5/5; WORLD A 3/5, WORLD B 5/5, WORLD C 5/5.
- Failure classes: `CONTEXT_MATCHING` 5, `SEMANTIC_ACCEPTANCE` 3, `OTHER` 1.
- `UNRESOLVED` → false count: **0**.
- Task A `support` present on all 10 runs.
- 11/30 trials Read forbidden parent-repo artifacts.
- All 30 saved programs executed; 0 timeouts.

### OBSERVED

- Cursor-agent `--sandbox enabled` did not isolate trials from this repository. Later trials could (and did) read human solutions and prior trial outputs.
- RAW A consistently generated cases from notes rather than from BOM contexts of a candidate pair.
- WORLD programs recovered a TaskView view-id mismatch before doing semantic work.
- WORLD B is the least contaminated WORLD cell (5/5, 0 human-solution Reads).

### HYPOTHESIS

- WORLD helps when the hard part is constructing demanded cases and keeping missing acceptance distinct from false, given compiled relations plus obligations.
- That does not imply construction cost is justified, other domains benefit, or Python/SQL is the right long-term interface.
- Next campaign should isolate first, then replicate tasks A/B, then reconsider C and a second domain.

---

## Stop

All 30 preregistered runs completed. The frozen scorer produced ITT scores. This report answers the preregistered questions. The World kernel, expected outputs, indoor obligation, C0/C1/C2, and operational frontier were not modified to improve WORLD performance.
