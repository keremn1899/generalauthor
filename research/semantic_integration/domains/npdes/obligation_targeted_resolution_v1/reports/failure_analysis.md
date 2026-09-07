# Failure analysis

## MEASURED establishability (hidden from host)

| obligation | evaluator label | note |
| --- | --- | --- |
| nodi_c | NOT_ESTABLISHABLE_IN_CORPUS | No NODI legend/codebook in permit packages or structured CSVs. Gold is hidden and is not corpus evidence. |
| nodi_9 | NOT_ESTABLISHABLE_IN_CORPUS | Same as C: no official code-9 definition in the frozen permit text or CSVs. |
| when_discharging | ESTABLISHABLE_IN_CORPUS | Aztec statement of basis: flow/TRC/pH monitored when discharging. CSV comment WHEN DISCHARGING on NM0028762 limits. Period-level discharge occurrence is a separate factual question. |
| geometric_mean | ESTABLISHABLE_IN_CORPUS | Farmington final permit footnotes *6/*7: report geometric mean of weekly TDS values; matches CSV comment language. Does not by itself reassign BOD rows that inherited a TDS comment. |
| pass_fail | ESTABLISHABLE_IN_CORPUS | Structured DMR_COMMENT_TEXT itself states PASS=0 FAIL=1 reporting for WET; Farmington permit footnote *9 points to Part II WET conditions. Encoding is in the structured comment. |
| empty_numeric_limit | UNCERTAIN_ESTABLISHABILITY | Empty LIMIT_VALUE_NMBR is visible in CSV; some WET/pass-fail rows are empty by design. Permit text may classify WET as report-only, but not every empty cell has a matching clause. |
| document_authority | UNCERTAIN_ESTABLISHABILITY | Document bodies exist, so some narrative conditions are readable. A general final-permit-over-fact-sheet legal hierarchy is not clearly established as a single corpus sentence covering all facilities. |
| monitoring_frequency | NOT_ESTABLISHABLE_IN_CORPUS | No frequency codebook mapping 05/WK etc. in the frozen permit packages. NMIP is referenced but not included as a source file. |

## OBSERVED

- unsupported_closures=0 (target 0)
- protocol_mismatches=['T2:geometric_mean']
- failed_dry_runs=['T2:pass_fail']
- mutated_before_evidence=0
- leakage_flags={}
- unresolved_by_mode={"EVIDENCE_INSUFFICIENT": 9, "OBLIGATION_TOO_BROAD": 3}
- extra_corpus Arm B=[] Arm A=[]

NODI C stayed UNRESOLVED on all three Arm B trials with failure_mode EVIDENCE_INSUFFICIENT, matching NOT_ESTABLISHABLE_IN_CORPUS.
NODI 9 stayed unadmitted; T3 returned SUPPORTED_NEGATIVE without ADMIT_DISPOSABLE (the code legend is still absent).
empty_numeric_limit was refined into comment-family children and left UNRESOLVED at parent grain — OBLIGATION_TOO_BROAD / EVIDENCE_INSUFFICIENT, not a retrieval miss of a single codebook.
T2 pass_fail dry-run crashed (`KeyError: 'limit_value_desc'`-class construction error). That is a disposable-apply failure, not a sibling-leakage event.
T2 geometric_mean admitted a TDS-scoped proposal while the parent disposition remained UNRESOLVED (protocol mismatch, grounded footnote evidence).
document_authority exceeded the 5-document soft budget (T1 wrote BUDGET_EXCEPTION.md) because the obligation spans three facilities.

An aborted first Arm A wave cited an extra-corpus EPA NODI legend. Those cases were deleted before sealing. See frozen/aborted_arm_a_wave.md.

## HYPOTHESIS

Establishability audit distinguishes retrieval quality from epistemic insufficiency. That distinction held for NODI codes.
