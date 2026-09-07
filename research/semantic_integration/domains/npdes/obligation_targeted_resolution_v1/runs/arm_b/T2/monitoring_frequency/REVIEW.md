# Adjudication Review: monitoring_frequency

## What I investigated

I read only `PASS_TASK_ADJUDICATE.md`, `PACKET.json`, and `construction.py` (for obligation context). I did not search `documents/` or `sources/` beyond the frozen retained snippets in the packet.

The obligation asks: **What monitoring frequencies do opaque `LIMIT_FREQ_OF_ANALYSIS_CODE` values establish?** Purpose B requires `monitoring_frequency_code` interpretation on `monitoring_requirement_fy2025.limit_freq_of_analysis_code` (construction.py lines 542–548). The packet presents three candidate interpretations and eight retained workspace snippets.

## What I found

### Calendar / periodic codes — UNRESOLVED

The packet identifies eight distinct `LIMIT_FREQ_OF_ANALYSIS_CODE` values across 105 limit rows (`sources/permit_limits.csv` snippet). No workspace file defines the NN/XX or NN/WK encoding. Permit narratives for Farmington (NM0020583), GCC (NM0000116), and Aztec (NM0028762) state human-readable MEASUREMENT FREQUENCY values—Five/Week, 1/Day, 1/Week, 2/Week, Daily, 2/month, Once/Quarter—but never mention or define tokens such as `05/WK`, `01/01`, or `01/07`.

The packet records consistent row-level alignment between structured codes and permit text (e.g. `05/WK` with Five/Week, `01/01` with 1/Day or Daily, `01/07` with 1/Week). That alignment is explicitly **not dispositive**: structural CSV correlation alone is forbidden as a code legend, and permit text does not state that structured tokens encode those strings.

### Non-calendar codes — supported negative (partial)

For `99/99` and `09/99`, workspace permit text supports a negative finding:

- **99/99**: Farmington permit text describes Flow as "Continuous" with a Totalizing Meter; the packet states `99/99` appears only on continuous-flow (TM sample type) rows.
- **09/99**: Farmington permit text describes WET retest reporting as conditional ("If required"), not a fixed calendar schedule; structured retest rows use `09/99`.

These codes do **not** establish ordinary periodic sampling frequencies comparable to `01/07` or `05/WK`.

### Additional limitations noted in the packet

- Footnotes qualify nominal frequencies (e.g. "*1 Sampling on at least five different days"; "*1 When discharging") but are not encoded in the code field.
- `DMR_FREQ_OF_ANALYSIS_CODE` sometimes differs from `LIMIT_FREQ_OF_ANALYSIS_CODE`, so DMR codes do not provide a standalone legend.
- Some permit-text frequencies (e.g. Aztec WET Once/Term, GCC WET Once/5 years) have no corresponding structured rows in this workspace.

## Evidence that supports the judgment

| Finding | Admissible grounding |
|--------|----------------------|
| Opaque codes exist without workspace legend | `sources/permit_limits.csv` |
| Permit text uses human-readable frequencies, not opaque tokens | `documents/*/final_permit.txt` snippets |
| `99/99` aligns with Continuous flow monitoring | `documents/farmington/final_permit.txt` |
| `09/99` aligns with conditional WET retest, not calendar schedule | `documents/farmington/final_permit.txt` |
| Statement of basis confirms plain-language frequencies but not code tokens | `documents/farmington/statement_of_basis.txt` |

All retained snippet `source_id` values are workspace paths under `sources/` or `documents/` and are admissible.

## What remains uncertain

- Whether any calendar-structured token can be decoded to a specific monitoring frequency from workspace sources alone.
- Whether a permit-row crosswalk join is an authorized interpretation rule (the packet treats it as inferential).
- How footnotes and discharge conditions modify the obligation relative to the bare code value.
- Generalizability to code values not represented in `permit_limits.csv`.

## Disposition and proposal

**JUDGMENT**: `UNRESOLVED` with scope `ONE_RELATION_OR_VOCABULARY` and `failure_mode_if_unresolved: EVIDENCE_INSUFFICIENT`. A partial supported negative for `09/99` and `99/99` does not answer what frequencies the remaining calendar codes establish for purpose B.

**PROPOSAL**: `admit: UNRESOLVED`. No `dry_run/construction.py` was written. A world-scope codebook or permit-crosswalk mapping would rely on `MODEL_HYPOTHESIS` / correlational inference without `SOURCE_ESTABLISHED` grounding; per adjudication rules, that must not be admitted as World truth.

## What would change if admitted

If a future packet supplied an explicit workspace code legend or an authorized join contract defining `LIMIT_FREQ_OF_ANALYSIS_CODE` semantics, `construction.py` could add a reusable mapping function (not per-row judgments) to populate interpreted monitoring-frequency values on `monitoring_requirement_fy2025`, satisfying purpose B's `monitoring_frequency_code` requirement for all FY2025 overlapping limit rows. Until then, `limit_freq_of_analysis_code` should remain opaque pass-through and the obligation stays unresolved.
