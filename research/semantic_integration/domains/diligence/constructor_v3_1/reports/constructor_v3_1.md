# Constructor v3.1

Experiment `diligence-constructor-v3-1`. Model: `composer-2.5`. Diligence hardening increment on frozen v3. Not a fourth domain.

Labels: **MEASURED** = campaign, micro-benchmark, or certified suite; **OBSERVED** = trial-level detail; **HYPOTHESIS** = interpretation.

Sealed v1, v2, Probe A, Probe B, post-v2, and Constructor v3 reports were not overwritten.

## Implementation delta

- H1: DISTINCT-only negative-closure gate after structural admission. SAME and UNRESOLVED are not gated. Fail-closed to UNRESOLVED.
- H2: constructor-runtime `validate_provenance()` after P6. TaskView still accepts empty grounding; v3.1 rejects that World as invalid.
- H3: ABI completeness (`SATISFIED` / `UNSATISFIED` / `AMBIGUOUS`) after vocabulary and before projection. Unsatisfied/ambiguous purposes are `INCOMPLETE_PURPOSE`, not silent projection.
- Default P5 remains the Probe A A1 bounded single adjudicator.
- P3 is unchanged. Kernel / TaskView unchanged.

## Kernel diff

MEASURED: v3.1 does not modify `taskview/`. Fingerprints match frozen v3:

```
{
  "__init__.py": "sha256:3dcc6f08802891678dd6045204c7f24a0f9b13551e6a07dac39e530e28099c4a",
  "model.py": "sha256:7221d90855bfe7e99ab65f38b49d9356a38fe8cdc0dd99753b62c23f4ba0aeff",
  "store.py": "sha256:fb3d3bbf90e6d149921c420636860db239d96af1b8580aa7af22d0ddddc884d7",
  "agent_surface.py": "sha256:3fad57102afa52ff659527cc4bb9fdb7753fe517338e6fe9a7f925f05909dfc9"
}
```

## Architecture / dependency audit

See `research/semantic_integration/ARCHITECTURE.md`.

- Negative-closure gate: runtime semantic safety, isolated in `runtime/negative_closure.py`. Foundational code does not import it.
- Provenance invariant: constructor-runtime `validate_provenance()` after P6 World commit.
- ABI completeness: constructor-runtime check of required consumer identities before projection.

Forbidden-import audit: {'forbidden_hits': [], 'ok': True}

## H1 negative-closure micro-benchmark

Frozen packets only. Baseline A1 DISTINCT vs A1 + gate. Packets were not regenerated.

```
{
  "n": 5,
  "unsupported_distinct_baseline": 1,
  "unsupported_distinct_gated": 0,
  "distinct_recall_baseline": 1.0,
  "distinct_recall_gated": 1.0,
  "unresolved_preservation_gated": 1.0,
  "distinct_downgraded": 1,
  "correct_distinct_downgraded": 0,
  "finished_at": "2026-09-02T22:31:25.600674+00:00"
}
```

MEASURED: unsupported DISTINCT baseline 1 → gated 0. DISTINCT recall 1.0 → 1.0. Correct DISTINCT downgraded 0. UNRESOLVED preservation 1.0.
OBSERVED: the v3 T1 Northbridge/Wyoming packet downgraded DISTINCT → UNRESOLVED. Probe A id-15 and id-16 retained SUPPORTED_DISTINCT.
MEASURED: SAME was not an input to the gate in this micro-benchmark.

Ordinary-trial gate (not used to tune): gate_ran 4/1/4/2/4. gate_downgraded 2/1/0/0/0. All three downgrades were non-oracle `registry:2019-0008841` ↔ `registry:3840192` pairs. No oracle-DISTINCT pair was downgraded.
MEASURED: the v3 T1 failing pair `billing:Northbridge Analytics Inc.` ↔ `registry:2019-0008841` is `UNRESOLVED` on all five ordinary trials. Oracle: `UNRESOLVED`. Delaware `3840192` stayed `UNRESOLVED` on all five.

## H2 grounding root cause

MEASURED cause **A**: P6 admission path bypassed grounding validation.

v3 T2 P6 World had 105 assertions, 20 ungrounded, all `origin=ASSERTED` (18 `identity_judgment`, 2 `invoice_contract_association`). P2 of the same trial had 0 ungrounded. TaskView `assert_tuple(..., grounding=())` permits empty grounding. The scorer correctly counted them ungrounded. Not B (missing derivation provenance), not C (dropped during pass transition), not D (scorer bug).

Enforcement is constructor-runtime after P6, not a kernel change.

## H2 grounding regression tests

Deterministic: ungrounded `assert_tuple` fails `validate_provenance()`. Grounded SOURCE assertion passes. P6 score requires `ungrounded_count=0`.

## H3 ABI completeness behavior

Required identities: invoice_id, billed_name, amount, currency, period, status, contract_id, counterparty_text, active, clause_kind, left, right, disposition.
Unbound `active` → `UNSATISFIED` and `INCOMPLETE_PURPOSE`. No fuzzy repair. No semantic-family inference.

## Negative controls

1. Unbound required semantic identity → ABI completeness failure (deterministic).
2. Attempted ungrounded World assertion → `validate_provenance()` failure (deterministic).
3. Misleading attribute mismatch with no exclusion proof → DISTINCT downgraded (H1 micro v3-T1 packet).
4. Certified valid DISTINCT evidence → DISTINCT retained (H1 micro id-15, id-16).

## Trial matrix

```
       p0    p1    p2    p3    p4    p5    p6    p7    p8
T1   ✓  ✓  ✓  ✓  ✓  ✓  ✓  ✓  ✗
T2   ✓  ✓  ✓  ✓  ✓  ✓  ✓  ✓  ✗
T3   ✓  ✓  ✓  ✓  ✓  ✓  ✓  ✓  ✗
T4   ✓  ✓  ✓  ✓  ✓  ✓  ✓  ✓  ✗
T5   ✓  ✓  ✓  ✓  ✓  ✓  ✓  ✓  ✗
```

P8 pass requires exact A and B and C and ABI ok. D and D_WORLD_ONLY (deterministic projector, sources absent from the P8 path) are reported separately.

## Semantic safety (P5)

```
trial compared exact unsupported under polarity SAME_recall DISTINCT_recall coverage Delaware gate
T1   36 6/36 0 30 0 0.0 0.5 0.0625 UNRESOLVED gate_ran=4 gate_down=2
T2   16 13/16 0 3 0 0.7857142857142857 None 0.7857142857142857 UNRESOLVED gate_ran=1 gate_down=1
T3   18 6/18 0 12 0 0.14285714285714285 1.0 0.25 UNRESOLVED gate_ran=4 gate_down=0
T4   17 9/17 0 8 0 0.42857142857142855 1.0 0.4666666666666667 UNRESOLVED gate_ran=2 gate_down=0
T5   18 12/18 0 6 0 0.5714285714285714 1.0 0.625 UNRESOLVED gate_ran=4 gate_down=0
```

## Grounding / provenance integrity

- T1: P2_ungrounded=0 P6_ungrounded=0 P6_pass=True
- T2: P2_ungrounded=0 P6_ungrounded=0 P6_pass=True
- T3: P2_ungrounded=0 P6_ungrounded=0 P6_pass=True
- T4: P2_ungrounded=0 P6_ungrounded=0 P6_pass=True
- T5: P2_ungrounded=0 P6_ungrounded=0 P6_pass=True

## Contract integrity

- T1: n_purpose=4 counterparty_unbound=['commercial_dependency'] role_type=0 invalid_disp=0 kinds=0 axis_b_ungrounded=0
- T2: n_purpose=2 counterparty_unbound=['commercial_dependency_judgment'] role_type=0 invalid_disp=0 kinds=0 axis_b_ungrounded=0
- T3: n_purpose=3 counterparty_unbound=[] role_type=0 invalid_disp=0 kinds=0 axis_b_ungrounded=0
- T4: n_purpose=6 counterparty_unbound=['commercial_dependency_row'] role_type=0 invalid_disp=0 kinds=0 axis_b_ungrounded=0
- T5: n_purpose=2 counterparty_unbound=[] role_type=0 invalid_disp=0 kinds=0 axis_b_ungrounded=0

## ABI completeness

```
T1   required=13 satisfied=13 unsatisfied=[] ambiguous=[] false=[] dup=[{'field': 'contract_id', 'locations': ['contract.contract_id', 'commercial_dependency.contract_id']}, {'field': 'disposition', 'locations': ['contract_in_force.disposition', 'clause_presence.disposition', 'identity_judgment.disposition', 'invoice_contract_association.disposition']}, {'field': 'invoice_id', 'locations': ['invoice.invoice_id', 'open_invoice.invoice_id']}, {'field': 'status', 'locations': ['invoice.status', 'commercial_dependency.status']}] ok=True
T2   required=13 satisfied=13 unsatisfied=[] ambiguous=[] false=[] dup=[{'field': 'disposition', 'locations': ['identity_judgment.disposition', 'invoice_contract_association.disposition']}, {'field': 'invoice_id', 'locations': ['source_invoice.invoice_id', 'open_invoice.invoice_id']}, {'field': 'left', 'locations': ['identity_judgment.left', 'identity_link_candidate.left']}, {'field': 'right', 'locations': ['identity_judgment.right', 'identity_link_candidate.right']}, {'field': 'status', 'locations': ['source_invoice.status', 'commercial_dependency_judgment.status']}] ok=True
T3   required=13 satisfied=13 unsatisfied=[] ambiguous=[] false=[] dup=[{'field': 'disposition', 'locations': ['identity_judgment.disposition', 'clause_kind_judgment.disposition', 'contractual_exposure_invoice.disposition']}, {'field': 'left', 'locations': ['identity_judgment.left', 'reconciliation_link.left']}, {'field': 'right', 'locations': ['identity_judgment.right', 'reconciliation_link.right']}, {'field': 'status', 'locations': ['invoice_record.status', 'commercial_dependency_assessment.status']}] ok=True
T4   required=13 satisfied=13 unsatisfied=[] ambiguous=[] false=[] dup=[{'field': 'clause_kind', 'locations': ['clause_kind_present.clause_kind', 'acquisition_relevant_clause.clause_kind', 'commercial_dependency_obligations.clause_kind']}, {'field': 'contract_id', 'locations': ['contract_record.contract_id', 'commercial_dependency_row.contract_id']}, {'field': 'disposition', 'locations': ['clause_kind_present.disposition', 'identity_judgment.disposition', 'governing_contract_link.disposition', 'mechanical_identity_allowance.disposition', 'purpose_b_required_link.disposition']}, {'field': 'invoice_id', 'locations': ['invoice_record.invoice_id', 'open_invoice.invoice_id', 'commercial_dependency_open_invoices.invoice_id']}, {'field': 'left', 'locations': ['identity_judgment.left', 'mechanical_identity_allowance.left', 'purpose_b_required_link.left']}, {'field': 'right', 'locations': ['identity_judgment.right', 'mechanical_identity_allowance.right', 'purpose_b_required_link.right']}, {'field': 'status', 'locations': ['invoice_record.status', 'commercial_dependency_row.status']}] ok=True
T5   required=13 satisfied=13 unsatisfied=[] ambiguous=[] false=[] dup=[{'field': 'amount', 'locations': ['invoice_record.amount', 'purpose_a_qualifying_invoice.amount']}, {'field': 'billed_name', 'locations': ['invoice_record.billed_name', 'purpose_a_qualifying_invoice.billed_name']}, {'field': 'clause_kind', 'locations': ['clause_occurrence.kind', 'purpose_c_dependency_row.clause_kind']}, {'field': 'contract_id', 'locations': ['contract_document.contract_id', 'purpose_a_qualifying_invoice.contract_id', 'purpose_c_dependency_row.contract_id']}, {'field': 'currency', 'locations': ['invoice_record.currency', 'purpose_a_qualifying_invoice.currency']}, {'field': 'invoice_id', 'locations': ['invoice_record.invoice_id', 'open_invoice.invoice_id', 'purpose_a_qualifying_invoice.invoice_id']}, {'field': 'period', 'locations': ['invoice_record.period', 'purpose_a_qualifying_invoice.period']}, {'field': 'status', 'locations': ['invoice_record.status', 'open_invoice.status', 'purpose_a_qualifying_invoice.status', 'purpose_c_dependency_row.status']}] ok=True
```

## Normalization

- T1: recovered=['invoice_record', 'contract_record', 'contract_active', 'identity_judgment', 'crm_record', 'registry_record'] missed=['contract_clause_kind'] false=[]
- T2: recovered=['invoice_record', 'contract_record', 'contract_active', 'contract_clause_kind', 'identity_judgment', 'crm_record', 'registry_record'] missed=[] false=[]
- T3: recovered=['invoice_record', 'contract_record', 'identity_judgment', 'crm_record', 'registry_record'] missed=['contract_active', 'contract_clause_kind'] false=[]

OBSERVED: T3 ABI still marks `active` SATISFIED (identity declared). The consumer `contract_active` table was not recovered from World. That is a World/normalization miss with an explicit ABI bind, not the v3 omitted-binding class. T1 missed `contract_clause_kind` the same way.
- T4: recovered=['invoice_record', 'contract_record', 'contract_active', 'contract_clause_kind', 'identity_judgment', 'crm_record', 'registry_record'] missed=[] false=[]
- T5: recovered=['invoice_record', 'contract_record', 'contract_active', 'contract_clause_kind', 'identity_judgment', 'crm_record', 'registry_record'] missed=[] false=[]

## Frontier (P3)

- T1: recall=1.0 precision=0.47368421052631576 dup=101 invalid=0 pass=True
- T2: recall=0.8888888888888888 precision=0.34782608695652173 dup=50 invalid=0 pass=True
- T3: recall=1.0 precision=0.47368421052631576 dup=125 invalid=0 pass=True
- T4: recall=0.9444444444444444 precision=0.5862068965517241 dup=58 invalid=0 pass=True
- T5: recall=1.0 precision=0.47368421052631576 dup=53 invalid=0 pass=True

## End-to-end A/B/C/D

```
T1   A=False B=False C=False D=False attr=['semantic_under_closure'] norm_miss=['contract_clause_kind']
T2   A=False B=False C=False D=False attr=['semantic_under_closure'] norm_miss=[]
T3   A=False B=False C=False D=False attr=['semantic_under_closure'] norm_miss=['contract_active', 'contract_clause_kind']
T4   A=False B=False C=False D=False attr=['semantic_under_closure'] norm_miss=[]
T5   A=False B=False C=False D=False attr=['semantic_under_closure'] norm_miss=[]
```

D_WORLD_ONLY: P8 is the deterministic projector on World; sources are not reread. Ordinary D exact: 0/5 (monitored). Certified-World D: exact.

P8 source rereads: [0, 0, 0, 0, 0]
Isolation leaks: []
Timeouts: []
Identifier-render failures: 0. UNRESOLVED candidate-id loss: 0.

## Failure attribution

- T1: ['semantic_under_closure']
- T2: ['semantic_under_closure']
- T3: ['semantic_under_closure']
- T4: ['semantic_under_closure']
- T5: ['semantic_under_closure']

## Comparison to v3

v3 blocking: 1 unsupported DISTINCT (T1). v3 T2 P6 ungrounded 20. v3 T3/T5 missed `contract_active` without compiler error.

v3.1 ordinary: unsupported closure 0; P6 ungrounded 0; all 13 required identities SATISFIED on all five trials; certified exact; P8 source rereads 0; identifier/epistemic regressions 0.

Monitored, not blocking: ordinary A/B/C/D inexact 5/5 (semantic under-closure); T1 SAME recall 0.0; T1 DISTINCT recall 0.5 (`crm:HEL-441` ↔ `registry:11847299` left UNRESOLVED by A1, not by the gate); P3 duplicates remain high; T3 `contract_active` table still missing after ABI bind.

## Architectural audit

1. Experimental strategies removable? **Yes.** Default runtime does not import Probe A/B or the v2 cue verifier.
2. Foundational/kernel import experiment code? **No.** Kernel fingerprints above; runtime audit ok=True.
3. New adjudicator through a small interface? **Yes.** P5 prompt + `admit_workspace`. Gate is DISTINCT-only.
4. New normalizer through a small interface? **Yes.** `normalize_world` → canonical tables.
5. Constructor vocabulary without consumer name dependence? **Yes, if semantic_identity is declared.** Missing required identities fail ABI completeness.
6. Foundational: TaskView Referent / Relation / Derivation, grounding, open-world UNRESOLVED, World vs purpose lifetime.
7. Experimentally motivated: DISTINCT gate (v3 T1), provenance check (v3 T2), ABI completeness (v3 omitted `active`).
8. New kernel abstractions? **None.** `semantic_identity` and `field_sources` remain the v3 ABI. Gate/provenance/ABI are constructor-runtime.

## Recommendation

`READY_FOR_UNTOUCHED_DOMAIN`

Blocking mechanisms: none

## Required direct answers

1. Did the negative-closure gate eliminate the v3 unsupported DISTINCT failure class? **Yes.** MEASURED micro-benchmark unsupported DISTINCT gated=0. Ordinary-trial unsupported closures=0.
2. How many correct DISTINCT judgments did it downgrade? **0** in the frozen micro-benchmark. Ordinary trials: also **0** oracle-DISTINCT downgrades. Three DISTINCT proposals were downgraded; none were oracle DISTINCT.
3. Was SAME behavior changed at all? **No.** The gate does not run on SAME. Admission never upgrades UNRESOLVED.
4. What exactly caused the 20 ungrounded P6 assertions in v3 T2? **Cause A.** P6 called TaskView `assert_tuple` for identity/association BASE facts with empty `grounding`. TaskView permits that. The scorer counted them correctly.
5. Can an ungrounded durable World assertion now be admitted by any normal runtime path? **No as a valid World.** TaskView can still serialize empty grounding (kernel unchanged). `validate_provenance()` rejects it; P6 fails.
6. Are all required consumer semantic fields now checked before projection? **Yes.**
7. Do omitted bindings fail explicitly rather than becoming downstream projection misses? **Yes.** Status `UNSATISFIED`/`AMBIGUOUS` yields `INCOMPLETE_PURPOSE`.
8. Did certified normalization remain exact? **True.**
9. Did any new abstraction enter the semantic kernel? **No.**
10. Are all v3 experimental strategies still removable from the default runtime? **Yes.** Audit ok=True.
11. What known semantic capability limitation remains? **SAME under-closure (T1 SAME recall 0.0) and ordinary A/B/C/D inexactness. P3 was not redesigned; duplicate obligation ids remain high. A constructor may still fail to materialize a declared identity as a recovered consumer table (T3 `contract_active`). Incomplete purpose via explicit UNRESOLVED is allowed.**
12. `READY_FOR_UNTOUCHED_DOMAIN`

MEASURED: diligence development increment only. Do not treat as a fourth-domain result.

Written 2026-09-03T00:10:30.978477+00:00
Campaign: 2026-09-02T23:52:55.727201+00:00
