#!/usr/bin/env python3
"""Part B helper: print relation catalog from accepted World."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.semantic_integration.runtime_v0.world import ConstructionWorld  # noqa: E402


def main() -> None:
    db = ROOT / "world" / "world.sqlite"
    world = ConstructionWorld.open(db)
    try:
        print(json.dumps(world.taskview.describe(), indent=2, default=str))
        print(json.dumps({"admission": world.admission}, indent=2))
        if "purpose_requirement_failure" in world.admission:
            rows = world.query_semantic(
                "SELECT requirement_id, failure_kind, affected_identity, relation_name "
                "FROM purpose_requirement_failure"
            )
            print(json.dumps({"purpose_requirement_failure": rows}, indent=2, default=str))
    finally:
        world.close()


if __name__ == "__main__":
    main()
