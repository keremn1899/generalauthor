"""Paths for Conversational Semantic Review Microprobes v1. Research-only."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
NPDES = ROOT.parent
REPO = ROOT.parents[4]
PFPS = NPDES / "purpose_first_python_spine_v1"
ANATOMY = NPDES / "semantic_spine_anatomy_v1"
FIXTURE = NPDES / "fixture"
PARTICIPANT = FIXTURE / "participant_sources"
EVALUATOR_GOLD = FIXTURE / "evaluator_only"
FROZEN = ROOT / "frozen"
EVALUATOR_ONLY = ROOT / "evaluator_only"
RUNS = ROOT / "runs"
REPORTS = ROOT / "reports"
LIVE_ROOT = Path("/tmp/world-experiment") / "npdes-conversational-semantic-review-v1"
EXPERIMENT_ID = "npdes-conversational-semantic-review-v1"
MODEL = "composer-2.5"
ADAPTER = "cursor-agent-bwrap-isolated-npdes-conversational-semantic-review-v1"
TIMEOUT_SECONDS = 720
RUNNER_TIMEOUT_SECONDS = 120
N_MP1_TRIALS = 3
N_MP3_TRIALS = 3
DRAFT_TRIAL = "T5"
