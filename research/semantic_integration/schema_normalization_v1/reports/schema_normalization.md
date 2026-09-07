# Contract-Driven Schema Normalization Benchmark v1

Schema/IR compilation. No semantic adjudication. Not Constructor v3.
Semantic-family hints were not added.

## B0 — exact contracts

Certified World A/B/C/D exact after normalization: **true**. All seven canonical consumer relations recovered. Missed: none.

Participant Worlds (copied from Constructor v2 AXIS D; facts not repaired):

| Trial | Recovered | Missed | Normalized A/B/C/D | Raw projector A/B/C/D |
|---|---|---|---|---|
| T1 | invoice, clause, identity, registry | contract_record | F/F/F/F | F/F/F/F |
| T2 | invoice, clause, identity, registry | contract_record | F/F/F/F | F/F/F/F |
| T3 | invoice, clause, identity, crm, registry | contract_record | F/F/F/F | F/F/F/F |
| T4 | invoice, identity, crm, registry | contract_record | F/F/F/F | F/F/F/F |
| T5 | invoice, identity, crm, registry | contract_record | F/F/F/F | F/F/F/F |

## Metamorphic (certified World)

```
Class                     equiv    A/B/C/D exact
b1_rename                  True    True/True/True/True
b2_role_rename             True    True/True/True/True
b3_orientation             True    True/True/True/True
b4_physical                True    True/True/True/True
b5_epistemic               True    True/True/True/True
b6_decompose               True    True/True/True/True
b7_noise                   True    True/True/True/True
```

B7 `name_overlap` (MATCH/NO_MATCH) was not mapped into identity. False mappings: 0.

## STOP

Exact contracts were sufficient for every tested transformation of the certified World.

**semantic-family hints are not needed for normalization under the tested transformations.**

The optional family-hint condition was not run.

## MEASURED

- Certified B0 exact. Metamorphic B1–B7 behaviorally equivalent to Normalize(certified).
- Identity matched by disposition set, not relation name.
- Vertical invoice partition (B6) joined on the shared `invoice` role declared in contracts.
- Epistemic split (B5) preserved UNRESOLVED candidate IDs.
- Participant `contract_record` missed on 5/5: constructor role `counterparty` is not the consumer role `counterparty_text`.

## OBSERVED

- Participant A/B/C/D remain inexact after normalization, as they were under the raw projector. That is World content (under-closed identity, missing clauses) plus the counterparty role-name gap.
- Smallest missing semantic distinction is **stable consumer field/role identity** in contracts, not NEAR/IDENTITY/CONTAINS family types.

## HYPOTHESIS

- Constructor v3 should require relation contracts to bind roles to a published consumer field identity (or purpose field_sources), rather than introducing semantic-family primitives.
- Remaining participant inexactness vs hidden expected is not solved by schema family hints.

Frozen at 2026-09-02T13:33:48.186985+00:00.
