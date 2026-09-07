# NPDES Prose Compilation Probe v1

Sealed mechanism-localization experiment. Not Constructor v3.2.

- No constructor / kernel / P3 / P5 / admission / ABI edits
- No prompt tuning between conditions
- Frozen Composer 2.5
- Evaluator gold/cards never enter participant workspaces except permitted B1 passages and B2 oracle obligations without dispositions

Resume:

```bash
PYTHONPATH=. python3 -m research.semantic_integration.domains.npdes.prose_probe_v1.run_campaign
PYTHONPATH=. python3 -m research.semantic_integration.domains.npdes.prose_probe_v1.report
```

Completed conditions are skipped via `runs/**/agent.json`.
