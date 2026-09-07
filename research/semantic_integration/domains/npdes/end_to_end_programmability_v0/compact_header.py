"""Compact read contract. No rows. Per-state revision from the compiled World."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

READ_RULES = """Unresolved / insufficient / unknown / uninterpreted is not false.

A missing positive tuple is not an established negative.

PURPOSE relations are purpose-specific analytical state and do not replace more direct WORLD facts.

Unknown neighboring propositions do not invalidate independently established propositions unless an explicit dependency says so.

Inspect grounding when evidential status matters.

Do not invent NODI code meanings. Do not infer legends from value frequencies.
"""


def render_header(state_dir: Path) -> str:
    db = state_dir / "accepted" / "world.sqlite"
    purpose = json.loads((state_dir / "accepted" / "world.purpose.json").read_text(encoding="utf-8"))
    admission = json.loads((state_dir / "accepted" / "world.admission.json").read_text(encoding="utf-8"))
    meta = json.loads((state_dir / "compile_meta.json").read_text(encoding="utf-8"))
    conn = sqlite3.connect(db)
    try:
        rels = conn.execute(
            "SELECT name, mode, derived, description, roles_json FROM _relation_meta ORDER BY name"
        ).fetchall()
        reqs = conn.execute("SELECT DISTINCT name, kind FROM _requirement ORDER BY name").fetchall()
    finally:
        conn.close()
    lines = [
        "# Semantic header",
        "",
        "## PURPOSE",
        "",
        "Declared purposes for this accepted World (Federal FY2025 NPDES monitoring/compliance):",
        "",
        "### A — applicable discharge limits",
        "",
        purpose["A"].strip(),
        "",
        "### B — monitoring obligations",
        "",
        purpose["B"].strip(),
        "",
        "### C — missing-evidence semantics",
        "",
        purpose["C"].strip(),
        "",
        "## WORLD CONTRACT",
        "",
        "No rows are included. Relation names are constructor-authored. Empty description means none was provided.",
        "",
        f"state: {meta.get('state_id')}",
        f"proposals_admitted_to_this_copy: {', '.join(meta.get('proposal_ids') or []) or '(none — baseline T5)'}",
        "",
    ]
    for name, mode, derived, description, roles_json in rels:
        roles = json.loads(roles_json)
        role_text = ", ".join(f"{r.get('name')}:{r.get('type')}" for r in roles)
        lines.extend(
            [
                f"### {name}",
                f"meaning: {str(description or '').strip() or '(none provided)'}",
                f"roles: {role_text}",
                f"scope: {admission.get(name, mode)}",
                f"mode: {mode}",
                f"derived: {bool(derived)}",
                "",
            ]
        )
    lines.extend(["## PURPOSE REQUIREMENTS (names only)", ""])
    for name, kind in reqs:
        lines.append(f"- {name} ({kind})")
    lines.extend(
        [
            "",
            "## READ RULES",
            "",
            READ_RULES.strip(),
            "",
            "## REVISION",
            "",
            f"state_id={meta.get('state_id')}; world_sha256={meta.get('world_sha256')}; construction_sha256={meta.get('construction_sha256')}",
            "",
            "## ACCESS",
            "",
            "The compiled World is `accepted/world.sqlite`. Ordinary SQLite and Python are allowed.",
            "Do not modify the World. There are no raw source files in the consumer workspace.",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def write_header(state_dir: Path) -> Path:
    text = render_header(state_dir)
    path = state_dir / "compact_header.md"
    path.write_text(text, encoding="utf-8")
    return path
