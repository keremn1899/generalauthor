Many permit limits in this dataset carry free-text comments in DMR_COMMENT_TEXT. Out of 105 permit-limit rows, 69 have nonempty comments. The draft does not translate any of those comments into monitoring rules or comparison logic—it treats nonempty comment text as something that still needs interpretation.

Three patterns show up often enough that the draft also names them as separate unresolved items rather than lumping them into a generic "unread comment" bucket:

**"WHEN DISCHARGING"** appears on 17 limits. My read of the phrase in isolation is that monitoring or reporting might only apply when discharge actually occurred—but the structured CSVs don't tell us whether discharge happened in any given period, so the draft stops there and flags these as discharge-conditioned dependencies it cannot resolve from tables alone.

**Geometric mean / TDS language** appears on 40 limits—for example comments like "TOTAL DISSOLVED SOLIDS (TDS) MEASURED AT OUTFALL 001. REPORT THE GEOMETRIC MEAN VALUE OF THE WEEKLY VALUES." That sounds like an aggregation or reporting instruction rather than a simple single-sample concentration limit, but the draft does not decide how that affects whether a given week's row is in or out of compliance.

**Pass/fail reporting** appears on 12 limits—comments along the lines of "(PASS = 0 FAIL = 1) REPORT PASS AS '0' OR REPORT FAIL AS '1' IN CONCENTRATION..." which suggests compliance may be expressed as a binary outcome rather than an ordinary numeric comparison.

I'm not asking you to validate the draft's decision to leave all 69 comments uninterpreted—that's already what it does mechanically. What I need from you is substance: for the "WHEN DISCHARGING" limits, does that phrase mean monitoring was required only if discharge occurred, or does it mean something else in NPDES practice? And are the geometric-mean and pass/fail families genuinely different questions from the discharge-conditioned case, or would you handle them as variations of one "comment overrides the default limit logic" problem?

Concrete examples from the data if it helps jog memory:
- `WHEN DISCHARGING.`
- `TOTAL DISSOLVED SOLIDS (TDS) MEASURED AT OUTFALL 001. REPORT THE GEOMETRIC MEAN VALUE OF THE WEEKLY VALUES.`
- `(PASS = 0 FAIL = 1) REPORT PASS AS '0' OR REPORT FAIL AS '1' IN CONCENTRATION ...`