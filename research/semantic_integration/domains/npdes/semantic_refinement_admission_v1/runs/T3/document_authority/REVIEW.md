# Review: document_authority obligation

## Parent disposition

**parent_status: REFINED**

The parent question — *without ranking from filenames, what do inventoried permit documents establish, and which document governs if they disagree?* — is too coarse to admit as a single World proposition. Evidence shows five mechanically distinct `document_kind` partitions with different authority roles. The parent is not independently admitted and not independently unresolved; five child questions supersede it.

## Evidence summary

Inspection of all twelve inventoried documents (via `sources/document_inventory.json` and `documents/` text extracts) supports:

1. **Issued final_permit (3 docs)** — Cover pages for GCC, Farmington, and Aztec authorize discharge under named internal parts "hereof." This establishes a self-defined governing corpus without using filename kind as hierarchy.

2. **Incorporated parts (3 docs)** — `part_ii_appendix` and `part_iv` files are referenced from issued final_permit text (Appendix A of Part II; Part IV hereof / Part IV of the permit). They are subordinate parts of the issued corpus, not independent authorization documents.

3. **Supporting draft documents (3 docs)** — Fact sheets and statements of basis use draft/proposed framing and defer enforceable limitations to the permit. Farmington `statement_of_basis.txt` opens with a FACT SHEET header despite inventory `document_kind=statement_of_basis`, refuting filename-kind hierarchy.

4. **Calculation appendices (2 docs)** — Reasonable-potential files are WQBEL calculation workbooks. Aztec explicitly labels itself "APPENDIX A of FACT SHEET."

5. **Residual unresolved (1 doc)** — GCC `minor_modification.txt` contains Part I authorization language for NM0000116, but retrieved `final_permit.txt` text does not incorporate or rank it. Precedence for this pair remains UNRESOLVED.

## Refinement structure

| child_id | partition rule | count | disposition | admission |
|---|---|---:|---|---|
| issued_permit_self_defined_corpus | document_kind == final_permit | 3 | SUPPORTED_RESOLUTION | ADMIT_DISPOSABLE |
| incorporated_permit_parts | document_kind in (part_ii_appendix, part_iv) | 3 | SUPPORTED_RESOLUTION | ADMIT_DISPOSABLE |
| supporting_draft_not_standalone_authorization | document_kind in (fact_sheet, statement_of_basis) | 3 | SUPPORTED_NEGATIVE | ADMIT_DISPOSABLE |
| reasonable_potential_calculation_appendix | document_kind == reasonable_potential | 2 | SUPPORTED_NEGATIVE | ADMIT_DISPOSABLE |
| minor_modification_authority_unestablished | permit==NM0000116 and document_kind==minor_modification | 1 | UNRESOLVED | UNRESOLVED |

Partitions are complete (12/12), non-overlapping, and mechanically computable from `document_inventory.json` fields.

## Admission notes

- **Admitted (disposable):** Document-local and corpus-local (Level 1–2) authority roles grounded in workspace text.
- **Withheld:** WORLD-scope generalizations (e.g., "final_permit always governs supporting documents") — plausible from this inventory but not SOURCE_ESTABLISHED beyond these three permits.
- **Unresolved:** NM0000116 minor_modification vs final_permit precedence.

## Dry-run construction copies

Disposable semantic deltas applied under `dry_run/<child_id>/construction.py` for each ADMIT_DISPOSABLE child:

- `issued_permit_self_defined_corpus` — derives `issued_permit_governing_corpus`; narrows blanket unresolved to non-final_permit documents.
- `incorporated_permit_parts` — derives `incorporated_permit_part` for part_ii_appendix and part_iv.
- `supporting_draft_not_standalone_authorization` — derives `supporting_draft_document` for fact_sheet and statement_of_basis.
- `reasonable_potential_calculation_appendix` — derives `calculation_appendix_document` for reasonable_potential.

Root `construction.py` was not modified.

## Known limitations

- No explicit package-wide "in the event of conflict" clause was retrieved; functional precedence for most partitions comes from issued-permit self-definition and supporting-document deferral, not a named conflict rule.
- Resolving this obligation does not resolve every narrative monitoring condition for Purposes B and C; it only establishes which document corpus governs.
- GCC reasonable_potential lacks an explicit "Appendix A of FACT SHEET" label in retrieved text; subordination relies on document_kind plus calculation-workbook content.
