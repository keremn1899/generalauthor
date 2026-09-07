# NPDES fixture freeze — before constructor inference

**Status**: Frozen 2026-09-03T19:00:24Z. No constructor model call before this file.

## Domain

EPA NPDES individual permit compliance, New Mexico, Federal FY2025 (2024-10-01 through 2025-09-30 inclusive).

## Facilities

Primary set retained. No substitution.

| NPDES | Facility | FY2025 DMR rows | Limit rows | Outfalls | Parameters |
|---|---|---|---|---|---|
| NM0020583 | City of Farmington WWTP | 504 | 58 | 001, TX1 | 28 |
| NM0028762 | City of Aztec Water Treatment Plant | 140 | 17 | 001 | 6 |
| NM0000116 | GCC Rio Grande | 180 | 30 | 001 | 7 |

Optional substitute Bosque Farms NM0030279 was **not** used. All three primaries have sufficient FY2025 monitoring evidence.

## Structured sources

Official ECHO ICIS-NPDES jurisdiction files:

- `https://echo.epa.gov/files/echodownloads/NPDES_by_state_year/NM_FY2025_NPDES_DMRS_LIMITS.zip`
- `https://echo.epa.gov/files/echodownloads/NPDES_by_state_year/NM_NPDES_EFF_VIOLATIONS.zip` (evaluator-only)

## Column split

Participant DMR retains native observations and regulatory metadata (permit, outfall, parameter, period, value, units, statistical base, limit, limit type, frequency, sample type, effective dates, NODI, optional-monitoring flag).

Removed from participant (answer labels, not evidence):

`REPORTED_EXCURSION_NMBR`, `DAYS_LATE`, `EXCEEDENCE_PCT`, `NPDES_VIOLATION_ID`, `VIOLATION_CODE`, `RNC_DETECTION_CODE`, `RNC_DETECTION_DATE`, `RNC_RESOLUTION_CODE`, `RNC_RESOLUTION_DATE`

Entire effluent-violations file is evaluator-only.

## Oracle

- GOLD M: independent mechanical exceedance from raw value vs numeric limit. 334 scoreable rows. 8 `ORACLE_CONFLICT` rows (Farmington BOD E90 / 99999% where reported value is below the numeric limit — treated as reporting-label disagreement, excluded from exact numeric scoring).
- GOLD S: 12 scored permit-prose clauses (staged TDS, cyanide schedule, TRC-when-chlorine, report-only tables, Aztec when-discharging / WET seasonal / Delta-BHC study, GCC event-dependent discharge / mixed numeric-report / first-discharge WET, source-authority hierarchy).
- GOLD E: 638 OBSERVATION_PRESENT, 150 ESTABLISHED_NO_DISCHARGE (NODI C), 36 ESTABLISHED_MONITORING_NOT_REQUIRED (NODI 9).

## Constructor freeze

Generic Constructor v3.1.1 prompts (pass_localization + domain-independent v3.1 hardening). No EPA ontology. No diligence consumer field list. No Purpose D in participant workspace.

See `fixture/manifests/manifest.json` for SHA-256 hashes.
