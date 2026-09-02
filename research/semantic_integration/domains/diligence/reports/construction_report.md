# Purpose-driven semantic compilation in a second domain

Experiment `diligence-purpose-driven-construction-v1`.
Model requested: `composer-2.5`. Stream-json reported: `Composer 2.5` for both A/B/C and D. Isolation: bwrap, repository hidden. Purpose D was sealed until the A/B/C World fingerprint `sha256:b7ca189ec402e2d178925fccca8255a66a22acc213dbaabaaf2e3f2fb8a8a45b`.

This is a construction-architecture test, not a RAW-vs-WORLD programming campaign.

Constructor saw sources, visible purposes A/B/C, and the frozen TaskView kernel. It did not see expected outputs, designer annotations, purpose D, or the BOM ontology.

---

## 1. Can the existing kernel represent this domain?

**MEASURED:** no new primitive was added. The constructor used Referent, named typed n-ary BASE relations, DERIVED relations, grounding, and completeness-capable SQL. Kernel counterexample: none.

Clause types, identity dispositions, invoices, and registry rows were ordinary relations. Purpose filters were PURPOSE DERIVED relations, not kernel extensions.

---

## 2. Smallest useful vocabulary?

The constructor invented 16 named relations: 11 WORLD, 5 PURPOSE.

WORLD covers source observations, mechanical candidates, contract clause/term kinds, and `identity_judgment`. PURPOSE holds acquisition-relevance, invoice–contract association, and the A/B/C export tables.

That is purpose-driven rather than a full commercial ontology. Some WORLD candidate relations (`crm_to_billing_candidate`, etc.) are scaffolding. Clause typing was labeled MECHANICAL because the constructor treated explicit contract wording as deterministic extraction; that is a classification choice, not a new primitive.

---

## 3. Mechanical compilation and bounded residual frontier?

**MEASURED:** 30 referents, 95 grounded BASE tuples, 0 ungrounded BASE assertions.

The residual semantic frontier was identity: 28 `identity_judgment` obligations. Dispositions in World: 25 SAME_ENTITY, 1 DISTINCT (`registry:11847201` vs `registry:11847299`), 2 UNRESOLVED (Northbridge Wyoming LLC and the CRM transitive of that pair).

The Delaware Inc registry row was incorrectly SAME_ENTITY. The notes required both Delaware Inc and Wyoming LLC to remain UNRESOLVED as contracting-party candidates.

---

## 4. World vs Purpose split?

**MEASURED:** Purpose A’s acquisition-relevance filter, A/B/C output tables, and invoice–contract association were classified PURPOSE. Identity and contract clauses were WORLD.

No `answer_to_purpose_a` World relation. Manual review: the split is directionally correct. `acquisition_relevant_clause` is a purpose policy over WORLD `contract_clause` tuples.

---

## 5. Held-out D?

After A/B/C freeze, D was revealed. The World SQLite bytes did not change.

D canonical output **exact pass** (INV-1002 Helion, INV-3002 Oakfield, INV-5001 Meridian). NBA open AR was correctly excluded: CoC termination and competitor-assignment prohibition without general assignment notice/consent.

**MEASURED incremental construction:** 0 new mechanical relations, 0 new semantic relations, 0 new semantic obligations. New purpose-only state: `purpose_ir/d/output.json`.

The D session queried `world.sqlite` and also reread contract markdown. World reuse was sufficient; source rereads were not required by missing World state.

---

## Computability A/B/C

| Purpose | Canonical exact | Notes |
|---|---|---|
| A | **pass** | 7 invoices; Vellum excluded |
| B | **fail** | Delaware Inc asserted SAME_ENTITY; CRM↔Helion Industrial DISTINCT link omitted (registry–registry DISTINCT present) |
| C | **fail** | NBA `unresolved` instead of `dependent`; counterparties emitted as `billing:*` not `crm:*` |

Ordinary Python/SQL was sufficient for A and for D. Downstream purpose JSON for A/C was derived from World tables (`derive_purposes.py`). D did not add World tables.

Target “0 raw source reads” after construction: A/B/C purpose export reads World, not CSV. The D agent still opened contract files.

---

## Isolation

A/B/C and D: 0 repository Reads of hidden oracles. Preflight ok. D was absent from the A/B/C workspace.

---

## MEASURED

- New primitive: **no**.
- Grounding of BASE assertions: **95/95**.
- Purpose A exact: **yes**. Purpose B exact: **no**. Purpose C exact: **no**. Purpose D exact: **yes**.
- D World delta: **none**.
- Isolation leaks: **0**.

## OBSERVED

- Composer 2.5 produced a TaskView World and a WORLD/PURPOSE split without being given an ontology.
- The hard residual was identity, not kernel expressiveness.
- Over-assertion of Northbridge↔Delaware Inc is a semantic error, not closed-world false (Wyoming LLC stayed UNRESOLVED).
- Purpose C treated unresolved registry identity as blocking commercial dependency even though billing–contract identity was asserted. That is a derivation policy mistake.
- Held-out D was already enabled by WORLD `contract_clause` assignment kinds plus open invoices.

## HYPOTHESIS

- The frozen calculus can host a second, non-BOM domain without a new primitive.
- Purpose-driven construction can produce reusable World state (identity, clause kinds, invoices) that a held-out purpose consumes with no World mutation.
- That does not imply the constructor reliably preserves unresolved identity, nor that this amortizes construction cost, nor that arbitrary domains work.

---

## Stop

A/B/C construction, held-out D, and this report are frozen. No RAW-vs-WORLD programming. No visualization. Kernel primitives were not modified.
