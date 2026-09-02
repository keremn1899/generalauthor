# Purpose D — held out from the constructor

Do not place this file in the constructor workspace until A/B/C construction is frozen.

Using only the compiled World (and, if present, the authoritative source files), identify registered studies where:

1. the **published primary result** is traceable to the **registered primary outcome**, and
2. a **dataset belonging to that study** is available.

This is not reanalysis-readiness. Dataset availability here means an established dataset-of-study link, not measurement sufficiency for reanalysis.

Preserve unresolved study identity or unresolved outcome linkage explicitly. Do not coerce unresolved cases into matches or into omissions.

A study whose published result is established as not corresponding to the registered primary is not a match. A study with no publication is not a match.

Save JSON as `purpose_ir/d/output.json`:

```json
{
  "purpose": "traceable_result_with_dataset",
  "cases": [
    {
      "registry_id": "string",
      "publication_id": "string or null",
      "dataset_id": "string or null",
      "status": "matches" | "unresolved"
    }
  ]
}
```

Include matching cases and unresolved cases. Do not include established non-matches. Sort by `registry_id`.
