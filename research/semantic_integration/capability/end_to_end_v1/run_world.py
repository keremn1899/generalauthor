#!/usr/bin/env python3
"""Host-facing: execute construction.py against frozen runtime_v0."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.semantic_integration.runtime_v0.project import Project  # noqa: E402


def main() -> None:
    project = Project(ROOT)
    result = project.run()
    payload = {
        "accepted": bool(result.accepted),
        "reason": result.reason,
        "errors": list(result.errors),
    }
    (ROOT / "diagnostics.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload))
    if result.accepted:
        world = project.open_accepted()
        try:
            description = world.taskview.describe()
            inventory = {
                "relations": description.get("relations"),
                "admission": world.admission,
            }
            (ROOT / "relation_inventory.json").write_text(
                json.dumps(inventory, indent=2, default=str) + "\n", encoding="utf-8"
            )
        finally:
            world.close()
        raise SystemExit(0)
    raise SystemExit(1)


if __name__ == "__main__":
    main()
