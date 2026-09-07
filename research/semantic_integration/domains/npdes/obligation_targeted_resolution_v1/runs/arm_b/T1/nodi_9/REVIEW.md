# Adjudication review: nodi_9

## What I investigated

I read the frozen evidence packet for obligation `nodi_9`, which asks: **What does NODI code 9 mean for a FY2025 DMR row with no numeric result?** Purpose is **C**; the relation contract requires interpreting `no_numeric_result_case.nodi_code` while forbidding inheritance between codes **C** and **9**.

I evaluated only the seven retained snippets in `PACKET.json`, all of which have admissible workspace `source_id` paths (`sources/` or `documents/`). I did not search the broader corpus, use training-data knowledge, or treat CSV structural correlation as semantic evidence.

## What I found

### Established from the packet

1. **Field existence, not semantics.** `sources/dmr_measurements.csv` header confirms `NODI_CODE` is a structured column with no accompanying legend in the CSV.
2. **Observed instance.** A representative FY2025 row (monitoring period ending 2024-11-30) on permit NM0020583 has empty `DMR_VALUE_NMBR` and `NODI_CODE=9` for WET retest parameter 22415.
3. **Disjoint code populations.** NODI `C` appears on permit NM0000116; NODI `9` appears on NM0020583. This supports the contract exclusion of inheriting C semantics for 9, but does not define what 9 means.
4. **Context without definition.** Permit limit comments and Farmington permit excerpts describe WET pass/fail reporting, optional retest entry, and conditional TRC monitoring—but none mention NODI, code 9, or a no-data indicator mapping.

### Not established (all packet candidate interpretations)

| Candidate | Packet status | Why insufficient |
|---|---|---|
| Standard EPA/NetDMR NODI legend | not_established | No codebook or glossary in workspace |
| Optional/conditional monitoring not required | not_established | Permit conditions exist but never tie them to NODI code 9 |
| Inherits NODI C | excluded | Contract forbids; codes on disjoint permits |
| No-discharge period | not_established | No NO DISCHARGE DMR instruction; zero NODI mentions in documents |

The packet's known limitations reinforce this: 36 FY2025 NODI-9 rows co-occur with WET retest and chlorine parameters, but **no workspace text maps NODI 9 to any condition**. EPA DMR Form 3320-1 general instructions are referenced by the permit but are **not in the workspace**.

## Evidence that supports the judgment

Admissible snippets establish **that** NODI code 9 appears on no-numeric-result rows and **that** surrounding permit context discusses related monitoring/reporting rules. They do **not** establish **what label or absence-of-data reason code 9 denotes**.

Under `PASS_TASK_ADJUDICATE.md` rules: a plausible interpretation is insufficient; CSV correlation is insufficient; snippets without workspace paths are inadmissible (none were used beyond those paths).

## What remains uncertain

The positive semantic label for NODI code 9—whether it indicates monitoring not required, a specific NetDMR no-data reason, no discharge, or another standardized EPA meaning—remains entirely unknown from frozen workspace evidence.

## Proposal disposition

**admit: UNRESOLVED** — no `dry_run/construction.py` was written.

A reusable semantic mapping in `construction.py` (e.g., extending `known` values for `nodi_code_semantics`) would assert World truth at vocabulary scope without `SOURCE_ESTABLISHED` grounding. The current construction already marks only empty `nodi_code` as known; values `9` and `C` correctly remain unresolved obligations affecting 36 and 150 FY2025 rows respectively per packet limitations.

## What would change if admitted

Admission would require workspace-sourced text explicitly defining NODI code 9 (or an EPA form instruction document present in the workspace). That would permit a disposable edit adding code `9` to the `known` list for `nodi_code_semantics` with grounding tied to the defining source—not inference from parameter co-occurrence or optional-monitoring flags.
