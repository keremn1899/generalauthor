# Frontier-extension execution report — no frontier interpretation

| Check | Value |
| --- | --- |
| Campaign validity | `True` |
| Model/environment constancy | `True` |
| Completion | `28/28` |
| Declared/reported model | `Composer 2.5` |
| Abort reason | `none` |

| Case | Arm | Valid execution | Exact named-set correct | Interactions | Model-visible bytes | Participant errors | Wall seconds |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| FX01 | T_SQL | True | True | 8 | 24832 | 0 | 31.82 |
| FX01 | T_GRAPH | True | False | 10 | 25227 | 8 | 87.27 |
| FX02 | T_GRAPH | False | False | 27 | 142810 | 5 | 240.05 |
| FX02 | T_SQL | True | True | 8 | 17269 | 0 | 36.25 |
| FX03 | T_SQL | True | True | 8 | 21632 | 0 | 30.03 |
| FX03 | T_GRAPH | True | True | 11 | 24053 | 4 | 73.06 |
| FX04 | T_GRAPH | True | True | 11 | 24005 | 8 | 148.52 |
| FX04 | T_SQL | True | True | 9 | 14078 | 0 | 39.64 |
| FX05 | T_SQL | True | True | 10 | 15295 | 0 | 70.66 |
| FX05 | T_GRAPH | True | True | 11 | 23815 | 31 | 164.13 |
| FX06 | T_GRAPH | True | True | 11 | 27315 | 10 | 225.36 |
| FX06 | T_SQL | True | True | 9 | 22484 | 0 | 99.48 |
| FX07 | T_SQL | True | True | 8 | 13552 | 0 | 79.86 |
| FX07 | T_GRAPH | True | True | 12 | 25998 | 4 | 214.15 |
| FX08 | T_GRAPH | True | True | 11 | 20916 | 4 | 97.29 |
| FX08 | T_SQL | True | True | 7 | 22352 | 0 | 47.04 |
| FX09 | T_SQL | True | True | 9 | 23868 | 0 | 40.84 |
| FX09 | T_GRAPH | False | False | 34 | 136666 | 16 | 240.25 |
| FX10 | T_GRAPH | False | False | 50 | 276723 | 12 | 240.23 |
| FX10 | T_SQL | True | False | 8 | 22932 | 0 | 131.30 |
| FX11 | T_SQL | True | False | 10 | 20340 | 0 | 97.47 |
| FX11 | T_GRAPH | False | False | 51 | 418967 | 5 | 240.22 |
| FX12 | T_GRAPH | True | True | 10 | 20931 | 11 | 172.14 |
| FX12 | T_SQL | True | True | 7 | 12699 | 0 | 40.44 |
| FX13 | T_SQL | True | True | 9 | 30413 | 0 | 89.90 |
| FX13 | T_GRAPH | False | False | 26 | 201259 | 10 | 240.25 |
| FX14 | T_GRAPH | True | False | 11 | 20320 | 7 | 159.52 |
| FX14 | T_SQL | True | False | 9 | 11776 | 0 | 92.50 |

This report intentionally contains no SQL-versus-graph frontier conclusion.
The sealed records retain SQL statement/row telemetry and graph-operation,
program, result-mode, and evidence telemetry for the preregistered analysis.
