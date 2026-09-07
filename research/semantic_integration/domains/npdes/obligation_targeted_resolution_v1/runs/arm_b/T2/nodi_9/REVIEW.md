# Adjudication review: nodi_9

## What was investigated

Judgment was limited to the frozen `PACKET.json` and `PASS_TASK_ADJUDICATE.md`. No corpus search, no CSV re-query, and no use of training-data or external EPA NODI legends.

The obligation asks: **What does NODI code 9 mean for a FY2025 DMR row with no numeric result?** Purpose **C** requires interpreting `no_numeric_result_case.nodi_code` under the relation contract that **C and 9 must not inherit each other's semantics**.

## What was found

### Occurrence structure (admissible)

From `sources/dmr_measurements.csv` (retained snippets):

- All **36** rows with `NODI_CODE='9'` and empty `DMR_VALUE_NMBR` belong to permit **NM0020583**.
- They form **two clusters**:
  1. **12 rows**, parameter **50060** (total residual chlorine): `OPTIONAL_MONITORING_FLAG=N`, `LIMIT_FREQ_OF_ANALYSIS_CODE=01/01` (daily).
  2. **24 rows**, WET retest parameters **22415/22416/22418/22419/51443/51444**: `OPTIONAL_MONITORING_FLAG=Y`, `LIMIT_FREQ_OF_ANALYSIS_CODE=09/99`.
- All **150** rows with `NODI_CODE='C'` are on permit **NM0000116** with disjoint parameters. No workspace row links code 9 to code C.

### Permit and limit context (admissible)

From `sources/permit_limits.csv` and `documents/farmington/final_permit.txt`:

- Parameter **50060** is nominally **required** daily grab monitoring on NM0020583.
- Footnote **\*5** states TRC shall be monitored **only when chlorine is used** for disinfection, cleaning, maintenance, or other purposes. It does **not** name NODI code 9 or specify which no-data code applies when chlorine is unused.
- WET retest parameters are **optional** (`OPTIONAL_MONITORING_FLAG=Y`). Part II **§D.3** reporting text labels retests **"(If required)"** and gives pass/fail entry rules. It does **not** define NODI code 9 or state that omission maps to code 9.

### Construction state (admissible)

`construction.py` declares `nodi_code_semantics` with `known=['']` only. Nonempty codes, including `'9'`, remain **UNINTERPRETED** for purpose C.

### Absence of code legend (admissible)

`OBLIGATION.md` and packet limitations confirm: **no NODI code definition, DMR form instructions, or ICIS codebook** appear in the workspace. `LIMIT_FREQ_OF_ANALYSIS_CODE` value `09/99` has no document legend.

## What evidence supports

| Claim | Support | Limit |
| --- | --- | --- |
| NODI=9 and NODI=C must not be equated | Partition by permit and parameter context in CSV snippets; relation contract | Does not define what 9 **does** mean |
| NODI=9 rows are structurally heterogeneous | Two distinct clusters within the 36 rows | Structural correlation is not semantic definition |
| TRC monitoring is conditionally required | Footnote *5 in `final_permit.txt` | No link to code 9 |
| WET retest reporting is conditional | Part II §D.3 "(If required)" text | No link to code 9 |
| Code 9 semantics cannot be read from structured fields alone | No codebook; contradictory cluster directions in packet | — |

The packet's **contradictory_evidence** is decisive: optional WET retest rows suggest permitted non-reporting, while required daily TRC rows suggest conditional non-activation of an otherwise scheduled parameter—**opposite directions under one code**, with **no workspace text resolving which applies to code 9**.

Candidate interpretation **"No discharge (same as NODI code C)"** is structurally rejected by the occurrence partition, but that negative finding does not supply a positive meaning for code 9.

## What remains uncertain

- The authoritative semantic label for NODI code **9** on ICIS/DMR reporting forms.
- Whether code 9 denotes one unified concept or context-dependent reporting practice that happens to share a code.
- How FY2025 rows in each cluster should be classified for purpose C (permitted omission, condition not met, missing evidence, or other).

## Disposition and proposal

- **JUDGMENT disposition: UNRESOLVED** — admissible workspace evidence does not establish what NODI code 9 means; plausible interpretations and CSV clustering are insufficient.
- **PROPOSAL admit: UNRESOLVED** — no reusable semantic mapping can be admitted without asserting unstated codebook knowledge or per-cluster model judgments.
- **`construction.py` unchanged** — no `dry_run/construction.py` disposable edit was written.

## What would change if admitted

Admission would require a **SOURCE_ESTABLISHED** or contract-sufficient reusable rule mapping `nodi_code='9'` into known semantics for `no_numeric_result_case` (e.g., extending `known=[...]` or adding a derived interpretation relation). That would resolve obligation **nodi_9** for **36** FY2025 no-numeric-result rows on NM0020583. Without a workspace NODI definition or unambiguous permit text tying code 9 to a single meaning, any admitted mapping would be **UNVERIFIED** at WORLD scope and would incorrectly collapse two contradictory cluster readings into one code label.
