Many permit limit rows carry free-text in `DMR_COMMENT_TEXT`. On this dataset 69 limits have nonempty comments. The draft stores the text but does not turn it into a definite monitoring rule. It also flags three recurring patterns as explicitly unresolved:

**"WHEN DISCHARGING."** — 17 limit rows (for example, backwash-water limits on permit NM0028762). The draft notes that structured data here don't tell us whether discharge actually occurred in a given monitoring period, so it won't decide if monitoring was required or not required based on this phrase alone.

**Geometric mean / TDS language** — 40 rows with comments like: "TOTAL DISSOLVED SOLIDS (TDS) MEASURED AT OUTFALL 001. REPORT THE GEOMETRIC MEAN VALUE OF THE WEEKLY VALUES." The draft doesn't know how that instruction changes what a single weekly DMR row should be compared against.

**Pass/fail reporting** — 12 rows with comments along the lines of "(PASS = 0 FAIL = 1) REPORT PASS AS '0' OR REPORT FAIL AS '1' IN CONCENTRATION ..." The draft treats these as a different reporting channel than ordinary numeric concentration comparison.

For monitoring obligations (Purpose B), the central question on the "when discharging" limits is: does that phrase mean monitoring is required only when there was a discharge, or does it mean something else—reporting format, limit applicability, something that can't be resolved without permit narrative we don't have in structured form?

I'd also like to know whether you see these three comment families as genuinely different questions, or whether one general rule ("read the permit comment") would cover them.

Please correct any of my readings of what the comments are trying to say. I am not asking you to confirm the draft's mechanical choice to leave comments uninterpreted—that is already what it does. I'm asking what the comments *mean* for whether monitoring was required and how results should be evaluated.
