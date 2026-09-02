# Purpose C — primary-outcome reanalysis readiness

Using only the authoritative files in this evidence room, determine which represented registered studies have an available dataset containing **sufficient represented measurements** to reanalyse the **registered primary outcome**.

This requires integration across registry records, study identity, dataset identity, outcome semantics, and dataset variable semantics.

Do not define reanalysis readiness by filename or by exact variable-name equality alone.

Distinguish:

- a dataset belonging to a study
- a dataset containing measurements sufficient for a particular registered outcome

If dataset-to-study identity is unresolved, report readiness as unresolved rather than as false.

If a dataset is established as belonging to the study but the represented variables are not sufficient for the registered primary outcome, report insufficient.

A registered study with no dataset candidate is insufficient.

Do not write a prose memo. Save a JSON result as `purpose_ir/c/output.json` with this shape:

```json
{
  "purpose": "reanalysis_readiness",
  "studies": [
    {
      "registry_id": "string",
      "dataset_id": "string or null",
      "status": "ready" | "insufficient" | "unresolved"
    }
  ]
}
```

Include one row per represented registry study. Sort by `registry_id`.
