# Pass localization report

Experiment `diligence-pass-localization-v1`. Model requested: `composer-2.5`. Stream-json: `Composer 2.5`.
No constructor repairs. Frozen diligence fixture unchanged. Kernel unchanged.

Ordinary construction: 5 trials × P0–P8 completed. Isolation leaks: 0. Timeouts: 0.

## Failure matrix

```
                     T1  T2  T3  T4  T5
p0                    ✓  ✓  ✓  ✓  ✓
p1                    ✓  ✓  ✓  ✓  ✓
p2                    ✓  ✓  ✓  ✓  ✓
p3                    ✓  ✓  ✓  ✓  ✓
p4                    ✓  ✓  ✓  ✓  ✓
p5                    ✓  ✗  ✗  ✓  ✗
p6                    ✓  ✓  ✓  ✓  ✓
p7                    ✓  ✓  ✓  ✓  ✓
P8 A/B/C              ✓✗✗  ✓✗✗  ✓✗✗  ✓✗✗  ✓✗✗
```

Delaware Inc (`billing:Northbridge Analytics Inc.` ↔ `registry:3840192`): {'T1': 'UNRESOLVED', 'T2': 'SAME_ENTITY', 'T3': 'SAME_ENTITY', 'T4': 'UNRESOLVED', 'T5': 'SAME_ENTITY'}

## Answers

1. **Consistently correct passes:** P0 intention, P1 vocabulary, P2 mechanical (token recovery + 100% BASE grounding, no early identity closure), P3 frontier (scorer pass: recall ≥ 0.7), P4 evidence packets, P6 admission, P7 derivation *spec/script presence*. P8 purpose A also 5/5.

2. **Passes accounting for most errors:** P5 identity adjudication (3/5 fail: T2/T3/T5 Delaware `SAME_ENTITY`) and P8 B/C export (0/5). B/C fail even on T1 and T4 where P5 is exact on compared oracle pairs, so those output failures are not solely P5.

3. **Vocabulary errors:** rare. P1 5/5. No purpose-output names admitted as WORLD.

4. **Frontier-generation errors:** uncommon on the scorer threshold. P3 5/5. Residual misses include Helion Industrial DISTINCT pairs on some trials (`crm:HEL-441`–`registry:11847299`, `registry:11847201`–`registry:11847299`).

5. **Evidence packets when adjudication fails:** P4 5/5; required oracle pairs that were generated had packets. Failures `['T2', 'T3', 'T5']` are P4-pass / P5-fail: retrieval looks sufficient, adjudication still over-committed Delaware.

6. **Adjudication with sufficient evidence:** yes. T2/T3/T5 packets existed; Delaware was still `SAME_ENTITY`. T1/T4 correctly left it `UNRESOLVED`.

7. **Incorrect semantic commitments vs downstream failure:** Intervention 1 (oracle identity in `05_dispositions.json`, **participant** P7 script rerun) keeps A passing; C never becomes exact; B becomes exact only on T2. Delaware-only counterfactual does not flip B/C pass/fail. Identity overcommitment is real and localizable, but B/C exact-match failures are dominated by export shape (left/right orientation, extra transitive links, `billing:` vs `crm:` counterparties, extra `auto_renewal`/`rolling_term` kinds compiled into World).

8. **Derivation on a correct World:** Intervention 3 (evaluator-certified World + gold derive) yields A/B/C exact on all five trials. Intervention 2 (gold derive against **participant** sqlite schema) does not compute A — participant relation names differ from the certified schema, so that cell does not isolate P7. Certified-P7 LLM diagnostic: T1 A=True B=True C=True; T2 A=True B=True C=True; T3 A=True B=True C=True; T4 A=True B=True C=True; T5 A=True B=True C=True.

9. **WORLD/PURPOSE admission:** stable. P6 5/5. No `purpose_a`/`purpose_b`/`purpose_c` WORLD leakage.

10. **D_WORLD_ONLY:** sources physically absent; source rereads empty; isolation held; model Composer 2.5. Exact canonical **fail** because IDs were emitted as `invoice:INV-1002` / `contract:MSA-…` instead of `INV-1002` / `MSA-…`. The three cases are otherwise the held-out set (Helion, Oakfield, Meridian; NBA excluded). Prefix-normalized pass: **True**.

11. **Deterministic validators that would have prevented observed failures:** (a) identity: notes-stated UNRESOLVED must not become SAME_ENTITY; (b) export: purpose B identifier orientation and required DISTINCT pairs; (c) purpose C: counterparty must use declared `crm:` form; obligation_kinds must be the declared set, not every extracted term clause; (d) grounding already held. Clause-kind over-extraction (`auto_renewal_term` on Helion, `rolling_term` on NBA in T1 World) is a mechanical/semantic typing error that a clause-kind validator against explicit contract wording could catch.

12. **Still requiring model intelligence:** bounded identity adjudication (Delaware/Wyoming) even with `commercial_notes` in the packet; deciding SAME vs UNRESOLVED from prose. Export/schema validators would have caught B/C exact failures without more inference.

## Causal interventions (not constructor successes)

| Trial | I1 correct P5 + participant derive | I2 gold derive on participant sqlite | I3 certified World+derive | Delaware → UNRESOLVED |
|---|---|---|---|---|
| T1 | A✓ B✗ C✗ | A✗ B✗ C✗ | A✓ B✓ C✓ | A✓ B✗ C✗ |
| T2 | A✓ B✓ C✗ | A✗ B✗ C✗ | A✓ B✓ C✓ | A✓ B✗ C✗ |
| T3 | A✓ B✗ C✗ | A✗ B✗ C✗ | A✓ B✓ C✓ | A✓ B✗ C✗ |
| T4 | A✓ B✗ C✗ | A✗ B✗ C✗ | A✓ B✓ C✓ | A✓ B✗ C✗ |
| T5 | A✓ B✗ C✗ | A✗ B✗ C✗ | A✓ B✓ C✓ | A✓ B✗ C✗ |

I2 is an intervention-harness miss on schema, not a finding that gold P7 fails a certified World.

## MEASURED

- New kernel primitive: no.
- Ordinary P8 A: 5/5. B: 0/5. C: 0/5. Zero P8 source rereads.
- P5 Delaware UNRESOLVED: T1, T4. SAME_ENTITY: T2, T3, T5.
- D_WORLD_ONLY exact: False. Prefix-normalized: True. Sources present: False.
- Certified-P7 LLM on evaluator World: A/B/C exact 5/5. Isolation leaks 0.
- Isolation leaks ordinary + D: 0.

## OBSERVED

The first-domain hypothesis that B fails from Delaware over-assertion is only partly right. That over-assertion occurs in 3/5 trials **and** B/C still fail when it does not. Purpose A is robust to identity residual. Purpose C exact-match is sensitive to identifier form and extra clause kinds already in World. D was computable from the frozen prior World without sources; the remaining miss is identifier prefixing.

## HYPOTHESIS

On this fixture, the constructor’s fragile pass is P5 identity, and the exact-output fragile pass is P7/P8 export/policy over an otherwise usable World. Validators for unresolved-preservation, export schemas, and clause-kind minimality are justified here. This is repair evidence for this fixture, not third-domain generalization.
