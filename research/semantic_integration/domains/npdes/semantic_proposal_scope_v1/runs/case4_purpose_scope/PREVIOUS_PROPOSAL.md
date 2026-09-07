# Uncommitted previous proposal

This proposal has NOT been committed. Durable construction.py is still the original draft.
The expert is now responding to this proposal.

## PROPOSAL.json

{
  "utterance_understood": "No. A measurement may need to be compared against multiple genuinely different limit types, but duplicate or restated catalog rows should still collapse.",
  "candidate_scope": "ONE_PURPOSE",
  "semantic_delta": "Reject the draft policy that each FY2025 measurement has exactly one applicable numeric limit. Derive measurement_limit_pair by matching each measurement to all permit-limit catalog rows that share permit, outfall, parameter, and an effective interval containing the monitoring period, then collapse duplicate or restated catalog rows before materialization. Replace the Purpose A uniqueness requirement from cardinality ONE per measurement to AT_LEAST_ONE per measurement, allowing multiple surviving pairs when they represent genuinely different limits.",
  "epistemic_basis": "USER_CERTIFIED_POLICY",
  "remaining_ambiguity": "The expert did not specify which structured fields distinguish genuinely different limits from restatements beyond limit type. The dry-run collapse key uses limit_type_code, limit_id, limit_value_standard_units, limit_value_qualifier_code, and statistical_base_type_code; narrower keys (e.g., limit_value_id only) or broader keys may be intended. It is also unresolved whether multiple limits sharing the same limit_type_code but differing in numeric value or limit_id should all remain applicable, or whether downstream per-measurement comparison requirements should be re-scoped to each measurement–limit pair.",
  "primary_dry_run_id": "multi_applicable_limits"
}


## CANDIDATES.json

[
  {
    "id": "multi_applicable_limits",
    "interpretation": "A measurement may have multiple applicable limits after collapsing restated catalog rows; Purpose A requires at least one pair per measurement but does not cap multiplicity.",
    "scope": "ONE_PURPOSE",
    "dry_run_id": "multi_applicable_limits",
    "why_plausible": "The expert explicitly rejected exactly-one applicability and said measurements may need comparison against multiple genuinely different limit types. Allowing AT_LEAST_ONE cardinality preserves the obligation that each measurement have some applicable limit while permitting multiple surviving pairs."
  },
  {
    "id": "per_limit_type_unique",
    "interpretation": "After collapsing restated catalog rows, at most one applicable limit per measurement per limit_type_code remains; multiple pairs are allowed only across genuinely different limit types.",
    "scope": "ONE_PURPOSE",
    "dry_run_id": "per_limit_type_unique",
    "why_plausible": "The phrase genuinely different limit types can be read as allowing multiplicity only across limit_type_code, with still-at-most-one governing limit within each type after deduplication."
  }
]


## DECISION.json

{
  "disposition": "NEEDS_CLARIFICATION",
  "reason": "Your correction clearly rejects exactly-one applicable limit per measurement and requires collapsing duplicate catalog rows, but the phrase \"multiple genuinely different limit types\" supports two readings that the dry runs treat differently: allow multiple surviving limits per measurement without a per-type cap, versus allow multiplicity only across different limit types (at most one per type). After the same deduplication step, 692 FY2025 measurements still have multiple collapsed limits sharing the same limit type code; one reading leaves them as valid comparisons (535 total unresolved items, unchanged from baseline), while the other flags those 692 cases as unresolved multiplicity (1,919 total unresolved items, +1,384).",
  "consequence_divergence": true,
  "chosen_dry_run_id": null
}


## CLARIFY.md

# Clarification needed: how many limits can apply to one measurement?

You said that a measurement may need to be compared against **multiple genuinely different limit types**, and that **duplicate or restated catalog rows should still collapse**. We took that as a correction to the current draft rule that forces exactly one applicable limit per FY2025 measurement.

Both ways we modeled your correction agree on the big structural shift: match each measurement to every permit-limit catalog row that shares permit, outfall, parameter, and an effective interval covering the monitoring period, collapse restated rows before pairing, and expand comparisons. On this dataset that raises measurement–limit pairs from **824 to 2,812** and numeric comparison candidates from **342 to 1,336**. All other unresolved items (monitoring frequency codes, pass/fail semantics, permit comments, and the rest) stay the same in both models—**535 unresolved items across 8 issue groups**.

Where the two readings diverge is what happens **after** deduplication, for measurements that still have more than one surviving limit.

## The sticking point

After collapsing restated catalog rows (using limit type, limit id, numeric value, value qualifier, and statistical base to decide sameness), **692 measurements** still have **multiple applicable limits that share the same limit type code** but differ in other fields—for example different limit ids, numeric values, or statistical bases under the same type.

Your phrase “genuinely different **limit types**” can reasonably mean either of the following:

**Reading 1 — multiplicity is about distinct limits, not capped by type.**  
Once restated catalog duplicates are collapsed, every remaining limit is fair game. A measurement may be compared against several limits even when they share a limit type code, as long as they are not the same restated row. Under this reading, those 692 cases are expected and acceptable; the obligation is simply that each measurement has at least one applicable limit, not exactly one. **Total unresolved items stay at 535** (same as today).

**Reading 2 — multiplicity is only across limit types.**  
After deduplication, a measurement may have multiple applicable limits, but **at most one per limit type code**. Limits that share a type code must be narrowed to a single governing limit even when their ids or numeric values differ. Under this reading, those same **692 measurements** are problematic: each would still need a disambiguation rule to pick one limit per type. **Total unresolved items rise to 1,919**—an additional **1,384** flagged cases tied to that multiplicity rule alone.

Both readings honor your rejection of “exactly one limit per measurement” and both collapse duplicate catalog rows the same way. They differ only in whether **same-type, non-restated multiplicity** is allowed or must still be resolved.

## What would change depending on your answer

If Reading 1 matches your intent, we keep all **2,812** pairs and **1,336** comparison candidates, and change the Purpose A rule from “exactly one applicable limit per measurement” to “at least one,” with no upper bound after deduplication. The 692 same-type multi-limit cases become normal comparison rows rather than holes.

If Reading 2 matches your intent, we still materialize the same **2,812** pairs initially, but **692 measurement–limit-type combinations** would remain unresolved until we know how to choose a single governing limit within each type—adding **1,384** new unresolved items on top of the existing **535**.

## A separate, smaller ambiguity (not what split the dry runs)

You did not specify which catalog fields should define “duplicate or restated” beyond what we inferred. Both dry runs used the same collapse rule (limit type, limit id, standard-unit value, value qualifier, statistical base). A narrower or broader collapse key could change pair counts, but that was **not** what separated the two interpretations above—the per-type cap question is what drove the large difference in unresolved-item counts.

Please say—in your own words—whether, after restated rows are collapsed, a measurement may still be compared against **multiple limits that share the same limit type code**, or whether multiplicity should stop at **one limit per type per measurement**. If you have a different rule entirely, that works too.


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
      "construction_sha256": "65de5908119cfc9e754b643a4dc25bf50fa781b55600415a6b39f4c9e4f3bd7d"
    },
    {
      "id": "per_limit_type_unique",
      "public": {
        "ok": true,
        "errors": [],
        "n_hole_groups": 10,
        "n_hole_instances": 1919,
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
          },
          {
            "group_id": "g008",
            "requirement": "unique_applicable_limit_per_measurement",
            "failure_kind": "CARDINALITY_OVERSATISFIED",
            "relation": "measurement_limit_pair",
            "n_instances": 692
          },
          {
            "group_id": "g009",
            "requirement": "unique_applicable_limit_per_measurement",
            "failure_kind": "MULTIPLE_CANDIDATES",
            "relation": "measurement_limit_pair",
            "n_instances": 692
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
        "requirements_changed": [],
        "relation_mode_changes": {},
        "n_hole_groups": {
          "baseline": 8,
          "proposed": 10
        },
        "n_hole_instances": {
          "baseline": 535,
          "proposed": 1919
        },
        "hole_requirements_added": [
          "unique_applicable_limit_per_measurement"
        ],
        "hole_requirements_removed": [],
        "WORLD_semantics_changed": false,
        "PURPOSE_semantics_changed": true,
        "ok": {
          "baseline": true,
          "proposed": true
        }
      },
      "construction_sha256": "2f6dcb21ccddc28871c855b19b69dd26f2dcad86add008ee06590bb0ab23aad5"
    }
  ]
}


