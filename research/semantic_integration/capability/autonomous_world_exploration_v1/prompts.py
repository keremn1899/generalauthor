"""Frozen prompts. No leads. No domain summaries."""

READ_RULES_SHORT = (
    "Follow HEADER.md READ RULES. Unresolved is not false. "
    "PURPOSE state does not replace more direct WORLD facts."
)

E0_AGENT = """You are a fresh analyst. You receive a compiled World and a compact semantic header.

Read HEADER.md and TASKS.md.

Use ordinary SQL/Python against `world/world.sqlite` as described in ACCESS.md.

There are no raw sources. Do not modify the World. Do not look for construction.py.

Write `answers.json`:

```json
{
  "answers": [
    {"id": "T1", "status": "ANSWERED"|"UNRESOLVED", "value": null, "rationale": "..."}
  ]
}
```

Cover T1–T6. Use UNRESOLVED when the World does not establish the answer.
"""

E1_ORIENT_AGENT = """You are a fresh analyst. You receive a compiled World and a compact semantic header.

Read HEADER.md and ACCESS.md.

Explore this World until you have a useful working understanding of its purpose-relevant structure. Inspect whatever relations, rows, relationships, unresolved state, or grounding you think will matter. Do not try to enumerate the whole database. Stop when you believe you understand enough to perform varied analyses over it.

Write compact working notes to `NOTES.md`. Do not dump every row. There are no downstream tasks in this workspace yet.

There are no raw sources. Do not modify the World.
"""

E1_TASK_AGENT = """You previously explored this World. Read HEADER.md, NOTES.md, ACCESS.md, and now TASKS.md.

Use ordinary SQL/Python against `world/world.sqlite`.

There are no raw sources. Do not modify the World.

Write `answers.json`:

```json
{
  "answers": [
    {"id": "T1", "status": "ANSWERED"|"UNRESOLVED", "value": null, "rationale": "..."}
  ]
}
```

Cover T1–T6. Use UNRESOLVED when the World does not establish the answer.
"""

E0_PROMPT = (
    "Read HEADER.md, ACCESS.md, and TASKS.md. "
    "Query world/world.sqlite with SQL/Python. Write answers.json for T1–T6. "
    "No raw sources. Do not modify the World."
)

E1_ORIENT_PROMPT = (
    "Read HEADER.md and ACCESS.md. Explore the World until you have a useful working "
    "understanding of its purpose-relevant structure. Inspect relations, rows, relationships, "
    "unresolved state, or grounding that you think will matter. Do not enumerate the whole database. "
    "Write compact NOTES.md. Stop when you understand enough for varied analyses. "
    "No raw sources. Do not modify the World."
)

E1_TASK_PROMPT = (
    "Read HEADER.md, NOTES.md, ACCESS.md, and TASKS.md. "
    "Query world/world.sqlite with SQL/Python. Write answers.json for T1–T6. "
    "No raw sources. Do not modify the World."
)
