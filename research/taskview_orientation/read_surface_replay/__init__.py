"""Deterministic offline TaskView read-surface replay.

This package never invokes a participant model.  It reconstructs the sealed
v0.1 TASKVIEW trajectories and counterfactually serializes alternative read
surfaces against the exact historical logical accesses.
"""

from __future__ import annotations

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
SEALED_CAMPAIGN_ID = "taskview-orientation-stage1-cursor-v01-v4-searchfix"
SEALED_RESULTS_ROOT = PACKAGE_ROOT / "results" / "stage1-cursor-v01-v4-searchfix"
AUTHORIZED_MANIFEST_PATH = (
    PACKAGE_ROOT
    / "manifests"
    / "taskview-orientation-v01-stage1-v4-searchfix-authorized.json"
)
DIAGNOSTICS_PATH = PACKAGE_ROOT / "diagnostics" / "read_surface_replay.json"
REPORT_PATH = PACKAGE_ROOT / "READ_SURFACE_REPLAY_RESULTS.md"

EXPECTED_SQL_FACTS = {
    "query_sql_calls": 111,
    "plain_enumerations": 89,
    "filtered_calls": 16,
    "order_limit_variants": 6,
    "single_relation": 111,
    "select_star": 111,
    "join": 0,
    "subquery": 0,
    "cte": 0,
    "aggregate": 0,
    "set_operation": 0,
}

CANDIDATES = ("A", "B", "C", "D", "E", "E1", "Eall", "F")
REPLAY_LEVELS = (
    "trajectory_preserving",
    "mechanical_dedup_floor",
    "row_floor",
)
