# Clarification needed: how many limits can apply to one measurement?

You said that a measurement may need to be compared against **multiple genuinely different limit types**, and that **duplicate or restated catalog rows should still collapse**. We took that as a correction to the current draft rule that forces exactly one applicable limit per FY2025 measurement.

Both ways we modeled your correction agree on the big structural shift: match each measurement to every permit-limit catalog row that shares permit, outfall, parameter, and an effective interval covering the monitoring period, collapse restated rows before pairing, and expand comparisons. On this dataset that raises measurement–limit pairs from **824 to 2,812** and numeric comparison candidates from **342 to 1,336**. All other unresolved items (monitoring frequency codes, pass/fail semantics, permit comments, and the rest) stay the same in both models—**535 unresolved items across 8 issue groups**.

Where the two readings diverge is what happens **after** deduplication, for measurements that still have more than one surviving limit.

## The sticking point

After collapsing restated catalog rows (using limit type, limit id, numeric value, value qualifier, and statistical base to decide sameness), **692 measurements** still have **multiple applicable limits that share the same limit type code** but differ in other fields—for example different limit ids, numeric values, or statistical bases under the same type.

Your phrase “genuinely different **limit types**” can reasonably mean either of the following:

**Reading 1 — multiplicity is about distinct limits, not capped by type.**  
Once restated catalog duplicates are collapsed, every remaining limit is fair game. A measurement may be compared against several limits even when they share a limit type code, as long as they are not the same restated row. Under this reading, those 692 cases are expected and acceptable; the obligation is simply that each measurement has at least one applicable limit, not exactly one. **Total unresolved items stay at 535** (same as today).

**Reading 2 — multiplicity is only across limit types.**  
After deduplication, a measurement may have multiple applicable limits, but **at most one per limit type code**. Limits that share a type code must be narrowed to a single governing limit even when their ids or numeric values differ. Under this reading, those same **692 measurements** are problematic: each would still need a disambiguation rule to pick one limit per type. **Total unresolved items rise to 1,919**—an additional **1,384** flagged cases tied to that multiplicity rule alone.

Both readings honor your rejection of “exactly one limit per measurement” and both collapse duplicate catalog rows the same way. They differ only in whether **same-type, non-restated multiplicity** is allowed or must still be resolved.

## What would change depending on your answer

If Reading 1 matches your intent, we keep all **2,812** pairs and **1,336** comparison candidates, and change the Purpose A rule from “exactly one applicable limit per measurement” to “at least one,” with no upper bound after deduplication. The 692 same-type multi-limit cases become normal comparison rows rather than holes.

If Reading 2 matches your intent, we still materialize the same **2,812** pairs initially, but **692 measurement–limit-type combinations** would remain unresolved until we know how to choose a single governing limit within each type—adding **1,384** new unresolved items on top of the existing **535**.

## A separate, smaller ambiguity (not what split the dry runs)

You did not specify which catalog fields should define “duplicate or restated” beyond what we inferred. Both dry runs used the same collapse rule (limit type, limit id, standard-unit value, value qualifier, statistical base). A narrower or broader collapse key could change pair counts, but that was **not** what separated the two interpretations above—the per-type cap question is what drove the large difference in unresolved-item counts.

Please say—in your own words—whether, after restated rows are collapsed, a measurement may still be compared against **multiple limits that share the same limit type code**, or whether multiplicity should stop at **one limit per type per measurement**. If you have a different rule entirely, that works too.
