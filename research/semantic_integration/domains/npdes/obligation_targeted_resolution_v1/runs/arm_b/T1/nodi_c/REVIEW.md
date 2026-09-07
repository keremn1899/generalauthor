# Adjudication Review: nodi_c

## What was investigated

Obligation `nodi_c` asks: **What does NODI code C mean for a FY2025 DMR row with no numeric result?** The relation contract requires `no_numeric_result_case.nodi_code` to be interpreted before missing-evidence classification under Purpose C.

Judgment was limited to the frozen `PACKET.json`. No corpus search, no external EPA/NetDMR dictionaries, and no snippets whose `source_id` is not a workspace path.

## What was found

### Structural facts (mechanically derivable from CSV)

- 186 FY2025 rows have empty `DMR_VALUE_NMBR`; 150 carry `NODI_CODE=C` and 36 carry `NODI_CODE=9`.
- All 150 C-coded rows belong to `EXTERNAL_PERMIT_NMBR=NM0000116`.
- Every C-coded row has `OPTIONAL_MONITORING_FLAG=N`.
- C appears across six parameter codes in 10 monthly reporting events (15 parameters each), not on isolated flow rows alone.

These facts scope the obligation but do not supply a code legend.

### Workspace permit documents (NM0000116 / gcc package)

- `documents/gcc/final_permit.txt` requires daily flow reporting by estimate and electronic DMR submission via NetDMR. It does not define NODI codes and does not include a NO DISCHARGE checkbox instruction comparable to other permits in the inventory.
- `documents/gcc/fact_sheet.txt` describes very infrequent discharge. That context is compatible with empty numeric results but does not state that reporters use NODI C or what C documents.

### Construction state

- `construction.py` blocks Purpose C until `nodi_code` is interpreted for `no_numeric_result_case`. The only known value is the empty string; `C` is UNINTERPRETED.

### Candidate interpretations assessed in the packet

| Candidate | Packet status |
|-----------|---------------|
| Documented no discharge | not_established |
| Conditional monitoring not required | not_established_and_structurally_inconsistent (all C rows have `OPTIONAL_MONITORING_FLAG=N`) |
| Other authorized no-data state | not_established |
| Missing required evidence | not_established |
| Unresolved code | supported_by_absence_of_establishing_text |

## What evidence supports the judgment

**UNRESOLVED** is supported because:

1. No workspace source in the packet provides a NODI code definition or field legend for `NODI_CODE=C`.
2. Facility narrative and permit reporting requirements contextualize NM0000116 but do not map C to a named missing-evidence state.
3. CSV co-occurrence (C with empty numeric, single permit, batched parameters) identifies affected rows but is explicitly insufficient per adjudication rules.
4. The only structurally ruled-out candidate is "monitoring not required," via `OPTIONAL_MONITORING_FLAG=N` on all 150 rows. Ruling out one candidate does not establish any positive meaning for C.
5. Cross-permit no-discharge instructions (`documents/aztec/final_permit.txt` for NM0028762) show the workspace can contain such text, but that text is not in the NM0000116 package where all C rows occur and is not admissible as establishing evidence for this obligation.

## What remains uncertain

Without establishing text, it is unknown whether NODI C for these rows documents:

- permit-authorized no discharge,
- another authorized no-data reporting state (zero flow, not sampled, below quantification with authorized zero reporting),
- or required monitoring reported without a numeric result and without a source-established no-data authorization.

150 measurement occurrences remain blocked for Purpose C classification.

## What would change if admitted

**No disposable construction change is proposed** (`admit: UNRESOLVED`).

Admission would require `SOURCE_ESTABLISHED` grounding—e.g., a NODI codebook, NetDMR legend, or NM0000116 permit language explicitly defining C—and a reusable semantic mapping added to `known` in `purpose.require_interpreted("nodi_code_semantics", ...)`. Without that, adding `C` to `known` would encode model hypothesis as World truth, which is not permitted for vocabulary-scope obligations.

If establishing text were later found, a disposable `dry_run/construction.py` edit could extend `known` from `[""]` to include `C` with a documented meaning tied to that source, unblocking 150 affected rows for Purpose C downstream classification.
