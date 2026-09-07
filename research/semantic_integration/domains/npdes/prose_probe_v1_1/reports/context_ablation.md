# Probe v1.1 — context ablation (Farmington report-only, source-authority)

C2 reuses sealed v1 B1 R1–R5 (full local structural context). C1 is span-only, newly run.

Labels: **MEASURED**, **OBSERVED**, **HYPOTHESIS**.

| seam | C1 span-only FULL | C2 full context FULL (v1 B1) |
|---|---|---|
| S-FARM-REPORT-ONLY | 0.40 (PARTIAL_OBLIGATION, PARTIAL_OBLIGATION, FULL_OBLIGATION, PARTIAL_OBLIGATION, FULL_OBLIGATION) | 0.40 (FULL_OBLIGATION, PARTIAL_OBLIGATION, FULL_OBLIGATION, PARTIAL_OBLIGATION, PARTIAL_OBLIGATION) |
| S-SOURCE-AUTHORITY | 0.60 (FULL_OBLIGATION, MISS, MISS, FULL_OBLIGATION, FULL_OBLIGATION) | 0.60 (FULL_OBLIGATION, FULL_OBLIGATION, FULL_OBLIGATION, MISS, MISS) |

## OBSERVED

Do not generalize document-topology machinery from a tiny effect.

- Farmington report-only C2−C1: +0.00
- source-authority C2−C1: +0.00

**OBSERVED:** topology effect is small on this pair. Do not add document-topology machinery from it.

