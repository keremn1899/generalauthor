"""Compact semantic header from the frozen World. No rows. No invented meanings."""

from __future__ import annotations

from pathlib import Path

from research.semantic_integration.runtime_v0.world import ConstructionWorld

READ_RULES = """Unresolved / insufficient / unknown / uninterpreted is not false.

An empty result alone means no matching tuple was observed, not established absence.

PURPOSE relations are purpose-specific analytical state and do not replace more direct WORLD facts.

Unknown neighboring propositions do not invalidate independently established propositions unless an explicit dependency says so.

Inspect grounding when evidential status matters.
"""

ACCESS = """The compiled World is `world/world.sqlite`. PYTHONPATH is this workspace.

```python
from research.semantic_integration.runtime_v0.world import ConstructionWorld
world = ConstructionWorld.open("world/world.sqlite")
rows = world.query_semantic("SELECT ...")
```

Ordinary Python and SQL are allowed. Do not modify the World. There are no raw sources.
"""


def render_header(*, purpose: str, world_dir: Path) -> str:
    db = world_dir / "world.sqlite"
    world = ConstructionWorld.open(db)
    try:
        described = world.taskview.describe()
        view = described.get("view") or {}
        revision = view.get("revision")
        lines = [
            "# Semantic header",
            "",
            "## PURPOSE",
            "",
            purpose.strip(),
            "",
            "## WORLD CONTRACT",
            "",
            "No rows are included. Meanings are constructor-authored; empty means none was provided.",
            "",
        ]
        by_name = {rel["name"]: rel for rel in (described.get("relations") or [])}
        for name in sorted(world.admission):
            rel = by_name.get(name) or {}
            meaning = str(rel.get("description") or "").strip() or "(none provided)"
            roles = rel.get("roles") or []
            role_text = ", ".join(f"{r.get('name')}:{r.get('type')}" for r in roles)
            scope = world.admission.get(name, "?")
            mode = rel.get("mode") or "?"
            lines.extend(
                [
                    f"### {name}",
                    f"meaning: {meaning}",
                    f"roles: {role_text}",
                    f"scope: {scope}",
                    f"mode: {mode}",
                    "",
                ]
            )
        lines.extend(
            [
                "## READ RULES",
                "",
                READ_RULES.strip(),
                "",
                "## REVISION",
                "",
                f"view_id={view.get('view_id')}; schema_revision={revision}",
                "",
            ]
        )
        return "\n".join(lines)
    finally:
        world.close()
