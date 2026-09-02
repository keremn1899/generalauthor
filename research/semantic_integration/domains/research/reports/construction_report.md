# PRE_REPAIR_CONSTRUCTOR_BASELINE

Third-domain blind semantic-construction replication.
Experiment `research-purpose-driven-construction-v1`.
This report is the frozen pre-repair baseline. Do not overwrite or regenerate it. Diligence-motivated constructor repairs must not be applied retroactively to this campaign.

## Fingerprints

| Item | Value |
|---|---|
| Label | `PRE_REPAIR_CONSTRUCTOR_BASELINE` |
| Experiment | `research-purpose-driven-construction-v1` |
| Constructor version | `pre-repair-diligence-equivalent-v1` |
| Model requested | `composer-2.5` |
| Stream-json reported | `Composer 2.5` (A/B/C, D, and D_WORLD_ONLY) |
| Adapter | `cursor-agent-bwrap-isolated-constructor-research-v1` |
| Manifest | `sha256:92db01dc96b94f99a982606bb8b1550936fa63c798413c227773ffb02180e54d` |
| Kernel | `sha256:0a0d9f7a730c6c78f40ba96b9791c1ace017cc29393403ca2cffeb9267797bfb` |
| Constructor agent | `sha256:29c10a869b5b6943d96713e35846e9cbfcfa073bfe6420d059ce5002e4c21844` |
| Prompt README | `sha256:317d6e83629a1bfe3cc66e658b767c14d3f902011bc4a19817ad163c2d9ca7b9` |
| Prompt CONSTRUCTION_TASK | `sha256:5b6883fb18838aa09f3b884f681e868fdc86b3924bc4f2d150acded690734176` |
| A/B/C World | `sha256:dd413f9b30a35c8a377f79f0b246a57f1a7dfec531987d0f24a92acc2cfb03f0` |
| Isolation | bwrap tmpfs over repository, Cursor projects, sibling trials |

Constructor saw sources, visible purposes A/B/C, and the frozen TaskView kernel. It did not see expected outputs, designer annotations, purpose D, the BOM ontology, or the diligence ontology.

This is a construction-architecture baseline, not a RAW-vs-WORLD programming campaign. The constructor was not modified after observing outputs.

---

## 1. Did the frozen kernel survive a third domain?

**MEASURED:** no new primitive was added. The constructor used Referent, named typed n-ary BASE relations, DERIVED relations, grounding, completeness-capable SQL, and explicit UNRESOLVED dispositions. Kernel counterexample: none.

Study identity, outcome correspondence, and measurement sufficiency were ordinary relations. Purpose filters and export tables were DERIVED, not kernel extensions.

---

## 2. What semantic vocabulary did the constructor independently discover?

Seventeen named relations. Names were invented by the constructor, not supplied.

WORLD (mechanical, constructor labels):

- `registered_primary_outcome`
- `publication_reported_primary`
- `publication_stated_registry_id`
- `dataset_stated_registry_link`
- `dataset_protocol_code` / `publication_protocol_code`
- `dataset_row_count` / `publication_n_analysed`
- `dataset_variable`
- `identity_candidate`
- `outcome_correspondence_candidate`

Semantic residual (constructor labeled PURPOSE, persisted as BASE in `world.sqlite`):

- `study_identity_judgment` (ACCEPT / REJECT / UNRESOLVED)
- `outcome_correspondence_judgment`
- `variable_sufficiency_judgment`

PURPOSE DERIVED export tables: `purpose_a_study`, `purpose_b_link`, `purpose_c_study`.

That is purpose-driven rather than a full scientific-research ontology. The discovered residual is study identity, outcome correspondence, and measurement/variable sufficiency — not BOM qualification/replacement, and not diligence counterparty identity as such.

---

## 3. What fraction of construction was mechanical?

**MEASURED:**

| Quantity | Count |
|---|---|
| Referents | 19 |
| Named relations | 17 |
| BASE assertions | 110 |
| Grounded BASE | 110 |
| Ungrounded BASE | 0 |
| Mechanical BASE tuples (non-judgment) | 84 |
| Semantic BASE tuples (judgments) | 26 |
| DERIVED assertions | 31 |
| Identity candidates | 12 |
| Exact stated registry-id joins | publication 4 + dataset 5 |

Mechanical share of BASE: **84/110 (76%)**. Semantic share of BASE: **26/110 (24%)**.

Deterministic joins used explicit registry identifiers with heterogeneous field names (`registry_id`, `trial_registration`, `registration`, `linked_registry`) and one protocol-code/n match (`NW-PULM-24`, n=148).

---

## 4. What was the residual semantic frontier?

**MEASURED:** 26 obligations in `world/obligations.json`. Evidence packets are one-line source pointers, not multi-document dossiers.

| Relation | ACCEPT | REJECT | UNRESOLVED |
|---|---|---|---|
| `study_identity_judgment` | 10 | 3 | 4 |
| `outcome_correspondence_judgment` | 3 | 1 | 0 |
| `variable_sufficiency_judgment` | 3 | 2 | 0 |

The actual residual is three-typed:

1. **Cross-authority study identity** — NORTHWIND RCT vs observational programme vs shared publication/dataset package. Four UNRESOLVED registry links preserved. Two registry rows correctly DISTINCT. MARLIN clinic audit correctly DISTINCT from the trial.
2. **Outcome correspondence** — HELIOS registered PSQI vs published sleep latency correctly REJECTED. CLEAR-HTN systolic/SBP and AURORA HbA1c/glycated haemoglobin correctly ACCEPTED despite non-identical wording.
3. **Measurement correspondence** — AURORA fasting glucose vs HbA1c REJECT; PINE screening TNSS vs 4-week outcome REJECT; CLEAR/HELIOS/MARLIN variables ACCEPT for the registered primary.

Missing from the frontier, relative to the hidden oracle: transitive publication–dataset SAME_STUDY for mechanically bound studies (CLEAR, AURORA, HELIOS, MARLIN), and MARLIN trial-paper vs audit DISTINCT. Those are omitted identity judgments, not kernel gaps.

NORTHWIND outcome correspondence was not separately judged; identity UNRESOLVED blocked a correspondence assertion. That is conservative, not a false ACCEPT.

---

## 5. Were evidence packets and assertions grounded?

**MEASURED:** 110/110 BASE assertions grounded. 141/141 assertions have assertion-level grounding. 19/19 referents grounded. Obligations cite source files and codebook lines.

No ungrounded persistent semantic assertion was observed in World.

---

## 6. Did A/B/C compute correctly?

Exact score against hidden canonical outputs:

| Purpose | Exact | Semantic cause of failure |
|---|---|---|
| A | **fail** | HELIOS World REJECT mapped to export `unresolved` instead of `not_traced`. NORTHWIND unresolved preserved but candidate `publication_id` dropped. CLEAR/AURORA/MARLIN asserted correctly. PINE `not_traced` correctly. |
| B | **fail** | Required UNRESOLVED NORTHWIND links present. DISTINCT not collapsed. Missing four transitive SAME_STUDY pub–dataset links and one MARLIN paper-vs-audit DISTINCT. |
| C | **fail** | AURORA insufficient, HELIOS ready, PINE insufficient, CLEAR/MARLIN ready: all correct. NORTHWIND status `unresolved` correct, but candidate `dataset_id` dropped to null. |

Ordinary Python/SQL was sufficient to emit purpose JSON from World (`derive_purposes.py`). Failures are derivation policy and incomplete identity closure, not missing kernel primitives.

Purpose A’s HELIOS error is **export mapping**, not a wrong World judgment: `outcome_correspondence_judgment` is REJECT with evidence that PSQI is not sleep latency.

---

## 7. Which constructor failures occurred?

Do not treat these as repair tickets. They are baseline error classes.

1. **Unresolved candidate identifiers dropped at export.** World stores UNRESOLVED NORTHWIND publication and dataset links. Purpose A/C/D JSON omit those identifiers.
2. **REJECT correspondence mapped to `unresolved` rather than `not_traced`.** Schema interpretation, after a correct semantic REJECT.
3. **Incomplete identity closure.** Registry–publication and registry–dataset ACCEPT were not compiled into publication–dataset SAME_STUDY except where no registry bind existed (NORTHWIND).
4. **WORLD/PURPOSE label vs persistence.** Identity, outcome, and measurement judgments were labeled PURPOSE but written into `world.sqlite` as BASE. Physically reusable; taxonomically over-conservative.
5. **Held-out D with sources added a spurious PINE `unresolved`.** D_WORLD_ONLY did not. Source-present D was slightly worse than World-only D.

No closed-world false DISTINCT on NORTHWIND. No global referent merge.

---

## 8. Was WORLD/PURPOSE admission sensible?

Directionally: source facts and mechanical candidates are WORLD; A/B/C export tables are PURPOSE DERIVED. No `answer_to_purpose_a(...)` World relation.

The three semantic judgment relations are independently meaningful (same-study, outcome correspondence, variable sufficiency) and were in fact reused by D without World mutation. Labeling them PURPOSE understates reuse. Persistence in World was the behavior that mattered.

Purpose-demanded discoveries physically present in World: the three judgment relations. Purpose outputs incorrectly promoted into World as BASE: none.

---

## 9. Did held-out D require additional World construction?

**MEASURED:** after A/B/C freeze, D was revealed. World SQLite bytes did not change (`sha256:dd413f9b…` before and after).

Incremental construction: 0 new WORLD relation types, 0 new mechanical construction, 0 new semantic relation types, 0 new semantic obligations, 0 new World assertions. New purpose-only state: `purpose_ir/d/output.json`.

D queried `world.sqlite` and purpose A/C files. It did not add World tables.

Exact D: **fail**. Matches for CLEAR, AURORA, and MARLIN are correct — including AURORA, which C marks insufficient. HELIOS correctly excluded. NORTHWIND unresolved preserved but IDs dropped. Extra PINE `unresolved` (should be omitted as an established non-match).

D is not A concatenated with C: AURORA is in D and not C-ready; HELIOS is C-ready and not in D. The constructor recovered that distinction for the matching cases.

---

## 10. Did D_WORLD_ONLY pass?

Environment: frozen World, purpose D, Python/SQL. Sources physically absent. World mutation: **false**. Isolation leaks: 0.

Exact: **fail** (NORTHWIND unresolved rows still omit candidate publication/dataset ids).

Behavioral: World was sufficient to compute the three matches and to exclude HELIOS and PINE without raw sources. D_WORLD_ONLY did **not** emit the spurious PINE row that source-present D emitted. The agent did not declare `insufficient_world`.

So: pre-D World is semantically sufficient for the unseen purpose’s matching/exclusion structure; export of unresolved candidate identifiers remains the failure.

---

## 11. What constructor weakness appears common with diligence?

- The hard residual is **cross-authority identity**, not kernel expressiveness.
- Unresolved identity can be preserved in World and then **mishandled at derivation/export**.
- Identity **closure is incomplete** (research: missing transitive SAME_STUDY; diligence: missing a DISTINCT CRM link / over-asserting a registry pair).
- Held-out D was already enabled by reusable World state with **no World mutation**.
- Grounding of BASE assertions was complete in both domains.
- WORLD/PURPOSE split is directionally right and locally sloppy.

---

## 12. What weakness appears domain-specific?

Research’s residual is not only identity. Outcome correspondence and measurement sufficiency appeared as first-class semantic obligations.

Domain-specific error: mapping an established outcome **REJECT** (HELIOS PSQI vs latency) onto purpose-schema `unresolved` instead of `not_traced`. Diligence had no analogue of registered-vs-reported endpoint switching.

Measurement sufficiency was comparatively reliable: AURORA/PINE insufficient and HELIOS ready were correct even though HELIOS publication correspondence failed at export.

NORTHWIND dropping candidate IDs while keeping status `unresolved` is the research-shaped form of “unresolved is a flag, not a reified candidate link.”

---

## 13. What does this imply about the pre-repair constructor architecture?

The frozen calculus hosted a third heterogeneous domain without a new primitive. Purpose-driven construction independently rediscovered a sparse vocabulary whose residual **did** change by domain:

| Domain | Observed residual |
|---|---|
| BOM | qualification / replacement semantics |
| diligence | cross-authority legal/commercial identity |
| research | study identity / outcome correspondence / measurement correspondence |

That pattern was not forced on the constructor. It is what this run produced.

The architecture compiles a reusable World that an unseen purpose can query. It does not yet reliably (a) close identity, (b) export unresolved candidates with their identifiers, or (c) map REJECT vs UNRESOLVED onto purpose schemas.

This baseline does **not** imply that prompt tuning would fix those classes, that World amortizes construction cost, or that arbitrary domains work.

---

## Isolation

A/B/C, D, and D_WORLD_ONLY: 0 repository Reads of hidden oracles. Preflight ok. Purpose D was absent from the A/B/C workspace. D_WORLD_ONLY contained no `study_registry.csv` or other source files.

---

## MEASURED

- New primitive: **no**.
- Grounding of BASE assertions: **110/110**.
- Semantic obligations: **26**.
- Purpose A exact: **no**. Purpose B exact: **no**. Purpose C exact: **no**.
- Purpose D exact: **no**. D World delta: **none**.
- D_WORLD_ONLY exact: **no**. World mutated: **no**. Isolation leaks: **0**.
- Model: Composer 2.5 on all three inference sessions.

## OBSERVED

- Composer 2.5 produced a TaskView World and a purpose-driven vocabulary without a gold ontology.
- Semantic residual naturally included study identity, outcome correspondence, and measurement correspondence.
- HELIOS outcome REJECT was a correct World judgment; A failed on export mapping.
- NORTHWIND UNRESOLVED was preserved in World and stripped of identifiers in purpose JSON.
- Held-out D reused World without mutation. D_WORLD_ONLY was slightly cleaner than source-present D.
- AURORA in D-and-not-C and HELIOS in C-and-not-D shows D was not a concatenation of A and C at the matching layer.

## HYPOTHESIS

- The frozen calculus can host at least three domains (BOM, diligence, research) without a new primitive.
- Domain changes the semantic residual while the construction architecture stays fixed.
- Pre-repair constructor failures cluster in identity closure and derivation/export of unresolved state, with domain-specific overlay in outcome/measurement correspondence.
- That does not imply the constructor is ready to repair from this report, nor that these error rates are stable across seeds.

---

## Stop

A/B/C construction, held-out D, D_WORLD_ONLY, and this report are frozen as `PRE_REPAIR_CONSTRUCTOR_BASELINE`. No constructor repairs. No prompt retuning. No additional retries. No new validators. No kernel primitive changes. No RAW-vs-WORLD programming. Hidden oracles were not exposed to the constructor.
