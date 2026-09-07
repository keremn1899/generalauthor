"""Paths for World read-side discipline & programming probe v1."""

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
LIVE_ROOT = Path("/tmp/world-experiment") / "world-read-programming-v1"
EXPERIMENT_ID = "world-read-programming-v1"
MODEL = "composer-2.5"
ADAPTER = "cursor-agent-bwrap-isolated-world-read-programming-v1"
DOMAIN_IDS = ("harbor_towing", "seed_grants", "makerspace_checkout")
PART_A_TRIALS = ("C1", "C2", "C3")
PART_B_TRIALS = ("P1", "P2")
ARMS = ("A0", "A1")
HOST_RETRIES = 6
PART_A_TIMEOUT = 900
PART_B_TIMEOUT = 900


def t1_accepted(domain_id: str) -> Path:
    return E2E_RUNS / "construction" / domain_id / "T1" / "accepted"
