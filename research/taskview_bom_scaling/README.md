# BOM scaling and C2 preflight

This sibling research package extends, but does not overwrite, the completed
`research/taskview_bom/` experiment.

Generate and run:

```bash
uv run --extra dev python -m research.taskview_bom_scaling.run
uv run --extra dev pytest tests/taskview_bom_scaling -q
```

Key artifacts:

- `SPEC.md` freezes hypotheses, selection, accounting, and authorization rules.
- `scales/S1`, `S10`, and `S100` contain frozen sources, mutation, C0, and
  manifests.
- `results/scaling_seal.json` seals deterministic scale results before C2.
- `results/scaling_report.json` and `.md` contain curves and interpretation.
- `c2/packets/` contains the exact two participant-visible packets.
- `c2/adjudication_oracle.json` is hidden scoring state.
- `c2/packet_schema.json`, `output_schema.json`, and `protocol.json` are frozen.
- `c2/PRELFIGHT.json` is the requested fail-closed preflight receipt;
  `c2/PREFLIGHT.json` is an identically generated correctly spelled alias.

Generated result files follow repository convention and may be ignored by Git;
the scale sources, generator, protocol, and tests are source artifacts.

Live inference is not authorized, and the runner raises before reaching an
injected provider while the authorization flag remains false.
