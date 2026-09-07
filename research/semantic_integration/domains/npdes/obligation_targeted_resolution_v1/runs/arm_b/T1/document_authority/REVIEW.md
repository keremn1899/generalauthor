# Adjudication Review: document_authority

## Investigated

Judged only the frozen `PACKET.json` under the constraints in `PASS_TASK_ADJUDICATE.md`. All eight retained snippets carry admissible workspace `source_id` paths under `documents/`. No corpus search, no CSV correlation, and no non-workspace snippets were used.

## Semantic question

Without ranking from filenames, what do inventoried permit documents establish, and which document governs if they disagree?

Purposes: **B**, **C**. Relation contract: narrative conditions require document text; filename kind is not hierarchy.

## Findings

### Supported resolution: `issued_permit_self_defined_corpus`

Workspace permit text establishes a functional authority structure:

1. **Issued permits self-define the binding corpus.** GCC and Farmington `final_permit.txt` cover pages authorize discharge only under named Parts I–III (GCC) or I–IV (Farmington) of the issued permit.
2. **Incorporation is by internal cross-reference.** GCC Part II incorporates Appendix A of Part II by reference, showing part appendices enter the governing corpus through permit text, not filename kind alone.
3. **Supporting package documents defer enforceable limits.** GCC `fact_sheet.txt` labels Section V as draft/proposed rationale; Aztec `statement_of_basis.txt` directs readers to the draft permit for effluent limitations; Aztec `reasonable_potential.txt` is an appendix to the fact sheet.
4. **Filename / inventory kind is not hierarchy.** Farmington `statement_of_basis.txt` opens with a FACT SHEET header despite inventory kind, refuting filename-kind precedence.

### Refuted interpretations

- **filename_kind_hierarchy** — refuted by Farmington header mismatch and draft/proposed framing in fact sheets and statements of basis.
- **all_documents_co_equal** — refuted by explicit deferral to the permit for limitations and draft/proposed framing.

### Partial limitation retained

- **explicit_conflict_clause_required** — no named “in the event of conflict” clause was found, but functional precedence still follows from issued-permit self-definition plus supporting-document deferral.

## Evidence supporting disposition

| Source | What it establishes |
|--------|---------------------|
| `documents/gcc/final_permit.txt` (cover) | Binding corpus = cover page + Parts I–III |
| `documents/farmington/final_permit.txt` (cover) | Binding corpus = cover page + Parts I–IV |
| `documents/gcc/final_permit.txt` (Part II) | Appendix incorporated by internal reference |
| `documents/gcc/fact_sheet.txt` | Draft/proposed explanatory content |
| `documents/aztec/statement_of_basis.txt` | Limitations deferred to permit |
| `documents/aztec/reasonable_potential.txt` | Calculation appendix, not authorization |
| `documents/farmington/statement_of_basis.txt` | Text contradicts kind-as-hierarchy |

Epistemic basis: **SOURCE_ESTABLISHED** (direct workspace document text). Disposition: **SUPPORTED_RESOLUTION**.

## Remaining uncertainty

From packet `known_limitations`:

- No explicit inter-document conflict clause across all file types.
- `documents/gcc/minor_modification.txt` incorporation into the issued permit is unestablished.
- Document authority is resolved; conditional monitoring facts in supporting narrative still require reading permit parts for full Purpose B/C resolution.
- `document_inventory.json` supplies kind labels only, not precedence metadata.

## Proposal (ADMIT_DISPOSABLE)

`dry_run/construction.py` adds:

- `DOCUMENT_AUTHORITY_ROLE_BY_KIND` — reusable mapping from inventory `document_kind` to authority role (not per-row judgments).
- `permit_document_authority` relation materialized from that mapping.
- Purpose requirements for `document_authority_role` and `document_conflict_precedence`.
- Replacement of blanket `permit_document_text_not_available` with narrower unresolved markers: unestablished kinds (e.g. `minor_modification`) and the fact that narrative conditions are not yet structured.

## What would change if admitted

- Purposes B and C would treat issued permits (and permit-referenced parts) as the governing enforceable corpus when package documents disagree.
- Supporting documents would be classified explanatory/calculatory rather than co-equal authorization.
- Downstream conditional obligations (discharge-dependent monitoring, comment-driven semantics) would still need permit-text extraction; authority resolution alone does not close those gaps.
