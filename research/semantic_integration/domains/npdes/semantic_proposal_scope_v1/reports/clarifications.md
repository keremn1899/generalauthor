# Clarifications

## MEASURED

Clarification dispositions: 3 / 8

| case | preferred | got | under | over | closed menu | ontology-heavy | divergence flag |
| --- | --- | --- | --- | --- | --- | --- | --- |
| case1_bare_rejection | NEEDS_CLARIFICATION | NEEDS_CLARIFICATION | N | N | N | N | True |
| case2_underspecified | NEEDS_CLARIFICATION | NEEDS_CLARIFICATION | N | N | N | N | True |
| case3_substantive | READY_FOR_ACCEPTANCE | NEEDS_CLARIFICATION | N | N | N | N | True |
| case4_purpose_scope | READY_FOR_ACCEPTANCE | READY_FOR_ACCEPTANCE | N | N | N | N | False |
| case5_world_generalization | READY_FOR_ACCEPTANCE | READY_FOR_ACCEPTANCE | N | N | N | N | False |
| case6_uncertainty | READY_FOR_ACCEPTANCE | READY_FOR_ACCEPTANCE | N | N | N | N | False |
| case7_policy | READY_FOR_ACCEPTANCE | READY_FOR_ACCEPTANCE | N | N | N | N | False |
| case8_external_fact | READY_FOR_ACCEPTANCE | READY_FOR_ACCEPTANCE | N | N | N | N | False |

## OBSERVED

### case1_bare_rejection

# Clarification needed: what is wrong about "one governing limit per measurement"?

You said the draft is wrong to treat each FY2025 measurement as having exactly one governing applicable numeric limit. That rejection is clear, but it could point in very different directions—and those directions produce very different results on this fixture.

## Where the disagreement sits

The draft currently builds **824** measurement–limit pairs (one per FY2025 measurement) by following the limit identity already carried on each DMR row (`LIMIT_VALUE_ID` and `LIMIT_SET_SCHEDULE_ID`). It then treats the "exactly one applicable limit per measurement" rule as **satisfied** on this data.

A separate issue summary describes pairing differently—as if each measurement were matched against all permit limit rows by permit, outfall, parameter, and whether the monitoring period falls inside each limit's effective dates. Under that catalog-style rule, most measurements would match **multiple** permit limit rows (overlapping or staged intervals), not one.

So the open question is not whether you disagree with the draft's conclusion—you already said you do—but **which part** you are rejecting.

## What would

### case2_underspecified

You confirmed that a single FY2025 measurement can have more than one applicable discharge limit. We should stop treating “exactly one governing limit per measurement” as a policy for this analysis. That part is clear.

What is still open is how we decide which limit rows belong to each measurement.

The current draft links each measurement to the specific limit identifiers carried on that DMR row — the limit value and schedule IDs in the reporting data. On this dataset that yields **824** measurement–limit pairs, of which **342** have both a reported value and a numeric limit suitable for comparison.

Another reading of “multiple limits can apply” is that we should enumerate **every** permit limit row whose effective dates overlap the monitoring period for the same permit, outfall, and parameter — not just the limit the DMR row points at. On this dataset that would yield about **4,076** pairs and about **1,388** numeric comparison candidates — roughly five times as many relationships.

These are not the same analysis. They change how many measurement–limit relationships exist and how many numeric comparisons the construction considers, even though both versions drop the one-limit 

### case3_substantive

# Clarification needed: how many limits can apply to one measurement?

You said that a measurement may need to be compared against **multiple genuinely different limit types**, and that **duplicate or restated catalog rows should still collapse**. We took that as a correction to the current draft rule that forces exactly one applicable limit per FY2025 measurement.

Both ways we modeled your correction agree on the big structural shift: match each measurement to every permit-limit catalog row that shares permit, outfall, parameter, and an effective interval covering the monitoring period, collapse restated rows before pairing, and expand comparisons. On this dataset that raises measurement–limit pairs from **824 to 2,812** and numeric comparison candidates from **342 to 1,336**. All other unresolved items (monitoring frequency codes, pass/fail semantics, permit comments, and the rest) stay the same in both models—**535 unresolved items across 8 issue groups**.

Where the two readings diverge is what happens **after** deduplication, for measurements that still have more than one surviving limit.

## The sticking point

After collapsing restated catalog rows (using limit type, limit 

## HYPOTHESIS

Clarification is warranted by semantic consequence divergence, not generic language-model uncertainty.
