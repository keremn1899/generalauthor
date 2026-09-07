#!/usr/bin/env python3
"""Part A helper: print catalogs for all domain Worlds."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.semantic_integration.runtime_v0.world import ConstructionWorld  # noqa: E402


def dump_world(label: str, db: Path) -> None:
    world = ConstructionWorld.open(db)
    try:
        print(json.dumps({"domain": label, "describe": world.taskview.describe()}, indent=2, default=str))
        print(json.dumps({"domain": label, "admission": world.admission}, indent=2))
        if "purpose_requirement_failure" in world.admission:
            rows = world.query_semantic(
                "SELECT requirement_id, failure_kind, affected_identity, relation_name "
                "FROM purpose_requirement_failure"
            )
            print(json.dumps({"domain": label, "purpose_requirement_failure": rows}, indent=2, default=str))
    finally:
        world.close()


def main() -> None:
    worlds = ROOT / "worlds"
    for path in sorted(worlds.iterdir()):
        db = path / "world.sqlite"
        if db.exists():
            dump_world(path.name, db)


if __name__ == "__main__":
    main()
