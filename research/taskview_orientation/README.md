# TaskView orientation Stage 0 apparatus

This package operationalizes the five-phase RAW versus preconstructed-TaskView
experiment in `EXPERIMENT_DESIGN.md`. It is research infrastructure, not a
TaskView or Graphauthor product path.

Participant execution is disabled by policy and by the frozen manifest. The only
included session implementation is `ScriptedApparatusParticipant`, a deterministic
source-derived lifecycle probe used to validate the runner. It is not evidence
about agent performance.

## Frozen artifacts

`frozen/source_initial/` contains the participant-readable repository.
`frozen/phase4/` contains the exact replacement introduced after Phase 3.
`frozen/prompts.json`, `oracle.json`, `span_classification.json`, and
`tool_schemas.json` are the participant and evaluator contracts.
`grounding_ledger.json`, `parity_review.json`, and `leakage_audit.json` establish
RAW parity and treatment leakage boundaries. `taskview.sqlite` is the immutable
initial treatment fixture. `experiment_manifest.json` hashes the full package.

## Stateful lifecycle

`EpisodeRunner` creates one session object exactly once and invokes its `turn`
method five times. It rejects a changed session identity. A phase answer is
schema-validated and committed before the next prompt is released. The runner
replaces `tests/checkout_contract.py` after Phase 3 commits and before Phase 4 is
shown; it never edits TaskView state on the participant's behalf.

The model/provider adapter used after authorization must implement
`StatefulParticipantSession` with a genuine persistent provider conversation. A
wrapper that merely prepends earlier text is nonconforming.

## Participant tools

Both arms receive the same instrumented `search_source`, `read_source`, and
`write_scratch` operations. TASKVIEW additionally receives `describe`,
`query_sql`, `assertion`, and the experiment-only contract-bound `rerun`.
`rerun("verification_gap")` selects a fixture-owned completeness declaration;
participant completeness arguments are rejected.

## Stage 0 commands

Freeze inputs before authorization review:

```bash
uv run --extra dev python -m research.taskview_orientation freeze --replace
```

The replacement flag is intentionally explicit. Never refreeze after participant
execution begins.

Exercise both arms with the non-model scripted lifecycle probe:

```bash
stage0_dir=$(mktemp -d)
uv run --extra dev python -m research.taskview_orientation dry-run --out "$stage0_dir"
```

Run deterministic checks:

```bash
uv run --extra dev pytest tests/taskview tests/taskview_orientation -q
```
