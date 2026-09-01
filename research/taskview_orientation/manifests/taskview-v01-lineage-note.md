# TaskView v0.1 lineage note

This note records a provenance bookkeeping limitation without reconstructing or
claiming custody of unavailable historical bytes.

## Attested but unavailable transient artifact

The deterministic preflight receipt
`research/taskview_orientation/preflight/taskview-orientation-v01-deterministic.json`
attests the transient manifest digest:

```text
6e3f5498aaafa50da949857d3061525d2aa51afaa4e45a03b47b00af774c83e1
```

The corresponding manifest bytes are unavailable. This digest is retained as
an attested historical reference only. No fields are inferred from it and no
file is reconstructed or presented as that historical manifest.

## Earliest retained, hash-verifiable successors

```text
9d9adb6bf4a163ddf436392a4db3d9e24e9f527b02597684bedeb837fdf4ca61
    retained v0.1 repeat manifest

5a5126c2b044ac95fa1214413b9f371f9ff00b5a908f5e1fa90afbcfd83210cb
    retained unauthorized runtime-bound v0.1 manifest
```

The retained manifests mechanically preserve the original scientific-world,
TaskView-semantic, prompt, oracle, classification, threshold, and prospective
criterion hashes. The unavailable transient digest therefore affects only
provenance completeness, not the scientific experiment definition or
participant timing.
