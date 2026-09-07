"""Paths for Semantic Proposal & Scope Clarification Microprobe v1. Research-only."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
NPDES = ROOT.parent
REPO = ROOT.parents[4]
PFPS = NPDES / "purpose_first_python_spine_v1"
ANATOMY = NPDES / "semantic_spine_anatomy_v1"
CONVERSATIONAL = NPDES / "conversational_semantic_review_v1"
FIXTURE = NPDES / "fixture"
PARTICIPANT = FIXTURE / "participant_sources"
EVALUATOR_GOLD = FIXTURE / "evaluator_only"
FROZEN = ROOT / "frozen"
EVALUATOR_ONLY = ROOT / "evaluator_only"
RUNS = ROOT / "runs"
REPORTS = ROOT / "reports"
LIVE_ROOT = Path("/tmp/world-experiment") / "npdes-semantic-proposal-scope-v1"
EXPERIMENT_ID = "npdes-semantic-proposal-scope-v1"
MODEL = "composer-2.5"
ADAPTER = "cursor-agent-bwrap-isolated-npdes-semantic-proposal-scope-v1"
TIMEOUT_SECONDS = 720
DRAFT_TRIAL = "T5"
