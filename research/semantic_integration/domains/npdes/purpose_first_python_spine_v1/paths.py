"""Paths for Purpose-First Python Spine Probe v1. Core/runtime must not import this package."""

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
SPINE_V1 = NPDES / "spine_compiler_probe_v1"
STRUCTURED = PARTICIPANT / "sources" / "structured"
FROZEN = ROOT / "frozen"
RUNS = ROOT / "runs"
REPORTS = ROOT / "reports"
LIVE_ROOT = Path("/tmp/world-experiment") / "npdes-purpose-first-python-spine-v1"
EXPERIMENT_ID = "npdes-purpose-first-python-spine-v1"
MODEL = "composer-2.5"
ADAPTER = "cursor-agent-bwrap-isolated-npdes-purpose-first-python-spine-v1"
MAX_CONSTRUCT_ITERS = 3
N_TRIALS = 5
TIMEOUT_SECONDS = 900
RUNNER_TIMEOUT_SECONDS = 120
