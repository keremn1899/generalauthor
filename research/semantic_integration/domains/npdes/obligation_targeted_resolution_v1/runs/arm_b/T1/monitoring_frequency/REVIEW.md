# Adjudication Review: monitoring_frequency

## What I investigated

I read `PASS_TASK_ADJUDICATE.md`, the frozen `PACKET.json`, and `construction.py` (for purpose-B obligation context only). I did not search `documents/` or `sources/` beyond the retained snippets already frozen in the packet.

The obligation asks what monitoring frequencies opaque `LIMIT_FREQ_OF_ANALYSIS_CODE` values (e.g. `05/WK`, `01/07`, `01/01`) establish. Purpose B requires `monitoring_frequency_code` to be interpreted per `permit_limit_row` on relation `monitoring_requirement_fy2025`.

## What I found

### Established from admissible workspace snippets

Permit documents in the packet **do** state plain-language monitoring frequencies for specific parameters on three permits:

| Permit | Source snippet | Examples |
|--------|----------------|----------|
| NM0020583 | `documents/farmington/final_permit.txt` | pH Five/Week, TRC Daily, TDS 1/Week, Flow Continuous |
| NM0000116 | `documents/gcc/final_permit.txt` | pH and Flow 1/Day, TSS and metals 1/Week |
| NM0028762 | `documents/aztec/final_permit.txt` | Flow 2/Week, TRC 1/Day, TDS 1/Quarter |

Narrative sources (`documents/farmington/statement_of_basis.txt`, `documents/gcc/fact_sheet.txt`) corroborate some of these frequencies in prose.

`sources/permit_limits.csv` (as summarized in the packet) shows eight distinct code values on limit rows with **no accompanying definition column**.

### Not established from workspace snippets

1. **No code legend.** No retained snippet defines `LIMIT_FREQ_OF_ANALYSIS_CODE`, prints any opaque token (`05/WK`, `99/99`, etc.), or states an NN/PP encoding rule.
2. **Crosswalk is structural, not definitional.** The packet's candidate mappings (e.g. `05/WK` ↔ Five/Week) depend on pairing CSV rows to permit-table rows by permit number and parameter code. Adjudication rules forbid treating structural/CSV correlation alone as sufficient semantics.
3. **Sentinel codes lack document literals.** `99/99` (continuous flow) and `09/99` (conditional WET retest) are inferred only from row pairing with "Continuous" and "(If required) Retest" language; the code strings never appear in document text.
4. **Contradictory evidence on flow.** Farmington's statement of basis says flow is monitored five times per week, while the final permit table says Continuous and structured rows carry `99/99`, not `05/WK`.

### Candidate interpretations assessed

| ID | Verdict from packet alone |
|----|---------------------------|
| `calendar_count_over_period` | Plausible but crosswalk-dependent; NN/PP rule never authoritatively stated |
| `continuous_flow` | Pairing inference only; code absent from documents |
| `conditional_retest` | Pairing inference only; code absent from documents |
| `unresolved_no_legend` | Best supported negative posture, but full SUPPORTED_NEGATIVE not reached because exemplar plain-language frequencies *are* established—just not linked to codes |

## Evidence supporting UNRESOLVED disposition

- Packet `known_limitations` explicitly: no workspace file defines the field, sentinel codes lack document literals, general NN/PP convention unstated, coverage limited to three permits.
- Packet `evidence_basis` for the leading candidate admits: "no workspace file states the NN/PP rule explicitly."
- Adjudication constraints: plausible interpretation insufficient; CSV/structural correlation insufficient; snippets with non-workspace `source_id` inadmissible (all retained snippets are admissible, but they still do not define codes).

Plain-language permit text establishes **what frequency each named parameter requires** on specific permits. It does **not** establish **what each opaque code token means** as reusable vocabulary.

## What remains uncertain

- Whether `LIMIT_FREQ_OF_ANALYSIS_CODE` follows a general NN/PP count-over-period scheme.
- Semantics of `99/99` and `09/99` without an in-workspace codebook.
- Whether the permit+parameter crosswalk is authoritative for all rows in the dataset.
- How to resolve the Farmington flow-frequency contradiction.
- Whether conditional footnotes (e.g. aztec `*1 When discharging`) affect code interpretation.

## What would change if admitted

If `calendar_count_over_period` were admitted as `ADMIT_DISPOSABLE` with `SOURCE_ESTABLISHED` grounding, `dry_run/construction.py` would add a reusable code→frequency mapping (not per-row judgments) so purpose B's `monitoring_frequency_code` obligation could resolve for all FY2025 monitoring requirements.

**Not admitted.** Disposition is `UNRESOLVED`; proposal is `UNVERIFIED_PROPOSAL` with `MODEL_HYPOTHESIS` epistemic basis. `construction.py` is unchanged. A disposable mapping would assert World truth for a vocabulary whose semantics are not source-established—disallowed for WORLD or vocabulary-scope claims without `SOURCE_ESTABLISHED` grounding.

Admission would require at least one of: an in-workspace codebook printing the tokens and their definitions, an authoritative workspace rule stating the NN/PP convention, or user-certified policy grounding the crosswalk as definitional rather than correlational.
