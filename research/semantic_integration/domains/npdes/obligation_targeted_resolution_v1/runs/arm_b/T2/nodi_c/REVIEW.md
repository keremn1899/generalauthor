# Adjudication Review: nodi_c

## What was investigated

Obligation `nodi_c` asks: **What does NODI code C mean for a FY2025 DMR row with no numeric result?** The relation contract requires that `no_numeric_result_case.nodi_code` be interpreted before missing-evidence classification (purpose C).

I judged only the frozen packet in `PACKET.json` per `PASS_TASK_ADJUDICATE.md`. I did not search `documents/`, `sources/`, or any broader corpus.

## What was found

### Structural facts (mechanically established from workspace CSV snippets)

- **150 FY2025 DMR rows** on permit **NM0000116** have empty `DMR_VALUE_NMBR` and `NODI_CODE=C`.
- These rows link to a **storm-runoff limit set** (`DISCHARGE STORM RUNOFFS FROM STORAGE`) with **`OPTIONAL_MONITORING_FLAG=N`**.
- The pattern is concentrated on one permit; no other NODI codes share this C+empty-value pattern except separate NODI 9 rows on NM0020583.

### Document evidence (workspace permit text)

- **NM0000116 permit text** (`documents/gcc/final_permit.txt`) describes conditional storm-runoff discharge and standard DMR reporting obligations but **does not define NODI codes** or instruct how to report no discharge via code C.
- **NM0000116 fact sheet** (`documents/gcc/fact_sheet.txt`) notes the facility has not discharged in over five years but **does not map NODI C** to no-discharge reporting.
- **A different permit** (`documents/aztec/final_permit.txt`) instructs no-discharge reporting via a **DMR checkbox**, not NODI code C — and is not NM0000116's permit.

### Absence of definitional evidence

- `OBLIGATION.md` confirms **no codebook table** in structured sources and **no NODI definitional text** in `documents/`.
- Packet known limitations state external EPA ICIS/NODI documentation was **out of scope and not used**.

## Candidate interpretations assessed

| Label | Packet assessment |
|---|---|
| `documented_no_discharge_period` | Plausible from facility context, but permit text lacks no-discharge/NODI-C instruction; another permit uses a checkbox instead. Not established. |
| `conditional_monitoring_not_required` | Storm-runoff limits are conditional on discharge, but all C rows have `OPTIONAL_MONITORING_FLAG=N`, which contradicts a simple "monitoring not required" reading from flags alone. Not established. |
| `other_documented_no_data_state` | No workspace source defines any EPA/ICIS no-data reason for code C. Not established. |
| `missing_required_monitoring_evidence` | Cannot be confirmed; empty numeric field + code C could equally represent a documented no-data state. Not established. |

## What evidence supports the judgment

The packet's retained snippets and contradictory evidence collectively show:

1. **What happened structurally** — 150 rows carry `NODI_CODE=C` with no numeric result on NM0000116 storm-runoff limits.
2. **What is missing** — any workspace-authoritative definition of NODI code C.
3. **Why correlation is insufficient** — structural fields do not uniquely select among the four candidate interpretations (packet contradictory evidence, known limitations).

Per adjudication rules: a plausible interpretation is not enough; CSV correlation is not enough; snippets without workspace `source_id` paths are inadmissible (all retained snippets here are admissible, but none define code C).

## What remains uncertain

The semantic meaning of NODI code C for purpose-C missing-evidence classification. Without a workspace NODI legend or permit-specific code instruction, none of the candidate interpretations can be admitted as resolved truth.

## What would change if admitted

If a specific NODI C interpretation were **source-established** and admitted as `ADMIT_DISPOSABLE`, `construction.py` would need a reusable mapping in `purpose.require_interpreted("nodi_code_semantics", ...)` — extending `known` from `[""]` to include the admitted meaning for code `C` on relation `no_numeric_result_case`. That would unblock interpretation for **150 occurrences** under obligation `nodi_c`.

**No disposable edit was written** because disposition is `UNRESOLVED` and admit is `UNRESOLVED`. WORLD-scope semantic truth cannot be admitted without `SOURCE_ESTABLISHED` grounding.

## Disposition

**UNRESOLVED** — `failure_mode_if_unresolved`: `EVIDENCE_INSUFFICIENT`
