# Adjudication review: `when_discharging`

## Investigated

Judged only the frozen evidence in `PACKET.json` for obligation `when_discharging`: what the permit-limit comment `WHEN DISCHARGING` does to monitoring and limit applicability. No corpus search was performed outside the packet.

## Found

The supported interpretation is established from workspace permit documents for NM0028762, not from CSV correlation alone.

1. **Authoritative definition.** `documents/aztec/final_permit.txt` (lines 92–94) defines footnote *1 as "When discharging." The packet identifies this as the authoritative text behind `DMR_COMMENT_TEXT = WHEN DISCHARGING.`

2. **Comment attaches to monitoring frequencies, not optional flags.** The same permit (lines 56–66, 72–80) marks pH, flow, TSS, and TRC monitoring frequencies with (*1) on an intermittent-flow outfall. Structured data confirms all 17 matching rows have `OPTIONAL_MONITORING_FLAG=N`, refuting optional-monitoring and limit-voiding readings.

3. **No-discharge alternative is permit-prescribed.** `documents/aztec/final_permit.txt` (lines 150–153) requires marking the NO DISCHARGE box on the DMR when there is no discharge during the sampling month, instead of parameter monitoring.

4. **Statement of basis corroborates.** `documents/aztec/statement_of_basis.txt` (lines 506–511) paraphrases the same schedule with explicit "when discharging" language for flow, TRC, pH, TDS, and cyanide.

5. **Relation contract honored.** The packet contract states the comment conditions monitoring while discharge occurrence in a period is a separate factual question. The permit text supports conditioning without supplying period-specific discharge facts.

Refuted interpretations (informational-only, optional monitoring, voided limits) are contradicted by the footnote linkage, statement-of-basis paraphrase, and non-optional structured flags.

## Evidence supporting resolution

| Source | Role |
|--------|------|
| `documents/aztec/final_permit.txt` footnote *1 | Defines the comment's meaning |
| `documents/aztec/final_permit.txt` effluent limits table | Shows (*1) on monitoring frequencies |
| `documents/aztec/final_permit.txt` NO DISCHARGE REPORTING | Establishes no-discharge reporting substitute |
| `documents/aztec/statement_of_basis.txt` lines 506–511 | Independent permit-package corroboration |
| `sources/permit_limits.csv` (17 rows) | Scopes occurrences; confirms non-optional encoding |

**Disposition:** `SUPPORTED_RESOLUTION`  
**Epistemic basis:** `SOURCE_ESTABLISHED`  
**Scope:** `ONE_RELATION_OR_VOCABULARY` (meaning of the `WHEN DISCHARGING` comment within NM0028762)

## Remaining uncertainty

- Whether discharge actually occurred during any specific FY2025 monitoring period is not established from structured DMR data (140 FY2025 rows for these limit_value_ids have blank `NODI_CODE` and numeric values).
- Resolution is grounded in the aztec permit package for NM0028762 and may not generalize to other permits.
- `permit_document_text_not_available` in construction remains valid: narrative conditions are not ingested structurally; the disposable edit maps the CSV comment via an admitted semantic rule, not by parsing documents at runtime.

## If admitted (`ADMIT_DISPOSABLE`)

`dry_run/construction.py` applies a reusable mapping:

- `DMR_COMMENT_TEXT` containing `WHEN DISCHARGING` → `monitoring_applicability_condition = DISCHARGE_OCCURRENCE`
- Registers `WHEN DISCHARGING.` as a known `permit_limit_comment_text` value
- Removes `conditional_discharge_dependent_monitoring` unresolved holes for the 17 affected rows

This encodes that monitoring/limit obligations are discharge-conditioned while leaving per-period discharge occurrence as a separate factual input. It does not infer discharge from DMR blanks or assert world-wide truth beyond the established permit-package meaning.
