# Adjudication Review: `when_discharging`

## What was investigated

The frozen packet for obligation `when_discharging` asks what permit-limit comment `WHEN DISCHARGING` does to monitoring and limit applicability. Three candidate interpretations were supplied; adjudication was limited to retained snippets in `PACKET.json` with workspace `source_id` paths (`documents/` and `sources/`).

## What was found

**Supported resolution: discharge-conditioned monitoring (`monitoring_conditional`).**

Authoritative permit text establishes that footnote *1 ("When discharging.") annotates monitoring-frequency requirements for pH, flow, TSS, TRC, cyanide, and TDS. The statement of basis repeats that each of these parameters is monitored at the stated frequency "when discharging." The permit's NO DISCHARGE reporting section provides the alternate path when no discharge occurs in a sampling month.

**Refuted alternatives:**

- `limit_waived_no_discharge`: Part I.A excursion and violation language (lines 155–163) shows numeric limits remain enforceable for reported DMR values. The comment does not suspend limit applicability.
- `optional_monitoring_flag`: All 17 structured rows have `OPTIONAL_MONITORING_FLAG=N` and `LIMIT_TYPE_CODE=ENF`; the comment is not equivalent to optional monitoring.

## Evidence supporting the resolution

| Source | Role |
|--------|------|
| `documents/aztec/final_permit.txt` (footnote *1, lines 72–93) | Defines "When discharging." as the monitoring-frequency condition |
| `documents/aztec/final_permit.txt` (NO DISCHARGE, lines 150–153) | Alternate reporting when monitoring does not apply |
| `documents/aztec/final_permit.txt` (intermittent outfall, lines 56–66) | Context: backwash discharge is intermittent |
| `documents/aztec/statement_of_basis.txt` (lines 506–511) | Permit-writer rationale explicitly conditioning monitoring on discharge |
| `documents/aztec/final_permit.txt` (lines 155–163) | Limits remain enforceable; refutes limit-waiver reading |
| `sources/permit_limits.csv` (2 representative rows) | Confirms comment appears on enforceable, non-optional rows across monthly and quarterly schedules |

Epistemic basis is `SOURCE_ESTABLISHED` from permit documents, not CSV correlation alone. CSV rows corroborate the comment's presence and structural attributes but do not independently establish semantics.

## What remains uncertain

1. **Per-period discharge occurrence** — The relation contract states this is a separate factual question. Structured DMR extracts lack a NO DISCHARGE indicator field, so construction cannot determine whether discharge occurred in any given monitoring period.
2. **Comment-to-footnote linkage in structured data** — No explicit CSV field links `DMR_COMMENT_TEXT` to footnote *1; linkage is textual match plus co-occurring parameters and frequencies.
3. **Permit scope** — All 17 workspace occurrences are on permit NM0028762 (aztec package). This resolution does not generalize to other permits without separate evidence.

## What would change if admitted

Proposal status: **ADMIT_DISPOSABLE**.

`dry_run/construction.py` copies `construction.py` and applies a reusable semantic mapping:

- `DMR_COMMENT_TEXT` value `WHEN DISCHARGING.` → `monitoring_condition_code=DISCHARGE_OCCURRENCE`
- Removes 17 `conditional_discharge_dependent_monitoring` EXPLICIT_UNRESOLVED holes
- Adds `monitoring_condition_from_comment` interpreted requirement
- Admits `WHEN DISCHARGING.` as a known `permit_limit_comment_text` value

This encodes **what the comment means** (monitoring is discharge-conditioned) without claiming per-period discharge facts or waiving numeric limits. Purpose C (`no_numeric_result_case`) would still lack programmatic discharge-occurrence evidence.

`construction.py` itself is unchanged per adjudication protocol.
