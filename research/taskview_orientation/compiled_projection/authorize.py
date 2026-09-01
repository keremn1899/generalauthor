"""Seal the execution-authorized compiled-projection campaign manifest."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from research.taskview_orientation.compiled_projection import (
    ADAPTER,
    BLOCK_COUNT,
    CAMPAIGN_ID,
    CONDITIONS,
    FROZEN_DIR,
    MODEL,
    MODEL_FAST_FORBIDDEN,
    PACKAGE_ROOT,
)
from research.taskview_orientation.compiled_projection.entitlement import episode_matrix
from research.taskview_orientation.freeze import FROZEN_ROOT, REPOSITORY_ROOT, sha256_file
from research.taskview_orientation.runtime import (
    CURSOR_AGENT_VERSION,
    MODEL as RUNTIME_MODEL,
    runtime_binding,
)


AUTHORIZED_MANIFEST_PATH = (
    REPOSITORY_ROOT
    / "research/taskview_orientation/manifests/"
    "taskview-orientation-compiled-projection-v1-authorized.json"
)
AUTHORIZED_SIDECAR_PATH = AUTHORIZED_MANIFEST_PATH.with_suffix(".sha256")
PREFLIGHT_PATH = (
    REPOSITORY_ROOT / "research/taskview_orientation/preflight/compiled-projection-v1.json"
)
SPEC_PATH = PACKAGE_ROOT / "SPEC.md"

EXPERIMENT_FILES = (
    "research/taskview_orientation/compiled_projection/SPEC.md",
    "research/taskview_orientation/compiled_projection/frozen/reassembly.json",
    "research/taskview_orientation/compiled_projection/frozen/block_order.json",
    "research/taskview_orientation/compiled_projection/frozen/parity.json",
    "research/taskview_orientation/compiled_projection/projection.py",
    "research/taskview_orientation/compiled_projection/delivery.py",
    "research/taskview_orientation/compiled_projection/surface.py",
    "research/taskview_orientation/compiled_projection/metrics.py",
    "research/taskview_orientation/compiled_projection/entitlement.py",
    "research/taskview_orientation/compiled_projection/preflight.py",
)

APPARATUS_FILES = (
    "research/taskview_orientation/compiled_projection/campaign.py",
    "research/taskview_orientation/compiled_projection/report.py",
    "research/taskview_orientation/compiled_projection/cursor_tool_server.py",
    "research/taskview_orientation/compiled_projection/__init__.py",
    "research/taskview_orientation/runtime.py",
    "research/taskview_orientation/runner.py",
    "research/taskview_orientation/cursor_tool_server.py",
    "research/taskview_orientation/surface.py",
    "research/taskview_orientation/tools.py",
    "research/taskview_orientation/telemetry.py",
)


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _hashes(relatives: tuple[str, ...]) -> dict[str, str]:
    return {relative: sha256_file(REPOSITORY_ROOT / relative) for relative in relatives}


def build_manifest() -> dict[str, Any]:
    preflight = json.loads(PREFLIGHT_PATH.read_text(encoding="utf-8"))
    if preflight.get("status") != "PASS":
        raise RuntimeError("refusing to authorize: deterministic preflight is not PASS")
    if RUNTIME_MODEL != MODEL or MODEL == MODEL_FAST_FORBIDDEN:
        raise RuntimeError("refusing to authorize: participant is not composer-2.5")
    episodes = episode_matrix()
    return {
        "campaign_id": CAMPAIGN_ID,
        "status": "COMPILED_PROJECTION_V1_LIVE_AUTHORIZED",
        "participant_execution_authorized": True,
        "fresh_authorization_required": False,
        "participant_model": MODEL,
        "participant_model_forbidden": MODEL_FAST_FORBIDDEN,
        "adapter": ADAPTER,
        "cursor_agent_version": CURSOR_AGENT_VERSION,
        "runtime_binding": runtime_binding(),
        "blocks": BLOCK_COUNT,
        "conditions": list(CONDITIONS),
        "episodes": 6,
        "turns": 30,
        "stage1": {
            "episode_count": 6,
            "turns_per_episode": 5,
            "retry_policy": "none",
            "within_episode_retry": False,
            "selective_reruns": False,
            "episodes": episodes,
        },
        "primary_metric": "reassembly-after-delivery",
        "economics_is_primary_success_criterion": False,
        "force_taskview_use": False,
        "force_trust": False,
        "force_avoid_repository_inspection": False,
        "force_minimize_tool_calls": False,
        "lineage": {
            "kind": "execution_authorized",
            "spec_sha256": sha256_file(SPEC_PATH),
            "preflight_path": str(PREFLIGHT_PATH),
            "preflight_sha256": sha256_file(PREFLIGHT_PATH),
            "reassembly_sha256": sha256_file(FROZEN_DIR / "reassembly.json"),
            "block_order_sha256": sha256_file(FROZEN_DIR / "block_order.json"),
            "parity_sha256": sha256_file(FROZEN_DIR / "parity.json"),
            "frozen_taskview_sha256": sha256_file(FROZEN_ROOT / "taskview.sqlite"),
            "historical_parent_immutable": True,
        },
        "execution_authorization": {
            "authorized_timestamp_ns": time.time_ns(),
            "authorization_basis": (
                "Explicit user authorization to run the compiled-projection "
                "live campaign after deterministic preflight PASS."
            ),
            "campaign_id": CAMPAIGN_ID,
            "results_root": "research/taskview_orientation/results/compiled-projection-v1",
            "report_module": "research.taskview_orientation.compiled_projection.report",
            "retry_policy": "none",
            "within_episode_retry": False,
            "selective_reruns": False,
        },
        "experiment_code_hashes": _hashes(EXPERIMENT_FILES),
        "apparatus_code_hashes": _hashes(APPARATUS_FILES),
    }


def write_authorized_manifest() -> dict[str, Any]:
    manifest = build_manifest()
    _write(AUTHORIZED_MANIFEST_PATH, manifest)
    digest = hashlib.sha256(AUTHORIZED_MANIFEST_PATH.read_bytes()).hexdigest()
    AUTHORIZED_SIDECAR_PATH.write_text(f"{digest}  {AUTHORIZED_MANIFEST_PATH.name}\n")
    return {
        "path": str(AUTHORIZED_MANIFEST_PATH),
        "sha256": digest,
        "campaign_id": CAMPAIGN_ID,
    }


if __name__ == "__main__":
    print(json.dumps(write_authorized_manifest(), indent=2, sort_keys=True))
