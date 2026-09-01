"""Seal the aborted attempt and refreeze adapter v2 for fresh authorization."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any

from research.taskview_orientation.freeze import MANIFEST_PATH, PACKAGE_ROOT, sha256_file
from research.taskview_orientation.runtime import runtime_binding


NEXT_MANIFEST_PATH = MANIFEST_PATH.with_name("experiment_manifest.next.json")


def _write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _hash_tree(root: Path, excluded: set[str]) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha256_file(path)
        for path in sorted(item for item in root.rglob("*") if item.is_file())
        if path.relative_to(root).as_posix() not in excluded
    }


def seal_invalid_campaign(campaign_root: Path) -> dict[str, Any]:
    seal_path = campaign_root / "campaign_invalid_seal.json"
    if seal_path.exists():
        raise FileExistsError("invalid campaign is already sealed")
    invalid = json.loads((campaign_root / "campaign_invalid.json").read_text(encoding="utf-8"))
    if invalid.get("status") != "PILOT_ABORTED" or invalid.get("valid") is not False:
        raise RuntimeError("campaign is not explicitly marked PILOT_ABORTED")
    files = _hash_tree(campaign_root, {seal_path.name})
    seal = {
        "campaign_id": invalid["campaign_id"],
        "status": "PILOT_ABORTED_SEALED",
        "valid": False,
        "authorized_manifest_sha256": invalid["manifest_sha256"],
        "episodes_completed": len(invalid["episodes_completed"]),
        "failure_episode": invalid["failure_episode"],
        "failure_type": invalid["failure_type"],
        "failure": invalid["failure"],
        "file_hashes": files,
        "content_sha256": hashlib.sha256(
            json.dumps(files, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "sealed_timestamp_ns": time.time_ns(),
    }
    _write(seal_path, seal)
    return seal


def refreeze_recovery(preflight_path: Path, campaign_root: Path) -> dict[str, Any]:
    next_sidecar = NEXT_MANIFEST_PATH.with_suffix(".sha256")
    if NEXT_MANIFEST_PATH.exists() or next_sidecar.exists():
        raise FileExistsError("next runtime manifest already exists")
    original_sidecar = MANIFEST_PATH.with_suffix(".sha256")
    original_hash = hashlib.sha256(MANIFEST_PATH.read_bytes()).hexdigest()
    if original_sidecar.read_text(encoding="utf-8").split()[0] != original_hash:
        raise RuntimeError("original authorized manifest no longer matches its sidecar")
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    if preflight.get("status") != "PASS":
        raise RuntimeError("replacement runtime preflight did not pass")
    invalid_seal = seal_invalid_campaign(campaign_root)
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    binding = runtime_binding()
    runtime_files = [
        "runtime.py",
        "runtime_preflight.py",
        "runtime_manifest.py",
        "campaign.py",
        "report.py",
        "recovery_manifest.py",
    ]
    manifest.update(
        {
            "status": "STAGE1_RUNTIME_REFROZEN_AWAITING_FRESH_AUTHORIZATION",
            "participant_execution_authorized": False,
            "runtime_refrozen_timestamp_ns": time.time_ns(),
            "previous_authorized_manifest_sha256": original_hash,
            "recovery_reason": (
                "The first RAW episode of the authorized attempt aborted before any turn "
                "completed because a peer JSON-RPC tool request reused the active client "
                "request ID. Adapter v2 discriminates requests by method presence."
            ),
        }
    )
    manifest["stage1"].update(
        {
            "participant_config": binding,
            "provider_adapter": {
                "name": binding["adapter"],
                "cursor_agent_version": binding["cursor_agent_version"],
                "implementation_sha256": sha256_file(PACKAGE_ROOT / "runtime.py"),
            },
            "runtime_preflight": {
                "status": preflight["status"],
                "receipt_path": str(preflight_path.resolve()),
                "receipt_sha256": sha256_file(preflight_path),
                "probe_trajectory_sha256": preflight["probe_trajectory_sha256"],
                "parallel_dynamic_tool_probe_trajectory_sha256": preflight[
                    "dynamic_tool_probe_trajectory_sha256"
                ],
                "parallel_dynamic_tool_calls": len(
                    preflight["dynamic_tool_probe"]["tool_calls"]
                ),
            },
            "previous_invalid_campaign": {
                "path": str(campaign_root.resolve()),
                "seal_sha256": sha256_file(campaign_root / "campaign_invalid_seal.json"),
                "content_sha256": invalid_seal["content_sha256"],
                "episodes_completed": invalid_seal["episodes_completed"],
                "failure_episode": invalid_seal["failure_episode"],
                "failure_type": invalid_seal["failure_type"],
            },
        }
    )
    manifest["runtime_code_hashes"] = {
        f"research/taskview_orientation/{name}": sha256_file(PACKAGE_ROOT / name)
        for name in runtime_files
    }
    manifest["unresolved_before_execution"] = [
        "Fresh participant-execution authorization is required after the sealed aborted attempt."
    ]
    manifest["manifest_integrity"] = {
        "algorithm": "sha256",
        "scope": "exact experiment_manifest.next.json bytes",
        "sidecar": next_sidecar.name,
    }
    _write(NEXT_MANIFEST_PATH, manifest)
    digest = hashlib.sha256(NEXT_MANIFEST_PATH.read_bytes()).hexdigest()
    next_sidecar.write_text(f"{digest}  {NEXT_MANIFEST_PATH.name}\n", encoding="utf-8")
    return {
        "next_manifest": str(NEXT_MANIFEST_PATH),
        "next_manifest_sha256": digest,
        "participant_execution_authorized": False,
        "invalid_campaign_seal": invalid_seal,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", type=Path, required=True)
    parser.add_argument("--campaign", type=Path, required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            refreeze_recovery(args.preflight, args.campaign),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
