# Purpose-First Python Spine Probe v1

Sealed interpretation: **PURPOSE_FIRST_PYTHON_SPINE_SUPPORTED**

Not Constructor v3.2. TaskView/kernel, Constructor v3.1.1, P3/P5, Spine Compiler Probe v1, and prose probes were not modified.

## MEASURED headline

- successful clean runs: 5/5
- E1 mean recall: 1.00 (v1 was 0.46)
- candidate correspondence materialized: 5/5
- E3 mean groups/instances: 16.0 / 2972.0
- WHEN DISCHARGING: 5/5
- staged TDS: 5/5
- source authority: 5/5

P3 counts were {'T1': 2776, 'T2': 958, 'T3': 5152, 'T4': 4092, 'T5': 2506} (mean 3096.8). B3 ~1800/replicate. Spine Compiler v1 mean groups 5.4 / instances 955.2 (unlike grains).

## OBSERVED

T1 and T5 match the source-native comment `WHEN DISCHARGING` in order to emit `purpose.unresolved`, not to assert conditional monitoring as World truth. Flagged by the hardcode audit; not silently rewritten.
T5 Read-tool traces missed the CSVs; construction.py still loaded them via Source.rows.

## Required questions

### 1

5/5 clean executions succeeded (MEASURED). IR bind failures of the JSON probe are replaced by ordinary Python/API errors when they occur.

### 2

5/5 final programs executed successfully after at most 3 attempts; mean attempts 1.0 (MEASURED).

### 3

Candidate correspondence materialized in 5/5 trials (MEASURED).

### 4

Mean primary E1 1.00 (all trials); 1.0 over successful runs. Spine Compiler Probe v1 mean E1 was 0.46 (MEASURED).

### 5

Staged TDS hole hits 5/5 (MEASURED).

### 6

WHEN DISCHARGING unresolved dependency hits 5/5 (MEASURED).

### 7

Source-authority hole hits 5/5 (MEASURED).

### 8

Mean hole groups 16.0; mean instances 2972.0 (MEASURED).

### 9

Mean E2 distinctions 7.0/7. Low groups with failed/empty candidate correspondence is a weak spine, not compression (OBSERVED).

### 10

Mean purpose-relevant group fraction 1.0 (OBSERVED heuristic).

### 11

E5: {"distinctions": {"measurement": {"n_true": 5, "stable": true}, "limit": {"n_true": 5, "stable": true}, "parameter_context": {"n_true": 5, "stable": true}, "period_or_interval": {"n_true": 5, "stable": true}, "candidate_correspondence": {"n_true": 5, "stable": true}, "document_inventory": {"n_true": 5, "stable": true}, "opaque_code_or_text": {"n_true": 5, "stable": true}}} (OBSERVED).

### 12

See construction_traces.md for per-trial reads/shells before spine decisions (OBSERVED from tool events).

### 13

Per-trial first-failure buckets are in trial_results.md (OBSERVED).

### 14

Model: purpose interpretation, which distinctions to commit, which fields need interpretation, join predicates (OBSERVED).

### 15

Deterministic: CSV load, profiles, joins, date parsing, uniqueness/numeric/interpreted checks, hole grouping (MEASURED by construction).

### 16

Yes, as a next probe only: 5/5 spines materialized, diagnostic seams all fired, and the JSON-IR physical confound is gone. Do not implement hole→retrieval→P5 here (HYPOTHESIS).

## STOP

No constructor promotion. No P1–P4 collapse. No prose retrieval. No P5.

