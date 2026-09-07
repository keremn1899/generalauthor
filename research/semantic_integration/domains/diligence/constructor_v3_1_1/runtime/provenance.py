"""World provenance invariant. Not a kernel change. Constructor-runtime validation only.

Every durable World assertion must have SOURCE, WORLD, ASSERTION, or DERIVATION grounding.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

VALID_KINDS = {"SOURCE", "WORLD", "ASSERTION", "DERIVATION"}


def validate_provenance(world: Path) -> dict[str, Any]:
    if not world.exists():
        return {
            "ok": False,
            "reason": "missing_world",
            "ungrounded": [],
            "ungrounded_count": 0,
        }
    conn = sqlite3.connect(str(world))
    conn.row_factory = sqlite3.Row
    ungrounded: list[dict[str, Any]] = []
    try:
        rows = conn.execute(
            "SELECT assertion_id, relation_name, origin FROM _tv_assertions"
        ).fetchall()
        for row in rows:
            grounds = conn.execute(
                "SELECT kind, reference FROM _tv_groundings "
                "WHERE subject_type='ASSERTION' AND subject_id=?",
                (row["assertion_id"],),
            ).fetchall()
            kinds = {str(g["kind"]) for g in grounds if g["kind"] in VALID_KINDS and str(g["reference"] or "").strip()}
            if not kinds:
                ungrounded.append(
                    {
                        "assertion_id": row["assertion_id"],
                        "relation": row["relation_name"],
                        "origin": row["origin"],
                    }
                )
    except sqlite3.Error as exc:
        return {"ok": False, "reason": str(exc), "ungrounded": [], "ungrounded_count": 0}
    finally:
        conn.close()
    return {
        "ok": not ungrounded,
        "ungrounded_count": len(ungrounded),
        "ungrounded": ungrounded,
        "reason": None if not ungrounded else "ungrounded_durable_assertions",
    }
