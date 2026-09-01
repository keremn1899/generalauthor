"""Bounded-reliance and grounding-freshness experiment.

Deterministic preflight is the default.  Live Cursor CLI inference is refused
until preflight passes and an authorized manifest is present.
"""

from __future__ import annotations

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
FROZEN_DIR = PACKAGE_ROOT / "frozen"
EXPORT_PREFLIGHT_PATH = PACKAGE_ROOT.parent / "preflight" / "bounded-reliance-v1.json"
CAMPAIGN_ID = "taskview-orientation-bounded-reliance-v1"
MODEL = "composer-2.5"
MODEL_FAST_FORBIDDEN = "composer-2.5-fast"
ADAPTER = "taskview-cursor-cli-v1"
CONDITIONS = ("R", "T00", "T10", "T01", "T11")
TASKVIEW_CONDITIONS = ("T00", "T10", "T01", "T11")
BLOCK_COUNT = 4
SEED = 20260901
PARTICIPANT_INFERENCE_AUTHORIZED = True
CHECKOUT_CONTRACT_PATH = "tests/checkout_contract.py"
CHECKOUT_VERIFIED_BY = {
    "relation": "verified_by",
    "tuple": {"service": "service:checkout", "test": "test:checkout-contract"},
}
REPORTING_VERIFIED_BY = {
    "relation": "verified_by",
    "tuple": {"service": "service:reporting", "test": "test:reporting-contract"},
}
