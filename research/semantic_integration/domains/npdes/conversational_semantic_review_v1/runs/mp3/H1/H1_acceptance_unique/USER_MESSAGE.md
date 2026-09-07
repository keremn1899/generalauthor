For federal fiscal year 2025 (October 1, 2024 through September 30, 2025), we are trying to line up each reported DMR measurement with the numeric discharge limit that should govern it, and then see whether the reported value exceeds that limit.

Right now we are working from the structured fields in the DMR and permit-limit tables. For each FY2025 measurement, we look at the permit, outfall, parameter, and monitoring-period end date, and we tie the measurement to a permit-limit row when the monitoring period falls within that limit’s begin and end dates. On this dataset that gives us 824 measurement–limit pairings for 824 FY2025 measurements, and each measurement lands on exactly one limit. So far, nothing in the data is forcing us to choose between two competing limits for the same measurement.

What we are less sure about is whether that “exactly one governing limit per measurement” rule is actually right as a general matter, even though it happens to hold here.

One worry is staged or overlapping limit intervals. Permit limits can have different effective dates. If two limit rows are both technically in force for the same monitoring period—say a superseded limit and its replacement, or limits that overlap during a transition—should we still treat them as separate applicable limits? Or is there really only one limit that governs compliance for that measurement, and the other row is just catalog history?

A related worry is duplicate-looking limit rows. Sometimes the same numeric limit may appear more than once in the permit-limit schedule, perhaps as a restatement or a catalog artifact rather than a genuinely separate obligation. If two rows carry the same limit value for the same outfall and parameter, should that count as two applicable limits, or as one limit recorded twice?

We have not resolved those cases from the structured data alone. We are asking because your read of how permit limits actually work will shape whether we should keep assuming one governing limit per measurement, or treat some situations as genuinely ambiguous or multi-limit.

Does that match how you think about it? If not, what would you correct or add?
