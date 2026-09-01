"""Freeze and authorize the Stage 1 Cursor v2 recovery campaign."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from research.taskview_orientation.freeze import PACKAGE_ROOT, sha256_file
from research.taskview_orientation.recovery_manifest import NEXT_MANIFEST_PATH
from research.taskview_orientation.runtime import runtime_binding
from research.taskview_orientation.runtime_manifest import EPISODES


RECOVERY_BASE_SHA256 = "1a0c3cf143ed6e683c159739ecf26c705fe11863f9f4453f7302ae0ea1418be4"
INVALID_CAMPAIGN_ROOT = PACKAGE_ROOT / "results" / "stage1-cursor-v1"
INVALID_CAMPAIGN_SHA256 = "ac27725c10dd36e9fef2f7a573124860d6b83ab2adcf1f6e2189dc9f78201647"
INVALID_SEAL_SHA256 = "3b1a33a0fcf93e97a9d6195cd843493252b69f73f1eea8a77fe847d744f99d3d"
INVALID_CONTENT_SHA256 = "bddf8e881ee40549378026df45be3c25de30777acdd7a9e42afda05d75f05c52"
PREFLIGHT_PATH = PACKAGE_ROOT / "runtime_preflight" / "stage1-cursor-v7-recovery" / "runtime_preflight.json"
CAMPAIGN_ROOT = PACKAGE_ROOT / "results" / "stage1-cursor-v2"


def _write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _require_hash(path: Path, expected: str, label: str) -> None:
    actual = sha256_file(path)
    if actual != expected:
        raise RuntimeError(f"{label} drift: {actual} != {expected}")


def authorize() -> dict[str, Any]:
    sidecar = NEXT_MANIFEST_PATH.with_suffix(".sha256")
    actual = sha256_file(NEXT_MANIFEST_PATH)
    sealed = sidecar.read_text(encoding="utf-8").split()[0]
    if actual != RECOVERY_BASE_SHA256 or sealed != RECOVERY_BASE_SHA256:
        raise RuntimeError(f"recovery base manifest drift: actual={actual}, sidecar={sealed}")
    if CAMPAIGN_ROOT.exists():
        raise RuntimeError("recovery campaign root already exists")

    _require_hash(INVALID_CAMPAIGN_ROOT / "campaign_invalid.json", INVALID_CAMPAIGN_SHA256, "invalid campaign")
    _require_hash(INVALID_CAMPAIGN_ROOT / "campaign_invalid_seal.json", INVALID_SEAL_SHA256, "invalid campaign seal")
    invalid_seal = json.loads((INVALID_CAMPAIGN_ROOT / "campaign_invalid_seal.json").read_text(encoding="utf-8"))
    if (
        invalid_seal.get("status") != "PILOT_ABORTED_SEALED"
        or invalid_seal.get("valid") is not False
        or invalid_seal.get("authorized_manifest_sha256") != RECOVERY_BASE_SHA256
        or invalid_seal.get("content_sha256") != INVALID_CONTENT_SHA256
    ):
        raise RuntimeError("invalid campaign seal does not match the recovery base")

    preflight = json.loads(PREFLIGHT_PATH.read_text(encoding="utf-8"))
    binding = runtime_binding()
    if preflight.get("status") != "PASS" or preflight.get("participant_campaign_calls") != 0:
        raise RuntimeError("recovery preflight did not pass cleanly")
    if preflight.get("manifest_source_sha256") != RECOVERY_BASE_SHA256:
        raise RuntimeError("recovery preflight used a different base manifest")
    if preflight.get("runtime_binding") != binding:
        raise RuntimeError("live runtime binding differs from the recovery preflight")
    required = {
        "provider": "cursor",
        "model": "composer-2.5",
        "adapter": "taskview-cursor-agent-v2",
    }
    observed = {key: binding[key] for key in required}
    if observed != required:
        raise RuntimeError(f"recovery runtime binding differs: {observed}")

    manifest = json.loads(NEXT_MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest["stage1"]["episodes"] != EPISODES:
        raise RuntimeError("authorized episode order differs")
    manifest.update(
        {
            "status": "STAGE1_CURSOR_RUNTIME_FROZEN_AUTHORIZED",
            "participant_execution_authorized": True,
            "recovery_base_manifest_sha256": RECOVERY_BASE_SHA256,
            "participant_authorized_timestamp_ns": time.time_ns(),
            "authorization": {
                "declaration": "PROCEED WITH WHATEVER NEEDS DOING TO KEEP MOVING AS SOON AS POSSIBLE",
                "scope": "replacement Stage 1 eight-episode pilot after sealed apparatus abort",
                "episode_count": 8,
                "replicates_per_arm": 4,
                "turns_per_episode": 5,
                "retry_policy": "none",
                "fresh_provider_session_per_episode": True,
                "post_first_call_apparatus_changes": "forbidden; abort instead",
                "stage2_authorized": False,
            },
            "recovery_revision": {
                "adapter_from": "taskview-cursor-agent-v1",
                "adapter_to": "taskview-cursor-agent-v2",
                "scope": "canonicalize provider-side MCP validation rejections as failed logical tool attempts",
                "scientific_treatment_changed": False,
                "frozen_inputs_changed": False,
                "episode_order_changed": False,
            },
        }
    )
    manifest["stage1"]["participant_config"] = binding
    manifest["stage1"]["provider_adapter"] = {
        "name": binding["adapter"],
        "cursor_agent_version": binding["cursor_agent_version"],
        "implementation_sha256": sha256_file(PACKAGE_ROOT / "runtime.py"),
        "tool_server_sha256": sha256_file(PACKAGE_ROOT / "cursor_tool_server.py"),
    }
    manifest["stage1"]["runtime_preflight"] = {
        "status": "PASS",
        "receipt_path": str(PREFLIGHT_PATH.resolve()),
        "receipt_sha256": sha256_file(PREFLIGHT_PATH),
        "participant_campaign_calls": 0,
        "stateful_turns": preflight["statefulness_probe"]["turn_count"],
        "probe_trajectory_sha256": preflight["probe_trajectory_sha256"],
        "dynamic_tool_probe_trajectory_sha256": preflight["dynamic_tool_probe_trajectory_sha256"],
        "logical_dynamic_tool_calls": preflight["dynamic_tool_probe"]["logical_tool_call_count"],
        "failed_campaign_replay": {
            "provider_mcp_calls": 39,
            "bridge_calls": 38,
            "provider_validation_rejections": 1,
            "reconciled_logical_calls": 39,
            "status": "PASS",
        },
    }
    manifest["stage1"]["previous_invalid_campaign"] = {
        "path": str(INVALID_CAMPAIGN_ROOT.resolve()),
        "authorized_manifest_sha256": RECOVERY_BASE_SHA256,
        "campaign_invalid_sha256": INVALID_CAMPAIGN_SHA256,
        "seal_sha256": INVALID_SEAL_SHA256,
        "content_sha256": INVALID_CONTENT_SHA256,
        "episodes_completed": 0,
        "failure_episode": invalid_seal["failure_episode"],
        "failure_type": invalid_seal["failure_type"],
        "failure": invalid_seal["failure"],
    }

    runtime_files = [
        "runtime.py",
        "cursor_tool_server.py",
        "runtime_preflight.py",
        "runtime_manifest.py",
        "campaign.py",
        "report.py",
        "recovery_manifest.py",
        "cursor_default_manifest.py",
        "authorize_cursor_campaign.py",
        "authorize_cursor_recovery_v2.py",
    ]
    manifest["runtime_code_hashes"] = {
        f"research/taskview_orientation/{name}": sha256_file(PACKAGE_ROOT / name)
        for name in runtime_files
    }
    manifest["unresolved_before_execution"] = []
    _write(NEXT_MANIFEST_PATH, manifest)
    final_hash = sha256_file(NEXT_MANIFEST_PATH)
    sidecar.write_text(f"{final_hash}  {NEXT_MANIFEST_PATH.name}\n", encoding="utf-8")
    return {
        "status": manifest["status"],
        "recovery_base_manifest_sha256": RECOVERY_BASE_SHA256,
        "authorized_manifest_sha256": final_hash,
        "participant_execution_authorized": True,
        "manifest": str(NEXT_MANIFEST_PATH.resolve()),
        "campaign_root": str(CAMPAIGN_ROOT.resolve()),
    }


def main() -> None:
    print(json.dumps(authorize(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
