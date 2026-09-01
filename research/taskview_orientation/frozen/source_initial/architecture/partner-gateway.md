# Partner gateway boundary

`service:partner-gateway` is operated by the vendor-integrations team and calls a
vendor endpoint whose signed request contract is pinned to jsonlib v2.

The vendor validates the exact bytes of `signed_body`. Re-encoding that field
with v3 changes the signature input and is not permitted in this migration.

The gateway is a relevant boundary, but the vendor's internal consumers and
their dependency inventory are opaque to the commerce migration.

