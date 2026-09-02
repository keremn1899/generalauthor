# Constructor v2 repair report

Experiment `diligence-constructor-v2-repair`. Model: `composer-2.5`. Kernel unchanged. semantic_family_hint has no v2 behavior.

This is a **diligence repair fixture**, not a new generalization experiment. One frozen v2 implementation was evaluated. Failures were recorded, not iterated.

## AXIS A — semantic adjudication reliability

10 isolated P5 trials on frozen identity packets. Fresh workspaces. Packets only.

```
unsupported closures: 0
exact disposition: 99 / 180 = 0.55
under-closure: 81
polarity SAME↔DISTINCT: 0
verifier changed: 35
correct closures downgraded: 35
confusion: {"DISTINCT": {"DISTINCT": 20}, "SAME_ENTITY": {"SAME_ENTITY": 59, "UNRESOLVED": 81}, "UNRESOLVED": {"UNRESOLVED": 20}}
```

Primary target: 0 unsupported closures.

## AXIS B — relation-contract integrity

Certified World + projected C:

```
role type: 0
invalid disposition: 0
invalid purpose kinds: 0
algebra: 0
ungrounded: 0
all zero: True
rejected: {"kinds": [], "world": []}
```

## AXIS C — certified-World projection (no sources)

```
A exact: True
B exact: True
C exact: True
D_WORLD_ONLY exact: True
all exact: True
source reads: 0
identifier preservation: True
```

## AXIS D — constructor non-regression

```
                     T1  T2  T3  T4  T5
p0                    ✓  ✓  ✓  ✓  ✓
p1                    ✓  ✓  ✓  ✓  ✓
p2                    ✓  ✓  ✓  ✓  ✓
p3                    ✓  ✓  ✓  ✗  ✓
p4                    ✓  ✓  ✓  ✓  ✓
p5                    ✗  ✗  ✗  ✗  ✗
p6                    ✓  ✓  ✓  ✓  ✓
p7                    ✓  ✓  ✓  ✓  ✓
P8 A/B/C              ✗✗✗  ✗✗✗  ✗✗✗  ✗✗✗  ✗✗✗
```

P5 (full constructor, admitted after R3):

```
           compared  exact  unsupported  under  polarity  Delaware
T1         18        10/18   0            8      0         UNRESOLVED
T2         18        10/18   0            8      0         UNRESOLVED
T3         13         5/13   0            8      0         UNRESOLVED
T4          7         2/7    0            5      0         UNRESOLVED
T5         18         5/18   0           10      3         UNRESOLVED
```

P8 on participant Worlds: 0/5 exact A/B/C. Identifier-render failures 0. UNRESOLVED candidate-id loss 0. Missing A rows are typically all seven expected invoices when billed↔contract SAME is absent from World.

Required non-regression: P0/P1/P2/P4/P6/P7 = 5/5. P3 = 4/5 (T4 recall 0.39). BASE grounding 5/5 at 100% ungrounded=0. Isolation leaks 0. Timeouts 0. Model Composer 2.5.

P5/P8 reported separately and not collapsed into one success number.

## Comparison to v1

```
                         v1                              v2
P5 unsupported closure    3 ordinary trial-closures     AXIS A 0; AXIS D 0
P5 exact disposition      0.9382716049382716                         AXIS A 0.55
A exact                   5/5 P8                    AXIS C True; AXIS D 0/5
B exact                   0/5 P8                    AXIS C True; AXIS D 0/5
C exact                   0/5 P8                    AXIS C True; AXIS D 0/5
D_WORLD_ONLY exact         False                         AXIS C True
invalid clause/kind      v1 P8 extras                     AXIS C projected kinds 0
identifier-render         D prefixes                        AXIS C D True
candidate-id loss         v1 not isolated                    AXIS C preserved True
REJECT→UNRESOLVED         v1 not isolated                    mapping explicit; identity REJECT→DISTINCT
UNRESOLVED candidate loss v1 not isolated                  AXIS C false
BASE grounding            100%                            certified ungrounded 0
kernel changes            no                              no
```

n_v1 ordinary = 5 trials; n_AXIS A = 10 packet trials. Do not overclaim statistical generality.

## Answers

1. **Did proof-carrying semantic adjudication reduce unsupported closure?** MEASURED: v1 ordinary P5 unsupported closures = 3; v2 AXIS A = 0; v2 AXIS D = 0. OBSERVED: see AXIS A audits (`initial_disposition`, `verifier_result`, `final_disposition`). HYPOTHESIS: the verifier blocks unresolved-preservation closures without resampling.

2. **P5 exact disposition accuracy?** MEASURED AXIS A: 0.55.

3. **How often did the verifier change a model disposition?** MEASURED AXIS A: 35.

4. **Were any correct closures incorrectly downgraded?** MEASURED AXIS A: 35.

5. **Did relation contracts reject invalid World/purpose semantics?** MEASURED AXIS B all_zero=True. Rejected assertions are listed, not dropped.

6. **Did certified-World projection produce exact A/B/C/D?** MEASURED: True.

7. **Were epistemic states preserved through projection?** MEASURED: candidate IDs preserved True; B exact True.

8. **Were identifiers rendered correctly without mutating World identity?** MEASURED AXIS C A/D exact; rendering is projection-only prefix strip.

9. **Did previously stable constructor passes regress?** MEASURED: P0/P1/P2/P4/P6/P7 5/5; P3 4/5 (T4 frontier recall 7/18). OBSERVED: P2 grounding 100% on all trials; leaks 0. HYPOTHESIS: T4 P3 is trial variance on frontier generation, not a kernel change.

10. **Remaining failure still requiring semantic intelligence?** MEASURED: AXIS A SAME under-closure 81/140; AXIS D P5 0/5 on the v1 pass scorer because under-closure (and T5 three SAME↔DISTINCT). OBSERVED: UNRESOLVED oracle pairs were 20/20 on AXIS A; Delaware stayed UNRESOLVED on all five AXIS D trials. HYPOTHESIS: establishing SAME from bounded prose still needs a model; the cue verifier can only block unsupported closure, not recover missed SAME.

11. **Remaining failure that is compiler/runtime engineering?** MEASURED: AXIS C A/B/C/D exact from certified World; AXIS D P8 0/5. OBSERVED: participant schemas still do not feed the projector the certified relation layout; P8 itself is no longer an LLM. HYPOTHESIS: exact purpose output on constructor Worlds is an export/schema-alignment problem once identity is admitted.

12. **Ready for an untouched fourth-domain test?** MEASURED: no. OBSERVED: unsupported closure is repaired on this fixture; exact constructor P8 and SAME recall are not. HYPOTHESIS: a fourth domain would confound repair with new vocabulary.

## Scientific status

May establish: repair effectiveness on diligence; mechanism-level improvement; non-regression of stable passes.

May NOT establish: new domain generality; arbitrary-domain reliability.

## Stop

No fourth domain. No RAW-vs-WORLD. No kernel changes. No semantic-family behavior. No further repair iteration in this campaign.
