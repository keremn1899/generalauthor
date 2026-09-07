You confirmed that a single FY2025 measurement can have more than one applicable discharge limit. We should stop treating “exactly one governing limit per measurement” as a policy for this analysis. That part is clear.

What is still open is how we decide which limit rows belong to each measurement.

The current draft links each measurement to the specific limit identifiers carried on that DMR row — the limit value and schedule IDs in the reporting data. On this dataset that yields **824** measurement–limit pairs, of which **342** have both a reported value and a numeric limit suitable for comparison.

Another reading of “multiple limits can apply” is that we should enumerate **every** permit limit row whose effective dates overlap the monitoring period for the same permit, outfall, and parameter — not just the limit the DMR row points at. On this dataset that would yield about **4,076** pairs and about **1,388** numeric comparison candidates — roughly five times as many relationships.

These are not the same analysis. They change how many measurement–limit relationships exist and how many numeric comparisons the construction considers, even though both versions drop the one-limit rule and leave the same eight unresolved issue groups (535 unresolved instances total).

Which picture matches what you mean? If neither does, please describe in your own words how we should decide which limits apply to a given measurement.
