For Federal FY2025 we're trying to compare each reported DMR measurement to the one numeric limit that actually governs it. The draft links each measurement to a permit-limit row using the limit value ID and schedule ID already present on the DMR row, and only keeps measurements whose monitoring period end date falls in FY2025 (October 1, 2024 through September 30, 2025).

On this dataset that produces 824 measurement–limit pairs—one per FY2025 measurement. The construction mechanically requires exactly one applicable limit per measurement, and right now nothing violates that: there are no measurements with two competing pairs.

What I need your help with is whether that one-to-one result is the right *meaning*, not just whether the join happened to work here.

Sometimes the permit catalog has multiple limit rows for the same outfall and parameter with overlapping effective dates, or what look like restatements of the same limit under different IDs. The draft does not try to merge those; it trusts the IDs on the DMR row. Should overlapping or staged date intervals ever count as more than one governing limit for a single measurement? And when several catalog rows look like the same limit repeated, should they be treated as one identity for "which limit applies," or kept separate?

If the current approach matches how you'd read these permits, say so. If not, tell me what rule you'd use to pick—or to keep—multiple limits when intervals or catalog rows overlap.
