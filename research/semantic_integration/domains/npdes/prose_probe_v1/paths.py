"""Paths for the isolated NPDES prose probe. Core/runtime must not import this package."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
NPDES = ROOT.parent
REPO = ROOT.parents[4]
FIXTURE = NPDES / "fixture"
PARTICIPANT = FIXTURE / "participant_sources"
EVALUATOR = FIXTURE / "evaluator_only"
V311 = NPDES / "constructor_v3_1_1_untouched"
KERNEL = NPDES / "kernel_assets" / "KERNEL.md"
CORPUS = ROOT / "corpus" / "extracted"
FROZEN = ROOT / "frozen"
RUNS = ROOT / "runs"
REPORTS = ROOT / "reports"
LIVE_ROOT = Path("/tmp/world-experiment") / "npdes-prose-probe-v1"
EXPERIMENT_ID = "npdes-prose-probe-v1"
MODEL = "composer-2.5"
ADAPTER = "cursor-agent-bwrap-isolated-npdes-prose-probe-v1"
