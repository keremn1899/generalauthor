# Adjudication Review: document_authority

## What I investigated

I read only `PASS_TASK_ADJUDICATE.md`, `PACKET.json`, and `construction.py`. I did not search `documents/` or `sources/`. Judgment is based solely on the frozen packet's retained snippets (all with workspace paths under `documents/`), candidate interpretation statuses, contradictory-evidence notes, and known limitations.

The obligation asks: without ranking from filenames, what do inventoried permit documents establish, and which document governs if they disagree?

## What I found

**Refuted interpretations (packet status):**

- `inventory_kind_hierarchy`: document_kind values do not define a fixed governing hierarchy.
- `all_package_documents_equally_binding`: not supported; draft supporting documents defer enforceable limits.
- `structured_inventory_only`: refuted; narrative permit text is available in workspace extracts.

**Supported interpretation:** `issued_permit_authorization_governs`

Issued final permit narrative text establishes enforceable authorization. Draft supporting documents (fact sheet, statement of basis) frame themselves as draft/permit-development material and defer enforceable limits to permit text. Filename or inventory kind alone is not a hierarchy signal.

## Evidence supporting resolution

| Source | Finding |
|--------|---------|
| `documents/gcc/final_permit.txt` (lines 4-21) | AUTHORIZATION TO DISCHARGE binds conditions to Parts I–III of the issued permit. |
| `documents/gcc/final_permit.txt` (lines 23-24) | Explicit supersession of prior permit. |
| `documents/gcc/final_permit.txt` (lines 149-150) | Part II appendix incorporated by in-document citation. |
| `documents/gcc/fact_sheet.txt` (lines 1-4, 34-35) | Draft framing; proposed reissuance context. |
| `documents/aztec/statement_of_basis.txt` (lines 1-4) | Draft-permit framing. |
| `documents/aztec/statement_of_basis.txt` (lines 556-558) | Explicit deferral: "See the draft permit for limitations." |
| `documents/farmington/final_permit.txt` (lines 24-25) | Confirms same issued-permit Parts I–IV integration pattern at a second facility. |

All eight retained snippets have admissible `source_id` values (workspace paths). No snippet outside `documents/` was used.

## What remains uncertain

1. **No universal conflict clause.** The packet notes that workspace text does not state an explicit general rule such as "if the fact sheet disagrees with the issued permit, the issued permit governs." Governance is established through document-role text (issued authorization vs. draft deferral), not a single precedence sentence.

2. **Incomplete document coverage.** Only 5 of 12 inventoried narrative documents were opened. `gcc/minor_modification.txt` authority relative to the issued final permit is not established.

3. **Structural packaging gaps.** Farmington Part IV is a separate inventory file while the cover page references Part IV "hereof." `gcc/final_permit.txt` Part III extract appears truncated.

4. **Contradictory-evidence notes** (farmington SOB headers vs. inventory kind; minor_modification content) were not treated as admissible snippets—they are unopened-document notes only.

## Disposition rationale

Disposition is **SUPPORTED_RESOLUTION** because workspace narrative text directly establishes (a) what issued final permits authorize, (b) that draft supporting documents defer enforceable limits, and (c) that inventory kind alone is not authority. Three refuted alternatives are explicitly ruled out. CSV correlation and filename ranking were not used.

Epistemic basis is **SOURCE_ESTABLISHED** (not inference from structure alone). Scope is **ONE_RELATION_OR_VOCABULARY** (document authority contract for purposes B and C), not WORLD-wide truth.

## What would change if admitted

`PROPOSAL.json` admits **ADMIT_DISPOSABLE**. `dry_run/construction.py` copies `construction.py` and:

1. Adds a fixed `DOCUMENT_AUTHORITY_ROLE` lookup mapping inventory `document_kind` to narrative-established roles (`issued_authorization`, `draft_supporting`, `authority_unresolved`). This is a reusable semantic mapping—not per-row model judgment—and is keyed to roles established in packet snippets, not a filename hierarchy.

2. Extends `permit_document` with `authority_role` and `governs_enforceable_obligations` fields.

3. Removes the blanket `permit_document_text_not_available` unresolved and replaces it with per-document unresolved entries only for kinds whose authority role the packet does not establish (`minor_modification`, `reasonable_potential`, unknown kinds).

Production `construction.py` is unchanged.
