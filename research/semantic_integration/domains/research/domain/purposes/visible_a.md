# Purpose A — registered outcome traceability

Using only the authoritative files in this evidence room, determine for each represented **registered study** whether its **registered primary outcome** can be traced to a **reported publication result**.

Required distinctions:

- study identity across registry and publication records
- registered primary outcome
- reported outcome
- semantic correspondence of those outcomes
- unresolved correspondence where evidence does not establish a judgment

Do not assume differently worded outcomes are different.
Do not assume similarly worded outcomes are equivalent.
Exact string equality is not required for correspondence, and lexical similarity is not sufficient for correspondence.

If a publication cannot be confidently identified as reporting that registered study, do not treat missing identity as a negative outcome finding. Report unresolved correspondence instead of omitting the study or asserting a join.

A registered study with no candidate publication is not_traced.

Do not write a prose memo. Save a JSON result as `purpose_ir/a/output.json` with this shape:

```json
{
  "purpose": "registered_outcome_traceability",
  "studies": [
    {
      "registry_id": "string",
      "publication_id": "string or null",
      "correspondence": "asserted" | "unresolved" | "not_traced"
    }
  ]
}
```

Include one row per represented registry study. Use registry and publication identifiers as they appear in the sources. Sort by `registry_id`.
