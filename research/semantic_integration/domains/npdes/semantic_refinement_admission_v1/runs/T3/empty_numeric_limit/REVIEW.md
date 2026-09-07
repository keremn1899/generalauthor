# Review: empty_numeric_limit

## Parent disposition

**parent_status: REFINED** — The parent question ("When LIMIT_VALUE_NMBR is empty, is the row a numeric limit, report-only monitoring, or something else?") is too coarse. All 57 affected rows share empty `LIMIT_VALUE_NMBR` and `LIMIT_TYPE_CODE=ENF`, but they partition into four mutually exclusive, mechanically computable classes via `DMR_COMMENT_TEXT`. Different partitions have different answers; this is refinement, not parent-level UNRESOLVED.

`independently_admitted=false`, `independently_unresolved=false`.

## Evidence summary

| Partition rule | Count | Resolution |
|---|---:|---|
| blank `DMR_COMMENT_TEXT` | 18 | Report-only monitoring (permit "Report"/N/A cells) |
| `WHEN DISCHARGING` in comment | 12 | Conditional / N/A mass-load column |
| `PASS = 0` and `FAIL = 1` in comment | 12 | Pass/fail WET encoding |
| `GEOMETRIC MEAN` in comment | 15 | Aggregated geometric-mean reporting |

No residual rows. Zero empty-limit rows populate `LIMIT_VALUE_STANDARD_UNITS`.

## Key grounding

- **Blank comment (18):** GCC final permit maps TSS 30-day avg, dissolved copper, hardness to "Report" while daily max carries numeric limits. Farmington final permit maps cadmium, dioxin, and related pollutants to "Report" with all N/A limit columns.
- **When discharging (12):** Aztec permit TSS table uses N/A for mass-load columns with numeric mg/L limits; footnote *1 "When discharging." CSV rows carry `DMR_COMMENT_TEXT=WHEN DISCHARGING.` with empty mass-load `LIMIT_VALUE_NMBR`.
- **Pass/fail WET (12):** CSV rows use `LIMIT_UNIT_DESC=pass=0;fail=1` and explicit PASS/FAIL comment instructions; not missing numeric concentration limits.
- **Geometric mean (15):** Farmington TDS table has Report cells without per-period numeric limits; footnote *6 defines geometric mean of weekly values.

## Refuted interpretation

Treating all empty-limit rows as deferred numeric limits (`LIMIT_TYPE_CODE=ENF` alone) is refuted: no row has `LIMIT_VALUE_STANDARD_UNITS`, and permit text plus comment partitions show distinct non-numeric classes.

## Construction gap (T5)

`numeric_comparison_candidate` filters on `has_limit_value_nmbr`, silently dropping all 57 rows without a named classification hole. Each admitted child proposes a `dry_run/<child_id>/construction.py` derive relation for its partition.

## Limitations

- No ICIS/NPDES field legend in workspace.
- Not every blank-comment row individually matched to permit-table text (partition rule is structurally grounded).
- PASS/FAIL WET permit narrative not located in farmington final_permit.txt within search budget; structured CSV comment is primary grounding.
- FY2025 DMR measurements contain rows with empty `LIMIT_VALUE_NMBR` (380 total) but Purpose A blocking is inferred from permit_limit structure and T5 filter logic.

## ADMISSION.json

Not written: obligation schema is `empty_numeric_limit_classification`, not `document_authority`.
