"""Paths for autonomous World exploration probe v1."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
RUNTIME_V0 = REPO / "research" / "semantic_integration" / "runtime_v0"
CORE = REPO / "research" / "semantic_integration" / "core"
TASKVIEW = REPO / "taskview"
E2E = ROOT.parent / "end_to_end_v1"
E2E_RUNS = E2E / "runs"
EVALUATOR_ONLY = ROOT / "evaluator_only"
RUNS = ROOT / "runs"
REPORTS = ROOT / "reports"
LIVE_ROOT = Path("/tmp/world-experiment") / "autonomous-world-exploration-v1"
EXPERIMENT_ID = "autonomous-world-exploration-v1"
MODEL = "composer-2.5"
ADAPTER = "cursor-agent-bwrap-isolated-autonomous-world-exploration-v1"
DOMAIN_IDS = ("harbor_towing", "seed_grants", "makerspace_checkout")
ARMS = ("E0", "E1")
TRIALS = ("R1", "R2", "R3")
HOST_RETRIES = 6
E0_TIMEOUT = 900
E1_ORIENT_TIMEOUT = 700
E1_TASK_TIMEOUT = 700


def t1_accepted(domain_id: str) -> Path:
    return E2E_RUNS / "construction" / domain_id / "T1" / "accepted"
