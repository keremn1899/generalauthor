"""Freeze and authorize the citation-guardrail + resume-support Stage 1 Cursor v9 recovery."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from research.taskview_orientation.freeze import PACKAGE_ROOT, sha256_file
from research.taskview_orientation.recovery_manifest import NEXT_MANIFEST_PATH
from research.taskview_orientation.runtime_manifest import EPISODES
from research.taskview_orientation.runtime_sdk import runtime_binding


RECOVERY_BASE_SHA256 = "9a151e05c70caa827c8d43f4a157efd48663f6e2fa3bb51709a6862d283f3422"
INVALID_CAMPAIGN_ROOT = PACKAGE_ROOT / "results" / "stage1-cursor-v8"
INVALID_CAMPAIGN_SHA256 = "100ae066f342c1a8f4a4b3e3a36143a5dd1ce43674ac901c45f97484836c9d56"
INVALID_SEAL_SHA256 = "4a55ebd2a1d457aa07a0e52c8b332c4f9a26757babb938e04e527864a287e84d"
INVALID_CONTENT_SHA256 = "43f83bd068c9132fc85150a11752fc926fbec5d1747faefacd5835438ddb7c8a"
PREFLIGHT_PATH = PACKAGE_ROOT / "runtime_preflight" / "stage1-cursor-v14-sdk"
PREFLIGHT_RECEIPT = PREFLIGHT_PATH / "runtime_preflight.json"
CAMPAIGN_ROOT = PACKAGE_ROOT / "results" / "stage1-cursor-v9"


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
        raise RuntimeError("invalid v8 campaign seal does not match the recovery base")

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
                "scope": "fresh Stage 1 eight-episode citation-guardrail + resume-support recovery",
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
                    "stage1-cursor-v8 e01-raw-r1 phase 4 cited its own write_scratch note "
                    "as a source citation; oracle.py correctly rejected it (citations must "
                    "resolve inside the frozen source tree) and the whole campaign aborted "
                    "on the ValueError. Two runtime-only (non-apparatus) changes: (1) "
                    "cursor_tool_server.py's write_scratch tool description now states "
                    "scratch paths are never valid citations, to reduce recurrence -- the "
                    "frozen prompts/oracle themselves are untouched; (2) campaign.py can now "
                    "resume a same-manifest retry from its own prior aborted attempt, "
                    "verifying every already-sealed episode's hash before skipping it, so a "
                    "later-episode failure never re-runs (and re-pays for) earlier episodes "
                    "that already completed and sealed cleanly. A changed manifest (any code "
                    "fix) still always starts a results root fresh, unchanged."
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
        "authorize_cursor_recovery_v9.py",
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
