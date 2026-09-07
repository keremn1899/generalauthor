"""Paths for Probe v1.1. Core/runtime must not import this package."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
NPDES = ROOT.parent
V1 = NPDES / "prose_probe_v1"
REPO = ROOT.parents[4]
FIXTURE = NPDES / "fixture"
PARTICIPANT = FIXTURE / "participant_sources"
EVALUATOR = FIXTURE / "evaluator_only"
V311 = NPDES / "constructor_v3_1_1_untouched"
KERNEL = NPDES / "kernel_assets" / "KERNEL.md"
FROZEN_V1 = V1 / "frozen"
FROZEN = ROOT / "frozen"
RUNS = ROOT / "runs"
REPORTS = ROOT / "reports"
LIVE_ROOT = Path("/tmp/world-experiment") / "npdes-prose-probe-v1-1"
EXPERIMENT_ID = "npdes-prose-probe-v1-1"
MODEL = "composer-2.5"
ADAPTER = "cursor-agent-bwrap-isolated-npdes-prose-probe-v1-1"
SEALED_V1_B0_FULL = 0.33
SEALED_V1_B1_FULL = 0.90
SEALED_V1_B2_SAFE = 1.00
SEALED_V1_B2_UNSUPPORTED = 0.00
