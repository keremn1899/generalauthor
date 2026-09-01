"""Compiled decision-projection experiment.

Deterministic preflight is the default. Live Cursor CLI inference is refused
until preflight passes and an authorized manifest is present.
"""

from __future__ import annotations

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
FROZEN_DIR = PACKAGE_ROOT / "frozen"
EXPORT_PREFLIGHT_PATH = PACKAGE_ROOT.parent / "preflight" / "compiled-projection-v1.json"
CAMPAIGN_ID = "taskview-orientation-compiled-projection-v1"
MODEL = "composer-2.5"
MODEL_FAST_FORBIDDEN = "composer-2.5-fast"
ADAPTER = "taskview-cursor-cli-v1"
CONDITIONS = ("ATOMIC", "COMPILED")
BLOCK_COUNT = 3
SEED = 20260902
PARTICIPANT_INFERENCE_AUTHORIZED = True
MIGRATION_SURFACE_RELATION = "migration_surface"
CHECKOUT_CONTRACT_PATH = "tests/checkout_contract.py"
CHECKOUT_VERIFIED_BY = {
    "relation": "verified_by",
    "tuple": {"service": "service:checkout", "test": "test:checkout-contract"},
}

SUBSUMED_RELATIONS = (
    "in_scope",
    "affected_service",
    "requires_change",
    "protected_by",
    "compatible_via",
    "boundary",
    "excluded",
    "unresolved_scope",
    "verified_by",
    "verification_gap",
)

REASSESSMENT_RELATIONS = frozenset({"verified_by", "verification_gap"})
