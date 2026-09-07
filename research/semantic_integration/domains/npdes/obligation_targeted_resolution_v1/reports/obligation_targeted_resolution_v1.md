# Obligation-Driven Targeted Semantic Resolution Probe v1

Sealed interpretation: **MIXED_OBLIGATION_RESOLUTION_RESULT**

Draft spine: sealed Purpose-First Python Spine Probe **T5**.
Model: **Composer 2.5** on every successful host call (Arm A ×20, Arm B retrieve+adjudicate ×24×2).
GOLD and `evaluator_only/establishability.json` were not copied into host workspaces.
This is evaluator/host-agent evidence, not real-user usability. Not constructor promotion.

## What was tested

```text
semantic obligation → evidence plan → targeted retrieval → bounded packet
→ bounded judgment → semantic proposal → disposable dry-run → admit or UNRESOLVED
```

Desired shape: many blocked occurrences → few reusable obligations → few investigations → few judgments → many deterministic consequences.

## Required answers

### 1. How many raw hole occurrences are covered by the selected obligations?

MEASURED: **418** affected occurrences across 8 selected obligations (families counted separately; a row may appear in more than one family).

- nodi_c: 150
- nodi_9: 36
- when_discharging: 17
- geometric_mean: 40
- pass_fail: 12
- empty_numeric_limit: 57
- document_authority: 1
- monitoring_frequency: 105

T5 baseline hole instances were 535 across 8 hole groups. Selected coverage is 418 after splitting NODI by code and adding empty LIMIT_VALUE_NMBR rows that T5 never named as a hole.

### 2. How many reusable obligations remain after evidence-contact refinement?

MEASURED: initial selected = **8**. Host wrote refinements on **12** of 24 Arm B cells.
Typical children: geometric_mean → TDS vs non-TDS comment carryover (2); empty_numeric_limit → 4 comment-family partitions; monitoring_frequency → calendar vs continuous vs retest; nodi_9 → WET-optional vs TRC. Final reusable grain is on the order of **12–16** questions, not thousands of rows.

### 3. Does the factorization remain compact, or does it explode?

MEASURED: 23 candidate obligations after value-level grouping; 8 selected; refinements added a handful of children per parent. Not occurrence-level explosion. Not compact enough for the strict success label (refinement cells=12, threshold was ≤8).
OBSERVED: children follow mechanically computable structured partitions (PARAMETER_CODE, DMR_COMMENT_TEXT, LIMIT_FREQ_OF_ANALYSIS_CODE), not unique source wording per row.

### 4. How many selected obligations are establishable from the frozen corpus?

MEASURED evaluator labels: ESTABLISHABLE = ['when_discharging', 'geometric_mean', 'pass_fail'] (**3**).
NOT_ESTABLISHABLE: nodi_c, nodi_9, monitoring_frequency (no codebook in permit packages).
UNCERTAIN: empty_numeric_limit, document_authority.

### 5. Of establishable obligations, how many are successfully retrieved and resolved?

MEASURED: **3 / 3** had at least one Arm B trial with SUPPORTED_RESOLUTION or SUPPORTED_NEGATIVE.
when_discharging: 3/3 SUPPORTED_RESOLUTION with Aztec permit footnote *1 and statement-of-basis 'when discharging'.
pass_fail: 3/3 SUPPORTED_RESOLUTION with Farmington Part II 0/1 WET coding plus structured PASS=0 FAIL=1 comments.
geometric_mean: T1 UNRESOLVED (too broad / residual comparison statistic); T3 SUPPORTED_RESOLUTION after TDS vs non-TDS split; T2 parent UNRESOLVED but admitted a TDS-scoped proposal.
Establishing permit passages were retrieved into the frozen packets (not missed).

### 6. How many obligations correctly remain unresolved because the corpus is insufficient?

OBSERVED: nodi_c 3/3 UNRESOLVED + unadmitted, failure_mode EVIDENCE_INSUFFICIENT.
nodi_9 unadmitted on all trials; T1/T2 UNRESOLVED, T3 SUPPORTED_NEGATIVE without durable admit (still no NODI legend).
monitoring_frequency: T1 UNVERIFIED_PROPOSAL, T2 UNRESOLVED, T3 SUPPORTED_NEGATIVE unadmitted — no workspace codebook mapping 05/WK as a field legend, though occurrence-local permit tables can gloss some codes (see Arm A).
empty_numeric_limit parent remained UNRESOLVED after justified splits.

### 7. Are retrieval failure and evidence insufficiency distinguishable in practice?

YES for NODI. Evaluator pre-labeled NOT_ESTABLISHABLE; host failure_mode was EVIDENCE_INSUFFICIENT, not RETRIEVAL_FAILURE. Packets cite GCC permit/fact-sheet absence of a NODI legend rather than inventing EPA ICIS text.
unresolved_by_mode={"EVIDENCE_INSUFFICIENT": 9, "OBLIGATION_TOO_BROAD": 3}
An earlier unsealed Arm A wave *did* cite extra-corpus EPA NODI legends; the sealed protocol forbade that. Distinction requires both the hidden establishability audit and workspace-only grounding.

### 8. How much evidence is inspected per obligation?

MEASURED Arm B mean documents_touched=6.29 mean retained snippets=7.79 (cap 8).
pass_fail typically 2–3 documents; when_discharging 4–5; geometric_mean 3–4; document_authority 11–13 (over budget).

### 9. Does obligation-first retrieval avoid broad corpus attention?

MOSTLY. Plans named codebook vs permit-clause vs filename-metadata insufficiency before retrieval. Hosts did not run 'find all useful semantic passages'.
Exception: document_authority opened most of the 12 permit-text files to test cross-facility self-description; T1 recorded BUDGET_EXCEPTION.md. That is still bounded to inventoried permit packages, not the hidden GOLD corpus.
Instrumentation counts path touches under documents/; directory reads inflate n_documents_touched relative to unique .txt files.

### 10. Does one semantic judgment propagate to many occurrences?

YES for supported comment-family obligations.
T1 when_discharging: 535 → 518 hole instances (−17, matching the 17 WHEN DISCHARGING rows) and added `discharge_occurrence_in_period` (semantic sharpening).
T2/T3 when_discharging: 535 → 501 (−34); they removed `conditional_discharge_dependent_monitoring` and added a monitoring-condition relation without always emitting the factual discharge hole as cleanly as T1.
T1 pass_fail: 535 → 525 (−10-class) after replacing the pass/fail unresolved family with binary reporting relations.
T3 geometric_mean: numeric_comparison_candidate 342 → 318 (−24 non-TDS carryover rows) and removed `aggregated_reporting_requirement`.

### 11. What is the measured occurrences-per-semantic-judgment ratio?

MEASURED across all 24 Arm B cells: 418 / 24 = **17.416666666666668**.
That denominator counts unresolved cells too. Per supported reusable decision the leverage is higher: 17 WHEN DISCHARGING rows per when_discharging judgment; 12 pass/fail rows; 40 geometric-mean comment rows collapsing to a 16/24 TDS vs carryover split.

### 12. Does deterministic propagation affect exactly the intended occurrences?

T1 when_discharging delta matches the 17-row family and does not remove geometric-mean or pass/fail hole requirements.
T3 geometric_mean removed only `aggregated_reporting_requirement` (not WHEN DISCHARGING / pass-fail).
T2 pass_fail dry-run **failed** and is not a valid propagation observation.
leakage_flags after ignoring failed dry-runs: {}

### 13. Are sibling values/comments protected from semantic leakage?

NODI C was never admitted; NODI 9 was never admitted as a positive code legend. No trial wrote known=['C','9'].
geometric_mean refinements explicitly refuse to apply footnote *6 to BOD/pH/TSS rows that inherited the TDS comment — Arm A occurrence-first reached the same BOD-negative on A10/A11.
when_discharging dry-runs did not drop pass_fail or aggregated_reporting hole requirements.
document_authority replaced filename-only unresolved with role/precedence unresolved rather than ranking every kind from names alone.

### 14. Does resolving semantic meaning sometimes generate sharper factual obligations?

YES. T1 when_discharging is the spec's acceptable example: comment semantics resolved; `discharge_occurrence_in_period` added; remaining uncertainty is whether discharge occurred in FY2025 periods (structured NODI blank / numeric values present, not independently proving discharge).

### 15. Does obligation refinement improve semantic grain, or merely split source wording?

JUSTIFIED_FACTORIZATION for geometric_mean (TDS vs misattached comment), empty_numeric_limit (report-only / WET / WHEN DISCHARGING / geometric-mean empty cells), nodi_9 (optional WET retest vs TRC), monitoring_frequency (calendar vs 99/99 continuous vs 09/99 retest).
Not SURFACE_TEXT_SPLIT_ONLY: partitions are mechanically computable from structured fields and change the computational consequence.
Not OVERFRAGMENTATION to unique rows.

### 16. Does occurrence-first reasoning repeat the same retrieval/judgment work?

MEASURED Arm A n=20 mean documents_touched=4.9.
Three WHEN DISCHARGING samples each reopened Aztec final_permit + statement_of_basis. Three NODI C samples each searched GCC documents for a missing legend. Four monitoring_frequency samples each joined a local permit table.
Arm B asked the reusable question once per trial. Duplicate work is real even though mean documents/call is similar (Arm B mean is pulled up by document_authority).

### 17. Is obligation-first reasoning more semantically consistent than occurrence-first?

Arm A inconsistent interpretation sets (string-level): ['nodi_c', 'nodi_9', 'when_discharging', 'geometric_mean', 'pass_fail', 'empty_numeric_limit', 'monitoring_frequency'].
NODI 9 mixed UNRESOLVED (A04/A05) vs SUPPORTED_NEGATIVE on the WET retest row (A06) — occurrence-local optional-retest facts, not a code legend.
Arm B NODI C was stable UNRESOLVED. when_discharging and pass_fail were stable SUPPORTED_RESOLUTION.
geometric_mean and monitoring_frequency dispositions varied by trial (UNRESOLVED vs supported/negative) while the *consequential* split (TDS vs carryover; calendar vs special codes) recurred. Naming differences were ignored per spec.

### 18. Are there any unsupported durable closures?

MEASURED unsupported_closures=0 (target 0).
NODI C/9 were not admitted as World code legends. Sealed packets do not retain extra-corpus EPA dictionaries.
protocol_mismatches=['T2:geometric_mean'] (T2 geometric_mean: parent UNRESOLVED, TDS-scoped ADMIT_DISPOSABLE with footnote grounding).
failed_dry_runs=['T2:pass_fail'].
mutated_before_evidence=0: retrieve stage did not rewrite durable construction.py.

### 19. Do semantic proposals preserve exact source grounding?

Supported packets retain quoted permit footnotes and CSV locations (Aztec *1, Farmington *6/*9 / Part II 0/1 WET). Adjudicator workspaces had PACKET.json only — no documents/ tree.

### 20. Does scope remain distinct from epistemic admission?

YES in the artifact schema. Proposals carry separate `scope` and `epistemic_basis` and `admit`.
T1 monitoring_frequency used admit=UNVERIFIED_PROPOSAL while remaining UNRESOLVED — a WORLD-ish frequency guess was not treated as World truth.

### 21. Can a WORLD-scoped but unverified proposition remain unadmitted as World truth?

YES. T2 geometric_mean interpretation discussed WORLD-scope uncertainty while the admitted delta was ONE_SOURCE_VALUE (PARAMETER_CODE=70295). T1 monitoring_frequency stayed UNVERIFIED_PROPOSAL. empty_numeric_limit proposals were not admitted.

### 22. How many model semantic judgments relative to affected source occurrences?

Arm B: 24 adjudicator judgments (plus 24 retrieve calls) covering 418 selected occurrences, vs Arm A: 20 judgments covering 20 sampled rows.
If occurrence-first were run on all 150 NODI-C rows it would take 150 judgments for one missing legend; obligation-first used 3 retrieve+3 adjudicate and correctly refused closure.

### 23. Does the experiment support compile-meaning-once → compute-consequences-many-times at residual resolution?

PARTIALLY. Supported for WHEN DISCHARGING and pass/fail: one grounded permit reading, disposable construction change, many hole instances moved.
Supported negatively for NODI: compiling the reusable question prevented 150+36 invented legends.
Weaker where dry-run quality is uneven (T2 pass_fail crash) or parent/child admit protocol drifts (T2 geometric_mean).
Interpretation: **MIXED_OBLIGATION_RESOLUTION_RESULT** — not a clean promotion of obligation-factoring into the kernel.

### 24. Does the experiment support purpose-derived obligation → selective evidence → bounded judgment → grounded reusable semantic state as an alternative to broad prose attention?

YES as a *research mechanism*, with caveats.
Evidence plans constrained attention; packets were bounded (≤8 snippets); adjudicator could not search the corpus; establishable permit clauses were found without nominating the whole library; unsupported NODI closure was avoided.
Caveats: document_authority still opened most permit files; refinements multiplied questions (justifiably); disposable apply is not yet a reliable mechanical compiler (one crash); Arm A can locally join a permit table and 'resolve' a frequency code that the reusable codebook obligation correctly leaves unresolved.

## Bad outcomes checked

- 8 obligations → hundreds of bespoke obligations: **not observed**.
- One code meaning → model re-judges every row: **not observed in Arm B** (Arm A is that baseline, capped at 20).
- Resolver reads most of the corpus every question: **only document_authority** approached that, with a recorded budget exception.
- Structural correlation as durable NODI truth: **not admitted** in sealed Arm B.
- Comment-family leakage: **not observed** on successful dry-runs.
- Unresolved evidence treated as negative durable World: NODI 9 T3 SUPPORTED_NEGATIVE was **not admitted**.
- Retrieval failure mislabeled as insufficiency: NODI insufficiency matches the hidden audit.

## Interpretation

**MIXED_OBLIGATION_RESOLUTION_RESULT**

Factorization stayed compact at reusable grain. Targeted retrieval found establishing permit text when it existed (WHEN DISCHARGING, pass/fail, TDS geometric-mean footnotes). Unsupported NODI durable closure was 0. Propagation of supported comment semantics moved many hole instances. Obligation-first avoided repeating NODI/permit lookups per row.
The strict success label is withheld because refinements were frequent, document_authority overran the document budget, one disposable apply crashed, and one trial admitted a refined geometric-mean proposal while leaving the parent UNRESOLVED.

## STOP

No constructor/kernel change. No P1–P4 collapse. No semantic-family taxonomy. No broad prose nomination. No product promotion. No UI. No real-user study. No fifth domain. No spine rewrite from scratch.
