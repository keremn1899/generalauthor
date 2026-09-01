"""One-way refreeze of runtime-dependent Stage 1 manifest fields."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any

from research.taskview_orientation.freeze import MANIFEST_PATH, PACKAGE_ROOT, sha256_file
from research.taskview_orientation.runtime import runtime_binding


EPISODES = [
    {"ordinal": 1, "episode_id": "taskview-orientation-v1-e01-raw-r1", "arm": "RAW", "replicate": 1},
    {"ordinal": 2, "episode_id": "taskview-orientation-v1-e02-taskview-r1", "arm": "TASKVIEW", "replicate": 1},
    {"ordinal": 3, "episode_id": "taskview-orientation-v1-e03-taskview-r2", "arm": "TASKVIEW", "replicate": 2},
    {"ordinal": 4, "episode_id": "taskview-orientation-v1-e04-raw-r2", "arm": "RAW", "replicate": 2},
    {"ordinal": 5, "episode_id": "taskview-orientation-v1-e05-raw-r3", "arm": "RAW", "replicate": 3},
    {"ordinal": 6, "episode_id": "taskview-orientation-v1-e06-taskview-r3", "arm": "TASKVIEW", "replicate": 3},
    {"ordinal": 7, "episode_id": "taskview-orientation-v1-e07-taskview-r4", "arm": "TASKVIEW", "replicate": 4},
    {"ordinal": 8, "episode_id": "taskview-orientation-v1-e08-raw-r4", "arm": "RAW", "replicate": 4},
]


DIMENSION_FIELD_MAP = {
    "task_scope": [
        [1, "direct_change_services"],
        [3, "boundary_status"],
        [3, "unresolved_status"],
        [3, "whole_world_complete"],
    ],
    "affected_change_set": [
        [1, "direct_change_services"],
        [2, "protected_service"],
        [2, "direct_edit_required"],
        [2, "adapter"],
        [5, "current_verification_gap"],
    ],
    "exclusions_and_unresolved": [
        [3, "boundary_subject"],
        [3, "boundary_status"],
        [3, "unresolved_subject"],
        [3, "unresolved_status"],
        [3, "dynamic_lookup_mechanism"],
        [5, "whole_world_blockers"],
    ],
    "local_implementation_semantics": [
        [1, "decoding_invariants"],
        [1, "v3_call_shape"],
        [2, "canonical_key_behavior"],
        [2, "decimal_serialization_behavior"],
        [3, "byte_stable_wire_field"],
        [3, "dynamic_lookup_mechanism"],
        [4, "missing_behaviors"],
        [5, "proposed_replacement_verification"],
    ],
    "verification_surface": [
        [2, "verification_assertion"],
        [4, "invalidated_verification"],
        [4, "downstream_result_state"],
        [4, "retained_state_update"],
        [5, "current_verification_gap"],
        [5, "proposed_replacement_verification"],
    ],
    "changed_evidence_reaction": [
        [4, "invalidated_verification"],
        [4, "missing_behaviors"],
        [4, "downstream_result_state"],
        [4, "retained_state_update"],
        [5, "current_verification_gap"],
    ],
    "scoped_exhaustiveness": [
        [3, "whole_world_complete"],
        [5, "other_gaps_in_affected_service"],
        [5, "completeness_universe"],
        [5, "whole_world_complete"],
        [5, "whole_world_blockers"],
    ],
}


def _write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def refreeze_runtime(preflight_path: Path) -> dict[str, Any]:
    sidecar = MANIFEST_PATH.with_suffix(".sha256")
    if sidecar.exists():
        raise FileExistsError("runtime manifest is already sealed")
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    if preflight.get("status") != "PASS":
        raise RuntimeError("runtime preflight did not pass")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("participant_execution_authorized"):
        raise RuntimeError("participant execution was already authorized")
    expected = [[record["arm"], record["replicate"]] for record in EPISODES]
    if manifest["stage1"]["arm_order"] != expected:
        raise RuntimeError("episode IDs do not match frozen arm order")
    binding = runtime_binding()
    runtime_files = [
        "runtime.py",
        "runtime_preflight.py",
        "runtime_manifest.py",
        "campaign.py",
        "report.py",
    ]
    missing = [name for name in runtime_files if not (PACKAGE_ROOT / name).is_file()]
    if missing:
        raise RuntimeError(f"runtime files missing before refreeze: {missing}")
    manifest["status"] = "STAGE1_RUNTIME_FROZEN_AUTHORIZED"
    manifest["participant_execution_authorized"] = True
    manifest["runtime_frozen_timestamp_ns"] = time.time_ns()
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
            },
            "episodes": EPISODES,
            "execution_order_seed": "frozen blocked order; no runtime draw",
            "runtime_preflight": {
                "status": preflight["status"],
                "receipt_path": str(preflight_path.resolve()),
                "receipt_sha256": sha256_file(preflight_path),
                "probe_trajectory_sha256": preflight["probe_trajectory_sha256"],
                "dynamic_tool_probe_trajectory_sha256": preflight[
                    "dynamic_tool_probe_trajectory_sha256"
                ],
            },
            "alternative_witness_policy": (
                "primary labels immutable; separately mark genuinely valid unanticipated "
                "local citations ALTERNATIVE_VALID_LOCAL"
            ),
        }
    )
    manifest["runtime_code_hashes"] = {
        f"research/taskview_orientation/{name}": sha256_file(PACKAGE_ROOT / name)
        for name in runtime_files
    }
    manifest["unresolved_before_execution"] = []
    manifest["manifest_integrity"] = {
        "algorithm": "sha256",
        "scope": "exact experiment_manifest.json bytes",
        "sidecar": sidecar.name,
    }
    _write(MANIFEST_PATH, manifest)
    digest = hashlib.sha256(MANIFEST_PATH.read_bytes()).hexdigest()
    sidecar.write_text(f"{digest}  {MANIFEST_PATH.name}\n", encoding="utf-8")
    return {"manifest": manifest, "manifest_sha256": digest, "sidecar": str(sidecar)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(refreeze_runtime(args.preflight), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
