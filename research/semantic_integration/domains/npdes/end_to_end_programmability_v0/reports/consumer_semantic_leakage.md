# Consumer semantic leakage

## MEASURED

`consumer_semantic_leakage = NONE`

Hits after auditor correction (World field `nodi_code` is not a legend): {
  "native_csv_filename": [],
  "native_pdf_or_txt": [],
  "native_source_path": [],
  "comment_literal": [],
  "nodi_legend": [],
  "comment_parse": []
}

## OBSERVED

No CSV/PDF paths, no `WHEN DISCHARGING` string match, no NODI meaning table in consumer code.

## HYPOTHESIS

Source reconciliation can stay out of application code when the World already holds holes and compiled relations.
