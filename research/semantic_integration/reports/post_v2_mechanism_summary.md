# Post-v2 mechanism summary

Frozen from two independent probes. No rerun. Not Constructor v3.

Sources:

- Constructor v2: `domains/diligence/reports/constructor_v2_repair.md`
- Probe A: `domains/diligence/semantic_proof_benchmark_v1/reports/semantic_proof_benchmark.md`
- Probe B: `schema_normalization_v1/reports/schema_normalization.md`

A0 compared 180 judgments (10×18). A1–A6 compared 90 each (5×18). Probe B used the five frozen AXIS D Worlds and a certified World. Semantic-family hints were not run.

---

## 1. Can positive semantic closure be improved without reopening unsupported closure?

**MEASURED.** Every Probe A strategy, including unconstrained A1, had **unsupported closures = 0** and **semantic risk = 0**. SAME↔DISTINCT polarity errors were 0. A1 SAME recall **0.457** vs A0 **0.421**; exact **0.578** vs **0.55**. Coverage 0.467 vs 0.439.

**OBSERVED.** The lift is small. A1 still left 38/70 gold SAME as UNRESOLVED. A2–A6 did not beat A0 on SAME recall. A4’s obligation gate admitted almost nothing (coverage 0.033).

**HYPOTHESIS.** Zero unsupported closure is a stable property of bounded packets plus identity burden, not an artifact of the v2 cue list. Recovering the remaining SAME still needs better positive proof, not a looser closer.

---

## 2. Which semantic-proof strategy lies on the best observed risk–coverage frontier?

**MEASURED.** All finished strategies sit on the **risk = 0** line. Among them, **A1 single adjudicator** has the highest SAME recall and coverage.

```
Strategy           Risk   Coverage   SAME recall   Exact
A0 v2              0.000     0.439         0.421    0.550
A1 single          0.000     0.467         0.457    0.578
A2 critic          0.000     0.422         0.414    0.533
A3 entailment      0.000     0.400         0.371    0.511
A5 pairwise        0.000     0.389         0.357    0.500
A6 multistep       0.000     0.300         0.271    0.411
A4 proof           0.000     0.033         0.043    0.144
```

A0 incorrectly downgraded 35 correct SAME (cue verifier). A1 has 0 such downgrades because it has no verifier. A4 incorrectly downgraded 31.

**OBSERVED.** Extra proof machinery (critic, entailment, pairwise split, multi-step, explicit obligations) moved mass from SAME into UNRESOLVED. It did not catch a pool of unsupported closures, because A1 produced none to catch.

**HYPOTHESIS.** On this fixture the binding error is missed SAME, not false SAME. Second-stage critics therefore cannot improve the frontier unless the first stage starts over-closing.

---

## 3. Are relation contracts sufficient to normalize constructor-authored vocabularies?

**MEASURED.** On the **certified World**, yes: B0 recovered all seven consumer relations and A/B/C/D were exact. On the **five participant Worlds**, `contract_record` was missed 5/5. Normalized A/B/C/D remained inexact, matching the raw projector (also inexact).

**OBSERVED.** Participant contracts name the counterparty role `counterparty`; the consumer interface names it `counterparty_text`. Identity was recovered by disposition set, not by relation name. Invoice factored tables assembled when the `invoice` / `billed_name` roles matched.

**HYPOTHESIS.** Exact contracts suffice when role identity matches the consumer vocabulary. They are not sufficient when constructors pick synonymous role names. That is a contract-completeness gap, not a missing semantic-family type.

---

## 4. Which schema transformations are mechanically normalizable?

**MEASURED.** On certified W, `Program(Normalize(W)) == Program(Normalize(M(W)))` for all of:

- B1 table rename
- B2 role-surface rename with role identity preserved in the contract
- B3 orientation (physical columns swapped, roles declared)
- B4 physical layout
- B5 epistemic split (SAME/DISTINCT/UNRESOLVED tables)
- B6 vertical invoice decomposition + join-on-shared-role
- B7 irrelevant `name_overlap` noise (MATCH/NO_MATCH)

False mappings: 0. UNRESOLVED candidate IDs preserved. Identifier preservation true.

**OBSERVED.** These were controlled morphisms with attached contracts. They are not a survey of every constructor schema.

---

## 5. Where does normalization genuinely require additional semantics?

**MEASURED.** The only systematic miss on participant Worlds was **consumer field/role identity** (`counterparty` vs `counterparty_text`). Identity vs noise was already separated by disposition sets. Family hints were not required for B1–B7.

**OBSERVED.** Participant A/B/C/D inexactness after Normalize equals inexactness of the raw projector: World content (under-closed identity, missing clauses) is not a mapping problem.

**HYPOTHESIS.** The smallest missing distinction is a published consumer field binding (purpose `field_sources` or stable role ids), not NEAR / IDENTITY / CONTAINS / LEADS_TO / EXPRESSES.

---

## 6. Did semantic-family hints add measurable information, if tested?

**MEASURED.** Not tested. Probe B STOP: certified contracts were sufficient under the tested transformations, so the optional family condition was not run.

**OBSERVED.** B7 noise with similar left/right columns and non-identity dispositions was not folded into identity.

**HYPOTHESIS.** Family hints would not have repaired participant `contract_record` miss or AXIS D under-closure.

---

## 7. Which remaining issue requires model intelligence?

**MEASURED.** SAME under-closure on bounded packets: A0 81/140 gold SAME; A1 38/70. Oracle UNRESOLVED recall stayed 1.0 on A0–A3 and A5.

**OBSERVED.** Packets that mix a true SAME (CRM↔billing) with unresolved-registry language caused A1 to abstain on the commercial-layer SAME (e.g. NBA CRM↔billing). That is packet/proof scope, still a semantic decision.

**HYPOTHESIS.** Establishing SAME from establishing prose, without name-similarity, remains the model-owned remainder. No tested strategy recovered it in bulk.

---

## 8. Which remaining issue is deterministic compiler engineering?

**MEASURED.** Certified projection is already exact (Constructor v2 AXIS C; Probe B B0). Rename, orientation, physical layout, epistemic representation, and known vertical partitions compiled without an LLM.

**OBSERVED.** AXIS D P8 0/5 was not “the projector is an LLM.” It was constructor Worlds whose tables/roles do not match the consumer interface, plus missing SAME facts. Probe B separated those: mapping miss (`contract_record`) vs unrepaired facts (identity/clauses).

**HYPOTHESIS.** Constructor v3 compiler work is: (i) require role-to-consumer-field bindings in contracts; (ii) keep the deterministic projector; (iii) do not ask P8 to re-read sources.

---

## 9. What should enter Constructor v3?

**MEASURED inputs, not an implementation.**

Keep:

- Bounded packet adjudication (one candidate, one contract, one packet)
- Identity burden: SAME/DISTINCT need establishing evidence; UNRESOLVED is success
- Deterministic projector on a stable consumer interface
- Isolation; no hidden-oracle leakage

Add as compiler, not as World primitives:

- Relation contracts that bind roles to consumer field identity (or purpose field_sources)
- Normalization of constructor-authored tables into that interface (Probe B B0–B6 behavior)

Consider dropping or weakening:

- The v2 cue-list verifier, if A1’s zero-risk SAME lift is the desired operating point
- P8 as an LLM

Do not add in v3 on this evidence:

- Semantic-family World types
- A4-style obligation gates as the primary closer
- A fourth domain as a success claim

---

## 10. What should remain experimental?

**MEASURED.** A2–A6 did not improve the risk–coverage frontier. They stay experimental.

Remain out of product:

- Critic/verifier architecture search
- Evidence-entailment and multi-step proof DSLs
- Semantic-family hints
- RAW-vs-WORLD
- Untouched fourth-domain claims
- Prompt tuning on this fixture after seeing scores

---

## Combined scientific call

**MEASURED.** Two v2 leftovers were tested independently.

- Probe A: unsupported closure stayed 0; positive SAME improved only slightly (A1); extra proof structure reduced coverage.
- Probe B: contracts + role identity normalize certified Worlds through rename/orientation/layout/epistemic-split/decomposition/noise; constructor Worlds still miss `contract_record` and remain fact-inexact.

**OBSERVED.** Constructor v2’s safety repair holds under broader proof strategies. Full-constructor purpose exactness is still not a success.

**HYPOTHESIS.** Constructor v3, if started, is a **compiler/contract** increment plus the same bounded adjudicator—not a new semantic kernel, and not family types.

No inference was rerun for this summary.
