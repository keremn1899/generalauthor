# Consequence of domain expert reply on "WHEN DISCHARGING"

## What changed

The `conditional_discharge_dependent_monitoring` unresolved entries for the 17 permit-limit rows whose DMR comment contains "WHEN DISCHARGING" now carry a reason aligned with the expert's reply. The reason records that the phrase is a precondition for monitoring and reporting obligation (only when the outfall actually discharged in the evaluated period), that it does not change the numeric limit itself, and that permit narrative or permittee records—not limit or DMR tables—are needed to establish discharge occurrence. The grounding still includes `comment_semantic_role: discharge_occurrence_conditioning` to keep this comment family separate from aggregation and pass/fail remarks.

## What did not change

No monitoring applicability rule was added. `monitoring_requirement_fy2025` still lists every FY2025-overlapping limit row without treating discharge as satisfied from structured sources alone. All 17 "WHEN DISCHARGING" rows remain explicitly unresolved for purposes B and C.

The three comment families stay separate: geometric-mean comments use `aggregated_reporting_requirement`, pass/fail comments use `pass_fail_reporting_semantics`, and "WHEN DISCHARGING" uses `conditional_discharge_dependent_monitoring`. No rows were reinterpreted as known, false, or not applicable.

The `permit_limit_comment_text` requirement still treats only blank comments as interpreted. `permit_document_text_not_available` remains unresolved. No source facts were invented.
