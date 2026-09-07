# ADR: Constructor v3 contract ABI

FOUNDATIONAL: TaskView kernel is unchanged.

EXPERIMENTALLY_MOTIVATED: default P5 is the Probe A A1 single adjudicator because it had the best observed risk/coverage point with semantic risk 0. Critics, proof gates, and the v2 cue verifier are not on the default path.

DOMAIN_POLICY: diligence consumer fields (`counterparty_text`, `billed_name`, …) are the purpose ABI, not global ontology names.

IMPLEMENTATION_DETAIL: normalizer emits ordinary tables (`invoice_record`, `contract_record`, …). Projector reads those tables.

Measured failure that justified `semantic_identity`: Probe B participant Worlds used constructor role `counterparty` while the consumer field is `counterparty_text`. No fuzzy name matching.
