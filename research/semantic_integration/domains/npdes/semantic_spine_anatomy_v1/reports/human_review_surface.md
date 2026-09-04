# Human / ontology-engineer review surface

Not an interactive repair experiment. Compact questions a human would need to certify a draft spine. Raw Python is out of scope unless a fixture-sensitive match must be inspected.

## Shared review packet (all trials)

Declared purposes: A applicable FY2025 numeric limits; B monitoring obligations; C missing-evidence classification.

Stable semantic spine to certify:

1. Is FY2025 ∩ measurement-period ∩ limit-effective-interval the right applicability geometry?
2. Is uniqueness of applicable limit the right cardinality (ONE per measurement), or can staged/catalog variants be simultaneous?
3. What does each distinct NODI code mean for missing-evidence / requiredness?
4. What does nonempty DMR comment text do to monitoring/limit applicability, including WHEN DISCHARGING?
5. Are empty numeric limits report-only, or is another classification required?
6. Does document inventory without text correctly leave narrative authority unresolved?

Estimate: **6 genuinely consequential questions** for the shared core, not 2,972 hole occurrences.

## T1

- declared purpose: A/B/C as in participant `visible_*.md`
- stable spine schemas: 14 normalized requirements, 9 relation schemas
- trial-specific extras: `materializable_monitoring`
- unresolved obligations (candidate): 30
- hole occurrences (do not review one-by-one): 3414
- fixture-sensitive matches: WHEN DISCHARGING literal (hardcode-flagged)

## T2

- declared purpose: A/B/C as in participant `visible_*.md`
- stable spine schemas: 11 normalized requirements, 12 relation schemas
- trial-specific extras: none
- unresolved obligations (candidate): 33
- hole occurrences (do not review one-by-one): 1891
- fixture-sensitive matches: generic nonempty-comment detection

## T3

- declared purpose: A/B/C as in participant `visible_*.md`
- stable spine schemas: 16 normalized requirements, 6 relation schemas
- trial-specific extras: `interpret_sample_type`, `interpret_unit`, `interpret_value_type`, `materializable_documents`, `pass_fail_semantics`
- unresolved obligations (candidate): 63
- hole occurrences (do not review one-by-one): 6116
- fixture-sensitive matches: generic nonempty-comment detection

## T4

- declared purpose: A/B/C as in participant `visible_*.md`
- stable spine schemas: 13 normalized requirements, 9 relation schemas
- trial-specific extras: `report_only_gap`
- unresolved obligations (candidate): 25
- hole occurrences (do not review one-by-one): 2904
- fixture-sensitive matches: generic nonempty-comment detection

## T5

- declared purpose: A/B/C as in participant `visible_*.md`
- stable spine schemas: 16 normalized requirements, 7 relation schemas
- trial-specific extras: `aggregated_reporting`, `interpret_statistical_base`, `materializable_monitoring`, `pass_fail_semantics`
- unresolved obligations (candidate): 23
- hole occurrences (do not review one-by-one): 535
- fixture-sensitive matches: WHEN DISCHARGING literal (hardcode-flagged)

## Uncertified modeling choices (do not auto-promote)

- T1 uniqueness on catalog variants vs T5 uniqueness on measurement–limit pairs
- T3 12-month seasonal flags vs T5 omitting seasonal GOLD (primary E1 did not require it)
- T1/T5 literal WHEN DISCHARGING vs T2–T4 generic comments
- known-empty vs known-token lists on `require_interpreted` (T5 lists `<=`, `ENF`, month codes)

## HYPOTHESIS

Conversational certification should present the 6 core questions plus a short extras list, never raw Python or per-row holes.
