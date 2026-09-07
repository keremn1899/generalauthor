"""Resume remaining Constructor v3 trials, then write the frozen report.

Safe to re-run: completed passes are skipped via sealed agent.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from research.semantic_integration.domains.diligence.constructor_v3.campaign import run_all_trials
from research.semantic_integration.domains.diligence.constructor_v3.report import write_report


def main() -> None:
    dest = ROOT / "axis_d"
    dest.mkdir(parents=True, exist_ok=True)
    payload = run_all_trials()
    (dest / "campaign.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    report = write_report()
    print(str(report))


if __name__ == "__main__":
    main()
