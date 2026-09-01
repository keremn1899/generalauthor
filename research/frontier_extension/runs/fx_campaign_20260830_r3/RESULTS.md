# Frozen frontier-extension campaign results

Campaign validity: valid.

- T_SQL: 11/14 exact; 11/14 valid
- T_GRAPH: 7/14 exact; 7/14 valid

| Case | Arm | Valid execution | Exact correct | Wall seconds | Participant errors |
| --- | --- | --- | --- | ---: | ---: |
| FX01 | T_SQL | True | True | 31.82 | 0 |
| FX01 | T_GRAPH | True | False | 87.27 | 8 |
| FX02 | T_SQL | True | True | 36.25 | 0 |
| FX02 | T_GRAPH | False | False | 240.05 | 5 |
| FX03 | T_SQL | True | True | 30.03 | 0 |
| FX03 | T_GRAPH | True | True | 73.06 | 4 |
| FX04 | T_SQL | True | True | 39.64 | 0 |
| FX04 | T_GRAPH | True | True | 148.52 | 8 |
| FX05 | T_SQL | True | True | 70.66 | 0 |
| FX05 | T_GRAPH | True | True | 164.13 | 31 |
| FX06 | T_SQL | True | True | 99.48 | 0 |
| FX06 | T_GRAPH | True | True | 225.36 | 10 |
| FX07 | T_SQL | True | True | 79.86 | 0 |
| FX07 | T_GRAPH | True | True | 214.15 | 4 |
| FX08 | T_SQL | True | True | 47.04 | 0 |
| FX08 | T_GRAPH | True | True | 97.29 | 4 |
| FX09 | T_SQL | True | True | 40.84 | 0 |
| FX09 | T_GRAPH | False | False | 240.25 | 16 |
| FX10 | T_SQL | True | False | 131.30 | 0 |
| FX10 | T_GRAPH | False | False | 240.23 | 12 |
| FX11 | T_SQL | True | False | 97.47 | 0 |
| FX11 | T_GRAPH | False | False | 240.22 | 5 |
| FX12 | T_SQL | True | True | 40.44 | 0 |
| FX12 | T_GRAPH | True | True | 172.14 | 11 |
| FX13 | T_SQL | True | True | 89.90 | 0 |
| FX13 | T_GRAPH | False | False | 240.25 | 10 |
| FX14 | T_SQL | True | False | 92.50 | 0 |
| FX14 | T_GRAPH | True | False | 159.52 | 7 |

## Execution status

- Protocol version: frozen-frontier-extension-v1
- Candidate source: research/frontier_extension/candidates_v5_final_review
- Declared model: Composer 2.5
- Model selector: composer-2.5
- Model command: cursor-agent -p --output-format stream-json --model composer-2.5 --force
- Episode count: 28
- Arms: T_SQL, T_GRAPH
- Retry policy: no within-episode automatic retries
- Abort reason: none

## Preflight

The sealed run passed preflight before execution. The preflight receipt records the following checks as passing:

- model callable: true
- SQL treatment callable: true
- graph treatment callable: true
- model identity matches declared model: true
- excluded operation rejected: true
- logging endpoints work: true
- treatment matches manifest: true
- quota detector operational: true

This verifies that the harness and treatment surface were structurally valid before model execution began.

## Execution notes

The campaign ran through all scheduled cells without a campaign-level abort. A false quota detection bug was corrected before execution, and the rerun did not terminate on a raw text match such as a timestamp containing `429`.

The graph treatment remained subject to a separate operational issue that can arise when multiple graph CLI calls overlap on the same `.lbug` file. That issue is a single-owner lock problem in LadybugDB and is distinct from a real account or model quota failure. In this rerun, the harness did not abort on that condition, and the campaign proceeded to completion.

## Result summary

The execution completed with all 28 expected cells present. The overall campaign remained valid and complete. The primary result pattern is that the T_SQL arm remained substantially stronger across the campaign, while several T_GRAPH cells were invalid or timed out under the frozen treatment.

The current execution shows a mixed outcome profile rather than a uniform winner across arms. The sealed records retain the full event telemetry for later preregistered analysis.

## Interpretation discipline

This report intentionally contains no SQL-versus-graph frontier conclusion.

The sealed records retain SQL statement/row telemetry and graph-operation,
program, result-mode, and evidence telemetry for the preregistered analysis.

No causal interpretation is made here; these are the required execution outcomes.
