# Dynamic consumer inventory

`service:external-worker` loads a consumer by tenant alias at runtime. The frozen
registry includes two concrete aliases and one wildcard fallback.

The wildcard can resolve plugins supplied outside this repository. There is no
complete alias-to-component export for production, so the worker's migration
scope mapping remains unresolved.

The loader implementation is `runtime/consumer_registry.py`.

