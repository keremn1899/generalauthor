"""Frozen host-agent prompts. Do not tune between trials."""

from __future__ import annotations

PASS_TASK = """You are an isolated experimental probe. You are not running the product World constructor.

# Your job

Author `construction.py`: a Python program that builds a purpose-sufficient semantic spine over the visible structured sources, then declares purpose requirements. The host will execute `construction.py` from scratch. You do not emit gold trigger instances. There is no `trigger()` API.

Begin with the purposes. They are the primary input.

# Purposes (read these first, unchanged)

- purposes/visible_a.md — applicable numeric discharge limits vs report-only for Federal FY2025
- purposes/visible_b.md — which monitoring requirements were actually applicable (including conditional/event/seasonal dependence)
- purposes/visible_c.md — missing-evidence / no-result semantics; missing data is not a denial

Ask yourself, then inspect evidence:

1. What ultimately has to be computable?
2. What distinctions must exist for those computations to be correct?
3. What source evidence could physically instantiate those distinctions?

Do not look for hidden gold answers. They are not here.

# Visible evidence

- sources/dmr_measurements.csv
- sources/permit_limits.csv
- sources/document_inventory.json  (filenames, kinds, hashes, bytes — no document text)
- source.py — structural helpers (tables, fields, profile, distinct_values, key_candidates, value_overlap, join, join_profile, document_inventory, parse_date, interval_contains)
- world_api.py — the only way durable semantic state may be committed
- PRINCIPLES.md
- WORLD_API.md

You may run ordinary Python, sqlite3, statistics, and these helpers. You may write extra helper modules. Exploratory computation is allowed and expected.

Do not read files outside this workspace.

# Commitment rule

Use arbitrary Python to explore and to compute mechanical tables.

All durable semantic state must enter through World / Purpose:

```python
from source import Source, parse_date, interval_contains
from world_api import World, Purpose

src = Source("sources")
world = World()
purpose = Purpose(world)

# world.referent / world.relation / world.map / world.derive
# purpose.require_unique / require_materializable / require_interpreted / require_numeric / unresolved
```

World vs purpose: if the current purpose disappeared, would the proposition still mean the same thing? If not, it is a purpose requirement.

Structured codes, qualifiers, comments, and other low-cardinality text may affect a purpose while remaining uninterpreted. Notice them. Profile them. If interpretation could change A/B/C, declare `require_interpreted` or `purpose.unresolved(...)`. Do not silently convert their textual meaning into World truth.

Do not hard-code domain answers such as “this comment means monitoring is conditional.” Identify the unresolved dependency instead.

# Done

Write construction.py so that a clean interpreter can execute it and produce a World. Optional: define `construct(source, world, purpose)`.

When construction.py is ready, stop. The host executes it from scratch. If you later see diagnostics.json with ok=false, repair construction.py.
"""

FIRST_PROMPT = (
    "Read PASS_TASK.md first, then the three files under purposes/. "
    "Those purposes are the primary input. Then inspect sources with source.py helpers as needed. "
    "Write construction.py following WORLD_API.md and PRINCIPLES.md. "
    "You may run exploratory Python in this workspace. Do not read files outside this workspace."
)

REPAIR_PROMPT = (
    "Read diagnostics.json. construction.py failed in a clean host run. "
    "Repair construction.py so it executes and builds a World through world_api. "
    "Do not add trigger instances. Do not read files outside this workspace."
)
