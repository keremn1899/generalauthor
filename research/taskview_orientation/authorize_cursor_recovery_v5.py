"""Freeze and authorize the write_scratch-accounting Stage 1 Cursor v5 recovery."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from research.taskview_orientation.freeze import PACKAGE_ROOT, sha256_file
from research.taskview_orientation.recovery_manifest import NEXT_MANIFEST_PATH
from research.taskview_orientation.runtime_manifest import EPISODES
from research.taskview_orientation.runtime_sdk import runtime_binding


RECOVERY_BASE_SHA256 = "4c35b5a3da02048f345a4cb57887337b0bb1c179e9b262db0a2edce0562e06ff"
INVALID_CAMPAIGN_ROOT = PACKAGE_ROOT / "results" / "stage1-cursor-v4"
INVALID_CAMPAIGN_SHA256 = "a58aba335a59cd6b9a894d834cb7747e6e6d700b94935cb038ddcf440e3331a3"
INVALID_SEAL_SHA256 = "bad5ccc200e4b98fa9e009659cbf24a0a0462e360006a4445a1273ee321dda52"
INVALID_CONTENT_SHA256 = "8ebd8f407660d3afb26ec579da2492f9b9699969778e4a76c756324a7a59a297"
PREFLIGHT_PATH = PACKAGE_ROOT / "runtime_preflight" / "stage1-cursor-v11-sdk"
PREFLIGHT_RECEIPT = PREFLIGHT_PATH / "runtime_preflight.json"
CAMPAIGN_ROOT = PACKAGE_ROOT / "results" / "stage1-cursor-v5"


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
        raise RuntimeError("SDK recovery campaign root already exists")

    _require_hash(INVALID_CAMPAIGN_ROOT / "campaign_invalid.json", INVALID_CAMPAIGN_SHA256, "invalid campaign")
    _require_hash(INVALID_CAMPAIGN_ROOT / "campaign_invalid_seal.json", INVALID_SEAL_SHA256, "invalid campaign seal")
    invalid_seal = json.loads((INVALID_CAMPAIGN_ROOT / "campaign_invalid_seal.json").read_text(encoding="utf-8"))
    if (
        invalid_seal.get("status") != "PILOT_ABORTED_SEALED"
        or invalid_seal.get("valid") is not False
        or invalid_seal.get("authorized_manifest_sha256") != RECOVERY_BASE_SHA256
        or invalid_seal.get("content_sha256") != INVALID_CONTENT_SHA256
    ):
        raise RuntimeError("invalid v4 campaign seal does not match the recovery base")

    preflight = json.loads(PREFLIGHT_RECEIPT.read_text(encoding="utf-8"))
    binding = runtime_binding()
    if preflight.get("status") != "PASS" or preflight.get("participant_campaign_calls") != 0:
        raise RuntimeError("SDK recovery preflight did not pass cleanly")
    if preflight.get("manifest_source_sha256") != RECOVERY_BASE_SHA256:
        raise RuntimeError("SDK recovery preflight used a different base manifest")
    if preflight.get("runtime_binding") != binding:
        raise RuntimeError("live SDK runtime binding differs from preflight")
    if binding.get("builtin_tool_allowlist") != ["mcp"]:
        raise RuntimeError("SDK built-in tool restriction differs")
    required = {
        "provider": "cursor",
        "model": "composer-2.5",
        "adapter": "taskview-cursor-sdk-v3",
    }
    if {key: binding[key] for key in required} != required:
        raise RuntimeError("SDK runtime identity differs")

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
                "scope": "fresh Stage 1 eight-episode write_scratch-accounting recovery",
                "episode_count": 8,
                "replicates_per_arm": 4,
                "turns_per_episode": 5,
                "retry_policy": "none",
                "fresh_provider_session_per_episode": True,
                "post_first_call_apparatus_changes": "forbidden; abort instead",
                "stage2_authorized": False,
            },
            "recovery_revision": {
                "adapter_from": "taskview-cursor-sdk-v3",
                "adapter_to": "taskview-cursor-sdk-v3",
                "scope": (
                    "count the frozen apparatus's write_scratch SCRATCH_WRITE event as its "
                    "logical-call accounting marker, since the frozen EpisodeTools.write_scratch "
                    "never emits a TOOL_CALL the way every other tool method does; the frozen "
                    "apparatus itself (tools.py, in apparatus_code_hashes) is untouched"
                ),
                "builtin_tools_visible": [],
                "inline_mcp_servers": ["taskview-orientation"],
                "scientific_treatment_changed": False,
                "frozen_inputs_changed": False,
                "frozen_apparatus_changed": False,
                "episode_order_changed": False,
            },
        }
    )
    manifest["stage1"]["participant_config"] = binding
    manifest["stage1"]["provider_adapter"] = {
        "name": binding["adapter"],
        "cursor_sdk_version": binding["cursor_sdk_version"],
        "implementation_sha256": sha256_file(PACKAGE_ROOT / "runtime_sdk.py"),
        "tool_server_sha256": sha256_file(PACKAGE_ROOT / "cursor_tool_server.py"),
        "builtin_tool_allowlist": binding["builtin_tool_allowlist"],
    }
    manifest["stage1"]["runtime_preflight"] = {
        "status": "PASS",
        "receipt_path": str(PREFLIGHT_RECEIPT.resolve()),
        "receipt_sha256": sha256_file(PREFLIGHT_RECEIPT),
        "participant_campaign_calls": 0,
        "stateful_turns": preflight["statefulness_probe"]["turn_count"],
        "statefulness_builtin_tools": preflight["statefulness_probe"]["builtin_tools"],
        "probe_trajectory_sha256": preflight["probe_trajectory_sha256"],
        "dynamic_tool_probe_trajectory_sha256": preflight["dynamic_tool_probe_trajectory_sha256"],
        "logical_dynamic_tool_calls": preflight["dynamic_tool_probe"]["logical_tool_call_count"],
    }
    manifest["stage1"]["previous_invalid_campaign"] = {
        "path": str(INVALID_CAMPAIGN_ROOT.resolve()),
        "authorized_manifest_sha256": RECOVERY_BASE_SHA256,
        "campaign_invalid_sha256": INVALID_CAMPAIGN_SHA256,
        "seal_sha256": INVALID_SEAL_SHA256,
        "content_sha256": INVALID_CONTENT_SHA256,
        "episodes_completed": invalid_seal["episodes_completed"],
        "failure_episode": invalid_seal["failure_episode"],
        "failure_type": invalid_seal["failure_type"],
        "failure": invalid_seal["failure"],
    }

    runtime_files = [
        "runtime.py",
        "runtime_sdk.py",
        "cursor_tool_server.py",
        "runtime_preflight.py",
        "runtime_manifest.py",
        "campaign.py",
        "report.py",
        "recovery_manifest.py",
        "authorize_cursor_recovery_v5.py",
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
