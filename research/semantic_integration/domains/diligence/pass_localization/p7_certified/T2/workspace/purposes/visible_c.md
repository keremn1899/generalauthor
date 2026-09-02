# Purpose C — commercial obligation / dependency

Using only the authoritative files in this data room, compute a commercial dependency view.

A counterparty is commercially dependent, for this purpose, when both of the following hold:

1. There is a current commercial relationship: an **open** invoice, or an **active** contract that auto-renews or continues on a rolling term.
2. The active contract contains an **exclusivity** commitment, or a **term auto-renewal**, or a **rolling term** that continues unless notice is given.

Expired contracts do not create current dependency. A one-off paid historical invoice without an active contract does not.

Identify the counterparty using the same identifier forms as purpose B. If identity needed to join invoice and contract is unresolved, report the dependency as unresolved rather than as false.

Do not write a prose memo. Save a JSON result as `purpose_ir/c/output.json` with this shape:

```json
{
  "purpose": "commercial_dependency",
  "dependencies": [
    {
      "counterparty": string,
      "contract_id": string,
      "open_invoice_ids": [string],
      "obligation_kinds": [string],
      "status": "dependent" | "unresolved"
    }
  ]
}
```

`obligation_kinds` is a sorted list drawn from `exclusivity`, `auto_renewal`, `rolling_term`. Sort dependencies by `contract_id`.
