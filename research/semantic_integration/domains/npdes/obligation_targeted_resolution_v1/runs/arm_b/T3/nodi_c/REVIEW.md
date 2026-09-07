# Adjudication Review: nodi_c

## What was investigated

The frozen packet for obligation `nodi_c` was adjudicated against the exact semantic question: **What does NODI code C mean for a FY2025 DMR row with no numeric result?** The relation contract requires `no_numeric_result_case.nodi_code` to be interpreted before missing-evidence classification under Purpose C.

Four candidate interpretations were evaluated using only retained snippets whose `source_id` is a workspace path (`OBLIGATION.md`, `construction.py`, `sources/dmr_measurements.csv`, `documents/gcc/final_permit.txt`, `documents/aztec/final_permit.txt`). No broader corpus search was performed.

## What was found

1. **Structured data shows the code, not its meaning.** Among 186 FY2025 rows with empty `DMR_VALUE_NMBR`, 150 carry `NODI_CODE='C'`. All 150 are on permit NM0000116 and have `OPTIONAL_MONITORING_FLAG='N'`. This is structural correlation only; it does not define what C means.

2. **Construction does not interpret C.** `construction.py` declares `nodi_code_semantics` with `known=[""]` for Purpose C. Only the empty NODI code is pre-interpreted; value `C` remains UNINTERPRETED.

3. **No workspace codebook or permit definition for C.** `OBLIGATION.md` records the obligation as UNRESOLVED and notes no NODI codebook in structured sources. The NM0000116 permit package (`documents/gcc/final_permit.txt`) contains DMR reporting requirements but no NODI legend and no NO DISCHARGE box instruction. A NO DISCHARGE instruction exists in `documents/aztec/final_permit.txt`, but that text applies to permit NM0028762, not NM0000116 where all C rows occur.

4. **Contradictory evidence weakens positive candidates.**
   - *Monitoring not required*: contradicted by `OPTIONAL_MONITORING_FLAG='N'` on all 150 C rows.
   - *Documented no-discharge period*: contradicted by absence of NO DISCHARGE language in the NM0000116 permit reporting section.

## Evidence supporting the judgment

| Proposition | Source |
|---|---|
| Obligation is UNRESOLVED; no structured codebook | `OBLIGATION.md` lines 4–18 |
| Only empty `nodi_code` is pre-interpreted | `construction.py` lines 584–590 |
| C appears on 150 FY2025 no-result rows, all NM0000116, flag N | `sources/dmr_measurements.csv` |
| NM0000116 permit lacks NODI legend / NO DISCHARGE box | `documents/gcc/final_permit.txt` lines 103–122 |
| NO DISCHARGE instructions are for a different permit | `documents/aztec/final_permit.txt` lines 150–153 |

Disposition: **UNRESOLVED**. Epistemic basis: **SOURCE_ESTABLISHED** (the absence of a definition is established from workspace sources, not inferred from correlation or external knowledge). Failure mode: **EVIDENCE_INSUFFICIENT**.

## What remains uncertain

- The EPA or NetDMR authoritative definition of NODI code C (explicitly out of scope per packet limitations).
- Whether C indicates no discharge, a standardized no-data indicator, or another reporting state.
- Whether any uninventoried narrative in the NM0000116 permit package would tie blank results to a specific reporting action.

## Proposal disposition

`admit: UNRESOLVED`. No `dry_run/construction.py` was written. A reusable semantic mapping cannot be admitted without an authoritative workspace source defining C's meaning. Adding `C` to `known` values in `require_interpreted("nodi_code_semantics", ...)` would constitute an unverified model hypothesis.

## What would change if admitted

If a workspace source later established that NODI code C has a fixed, permit-applicable meaning (e.g., a codebook table or permit text defining C for NM0000116), a disposable edit could extend `known` in `nodi_code_semantics` with a reusable mapping. That would resolve Purpose C interpretation for all 150 affected occurrences and unblock missing-evidence classification downstream. Until such grounding exists, `construction.py` remains unchanged.
