# Failure analysis

## MEASURED

Failed downstream cells (not CORRECT / UNRESOLVED_CORRECTLY):

| arm | domain | task | class | family |
| --- | --- | --- | --- | --- |
| E0, E1 | harbor_towing | T4 ×3 | INCORRECT (3) | GRAIN — PURPOSE `billable_hours` absence, not WORLD blank `billed_hours` |
| E0 R2,R3; E1 ×3 | harbor_towing | T5 | UNSUPPORTED_CLOSURE (`false`) | UNRESOLVED_AS_FALSE |
| E0 ×3; E1 R2 | seed_grants | T4 | UNRESOLVED_INCORRECTLY | waiver overlay on established match rate |
| E1 R1 | seed_grants | T4 | INCORRECT (3000) | OTHER_REASONING — 20% of remaining, not of award amount |

Unused: READ_SIDE_GUIDANCE (could not find relation), WORLD_SEMANTICS_INSUFFICIENT, pathological enumeration.

## OBSERVED

E1 harbor notes already contained the T4/T5 distinctions and the read rule “unresolved ≠ false,” then the task phase repeated the old errors. The compact header and an orientation memo are not what is missing for those families.

Agents reliably found `tow_job`, `billable_hours`, `purpose_requirement_failure`, `award_match_obligation`, remaps. Failures are how they bind a question to a grain or polar closure.

## HYPOTHESIS

Do not add leads, domain summaries, or exploration planners for “can’t find the World.” If anything is still justified, it is the same polar-question / grain discipline as `world_read_programming_v1`, which is host text, not a navigation system. This probe does not re-open ABI or graph APIs.
