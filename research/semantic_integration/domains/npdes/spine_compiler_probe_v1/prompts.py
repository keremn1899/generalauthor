"""Frozen host-agent prompts. Do not tune between trials."""

from __future__ import annotations

TIMEOUT_SECONDS = 600

PASS_TASK = """You are an isolated experimental probe. You are not running the product World constructor.

Write one Construction IR program. The host compiles it with a deterministic runtime you cannot edit. Do not emit trigger instances. Do not write domain-specific trigger rules. Do not look for hidden gold answers. They are not here. Do not read files outside this workspace.

# Workspace

- purposes/visible_a.md, visible_b.md, visible_c.md
- sources/dmr_measurements.csv
- sources/permit_limits.csv
- sources/document_inventory.json  (filenames, document kinds, hashes, bytes — no document text)
- PRINCIPLES.md
- CONSTRUCTION_IR.md  (the only IR you may author)
- diagnostics.json after a compile attempt (may be absent on the first attempt)

# Task

1. Read the three purposes and the IR spec.
2. Inspect the structured sources and document inventory metadata.
3. Author the minimum referents, maps, relations, and purpose requirements needed so that purpose A/B/C questions become executable over a mechanical spine.
4. Write exactly one JSON object to program.json following CONSTRUCTION_IR.md.
5. Stop. The host will compile. If diagnostics.json later says structurally_valid is false, revise program.json. Do not revise merely to chase trigger counts.

Dates in these CSVs are MM/DD/YYYY.

Do not copy TaskView APIs. Do not invent a new semantic primitive. Do not author keys: triggers, trigger_rules, gold, expected, families.

Declare base relations before derived relations that consume them.
"""

FIRST_PROMPT = (
    "Read PASS_TASK.md, PRINCIPLES.md, CONSTRUCTION_IR.md, and the files under purposes/ and sources/. "
    "Follow PASS_TASK.md exactly. Write program.json. Do not read files outside this workspace."
)

REPAIR_PROMPT = (
    "Read diagnostics.json. structurally_valid is false. Repair program.json so the host compiler "
    "can bind maps, types, and relations. Do not add trigger instances. Do not read files outside this workspace."
)
