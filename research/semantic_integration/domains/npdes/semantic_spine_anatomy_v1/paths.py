"""Paths for Semantic Spine Anatomy & Minimality Probe v1. Research-only."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
NPDES = ROOT.parent
REPO = ROOT.parents[4]
PFPS = NPDES / "purpose_first_python_spine_v1"
PFPS_RUNS = PFPS / "runs"
FROZEN = ROOT / "frozen"
RUNS = ROOT / "runs"
REPORTS = ROOT / "reports"
COPIES = ROOT / "copies"
ABLATIONS = ROOT / "ablations"
EXPERIMENT_ID = "npdes-semantic-spine-anatomy-v1"
TRIALS = ("T1", "T2", "T3", "T4", "T5")
