# Semantic Proof / Risk-Coverage Benchmark v1

Mechanism study of bounded identity adjudication. Not Constructor v3.
A0 is imported from frozen Constructor v2 AXIS A. A1–A6 were not prompt-tuned after seeing results.

```
Strategy                   Risk   Coverage  SAME recall    Exact
a0_v2                     0.000      0.439        0.421    0.550
a1_single                 0.000      0.467        0.457    0.578
a2_critic                 0.000      0.422        0.414    0.533
a3_entailment             0.000      0.400        0.371    0.511
a4_proof_obligation       0.000      0.033        0.043    0.144
a5_pairwise               0.000      0.389        0.357    0.500
a6_multistep              0.000      0.300        0.271    0.411
```

Primary question: can any strategy materially increase SAME recall over v2 while retaining zero or near-zero unsupported closure?

## MEASURED
- **a0_v2**: unsupported=0 risk=0.0 coverage=0.4388888888888889 exact=0.55 SAME_recall=0.42142857142857143 under_closure=81 polarity=0 correct_downgraded=35 SAME_never_proposed=46 compared=180
- **a1_single**: unsupported=0 risk=0.0 coverage=0.4666666666666667 exact=0.5777777777777777 SAME_recall=0.45714285714285713 under_closure=38 polarity=0 correct_downgraded=0 SAME_never_proposed=38 compared=90
- **a2_critic**: unsupported=0 risk=0.0 coverage=0.4222222222222222 exact=0.5333333333333333 SAME_recall=0.4142857142857143 under_closure=42 polarity=0 correct_downgraded=2 SAME_never_proposed=40 compared=90
- **a3_entailment**: unsupported=0 risk=0.0 coverage=0.4 exact=0.5111111111111111 SAME_recall=0.37142857142857144 under_closure=44 polarity=0 correct_downgraded=1 SAME_never_proposed=43 compared=90
- **a4_proof_obligation**: unsupported=0 risk=0.0 coverage=0.03333333333333333 exact=0.14444444444444443 SAME_recall=0.04285714285714286 under_closure=77 polarity=0 correct_downgraded=31 SAME_never_proposed=46 compared=90
- **a5_pairwise**: unsupported=0 risk=0.0 coverage=0.3888888888888889 exact=0.5 SAME_recall=0.35714285714285715 under_closure=45 polarity=0 correct_downgraded=0 SAME_never_proposed=45 compared=90
- **a6_multistep**: unsupported=0 risk=0.0 coverage=0.3 exact=0.4111111111111111 SAME_recall=0.2714285714285714 under_closure=53 polarity=0 correct_downgraded=9 SAME_never_proposed=44 compared=90

## OBSERVED
- A0 SAME recall=0.42142857142857143 exact=0.55 risk=0.0.
- Lowest-risk strategy with highest SAME recall among A1–A6: ('a1_single', 0.45714285714285713, 0).

## HYPOTHESIS
- Positive semantic proof remains the binding constraint if SAME recall stays near A0 while risk stays near zero.
- If a strategy raises SAME recall by recovering cue-verifier downgrades without new unsupported closures, the v2 cue list was the bottleneck rather than the model.

Frozen at 2026-09-02T16:23:59.428348+00:00.

