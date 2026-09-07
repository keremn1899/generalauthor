# Probe v1.1 — B4-lite results

This is **not** Constructor v3.2. v1 measurements are sealed and unaltered.

Labels: **MEASURED**, **OBSERVED**, **HYPOTHESIS**.

## MEASURED subset

Evaluator-side classification used frozen source locators
(facility-qualified document + page + span overlap).
The model was never told GOLD vs NEGATIVE.
`OTHER` candidates were not processed.

- Selected candidates R1–R3: **132**
- R1: GOLD 36 + NEG 8 (OTHER 1760; locator gold-seam recall 1.00; missing none)
- R2: GOLD 29 + NEG 10 (OTHER 1734; locator gold-seam recall 0.92; missing ['S-FARM-TRC-CONDITIONAL'])
- R3: GOLD 39 + NEG 10 (OTHER 1768; locator gold-seam recall 0.92; missing ['S-FARM-TRC-CONDITIONAL'])

Sealed v1 B3 recall of 12/12 used a looser matcher that aliased `final_permit` across facilities.
That figure is **not changed**. Locator-true nomination is the v1.1 selection basis.

## Primary endpoints

- **E1 B4-lite FULL obligation recall:** 0.94
- **E2 gain over sealed B0 0.33:** 0.61
- **E3 negative rejection rate:** 0.39
- **E4 unsupported P5 closure count:** 0
- Sealed B1 oracle-passage FULL recall (not re-run): **0.90**

## Compression

- nominated candidates processed: 132
- generated obligations: 115
- NO_RELEVANT_OBLIGATION: 16
- FULL gold obligations (candidate-level): 77
- spurious negative obligations: 17
- semantic compression ratio: 0.87
- useful obligation yield: 0.67

## Negative-control scoring

{
  "NO_RELEVANT_OBLIGATION": 11,
  "PARTIAL_WEAK_OBLIGATION": 0,
  "FULL_SPURIOUS_OBLIGATION": 17,
  "PARSE_FAIL": 0
}

## Per-seam B4-lite stability

| seam | R1–R3 best | FULL | FULL+PARTIAL |
|---|---|---|---|
| S-FARM-TDS-STAGE | FULL_OBLIGATION, FULL_OBLIGATION, FULL_OBLIGATION | 3/3 | 1.00 |
| S-FARM-CN-SCHEDULE | FULL_OBLIGATION, FULL_OBLIGATION, FULL_OBLIGATION | 3/3 | 1.00 |
| S-FARM-TRC-CONDITIONAL | FULL_OBLIGATION, MISS, MISS | 1/3 | 0.33 |
| S-FARM-REPORT-ONLY | FULL_OBLIGATION, FULL_OBLIGATION, FULL_OBLIGATION | 3/3 | 1.00 |
| S-AZTEC-WHEN-DISCHARGING | FULL_OBLIGATION, FULL_OBLIGATION, FULL_OBLIGATION | 3/3 | 1.00 |
| S-AZTEC-REPORT-ONLY | FULL_OBLIGATION, FULL_OBLIGATION, FULL_OBLIGATION | 3/3 | 1.00 |
| S-AZTEC-WET-SEASONAL | FULL_OBLIGATION, FULL_OBLIGATION, FULL_OBLIGATION | 3/3 | 1.00 |
| S-AZTEC-DELTA-BHC | FULL_OBLIGATION, FULL_OBLIGATION, FULL_OBLIGATION | 3/3 | 1.00 |
| S-GCC-EVENT-DISCHARGE | FULL_OBLIGATION, FULL_OBLIGATION, FULL_OBLIGATION | 3/3 | 1.00 |
| S-GCC-REPORT-ONLY | FULL_OBLIGATION, FULL_OBLIGATION, FULL_OBLIGATION | 3/3 | 1.00 |
| S-GCC-WET-FIRST-DISCHARGE | FULL_OBLIGATION, FULL_OBLIGATION, FULL_OBLIGATION | 3/3 | 1.00 |
| S-SOURCE-AUTHORITY | FULL_OBLIGATION, FULL_OBLIGATION, FULL_OBLIGATION | 3/3 | 1.00 |

## Selective P5

- gold obligations judged: 93
- negative obligations judged: 17
- gold dispositions: {'ACCEPT': 18, 'REJECT': 4, 'UNRESOLVED': 71, 'NONE': 0}
- negative dispositions: {'ACCEPT': 1, 'REJECT': 1, 'UNRESOLVED': 15, 'NONE': 0}
- gold safe rate: 0.96
- unsupported closure: 0 (gold 0, negative 0)
- negative propagated ACCEPT: 1

## OBSERVED label: `ATTENTION_RECALL_HIGH_SELECTIVITY_WEAK`

E1 and E2 clear the funnel-recall bar. E3 does not. E4 unsupported closure is 0.
Compression 0.87 is not useful compression: 17/28 nominated negatives became FULL spurious obligations.
TRC locator-miss on R2/R3 is a B3 nomination gap under frozen locators, not a B4-lite formulation miss.

Thresholds are decision aids from the v1.1 protocol, not universal claims.

