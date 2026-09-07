# Clarification needed: what is wrong about "one governing limit per measurement"?

You said the draft is wrong to treat each FY2025 measurement as having exactly one governing applicable numeric limit. That rejection is clear, but it could point in very different directions—and those directions produce very different results on this fixture.

## Where the disagreement sits

The draft currently builds **824** measurement–limit pairs (one per FY2025 measurement) by following the limit identity already carried on each DMR row (`LIMIT_VALUE_ID` and `LIMIT_SET_SCHEDULE_ID`). It then treats the "exactly one applicable limit per measurement" rule as **satisfied** on this data.

A separate issue summary describes pairing differently—as if each measurement were matched against all permit limit rows by permit, outfall, parameter, and whether the monitoring period falls inside each limit's effective dates. Under that catalog-style rule, most measurements would match **multiple** permit limit rows (overlapping or staged intervals), not one.

So the open question is not whether you disagree with the draft's conclusion—you already said you do—but **which part** you are rejecting.

## What would change depending on the answer

**If the pairing rule should be catalog-style matching** (enumerate every permit limit row whose interval covers the measurement's monitoring period, regardless of what the DMR row names):

- Measurement–limit pairs rise from **824 to 4,076** (roughly five per measurement on average).
- Numeric comparison candidates rise from **342 to 1,388**.
- The "exactly one limit per measurement" rule would be **violated on 704 measurements**, surfacing as new unresolved items rather than staying satisfied.

**If the pairing rule is fine but the "exactly one governing limit" requirement is wrong** (multiple limits may apply, or we should not commit to a count yet):

- Pair counts stay at **824**; numeric comparison candidates stay at **342**.
- Only the uniqueness policy changes: one new unresolved item appears where the draft previously reported satisfaction.

**If the construction logic is already correct and the error was in how the issue was described** (the DMR-named limit is the applicable one; the catalog-match story was a misread):

- Nothing material changes: **824** pairs, **342** comparisons, uniqueness remains satisfied as today.

These are not small rounding differences. They change how many limits we think govern each discharge measurement and whether the data currently passes or fails the one-limit test.

## What would help

In your own words: when you said the draft is wrong about one governing limit per measurement, what should we do differently?

For example—should we pair measurements to limits a different way? Should we stop requiring exactly one limit even if pairing stays as-is? Or was the problem that we described the existing pairing incorrectly, and the real issue lies elsewhere?

Any concrete example (a measurement that should pair to zero, one, or several limits—and why) would pin this down. A completely different framing is welcome too.
