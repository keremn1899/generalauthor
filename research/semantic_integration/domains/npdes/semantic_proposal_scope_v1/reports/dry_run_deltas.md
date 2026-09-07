# Dry-run deltas

Counts are diagnostic, not definitions of correctness.

## MEASURED

### case1_bare_rejection

Baseline holes groups=8 instances=535 pairs=824

| id | ok | pairs | comparisons | hole groups | hole instances | req + | req - | WORLD | PURPOSE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| catalog_applicable_limits | True | 4076 | 1388 | 10 | 1943 | [] | [] | N | Y |
| remove_forced_uniqueness | True | 824 | 342 | 9 | 536 | [] | [] | N | N |

- catalog_applicable_limits count changes: `{"measurement_limit_pair": {"baseline": 824, "proposed": 4076}, "numeric_comparison_candidate": {"baseline": 342, "proposed": 1388}}`
- remove_forced_uniqueness requirements changed: `[{"name": "unique_applicable_limit_per_measurement", "baseline": {"name": "unique_applicable_limit_per_measurement", "kind": "UNIQUE", "purpose": ["A"], "cardinality": "ONE", "relation": "measurement_limit_pair", "field": null, "known": null}, "proposed": {"name": "unique_applicable_limit_per_measurement", "kind": "UNRESOLVED", "purpose": ["A"], "cardinality": null, "relation": "measurement_limit_pair", "field": null, "known": null}}]`

### case2_underspecified

Baseline holes groups=8 instances=535 pairs=824

| id | ok | pairs | comparisons | hole groups | hole instances | req + | req - | WORLD | PURPOSE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| drop_unique_requirement | True | 824 | 342 | 8 | 535 | [] | ['unique_applicable_limit_per_measurement'] | Y | Y |
| expand_applicable_limits | True | 4076 | 1388 | 8 | 535 | [] | ['unique_applicable_limit_per_measurement'] | Y | Y |

- expand_applicable_limits count changes: `{"measurement_limit_pair": {"baseline": 824, "proposed": 4076}, "numeric_comparison_candidate": {"baseline": 342, "proposed": 1388}}`

### case3_substantive

Baseline holes groups=8 instances=535 pairs=824

| id | ok | pairs | comparisons | hole groups | hole instances | req + | req - | WORLD | PURPOSE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| multi_applicable_limits | True | 2812 | 1336 | 8 | 535 | [] | [] | N | Y |
| per_limit_type_unique | True | 2812 | 1336 | 10 | 1919 | [] | [] | N | Y |

- multi_applicable_limits count changes: `{"measurement_limit_pair": {"baseline": 824, "proposed": 2812}, "numeric_comparison_candidate": {"baseline": 342, "proposed": 1336}}`
- multi_applicable_limits requirements changed: `[{"name": "unique_applicable_limit_per_measurement", "baseline": {"name": "unique_applicable_limit_per_measurement", "kind": "UNIQUE", "purpose": ["A"], "cardinality": "ONE", "relation": "measurement_limit_pair", "field": null, "known": null}, "proposed": {"name": "unique_applicable_limit_per_measurement", "kind": "UNIQUE", "purpose": ["A"], "cardinality": "AT_LEAST_ONE", "relation": "measurement_limit_pair", "field": null, "known": null}}]`
- per_limit_type_unique count changes: `{"measurement_limit_pair": {"baseline": 824, "proposed": 2812}, "numeric_comparison_candidate": {"baseline": 342, "proposed": 1336}}`

### case4_purpose_scope

Baseline holes groups=8 instances=535 pairs=824

| id | ok | pairs | comparisons | hole groups | hole instances | req + | req - | WORLD | PURPOSE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| multi_applicable_limits | True | 2812 | 1336 | 8 | 535 | [] | [] | N | Y |

- multi_applicable_limits count changes: `{"measurement_limit_pair": {"baseline": 824, "proposed": 2812}, "numeric_comparison_candidate": {"baseline": 342, "proposed": 1336}}`
- multi_applicable_limits requirements changed: `[{"name": "unique_applicable_limit_per_measurement", "baseline": {"name": "unique_applicable_limit_per_measurement", "kind": "UNIQUE", "purpose": ["A"], "cardinality": "ONE", "relation": "measurement_limit_pair", "field": null, "known": null}, "proposed": {"name": "unique_applicable_limit_per_measurement", "kind": "UNIQUE", "purpose": ["A"], "cardinality": "AT_LEAST_ONE", "relation": "measurement_limit_pair", "field": null, "known": null}}]`

### case5_world_generalization

Baseline holes groups=8 instances=535 pairs=824

| id | ok | pairs | comparisons | hole groups | hole instances | req + | req - | WORLD | PURPOSE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| world_multi_applicable_limits | True | 2812 | 1336 | 8 | 535 | [] | [] | Y | Y |

- world_multi_applicable_limits count changes: `{"measurement_limit_pair": {"baseline": 824, "proposed": 2812}, "numeric_comparison_candidate": {"baseline": 342, "proposed": 1336}}`
- world_multi_applicable_limits requirements changed: `[{"name": "unique_applicable_limit_per_measurement", "baseline": {"name": "unique_applicable_limit_per_measurement", "kind": "UNIQUE", "purpose": ["A"], "cardinality": "ONE", "relation": "measurement_limit_pair", "field": null, "known": null}, "proposed": {"name": "unique_applicable_limit_per_measurement", "kind": "UNIQUE", "purpose": ["A"], "cardinality": "AT_LEAST_ONE", "relation": "measurement_limit_pair", "field": null, "known": null}}]`

### case6_uncertainty

Baseline holes groups=8 instances=535 pairs=824

No dry-run constructions.

### case7_policy

Baseline holes groups=8 instances=535 pairs=824

| id | ok | pairs | comparisons | hole groups | hole instances | req + | req - | WORLD | PURPOSE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| final_permit_over_fact_sheet | True | 824 | 342 | 9 | 536 | ['document_authority_among_other_kinds'] | [] | Y | Y |

- final_permit_over_fact_sheet count changes: `{"document_conflict_authority": {"baseline": null, "proposed": 1}}`

### case8_external_fact

Baseline holes groups=8 instances=535 pairs=824

| id | ok | pairs | comparisons | hole groups | hole instances | req + | req - | WORLD | PURPOSE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| legal_hierarchy_world | True | 824 | 342 | 9 | 536 | ['permit_document_authority_other_kinds'] | [] | Y | Y |
| purpose_policy_bc | True | 824 | 342 | 9 | 536 | ['final_permit_overrides_fact_sheet', 'permit_document_authority_other_kinds'] | [] | Y | Y |

- legal_hierarchy_world count changes: `{"document_kind_precedence": {"baseline": null, "proposed": 1}}`
- purpose_policy_bc count changes: `{"document_kind_precedence": {"baseline": null, "proposed": 1}}`

## OBSERVED

See per-case tables. Ambiguous cases should show consequence divergence across candidate dry-runs if the host wrote more than one construction.

## HYPOTHESIS

Dry-running a proposed construction on a disposable copy can expose blast radius before durable commit.
