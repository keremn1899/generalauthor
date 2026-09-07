# Adjudication Review: pass_fail reporting semantics

## What I investigated

I read `PASS_TASK_ADJUDICATE.md`, the frozen `PACKET.json`, and `construction.py` (for a disposable mapping draft only). I did not search `documents/` or `sources/` beyond the retained snippets in the packet.

The obligation asks: what does PASS=0 / FAIL=1 reporting mean, and is it a numeric concentration comparison?

## What I found

The packet resolves the question in favor of categorical whole-effluent-toxicity (WET) outcome reporting, not ordinary numeric concentration comparison.

**Structured permit limits** (`sources/permit_limits.csv` snippets) define PASS=0 and FAIL=1 as explicit DMR entry codes in the CONCENTRATION MAX field. TEM3D rows carry `LIMIT_UNIT_DESC=pass=0;fail=1` with an empty `LIMIT_VALUE_NMBR`, indicating no numeric effluent limit is available for comparison. TOM3D rows in the same WET set use percent units for numeric NOEC reporting, contrasting pass/fail coding from concentration reporting.

**Permit narrative** (`documents/farmington/final_permit.txt` snippets) states the biological rule: enter 1 if NOEC for survival is less than the critical dilution (fail), otherwise enter 0 (pass). It separately directs numeric NOEC reporting on TOM3D/TOM6C. Retest parameters follow the same 0/1 rule. Acute test failure is defined as lethal effect at or below the critical dilution.

**Observed DMR data** (`sources/dmr_measurements.csv` snippet) shows TEM3D reported `DMR_VALUE_NMBR=0` with `DMR_UNIT_DESC=pass=0;fail=1` and no paired limit value, consistent with categorical outcome coding.

The candidate interpretation `numeric_concentration_comparison` is refuted by empty limit values, pass/fail unit descriptors, permit text separating NOEC concentration from pass/fail codes, and the relation contract that binary pass/fail coding is not ordinary concentration comparison.

## Evidence supporting resolution

| Source | Role |
|--------|------|
| `sources/permit_limits.csv` | Defines PASS/FAIL coding, pass=0;fail=1 units, empty numeric limits |
| `documents/farmington/final_permit.txt` | Authoritative biological meaning of 0 vs 1; separates NOEC concentration reporting |
| `sources/dmr_measurements.csv` | Confirms categorical 0/1 reporting with pass/fail units in practice |

All retained snippets use admissible workspace `source_id` paths. No snippet relied on non-workspace sources.

## What remains uncertain

- **Critical dilution value** is referenced in permit narrative but not encoded as `LIMIT_VALUE_NMBR` on pass/fail rows, so structured automation cannot independently compute pass/fail from concentration data.
- **Retest parameters** (six of twelve WET rows) are optional; semantics are established in permit text but occurrence-level applicability depends on whether a retest was required.
- **Permit scope** is limited to NM0020583 (Farmington); the resolution applies to this permit's WET vocabulary, not as general world truth.

The phrase "CONCENTRATION MAX" in DMR comments is noted as potentially misleading, but permit Part II clarifies it names the pass/fail entry field, not a concentration magnitude comparison.

## What would change if admitted

`PROPOSAL.json` recommends `ADMIT_DISPOSABLE`. The disposable edit in `dry_run/construction.py` would:

1. Detect `pass=0;fail=1` unit descriptions via a reusable pattern (not per-row judgments).
2. Derive a `pass_fail_outcome_reporting` relation for matching FY2025 measurement-limit pairs.
3. Register interpreted outcome values 0 (pass) and 1 (fail).
4. Stop emitting `pass_fail_reporting_semantics` unresolved obligations for rows matching the established unit-and-comment pattern.

This would resolve 12 affected permit-limit rows tied to the WET pass/fail vocabulary. It would not encode critical dilution thresholds, generalize beyond Farmington, or alter numeric comparison logic for parameters that have actual `LIMIT_VALUE_NMBR` values.

Production `construction.py` is unchanged per adjudication rules.
