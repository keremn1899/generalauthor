# Constructor v3

Experiment `diligence-constructor-v3`. Model: `Composer 2.5`. Diligence repair fixture only. Not a fourth-domain claim.

Labels: **MEASURED** = campaign or certified suite; **OBSERVED** = trial-level detail; **HYPOTHESIS** = interpretation not required by the numbers.

Sealed v1, v2, Probe A, Probe B, and post-v2 reports were not overwritten.

---

## Implementation delta

- `RoleSpec.semantic_identity` is the consumer ABI key. Surface role names may differ.
- `PurposeProjectionContract.field_sources` maps consumer fields to those identities.
- Default P5 is the Probe A A1 bounded single adjudicator: one candidate, one relation contract, one packet → disposition, grounding, `support_claim`.
- Admission is structural only (invalid disposition / missing grounding). No cue-list verifier.
- P8 is World → contract-driven normalize → deterministic project. No source reread.
- P3 is the existing v2 frontier generator. It was not redesigned.

## Architecture / dependency delta

See `research/semantic_integration/ARCHITECTURE.md`.

MEASURED: `constructor_v3/runtime/` imports none of `constructor_v2.runtime.verifier`, Probe A, or Probe B. Forbidden-import audit: `forbidden_hits=[]`.

## Kernel diff

MEASURED: v3 does not modify `taskview/`.

```
__init__.py        sha256:3dcc6f08802891678dd6045204c7f24a0f9b13551e6a07dac39e530e28099c4a
model.py           sha256:7221d90855bfe7e99ab65f38b49d9356a38fe8cdc0dd99753b62c23f4ba0aeff
store.py           sha256:fb3d3bbf90e6d149921c420636860db239d96af1b8580aa7af22d0ddddc884d7
agent_surface.py   sha256:3fad57102afa52ff659527cc4bb9fdb7753fe517338e6fe9a7f925f05909dfc9
```

## Contract schema delta

Added, because Probe B measured a participant miss of `counterparty` vs `counterparty_text`:

```
RoleSpec.semantic_identity
PurposeProjectionContract.field_sources[consumer_field] = {semantic_identity}
```

Not added: semantic-family runtime behavior, fuzzy role-name matching, new kernel primitives.

`semantic_family_hint` remains unused metadata.

## P5 simplification

Default path is A1. Removed from default: v2 cue-list verifier, critic, entailment decomposition, A4 proof-obligation gate, pairwise proof, multistep proof DSL.

Burden rule unchanged: SAME and DISTINCT require establishing evidence; otherwise UNRESOLVED.

MEASURED: structural admission changed 0 dispositions (`structural_changed=0` on all five trials). Verifier changed 0 (verifier absent).

## Normalization behavior

No LLM. Joins and projections keyed by `semantic_identity`.

Certified World plus morphisms (rename, role-surface, orientation, layout, epistemic split, invoice decomposition, name-overlap noise, and explicit `counterparty`→`counterparty_text` bind):

```
suite                         A  B  C  D  recovered  missed  false
certified                     ✓  ✓  ✓  ✓  7/7        0       0
rename                        ✓  ✓  ✓  ✓  7/7        0       0
role_surface                  ✓  ✓  ✓  ✓  7/7        0       0
orientation                   ✓  ✓  ✓  ✓  7/7        0       0
layout                        ✓  ✓  ✓  ✓  7/7        0       0
epistemic split               ✓  ✓  ✓  ✓  7/7        0       0
decompose                     ✓  ✓  ✓  ✓  7/7        0       0
noise                         ✓  ✓  ✓  ✓  7/7        0       0
counterparty_bind             ✓  ✓  ✓  ✓  7/7        0       0
```

MEASURED: certified-World projection remains exact. Unbound `counterparty` without `semantic_identity` still misses `contract_record` (negative control). T1 participant vocabulary used surface role `party` with `semantic_identity=counterparty_text` and recovered all seven consumer relations.

## Trial matrix

Five independent ordinary trials. Isolation leaks 0. Timeouts 0. LLM passes reported `Composer 2.5`. P8 is the deterministic projector.

```
                     T1  T2  T3  T4  T5
p0                    ✓   ✓   ✓   ✓   ✓
p1                    ✓   ✗   ✓   ✓   ✓
p2                    ✓   ✓   ✓   ✓   ✓
p3                    ✓   ✗   ✓   ✓   ✓
p4                    ✓   ✓   ✓   ✓   ✓
p5                    ✗   ✓   ✓   ✓   ✓
p6                    ✓   ✓   ✓   ✓   ✓
p7                    ✓   ✓   ✓   ✓   ✓
P8 A/B/C              ✗   ✗   ✗   ✗   ✗
```

P5 pass requires zero unsupported closures on oracle pairs (T1 fails that gate). P8 pass requires exact A and B and C. D is reported separately.

OBSERVED: T2 P1 has zero PURPOSE-admitted relations (`n_purpose=0`). T2 P3 frontier recall 0.667.

## Semantic safety (P5)

Oracle-scored identity pairs (constructor-generated obligations ∩ 18 gold pairs):

```
trial  compared  exact   unsupported  under  polarity  SAME_recall  DISTINCT_recall  coverage  Delaware
T1     18        4/18    1            13     0         0.071         (see json)       0.188     UNRESOLVED
T2     12        6/12    0             6     0         0.400         0.400            0.400     UNRESOLVED
T3     32        28/32   0             4     0         0.857         (see json)       0.857     UNRESOLVED
T4     15        9/15    0             6     0         0.538         0.538            0.538     UNRESOLVED
T5     17        9/17    0             8     0         0.429         0.467            0.467     UNRESOLVED
```

Totals: compared 94; exact 56/94 = 0.596; unsupported 1; polarity 0.

MEASURED unsupported closure: T1 judged `DISTINCT` for
`(billing:Northbridge Analytics Inc., registry:2019-0008841)`.
Oracle: `UNRESOLVED`. Support claim cited Wyoming LLC vs Inc. form as contrary evidence.

MEASURED: billing↔Delaware registry `3840192` stayed `UNRESOLVED` on all five trials.

HYPOTHESIS: dropping the v2 cue verifier re-opened one negative-closure path on a live multi-jurisdiction packet. It is not a kernel failure.

## Frontier (P3)

P3 was not redesigned.

```
trial  recall   precision_vs_oracle  duplicate_ids  invalid  pass
T1     1.000    0.474                62             0        ✓
T2     0.667    0.500                 8             0        ✗
T3     0.889    0.390                92             0        ✓
T4     0.833    0.484                47             0        ✓
T5     0.944    0.472                50             0        ✓
```

MEASURED: 4/5 trials at recall ≥ 0.7, same pass rate as v2 AXIS D (4/5). OBSERVED: duplicate obligation ids are high; they are not invalid pairs. Do not tune P3 from T2 alone.

## Contract integrity

```
trial  role_type  invalid_disp  invalid_kinds  algebra  P2_ungrounded  P6_ungrounded
T1     0          0             0              0        0              0
T2     0          0             0              0        0             20
T3     0          0             0              0        0              0
T4     0          0             0              0        0              0
T5     0          0             0              0        0              0
```

MEASURED: P2 BASE grounding 5/5 at 100%. OBSERVED: T2 P6 World has 20 ungrounded assertions. Identifier-render failures 0. UNRESOLVED candidate-id loss 0.

The scorer also flags any surface role named `counterparty` that is not bound to `counterparty_text`. On T1/T3 that hit Purpose-C output roles, not the World contract header. OBSERVED scorer collision; not a missed `contract_record` mapping on those trials.

## Normalization (participant Worlds)

```
trial  recovered                         missed             false
T1     7/7                               []                 []
T2     7/7                               []                 []
T3     6/7                               [contract_active]  []
T4     7/7                               []                 []
T5     6/7                               [contract_active]  []
```

MEASURED: the Probe B participant `contract_record` miss is gone when `semantic_identity` is declared. T3/T5 miss `contract_active` (lifecycle not bound as `active`).

## End-to-end A/B/C/D

```
trial  A      B_exact  C      D      attribution
T1     False  False    False  False  adjudication_under_closure; semantic_fact_failure
T2     False  False    False  False  adjudication_under_closure; frontier_failure; semantic_fact_failure
T3     True   False    False  True   adjudication_under_closure
T4     False  False    False  False  adjudication_under_closure; semantic_fact_failure
T5     False  False    False  False  adjudication_under_closure; semantic_fact_failure
```

P8 source rereads: 0 (deterministic projector).

Do not collapse these into one score. Ordinary A/B/C remain inexact on 4/5 trials. T3 A and D are exact; B/C are not.

HYPOTHESIS: T1/T2/T5 missing all seven Purpose A invoices is under-closure of billed↔contract SAME, as in v2, not a projector identifier bug.

## Grounding / isolation

MEASURED: isolation leaks 0; oracle files were not readable from the sandbox; P8 source reads 0; P2 ungrounded 0; T2 P6 ungrounded 20.

## Comparison to v2

```
                         v2 AXIS D                         v3 ordinary
P0/P2/P4/P6/P7           5/5                              5/5
P1                       5/5                              4/5 (T2 n_purpose=0)
P3                       4/5                              4/5 (T2 recall 0.667)
P5 unsupported           0                               1 (T1)
P8 A/B/C exact            0/5                              0/5 (T3 A exact, B/C not)
identifier-render        0                               0
certified A/B/C/D        exact                              exact
participant contract_record  Probe B miss 5/5            recovered when identity declared
```

## Comparison to Probe A/B

Probe A A1: risk 0, SAME recall 0.457, coverage 0.467, exact 0.578. v3 default P5 is that adjudicator. Ordinary-trial exact 0.596 is not an A1 replication (different candidate set, batched constructor P5, not 18 frozen packets × 5 isolated calls). Do not claim v3 beat A1.

Probe B: certified exact; participant miss was unbound `counterparty`. v3 binds that explicitly. Certified morphisms remain exact. Family hints were not used.

## Architectural audit

1. Can experimental adjudication strategies be removed without changing foundational semantics? **Yes.** They are not imported by `taskview/` or `constructor_v3/runtime/`.
2. Does foundational/kernel code import experiment-specific code? **No.**
3. Can a new adjudicator be substituted through a small stable interface? **Yes.** Replace the P5 prompt and `admit_workspace`. World semantics unchanged.
4. Can a new normalizer be substituted through a small stable interface? **Yes.** `normalize_world(...)` → canonical tables consumed by `project_tables`.
5. Can constructor vocabulary change without consumer programs depending on relation names? **Yes, if `semantic_identity` is declared.** T1 `party` → `counterparty_text` recovered `contract_record`. Unbound `counterparty` does not.
6. Foundational: TaskView Referent, named typed n-ary Relation, Derivation, grounding, open-world UNRESOLVED, World vs purpose lifetime, mechanical-before-semantic.
7. Experimentally motivated and replaceable: Probe A A2–A6, v2 cue verifier, semantic-family hints, alternative evidence selectors.
8. Abstractions added: `semantic_identity` and `field_sources`. Required by the measured Probe B miss. No ontology layer, proof language, agent orchestration, or family runtime.

## Recommendation

`NOT_READY`

Blocking mechanisms:

1. **Unsupported semantic closure (T1 P5).** One oracle-`UNRESOLVED` pair closed `DISTINCT` (`billing:Northbridge Analytics Inc.` vs `registry:2019-0008841`). v2 AXIS D had zero ordinary unsupported closures. Untouched-domain work should not start while the default A1 path can still emit negative closure on that class of packet.

Not blocking the increment, but not hidden:

- Ordinary P8 A/B/C still inexact (under-closure). Not a projector/identifier regression.
- T2 P1 missing PURPOSE relations; T2 P3 recall 0.667; T2 P6 20 ungrounded assertions.
- T3/T5 `contract_active` not recovered when constructors omit the `active` identity.

MEASURED: this is a diligence development increment. Do not treat as a fourth-domain result.

Campaign finished `2026-09-02T21:31:47Z`. Report frozen after scoring. Stop.
