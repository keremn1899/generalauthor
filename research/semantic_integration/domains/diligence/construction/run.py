#!/usr/bin/env python3
"""Compile the diligence World and purpose outputs."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from construction.derivations.derive_purposes import export_all
from construction.evidence_selector.resolve import apply_resolutions
from construction.mechanical_compiler.compile import compile_mechanical, run_derivations
from taskview import TaskView

WORLD_PATH = ROOT / "world" / "world.sqlite"


def main() -> None:
    if WORLD_PATH.exists():
        WORLD_PATH.unlink()
    with TaskView(WORLD_PATH, view_id="diligence-world") as tv:
        compile_mechanical(tv)
        obligations = apply_resolutions(tv)
        (ROOT / "world").mkdir(parents=True, exist_ok=True)
        (ROOT / "world" / "obligations.json").write_text(
            json.dumps(obligations, indent=2) + "\n"
        )
        run_derivations(tv)
        export_all(tv)
    print(f"Compiled {WORLD_PATH}")


if __name__ == "__main__":
    main()
