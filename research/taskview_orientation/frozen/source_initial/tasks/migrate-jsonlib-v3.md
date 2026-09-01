# jsonlib v3 migration charter

Migrate commerce-owned production behavior from jsonlib v2 to v3.

Scope is established by composing production deployment membership, component
ownership, and a pinned v2 dependency. Do not infer scope from a source import
alone.

A compatibility adapter may count as protection only when its contract test
demonstrates canonical object-key ordering and string-preserving Decimal output.

Vendor-owned protocol boundaries remain on their supported v2 wire contract and
are excluded from direct code change. Their internals are not declared complete.

Dynamic consumers remain unresolved until every tenant alias can be mapped to a
deployable component from the frozen registry evidence.

Verification is task-relevant only when a test exercises the migration behavior,
not merely when a test file names the service.

