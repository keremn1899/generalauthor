# Agent-authored relational-materialization pilot

This is the executable form of the *smallest credible pilot* in
`docs/experiments/AGENT_AUTHORED_RELATIONAL_MATERIALIZATION_EXPERIMENT.md`.
It is research infrastructure, not a Graphauthor product path.

It freezes the first pilot matrix:

| Factor | Levels |
| --- | --- |
| Source heterogeneity | H0 prestructured, H2 mixed files |
| Schema novelty | N0 standard direct dependency, N2 task-specific composed relation |
| Reuse | cumulative prefixes R1, R2, R4, R8 |
| Arms | A ordinary, B generic relation store, C Graphauthor forced, D Graphauthor optional |

Each case begins with a hidden latent world. H0 and H2 render the same facts
and retain exactly the same oracle; only source fragmentation changes. The
agent only receives `agent/sources/` and `agent/workload.json`. The evaluator
oracle is never copied to an agent run workspace.

R8 is a coherent eight-question sequence, not eight copies of a question:
services for a resource, their capabilities, owners, tests, missing fallbacks,
production environments, a bounded path check, and the teams requiring
migration notification. R1/R2/R4 are prefixes of that same sequence.

The current Cursor CLI adapter is **one-shot**: it supplies a whole prefix in
one agent invocation and cannot yet preserve a Cursor session across sequential
follow-ups. This is recorded as an apparatus limitation; the harness does not
pretend that its R8 execution is sequential delivery.

## Generate cases

```bash
uv run --extra dev python -m research.relational_materialization generate \
  --out /tmp/relational-pilot --seeds 101 102 103
```

## Run an external agent

The harness deliberately has no model provider dependency. Run a generated
arm with an agent command and the harness creates a throwaway copy of each
visible workspace:

```bash
uv run --extra dev python -m research.relational_materialization run \
  --cases /tmp/relational-pilot/cases \
  --results /tmp/relational-pilot/results/agent-a \
  --arm A --agent-command 'your-agent-wrapper'
```

The command receives these environment variables:

- `RM_AGENT_WORKSPACE` — workspace to inspect and modify
- `RM_RESPONSE_PATH` — required response JSON path
- `RM_ARM` and `RM_ARM_RULE` — frozen arm contract
- `RM_ARM_TOOL_POLICY` — treatment-specific tool availability; agent wrappers
  must not mention Graphauthor to Arms A/B
- `RM_PARTICIPANT_PROMPT_PATH` — exact prebuilt arm-isolated prompt; pass it
  verbatim to the agent and retain it as the prompt audit artifact
- `RM_PROTOCOL` — protocol version

The response must contain one answer set per operation:

```json
{
  "answers": [{"operation_id": "op-01", "answer_ids": ["service:purchase"]}],
  "artifacts": {
    "representation_path": "optional/path/to/index-or-store",
    "graphauthor_workbook": "workbook-if-used"
  }
}
```

Arm B receives a pre-created SQLite file with `entities` and `relations`
tables before measurement. It must name a real store; paths are normalized
relative to the workspace or run root (including contained absolute paths), then
validated strictly. Arm C must name a workbook
containing `out/encoding.json`. The runner records wall time, stdout/stderr,
answer precision/recall, exact workload success, prompt path, workspace-derived
representation category/artifacts, visible relational-operation labels, and
arm-contract symptoms in `record.json`. Model tokens, calls, pricing, and
source-read telemetry belong in the external agent wrapper and should be
merged into the record before confirmatory use.

For arm isolation, pass the runner-produced prompt at `RM_PARTICIPANT_PROMPT_PATH`
without adding treatment language. The evaluator rejects declared or actual
Graphauthor artifacts in Arms A/B as treatment leakage.

## Smoke test

```bash
uv run --extra dev python -m research.relational_materialization smoke \
  --out /tmp/relational-pilot-smoke --seeds 11
```

This runs all 32 cell/arm combinations with a deterministic source-derived
participant. It validates case generation, isolation, oracle scoring, and arm
artifact checks only. It is explicitly not evidence of agent or Graphauthor
performance.
