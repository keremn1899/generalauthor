"""Paths for Spine Compiler Probe v1. Core/runtime must not import this package."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
NPDES = ROOT.parent
REPO = ROOT.parents[4]
FIXTURE = NPDES / "fixture"
PARTICIPANT = FIXTURE / "participant_sources"
EVALUATOR = FIXTURE / "evaluator_only"
V311 = NPDES / "constructor_v3_1_1_untouched"
PROSE_V1 = NPDES / "prose_probe_v1"
PROSE_V11 = NPDES / "prose_probe_v1_1"
KERNEL_MD = NPDES / "kernel_assets" / "KERNEL.md"
STRUCTURED = PARTICIPANT / "sources" / "structured"
FROZEN = ROOT / "frozen"
RUNS = ROOT / "runs"
REPORTS = ROOT / "reports"
LIVE_ROOT = Path("/tmp/world-experiment") / "npdes-spine-compiler-probe-v1"
EXPERIMENT_ID = "npdes-spine-compiler-probe-v1"
MODEL = "composer-2.5"
ADAPTER = "cursor-agent-bwrap-isolated-npdes-spine-compiler-probe-v1"
MAX_COMPILE_ITERS = 3
N_TRIALS = 5
