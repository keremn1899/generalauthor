# Consequence of domain expert reply on "WHEN DISCHARGING"

## What changed

The `conditional_discharge_dependent_monitoring` unresolved entries for the 17 permit-limit rows whose DMR comment contains "WHEN DISCHARGING" now carry a more precise reason and grounding metadata. The reason records the expert's clarification that the phrase ties monitoring obligation to discharge occurrence in the evaluated period—not to how a limit applies during an event—and that intermittent or conditional outfalls generally require monitoring and reporting only when discharge actually occurred. The grounding now includes `comment_semantic_role: discharge_occurrence_conditioning` to distinguish this comment family from aggregation or pass/fail remarks.

## What did not change

No monitoring applicability rule was added. The issue stays explicitly unresolved for purposes B and C because the expert said not to lock discharge-conditioned obligation into a rule without checking permit narrative language, and structured sources still do not establish discharge occurrence for evaluated periods.

The three comment families remain separate: geometric-mean comments still use `aggregated_reporting_requirement`, pass/fail comments still use `pass_fail_reporting_semantics`, and "WHEN DISCHARGING" still uses `conditional_discharge_dependent_monitoring`. No rows were reinterpreted as known or not applicable.

The `permit_limit_comment_text` requirement still treats only blank comments as interpreted. `permit_document_text_not_available` remains unresolved. No source facts were invented.
