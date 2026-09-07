# Scope analysis

## MEASURED

| case | intended | inferred | ok | silent WORLD |
| --- | --- | --- | --- | --- |
| case1_bare_rejection | UNKNOWN | ONE_RELATION_OR_VOCABULARY | Y | N |
| case2_underspecified | UNKNOWN | ONE_PURPOSE | Y | N |
| case3_substantive | ONE_PURPOSE | ONE_PURPOSE | Y | N |
| case4_purpose_scope | ONE_PURPOSE | ONE_PURPOSE | Y | N |
| case5_world_generalization | WORLD | WORLD | Y | N |
| case6_uncertainty | ONE_SOURCE_VALUE | ONE_SOURCE_VALUE | Y | N |
| case7_policy | ONE_PURPOSE | ONE_PURPOSE | Y | N |
| case8_external_fact | ONE_PURPOSE | ONE_RELATION_OR_VOCABULARY | N | N |

## OBSERVED

Purpose-specific feedback must not silently become WORLD. Case 3 omits scope; Cases 4 and 5 name it.
any_silent_world=False

## HYPOTHESIS

The host can own scope inference if it prefers the narrowest defensible reading and clarifies only when scopes diverge consequentially.
