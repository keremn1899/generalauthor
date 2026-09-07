# Adjudication Review: pass_fail

## What was investigated

The frozen packet for obligation `pass_fail` asks: **What does PASS=0 / FAIL=1 reporting mean, and is it a numeric concentration comparison?**

Investigation was limited to `PASS_TASK_ADJUDICATE.md`, `PACKET.json`, and (for disposable drafting) `construction.py`. No corpus search was performed.

## What was found

### Positive resolution: binary WET outcome codes

Workspace sources establish that PASS=0 / FAIL=1 is a **categorical whole-effluent-toxicity (WET) pass/fail coding scheme**, not a pollutant concentration:

1. **Structured limit definition** (`sources/permit_limits.csv`, LIMIT_VALUE_ID=3610839676): the DMR comment explicitly instructs reporters to enter `'0'` for pass or `'1'` for fail in the concentration-max field.

2. **Unit and threshold structure** (`sources/permit_limits.csv`, TEM3D row): pass/fail parameters use unit `9A` with description `pass=0;fail=1` and **empty** `LIMIT_VALUE_NMBR`, indicating no numeric limit threshold for comparison.

3. **Observed reporting** (`sources/dmr_measurements.csv`): a FY2025 measurement reports `DMR_VALUE_NMBR=0` with unit `9A`, matching pass/fail coding rather than a concentration magnitude.

4. **Authoritative permit text** (`documents/farmington/final_permit.txt`, Part II reporting table): enter `"1"` when survival NOEC is **less than** critical dilution (fail), otherwise `"0"` (pass). Retest rows repeat the same rule.

5. **Underlying criterion** (`documents/farmington/final_permit.txt`, lines 390–393): acute test failure is defined as a statistically significant lethal effect at or below critical dilution—a toxicity outcome, not concentration arithmetic.

### Negative resolution: not numeric concentration comparison

The `numeric_concentration_comparison` candidate is **refuted** by the same evidence:

- Permit text and DMR comment define 0/1 as pass/fail codes, not concentrations.
- Pass/fail parameters lack numeric `LIMIT_VALUE_NMBR`; companion TOM3D reports a numeric 23% NOEC limit under a separate reporting instruction (permit line 515).

### Scoped nuance: shared comment, different regimes

Four of twelve affected limit rows (TOM3D, TOM6C, TQM3D, TQM6C) share the PASS/FAIL comment at the limit-set level but carry numeric percent limits and separate NOEC reporting instructions. The binary 0/1 semantics apply to **TEM and retest parameters** (8 rows), not those four.

## Evidence supporting the judgment

| Source | Role |
|--------|------|
| `sources/permit_limits.csv` | Defines 0/1 legend, unit 9A, empty numeric limit for TEM; numeric 23% limit for TOM companion |
| `sources/dmr_measurements.csv` | Confirms literal 0 reported with pass/fail unit in practice |
| `documents/farmington/final_permit.txt` | Authoritative mapping of 0/1 to NOEC vs critical dilution; separates TOM numeric NOEC reporting |

All retained snippets use admissible workspace paths. No contradictory evidence is in the packet.

## What remains uncertain

- **Critical dilution magnitude** is not stated in retained structured rows; only the comparison logic (NOEC vs critical dilution) is established.
- **Sublethal retest parameters** (22418, 22419) use the same 0/1 structured coding; permit retest text inspected references survival NOEC for retests 1–3.

These gaps do not block resolving the core question (meaning of 0/1 and whether it is numeric concentration comparison).

## What would change if admitted

`PROPOSAL.json` recommends `ADMIT_DISPOSABLE` with scope `ONE_RELATION_OR_VOCABULARY` and `SOURCE_ESTABLISHED` grounding.

If admitted, `dry_run/construction.py` would:

1. Classify pass/fail limit rows by **unit 9A / pass=0;fail=1 with empty numeric limit** (reusable rule), not by shared comment alone.
2. Derive `binary_pass_fail_limit` and `binary_pass_fail_measurement` relations for those rows.
3. Remove blanket `pass_fail_reporting_semantics` unresolved holes for the 8 binary pass/fail rows.
4. Leave TOM/TQM numeric NOEC rows outside the pass/fail unresolved bucket.

`construction.py` itself is unchanged per adjudication protocol; only the disposable dry-run copy is modified.

## Disposition

**SUPPORTED_RESOLUTION** — workspace sources establish that PASS=0/FAIL=1 is binary WET outcome coding (NOEC vs critical dilution) and is **not** ordinary numeric concentration comparison against `LIMIT_VALUE_NMBR`.
