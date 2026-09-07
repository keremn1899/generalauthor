# Consequence of domain expert reply

## What changed

The expert could not supply definitive NODI code meanings. They directed us to keep both codes open for purpose C and not treat C and 9 as the same statement.

I recorded that guidance in `construction.py`:

- Added a purpose-C policy note (`nodi_missing_evidence_policy`) on `no_numeric_result_case`: C and 9 are not interchangeable; blank plus C usually indicates documented no-data rather than a measured concentration; neither code alone proves compliance or violation; empty NODI would be a different problem than a populated code; code 9 needs the official NODI legend.
- Added derivation grounding on `no_numeric_result_case` documenting those constraints.
- Added two explicit unresolved items: `nodi_code_9_semantics_without_legend` (36 rows with code 9) and `nodi_code_c_monitoring_period_semantics` (150 rows with code C), capturing why each family remains open.

The existing `nodi_code_semantics` requirement still treats only an empty code as known. Codes **C** and **9** remain UNINTERPRETED on all 186 no-result rows.

## What did not change

I did not assign "no discharge," "not required," or any other closed missing-evidence classification to either code. The expert's soft statement about C signaling documented no-data is policy context only; it does not close the interpretation holes or add new World-true fields.

I did not treat code 9 as equivalent to C or infer its meaning from the digit. I did not use the optional-monitoring or parameter-type patterns as conclusions.

No changes were made to measurement–limit pairing, numeric comparison, permit-limit comments, or document authority.
