# Uncommitted previous proposal

This proposal has NOT been committed. Durable construction.py is still the original draft.
The expert is now responding to this proposal.

## PROPOSAL.json

{
  "utterance_understood": "Yes, but only for Purpose A. Don't make that a general rule.",
  "candidate_scope": "ONE_PURPOSE",
  "semantic_delta": "Confirm that after collapsing duplicate or restated permit-limit catalog rows, a FY2025 measurement may be compared against multiple applicable limits even when they share the same limit type code. Derive measurement_limit_pair by matching each measurement to every permit-limit row sharing permit, outfall, parameter, and an effective interval containing the monitoring period, collapse restated rows, and materialize all surviving pairs. Change the Purpose A unique_applicable_limit_per_measurement requirement from cardinality ONE to AT_LEAST_ONE per measurement. Do not generalize this multiplicity policy beyond Purpose A—leave purposes B and C without an analogous applicability cap, and do not restate it as a WORLD-mode rule.",
  "epistemic_basis": "USER_CERTIFIED_POLICY",
  "remaining_ambiguity": "The expert did not specify which structured fields define duplicate or restated catalog rows; the dry run collapses on limit_type_code, limit_id, limit_value_standard_units, limit_value_qualifier_code, and statistical_base_type_code. It remains unresolved whether downstream per-measurement comparison requirements (numeric value, operator, qualifier, statistical base) should stay scoped per measurement or be re-scoped per measurement–limit pair when multiple limits survive.",
  "primary_dry_run_id": "multi_applicable_limits"
}


## DECISION.json

{
  "disposition": "READY_FOR_ACCEPTANCE",
  "reason": "Your reply affirms the multi-limit reading from the prior clarification—after collapsing restated catalog rows, a FY2025 measurement may be compared against multiple applicable limits even when they share a limit type code—and restricts that policy to Purpose A only, not as a general WORLD rule. The sole dry run (multi_applicable_limits) matches this scope and produces the expected expansion in pairs and comparison candidates without adding new unresolved items.",
  "consequence_divergence": false,
  "chosen_dry_run_id": "multi_applicable_limits"
}


## ACCEPTANCE.md

# Acceptance: multiple applicable limits for Purpose A

## What you mean

You are confirming the correction we asked about: after duplicate or restated permit-limit catalog rows are collapsed, a single FY2025 measurement may still be compared against **multiple applicable limits**, including cases where those limits share the same limit type code but differ in other fields (such as limit id, numeric value, or statistical base). You are **not** asking us to keep forcing exactly one governing limit per measurement.

You are also drawing a scope line: this multiplicity policy applies **only to Purpose A** (applicable discharge limits for Federal FY2025). It should **not** be generalized to Purposes B or C, and it should **not** be restated as a global WORLD-mode rule.

## Where it applies

- **Purpose A only** — evaluating which enforceable numeric discharge limits apply to FY2025 measurements and whether reported values exceed them.
- **Not** Purposes B or C, and **not** a cross-purpose or WORLD-level applicability cap.

## What rule would change

The Purpose A requirement `unique_applicable_limit_per_measurement` would change from **exactly one** applicable limit per measurement to **at least one** per measurement, with no upper bound after deduplication.

Measurement–limit pairs would be derived by matching each FY2025 measurement to every permit-limit catalog row that shares permit, outfall, parameter, and an effective interval containing the monitoring period, **collapsing restated catalog rows first**, then materializing all surviving pairs.

## Measurable consequences (dry run vs. baseline draft)

| Measure | Baseline draft | Proposed (multi_applicable_limits) |
|---|---:|---:|
| measurement–limit pairs | 824 | **2,812** (+1,988) |
| numeric comparison candidates | 342 | **1,336** (+994) |
| unresolved issue groups | 8 | **8** (unchanged) |
| unresolved items (total) | 535 | **535** (unchanged) |

The expansion reflects measurements now paired with every surviving applicable limit after deduplication, rather than being forced to a single pair. The **692 measurements** that still have multiple collapsed limits sharing the same limit type code are treated as expected under your confirmed reading—they do not create new unresolved multiplicity holes.

All eight existing unresolved groups are unchanged in count:

- aggregated reporting requirements (40)
- conditional discharge-dependent monitoring (17)
- limit sample type codes (105)
- monitoring frequency codes (105)
- NODI code semantics (186)
- pass/fail reporting semantics (12)
- permit document text unavailable (1)
- permit limit comment text (69)

WORLD-mode semantics are unchanged; only Purpose A purpose semantics change.

## What remains unresolved

These were **not** settled by your reply and were **not** what separated the prior dry-run interpretations:

1. **Which catalog fields define a restated duplicate row.** The dry run collapses on limit type code, limit id, standard-unit numeric value, value qualifier, and statistical base. A narrower or broader collapse key could shift pair counts, but you have not specified an alternative.

2. **How downstream comparison fields (numeric value, operator, qualifier, statistical base) should be scoped** when multiple limits survive for one measurement. The dry run materializes comparison candidates at the measurement–limit pair level (1,336 candidates across 2,812 pairs), which is consistent with per-pair scoping, but you have not explicitly confirmed that as policy.

Neither of these produced competing dry-run outcomes in the current results, and neither blocks accepting the core policy you confirmed.


## DRY_RUN_RESULTS.json

{
  "baseline": {
    "ok": true,
    "errors": [],
    "n_hole_groups": 8,
    "n_hole_instances": 535,
    "relation_row_counts": {
      "dmr_measurement": 824,
      "permit_limit": 105,
      "permit_document": 12,
      "fy2025_measurement": 824,
      "measurement_limit_pair": 824,
      "numeric_comparison_candidate": 342,
      "no_numeric_result_case": 186,
      "monitoring_requirement_fy2025": 105
    },
    "requirement_names": [
      "fy2025_measurements_materializable",
      "measurement_limit_pairs_materializable",
      "unique_applicable_limit_per_measurement",
      "numeric_comparison_candidates_materializable",
      "limit_value_for_comparison",
      "reported_value_for_comparison",
      "limit_comparison_operator",
      "reported_value_qualifier",
      "optional_monitoring_flag_for_limit_applicability",
      "limit_type_code_for_enforceability",
      "statistical_base_for_limit_comparison",
      "monitoring_requirements_materializable",
      "monitoring_frequency_code",
      "limit_sample_type_code",
      "optional_monitoring_flag_for_obligation",
      "permit_limit_comment_text",
      "limit_set_designator_for_schedule",
      "no_numeric_result_cases_materializable",
      "nodi_code_semantics",
      "optional_monitoring_flag_for_missing_evidence",
      "aggregated_reporting_requirement",
      "aggregated_reporting_requirement",
      "aggregated_reporting_requirement",
      "aggregated_reporting_requirement",
      "aggregated_reporting_requirement",
      "aggregated_reporting_requirement",
      "conditional_discharge_dependent_monitoring",
      "conditional_discharge_dependent_monitoring",
      "aggregated_reporting_requirement",
      "aggregated_reporting_requirement",
      "aggregated_reporting_requirement",
      "aggregated_reporting_requirement",
      "conditional_discharge_dependent_monitoring",
      "conditional_discharge_dependent_monitoring",
      "conditional_discharge_dependent_monitoring",
      "conditional_discharge_dependent_monitoring",
      "aggregated_reporting_requirement",
      "aggregated_reporting_requirement",
      "aggregated_reporting_requirement",
      "aggregated_reporting_requirement",
      "pass_fail_reporting_semantics",
      "pass_fail_reporting_semantics",
      "pass_fail_reporting_semantics",
      "pass_fail_reporting_semantics",
      "aggregated_reporting_requirement",
      "aggregated_reporting_requirement",
      "aggregated_reporting_requirement",
      "conditional_discharge_dependent_monitoring",
      "conditional_discharge_dependent_monitoring",
      "aggregated_reporting_requirement",
      "conditional_discharge_dependent_monitoring",
      "aggregated_reporting_requirement",
      "aggregated_reporting_requirement",
      "aggregated_reporting_requirement",
      "aggregated_reporting_requirement",
      "pass_fail_reporting_semantics",
      "pass_fail_reporting_semantics",
      "aggregated_reporting_requirement",
      "aggregated_reporting_requirement",
      "aggregated_reporting_requirement",
      "aggregated_reporting_requirement",
      "aggregated_reporting_requirement",
      "aggregated_reporting_requirement",
      "aggregated_reporting_requirement",
      "aggregated_reporting_requirement",
      "aggregated_reporting_requirement",
      "aggregated_reporting_requirement",
      "aggregated_reporting_requirement",
      "aggregated_reporting_requirement",
      "aggregated_reporting_requirement",
      "aggregated_reporting_requirement",
      "aggregated_reporting_requirement",
      "aggregated_reporting_requirement",
      "conditional_discharge_dependent_monitoring",
      "conditional_discharge_dependent_monitoring",
      "conditional_discharge_dependent_monitoring",
      "conditional_discharge_dependent_monitoring",
      "conditional_discharge_dependent_monitoring",
      "conditional_discharge_dependent_monitoring",
      "conditional_discharge_dependent_monitoring",
      "conditional_discharge_dependent_monitoring",
      "aggregated_reporting_requirement",
      "aggregated_reporting_requirement",
      "pass_fail_reporting_semantics",
      "pass_fail_reporting_semantics",
      "pass_fail_reporting_semantics",
      "pass_fail_reporting_semantics",
      "pass_fail_reporting_semantics",
      "pass_fail_reporting_semantics",
      "permit_document_text_not_available"
    ],
    "hole_groups": [
      {
        "group_id": "g000",
        "requirement": "aggregated_reporting_requirement",
        "failure_kind": "EXPLICIT_UNRESOLVED",
        "relation": "monitoring_requirement_fy2025",
        "n_instances": 40
      },
      {
        "group_id": "g001",
        "requirement": "conditional_discharge_dependent_monitoring",
        "failure_kind": "EXPLICIT_UNRESOLVED",
        "relation": "monitoring_requirement_fy2025",
        "n_instances": 17
      },
      {
        "group_id": "g002",
        "requirement": "limit_sample_type_code",
        "failure_kind": "UNINTERPRETED",
        "relation": "monitoring_requirement_fy2025",
        "n_instances": 105
      },
      {
        "group_id": "g003",
        "requirement": "monitoring_frequency_code",
        "failure_kind": "UNINTERPRETED",
        "relation": "monitoring_requirement_fy2025",
        "n_instances": 105
      },
      {
        "group_id": "g004",
        "requirement": "nodi_code_semantics",
        "failure_kind": "UNINTERPRETED",
        "relation": "no_numeric_result_case",
        "n_instances": 186
      },
      {
        "group_id": "g005",
        "requirement": "pass_fail_reporting_semantics",
        "failure_kind": "EXPLICIT_UNRESOLVED",
        "relation": "measurement_limit_pair",
        "n_instances": 12
      },
      {
        "group_id": "g006",
        "requirement": "permit_document_text_not_available",
        "failure_kind": "EXPLICIT_UNRESOLVED",
        "relation": "permit_document",
        "n_instances": 1
      },
      {
        "group_id": "g007",
        "requirement": "permit_limit_comment_text",
        "failure_kind": "UNINTERPRETED",
        "relation": "permit_limit",
        "n_instances": 69
      }
    ]
  },
  "proposals": [
    {
      "id": "multi_applicable_limits",
      "public": {
        "ok": true,
        "errors": [],
        "n_hole_groups": 8,
        "n_hole_instances": 535,
        "relation_row_counts": {
          "dmr_measurement": 824,
          "permit_limit": 105,
          "permit_document": 12,
          "fy2025_measurement": 824,
          "measurement_limit_pair": 2812,
          "numeric_comparison_candidate": 1336,
          "no_numeric_result_case": 186,
          "monitoring_requirement_fy2025": 105
        },
        "requirement_names": [
          "fy2025_measurements_materializable",
          "measurement_limit_pairs_materializable",
          "unique_applicable_limit_per_measurement",
          "numeric_comparison_candidates_materializable",
          "limit_value_for_comparison",
          "reported_value_for_comparison",
          "limit_comparison_operator",
          "reported_value_qualifier",
          "optional_monitoring_flag_for_limit_applicability",
          "limit_type_code_for_enforceability",
          "statistical_base_for_limit_comparison",
          "monitoring_requirements_materializable",
          "monitoring_frequency_code",
          "limit_sample_type_code",
          "optional_monitoring_flag_for_obligation",
          "permit_limit_comment_text",
          "limit_set_designator_for_schedule",
          "no_numeric_result_cases_materializable",
          "nodi_code_semantics",
          "optional_monitoring_flag_for_missing_evidence",
          "aggregated_reporting_requirement",
          "aggregated_reporting_requirement",
          "aggregated_reporting_requirement",
          "aggregated_reporting_requirement",
          "aggregated_reporting_requirement",
          "aggregated_reporting_requirement",
          "conditional_discharge_dependent_monitoring",
          "conditional_discharge_dependent_monitoring",
          "aggregated_reporting_requirement",
          "aggregated_reporting_requirement",
          "aggregated_reporting_requirement",
          "aggregated_reporting_requirement",
          "conditional_discharge_dependent_monitoring",
          "conditional_discharge_dependent_monitoring",
          "conditional_discharge_dependent_monitoring",
          "conditional_discharge_dependent_monitoring",
          "aggregated_reporting_requirement",
          "aggregated_reporting_requirement",
          "aggregated_reporting_requirement",
          "aggregated_reporting_requirement",
          "pass_fail_reporting_semantics",
          "pass_fail_reporting_semantics",
          "pass_fail_reporting_semantics",
          "pass_fail_reporting_semantics",
          "aggregated_reporting_requirement",
          "aggregated_reporting_requirement",
          "aggregated_reporting_requirement",
          "conditional_discharge_dependent_monitoring",
          "conditional_discharge_dependent_monitoring",
          "aggregated_reporting_requirement",
          "conditional_discharge_dependent_monitoring",
          "aggregated_reporting_requirement",
          "aggregated_reporting_requirement",
          "aggregated_reporting_requirement",
          "aggregated_reporting_requirement",
          "pass_fail_reporting_semantics",
          "pass_fail_reporting_semantics",
          "aggregated_reporting_requirement",
          "aggregated_reporting_requirement",
          "aggregated_reporting_requirement",
          "aggregated_reporting_requirement",
          "aggregated_reporting_requirement",
          "aggregated_reporting_requirement",
          "aggregated_reporting_requirement",
          "aggregated_reporting_requirement",
          "aggregated_reporting_requirement",
          "aggregated_reporting_requirement",
          "aggregated_reporting_requirement",
          "aggregated_reporting_requirement",
          "aggregated_reporting_requirement",
          "aggregated_reporting_requirement",
          "aggregated_reporting_requirement",
          "aggregated_reporting_requirement",
          "conditional_discharge_dependent_monitoring",
          "conditional_discharge_dependent_monitoring",
          "conditional_discharge_dependent_monitoring",
          "conditional_discharge_dependent_monitoring",
          "conditional_discharge_dependent_monitoring",
          "conditional_discharge_dependent_monitoring",
          "conditional_discharge_dependent_monitoring",
          "conditional_discharge_dependent_monitoring",
          "aggregated_reporting_requirement",
          "aggregated_reporting_requirement",
          "pass_fail_reporting_semantics",
          "pass_fail_reporting_semantics",
          "pass_fail_reporting_semantics",
          "pass_fail_reporting_semantics",
          "pass_fail_reporting_semantics",
          "pass_fail_reporting_semantics",
          "permit_document_text_not_available"
        ],
        "hole_groups": [
          {
            "group_id": "g000",
            "requirement": "aggregated_reporting_requirement",
            "failure_kind": "EXPLICIT_UNRESOLVED",
            "relation": "monitoring_requirement_fy2025",
            "n_instances": 40
          },
          {
            "group_id": "g001",
            "requirement": "conditional_discharge_dependent_monitoring",
            "failure_kind": "EXPLICIT_UNRESOLVED",
            "relation": "monitoring_requirement_fy2025",
            "n_instances": 17
          },
          {
            "group_id": "g002",
            "requirement": "limit_sample_type_code",
            "failure_kind": "UNINTERPRETED",
            "relation": "monitoring_requirement_fy2025",
            "n_instances": 105
          },
          {
            "group_id": "g003",
            "requirement": "monitoring_frequency_code",
            "failure_kind": "UNINTERPRETED",
            "relation": "monitoring_requirement_fy2025",
            "n_instances": 105
          },
          {
            "group_id": "g004",
            "requirement": "nodi_code_semantics",
            "failure_kind": "UNINTERPRETED",
            "relation": "no_numeric_result_case",
            "n_instances": 186
          },
          {
            "group_id": "g005",
            "requirement": "pass_fail_reporting_semantics",
            "failure_kind": "EXPLICIT_UNRESOLVED",
            "relation": "measurement_limit_pair",
            "n_instances": 12
          },
          {
            "group_id": "g006",
            "requirement": "permit_document_text_not_available",
            "failure_kind": "EXPLICIT_UNRESOLVED",
            "relation": "permit_document",
            "n_instances": 1
          },
          {
            "group_id": "g007",
            "requirement": "permit_limit_comment_text",
            "failure_kind": "UNINTERPRETED",
            "relation": "permit_limit",
            "n_instances": 69
          }
        ]
      },
      "delta": {
        "relation_count_changes": {
          "measurement_limit_pair": {
            "baseline": 824,
            "proposed": 2812
          },
          "numeric_comparison_candidate": {
            "baseline": 342,
            "proposed": 1336
          }
        },
        "requirements_added": [],
        "requirements_removed": [],
        "requirements_changed": [
          {
            "name": "unique_applicable_limit_per_measurement",
            "baseline": {
              "name": "unique_applicable_limit_per_measurement",
              "kind": "UNIQUE",
              "purpose": [
                "A"
              ],
              "cardinality": "ONE",
              "relation": "measurement_limit_pair",
              "field": null,
              "known": null
            },
            "proposed": {
              "name": "unique_applicable_limit_per_measurement",
              "kind": "UNIQUE",
              "purpose": [
                "A"
              ],
              "cardinality": "AT_LEAST_ONE",
              "relation": "measurement_limit_pair",
              "field": null,
              "known": null
            }
          }
        ],
        "relation_mode_changes": {},
        "n_hole_groups": {
          "baseline": 8,
          "proposed": 8
        },
        "n_hole_instances": {
          "baseline": 535,
          "proposed": 535
        },
        "hole_requirements_added": [],
        "hole_requirements_removed": [],
        "WORLD_semantics_changed": false,
        "PURPOSE_semantics_changed": true,
        "ok": {
          "baseline": true,
          "proposed": true
        }
      },
      "construction_sha256": "85c31524daf25001ef13f6c567be197105fde2ef459b7ca445bc6aa5b85c5f9e"
    }
  ]
}


