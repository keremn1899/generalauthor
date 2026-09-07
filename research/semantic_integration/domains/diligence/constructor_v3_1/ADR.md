# ADR: Constructor v3.1 hardening

FOUNDATIONAL: kernel unchanged. Provenance kinds remain TaskView SOURCE/WORLD/ASSERTION/DERIVATION.

EXPERIMENTALLY_MOTIVATED: DISTINCT-only negative-closure gate after A1, because v3 T1 closed UNRESOLVED as DISTINCT on legal-form/jurisdiction mismatch.

DOMAIN_POLICY: required consumer identities include `active` (contract_active).

IMPLEMENTATION_DETAIL: `validate_provenance()` is constructor-runtime validation after P6. TaskView still accepts empty grounding; v3.1 rejects that World as invalid.
