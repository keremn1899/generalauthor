# Adjudication Review: monitoring_frequency

## What I investigated

I read only `PASS_TASK_ADJUDICATE.md`, the frozen `PACKET.json`, and `construction.py` (for context on how purpose B consumes `limit_freq_of_analysis_code`). I did not search `documents/`, `sources/`, or any other corpus files.

The obligation asks: **What monitoring frequencies do opaque `LIMIT_FREQ_OF_ANALYSIS_CODE` values (e.g. 05/WK, 01/07, 01/01) establish?** Purpose B requires these codes to be interpretable on `monitoring_requirement_fy2025` rows.

## What I found

### Admissible workspace evidence

All eight retained snippets have `source_id` under `documents/` or `sources/` and are therefore admissible. They establish:

1. **Permit narratives use human-readable frequencies only.** Three `final_permit.txt` files (`farmington`, `gcc`, `aztec`) state frequencies such as Five/Week, 1/Day, 1/Week, Continuous, Once/Quarter. None of these documents mention opaque strings like `05/WK`, `01/07`, or `99/99`.

2. **CSV rows carry opaque codes structurally.** `sources/permit_limits.csv` snippets show `LIMIT_FREQ_OF_ANALYSIS_CODE` values (05/WK, 99/99, 09/99) on specific limit rows. These rows can be joined to permit narratives by permit number and parameter, but the packet explicitly labels that pairing as correlational, not definitional.

3. **No code legend exists in the workspace.** The packet's `known_limitations` state that grep across all `documents/` found zero occurrences of opaque code strings and no file defines the NN/XX grammar.

4. **Special codes lack document-level definitions.** `99/99` aligns with farmington flow described as Continuous/Totalizing Meter and sample type TM in CSV, but the document never names `99/99`. `09/99` appears only on optional WET retest parameters; farmington permit text describes retest timing as conditional on test failure and distinguishes "retest codes" (STORET parameter codes) from frequency codes.

### Candidate interpretations assessed

| Candidate | Verdict |
|-----------|---------|
| `periodic_count_per_period` | Not established. Pairings (05/WK↔Five/Week, 01/07↔1/Week, 01/90↔1/Quarter) are consistent across permits but constitute structural correlation, which adjudication rules exclude as sufficient evidence. |
| `continuous_metering` | Not established. Farmington flow is continuous in narrative, but `99/99` is never defined in text; code appears only at one permit. |
| `event_driven_retest` | Not established. Retest obligations are event-driven in narrative, but the packet notes the cited "retest codes" are not `LIMIT_FREQ_OF_ANALYSIS_CODE` 09/99. |
| `uninterpretable_without_legend` | **Supported.** Workspace sources establish human-readable frequencies and opaque structured codes separately, with no definitional bridge. |

### Contradictions and limits

- Farmington `statement_of_basis.txt` says "five times per week for … flow" while `final_permit.txt` assigns flow Continuous — an internal inconsistency that weakens any single-permit pairing inference.
- Code `01/01` is reused across daily pH, daily TRC, and daily flow contexts without a published grammar.
- Eight distinct codes affect 105 FY2025-overlapping rows; retained snippets cover representative codes within the 8-snippet budget.

## Evidence supporting the judgment

**Disposition: SUPPORTED_NEGATIVE** for interpretation `uninterpretable_without_legend`.

**Epistemic basis: SOURCE_ESTABLISHED** — the negative conclusion follows from what workspace documents contain and omit, not from model inference or external regulatory knowledge.

**Scope: WORLD** — applies to the full `monitoring_frequency` obligation over all FY2025-overlapping `limit_freq_of_analysis_code` values, because the absence of any code legend or in-document code mention is a workspace-wide finding reported in the packet.

Positive frequency semantics are not established. CSV-to-document correlation, internal consistency of pairings, and plausible NN/XX readings are explicitly insufficient under adjudication rules.

## What remains uncertain

- Whether ICIS-NPDES or EPA reference tables (outside the workspace) define the NN/XX code grammar.
- Whether permit-specific pairings would hold if tested against all 105 occurrences and all eight code values.
- The true regulatory meaning of single-permit codes `99/99` and `09/99`.

## Proposal and construction impact

**admit: UNRESOLVED** — no positive semantic mapping is admissible. WORLD-scope truth requires SOURCE_ESTABLISHED grounding; none is available for any candidate positive interpretation.

`construction.py` is unchanged. No `dry_run/construction.py` was written.

## What would change if a positive interpretation were admitted

If a workspace source later surfaced that explicitly defined `LIMIT_FREQ_OF_ANALYSIS_CODE` values (e.g., a code table naming `05/WK` as "five samples per week"), a reusable mapping could be added to construction (e.g., populating `known=[...]` on `monitoring_frequency_code` or deriving an interpreted frequency relation). Until then, purpose B's `require_interpreted` on `limit_freq_of_analysis_code` remains unsatisfied for monitoring obligations.
