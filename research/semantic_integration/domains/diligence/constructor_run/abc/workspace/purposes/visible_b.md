# Purpose B — counterparty identity reconciliation

Using only the authoritative files in this data room, identify represented customer and commercial identities across CRM, billing, the company registry, and contracts.

For each commercially relevant name or record, report whether it can be confidently treated as the same legal counterparty as other records, or whether that identification remains unresolved.

Do not globally merge records merely because two names look similar. Exact legal-form variants of the same registered name may be mechanical. Distinct registry entities with similar trade names are not automatically the same party.

Permit explicit unresolved identity. Missing a positive same-entity judgment is not a negative judgment.

Do not write a prose memo. Save a JSON result as `purpose_ir/b/output.json` with this shape:

```json
{
  "purpose": "counterparty_reconciliation",
  "links": [
    {
      "left": string,
      "right": string,
      "epistemic": "SAME_ENTITY" | "DISTINCT" | "UNRESOLVED"
    }
  ]
}
```

Use these identifier forms:

- CRM: `crm:<crm_account_id>`
- invoice billed name: `billing:<billed_name>`
- registry: `registry:<company_number>`
- contract: `contract:<filename without .md>`

Include every link that is required to connect a CRM account, its billed name, the contract that governs that relationship, and any registry row that is a candidate legal entity for that relationship. Sort by `left`, then `right`.
