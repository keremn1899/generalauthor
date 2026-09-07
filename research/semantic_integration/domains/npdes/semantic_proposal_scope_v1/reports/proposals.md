# Proposals

## MEASURED

| case | understood | scope vs intended | epistemic vs intended | proposal before mutation |
| --- | --- | --- | --- | --- |
| case1_bare_rejection | No, that's wrong. | ONE_RELATION_OR_VOCABULARY / UNKNOWN Y | MODEL_CORRECTION / AMBIGUOUS N | Y |
| case2_underspecified | No, multiple limits can apply. | ONE_PURPOSE / UNKNOWN Y | USER_CERTIFIED_POLICY / AMBIGUOUS N | Y |
| case3_substantive | No. A measurement may need to be compared against multiple genuinely different l | ONE_PURPOSE / ONE_PURPOSE Y | USER_CERTIFIED_POLICY / MODEL_CORRECTION N | Y |
| case4_purpose_scope | Yes, but only for Purpose A. Don't make that a general rule. | ONE_PURPOSE / ONE_PURPOSE Y | USER_CERTIFIED_POLICY / USER_CERTIFIED_POLICY Y | Y |
| case5_world_generalization | That's generally true, not just for this analysis. | WORLD / WORLD Y | USER_CERTIFIED_POLICY / USER_CERTIFIED_POLICY Y | Y |
| case6_uncertainty | I don't know what 9 means. Don't infer it from the pattern in the data. | ONE_SOURCE_VALUE / ONE_SOURCE_VALUE Y | USER_UNCERTAINTY / USER_UNCERTAINTY Y | Y |
| case7_policy | For this analysis, if the final permit and fact sheet disagree, use the final pe | ONE_PURPOSE / ONE_PURPOSE Y | USER_CERTIFIED_POLICY / USER_CERTIFIED_POLICY Y | Y |
| case8_external_fact | The final permit legally overrides the fact sheet. | ONE_RELATION_OR_VOCABULARY / ONE_PURPOSE N | USER_ASSERTED_EXTERNAL_FACT / USER_ASSERTED_EXTERNAL_FACT Y | Y |

## OBSERVED

### case1_bare_rejection

```json
{
  "utterance_understood": "No, that's wrong.",
  "candidate_scope": "ONE_RELATION_OR_VOCABULARY",
  "semantic_delta": "The expert rejects the draft interpretation that each FY2025 measurement has exactly one governing applicable numeric limit and that the unique_applicable_limit requirement is satisfied. The current measurement_limit_pair derivation (one pair per measurement via DMR-embedded limit keys) or the ONE cardinality policy misstates how many limits apply.",
  "epistemic_basis": "MODEL_CORRECTION",
  "remaining_ambiguity": "The expert did not say whether the error is the ONE-per-measurement cardinality rule, the DMR-embedded limit pairing shortcut, or the claim that uniqueness is satisfied on this fixture; they did not specify which limit(s) should govern when multiple permit_limit rows match permit, outfall, parameter, and monitoring period.",
  "primary_dry_run_id": "catalog_applicable_limits"
}
```

Candidates:

```json
[
  {
    "id": "catalog_applicable_limits",
    "interpretation": "Applicable limits should be enumerated from permit_limits by matching permit, outfall, parameter, and whether the monitoring period falls within each limit row's begin/end dates—not by trusting the DMR row's embedded limit_value_id and schedule_id as the sole applicable limit.",
    "scope": "ONE_RELATION_OR_VOCABULARY",
    "dry_run_id": "catalog_applicable_limits",
    "why_plausible": "ISSUES.md describes this catalog-match derivation; structured overlap shows most FY2025 measurements match multiple permit_limit rows under that rule, so forcing one pair via DMR keys would contradict staged or overlapping limit intervals."
  },
  {
    "id": "remove_forced_uniqueness",
    "interpretation": "The expert rejects requiring exactly one governing limit per measurement for purpose A; keep the current pairing logic but drop the ONE cardinality requirement and leave how many limits apply unresolved.",
    "scope": "ONE_PURPOSE",
    "dry_run_id": "remove_forced_uniqueness",
    "why_plausible": "ISSUES.md lists uncertainty about overlapping or staged intervals and catalog restatements; a bare rejection of the satisfied one-limit reading may target the cardinality policy rather than the join mechanics."
  },
  {
    "id": "dmr_embedded_limit_authoritative",
    "interpretation": "The expert rejects the catalog-match description of measurement_limit_pair, not the draft code: the applicable limit identity is the one carried on the DMR measurement row, and the error was mischaracterizing the construction as period-intersection catalog matching.",
    "scope": "ONE_RELATION_OR_VOCABULARY",
    "dry_run_id": null,
    "why_plausible": "construction.py already pairs via DMR-embedded keys while ISSUES.md incorrectly states catalog matching; a correction could mean the issue summary was wrong, not the durable draft."
  }
]
```

### case2_underspecified

```json
{
  "utterance_understood": "No, multiple limits can apply.",
  "candidate_scope": "ONE_PURPOSE",
  "semantic_delta": "The expert rejects the draft's Purpose A policy that each FY2025 measurement has exactly one applicable governing numeric limit (unique_applicable_limit_per_measurement with cardinality ONE). Multiple applicable limits per measurement are permitted for this analysis; the UNIQUE requirement should be removed. Whether measurement_limit_pair should also be re-derived to enumerate all temporally applicable permit-limit rows (not only the limit keys carried on each DMR row) is left to dry-run comparison.",
  "epistemic_basis": "USER_CERTIFIED_POLICY",
  "remaining_ambiguity": "The utterance clearly overturns the one-limit cardinality rule but does not say whether the DMR-embedded limit join is still the right materialization path, or whether pairs should be expanded by matching permit, feature, parameter, and monitoring-period overlap against all permit_limit schedule rows.",
  "primary_dry_run_id": "drop_unique_requirement"
}
```

Candidates:

```json
[
  {
    "id": "drop_unique_requirement",
    "interpretation": "Treat the expert's statement as a Purpose A policy correction only: remove the UNIQUE ONE requirement on measurement_limit_pair while keeping the existing DMR-embedded limit join (LIMIT_VALUE_ID + LIMIT_SET_SCHEDULE_ID from each measurement row).",
    "scope": "ONE_PURPOSE",
    "dry_run_id": "drop_unique_requirement",
    "why_plausible": "Narrowest change consistent with 'multiple limits can apply'—the analysis must not assert or enforce exactly one governing limit per measurement. The current join already materializes one pair per measurement on this fixture; dropping the cardinality rule avoids misrepresenting domain policy without restructuring relations."
  },
  {
    "id": "expand_applicable_limits",
    "interpretation": "Treat the expert's statement as requiring structural change: derive measurement_limit_pair by joining each FY2025 measurement to every permit_limit row with the same permit, feature, and parameter whose effective interval contains the monitoring period, and remove the UNIQUE ONE requirement.",
    "scope": "ONE_RELATION_OR_VOCABULARY",
    "dry_run_id": "expand_applicable_limits",
    "why_plausible": "ISSUES.md describes the pair relation as matching permit, outfall, parameter, and date overlap; the expert may mean that overlapping or staged schedule rows are separate applicable limits that should all appear as candidates rather than collapsing to the single limit referenced on the DMR row."
  }
]
```

### case3_substantive

```json
{
  "utterance_understood": "No. A measurement may need to be compared against multiple genuinely different limit types, but duplicate or restated catalog rows should still collapse.",
  "candidate_scope": "ONE_PURPOSE",
  "semantic_delta": "Reject the draft policy that each FY2025 measurement has exactly one applicable numeric limit. Derive measurement_limit_pair by matching each measurement to all permit-limit catalog rows that share permit, outfall, parameter, and an effective interval containing the monitoring period, then collapse duplicate or restated catalog rows before materialization. Replace the Purpose A uniqueness requirement from cardinality ONE per measurement to AT_LEAST_ONE per measurement, allowing multiple surviving pairs when they represent genuinely different limits.",
  "epistemic_basis": "USER_CERTIFIED_POLICY",
  "remaining_ambiguity": "The expert did not specify which structured fields distinguish genuinely different limits from restatements beyond limit type. The dry-run collapse key uses limit_type_code, limit_id, limit_value_standard_units, limit_value_qualifier_code, and statistical_base_type_code; narrower keys (e.g., limit_value_id only) or broader keys may be intended. It is also unresolved whether multiple limits sharing the same limit_type_code but differing in numeric value or limit_id should all remain applicable, or whether downstream per-measurement comparison requirements should be re-scoped to each measurement–limit pair.",
  "primary_dry_run_id": "multi_applicable_limits"
}
```

Candidates:

```json
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
```

### case4_purpose_scope

```json
{
  "utterance_understood": "Yes, but only for Purpose A. Don't make that a general rule.",
  "candidate_scope": "ONE_PURPOSE",
  "semantic_delta": "Confirm that after collapsing duplicate or restated permit-limit catalog rows, a FY2025 measurement may be compared against multiple applicable limits even when they share the same limit type code. Derive measurement_limit_pair by matching each measurement to every permit-limit row sharing permit, outfall, parameter, and an effective interval containing the monitoring period, collapse restated rows, and materialize all surviving pairs. Change the Purpose A unique_applicable_limit_per_measurement requirement from cardinality ONE to AT_LEAST_ONE per measurement. Do not generalize this multiplicity policy beyond Purpose A—leave purposes B and C without an analogous applicability cap, and do not restate it as a WORLD-mode rule.",
  "epistemic_basis": "USER_CERTIFIED_POLICY",
  "remaining_ambiguity": "The expert did not specify which structured fields define duplicate or restated catalog rows; the dry run collapses on limit_type_code, limit_id, limit_value_standard_units, limit_value_qualifier_code, and statistical_base_type_code. It remains unresolved whether downstream per-measurement comparison requirements (numeric value, operator, qualifier, statistical base) should stay scoped per measurement or be re-scoped per measurement–limit pair when multiple limits survive.",
  "primary_dry_run_id": "multi_applicable_limits"
}
```

### case5_world_generalization

```json
{
  "utterance_understood": "That's generally true, not just for this analysis.",
  "candidate_scope": "WORLD",
  "semantic_delta": "Affirm the prior multi-limit reading—after collapsing duplicate or restated permit-limit catalog rows, a measurement may be governed by multiple applicable limits even when they share the same limit type code—and reject the Purpose-A-only scope restriction. Model general limit applicability at WORLD level: derive measurement_limit_pair by matching each FY2025 measurement to every permit-limit row sharing permit, outfall, parameter, and an effective interval containing the monitoring period, collapse restated rows, and materialize all surviving pairs with mode WORLD. Change unique_applicable_limit_per_measurement from cardinality ONE to AT_LEAST_ONE per measurement so multiple surviving pairs are expected, not a cardinality hole.",
  "epistemic_basis": "USER_CERTIFIED_POLICY",
  "remaining_ambiguity": "The expert did not specify which structured fields define duplicate or restated catalog rows; the dry run collapses on limit_type_code, limit_id, limit_value_standard_units, limit_value_qualifier_code, and statistical_base_type_code. It remains unresolved whether downstream per-measurement comparison requirements (numeric value, operator, qualifier, statistical base) should stay scoped per measurement or be re-scoped per measurement–limit pair when multiple limits survive.",
  "primary_dry_run_id": "world_multi_applicable_limits"
}
```

### case6_uncertainty

```json
{
  "utterance_understood": "I don't know what 9 means. Don't infer it from the pattern in the data.",
  "candidate_scope": "ONE_SOURCE_VALUE",
  "semantic_delta": "For NODI_CODE='9' on FY2025 no-numeric-result rows (36 cases), do not assign any missing-evidence semantics. The expert does not know what code 9 means, and forbids inferring its meaning from co-occurrence or distributional patterns in dmr_measurements.csv (e.g. alongside code C or other field combinations). The existing nodi_code_semantics requirement with known=[\"\"] already leaves code 9 UNINTERPRETED; no construction edit is required.",
  "epistemic_basis": "USER_UNCERTAINTY",
  "remaining_ambiguity": "What NODI code 9 establishes for missing-evidence classification remains unknown per the expert. The expert did not address NODI code C (150 cases) or whether C and 9 are interchangeable.",
  "primary_dry_run_id": null
}
```

### case7_policy

```json
{
  "utterance_understood": "For this analysis, if the final permit and fact sheet disagree, use the final permit.",
  "candidate_scope": "ONE_PURPOSE",
  "semantic_delta": "Certify an analysis policy (purposes B/C) that on disagreement between final_permit and fact_sheet narrative content, final_permit governs. Encode this as a PURPOSE-mode document_conflict_authority derivation grounded in the user utterance. Keep permit_document_text_not_available unresolved because narrative text is still absent from structured sources. Add document_authority_among_other_kinds as unresolved for statement_of_basis, reasonable_potential, minor_modification, part_ii_appendix, part_iv, and any other inventoried kinds not covered by the certified pair rule.",
  "epistemic_basis": "USER_CERTIFIED_POLICY",
  "remaining_ambiguity": "Narrative permit text is still unavailable, so disagreement cannot be evaluated from structured sources alone. Authority among document kinds other than final_permit versus fact_sheet remains unset. The user did not define what counts as disagreement or how other document kinds relate to final_permit when text is present.",
  "primary_dry_run_id": "final_permit_over_fact_sheet"
}
```

### case8_external_fact

```json
{
  "utterance_understood": "The final permit legally overrides the fact sheet.",
  "candidate_scope": "ONE_RELATION_OR_VOCABULARY",
  "semantic_delta": "Add a document_kind_precedence relation recording that final_permit legally takes precedence over fact_sheet when narrative permit conditions conflict. Keep permit_document_text_not_available unresolved because structured sources still lack document body text. Split the former document_authority uncertainty by adding a narrower unresolved item for precedence among other inventoried document kinds (statement_of_basis, reasonable_potential, minor_modification, appendices, etc.).",
  "epistemic_basis": "USER_ASSERTED_EXTERNAL_FACT",
  "remaining_ambiguity": "Narrative permit text remains unavailable in structured sources, so no conditions can be read from any inventoried document. Legal precedence among document kinds other than final_permit over fact_sheet is still unknown. It is unclear whether minor_modification or other gcc package documents outrank or defer to the final permit. The utterance does not specify whether fact_sheet text may still inform analysis when it does not conflict with the final permit.",
  "primary_dry_run_id": "legal_hierarchy_world"
}
```

Candidates:

```json
[
  {
    "id": "legal_hierarchy_world",
    "interpretation": "The user states a general legal fact about NPDES permit packages: on conflict, final_permit document_kind prevails over fact_sheet document_kind regardless of analytical purpose.",
    "scope": "ONE_RELATION_OR_VOCABULARY",
    "dry_run_id": "legal_hierarchy_world",
    "why_plausible": "The wording uses definite articles and 'legally overrides' without limiting the claim to one permit or to purposes B/C, and PRINCIPLES treat legal document hierarchy as meaning that would survive if the current purpose disappeared."
  },
  {
    "id": "purpose_policy_bc",
    "interpretation": "The user certifies an analysis policy for narrative-condition work under purposes B and C: when final_permit and fact_sheet would disagree, treat final_permit as authoritative; do not treat this as a purpose-independent world truth.",
    "scope": "ONE_PURPOSE",
    "dry_run_id": "purpose_policy_bc",
    "why_plausible": "Document authority only matters for purposes B/C in this draft, and PASS_TASK distinguishes analysis policy from outside-world claims; encoding the rule in PURPOSE mode keeps purpose A free of a legal hierarchy it does not use."
  }
]
```

## HYPOTHESIS

A structured proposal can sit behind unrestricted natural-language user speech without the user naming scope enums.
