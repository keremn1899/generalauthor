Besides the CSV limit and DMR tables, this workspace inventories 12 permit PDFs across three permits (NM0020583, NM0028762, NM0000116). For each file we have filename, a document kind label, file size, and a hash—but no extracted narrative text in the structured sources the draft uses.

The kinds present include `final_permit`, `fact_sheet`, `statement_of_basis`, `reasonable_potential`, `minor_modification`, `part_ii_appendix`, and `part_iv`. The draft lists the documents and then marks narrative permit conditions as unresolved. It does not rank which document would win if text were available, and it does not infer conditions from the kind label alone.

Purposes B and C can depend on language that may only appear in those PDFs—conditional monitoring, special studies, seasonal requirements, explanations of what a limit comment means. Without the text, we're stuck.

If you were working from this package, which document would you treat as authoritative for operational permit conditions? Does the `document_kind` field imply a hierarchy (for example, final permit over fact sheet), or would you need to read and reconcile multiple documents every time?

I'm not asking you to supply the PDF text here—just whether filename/kind metadata alone is enough to establish authority, and how you'd resolve conflicts between documents if narrative were available.
