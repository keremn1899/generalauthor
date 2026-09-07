# Condition B2 — oracle obligation → bounded judgment

**MEASURED.** Frozen P5 protocol. Oracle obligation without the correct disposition. Labeled oracle relation contract (not persisted to World). 5 replicates × 12 seams.

Correct or legitimate UNRESOLVED = **1.00** (60/60).  
Unsupported closure rate = **0.00**.  
Dispositions among first-5: ACCEPT 22, REJECT 0, UNRESOLVED 38.

| Seam | safe | unresolved | unsupported | first-5 dispositions |
|---|---|---|---|---|
| `S-FARM-TDS-STAGE` | 5/5 | 5/5 | 0/5 | UNRESOLVED ×5 |
| `S-FARM-CN-SCHEDULE` | 5/5 | 0/5 | 0/5 | ACCEPT ×5 |
| `S-FARM-TRC-CONDITIONAL` | 5/5 | 0/5 | 0/5 | ACCEPT ×5 |
| `S-FARM-REPORT-ONLY` | 5/5 | 5/5 | 0/5 | UNRESOLVED ×5 |
| `S-AZTEC-WHEN-DISCHARGING` | 5/5 | 0/5 | 0/5 | ACCEPT ×5 |
| `S-AZTEC-REPORT-ONLY` | 5/5 | 5/5 | 0/5 | UNRESOLVED ×5 |
| `S-AZTEC-WET-SEASONAL` | 5/5 | 5/5 | 0/5 | UNRESOLVED ×5 |
| `S-AZTEC-DELTA-BHC` | 5/5 | 2/5 | 0/5 | ACCEPT ×3, UNRESOLVED ×2 |
| `S-GCC-EVENT-DISCHARGE` | 5/5 | 5/5 | 0/5 | UNRESOLVED ×5 |
| `S-GCC-REPORT-ONLY` | 5/5 | 5/5 | 0/5 | UNRESOLVED ×5 |
| `S-GCC-WET-FIRST-DISCHARGE` | 5/5 | 1/5 | 0/5 | ACCEPT ×4, UNRESOLVED ×1 |
| `S-SOURCE-AUTHORITY` | 5/5 | 5/5 | 0/5 | UNRESOLVED ×5 |

**OBSERVED.** Frozen P5 did not make unsupported closures on oracle obligations. It often preferred UNRESOLVED for staged TDS, report-only, WET seasonal, GCC event/report-only, and source-authority — which the gold cards treat as legitimate when operational completion/NODI legends are absent from the packet. It did close cyanide schedule, TRC-conditional rule, when-discharging, and usually first-discharge WET / Delta-BHC.

Raw runs: `runs/b2/`.
