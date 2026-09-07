# Condition B3 — automatic purpose-aware clause nomination (interim)

**MEASURED on finished replicates only.** R4/R5 were still running when this interim report was written. Do not treat 5-replicate means as final.

Same mechanical page segmentation in every replicate. Exact-span duplicates merged within a replicate. Precision scored only against frozen negative controls.

| Replicate | pages called | merged candidates | GOLD clause recall | negative-control rate |
|---|---|---|---|---|
| R1 | 173 | 1804 | **12/12 (1.00)** | 0.375 |
| R2 | 173 | 1773 | **12/12 (1.00)** | 0.375 |
| R3 | 173 | 1817 | **12/12 (1.00)** | 0.292 |
| R4 | unfinished | — | — | — |
| R5 | not started | — | — | — |

Finished-replicate mean gold recall: **1.00**.  
Finished-replicate mean negative-control rate: **0.35**.  
Candidates per page: ~10.

**OBSERVED.** Automatic nomination recovered every GOLD-S passage in every finished replicate. It also nominated about a third of the frozen negative controls and produced ~1,800 candidates per corpus. That is high recall with indiscriminate volume. Protocol forbids calling unmatched extra candidates false positives; the negative-control rate is the precision check.

**Why B4 is long:** protocol §11 runs the B1 obligation protocol on every B3 candidate. 1800 × 5 ≈ 9,000 isolated Composer calls. That is a protocol cost, not a machine hang.

Raw runs: `runs/b3/`.
