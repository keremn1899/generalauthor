# Adjudication review: obligation `nodi_9`

## Question

What does NODI code 9 mean for a FY2025 DMR row with no numeric result?

Purpose **C** requires interpreting `no_numeric_result_case.nodi_code` without inheriting semantics from NODI code C.

## What I investigated

I read only `PASS_TASK_ADJUDICATE.md`, `PACKET.json`, and `construction.py`. I did not search `documents/` or `sources/` beyond the frozen retained snippets and packet metadata.

From the packet I evaluated:

1. All four candidate interpretations and their stated statuses.
2. Eight retained snippets (six with admissible workspace `source_id` paths).
3. Contradictory evidence and known limitations bundled in the packet.
4. Whether `construction.py` already reflects the supported outcome.

## What I found

### Refuted or unsupported positive readings

| Candidate | Packet status | Why it fails on frozen evidence |
|-----------|---------------|----------------------------------|
| Not applicable / monitoring not required | Unsupported as uniform meaning | NODI 9 appears on both optional WET retest rows (`OPTIONAL_MONITORING_FLAG=Y`, freq `09/99`) and mandatory-flag chlorine rows (`OPTIONAL_MONITORING_FLAG=N`, freq `01/01`) on NM0020583. Permit text mentions "(If required)" for retests but does not name NODI 9. |
| No discharge during sampling month | Refuted for NODI 9 | Aztec `NO DISCHARGE REPORTING` applies to permit NM0028762 and instructs an "X" in a checkbox, not NODI code 9 on NM0020583. |
| Same meaning as NODI C | Refuted | NODI C occurs only on permit NM0000116; NODI 9 occurs only on NM0020583, on a different parameter set. |
| Indeterminate / legend absent | **Supported negative** | No workspace snippet defines NODI code 9; packet limitations confirm no structured codebook and no NM0020583 permit text mapping code 9. |

### Structural correlation is insufficient

CSV rows show that code 9 co-occurs with empty `DMR_VALUE_NMBR` across incompatible monitoring contexts. That pattern cannot yield a single permit-compliance meaning without an establishing legend or permit definition. The packet explicitly warns that structured data alone cannot distinguish conditional non-monitoring from missing evidence for chlorine rows.

### Authoritative permit text does not close the gap

Farmington permit snippets for NM0020583 discuss conditional TRC monitoring (footnote *5) and "(If required)" WET retest entry instructions. Neither passage references NODI code 9 or maps no-data reporting codes. Aztec no-discharge language governs a different permit and mechanism.

## Evidence that supports the judgment

**Disposition: SUPPORTED_NEGATIVE**

The source-supported proposition is negative: workspace sources **do not establish** what NODI code 9 means for FY2025 no-numeric-result rows.

Supporting admissible evidence:

- `sources/dmr_measurements.csv` — representative NODI 9 rows on NM0020583 for WET retest and chlorine parameters; separate NODI C row on NM0000116.
- `sources/permit_limits.csv` — linked limit rows showing optional vs non-optional flags for the two NODI-9 parameter families.
- `documents/farmington/final_permit.txt` — conditional monitoring and retest instructions without NODI 9 definition.
- `documents/aztec/final_permit.txt` — no-discharge checkbox instruction for a different permit.
- Packet `known_limitations` — no NODI codebook; no NM0020583 document mapping code 9.

**Epistemic basis:** SOURCE_ESTABLISHED (absence and refutation are grounded in retained workspace material, not model hypothesis or external training knowledge).

**Scope:** ONE_RELATION_OR_VOCABULARY (`no_numeric_result_case.nodi_code`, value `9`).

## What remains uncertain

The true regulatory or ICIS operational meaning of NODI code 9 is unknown in this workspace. The 36 NM0020583 occurrences may reflect one or more distinct compliance states (optional retest not triggered, chlorine not used, data not submitted, etc.) that cannot be resolved from the frozen packet.

## Proposal and construction impact

**Admit: UNRESOLVED** — no disposable construction edit.

`construction.py` already registers `nodi_code_semantics` with `known=[""]`, which correctly leaves `nodi_code` without established known values. There is no reusable semantic mapping to add without asserting ungrounded world truth. Per instructions, `dry_run/construction.py` was not written.

## What would change if admitted differently

- **ADMIT_DISPOSABLE with a positive mapping** (e.g., treating `9` as "not applicable") would incorrectly collapse contradictory parameter contexts and violate the relation contract that C and 9 must not inherit each other's semantics.
- **WORLD-scope positive truth** would require SOURCE_ESTABLISHED grounding from a codebook or permit definition naming code 9; the packet provides none.
- **New admissible evidence** — an NM0020583 permit passage or structured NODI legend in workspace sources naming code 9 — could support SUPPORTED_RESOLUTION and a scoped vocabulary mapping in a future disposable edit.
