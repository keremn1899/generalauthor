# Frozen frontier pilot results

Campaign validity: valid.

- T_SQL: 16/16 exact; 16/16 valid
- T_GRAPH: 16/16 exact; 16/16 valid
- U_GRAPH: 16/16 exact; 16/16 valid

| Case | Arm | Valid execution | Exact correct | Wall seconds | Tool calls |
| --- | --- | --- | --- | --- | --- |
| order-platform-verification-control | T_SQL | True | True | 29.42 | 15 |
| order-platform-verification-control | T_GRAPH | True | True | 96.48 | 19 |
| order-platform-verification-control | U_GRAPH | True | True | 79.46 | 18 |
| order-platform-production-impact | T_SQL | True | True | 26.42 | 14 |
| order-platform-production-impact | T_GRAPH | True | True | 77.85 | 19 |
| order-platform-production-impact | U_GRAPH | True | True | 63.04 | 17 |
| order-platform-cutover-boundary-control | T_SQL | True | True | 26.43 | 15 |
| order-platform-cutover-boundary-control | T_GRAPH | True | True | 67.08 | 19 |
| order-platform-cutover-boundary-control | U_GRAPH | True | True | 65.08 | 18 |
| order-platform-cutover-readiness | T_SQL | True | True | 28.83 | 12 |
| order-platform-cutover-readiness | T_GRAPH | True | True | 54.46 | 18 |
| order-platform-cutover-readiness | U_GRAPH | True | True | 64.07 | 17 |
| identity-platform-verification-control | T_SQL | True | True | 22.23 | 17 |
| identity-platform-verification-control | T_GRAPH | True | True | 88.12 | 19 |
| identity-platform-verification-control | U_GRAPH | True | True | 80.11 | 16 |
| identity-platform-production-impact | T_SQL | True | True | 31.85 | 18 |
| identity-platform-production-impact | T_GRAPH | True | True | 65.09 | 19 |
| identity-platform-production-impact | U_GRAPH | True | True | 66.89 | 17 |
| identity-platform-cutover-boundary-control | T_SQL | True | True | 33.25 | 13 |
| identity-platform-cutover-boundary-control | T_GRAPH | True | True | 49.07 | 18 |
| identity-platform-cutover-boundary-control | U_GRAPH | True | True | 85.52 | 20 |
| identity-platform-cutover-readiness | T_SQL | True | True | 22.23 | 13 |
| identity-platform-cutover-readiness | T_GRAPH | True | True | 54.08 | 17 |
| identity-platform-cutover-readiness | U_GRAPH | True | True | 47.45 | 20 |
| catalogue-platform-verification-control | T_SQL | True | True | 23.43 | 16 |
| catalogue-platform-verification-control | T_GRAPH | True | True | 65.87 | 18 |
| catalogue-platform-verification-control | U_GRAPH | True | True | 84.9 | 18 |
| catalogue-platform-production-impact | T_SQL | True | True | 21.43 | 13 |
| catalogue-platform-production-impact | T_GRAPH | True | True | 70.08 | 18 |
| catalogue-platform-production-impact | U_GRAPH | True | True | 76.89 | 19 |
| catalogue-platform-cutover-boundary-control | T_SQL | True | True | 29.24 | 15 |
| catalogue-platform-cutover-boundary-control | T_GRAPH | True | True | 54.06 | 18 |
| catalogue-platform-cutover-boundary-control | U_GRAPH | True | True | 83.91 | 18 |
| catalogue-platform-cutover-readiness | T_SQL | True | True | 26.23 | 16 |
| catalogue-platform-cutover-readiness | T_GRAPH | True | True | 56.27 | 18 |
| catalogue-platform-cutover-readiness | U_GRAPH | True | True | 83.3 | 20 |
| telemetry-platform-verification-control | T_SQL | True | True | 21.42 | 16 |
| telemetry-platform-verification-control | T_GRAPH | True | True | 132.96 | 19 |
| telemetry-platform-verification-control | U_GRAPH | True | True | 111.13 | 16 |
| telemetry-platform-production-impact | T_SQL | True | True | 23.03 | 16 |
| telemetry-platform-production-impact | T_GRAPH | True | True | 69.89 | 19 |
| telemetry-platform-production-impact | U_GRAPH | True | True | 66.69 | 19 |
| telemetry-platform-cutover-boundary-control | T_SQL | True | True | 23.23 | 18 |
| telemetry-platform-cutover-boundary-control | T_GRAPH | True | True | 56.48 | 21 |
| telemetry-platform-cutover-boundary-control | U_GRAPH | True | True | 65.49 | 17 |
| telemetry-platform-cutover-readiness | T_SQL | True | True | 24.83 | 13 |
| telemetry-platform-cutover-readiness | T_GRAPH | True | True | 65.89 | 19 |
| telemetry-platform-cutover-readiness | U_GRAPH | True | True | 62.69 | 18 |

No causal interpretation is made here; these are the first required execution outcomes.
