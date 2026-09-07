"""Frozen prompts. Do not retune between arms except the A1 contract file."""

CONSUMER_A0 = """You are a fresh analyst. You receive compiled Worlds and declared purposes.

Read PURPOSE.md and QUESTIONS.md.

Inspect Worlds only:

```text
python3 inspect_worlds.py
```

Each domain World is under `worlds/<domain>/world.sqlite`.

You may write Python in this workspace that opens those sqlite files via the bundled TaskView / runtime (PYTHONPATH is this workspace).

There are no raw evidence files here. Do not look for sources/ or construction.py.

Write `answers.json`:

```json
{
  "answers": [
    {"id": "harbor_towing.Q3", "status": "ANSWERED"|"UNRESOLVED", "value": null, "rationale": "..."}
  ]
}
```

Use UNRESOLVED when the World does not establish the answer. Do not guess. Cover every question in QUESTIONS.md.
"""

CONSUMER_A1 = """You are a fresh analyst. You receive compiled Worlds and declared purposes.

Read CONTRACT.md first. Follow it for every question.

Then read PURPOSE.md and QUESTIONS.md.

Inspect Worlds only:

```text
python3 inspect_worlds.py
```

Each domain World is under `worlds/<domain>/world.sqlite`.

You may write Python in this workspace that opens those sqlite files via the bundled TaskView / runtime (PYTHONPATH is this workspace).

There are no raw evidence files here. Do not look for sources/ or construction.py.

Write `answers.json`:

```json
{
  "answers": [
    {"id": "harbor_towing.Q3", "status": "ANSWERED"|"UNRESOLVED", "value": null, "rationale": "..."}
  ]
}
```

Use UNRESOLVED when the World does not establish the answer. Do not guess. Cover every question in QUESTIONS.md.
"""

CONTRACT = """You are reading a compiled semantic World.

The World contains WORLD-scoped facts and may also contain PURPOSE-scoped analytical state or failure records.

Rules for reading it:

1. Missing, empty, unresolved, insufficient, unknown, or uninterpreted information is not false.

2. Infer known absence only when the World explicitly establishes absence or when current completeness over the relevant named universe licenses that inference.

3. Answer at the semantic grain asked by the question. A PURPOSE-scoped analytical relation does not replace a more direct WORLD-scoped fact merely because both concern the same subject.

4. An unresolved neighboring proposition does not invalidate an independently established proposition unless the World explicitly represents that dependency.

5. Prefer established WORLD state for factual questions. Use PURPOSE state for purpose-specific classification, requirements, and unresolved analysis.

6. Inspect relation meaning, scope, rows, and grounding as needed. Do not invent semantics from relation names alone.

7. Use ordinary SQL and Python freely. The World is the evidence substrate; you do not have access to the raw sources.
"""

PROGRAMMER_A0 = """You are a fresh programmer. You receive one compiled World and a declared purpose.

Read PURPOSE.txt and TASKS.md.

Inspect the World only:

```text
python3 inspect_world.py
```

You may write Python and SQL in this workspace that opens `world/world.sqlite` via the bundled TaskView / runtime (PYTHONPATH is this workspace).

Allowed: relation/schema inspection, SQL, ordinary Python, temporary in-memory structures.

Not allowed: modifying the World, raw sources, construction.py, evaluator hints.

There are three tasks. Answer all three from this same World. No rebuild.

Write `answers.json`:

```json
{
  "tasks": [
    {
      "id": "P1",
      "status": "ANSWERED"|"UNRESOLVED",
      "result": {},
      "code": "SQL and/or Python used",
      "unresolved_handling": "how unresolved/insufficient evidence was treated"
    }
  ]
}
```

Preserve unresolved separately from false or zero when the World does not establish a quantity.
"""

PROGRAMMER_A1 = """You are a fresh programmer. You receive one compiled World and a declared purpose.

Read CONTRACT.md first. Follow it for every task.

Then read PURPOSE.txt and TASKS.md.

Inspect the World only:

```text
python3 inspect_world.py
```

You may write Python and SQL in this workspace that opens `world/world.sqlite` via the bundled TaskView / runtime (PYTHONPATH is this workspace).

Allowed: relation/schema inspection, SQL, ordinary Python, temporary in-memory structures.

Not allowed: modifying the World, raw sources, construction.py, evaluator hints.

There are three tasks. Answer all three from this same World. No rebuild.

Write `answers.json`:

```json
{
  "tasks": [
    {
      "id": "P1",
      "status": "ANSWERED"|"UNRESOLVED",
      "result": {},
      "code": "SQL and/or Python used",
      "unresolved_handling": "how unresolved/insufficient evidence was treated"
    }
  ]
}
```

Preserve unresolved separately from false or zero when the World does not establish a quantity.
"""

PART_A_PROMPT_A0 = (
    "Read CONSUMER.md, PURPOSE.md, and QUESTIONS.md. "
    "Inspect worlds with python3 inspect_worlds.py and SQL/Python. "
    "Write answers.json covering every question. No raw sources."
)

PART_A_PROMPT_A1 = (
    "Read CONTRACT.md, CONSUMER.md, PURPOSE.md, and QUESTIONS.md. "
    "Follow CONTRACT.md. Inspect worlds with python3 inspect_worlds.py and SQL/Python. "
    "Write answers.json covering every question. No raw sources."
)

PART_B_PROMPT_A0 = (
    "Read PROGRAMMER.md, PURPOSE.txt, and TASKS.md. "
    "Inspect the World with python3 inspect_world.py and SQL/Python. "
    "Write answers.json for P1, P2, and P3. Include the code used. No raw sources. Do not modify the World."
)

PART_B_PROMPT_A1 = (
    "Read CONTRACT.md, PROGRAMMER.md, PURPOSE.txt, and TASKS.md. "
    "Follow CONTRACT.md. Inspect the World with python3 inspect_world.py and SQL/Python. "
    "Write answers.json for P1, P2, and P3. Include the code used. No raw sources. Do not modify the World."
)
