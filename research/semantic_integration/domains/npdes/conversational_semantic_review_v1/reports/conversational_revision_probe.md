# Conversational revision (Microprobe 3)

Research copies of sealed T5 `construction.py`. Deterministic reruns via the frozen Python-spine runner.

## MEASURED

### H1

| step | kind | host epistemic | intended epistemic | host scope | turns | changed | rerun ok | generalization |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H1_acceptance_unique | ACCEPTANCE | USER_CERTIFIED_POLICY | USER_CERTIFIED_POLICY | general_world | 2 | True | True | OVERGENERALIZATION |
| H1_uncertainty_nodi | UNCERTAINTY | USER_UNCERTAINTY | USER_UNCERTAINTY | one_source_value | 2 | True | True | UNRESOLVED |

Baseline rerun ok=True groups=8 instances=535

### H2

| step | kind | host epistemic | intended epistemic | host scope | turns | changed | rerun ok | generalization |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H2_correction_comments | CORRECTION | MODEL_CORRECTION | MODEL_CORRECTION | one_relation | 2 | True | True | APPROPRIATE_REUSABLE_RULE |
| H2_qualification_when | QUALIFICATION | MODEL_CORRECTION | USER_CERTIFIED_POLICY | one_relation | 2 | True | True | APPROPRIATE_REUSABLE_RULE |

Baseline rerun ok=True groups=8 instances=535

### H3

| step | kind | host epistemic | intended epistemic | host scope | turns | changed | rerun ok | generalization |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H3_bare_no | AMBIGUOUS_REJECTION | USER_CERTIFIED_POLICY | MODEL_CORRECTION | one_purpose | 2 | True | True | APPROPRIATE_REUSABLE_RULE |
| H3_document_policy | CORRECTION | USER_CERTIFIED_POLICY | USER_CERTIFIED_POLICY | one_relation | 2 | True | True | APPROPRIATE_REUSABLE_RULE |

Baseline rerun ok=True groups=8 instances=535

## OBSERVED

All six MP3 deterministic reruns ok=true (Composer 2.5).
H1 NODI: groups 8→10; codes remain UNINTERPRETED; extra unresolved for 9 and C. Uncertainty preserved.
H2: groups stayed 8; three comment families remained separate.
H3 document: policy that final permit would outrank fact sheet *if text existed* was recorded without ranking from filenames.
H3_bare_no: the proxy did **not** emit the frozen sentence 'No, that's wrong.' It produced a long uniqueness correction. The host compiled that reply (removed uniqueness; pairs 824→2768) and did not write CLARIFY.md. The ambiguity-localization stress test is therefore proxy-contaminated and inconclusive.
See semantic_deltas.md for hole-group and requirement-name diffs. Epistemic labels are the host's INTERPRETATION.json, compared to frozen intended kinds.

## HYPOTHESIS

Unrestricted natural-language feedback can compile into scoped construction edits if the host keeps policy, uncertainty, and source-grounded state distinct.
