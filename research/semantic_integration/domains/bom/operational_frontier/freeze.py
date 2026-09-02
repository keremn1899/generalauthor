"""Compile C1 and freeze the operational frontier.  Does not load C0."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from research.semantic_integration.domains.bom.compiler import compile_c1
from research.semantic_integration.domains.bom.operational_frontier.generate import (
    freeze_operational_frontier,
)

ROOT = Path(__file__).resolve().parent
FROZEN_PATH = ROOT / "operational_frontier.json"


def freeze(path: Path = FROZEN_PATH) -> dict:
    with tempfile.TemporaryDirectory(prefix="operational-frontier-c1-") as temporary:
        compilation = compile_c1(Path(temporary) / "c1.sqlite")
        try:
            return freeze_operational_frontier(compilation.view, path)
        finally:
            compilation.view.close()


if __name__ == "__main__":
    document = freeze()
    print(
        json.dumps(
            {
                "path": str(FROZEN_PATH),
                "fingerprint": document["fingerprint"],
                "candidate_replacement_pairs": document["candidate_replacement_pairs"],
                "candidate_case_count": document["candidate_case_count"],
                "obligation_count": document["obligation_count"],
                "provider_inference_calls": document["provider_inference_calls"],
            },
            indent=2,
            sort_keys=True,
        )
    )
