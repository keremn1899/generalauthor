# Minimal non-software TaskView experiment

This research spike tests the existing `taskview` relational core against one
small parts/BOM integration problem. It is not a TaskView product revision and
does not add a construction path.

## Frozen object

- `fixtures/` contains 12 manufacturer parts, 12 supplier listings, four BOM
  requirements, two qualified replacement notes, and one frozen X100 mutation.
- `oracle.json` is C0: the hand-authored intended relation extensions and a
  construction-origin classification (`MECHANICAL`, `SEMANTIC`, or `DERIVED`)
  frozen before C1 evaluation. It contains semantic state, not question-specific
  answer fields.
- `experiment.py` is C1: four structural parsers, deterministic exact-identifier
  seams, TaskView materialization, four inspectable SQL derivations, C0
  comparison, mutation, and frontier packet selection.
- `report.json` and `frontier_packets.json` are deterministic generated results.

The compiler never imports a model SDK or invokes a provider. The only
replacement facts it compiles from Markdown are exact `Candidate:` records.
The two context-qualified acceptance judgments remain in the frontier.

Every mechanically asserted BASE tuple has a TaskView `SOURCE` grounding whose
detail identifies the source, SHA-256 fingerprint, native record location, and
construction method. The oracle's two semantic assertions separately identify
their exact note spans and hand-authored judgment method.

## Run

```bash
uv run --extra dev python -m research.taskview_bom.experiment \
  --output research/taskview_bom
uv run --extra dev pytest tests/taskview_bom -q
```

The SQLite database is temporary and deliberately not a research artifact.

## Result boundary

C1 establishes 178 of 180 C0 tuples. The unresolved frontier is exactly two
`acceptable_replacement(new_part, old_part, context)` tuples. The frozen
temperature mutation changes one observation and two BASE tuple memberships;
only `temperature_compatible` and its `eligible_part` dependent become stale.

The frontier packets select eight of 30 records, but their serialized form is
larger than the tiny source universe because exact grounding and normalized fact
metadata repeat per packet. The report records this as a negative result rather
than optimizing the packet format in this spike.
