# Purpose D — held out from the constructor

Do not place this file in the constructor workspace until A/B/C construction is frozen.

Using only the authoritative files in this data room, determine which counterparties have **open accounts receivable** and an **active** contract that requires **notice or consent before assignment**.

Change-of-control termination without an assignment notice/consent restriction is not sufficient. An expired statement of work is not an active contract.

If the billed party and the contracting party cannot be confidently associated, report the case as unresolved rather than as a negative.

Save JSON as `purpose_ir/d/output.json`:

```json
{
  "purpose": "open_ar_assignment_restriction",
  "cases": [
    {
      "invoice_id": string,
      "contract_id": string,
      "status": "matches" | "unresolved"
    }
  ]
}
```

Sort by `invoice_id`.
