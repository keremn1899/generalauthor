For federal fiscal year 2025, we are looking at DMR rows where the permittee did not report an ordinary numeric result — the concentration or measurement field is blank. There are 186 of these in the dataset. Each row carries a NODI code in the structured data, and in this fixture they fall into two values: **C** on 150 rows and **9** on 36 rows.

We are trying to understand what those codes actually establish about the monitoring period. Purpose C is about missing-evidence semantics: when there is no numeric result, can we tell whether the permittee documented no discharge, whether monitoring simply was not required that period, whether some other no-data condition applies, or whether required monitoring appears to lack adequate evidence? We do not want to treat a blank value by itself as proof of compliance or violation.

Right now we have not assigned meaning to either code. We are not assuming that C means "no discharge," that 9 means "not required," or that the two codes are interchangeable. The structured fields give us the code letters and the empty result, but not a plain-language interpretation we can rely on without your help.

A few patterns we notice, though we are not treating them as conclusions: code **C** shows up heavily on flow measurements where optional monitoring is flagged as not optional (`N`). Code **9** shows up on whole-effluent-toxicity retest parameters where optional monitoring is flagged as optional (`Y`). Whether that pattern is meaningful, coincidental, or permit-specific, we do not know.

So the question we need your judgment on is: what do NODI codes **C** and **9** mean in practice for these no-result rows? Do they establish different things, or are they effectively the same kind of statement? And for each, what does the code actually tell us about whether discharge occurred, whether monitoring was required, and whether the missing result is adequately explained?

If our framing is off — if these codes work differently than we are describing, or if the right answer depends on context we have not named — please correct or qualify it in whatever terms make sense to you.
