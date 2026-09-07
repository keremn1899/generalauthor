"""Paths for end-to-end capability probe v1. runtime_v0 must not import this package."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
RUNTIME_V0 = REPO / "research" / "semantic_integration" / "runtime_v0"
CORE = REPO / "research" / "semantic_integration" / "core"
TASKVIEW = REPO / "taskview"
DOMAINS = ROOT / "domains"
EVALUATOR_ONLY = ROOT / "evaluator_only"
RUNS = ROOT / "runs"
REPORTS = ROOT / "reports"
LIVE_ROOT = Path("/tmp/world-experiment") / "e2e-semantic-compilation-v1"
EXPERIMENT_ID = "e2e-semantic-compilation-v1"
MODEL = "composer-2.5"
ADAPTER = "cursor-agent-bwrap-isolated-e2e-semantic-compilation-v1"
DOMAIN_IDS = ("harbor_towing", "seed_grants", "makerspace_checkout")
CONSTRUCTION_TRIALS = ("T1", "T2")
CONSUMER_TRIALS = ("C1", "C2", "C3")
MAX_CONSTRUCT_ITERS = 3
HOST_RETRIES = 6
TIMEOUT_SECONDS = 900
CONSUMER_TIMEOUT_SECONDS = 600
