"""Seal the unauthorized runtime-bound manifest for the TaskView v0.1 repeat."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import random
from pathlib import Path
from typing import Any

from research.taskview_orientation.freeze import REPOSITORY_ROOT, sha256_file
from research.taskview_orientation.runtime import cursor_version
from research.taskview_orientation.runtime_sdk import runtime_binding
from research.taskview_orientation.v01_manifest import V01_MANIFEST_PATH


PACKAGE_ROOT = V01_MANIFEST_PATH.parent.parent
RUNTIME_MANIFEST_PATH = (
    V01_MANIFEST_PATH.parent / "taskview-orientation-v01-runtime.json"
)
RUNTIME_SIDECAR_PATH = RUNTIME_MANIFEST_PATH.with_suffix(".sha256")
RUNTIME_PREFLIGHT_RECEIPT = (
    PACKAGE_ROOT / "preflight" / "taskview-orientation-v01-runtime.json"
)

RANDOMIZATION_SEED = "taskview-v01-repeat-20260831"
RUNTIME_FILES = (
    "research/taskview_orientation/runtime.py",
    "research/taskview_orientation/runtime_sdk.py",
    "research/taskview_orientation/cursor_tool_server.py",
    "research/taskview_orientation/campaign.py",
    "research/taskview_orientation/report.py",
    "research/taskview_orientation/runtime_preflight.py",
    "research/taskview_orientation/v01_preflight.py",
    "research/taskview_orientation/v01_runtime_preflight.py",
)


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def randomized_order() -> list[list[Any]]:
    """Block-randomize pair order and the starting arm, reproducibly from the seed."""

    generator = random.Random(RANDOMIZATION_SEED)
    pairs = [1, 2, 3, 4]
    generator.shuffle(pairs)
    order: list[list[Any]] = []
    for replicate in pairs:
        first = generator.choice(["RAW", "TASKVIEW"])
        second = "TASKVIEW" if first == "RAW" else "RAW"
        order.extend([[first, replicate], [second, replicate]])
    return order


def _episodes(order: list[list[Any]]) -> list[dict[str, Any]]:
    episodes = []
    for ordinal, (arm, replicate) in enumerate(order, start=1):
        episodes.append(
            {
                "ordinal": ordinal,
                "episode_id": (
                    f"taskview-orientation-v01-e{ordinal:02d}-"
                    f"{arm.lower()}-r{replicate}"
                ),
                "arm": arm,
                "replicate": replicate,
            }
        )
    return episodes


def _runtime_hashes() -> dict[str, str]:
    return {relative: sha256_file(REPOSITORY_ROOT / relative) for relative in RUNTIME_FILES}


def _criteria() -> dict[str, Any]:
    return {
        "orientation_mechanism": {
            "name": "ORIENTATION MECHANISM",
            "rule": {
                "median_paired_O_post_reduction": {"operator": ">=", "value": 0.30},
                "TASKVIEW_lower_O_post_pairs": {"operator": ">=", "value": 3, "of": 4},
                "local_implementation_correctness": "not reduced",
                "required_local_source_inspection": {"operator": ">=", "value": 0.80},
            },
            "question": "Does TaskView suppress repeated repository-side orientation?",
        },
        "net_economics": {
            "name": "NET ECONOMICS",
            "definition": (
                "net_orientation = post-phase-1 repository orientation bytes + "
                "TaskView-visible consumption bytes"
            ),
            "pair_delta": "TASKVIEW net_orientation - RAW O_post",
            "success": {
                "median_paired_net_orientation_delta": {"operator": "<", "value": 0},
                "TASKVIEW_lower_net_orientation_pairs": {
                    "operator": ">=", "value": 3, "of": 4
                },
                "repository_side_O_post_lower_pairs": {"operator": ">=", "value": 3, "of": 4},
                "required_local_source_inspection": "preserved",
            },
            "minimum_percentage_net_saving": None,
            "interpretation": "directional mechanism/economics pilot; not an effect-size estimate",
        },
        "possible_outcomes": [
            "MECHANISM PASS / ECONOMICS PASS",
            "MECHANISM PASS / ECONOMICS FAIL",
            "MECHANISM FAIL / ECONOMICS PASS",
            "MECHANISM FAIL / ECONOMICS FAIL",
            "INCONCLUSIVE where the frozen rules require it",
        ],
    }


def build_manifest() -> dict[str, Any]:
    parent = json.loads(V01_MANIFEST_PATH.read_text(encoding="utf-8"))
    parent_hash = sha256_file(V01_MANIFEST_PATH)
    binding = runtime_binding()
    binding = copy.deepcopy(binding)
    binding["cursor_agent_version"] = cursor_version()
    order = randomized_order()
    episodes = _episodes(order)

    manifest = copy.deepcopy(parent)
    manifest.update(
        {
            "experiment_version": "taskview-orientation-v01-repeat-runtime",
            "status": "STAGE1_V01_RUNTIME_PREFLIGHT_UNAUTHORIZED",
            "participant_execution_authorized": False,
            "fresh_authorization_required": True,
            "lineage": {
                "kind": "runtime_bound_replacement_repeat",
                "parent_manifest_path": str(V01_MANIFEST_PATH),
                "parent_manifest_sha256": parent_hash,
                "parent_experiment_version": parent["experiment_version"],
                "historical_stage1_manifest_sha256": parent["lineage"][
                    "parent_manifest_sha256"
                ],
                "historical_parent_immutable": True,
                "sealed_stage1_results_untouched": True,
            },
            "runtime_binding": binding,
            "runtime_code_hashes": _runtime_hashes(),
            "prospective_criteria": _criteria(),
            "randomization": {
                "procedure": (
                    "Use Python MT19937 seeded by randomization_seed; shuffle pair "
                    "replicates 1..4, then independently choose each pair's starting "
                    "arm, placing RAW and TASKVIEW adjacently within each pair."
                ),
                "randomization_seed": RANDOMIZATION_SEED,
                "arm_order": order,
                "old_stage1_order_reused": False,
            },
            "telemetry_contract": {
                "preserve_aggregate": "taskview_visible_bytes",
                "taskview_categories": [
                    "describe_catalog",
                    "describe_relation",
                    "describe_why",
                    "query_sql",
                    "assertion",
                    "rerun",
                ],
                "per_operation_fields": [
                    "count",
                    "request_bytes",
                    "response_bytes",
                    "phase",
                    "rows_returned_where_applicable",
                ],
                "first_class_report_fields": [
                    "describe_catalog_calls",
                    "describe_relation_calls",
                    "describe_why_calls",
                    "post_phase1_repository_bytes_by_phase",
                ],
            },
            "known_oracle_limitations": [
                "affected_service exact-token weakness remains frozen",
                "current_verification_gap exact-token weakness remains frozen",
                "canonical changed-evidence label weakness remains frozen",
                "do not interpret these dimensions as new scoped-exhaustiveness or staleness superiority evidence",
            ],
            "statefulness_policy": {
                "fresh_provider_session_per_episode": True,
                "same_session_across_turns": 5,
                "cross_episode_session_reuse": False,
                "summarization_injection": False,
                "artificial_context_reset": False,
                "within_episode_retry": False,
            },
            "runtime_preflight": {
                "receipt_path": str(RUNTIME_PREFLIGHT_RECEIPT),
                "status": "PENDING_LIVE_PROVIDER_PREFLIGHT",
                "participant_execution_authorized": False,
            },
        }
    )
    manifest["stage1"] = copy.deepcopy(parent["stage1"])
    manifest["stage1"].update(
        {
            "arm_order": order,
            "episodes": episodes,
            "episode_count": 8,
            "replicates_per_arm": 4,
            "turns_per_episode": 5,
            "provider": binding["provider"],
            "model": binding["model"],
            "model_version": binding["exact_model_version_identifier"],
            "participant_config": binding,
            "phase_sequence": ["1", "2", "3", "4", "5"],
            "execution_order_seed": RANDOMIZATION_SEED,
            "retry_policy": "none",
        }
    )
    manifest["arm_policy"] = {
        "kind": "blocked matched pairs",
        "arm_order": order,
        "replicates_per_arm": 4,
        "retry_policy": "none",
        "same_case": True,
        "old_raw_trajectories_reused_as_controls": False,
    }
    manifest["unresolved_before_execution"] = [
        "Live provider statefulness and dynamic transport preflight must pass.",
        "Fresh authorization is required before any participant execution.",
        "No participant campaign has been run for this v0.1 lineage.",
    ]
    manifest["manifest_integrity"] = {
        "algorithm": "sha256",
        "scope": "exact taskview-orientation-v01-runtime.json bytes",
        "sidecar": RUNTIME_SIDECAR_PATH.name,
    }
    return manifest


def write_manifest() -> tuple[Path, str]:
    if RUNTIME_MANIFEST_PATH.exists() or RUNTIME_SIDECAR_PATH.exists():
        raise FileExistsError("v0.1 runtime manifest is already sealed")
    manifest = build_manifest()
    _write(RUNTIME_MANIFEST_PATH, manifest)
    digest = hashlib.sha256(RUNTIME_MANIFEST_PATH.read_bytes()).hexdigest()
    RUNTIME_SIDECAR_PATH.write_text(
        f"{digest}  {RUNTIME_MANIFEST_PATH.name}\n", encoding="utf-8"
    )
    return RUNTIME_MANIFEST_PATH, digest


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
