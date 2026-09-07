from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
SEMANTIC = ROOT.parent
REPO = SEMANTIC.parent.parent
DILIGENCE = SEMANTIC / "domains" / "diligence"
V2 = DILIGENCE / "constructor_v2"
HIDDEN = DILIGENCE / "hidden"
FIXTURES = ROOT / "fixtures"
PARTICIPANT = FIXTURES / "frozen_participant_worlds"
CERTIFIED = FIXTURES / "certified"
METAMORPHIC = FIXTURES / "metamorphic_worlds"
SCORING = ROOT / "scoring"
REPORTS = ROOT / "reports"
MANIFEST = ROOT / "manifest.json"
SEED = 20260902
