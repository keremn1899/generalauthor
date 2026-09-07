# Adjudication review: pass_fail reporting semantics

## What I investigated

I read only `PASS_TASK_ADJUDICATE.md`, `PACKET.json`, and `construction.py`. I did not search `documents/` or `sources/` beyond the frozen packet snippets. The obligation asks: what does PASS=0 / FAIL=1 reporting mean, and is it a numeric concentration comparison?

## What I found

The retained packet evidence establishes a single coherent interpretation (`binary_wet_outcome_codes`) and refutes the alternatives.

**Structured permit limits** (`sources/permit_limits.csv`) carry an explicit DMR comment: report pass as `0` or fail as `1` in the concentration MAX field. The pass/fail parameter rows (e.g., TEM3D) have `LIMIT_UNIT_DESC=pass=0;fail=1` and an empty `LIMIT_VALUE_NMBR`, meaning there is no numeric effluent limit to compare against.

**Permit narrative** (`documents/farmington/final_permit.txt`) states in Part II §3.c that the reporter enters `1` when NOEC for survival is less than the critical dilution, otherwise `0`. Part II §D.b defines pass/fail in terms of WET statistical outcome (NOEC vs critical dilution), not numeric effluent-limit comparison. Part I assigns WET parameters a reporting obligation rather than a numeric concentration limit. The same section distinguishes separate numeric NOEC (%) parameters (TOM3D, etc.) from binary pass/fail fields.

**DMR measurements** (`sources/dmr_measurements.csv`) show FY2025 reporting with `DMR_VALUE_NMBR=0`, `DMR_UNIT_DESC=pass=0;fail=1`, and no limit numeric—consistent with outcome coding, not concentration comparison.

The contradictory evidence (TOM3D row with 23% limit) is acknowledged in the packet as non-dispositive: numeric NOEC reporting is a separate parameter family within the same WET program.

## Evidence supporting the judgment

| Source | What it establishes |
|--------|---------------------|
| `sources/permit_limits.csv` DMR_COMMENT_TEXT | Explicit PASS=0 / FAIL=1 DMR reporting instructions |
| `sources/permit_limits.csv` TEM3D limit row | Pass/fail unit legend; no numeric limit |
| `documents/farmington/final_permit.txt` Part II §3.c | 0=pass, 1=fail tied to NOEC vs critical dilution |
| `documents/farmington/final_permit.txt` Part II §D.b | Outcome determined by toxicity test, not limit comparison |
| `sources/dmr_measurements.csv` TEM3D measurement | Actual 0 entry with pass/fail units, no limit numeric |

Disposition: **SUPPORTED_RESOLUTION**. Epistemic basis: **SOURCE_ESTABLISHED** (direct permit text and structured field definitions, not CSV correlation alone). Scope: **ONE_RELATION_OR_VOCABULARY** (NM0020583 WET pass/fail coding for one limit set; not generalized to all permits).

The relation contract—that binary pass/fail coding is not ordinary concentration comparison—is satisfied.

## What remains uncertain

- The numeric critical dilution value is not in the retained excerpts.
- Optional retest rows without a reported value cannot be classified as pass, fail, or not-required from structured data alone.
- Generalization beyond this permit and WET limit set is not established.

These limitations are explicit in the packet and do not block resolution of the core semantic question for the affected vocabulary.

## What would change if admitted

`PROPOSAL.json` recommends **ADMIT_DISPOSABLE** with a reusable classifier in `dry_run/construction.py`:

- Detect pass/fail vocabulary via `pass=0;fail=1` unit descriptors and `PASS=0`/`FAIL=1` DMR comment patterns (not per-row IDs).
- Derive `wet_pass_fail_reporting` with `is_numeric_concentration_comparison=false` and outcome semantics `{0: pass, 1: fail}`.
- Clear `pass_fail_reporting_semantics` purpose.unresolved for matching rows and add interpreted requirements on the derived relation.

`construction.py` itself is unchanged. Numeric comparison derivation is already structurally correct (pass/fail rows lack `has_limit_value_nmbr`); the disposable edit documents and classifies the established semantics rather than altering comparison logic.
