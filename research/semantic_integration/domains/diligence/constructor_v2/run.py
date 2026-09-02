"""Run the frozen Constructor v2 campaign: B/C then A then D then report."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> None:
    from research.semantic_integration.domains.diligence.constructor_v2.axis_a import run_all as run_a
    from research.semantic_integration.domains.diligence.constructor_v2.axis_b import run_axis_b
    from research.semantic_integration.domains.diligence.constructor_v2.axis_c import run_axis_c
    from research.semantic_integration.domains.diligence.constructor_v2.axis_d import run_all_trials
    from research.semantic_integration.domains.diligence.constructor_v2.freeze import freeze
    from research.semantic_integration.domains.diligence.constructor_v2.report import write_report

    manifest = ROOT / "experiment_manifest.json"
    if not manifest.exists():
        freeze()
    print(json.dumps(run_axis_b(ROOT / "axis_b"), indent=2, sort_keys=True))
    print(json.dumps(run_axis_c(ROOT / "axis_c"), indent=2, sort_keys=True))
    print(json.dumps(run_a(), indent=2, sort_keys=True)[:4000])
    print(json.dumps(run_all_trials(), indent=2, sort_keys=True)[:4000])
    print(json.dumps(write_report(), indent=2, sort_keys=True)[:4000])


if __name__ == "__main__":
    main()
