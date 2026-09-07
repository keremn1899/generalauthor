# Trigger analysis

Primary E1 excludes PROSE_ORIGINATING. Grain warning: trigger groups are not P3 obligations and not B3 nominations.

Mean E1 recall: **0.46** over 7 primary seams.
Mean trigger groups: **5.4**; mean instances: **955.2**.

## Special traces (hits / trials)

| gold_id | hits |
|---|---|
| S-FARM-TDS-STAGE | 3/5 |
| S-SOURCE-AUTHORITY | 3/5 |
| S-FARM-TRC-CONDITIONAL | 0/5 |
| S-AZTEC-WHEN-DISCHARGING | 0/5 |
| S-AZTEC-WET-SEASONAL | 0/5 |
| S-GCC-WET-FIRST-DISCHARGE | 0/5 |
| S-AZTEC-DELTA-BHC | 0/5 |
| S-FARM-REPORT-ONLY | 2/5 |
| S-AZTEC-REPORT-ONLY | 2/5 |
| S-GCC-REPORT-ONLY | 2/5 |
| S-FARM-CN-SCHEDULE | 0/5 |
| S-GCC-EVENT-DISCHARGE | 4/5 |

## E1 per primary seam per trial

Primary set: STRUCTURE_TRIGGERABLE + SOURCE_METADATA_TRIGGERABLE.

| seam | T1 | T2 | T3 | T4 | T5 |
|---|---|---|---|---|---|
| S-FARM-TDS-STAGE | Y | Y | n | Y | n |
| S-FARM-REPORT-ONLY | Y | Y | n | n | n |
| S-AZTEC-WHEN-DISCHARGING | n | n | n | n | n |
| S-AZTEC-REPORT-ONLY | Y | Y | n | n | n |
| S-GCC-EVENT-DISCHARGE | Y | Y | Y | Y | n |
| S-GCC-REPORT-ONLY | Y | Y | n | n | n |
| S-SOURCE-AUTHORITY | Y | n | Y | Y | n |

## E3 selectivity per trial

- T1: {'PURPOSE_RELEVANT': 8} purpose-relevant rate 1.0 irrelevant rate 0.0
- T2: {'PURPOSE_RELEVANT': 8} purpose-relevant rate 1.0 irrelevant rate 0.0
- T3: {'PURPOSE_RELEVANT': 6} purpose-relevant rate 1.0 irrelevant rate 0.0
- T4: {'PURPOSE_RELEVANT': 5} purpose-relevant rate 1.0 irrelevant rate 0.0
- T5: {} purpose-relevant rate None irrelevant rate None

## E5 distinction stability

```json
{
  "distinctions": {
    "facility_permit": {
      "n_true": 4,
      "stable": false
    },
    "measurements": {
      "n_true": 4,
      "stable": false
    },
    "parameters": {
      "n_true": 4,
      "stable": false
    },
    "periods": {
      "n_true": 4,
      "stable": false
    },
    "limit_rows": {
      "n_true": 4,
      "stable": false
    },
    "effective_intervals": {
      "n_true": 2,
      "stable": false
    },
    "candidate_links": {
      "n_true": 2,
      "stable": false
    },
    "nodi_or_codes": {
      "n_true": 4,
      "stable": false
    },
    "document_metadata": {
      "n_true": 3,
      "stable": false
    }
  },
  "identical_requirement_ids": false,
  "identical_relation_names": false,
  "n_distinct_requirement_id_sets": 5,
  "n_distinct_relation_name_sets": 5,
  "note": "Names may differ. Stability is scored on distinctions, not identifiers."
}
```

