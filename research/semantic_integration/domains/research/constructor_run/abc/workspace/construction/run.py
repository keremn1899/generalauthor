#!/usr/bin/env python3
"""Compile evidence room into world.sqlite and purpose outputs."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from construction.derivations.derive_purposes import register_derivations, run_derivations
from construction.mechanical_compiler.compile_sources import compile_sources
from construction.semantic_frontier.resolutions import apply_resolutions, write_obligations
from taskview import TaskView

WORLD_PATH = ROOT / "world" / "world.sqlite"


def export_purpose_json(tv: TaskView) -> None:
    rows_a = tv.query_semantic(
        "SELECT registry_id, publication_id, correspondence FROM purpose_a_study ORDER BY registry_id"
    )
    payload_a = {
        "purpose": "registered_outcome_traceability",
        "studies": [
            {
                "registry_id": row["registry_id"],
                "publication_id": row["publication_id"] or None,
                "correspondence": row["correspondence"],
            }
            for row in rows_a
        ],
    }
    (ROOT / "purpose_ir" / "a" / "output.json").write_text(
        json.dumps(payload_a, indent=2) + "\n",
        encoding="utf-8",
    )

    rows_b = tv.query_semantic(
        "SELECT left, right, epistemic FROM purpose_b_link ORDER BY left, right"
    )
    payload_b = {
        "purpose": "study_reconciliation",
        "links": [
            {"left": row["left"], "right": row["right"], "epistemic": row["epistemic"]}
            for row in rows_b
        ],
    }
    (ROOT / "purpose_ir" / "b" / "output.json").write_text(
        json.dumps(payload_b, indent=2) + "\n",
        encoding="utf-8",
    )

    rows_c = tv.query_semantic(
        "SELECT registry_id, dataset_id, status FROM purpose_c_study ORDER BY registry_id"
    )
    payload_c = {
        "purpose": "reanalysis_readiness",
        "studies": [
            {
                "registry_id": row["registry_id"],
                "dataset_id": row["dataset_id"] or None,
                "status": row["status"],
            }
            for row in rows_c
        ],
    }
    (ROOT / "purpose_ir" / "c" / "output.json").write_text(
        json.dumps(payload_c, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    if WORLD_PATH.exists():
        WORLD_PATH.unlink()

    with TaskView(WORLD_PATH, view_id="compiled-world") as tv:
        compile_sources(tv)
        obligations = apply_resolutions(tv)
        write_obligations(obligations)
        register_derivations(tv)
        run_derivations(tv)
        export_purpose_json(tv)
        print(tv.describe_text())


if __name__ == "__main__":
    main()
