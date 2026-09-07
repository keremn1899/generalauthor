"""Paths for Semantic Refinement & Admission Microprobe v1."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
NPDES = ROOT.parent
REPO = ROOT.parents[4]
PFPS = NPDES / "purpose_first_python_spine_v1"
OTR = NPDES / "obligation_targeted_resolution_v1"
ANATOMY = NPDES / "semantic_spine_anatomy_v1"
CONVERSATIONAL = NPDES / "conversational_semantic_review_v1"
PROPOSAL = NPDES / "semantic_proposal_scope_v1"
FIXTURE = NPDES / "fixture"
PARTICIPANT = FIXTURE / "participant_sources"
EVALUATOR_GOLD = FIXTURE / "evaluator_only"
PERMIT_TEXT = EVALUATOR_GOLD / "permit_text"
FROZEN = ROOT / "frozen"
EVALUATOR_ONLY = ROOT / "evaluator_only"
RUNS = ROOT / "runs"
REPORTS = ROOT / "reports"
LIVE_ROOT = Path("/tmp/world-experiment") / "npdes-semantic-refinement-admission-v1"
EXPERIMENT_ID = "npdes-semantic-refinement-admission-v1"
MODEL = "composer-2.5"
ADAPTER = "cursor-agent-bwrap-isolated-npdes-semantic-refinement-admission-v1"
TIMEOUT_SECONDS = 900
DRAFT_TRIAL = "T5"
N_TRIALS = 3
OBLIGATION_IDS = ("geometric_mean", "empty_numeric_limit", "document_authority")
