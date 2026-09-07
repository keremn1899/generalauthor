from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
DILIGENCE = ROOT.parent
REPO = ROOT.parents[4]
V2 = DILIGENCE / "constructor_v2"
APPARATUS_SRC = V2 / "axis_a_apparatus"
AXIS_A = V2 / "axis_a"
HIDDEN = DILIGENCE / "hidden"
STRATEGIES = ROOT / "strategies"
SCORING = ROOT / "scoring"
REPORTS = ROOT / "reports"
APPARATUS = ROOT / "apparatus"
MANIFEST = ROOT / "manifest.json"
