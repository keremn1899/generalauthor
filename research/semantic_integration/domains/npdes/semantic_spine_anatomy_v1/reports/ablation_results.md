# Ablation results

Research copies only. No model repair. Frozen E1/E2 functions imported read-only from Purpose-First Python Spine Probe v1.

Frozen E1 **did not move** on any single-element ablation (all remain 7/7). Labels below therefore rest on purpose-relevant precise coverage (cardinality hole, authored uniqueness, NODI hole, document-text hole), not on the coarse triggerability scorer.

## MEASURED baseline reruns of unmodified copies

| trial | ok | E1 hits | E2 | groups | instances |
| --- | --- | --- | --- | --- | --- |
| T1 | True | 7 | 7 | 14 | 3414 |
| T2 | True | 7 | 7 | 16 | 1891 |
| T3 | True | 7 | 7 | 31 | 6116 |
| T4 | True | 7 | 7 | 11 | 2904 |
| T5 | True | 7 | 7 | 8 | 535 |

## MEASURED single-element ablations

| trial | element | removed | ok | E1 | E2 | groups | ΔE1 | ΔE2 | Δgroups | TDS* | WHEN* | NODI* | AUTH* | label |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T1 | drop_season_month_flag | 1 | True | 7 | 7 | 13 | 0 | 0 | -1 | 1 | 1 | 1 | 1 | LOCALLY_REDUNDANT_FOR_PURPOSE |
| T1 | drop_limit_freq | 1 | True | 7 | 7 | 13 | 0 | 0 | -1 | 1 | 1 | 1 | 1 | LOCALLY_REDUNDANT_FOR_PURPOSE |
| T1 | drop_unique_catalog | 1 | True | 7 | 7 | 12 | 0 | 0 | -2 | 1 | 1 | 1 | 1 | REQUIRED_FOR_PURPOSE |
| T1 | drop_unique_schedule | 1 | True | 7 | 7 | 14 | 0 | 0 | 0 | 1 | 1 | 1 | 1 | LOCALLY_REDUNDANT_FOR_PURPOSE |
| T1 | drop_nodi | 1 | True | 7 | 7 | 13 | 0 | 0 | -1 | 1 | 1 | 0 | 1 | REQUIRED_FOR_PURPOSE |
| T1 | drop_comment_interpret | 1 | True | 7 | 7 | 13 | 0 | 0 | -1 | 1 | 1 | 1 | 1 | LOCALLY_REDUNDANT_FOR_PURPOSE |
| T1 | drop_when_unresolved | 1 | True | 7 | 7 | 13 | 0 | 0 | -1 | 1 | 1 | 1 | 1 | LOCALLY_REDUNDANT_FOR_PURPOSE |
| T1 | drop_non_numeric_class | 1 | True | 7 | 7 | 13 | 0 | 0 | -1 | 1 | 1 | 1 | 1 | LOCALLY_REDUNDANT_FOR_PURPOSE |
| T2 | drop_seasonal | 1 | True | 7 | 7 | 15 | 0 | 0 | -1 | 1 | 1 | 1 | 0 | LOCALLY_REDUNDANT_FOR_PURPOSE |
| T2 | drop_unique | 1 | True | 7 | 7 | 16 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | REQUIRED_FOR_PURPOSE |
| T2 | drop_nodi | 1 | True | 7 | 7 | 15 | 0 | 0 | -1 | 1 | 1 | 1 | 0 | LOCALLY_REDUNDANT_FOR_PURPOSE |
| T2 | drop_comment | 1 | True | 7 | 7 | 15 | 0 | 0 | -1 | 1 | 1 | 1 | 0 | LOCALLY_REDUNDANT_FOR_PURPOSE |
| T3 | drop_value_type | 1 | True | 7 | 7 | 30 | 0 | 0 | -1 | 1 | 1 | 1 | 1 | LOCALLY_REDUNDANT_FOR_PURPOSE |
| T3 | drop_limit_unit | 1 | True | 7 | 7 | 30 | 0 | 0 | -1 | 1 | 1 | 1 | 1 | LOCALLY_REDUNDANT_FOR_PURPOSE |
| T3 | drop_seasonal_loop | 1 | True | 7 | 7 | 19 | 0 | 0 | -12 | 1 | 1 | 1 | 1 | LOCALLY_REDUNDANT_FOR_PURPOSE |
| T3 | drop_unique_permit_limit | 1 | True | 7 | 7 | 31 | 0 | 0 | 0 | 1 | 1 | 1 | 1 | LOCALLY_REDUNDANT_FOR_PURPOSE |
| T3 | drop_nodi | 1 | True | 7 | 7 | 30 | 0 | 0 | -1 | 1 | 1 | 1 | 1 | LOCALLY_REDUNDANT_FOR_PURPOSE |
| T3 | drop_comment_interpret | 1 | True | 7 | 7 | 30 | 0 | 0 | -1 | 1 | 1 | 1 | 1 | LOCALLY_REDUNDANT_FOR_PURPOSE |
| T4 | drop_freq | 1 | True | 7 | 7 | 10 | 0 | 0 | -1 | 1 | 1 | 1 | 0 | LOCALLY_REDUNDANT_FOR_PURPOSE |
| T4 | drop_unique | 1 | True | 7 | 7 | 11 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | REQUIRED_FOR_PURPOSE |
| T4 | drop_nodi | 1 | True | 7 | 7 | 10 | 0 | 0 | -1 | 1 | 1 | 1 | 0 | LOCALLY_REDUNDANT_FOR_PURPOSE |
| T4 | drop_comment | 1 | True | 7 | 7 | 10 | 0 | 0 | -1 | 1 | 1 | 1 | 0 | LOCALLY_REDUNDANT_FOR_PURPOSE |
| T5 | drop_aggregated | 1 | True | 7 | 7 | 7 | 0 | 0 | -1 | 1 | 1 | 1 | 1 | LOCALLY_REDUNDANT_FOR_PURPOSE |
| T5 | drop_pass_fail | 1 | True | 7 | 7 | 7 | 0 | 0 | -1 | 1 | 1 | 1 | 1 | LOCALLY_REDUNDANT_FOR_PURPOSE |
| T5 | drop_unique | 1 | True | 7 | 7 | 8 | 0 | 0 | 0 | 0 | 1 | 1 | 1 | REQUIRED_FOR_PURPOSE |
| T5 | drop_nodi | 1 | True | 7 | 7 | 7 | 0 | 0 | -1 | 1 | 1 | 0 | 1 | REQUIRED_FOR_PURPOSE |
| T5 | drop_comment | 1 | True | 7 | 7 | 7 | 0 | 0 | -1 | 1 | 1 | 1 | 1 | LOCALLY_REDUNDANT_FOR_PURPOSE |
| T5 | drop_document_unresolved | 1 | True | 7 | 7 | 7 | 0 | 0 | -1 | 1 | 1 | 1 | 0 | REQUIRED_FOR_PURPOSE |
| T5 | drop_sample_type | 1 | True | 7 | 7 | 7 | 0 | 0 | -1 | 1 | 1 | 1 | 1 | LOCALLY_REDUNDANT_FOR_PURPOSE |
| T5 | drop_freq | 1 | True | 7 | 7 | 7 | 0 | 0 | -1 | 1 | 1 | 1 | 1 | LOCALLY_REDUNDANT_FOR_PURPOSE |

T2/T4 AUTH* is 0 on every row because those trials inventory documents but emit no document-text hole (frozen E1 authority still hits via inventory tokens). That is a coverage gap relative to T1/T3/T5, not an ablation artifact.

### Locally redundant under this purpose/fixture

- `T1/drop_season_month_flag` (Δgroups=-1)
- `T1/drop_limit_freq` (Δgroups=-1)
- `T1/drop_unique_schedule` (Δgroups=0)
- `T1/drop_comment_interpret` (Δgroups=-1)
- `T1/drop_when_unresolved` (Δgroups=-1)
- `T1/drop_non_numeric_class` (Δgroups=-1)
- `T2/drop_seasonal` (Δgroups=-1)
- `T2/drop_nodi` (Δgroups=-1)
- `T2/drop_comment` (Δgroups=-1)
- `T3/drop_value_type` (Δgroups=-1)
- `T3/drop_limit_unit` (Δgroups=-1)
- `T3/drop_seasonal_loop` (Δgroups=-12)
- `T3/drop_unique_permit_limit` (Δgroups=0)
- `T3/drop_nodi` (Δgroups=-1)
- `T3/drop_comment_interpret` (Δgroups=-1)
- `T4/drop_freq` (Δgroups=-1)
- `T4/drop_nodi` (Δgroups=-1)
- `T4/drop_comment` (Δgroups=-1)
- `T5/drop_aggregated` (Δgroups=-1)
- `T5/drop_pass_fail` (Δgroups=-1)
- `T5/drop_comment` (Δgroups=-1)
- `T5/drop_sample_type` (Δgroups=-1)
- `T5/drop_freq` (Δgroups=-1)

### Required for purpose (measurable degradation)

- `T1/drop_unique_catalog` (ΔE1=0, ΔE2=0)
- `T1/drop_nodi` (ΔE1=0, ΔE2=0)
- `T2/drop_unique` (ΔE1=0, ΔE2=0)
- `T4/drop_unique` (ΔE1=0, ΔE2=0)
- `T5/drop_unique` (ΔE1=0, ΔE2=0)
- `T5/drop_nodi` (ΔE1=0, ΔE2=0)
- `T5/drop_document_unresolved` (ΔE1=0, ΔE2=0)

### Coupled or indeterminate

- none

## Candidate locally deletion-minimal set

Modest claim: **locally deletion-minimal under the tested purpose and fixture**, not a globally minimal ontology.

Keep, across trials, the intersection of elements whose removal was REQUIRED_FOR_PURPOSE or that belong to the 5/5 stable core even when a single-element drop did not move frozen E1:

- FY2025-scoped measurement/limit correspondence with interval structure
- uniqueness of applicable limit (authored even when the cardinality hole is not the E1 token)
- NODI interpretation
- permit-comment interpretation or an equivalent unresolved discharge-condition hole
- document inventory plus unavailable-narrative hole
- numeric vs non-numeric/report-only split

Drop candidates that survived as LOCALLY_REDUNDANT_FOR_PURPOSE (seasonal-month flags, extra frequency/sample-type/unit/value-type interprets, T5 pass-fail and geometric-mean extras when comment/NODI/document holes remain).

## OBSERVED

Interactions (not jointly ablated):

- T1 `unique_catalog_variant` is the only cardinality hole; `unique_schedule_match` is satisfied. Dropping catalog loses the TDS uniqueness hole; dropping schedule does not. The pair is coupled: uniqueness remains authored if either `require_unique` survives.
- T1/T5 WHEN-literal unresolved and generic comment `require_interpreted` substitute for each other on WHEN* precise coverage.
- T2/T3/T4 NODI is duplicated across interpret + unresolved; dropping one named NODI requirement leaves another.
- T2/T4 have document inventory relations but no dedicated document-text hole; frozen E1 authority still fires from inventory tokens plus unrelated UNINTERPRETED groups.

## HYPOTHESIS

A substantially smaller locally deletion-minimal semantic core exists; T5 is already close to it.
