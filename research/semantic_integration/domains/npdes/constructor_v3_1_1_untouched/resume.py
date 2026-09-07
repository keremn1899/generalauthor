"""Resume remaining NPDES Constructor v3.1.1 trials. Safe to re-run: completed passes skipped."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from research.semantic_integration.domains.npdes.constructor_v3_1_1_untouched.campaign import (
    run_all_trials,
)


def main() -> None:
    payload = run_all_trials()
    (ROOT / "campaign.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
