"""Refreeze the awaiting-authorization manifest with Cursor as the default."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any

from research.taskview_orientation.freeze import PACKAGE_ROOT, sha256_file
from research.taskview_orientation.recovery_manifest import NEXT_MANIFEST_PATH
from research.taskview_orientation.runtime import runtime_binding


def _write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def refreeze_cursor_default(preflight_path: Path) -> dict[str, Any]:
    sidecar = NEXT_MANIFEST_PATH.with_suffix(".sha256")
    previous_hash = hashlib.sha256(NEXT_MANIFEST_PATH.read_bytes()).hexdigest()
    if sidecar.read_text(encoding="utf-8").split()[0] != previous_hash:
        raise RuntimeError("replacement manifest no longer matches its sidecar")
    manifest = json.loads(NEXT_MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("participant_execution_authorized") is not False:
        raise RuntimeError("refusing to change an authorized participant manifest")
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    if preflight.get("status") != "PASS" or preflight.get("participant_campaign_calls") != 0:
        raise RuntimeError("Cursor runtime preflight is not a clean apparatus-only PASS")
    binding = runtime_binding()
    if preflight.get("runtime_binding") != binding:
        raise RuntimeError("Cursor runtime binding changed after preflight")

    runtime_files = [
        "runtime.py",
        "cursor_tool_server.py",
        "runtime_preflight.py",
        "runtime_manifest.py",
        "campaign.py",
        "report.py",
        "recovery_manifest.py",
        "cursor_default_manifest.py",
    ]
    manifest.update(
        {
            "status": "STAGE1_CURSOR_RUNTIME_REFROZEN_AWAITING_FRESH_AUTHORIZATION",
            "participant_execution_authorized": False,
            "runtime_refrozen_timestamp_ns": time.time_ns(),
            "previous_recovery_manifest_sha256": previous_hash,
            "recovery_reason": (
                "User selected Cursor Composer 2.5 as the default after the sealed aborted "
                "Codex attempt. Cursor is bound through an isolated project MCP surface."
            ),
        }
    )
    manifest["stage1"].update(
        {
            "provider": binding["provider"],
            "model": binding["model"],
            "model_version": binding["exact_model_version_identifier"],
            "participant_config": binding,
            "provider_adapter": {
                "name": binding["adapter"],
                "cursor_agent_version": binding["cursor_agent_version"],
                "implementation_sha256": sha256_file(PACKAGE_ROOT / "runtime.py"),
                "tool_server_sha256": sha256_file(PACKAGE_ROOT / "cursor_tool_server.py"),
            },
            "runtime_preflight": {
                "status": preflight["status"],
                "receipt_path": str(preflight_path.resolve()),
                "receipt_sha256": sha256_file(preflight_path),
                "probe_trajectory_sha256": preflight["probe_trajectory_sha256"],
                "dynamic_tool_probe_trajectory_sha256": preflight[
                    "dynamic_tool_probe_trajectory_sha256"
                ],
                "stateful_turns": preflight["statefulness_probe"]["turn_count"],
                "logical_dynamic_tool_calls": preflight["dynamic_tool_probe"][
                    "logical_tool_call_count"
                ],
                "participant_campaign_calls": 0,
            },
        }
    )
    manifest["runtime_code_hashes"] = {
        f"research/taskview_orientation/{name}": sha256_file(PACKAGE_ROOT / name)
        for name in runtime_files
    }
    manifest["unresolved_before_execution"] = [
        "Fresh participant-execution authorization is required for the Cursor-default campaign."
    ]
    _write(NEXT_MANIFEST_PATH, manifest)
    digest = hashlib.sha256(NEXT_MANIFEST_PATH.read_bytes()).hexdigest()
    sidecar.write_text(f"{digest}  {NEXT_MANIFEST_PATH.name}\n", encoding="utf-8")
    return {
        "status": manifest["status"],
        "next_manifest": str(NEXT_MANIFEST_PATH),
        "next_manifest_sha256": digest,
        "previous_recovery_manifest_sha256": previous_hash,
        "participant_execution_authorized": False,
        "runtime_binding": binding,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(refreeze_cursor_default(args.preflight), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
