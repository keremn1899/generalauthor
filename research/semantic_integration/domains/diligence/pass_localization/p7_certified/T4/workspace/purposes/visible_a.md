# Purpose A — contractual exposure of represented revenue

Using only the authoritative files in this data room, determine which represented billed revenue is associated with counterparties whose **active** contracts contain acquisition-relevant conditions.

Acquisition-relevant conditions, for this purpose, are contractual terms that:

- require consent or notice on a change of control; or
- permit termination upon a change of control; or
- require consent or notice before assignment (including assignment restricted except to affiliates, or assignment prohibited to a competitor).

An expired statement of work is not an active contract.

Report each qualifying invoice and the associated counterparty and contract identifiers as they appear in the sources. Include amount, currency, period, and invoice status.

Do not treat missing identity as a negative contractual finding. If a billed name and a contract counterparty cannot be confidently associated, say so rather than omitting or asserting a join.

Do not write a prose memo. Save a JSON result as `purpose_ir/a/output.json` with this shape:

```json
{
  "purpose": "contractual_revenue_exposure",
  "invoices": [
    {
      "invoice_id": string,
      "billed_name": string,
      "amount": number,
      "currency": string,
      "period": string,
      "status": string,
      "contract_id": string,
      "association": "asserted" | "unresolved"
    }
  ]
}
```

Sort invoices by `invoice_id`.
