"""Build the unauthorized runtime-only successor to the aborted v0.1 campaign."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from research.taskview_orientation.freeze import REPOSITORY_ROOT, sha256_file
from research.taskview_orientation.runtime_accounting import ACCOUNTING_MODEL_VERSION
from research.taskview_orientation.runtime_sdk import runtime_binding
from research.taskview_orientation.v01_authorize import AUTHORIZED_MANIFEST_PATH


PACKAGE_ROOT = Path(__file__).parent
INVALID_CAMPAIGN_PATH = (
    PACKAGE_ROOT / "results/stage1-cursor-v01/campaign_invalid.json"
)
HARNESS_MANIFEST_PATH = (
    PACKAGE_ROOT / "manifests/taskview-orientation-v01-harness-v4.json"
)
HARNESS_SIDECAR_PATH = HARNESS_MANIFEST_PATH.with_suffix(".sha256")
HARNESS_AUTHORIZED_MANIFEST_PATH = (
    PACKAGE_ROOT / "manifests/taskview-orientation-v01-harness-v4-authorized.json"
)
CAMPAIGN_ID = "taskview-orientation-stage1-cursor-v01-harness-v4"

RUNTIME_FILES = (
    "research/taskview_orientation/cursor_tool_server.py",
    "research/taskview_orientation/runtime_accounting.py",
    "research/taskview_orientation/runtime_sdk.py",
    "research/taskview_orientation/telemetry.py",
    "research/taskview_orientation/v01_campaign.py",
)


def build_manifest() -> dict[str, Any]:
    parent = json.loads(AUTHORIZED_MANIFEST_PATH.read_text(encoding="utf-8"))
    invalid = json.loads(INVALID_CAMPAIGN_PATH.read_text(encoding="utf-8"))
    binding = runtime_binding()
    if invalid["status"] != "PILOT_ABORTED" or invalid["valid"] is not False:
        raise RuntimeError("preserved parent campaign is not invalid evidence")
    return {
        "experiment_version": "taskview-orientation-v01-harness-v4",
        "status": "HARNESS_V4_DETERMINISTIC_VALIDATED_UNAUTHORIZED",
        "participant_execution_authorized": False,
        "fresh_authorization_required": True,
        "campaign_id": CAMPAIGN_ID,
        "authorized_manifest_path": str(HARNESS_AUTHORIZED_MANIFEST_PATH),
        "lineage": {
            "kind": "runtime_accounting_repair",
            "parent_authorized_manifest_path": str(AUTHORIZED_MANIFEST_PATH),
            "parent_authorized_manifest_sha256": sha256_file(AUTHORIZED_MANIFEST_PATH),
            "invalid_campaign_path": str(INVALID_CAMPAIGN_PATH),
            "invalid_campaign_sha256": sha256_file(INVALID_CAMPAIGN_PATH),
            "invalid_campaign_id": invalid["campaign_id"],
            "invalid_campaign_preserved": True,
            "sealed_stage1_v10_results_untouched": True,
        },
        "runtime_binding": binding,
        "accounting": {
            "model": ACCOUNTING_MODEL_VERSION,
            "logical_identity": ["provider_session_id", "provider_call_id"],
            "bridge_identity": [
                "bridge_session_id",
                "server_instance_id",
                "mcp_request_id",
            ],
            "model_visible_bytes": "exact UTF-8 bytes in SDK completed MCP content text",
            "count_ratio_tolerance": None,
            "invariants": [
                "one start and one completion per provider logical identity",
                "every accepted logical call maps to exactly one bridge execution",
                "every bridge execution maps to exactly one logical call",
                "every bridge request has exactly one bridge response",
                "every logical call has exactly one model-visible result",
                "per-operation response bytes sum to total delivered bytes",
                "no cross-session identity",
                "no semantics-changing provider retry",
            ],
        },
        "failed_trajectory_replay": {
            "sdk_lifecycle_observations": 730,
            "unique_logical_calls": 365,
            "bridge_executions": 365,
            "successful_results": 122,
            "executed_error_results": 243,
            "provider_validation_rejections": 0,
            "model_visible_tool_result_bytes": 42790,
            "legacy_buggy_count": 608,
            "residual": 0,
        },
        "scientific_world": parent["scientific_world"],
        "all_frozen_input_hashes": parent["all_frozen_input_hashes"],
        "source_snapshot": parent["source_snapshot"],
        "phase4_replacement_sha256": parent["phase4_replacement_sha256"],
        "prompt_hashes": parent["prompt_hashes"],
        "oracle": parent["oracle"],
        "span_classification": parent["span_classification"],
        "taskview": parent["taskview"],
        "stage1": parent["stage1"],
        "arm_policy": parent["arm_policy"],
        "prospective_criteria": parent["prospective_criteria"],
        "runtime_code_hashes": {
            relative: sha256_file(REPOSITORY_ROOT / relative)
            for relative in RUNTIME_FILES
        },
        "changes": [
            "runtime/accounting/instrumentation only",
            "new adapter taskview-cursor-sdk-v4",
            "new identity-based reconciliation model",
            "new campaign identity; no participant authorization",
        ],
        "semantic_changes": [],
        "next_allowed_action": "one live canary after separate authorization",
    }


def write_manifest() -> tuple[Path, str]:
    manifest = build_manifest()
    HARNESS_MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    digest = sha256_file(HARNESS_MANIFEST_PATH)
    HARNESS_SIDECAR_PATH.write_text(
        f"{digest}  {HARNESS_MANIFEST_PATH.name}\n", encoding="utf-8"
    )
    return HARNESS_MANIFEST_PATH, digest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        path, digest = write_manifest()
        print(json.dumps({"manifest": str(path), "sha256": digest}, sort_keys=True))
    else:
        print(json.dumps(build_manifest(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
