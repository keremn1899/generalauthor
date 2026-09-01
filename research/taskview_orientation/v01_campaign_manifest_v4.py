"""Build the freshly authorized scientific v0.1 campaign manifest."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

from research.taskview_orientation.freeze import REPOSITORY_ROOT, sha256_file
from research.taskview_orientation.runtime_sdk import runtime_binding
from research.taskview_orientation.v01_authorize import AUTHORIZED_MANIFEST_PATH as SEALED_V3_MANIFEST
from research.taskview_orientation.v01_canary_manifest import MANIFEST_PATH as CANARY_MANIFEST_PATH


PACKAGE_ROOT = Path(__file__).parent
MANIFEST_PATH = PACKAGE_ROOT / "manifests/taskview-orientation-v01-stage1-v4-searchfix-authorized.json"
SIDECAR_PATH = MANIFEST_PATH.with_suffix(".sha256")
CAMPAIGN_ID = "taskview-orientation-stage1-cursor-v01-v4-searchfix"
RESULTS_ROOT = REPOSITORY_ROOT / "research/taskview_orientation/results/stage1-cursor-v01-v4-searchfix"

APPARATUS_FILES = (
    "research/taskview_orientation/__init__.py",
    "research/taskview_orientation/__main__.py",
    "research/taskview_orientation/fixture.py",
    "research/taskview_orientation/freeze.py",
    "research/taskview_orientation/oracle.py",
    "research/taskview_orientation/runner.py",
    "research/taskview_orientation/surface.py",
    "research/taskview_orientation/telemetry.py",
    "research/taskview_orientation/tools.py",
)
RUNTIME_FILES = (
    "research/taskview_orientation/cursor_tool_server.py",
    "research/taskview_orientation/runtime_accounting.py",
    "research/taskview_orientation/runtime_sdk.py",
    "research/taskview_orientation/runtime.py",
    "research/taskview_orientation/v01_campaign.py",
    "research/taskview_orientation/v01_preflight.py",
)
EXECUTION_FILES = (
    "research/taskview_orientation/v01_campaign.py",
    "research/taskview_orientation/v01_report.py",
)
TASKVIEW_FILES = (
    "taskview/__init__.py",
    "taskview/agent_surface.py",
    "taskview/migration_example.py",
    "taskview/model.py",
    "taskview/store.py",
)


def build_manifest() -> dict[str, Any]:
    base = json.loads(SEALED_V3_MANIFEST.read_text(encoding="utf-8"))
    canary = json.loads(CANARY_MANIFEST_PATH.read_text(encoding="utf-8"))
    manifest = copy.deepcopy(base)
    manifest.update(
        {
            "experiment_version": "taskview-orientation-v01-stage1-v4-searchfix",
            # The existing campaign executor validates this frozen status;
            # lineage and campaign_id distinguish this fresh authorization.
            "status": "STAGE1_V01_RUNTIME_FROZEN_AUTHORIZED",
            "participant_execution_authorized": True,
            "fresh_authorization_required": False,
            "runtime_binding": runtime_binding(),
            "campaign_id": CAMPAIGN_ID,
            "lineage": {
                "kind": "fresh_scientific_descendant_of_canary_runtime",
                "parent_manifest_path": str(CANARY_MANIFEST_PATH),
                "parent_manifest_sha256": sha256_file(CANARY_MANIFEST_PATH),
                "parent_canary_manifest_path": str(CANARY_MANIFEST_PATH),
                "parent_canary_manifest_sha256": sha256_file(CANARY_MANIFEST_PATH),
                "parent_v4_harness_manifest_sha256": canary["lineage"]["parent_v4_harness_manifest_sha256"],
                "canary_excluded_from_sample": True,
                "scientific_world_changed": False,
                "taskview_semantics_changed": False,
                "prompts_oracle_thresholds_changed": False,
            },
            "execution_authorization": {
                "authorization_basis": "Fresh authorization after deterministic v4 search-fix and live canary PASS.",
                "authorized_timestamp_ns": None,
                "campaign_id": CAMPAIGN_ID,
                "report_module": "research.taskview_orientation.v01_report",
                "results_root": str(RESULTS_ROOT),
                "retry_policy": "none",
                "selective_reruns": False,
                "within_episode_retry": False,
            },
            "stage1": copy.deepcopy(base["stage1"]),
            "apparatus_code_hashes": {
                relative: sha256_file(REPOSITORY_ROOT / relative) for relative in APPARATUS_FILES
            },
            "runtime_code_hashes": {
                relative: sha256_file(REPOSITORY_ROOT / relative) for relative in RUNTIME_FILES
            },
            "execution_apparatus_hashes": {
                relative: sha256_file(REPOSITORY_ROOT / relative) for relative in EXECUTION_FILES
            },
            "taskview_runtime_hashes": {
                relative: sha256_file(REPOSITORY_ROOT / relative) for relative in TASKVIEW_FILES
            },
            "search_source_fix": canary["search_source_fix"],
            "canary_manifest_sha256": sha256_file(CANARY_MANIFEST_PATH),
        }
    )
    manifest["execution_authorization"]["authorized_timestamp_ns"] = __import__("time").time_ns()
    manifest["stage1"]["participant_config"]["adapter"] = "taskview-cursor-sdk-v4"
    return manifest


def write_manifest() -> tuple[Path, str]:
    MANIFEST_PATH.write_text(json.dumps(build_manifest(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    digest = sha256_file(MANIFEST_PATH)
    SIDECAR_PATH.write_text(f"{digest}  {MANIFEST_PATH.name}\n", encoding="utf-8")
    return MANIFEST_PATH, digest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    path, digest = write_manifest()
    print(json.dumps({"manifest": str(path), "sha256": digest}, sort_keys=True))
