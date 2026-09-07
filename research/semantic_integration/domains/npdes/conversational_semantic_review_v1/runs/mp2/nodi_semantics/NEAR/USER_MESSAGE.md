For Federal FY2025, we have 186 DMR rows with no numeric reported value (`DMR_VALUE_NMBR` empty) but a nonempty NODI code: 150 rows carry code **C**, 36 carry code **9**. Purpose C asks us to say what the available evidence establishes for these missing-result cases — in particular, whether a row documents no discharge, documents that monitoring was not required, represents some other explained no-data state, or is a required monitoring gap that still lacks adequate evidence.

**My current best read**

I think **C** and **9** are not interchangeable labels for “no number on the form.” They appear to mark two different explained absences:

- **NODI C** — the permittee is documenting a **no-discharge period**: monitoring may still be required on the limit, but the reporter is asserting that discharge did not occur, so no numeric result applies for that period.
- **NODI 9** — the permittee is documenting that **monitoring was not required / not applicable** for that period, so absence of a numeric result is expected rather than a gap.

**Why I lean that way (from the data, not from treating the CSV as a codebook)**

The split is very clean structurally:

- All 150 **C** rows are on permit **NM0000116**, all with `OPTIONAL_MONITORING_FLAG = N` (non-optional limits), covering conventional parameters like flow and BOD/TSS-style codes. The same permit also has 30 FY2025 rows *with* numeric values, so C is not simply “this permit never reports.”
- All 36 **9** rows are on permit **NM0020583**, mostly on whole-effluent toxicity retest parameters (`22415`, `22416`, etc.). Twenty-four of those have `OPTIONAL_MONITORING_FLAG = Y`, and the limit frequency code is often `09/99` (event-based), with permit-limit comments describing pass/fail reporting that applies only when earlier tests fail. That pattern looks like “this limit exists, but this month’s retest slot was not triggered,” not “we had no discharge.”

So the codes correlate with different permit/limit shapes in ways that match how I would expect “no discharge” vs “not required this period” to show up in practice.

**Why the distinction matters for what we are building**

Purpose C is not just counting blank cells. We need to separate:

1. cases where missing evidence is **explained** by a documented no-discharge or not-required assertion, from  
2. cases where required monitoring appears to have **no adequate explanation**.

If C and 9 both just mean “no numeric value,” we cannot classify the 186 rows and would have to leave most of Purpose C unresolved. If C means no discharge and 9 means not required, we can route rows into different established states — but only if that reading is actually correct for how these codes are used in NPDES DMR reporting and in your review practice.

**Alternatives I have genuinely considered**

- **Both codes are generic “no data” markers** with no reliable semantic difference for compliance review; optional-monitoring flags and limit comments would be the real signals, and NODI would be mostly filing metadata.
- **C does not establish “no discharge” as a substantive fact** — it might only mean “no sample / no value reported” without committing to whether discharge occurred, so we should not treat it as documented no-discharge without more evidence.
- **9 might mean something narrower than “not required”** in your context — for example, a specific agency or form convention for toxicity retests, seasonal limits, or conditional parameters — even though the optional/event-driven pattern in this dataset fits a not-required reading.

I may be importing general NPDES/DMR familiarity that is not justified by these structured sources alone. The draft construction deliberately refuses to treat the codes as self-explaining and leaves them unresolved until interpreted.

Please correct any of this in whatever way is useful — including if the codes mean something else entirely, if the distinction is weaker or stronger than I think, or if optional-monitoring flags and limit comments should override NODI in some situations. There is no fixed menu of answers; I need your account of what C and 9 actually establish in cases like these.
