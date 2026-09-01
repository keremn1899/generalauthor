# Frontier-extension execution report — no frontier interpretation

| Check | Value |
| --- | --- |
| Campaign validity | `False` |
| Model/environment constancy | `True` |
| Completion | `11/28` |
| Declared/reported model | `Composer 2.5` |
| Abort reason | `quota/rate-limit dependency failure in FX06/T_GRAPH` |

| Case | Arm | Valid execution | Exact named-set correct | Interactions | Model-visible bytes | Participant errors | Wall seconds |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| FX01 | T_SQL | True | True | 9 | 19152 | 0 | 44.83 |
| FX01 | T_GRAPH | True | True | 10 | 22223 | 7 | 104.88 |
| FX02 | T_GRAPH | True | True | 10 | 23231 | 6 | 94.67 |
| FX02 | T_SQL | True | True | 8 | 17274 | 0 | 52.84 |
| FX03 | T_SQL | True | True | 10 | 19305 | 0 | 57.44 |
| FX03 | T_GRAPH | True | False | 11 | 22164 | 8 | 156.52 |
| FX04 | T_GRAPH | True | True | 11 | 22095 | 10 | 103.48 |
| FX04 | T_SQL | True | True | 9 | 13964 | 0 | 44.23 |
| FX05 | T_SQL | True | True | 9 | 21402 | 0 | 46.24 |
| FX05 | T_GRAPH | True | True | 11 | 18703 | 6 | 208.77 |
| FX06 | T_GRAPH | True | True | 10 | 23063 | 7 | 118.29 |

This report intentionally contains no SQL-versus-graph frontier conclusion.
The sealed records retain SQL statement/row telemetry and graph-operation,
program, result-mode, and evidence telemetry for the preregistered analysis.
