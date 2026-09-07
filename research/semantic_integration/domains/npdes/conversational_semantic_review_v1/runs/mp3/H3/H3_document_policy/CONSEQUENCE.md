# Consequence of domain expert reply on document authority

## What changed

The expert confirmed that the analysis should stop where it already stops: structured sources alone cannot establish narrative permit conditions or document authority.

**Refined unresolved reason:** `permit_document_text_not_available` now states explicitly that the document inventory establishes what files exist in the package, not what they say or which document governs. It also records the expert's policy that kind labels (for example final permit, fact sheet, minor modification) do not substitute for reading permit text, issuance dates, and cross-references.

No new relations, derived rows, or document-ranking logic were added.

## What did not change

- The `permit_document` relation still mirrors the inventory (permit, document hash, kind label, filename, bytes) without inferring authority from `document_kind`.
- No hierarchy was encoded (for example final permit over fact sheet, or minor modification over earlier language). The expert described that hierarchy as something you apply when you have the actual permit text in front of you, not from labels in the inventory.
- Comment-driven unresolved items (conditional discharge, geometric mean, pass/fail), NODI semantics, measurement-to-limit-kind matching, and superseded-limit applicability are untouched.
- Limit rows, DMR measurements, and pairing logic are unchanged.

## What remains open

Narrative monitoring obligations pointed to by DMR comments or limit rows stay unresolved until permit text enters working evidence. Which document would be authoritative for a given condition, and how modifications supersede earlier language, depend on content the structured dataset does not contain.
