For Federal FY2025, we are trying to decide which enforceable numeric discharge limit applies to each reported measurement — so we can later ask whether the reported value exceeds that limit.

Right now we are pairing each FY2025 measurement with a permit limit row by matching the permit, outfall, parameter, and the limit identifiers already carried on the DMR row, and we only keep the pair when the monitoring period end date falls inside that limit row’s begin/end dates. On this dataset that produces 824 measurement–limit pairs, one per measurement. We have been working from the assumption that each measurement should have exactly one governing numeric limit for that purpose — not zero, not two or more.

That assumption is not creating a problem on this particular fixture: every FY2025 measurement lands with a single pair. But we are not confident the assumption is generally right, and we would like your read before we treat it as settled.

The two places we are unsure:

**Overlapping or staged limits.** Sometimes the permit limit catalog has more than one row for the same permit/outfall/parameter with date ranges that overlap, or with one limit ending and another beginning during the year. Should those be understood as separate applicable limits that can both govern the same measurement period, or is there ordinarily one limit that actually governs and the others are superseded, historical, or otherwise not in play?

**Duplicate-looking catalog rows.** Sometimes what looks like the same limit may appear more than once in the structured data — restated rows, schedule variants, or other catalog artifacts. When that happens, should we treat those as genuinely multiple applicable limits, or as one limit represented more than once?

In short: for a given reported measurement in a given monitoring period, is “exactly one applicable numeric limit” the right rule? If not, what should we do instead — and are the overlapping-interval and duplicate-row cases the right things to worry about, or is there a different distinction we are missing?
