# Adjudication Review: document_authority

## What I investigated

I read only `PASS_TASK_ADJUDICATE.md`, `PACKET.json`, and `construction.py`. I did not search `documents/`, `sources/`, or any other corpus material beyond the frozen retained snippets in the packet.

The obligation asks, without ranking from filenames: what inventoried permit documents establish, and which document governs when they disagree. Purpose B and C are in scope. The relation contract requires document text for narrative conditions and rejects filename kind as hierarchy.

## What I found

### Supported resolution: `issued_authorization_binding`

Workspace permit text establishes a document-role vocabulary grounded in each file's own language:

1. **Issued authorization** (`final_permit.txt` in gcc and farmington): The authorization cover binds the permittee to effluent limitations, monitoring requirements, and other conditions in explicitly named Parts (I–III for gcc; I–IV for farmington). Each supersedes a prior issued permit. This is enforceable authorization language, not merely inventory metadata.

2. **Draft / supporting documents** (`fact_sheet.txt`, `statement_of_basis.txt`): Headers state "FOR THE DRAFT NPDES PERMIT." Fact-sheet body text attributes limits to the "proposed permit" and lists administrative-record materials "used to develop the proposed permit." Farmington statement-of-basis text explicitly defers reconsideration to the final permit. These establish permitting rationale and proposed conditions, not standalone enforceable authorization.

3. **Incorporation by reference**: gcc Part II text incorporates Appendix A by explicit reference into the issued permit.

4. **Governance when documents disagree** is relationship-specific, not universal: issued authorization supersedes prior issued permits; draft text defers to final permit; appendices govern when explicitly incorporated. No single workspace text resolves every possible pairwise conflict.

### Supported negatives (rejected candidates)

- **`inventory_kind_hierarchy`**: Rejected by relation contract and packet limitation that `document_inventory.json` provides only path, filename, kind, permit, bytes, sha256, origin with no authority rules.
- **`all_files_equally_enforceable`**: Rejected because draft documents self-identify as "FOR THE DRAFT" and describe proposed-permit conditions.
- **`universal_conflict_rule`**: Not found in retained workspace text.

## Evidence supporting the judgment

All retained snippets use admissible `documents/` workspace paths:

| Source | Role established |
|--------|------------------|
| `documents/gcc/final_permit.txt` (cover) | Issued authorization binding Parts I–III |
| `documents/farmington/final_permit.txt` (cover) | Issued authorization binding Parts I–IV |
| `documents/gcc/final_permit.txt` (Part II) | Appendix A incorporation |
| `documents/gcc/fact_sheet.txt` (header, VIII, XVI) | Draft / proposed / administrative-record |
| `documents/aztec/statement_of_basis.txt` (header) | Draft-permit document |
| `documents/farmington/statement_of_basis.txt` | Defers to final permit |

Contradictory evidence (`documents/gcc/minor_modification.txt`) undercuts equal enforceability of every inventoried file but does not overturn the issued-vs-draft distinction.

## What remains uncertain

- **`minor_modification.txt`**: Contains Part I limit tables only; no authorization cover or precedence language. Authority relative to the issued permit is unknown from the packet.
- **Unopened files**: Reasonable-potential worksheets and standalone appendix extracts were not examined as primary documents.
- **No universal precedence rule**: Workspace text does not state which document governs for every possible disagreement among all twelve inventoried files.
- **Internal part precedence**: Beyond explicit cross-references (e.g., Appendix A), precedence among all subparts within an issued permit is not fully specified.

## What would change if admitted

`PROPOSAL.json` admits a disposable edit in `dry_run/construction.py` that:

- Adds `document_authority_role` to the `permit_document` relation.
- Applies a reusable `DOCUMENT_AUTHORITY_ROLE` mapping: `final_permit` → `issued_authorization`; `fact_sheet` and `statement_of_basis` → `draft_supporting`; other kinds → empty (unresolved).
- Adds a purpose requirement interpreting `document_authority_role` for purposes B and C.

If admitted, construction would encode packet-grounded document roles without treating inventory kind labels as a filename hierarchy. The existing `permit_document_text_not_available` unresolved obligation would remain for narrative permit conditions not available as structured fields. Kinds without packet-established roles (e.g., `minor_modification`) would still lack authority assignment.

If not admitted, `construction.py` stays unchanged and document authority remains entirely unresolved at the world layer.
