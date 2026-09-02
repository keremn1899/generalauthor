# Purpose B — cross-source study reconciliation

Using only the authoritative files in this evidence room, determine which registry, publication, and dataset records can be established as referring to the **same underlying study**.

Do not globally merge records. Established identity is a relation or judgment, not destructive canonicalization.

Do not treat similar titles, shared programme names, overlapping authors, or shared clinic names as automatic identity.

Exact shared identifiers may support mechanical candidates. Semantic identity still requires a judgment where the sources do not make identity explicit.

Permit explicit unresolved identity. Absence of a linkage is not evidence of distinctness. Missing a positive same-study judgment is not a negative judgment.

Do not write a prose memo. Save a JSON result as `purpose_ir/b/output.json` with this shape:

```json
{
  "purpose": "study_reconciliation",
  "links": [
    {
      "left": "string",
      "right": "string",
      "epistemic": "SAME_STUDY" | "DISTINCT" | "UNRESOLVED"
    }
  ]
}
```

Use these identifier forms:

- registry: `registry:<registry_id>`
- publication: `publication:<publication_id>`
- dataset: `dataset:<dataset_id>`

Include every link required to connect a registry study to its publication and dataset records, and any other registry/publication/dataset pair that is a live identity candidate or an established distinctness needed to keep those candidates from collapsing. Sort by `left`, then `right`.
