# Review: document_authority obligation

## Parent disposition

**parent_status: REFINED** (not independently admitted)

The parent question — *what do inventoried permit documents establish, and which document governs if they disagree?* — is too coarse. It conflates document-role establishment with inter-document precedence. Workspace evidence supports mechanically partitionable children by `document_kind` and incorporation pattern. Different partitions have different answers, but that is refinement, not parent-level UNRESOLVED.

## Evidence summary

### Supported (source-established, corpus-local)

1. **Issued permit governing corpus** (`document_kind=final_permit`, n=3): Cover pages authorize discharge only under named Parts "hereof" (GCC/Aztec Parts I–III; Farmington Parts I–IV).

2. **Incorporated appendices** (`part_ii_appendix`, `part_iv`, n=3): Issued permits cross-reference "Appendix A of Part II of this permit" and Farmington Part IV "hereof"; adjunct files are not standalone authorization.

3. **Supporting package material** (`fact_sheet`, `statement_of_basis`, `reasonable_potential`, n=5): Text frames draft/proposed rationale, administrative record, or calculation appendices; Aztec statement_of_basis explicitly defers final effluent limitations to the draft permit.

4. **Filename/kind not hierarchy** (n=12, negative): Farmington `statement_of_basis` header reads "FACT SHEET"; no workspace text ranks `document_kind` values for precedence.

### Refuted

- Filename kind hierarchy as binding authority.
- All twelve files co-equal binding authorization.

### Residual UNRESOLVED

- **minor_modification** (n=1, GCC NM0000116): Part I authorization text parallels `final_permit` Part I, but no workspace incorporation or supersession cross-reference links the files.

### Withheld generalizations

- Global NPDES document-kind precedence (LEVEL_3_GENERAL, UNVERIFIED_PROPOSAL).
- Automatic minor-modification incorporation from Part I text overlap.

## Partition check

| Child | Rule | Count |
|-------|------|-------|
| issued_permit_governing_corpus | `document_kind == final_permit` | 3 |
| incorporated_appendix_authority | `document_kind in (part_ii_appendix, part_iv)` | 3 |
| supporting_package_non_governing | `document_kind in (fact_sheet, statement_of_basis, reasonable_potential)` | 5 |
| filename_kind_not_authority | all entries (negative) | 12 |
| minor_modification_standalone_authority | `document_kind == minor_modification` | 1 |

Partition complete (3+3+5+1=12), no overlap among positive role partitions. `filename_kind_not_authority` is a corpus-wide negative test, not a competing positive partition.

## Dry-run construction deltas

Four ADMIT_DISPOSABLE children have `dry_run/<child_id>/construction.py` copies adding `permit_document_authority` with partition-specific `authority_role` values:

- `ISSUED_GOVERNING_CORPUS`
- `INCORPORATED_BY_REFERENCE`
- `SUPPORTING_EXPLANATORY`
- `KIND_LABEL_ONLY`

Root `construction.py` is unchanged per PASS_TASK.md.

## Relation to Purposes B and C

This packet resolves **which document corpus governs**, not every narrative condition inside permit Parts. Supporting documents may still contain condition-relevant facts (e.g., discharge-occurrence triggers) that must be read from governing permit Parts. The residual `minor_modification` file blocks full closure for GCC NM0000116 package authority.

## Prior packet alignment

PRIOR_PACKET.json candidate interpretations are confirmed with one addition: `minor_modification_incorporated` remains unresolved. No contradictory evidence found.
