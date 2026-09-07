"""Paths for End-to-End Programmability Probe v0."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
NPDES = ROOT.parent
REPO = ROOT.parents[4]
PFPS = NPDES / "purpose_first_python_spine_v1"
OBLIGATION = NPDES / "obligation_targeted_resolution_v1"
ANATOMY = NPDES / "semantic_spine_anatomy_v1"
FIXTURE = NPDES / "fixture"
PARTICIPANT = FIXTURE / "participant_sources"
FROZEN = ROOT / "frozen"
STATES = ROOT / "states"
CONSUMERS = ROOT / "consumers"
ISOLATED = ROOT / "isolated_consumer"
OUTPUTS = ROOT / "outputs"
DIFFS = ROOT / "diffs"
FRESH = ROOT / "fresh_agent"
FAILURE = ROOT / "failure_path"
MANUAL = ROOT / "manual_inspection"
REPORTS = ROOT / "reports"
EVALUATOR_ONLY = ROOT / "evaluator_only"
RUNS = ROOT / "runs"
LIVE_ROOT = Path("/tmp/world-experiment") / "npdes-end-to-end-programmability-v0"
EXPERIMENT_ID = "npdes-end-to-end-programmability-v0"
MODEL = "composer-2.5"
ADAPTER = "cursor-agent-bwrap-isolated-npdes-end-to-end-programmability-v0"
TIMEOUT_SECONDS = 900
DRAFT_TRIAL = "T5"
STATES_USED = ("state_a", "state_b", "state_c")

T5_CONSTRUCTION = PFPS / "runs" / DRAFT_TRIAL / "iter1" / "construction.py"
T5_SOURCE = PFPS / "source.py"
T5_WORLD_API = PFPS / "world_api.py"
T5_RUNNER = PFPS / "runs" / DRAFT_TRIAL / "iter1" / "clean_run" / "_run_construction.py"
WD_CONSTRUCTION = (
    OBLIGATION / "runs" / "arm_b" / "T1" / "when_discharging" / "dry_run" / "construction.py"
)
WD_PROPOSAL = OBLIGATION / "runs" / "arm_b" / "T1" / "when_discharging" / "PROPOSAL.json"
WD_JUDGMENT = OBLIGATION / "runs" / "arm_b" / "T1" / "when_discharging" / "JUDGMENT.json"
PF_CONSTRUCTION = OBLIGATION / "runs" / "arm_b" / "T3" / "pass_fail" / "dry_run" / "construction.py"
PF_PROPOSAL = OBLIGATION / "runs" / "arm_b" / "T3" / "pass_fail" / "PROPOSAL.json"
PF_JUDGMENT = OBLIGATION / "runs" / "arm_b" / "T3" / "pass_fail" / "JUDGMENT.json"
PF_T1_DELTA = OBLIGATION / "runs" / "arm_b" / "T1" / "pass_fail" / "dry_run_delta.json"
PF_T2_CELL = OBLIGATION / "runs" / "arm_b" / "T2" / "pass_fail"
