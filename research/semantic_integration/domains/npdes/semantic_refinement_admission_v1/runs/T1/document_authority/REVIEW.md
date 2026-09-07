# Review: document_authority

## Parent disposition

**parent_status: REFINED** — The coarse parent question ("what do inventoried permit documents establish, and which governs on disagreement?") conflates five mechanically distinct `document_kind` roles. Evidence supports different authority propositions per partition; children supersede the parent. `independently_admitted=false`, `independently_unresolved=false`.

## Evidence summary

Workspace text refutes filename-kind hierarchy. Farmington `statement_of_basis` opens as "FACT SHEET" despite `document_kind=statement_of_basis` in inventory. All three `final_permit` cover pages self-limit authorization to named Parts I–III/IV "hereof." Supporting documents use draft/proposed framing and defer limitations (e.g., Aztec SOB: "See the draft permit for limitations."). `reasonable_potential` files are calculation workbooks (Aztec: "APPENDIX A of FACT SHEET"). Part appendices are incorporated by cross-reference from issued permits (GCC/Farmington/Aztec Appendix A of Part II; Farmington Part IV reporting).

No explicit "in the event of conflict" clause was found, but functional precedence follows from issued-permit self-definition plus supporting-document non-authorization framing — not from `document_kind` ordering.

## Refinement partitions

| child_id | partition rule | count | disposition | admission |
|---|---|---:|---|---|
| issued_final_permit_authority | `document_kind=final_permit` | 3 | SUPPORTED_RESOLUTION | ADMIT_DISPOSABLE |
| supporting_rationale_non_authoritative | `document_kind in {fact_sheet, statement_of_basis}` | 3 | SUPPORTED_NEGATIVE | ADMIT_DISPOSABLE |
| reasonable_potential_calculation_appendix | `document_kind=reasonable_potential` | 2 | SUPPORTED_NEGATIVE | ADMIT_DISPOSABLE |
| permit_incorporated_appendix | `document_kind in {part_ii_appendix, part_iv}` | 3 | SUPPORTED_RESOLUTION | ADMIT_DISPOSABLE |
| minor_modification_authority | `document_kind=minor_modification` | 1 | UNRESOLVED | UNRESOLVED |

Partition is complete (3+3+2+3+1=12), non-overlapping, and mechanically computable from `document_inventory.json` fields.

## Residual uncertainty

`documents/gcc/minor_modification.txt` contains Part I limitation tables but no retrieved text links it to `documents/gcc/final_permit.txt` by incorporation or supersession. Its standalone authority remains UNRESOLVED.

This packet resolves **document authority**, not every narrative monitoring condition needed for Purposes B and C (e.g., "WHEN DISCHARGING" comments still require permit-part text extraction).

## Dry-run construction deltas

Four `dry_run/<child_id>/construction.py` copies apply partition-specific semantic deltas:

- **issued_final_permit_authority** — adds `document_authority_role` and `governing_corpus_self_defined` on `permit_document`; resolves blanket text-unavailable for `final_permit` rows.
- **supporting_rationale_non_authoritative** — marks `limits_binding_authority=false` for fact_sheet/statement_of_basis.
- **reasonable_potential_calculation_appendix** — marks calculation-appendix role and non-binding authority for reasonable_potential.
- **permit_incorporated_appendix** — marks `incorporated_by_issued_permit=true` for part_ii_appendix/part_iv.

No dry_run for `minor_modification_authority` (UNRESOLVED, not ADMIT_DISPOSABLE).

## Admission posture

Local source-established observations admitted at LEVEL_1 and LEVEL_2. Broader corpus-wide and WORLD generalizations withheld as UNVERIFIED_PROPOSAL. Plausible generalization is not source-established generalization.
