"""Frozen host and consumer prompts. Do not tune between trials."""

PASS_TASK = """You are an isolated experimental probe. You are a semantic integration engineer.

# Job

Given a local evidence folder and a declared purpose, compile a grounded programmable World using the frozen runtime in this workspace.

Read `purpose.txt` first. It is the primary input.

Then inspect `sources/` with ordinary Python and `research.semantic_integration.runtime_v0.source_helpers.Source`.

Author `construction.py` that defines:

```python
def construct(source, world, purpose):
    ...
```

Execute it with `python3 run_world.py` (PYTHONPATH is this workspace).

You may revise `construction.py` when the runtime rejects a candidate (compiler/validation errors).

Do not guess unsupported semantics. Leave genuine insufficiency unresolved via `purpose.unresolved(...)` or requirement failures.

Do not read files outside this workspace.

There is no gold file. There are no hidden questions in this workspace.

# Commitment

Durable WORLD BASE assertions require SOURCE grounding (file observations).
PURPOSE-scoped policy and `purpose_requirement_failure` rows may omit SOURCE.
Do not treat structural overlap as semantic identity unless you assert it with grounding.
Do not invent legends, waivers, emergencies, fuel schedules, or insurance coverage that the packet does not establish.

# Done

Finish with an accepted World under `accepted/` if the runtime will accept it, or the best justified construction.py you can write. Stop when `run_world.py` reports accepted=true, or after you cannot repair a validation error without guessing.
"""

FIRST_PROMPT = (
    "Read PASS_TASK.md and RUNTIME.md. Read purpose.txt. Inspect sources/. "
    "Write construction.py and run python3 run_world.py. "
    "Repair runtime/validation errors only. Do not invent unsupported meaning. "
    "Do not read files outside this workspace."
)

REPAIR_PROMPT = (
    "Read diagnostics.json. The last candidate was not accepted. "
    "Repair construction.py for runtime or grounding validation errors. "
    "Do not close unresolved semantics by guessing. Do not read files outside this workspace."
)

RUNTIME_MD = """# Frozen runtime_v0 (Spike 1)

`construction.py` must define `construct(source, world, purpose)`.

`python3 run_world.py` executes it into a candidate TaskView and publishes `accepted/` if validation passes.

## World commit API

```python
world.add_referent(id, label=..., observations=...)
world.declare_relation(name, [Role(...), ...], scope="WORLD"|"PURPOSE")
world.assert_tuple(relation, values, origin=ConstructionOrigin.MECHANICAL, grounding=source.grounding(file, location))
purpose.require_numeric(name, relation=..., field=..., per=...)
purpose.require_interpreted(name, relation=..., field=..., known=[...], per=...)
purpose.unresolved(name, relation=..., subject={...}, reason=...)
```

Role names and relation names must match `^[a-z][a-z0-9_]*$`.

WORLD BASE requires SOURCE grounding. PURPOSE policy may use `origin=ConstructionOrigin.ADJUDICATED` without SOURCE.

Injected names in construct(): Source helpers already constructed; Role, RoleType, ConstructionOrigin, AssertionGrounding, SourceObservation.

`source.grounding("jobs.csv", "job_id=J1")` is the usual SOURCE pointer.

Failures of purpose requirements become rows in `purpose_requirement_failure` (PURPOSE-scoped). That is success when evidence is insufficient.
"""

CONSUMER_WORLD_TASK = """You are a fresh analyst. You receive a compiled World and a purpose.

Read purpose.txt and QUESTIONS.md.

Inspect the World only:

```text
python3 inspect_world.py
```

You may write Python in this workspace that opens `world/world.sqlite` via the bundled TaskView / runtime (PYTHONPATH is this workspace).

Do not read `sources/`. There are no raw evidence files here.

Write `answers.json`:

```json
{
  "answers": [
    {"id": "Q1", "status": "ANSWERED"|"UNRESOLVED", "value": null, "rationale": "..."}
  ]
}
```

Use UNRESOLVED when the World does not establish the answer. Do not guess. Cover Q1–Q6.
"""

CONSUMER_RAW_TASK = """You are a fresh analyst. You receive a raw evidence folder and a purpose.

Read purpose.txt, QUESTIONS.md, and sources/.

Write `answers.json`:

```json
{
  "answers": [
    {"id": "Q1", "status": "ANSWERED"|"UNRESOLVED", "value": null, "rationale": "..."}
  ]
}
```

Use UNRESOLVED when the packet does not establish the answer. Do not guess. Cover Q1–Q6.
Do not read files outside this workspace.
"""
