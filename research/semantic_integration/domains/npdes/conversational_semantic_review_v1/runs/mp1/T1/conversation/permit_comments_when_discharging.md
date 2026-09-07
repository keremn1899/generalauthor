Many permit limit rows in the structured extract carry free-text comments in the DMR comment field. The draft does not yet turn those comments into monitoring rules. Among 105 permit limit rows in scope for FY2025, 69 have nonempty comments, and the draft leaves all of them uninterpreted at the field level.

Three comment patterns show up often enough that the draft has flagged them separately as unresolved dependencies rather than silently ignoring them:

About 17 rows say something like "WHEN DISCHARGING." I read that as a hint that monitoring or limit applicability might depend on whether discharge actually occurred during the period being evaluated. The structured CSVs here do not tell us whether discharge occurred, so the draft stops short of saying what "when discharging" requires.

About 40 rows describe reporting a geometric mean — for example, total dissolved solids measured at an outfall with instruction to report the geometric mean of weekly values. That sounds like an aggregation rule rather than a simple per-sample numeric comparison, but the draft has not decided how that affects whether individual monitoring periods are in or out of compliance.

About 12 rows use pass/fail reporting language — report pass as 0 and fail as 1 in the concentration field. That is a different reporting convention from ordinary concentration limits, and the draft has not interpreted how those should be compared.

I am not asking you to confirm the draft's phrase matching — that part is already done mechanically. What I need from you is domain meaning. When a limit comment says "when discharging," does that mean monitoring is required only if there was a discharge, or does it mean something else? And are the geometric-mean instructions and pass/fail instructions genuinely different compliance questions, or would you treat them as variations of the same "read the permit narrative" problem?
