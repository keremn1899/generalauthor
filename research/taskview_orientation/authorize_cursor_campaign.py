"""Apply the user's one-way authorization to the Cursor replacement manifest."""

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


PRE_AUTHORIZATION_SHA256 = "720bfcf42ad1289a7b6497a4c9a637fa6b590a7c3562b7b97931ea67cdb4c337"
SUPERSEDED_AUTHORIZED_SHA256 = "2f496aaf89cbd313f6db069a4b484f96b095de6b288dfbd3d5f7b06c57cb6403"
CAMPAIGN_ROOT = PACKAGE_ROOT / "results" / "stage1-cursor-v1"


def _write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def authorize() -> dict[str, Any]:
    sidecar = NEXT_MANIFEST_PATH.with_suffix(".sha256")
    actual = hashlib.sha256(NEXT_MANIFEST_PATH.read_bytes()).hexdigest()
    sealed = sidecar.read_text(encoding="utf-8").split()[0]
    if actual != sealed or actual not in {
        PRE_AUTHORIZATION_SHA256,
        SUPERSEDED_AUTHORIZED_SHA256,
    }:
        raise RuntimeError(
            f"pre-authorization manifest drift: actual={actual}, sidecar={sealed}"
        )
    manifest = json.loads(NEXT_MANIFEST_PATH.read_text(encoding="utf-8"))
    prestart_correction = actual == SUPERSEDED_AUTHORIZED_SHA256
    if prestart_correction:
        if CAMPAIGN_ROOT.exists():
            raise RuntimeError("campaign root exists; pre-start correction is forbidden")
        if (
            manifest.get("participant_execution_authorized") is not True
            or manifest.get("status") != "STAGE1_CURSOR_RUNTIME_FROZEN_AUTHORIZED"
        ):
            raise RuntimeError("superseded authorized manifest state differs")
    elif manifest.get("participant_execution_authorized") is not False:
        raise RuntimeError("replacement manifest is not awaiting authorization")
    binding = runtime_binding()
    required = {
        "provider": "cursor",
        "model": "composer-2.5",
        "adapter": "taskview-cursor-agent-v1",
    }
    observed = {
        "provider": binding["provider"],
        "model": binding["model"],
        "adapter": binding["adapter"],
    }
    if observed != required or manifest["stage1"]["participant_config"] != binding:
        raise RuntimeError(f"authorized runtime binding differs: {observed}")
    if manifest["stage1"]["episodes"] != EPISODES:
        raise RuntimeError("authorized episode order differs")

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
    ]
    manifest.update(
        {
            "status": "STAGE1_CURSOR_RUNTIME_FROZEN_AUTHORIZED",
            "participant_execution_authorized": True,
            "pre_authorization_manifest_sha256": PRE_AUTHORIZATION_SHA256,
            "participant_authorized_timestamp_ns": time.time_ns(),
            "authorization": {
                "declaration": "AUTHORIZE 8-EPISODE PILOT",
                "episode_count": 8,
                "replicates_per_arm": 4,
                "turns_per_episode": 5,
                "retry_policy": "none",
                "fresh_provider_session_per_episode": True,
                "post_first_call_apparatus_changes": "forbidden; abort instead",
                "stage2_authorized": False,
            },
            "prestart_correction": (
                {
                    "superseded_authorized_manifest_sha256": SUPERSEDED_AUTHORIZED_SHA256,
                    "reason": (
                        "Campaign runner expected the former generic authorized status label; "
                        "execution stopped before campaign-root creation or participant calls."
                    ),
                }
                if prestart_correction
                else None
            ),
        }
    )
    manifest["runtime_code_hashes"] = {
        f"research/taskview_orientation/{name}": sha256_file(PACKAGE_ROOT / name)
        for name in runtime_files
    }
    manifest["unresolved_before_execution"] = []
    _write(NEXT_MANIFEST_PATH, manifest)
    final_hash = hashlib.sha256(NEXT_MANIFEST_PATH.read_bytes()).hexdigest()
    sidecar.write_text(f"{final_hash}  {NEXT_MANIFEST_PATH.name}\n", encoding="utf-8")
    return {
        "status": manifest["status"],
        "pre_authorization_manifest_sha256": PRE_AUTHORIZATION_SHA256,
        "authorized_manifest_sha256": final_hash,
        "participant_execution_authorized": True,
        "manifest": str(NEXT_MANIFEST_PATH.resolve()),
    }


def main() -> None:
    print(json.dumps(authorize(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
