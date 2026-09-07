# Cases

Frozen utterances injected exactly. No proxy user. Not real-user usability evidence.

## MEASURED

| case | issue | disposition | scope | epistemic | dry-runs | mutated before accept | committed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| case1_bare_rejection | unique_applicable_limit | NEEDS_CLARIFICATION | ONE_RELATION_OR_VOCABULARY | MODEL_CORRECTION | 2 | N | N |
| case2_underspecified | unique_applicable_limit | NEEDS_CLARIFICATION | ONE_PURPOSE | USER_CERTIFIED_POLICY | 2 | N | N |
| case3_substantive | unique_applicable_limit | NEEDS_CLARIFICATION | ONE_PURPOSE | USER_CERTIFIED_POLICY | 2 | N | N |
| case4_purpose_scope | unique_applicable_limit | READY_FOR_ACCEPTANCE | ONE_PURPOSE | USER_CERTIFIED_POLICY | 1 | N | Y |
| case5_world_generalization | unique_applicable_limit | READY_FOR_ACCEPTANCE | WORLD | USER_CERTIFIED_POLICY | 1 | N | Y |
| case6_uncertainty | nodi_semantics | READY_FOR_ACCEPTANCE | ONE_SOURCE_VALUE | USER_UNCERTAINTY | 0 | N | N |
| case7_policy | document_authority | READY_FOR_ACCEPTANCE | ONE_PURPOSE | USER_CERTIFIED_POLICY | 1 | N | Y |
| case8_external_fact | document_authority | READY_FOR_ACCEPTANCE | ONE_RELATION_OR_VOCABULARY | USER_ASSERTED_EXTERNAL_FACT | 2 | N | Y |

## OBSERVED

### case1_bare_rejection

Injected utterance: `No, that's wrong.`

- understood: No, that's wrong.
- remaining_ambiguity: The expert did not say whether the error is the ONE-per-measurement cardinality rule, the DMR-embedded limit pairing shortcut, or the claim that uniqueness is satisfied on this fixture; they did not specify which limit(s) should govern when multiple permit_limit rows match permit, outfall, parameter, and monitoring period.
- decision reason: The expert rejected the draft's one-limit-per-measurement reading, but the rejection could mean changing how limits are paired to measurements, dropping the one-limit rule while keeping current pairing, or correcting a mischaracterization of the existing pairing logic. Dry runs show materially different row counts and hole profiles across these readings.

Clarification excerpt:

# Clarification needed: what is wrong about "one governing limit per measurement"?

You said the draft is wrong to treat each FY2025 measurement as having exactly one governing applicable numeric limit. That rejection is clear, but it could point in very different directions—and those directions produce very different results on this fixture.

## Where the disagreement sits

The draft currently builds **824** measurement–limit pairs (one per FY2025 measurement) by following the limit identity already carried on each DMR row (`LIMIT_VALUE_ID` and `LIMIT_SET_SCHEDULE_ID`). It then treats the "exactly one applicable limit per measurement" rule as **satisfied** on this data.

A separate issue summary describes pairing differently—as if each measurement were matched against all permit limit rows by permit, outfall, parameter, and whether the monitoring period falls inside each limit's effective dates. Under that catalog-style rule, most measurements would match **multiple** permit limit rows (overlapping or staged intervals), not one.

So the open question is not whether you disagree with the draft's conclusion—you already said you do—but **which part** you are rejecting.

## What would

### case2_underspecified

Injected utterance: `No, multiple limits can apply.`

- understood: No, multiple limits can apply.
- remaining_ambiguity: The utterance clearly overturns the one-limit cardinality rule but does not say whether the DMR-embedded limit join is still the right materialization path, or whether pairs should be expanded by matching permit, feature, parameter, and monitoring-period overlap against all permit_limit schedule rows.
- decision reason: The expert clearly rejects the draft policy that each FY2025 measurement has exactly one applicable governing limit. Both tested constructions remove that rule, but they disagree on how to decide which limit rows belong to each measurement: keep the DMR-referenced limit join (824 pairs, 342 numeric comparisons) or enumerate every temporally overlapping permit limit for the same permit, outfall, and parameter (4,076 pairs, 1,388 numeric comparisons). Those are materially different outcomes on this fixture.

Clarification excerpt:

You confirmed that a single FY2025 measurement can have more than one applicable discharge limit. We should stop treating “exactly one governing limit per measurement” as a policy for this analysis. That part is clear.

What is still open is how we decide which limit rows belong to each measurement.

The current draft links each measurement to the specific limit identifiers carried on that DMR row — the limit value and schedule IDs in the reporting data. On this dataset that yields **824** measurement–limit pairs, of which **342** have both a reported value and a numeric limit suitable for comparison.

Another reading of “multiple limits can apply” is that we should enumerate **every** permit limit row whose effective dates overlap the monitoring period for the same permit, outfall, and parameter — not just the limit the DMR row points at. On this dataset that would yield about **4,076** pairs and about **1,388** numeric comparison candidates — roughly five times as many relationships.

These are not the same analysis. They change how many measurement–limit relationships exist and how many numeric comparisons the construction considers, even though both versions drop the one-limit 

### case3_substantive

Injected utterance: `No. A measurement may need to be compared against multiple genuinely different limit types, but duplicate or restated catalog rows should still collapse.`

- understood: No. A measurement may need to be compared against multiple genuinely different limit types, but duplicate or restated catalog rows should still collapse.
- remaining_ambiguity: The expert did not specify which structured fields distinguish genuinely different limits from restatements beyond limit type. The dry-run collapse key uses limit_type_code, limit_id, limit_value_standard_units, limit_value_qualifier_code, and statistical_base_type_code; narrower keys (e.g., limit_value_id only) or broader keys may be intended. It is also unresolved whether multiple limits sharing the same limit_type_code but differing in numeric value or limit_id should all remain applicable, or whether downstream per-measurement comparison requirements should be re-scoped to each measurement–limit pair.
- decision reason: Your correction clearly rejects exactly-one applicable limit per measurement and requires collapsing duplicate catalog rows, but the phrase "multiple genuinely different limit types" supports two readings that the dry runs treat differently: allow multiple surviving limits per measurement without a per-type cap, versus allow multiplicity only across different limit types (at most one per type). After the same deduplication step, 692 FY2025 measurements still have multiple collapsed limits sharing the same limit type code; one reading leaves them as valid comparisons (535 total unresolved items, unchanged from baseline), while the other flags those 692 cases as unresolved multiplicity (1,919 total unresolved items, +1,384).

Clarification excerpt:

# Clarification needed: how many limits can apply to one measurement?

You said that a measurement may need to be compared against **multiple genuinely different limit types**, and that **duplicate or restated catalog rows should still collapse**. We took that as a correction to the current draft rule that forces exactly one applicable limit per FY2025 measurement.

Both ways we modeled your correction agree on the big structural shift: match each measurement to every permit-limit catalog row that shares permit, outfall, parameter, and an effective interval covering the monitoring period, collapse restated rows before pairing, and expand comparisons. On this dataset that raises measurement–limit pairs from **824 to 2,812** and numeric comparison candidates from **342 to 1,336**. All other unresolved items (monitoring frequency codes, pass/fail semantics, permit comments, and the rest) stay the same in both models—**535 unresolved items across 8 issue groups**.

Where the two readings diverge is what happens **after** deduplication, for measurements that still have more than one surviving limit.

## The sticking point

After collapsing restated catalog rows (using limit type, limit 

### case4_purpose_scope

Injected utterance: `Yes, but only for Purpose A. Don't make that a general rule.`

- understood: Yes, but only for Purpose A. Don't make that a general rule.
- remaining_ambiguity: The expert did not specify which structured fields define duplicate or restated catalog rows; the dry run collapses on limit_type_code, limit_id, limit_value_standard_units, limit_value_qualifier_code, and statistical_base_type_code. It remains unresolved whether downstream per-measurement comparison requirements (numeric value, operator, qualifier, statistical base) should stay scoped per measurement or be re-scoped per measurement–limit pair when multiple limits survive.
- decision reason: Your reply affirms the multi-limit reading from the prior clarification—after collapsing restated catalog rows, a FY2025 measurement may be compared against multiple applicable limits even when they share a limit type code—and restricts that policy to Purpose A only, not as a general WORLD rule. The sole dry run (multi_applicable_limits) matches this scope and produces the expected expansion in pairs and comparison candidates without adding new unresolved items.

Acceptance excerpt:

# Acceptance: multiple applicable limits for Purpose A

## What you mean

You are confirming the correction we asked about: after duplicate or restated permit-limit catalog rows are collapsed, a single FY2025 measurement may still be compared against **multiple applicable limits**, including cases where those limits share the same limit type code but differ in other fields (such as limit id, numeric value, or statistical base). You are **not** asking us to keep forcing exactly one governing limit per measurement.

You are also drawing a scope line: this multiplicity policy applies **only to Purpose A** (applicable discharge limits for Federal FY2025). It should **not** be generalized to Purposes B or C, and it should **not** be restated as a global WORLD-mode rule.

## Where it applies

- **Purpose A only** — evaluating which enforceable numeric discharge limits apply to FY2025 measurements and whether reported values exceed them.
- **Not** Purposes B or C, and **not** a cross-purpose or WORLD-level applicability cap.

## What rule would change

The Purpose A requirement `unique_applicable_limit_per_measurement` would change from **exactly one** applicable limit per measurement to 

### case5_world_generalization

Injected utterance: `That's generally true, not just for this analysis.`

- understood: That's generally true, not just for this analysis.
- remaining_ambiguity: The expert did not specify which structured fields define duplicate or restated catalog rows; the dry run collapses on limit_type_code, limit_id, limit_value_standard_units, limit_value_qualifier_code, and statistical_base_type_code. It remains unresolved whether downstream per-measurement comparison requirements (numeric value, operator, qualifier, statistical base) should stay scoped per measurement or be re-scoped per measurement–limit pair when multiple limits survive.
- decision reason: Your reply withdraws the Purpose-A-only scope line from the prior round and affirms that the multi-limit reading is generally true—not confined to this FY2025 analysis. The sole dry run (world_multi_applicable_limits) matches that reading: it models limit applicability at WORLD level, switches measurement_limit_pair to WORLD mode, and relaxes unique_applicable_limit_per_measurement to AT_LEAST_ONE. No competing dry-run interpretations with materially different counts are present.

Acceptance excerpt:

# Acceptance: multiple applicable limits as a general policy

## What you mean

You are affirming the multi-limit reading we previously clarified—after duplicate or restated permit-limit catalog rows are collapsed, a single measurement may still be governed by **multiple applicable limits**, including cases where those limits share the same limit type code but differ in other fields (such as limit id, numeric value, or statistical base). You are **not** asking us to force exactly one governing limit per measurement.

You are also withdrawing the earlier scope restriction. In your prior reply you said this policy should apply only to Purpose A and not be generalized. Your latest reply—“that’s generally true, not just for this analysis”—means the multiplicity policy is **general**, not limited to Purpose A or to this Federal FY2025 discharge-limit evaluation.

## Where it applies

- **WORLD level** — limit applicability is modeled as a general fact about how measurements relate to permit limits, not as a Purpose-A-only overlay.
- **All analyses** that depend on measurement–limit pairing and numeric comparison, including Purposes B and C and any future work beyond this dataset.
- The 

### case6_uncertainty

Injected utterance: `I don't know what 9 means. Don't infer it from the pattern in the data.`

- understood: I don't know what 9 means. Don't infer it from the pattern in the data.
- remaining_ambiguity: What NODI code 9 establishes for missing-evidence classification remains unknown per the expert. The expert did not address NODI code C (150 cases) or whether C and 9 are interchangeable.
- decision reason: The expert's statement is an epistemic constraint on NODI code 9: they do not know its meaning and forbid inferring it from data patterns. The draft construction already treats all non-empty NODI codes as UNINTERPRETED under nodi_code_semantics (known only for empty string), so no construction change is required and no plausible reading of the utterance would produce materially different hole counts or classifications for code 9.

Acceptance excerpt:

# Acceptance

## What you mean

You are saying that NODI code **9** has no established missing-evidence meaning that you can affirm, and you do not want anyone to guess its meaning by looking at how code 9 co-occurs with other fields in the measurements data (for example, alongside code C or particular parameter combinations). Your statement is uncertainty plus a prohibition on pattern-based inference—not a claim that 9 means any particular thing.

## Where this applies

This applies to **FY2025 rows with no numeric result** where `NODI_CODE='9'`. In the current data that is **36 cases** out of **186** total no-numeric-result rows (the other **150** carry code C, which you did not address in this utterance).

## What rule would change

**No rule change is needed.** The draft already requires interpretation for NODI codes and treats only the empty code as known. Code 9 therefore stays **UNINTERPRETED** under the `nodi_code_semantics` requirement—it is not assigned "no discharge," "not required," or any other missing-evidence classification, and nothing in the construction infers meaning from distributional patterns in the CSV.

## Measurable consequences from the dry run

The dry ru

### case7_policy

Injected utterance: `For this analysis, if the final permit and fact sheet disagree, use the final permit.`

- understood: For this analysis, if the final permit and fact sheet disagree, use the final permit.
- remaining_ambiguity: Narrative permit text is still unavailable, so disagreement cannot be evaluated from structured sources alone. Authority among document kinds other than final_permit versus fact_sheet remains unset. The user did not define what counts as disagreement or how other document kinds relate to final_permit when text is present.
- decision reason: The user utterance is a narrow, pairwise analysis policy: when final permit and fact sheet narrative content disagree, final permit governs. The dry run encodes exactly that pair rule as a certified purpose policy without over-scoping to other document kinds or pretending narrative text is available. Plausible alternative readings (universal final-permit supremacy, or treating the policy as resolving all document-authority gaps) are weaker given the wording and would not change current measurable outcomes because narrative text is still absent from structured sources.

Acceptance excerpt:

# Acceptance summary

## What you mean

For this analysis, you are certifying a document-authority policy for a specific pair of permit documents: if the **final permit** and **fact sheet** disagree, the **final permit** governs. You are not asserting that narrative permit text is now available, and you are not claiming a universal hierarchy among every document kind in the permit package.

## Where it applies

This policy applies to purposes **B** and **C** (narrative conditions and source authority) for the three permits in the current inventory. Only one permit package (NM0000116) actually contains both a final permit and a fact sheet; the other two permits have final permits but no fact sheet in the inventory.

The policy is scoped to **this analysis** — it is a certified analytical choice, not a claim that the outside world inherently ranks these documents this way.

## What rule changes

Compared with the baseline draft, the construction would add one certified conflict rule:

- **On disagreement between final permit and fact sheet → use the final permit.**

The baseline left all narrative document authority unresolved under a single “permit document text not available” item.

### case8_external_fact

Injected utterance: `The final permit legally overrides the fact sheet.`

- understood: The final permit legally overrides the fact sheet.
- remaining_ambiguity: Narrative permit text remains unavailable in structured sources, so no conditions can be read from any inventoried document. Legal precedence among document kinds other than final_permit over fact_sheet is still unknown. It is unclear whether minor_modification or other gcc package documents outrank or defer to the final permit. The utterance does not specify whether fact_sheet text may still inform analysis when it does not conflict with the final permit.
- decision reason: The user asserted a general legal precedence rule (final permit over fact sheet on conflict). Two plausible encodings were dry-run—one as a world-level legal fact and one as a purpose-specific analysis policy—and they produced identical measurable outcomes on this dataset: both added one document_kind_precedence row, both increased unresolved holes by one group and one instance (splitting other document-kind authority into permit_document_authority_other_kinds), and left all other hole counts unchanged. Because the interpretations did not diverge in consequence here, no clarification is required to choose between them; the world-level encoding matches the utterance's legal framing and the proposal's epistemic basis.

Acceptance excerpt:

# Acceptance summary

## What I think you mean

When narrative permit conditions in the **final permit** and the **fact sheet** disagree, the **final permit legally wins**. You are stating how NPDES permit-package documents relate in law—not asking us to treat a missing fact sheet as denied, and not claiming we already have the full text of either document in structured form.

## Where this applies

This is treated as a **general legal fact about permit packages**, not as a rule tied only to one analytical purpose. It would still mean the same thing even if we were asking a different compliance question tomorrow.

Document authority only matters in parts of the draft that read narrative permit conditions. The precedence rule is therefore relevant wherever those analyses run, but it does **not** by itself resolve any numeric limit comparison, monitoring schedule code, or pass/fail semantics.

## What rule would change

The construction would record that **final_permit takes precedence over fact_sheet** when their narrative conditions conflict.

The former broad “document authority” uncertainty would be **split**:

- **Still unresolved:** we lack narrative body text for inventoried p

## HYPOTHESIS

Exact frozen utterances isolate scope/ambiguity behavior that a proxy user previously contaminated.
