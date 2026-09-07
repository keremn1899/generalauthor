# Failure analysis

## MEASURED

### Part A remaining errors (A1)

| cell | class | family | primary bucket |
| --- | --- | --- | --- |
| harbor Q6 × C1,C2,C3 | UNSUPPORTED_CLOSURE (`false`) | UNRESOLVED_AS_FALSE | CONSUMER_REASONING_FAILURE |
| harbor Q3 × C3 | INCORRECT (3) | WRONG_GRAIN | CONSUMER_REASONING_FAILURE |
| seed Q4 × C1,C3 | UNRESOLVED_INCORRECTLY | PROPOSITION_CONTAMINATION | CONSUMER_REASONING_FAILURE |

A0 had the same three families; grain was 3/3 rather than 1/3.

Unused: RUNTIME_FAILURE, SOURCE_DISCOVERY_FAILURE, WORLD_SEMANTICS_INSUFFICIENT, ABI_DISCOVERY_FAILURE, GRAPH_API_NEEDED.

### Part B

No failed tasks. Mixed P3 programs preserved unresolved lists beside empty/zero established sums.

## OBSERVED

The compact contract moved Q3 from PURPOSE `billable_hours` absence (count 3) to WORLD `tow_job.billed_hours` blank (count 1) in two of three A1 consumers. The same consumers still closed Q6.

Yes/no questions are the remaining hole: “was it a documented emergency?” plus a failure row is read as evidence for `false`, not as missing documentation.

Seed match-rate vs waiver overlay is still present when the PURPOSE failure is attached to the same relation as the established rate. Rule 4 of the contract states the right discipline; two of three A1 consumers did not apply it.

Programming agents, given an explicit “separately list unresolved” instruction in P3, did apply that discipline. The difference is task shape, not World state.

## HYPOTHESIS

Failures remain consumer reasoning. Vocabulary discovery was not the bottleneck (consumers and programmers found constructor-authored names). Graph expressiveness was not the bottleneck (joins sufficed). Semantics were present. A stronger polar-question rule (“insufficient documentation ≠ false”) would be the next read-contract increment — still not a runtime change, and not ABI.
