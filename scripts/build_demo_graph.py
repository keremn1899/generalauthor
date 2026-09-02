#!/usr/bin/env python3
"""Build the local demo graph the product UI opens by default.

The launcher (`scripts/run_local_product.py`) and the operator backend default
to `data/demo/organisation-ops/graph.lbug`. That path lives under the gitignored
`data/` tree, so a fresh checkout has no graph to open and the UI comes up empty.

This script rebuilds that graph from committed inputs so the development
environment is reproducible: a small organisation-ops source and an
agent-authored encoding of it. It runs the same host-owned workbook boundary an
agent would use — prepare, validate, materialize — and is idempotent.

    uv run --extra all python scripts/build_demo_graph.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.atoms import main as workbook_main

SOURCES = ROOT / "scripts" / "demo_sources" / "organisation-ops"
SOURCE = SOURCES / "source.html"
ENCODING = SOURCES / "encoding.json"

OUT_DIR = ROOT / "data" / "demo" / "organisation-ops"
WORKBOOK = OUT_DIR / "workbook"
GRAPH = OUT_DIR / "graph.lbug"


def build() -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    rc = workbook_main(
        ["--workbook", str(WORKBOOK), "prepare", "--source", str(SOURCE)]
    )
    if rc != 0:
        raise SystemExit(f"prepare failed with exit code {rc}")

    rc = workbook_main(
        ["--workbook", str(WORKBOOK), "validate", "--encoding", str(ENCODING)]
    )
    if rc != 0:
        raise SystemExit(
            "encoding did not validate against the prepared workbook; the "
            "committed source and encoding have drifted apart"
        )

    rc = workbook_main(
        [
            "--workbook", str(WORKBOOK),
            "materialize",
            "--encoding", str(ENCODING),
            "--out", str(GRAPH),
        ]
    )
    if rc != 0:
        raise SystemExit(f"materialize failed with exit code {rc}")
    return GRAPH


def main() -> int:
    graph = build()
    print(f"Demo graph ready: {graph}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
