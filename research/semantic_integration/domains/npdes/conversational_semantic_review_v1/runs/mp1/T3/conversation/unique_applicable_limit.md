For Federal FY2025 we're trying to compare each reported discharge measurement against the numeric limit that actually governs it. The structured data gives us 824 measurements in that window, and the draft links each one to exactly one permit-limit row—824 pairs total, with no case where a single measurement matched two different limits.

The pairing works by taking the limit identifiers already present on each DMR row (LIMIT_VALUE_ID and LIMIT_SET_SCHEDULE_ID) and looking up the matching row in permit_limits.csv. Measurements are filtered to those whose monitoring period end falls between 2024-10-01 and 2025-09-30. The draft then requires that each measurement have exactly one such pair before it will treat limit comparison as well-defined.

On this dataset that rule is satisfied: one limit per measurement, no gaps. So mechanically the draft does not currently flag a uniqueness problem here.

What I'm less sure about—and what I'd want your read on—is whether that one-to-one result is always the right conceptual answer, or just what happens to fall out of this particular export. Two situations worry me.

First, permits sometimes have overlapping or staged limit intervals—an old limit ending and a new one beginning, or parallel schedule rows whose effective dates overlap. Should those stay as separate limit identities even when only one applies to a given monitoring period, or should the analysis ever collapse them into a single governing limit?

Second, the same underlying limit can show up more than once in the catalog with different LIMIT_VALUE_ID or schedule keys. If that happened for one measurement, should we count that as multiple applicable limits (a real ambiguity) or as restatements of one limit that should not break uniqueness?

If either of those comes up in practice, Purpose A—deciding whether a measurement exceeds the applicable enforceable limit—would need a rule for picking or merging candidates. Right now the draft assumes the join already gives the answer and doesn't encode a tie-break. Does that match how you'd read these permits, or is there a domain rule we're missing?