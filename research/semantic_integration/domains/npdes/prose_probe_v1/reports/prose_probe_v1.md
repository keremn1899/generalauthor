# Prose Compilation Probe v1 — INTERIM report (B4 not run)

This is **not** Constructor v3.2. No constructor, kernel, P3, P5, admission, ABI, or prompt was modified.

This file is **INTERIM**. B3 R4/R5 and all of B4 were unfinished when it was written. Do not treat Endpoint 3 as measured.

Model: requested `composer-2.5`; finished agent records report `Composer 2.5`. Isolation leaks on finished runs: 0.

Labels: **MEASURED**, **OBSERVED**, **HYPOTHESIS**.

---

## Why B4 is ~20 hours

**MEASURED.** Each finished B3 replicate emitted ~1,800 merged `SemanticClauseCandidate`s. Protocol §11 requires the B1 obligation-formulation protocol on every candidate, then §12 bounded P5 only for gold-matching obligations. That is ~9,000 isolated Composer calls for B4 alone. Nomination is cheap relative to that; the length is the all-candidate obligation pass, not a stuck process.

---

## MEASURED endpoints (finished)

- Establishable GOLD-S seams: **12/12**
- B0 mean FULL P3 recall: **0.33** (per-trial 0.42 / 0.17 / 0.42 / 0.25 / 0.42)
- B1 PURPOSE_RELEVANT_OBLIGATION_RECALL: **0.90**
- B2 correct-or-legitimate-UNRESOLVED: **1.00**; unsupported closure **0.00**; UNRESOLVED 38/60
- B3 gold nomination recall (R1–R3): **1.00**; negative-control rate **0.29–0.38**
- B4 obligation recall: **unmeasured**
- B4−B0: **unmeasured**
- Context ablation C1/C2: **not run** (gated on B1; B1 is strong overall but Farmington report-only 2/5 and source-authority 3/5 would trigger it after B4)

## OBSERVED conclusion (interim)

Cannot return `PRE_ADJUDICATION_BOTTLENECK_SUPPORTED` until B4−B0 is measured.

Finished evidence already rejects:

- `PROPOSITIONIZATION_BOTTLENECK` (B1 = 0.90 ≥ 0.70)
- `ADJUDICATION_OR_EVIDENCE_BOTTLENECK` (B2 = 1.00 ≥ 0.70)

**HYPOTHESIS (not the sealed label):** H1 is directionally supported. The dominant miss is before P5: frozen P3 FULL recall 0.33; oracle passages yield 0.90; oracle P5 is safe; unfinished B3 already finds all gold passages. Remaining risks are indiscriminate nomination (negative-control ~0.35; ~1800 candidates) and whether B4 turns those passages into FULL obligations without extra unsupported closure.

Interim stage attribution: `MIXED_PROSE_COMPILATION_FAILURE` only if one insists on a sealed label before B4. Scientifically the finished stages localize to **P3 / clause attention**, not kernel, not P5 safety.

---

## Required answers

1. **How many GOLD-S seams were genuinely establishable from participant evidence?**  
   **MEASURED: 12/12.** None required extra-corpus legends (including NODI 9/C). See `evidence_sufficiency.md`.

2. **Where did each establishable seam first disappear in frozen v3.1.1?**  
   **MEASURED** in `retrospective_funnel.md`. B0 FULL misses 5/5: staged TDS, source-authority, first-discharge WET, WET seasonal, Delta-BHC, cyanide schedule, TRC-conditional (those last two often PARTIAL). Report-only often FULL. Earliest failure for the persistent FULL misses is **P3 obligation formation**. Evidence was in the participant PDFs and, for staged TDS, also in `permit_limits.csv` date bounds.

3. **Given the exact relevant prose, how often could the model formulate the correct bounded semantic obligation?**  
   **MEASURED B1 = 0.90.** 9/12 seams 5/5 FULL. Aztec report-only 4/5. Source-authority 3/5 (7/10 after extension). Farmington report-only 2/5 (5/10 after extension).

4. **Which clauses remained difficult even under oracle passage nomination?**  
   **OBSERVED:** Farmington report-only (2/5, then 5/10) and source-authority (3/5, then 7/10). Staged TDS was **not** difficult under oracle passage (5/5).

5. **Given an oracle obligation, could frozen P5 adjudicate safely?**  
   **MEASURED: yes.** 60/60 correct or legitimate UNRESOLVED. 0 unsupported closures.

6. **How often was UNRESOLVED the correct/safe result?**  
   **MEASURED: 38/60 (0.63)** of B2 first-5 dispositions were UNRESOLVED, all counted safe. Gold itself treats TRC month-level required/not-required and Aztec WET outstanding-test status as legitimately UNRESOLVED without operational logs. Staged TDS was UNRESOLVED 5/5 rather than closing *11 for post-2024-12-01 months — conservative under-closure, not unsafe closure.

7. **Were failures caused by missing vocabulary/contracts rather than judgment?**  
   **OBSERVED: no, not as the primary B0 miss.** Staged TDS is representable via dated limit rows / `applicable_limit_selection` (structured limits already split 497/27664 through 2024-11-30 and 449/24992 from 2024-12-01). Source-authority has document-inventory analogues in some trials, not an operative-vs-rationale contract. B2 used labeled oracle contracts; remaining B2 UNRESOLVED is judgment/evidence conservatism, not missing kernel primitives. T1 P3 explicitly recorded that permit PDFs were not ingested and obligations came from structured DMR comments.

8. **Could automatic purpose-aware clause nomination find the gold passages?**  
   **MEASURED on R1–R3: yes, 12/12 in every finished replicate.** R4/R5 unfinished.

9. **How often did it nominate frozen negative controls?**  
   **MEASURED R1–R3: 0.375, 0.375, 0.292.** About one third of frozen negatives were nominated. Volume is ~1,800 candidates/replicate. Precision is only defined against those negatives.

10. **Did automatic nomination + obligation formation materially outperform frozen P3?**  
    **Unmeasured.** B4 not run. B3 already finds the passages P3 missed; whether they become FULL obligations is Endpoint 3.

11. **Did increased prose recall create additional unsupported closure?**  
    **Unmeasured for B4.** B2 unsupported closure = 0. B3 does not adjudicate.

12. **Was local document structure materially useful?**  
    **Not run.** C1/C2 ablation is gated on weak/unstable B1. Overall B1 is 0.90; Farmington report-only and source-authority were the unstable seams.

13. **Staged TDS primary failure class:**  
    **Propositionization / P3 salience**, not missing evidence, not kernel representation, not P5. Evidence present (PDF *10/*11 and structured begin/end dates). P1 can represent dated limit rows. B0 FULL 0/5. B1 5/5 when the passage is supplied. B2 5/5 safe UNRESOLVED (under-closure of which regime applies in FY2025). T1 P3 notes: PDFs not ingested; DMR comments state TDS geometric-mean Report language, not *10/*11, even though the CSV already stages the numbers.

14. **Source-authority primary failure class:**  
    **Propositionization / P3 omission.** Fact sheets/SOBs were in the participant workspace. B0 MISS 5/5. B1 3/5 FULL (7/10 extended). B2 5/5 legitimate UNRESOLVED. Document paths in some trials are inventory, not operative-vs-rationale.

15. **Which conclusion is supported (finished stages)?**  
    Sealed pre-registered label **cannot be issued** without B4. Finished stages: **not** propositionization bottleneck, **not** adjudication/evidence bottleneck. H1 (pre-adjudication) is **directionally supported**. B3 recall is strong; B3 precision vs negatives is weak. Interim: do not implement a production pass; a follow-up should measure B4 on **gold-nominated clauses only**, not 9,000 candidates.

16. **Does the evidence justify implementing a small experimental purpose-aware prose-nomination pass?**  
    **Not yet as a compiler change.** Finished evidence justifies **keeping nomination as an experimental probe**, not adopting it into Constructor v3.1.1. Negative-control rate ~0.35 and ~1,800 candidates/page-corpus are not a small pass.

17. **If yes, MINIMUM mechanism; if no, what not to build.**  
    **Do not implement into P0–P8.** MINIMUM follow-up justified by finished evidence: score B4 only on B3 candidates that match gold locators (and the frozen negatives), instead of every candidate. That measures Endpoint 3 without 9,000 calls. The mechanism, if later adopted, must remain a replaceable attention pass: source-located candidates only; no World facts; no P5 bypass; no closed-world negation.

STOP relative to constructor repair. Do not repair P3, P5, Constructor v3.1.1, or the kernel from this interim file.
