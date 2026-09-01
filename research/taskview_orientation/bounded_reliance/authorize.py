"""Seal the execution-authorized bounded-reliance campaign manifest."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from research.taskview_orientation.bounded_reliance import (
    ADAPTER,
    BLOCK_COUNT,
    CAMPAIGN_ID,
    CONDITIONS,
    FROZEN_DIR,
    MODEL,
    MODEL_FAST_FORBIDDEN,
    PACKAGE_ROOT,
)
from research.taskview_orientation.bounded_reliance.entitlement import episode_matrix
from research.taskview_orientation.freeze import FROZEN_ROOT, REPOSITORY_ROOT, sha256_file
from research.taskview_orientation.runtime import (
    CURSOR_AGENT_VERSION,
    MODEL as RUNTIME_MODEL,
    runtime_binding,
)


PARENT_MANIFEST_PATH = (
    REPOSITORY_ROOT
    / "research/taskview_orientation/manifests/"
    "taskview-orientation-bounded-reliance-v1.json"
)
AUTHORIZED_MANIFEST_PATH = (
    REPOSITORY_ROOT
    / "research/taskview_orientation/manifests/"
    "taskview-orientation-bounded-reliance-v1-authorized.json"
)
AUTHORIZED_SIDECAR_PATH = AUTHORIZED_MANIFEST_PATH.with_suffix(".sha256")
PREFLIGHT_PATH = (
    REPOSITORY_ROOT / "research/taskview_orientation/preflight/bounded-reliance-v1.json"
)
SPEC_PATH = PACKAGE_ROOT / "SPEC.md"

EXPERIMENT_FILES = (
    "research/taskview_orientation/bounded_reliance/SPEC.md",
    "research/taskview_orientation/bounded_reliance/frozen/entitlement.json",
    "research/taskview_orientation/bounded_reliance/frozen/block_order.json",
    "research/taskview_orientation/bounded_reliance/contracts.py",
    "research/taskview_orientation/bounded_reliance/grounding.py",
    "research/taskview_orientation/bounded_reliance/surface.py",
    "research/taskview_orientation/bounded_reliance/metrics.py",
    "research/taskview_orientation/bounded_reliance/entitlement.py",
    "research/taskview_orientation/bounded_reliance/preflight.py",
)

APPARATUS_FILES = (
    "research/taskview_orientation/bounded_reliance/campaign.py",
    "research/taskview_orientation/bounded_reliance/report.py",
    "research/taskview_orientation/bounded_reliance/cursor_tool_server.py",
    "research/taskview_orientation/bounded_reliance/__init__.py",
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
    parent = json.loads(PARENT_MANIFEST_PATH.read_text(encoding="utf-8"))
    preflight = json.loads(PREFLIGHT_PATH.read_text(encoding="utf-8"))
    if preflight.get("status") != "PASS":
        raise RuntimeError("refusing to authorize: deterministic preflight is not PASS")
    if RUNTIME_MODEL != MODEL or MODEL == MODEL_FAST_FORBIDDEN:
        raise RuntimeError("refusing to authorize: participant is not composer-2.5")
    episodes = episode_matrix()
    return {
        "campaign_id": CAMPAIGN_ID,
        "status": "BOUNDED_RELIANCE_V1_LIVE_AUTHORIZED",
        "participant_execution_authorized": True,
        "fresh_authorization_required": False,
        "participant_model": MODEL,
        "participant_model_forbidden": MODEL_FAST_FORBIDDEN,
        "adapter": ADAPTER,
        "cursor_agent_version": CURSOR_AGENT_VERSION,
        "runtime_binding": runtime_binding(),
        "blocks": BLOCK_COUNT,
        "conditions": list(CONDITIONS),
        "episodes": 20,
        "turns": 100,
        "stage1": {
            "episode_count": 20,
            "turns_per_episode": 5,
            "retry_policy": "none",
            "within_episode_retry": False,
            "selective_reruns": False,
            "episodes": episodes,
        },
        "primary_metric": "reconstruction-after-entitlement",
        "economics_is_primary_success_criterion": False,
        "force_taskview_use": False,
        "force_trust": False,
        "force_avoid_repository_inspection": False,
        "force_minimize_tool_calls": False,
        "lineage": {
            "kind": "execution_authorized_descendant",
            "parent_manifest_path": str(PARENT_MANIFEST_PATH),
            "parent_manifest_sha256": sha256_file(PARENT_MANIFEST_PATH),
            "spec_sha256": sha256_file(SPEC_PATH),
            "preflight_path": str(PREFLIGHT_PATH),
            "preflight_sha256": sha256_file(PREFLIGHT_PATH),
            "entitlement_sha256": sha256_file(FROZEN_DIR / "entitlement.json"),
            "block_order_sha256": sha256_file(FROZEN_DIR / "block_order.json"),
            "frozen_taskview_sha256": sha256_file(FROZEN_ROOT / "taskview.sqlite"),
            "historical_parent_immutable": True,
        },
        "execution_authorization": {
            "authorized_timestamp_ns": time.time_ns(),
            "authorization_basis": (
                "Explicit user authorization to run the already-frozen "
                "bounded-reliance live campaign after deterministic preflight PASS."
            ),
            "campaign_id": CAMPAIGN_ID,
            "results_root": "research/taskview_orientation/results/bounded-reliance-v1",
            "report_module": "research.taskview_orientation.bounded_reliance.report",
            "retry_policy": "none",
            "within_episode_retry": False,
            "selective_reruns": False,
        },
        "experiment_code_hashes": _hashes(EXPERIMENT_FILES),
        "apparatus_code_hashes": _hashes(APPARATUS_FILES),
        "parent_constraints": {
            "force_taskview_use": parent["force_taskview_use"],
            "force_trust": parent["force_trust"],
            "force_avoid_repository_inspection": parent["force_avoid_repository_inspection"],
            "force_minimize_tool_calls": parent["force_minimize_tool_calls"],
        },
    }


def write_authorized_manifest() -> dict[str, Any]:
    manifest = build_manifest()
    _write(AUTHORIZED_MANIFEST_PATH, manifest)
    digest = hashlib.sha256(AUTHORIZED_MANIFEST_PATH.read_bytes()).hexdigest()
    AUTHORIZED_SIDECAR_PATH.write_text(f"{digest}  {AUTHORIZED_MANIFEST_PATH.name}\n")
    return {"path": str(AUTHORIZED_MANIFEST_PATH), "sha256": digest, "campaign_id": CAMPAIGN_ID}


if __name__ == "__main__":
    print(json.dumps(write_authorized_manifest(), indent=2, sort_keys=True))
