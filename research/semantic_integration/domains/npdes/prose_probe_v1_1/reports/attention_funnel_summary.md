# Probe v1.1 — attention funnel summary

This is **not** Constructor v3.2. No constructor, kernel, P3, P4, P5, admission, ABI, normalizer, or projection was modified.

v1 sealed: B0 FULL **0.33**, B1 **0.90**, B2 safe **1.00** / unsupported **0**, B3 R1–R3 gold recall **12/12** (loose matcher).

Model: requested `composer-2.5`. Label: **`ATTENTION_RECALL_HIGH_SELECTIVITY_WEAK`**.

Labels: **MEASURED**, **OBSERVED**, **HYPOTHESIS**.

## MEASURED endpoints

- E1 B4-lite FULL recall: **0.94**
- E2 B4-lite − B0: **0.61**
- E3 negative rejection: **0.39**
- E4 unsupported P5 closure: **0** (negative propagated ACCEPT 1)
- compression ratio: 0.87
- useful yield: 0.67

## Staged TDS

- B0 P3 FULL recall: 0.0 grades ['PARTIAL_OBLIGATION', 'PARTIAL_OBLIGATION', 'PARTIAL_OBLIGATION', 'MISS', 'PARTIAL_OBLIGATION']
- B3 locator nominations per R1–R3: [5, 5, 5]
- B4-lite best: {'grades': ['FULL_OBLIGATION', 'FULL_OBLIGATION', 'FULL_OBLIGATION'], 'full_over_3': '3/3', 'full_recall': 1.0, 'full_or_partial_recall': 1.0}
- P5 dispositions: ['UNRESOLVED', 'UNRESOLVED', 'UNRESOLVED', 'UNRESOLVED', 'UNRESOLVED', 'UNRESOLVED', 'UNRESOLVED', 'UNRESOLVED', 'UNRESOLVED', 'REJECT', 'UNRESOLVED', 'UNRESOLVED', 'UNRESOLVED']
- P5 unsupported: [False, False, False, False, False, False, False, False, False, False, False, False, False]

Safe UNRESOLVED is not a discovery failure. Discovery and semantic closure are separate.

## Source authority

- B0 P3 FULL recall: 0.0 grades ['MISS', 'MISS', 'MISS', 'MISS', 'MISS']
- B3 locator nominations per R1–R3: [6, 3, 5]
- B4-lite best: {'grades': ['FULL_OBLIGATION', 'FULL_OBLIGATION', 'FULL_OBLIGATION'], 'full_over_3': '3/3', 'full_recall': 1.0, 'full_or_partial_recall': 1.0}
- P5 dispositions: ['UNRESOLVED', 'UNRESOLVED', 'UNRESOLVED', 'UNRESOLVED', 'UNRESOLVED', 'UNRESOLVED', 'UNRESOLVED']
- C1 FULL: 0.6
- C2 FULL (v1 B1): 0.6

**OBSERVED source-authority remaining difficulty:** not attention (locator-nominated every replicate) and not automatic propositionization (B4-lite 3/3 FULL). C1 = C2 = 0.60, so document topology did not materially help. Frozen B2 was UNRESOLVED 5/5. Remaining is **judgment conservatism / evidence**, not an authority hierarchy.

**OBSERVED P5 caveat:** gold_safe_rate vs oracle expected_b2 is 0.96. Four gold P5 rows were grounded but not in the oracle safe set (three Aztec report-only ACCEPT; one staged-TDS REJECT). Agent-formulated obligation polarity need not match the oracle relation. E4 uses ungrounded ACCEPT/REJECT = 0. One negative-control P5 ACCEPT (Aztec oil-film narrative) was grounded; 15/17 negative obligations stayed UNRESOLVED.

## Required answers

1. Did B3 nomination → B4 obligation formation materially outperform frozen P3? **YES** (gain 0.61).
2. B4-lite FULL obligation recall: **0.94**
3. Absolute improvement over B0: **0.61**
4. Nominated negative controls rejected as NO_RELEVANT_OBLIGATION: **0.39**
5. Spurious obligations from negative controls: **17** (rate 0.61)
6. Semantic compression ratio: **0.87**
7. Negative-control obligation unsupported P5 closure: **0**; propagated ACCEPT **1**
8. Overall unsupported closure zero/negligible? **YES** (count 0)
9. Staged TDS recovered automatically through nomination → obligation? **YES** (3/3). P5 dispositions ['UNRESOLVED', 'UNRESOLVED', 'UNRESOLVED', 'UNRESOLVED', 'UNRESOLVED', 'UNRESOLVED', 'UNRESOLVED', 'UNRESOLVED', 'UNRESOLVED', 'REJECT', 'UNRESOLVED', 'UNRESOLVED', 'UNRESOLVED'].
10. Source-authority improved with structural context? **C1 0.60 vs C2 0.60**

11. Remaining major bottleneck: **selectivity**. Attention recovered gold locators; B4-lite formulated FULL obligations (0.94, above sealed B1 0.90 on this subset). Adjudication did not produce ungrounded closure. Negative rejection 0.39 < 0.70; compression 0.87 because most nominated negatives still became obligations.
12. Supported result: **`ATTENTION_RECALL_HIGH_SELECTIVITY_WEAK`**
13. Implement an EXPERIMENTAL prose-attention pass? **NO.** Recall is high; selectivity is not. The protocol requires negative rejection ≥ 0.70 for ATTENTION_FUNNEL_SUPPORTED.
14. Minimum mechanism if later justified: purpose + source prose → broad source-located clause nomination → bounded relevance / obligation formulation → existing P5 → existing admission. Not justified now. Do not implement.

**OBSERVED remaining bottleneck:** **selectivity** (negative rejection below 0.70) with high gold obligation recall.

## Stop

No Constructor change. No P3/P5 repair. No NPDES A/B/C rerun. No World repair. No RAW-vs-WORLD. No fifth domain.

