"""Build and validate the unauthorized TaskView v0.1 repeat manifest."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from research.taskview_orientation.fixture import (
    COMPLETENESS_CONTRACTS,
    DERIVATIONS,
    FROZEN_DB_PATH,
    FROZEN_ROOT,
    semantic_rows,
)
from research.taskview_orientation.freeze import REPOSITORY_ROOT, sha256_file, sha256_json
from research.taskview_orientation.runtime import PROVIDER_TOOL_SCHEMAS, answer_schema, provider_tools
from research.taskview_orientation.runtime_sdk import runtime_binding
from taskview import TaskView


PACKAGE_ROOT = FROZEN_ROOT.parent
ORIGINAL_MANIFEST_PATH = FROZEN_ROOT / "experiment_manifest.json"
V01_MANIFEST_PATH = PACKAGE_ROOT / "manifests" / "taskview-orientation-v01-repeat.json"
V01_SIDECAR_PATH = V01_MANIFEST_PATH.with_suffix(".sha256")

V01_RUNTIME_FILES = (
    "campaign.py",
    "cursor_default_manifest.py",
    "cursor_tool_server.py",
    "recovery_manifest.py",
    "report.py",
    "runtime.py",
    "runtime_manifest.py",
    "runtime_preflight.py",
    "runtime_sdk.py",
)


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _hashes(paths: list[Path] | tuple[Path, ...], *, root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha256_file(path)
        for path in sorted(paths)
    }


def _completeness_contracts() -> dict[str, dict[str, Any]]:
    return {
        relation: {
            "status": contract.status.value,
            "universe": contract.universe,
            "basis": contract.basis,
            "known_gaps": list(contract.known_gaps),
        }
        for relation, contract in sorted(COMPLETENESS_CONTRACTS.items())
    }


def _semantic_fixture_hashes() -> dict[str, Any]:
    view = TaskView(FROZEN_DB_PATH, view_id="jsonlib-v3-orientation-experiment")
    try:
        semantic = semantic_rows(view)
        return {
            "database_sha256": sha256_file(FROZEN_DB_PATH),
            "fixture_revision": view.revision,
            "semantic_snapshot_sha256": sha256_json(semantic),
            "derivations_sha256": sha256_json(DERIVATIONS),
            "completeness_contracts_sha256": sha256_json(_completeness_contracts()),
        }
    finally:
        view.close()


def _current_code_hashes() -> dict[str, Any]:
    orientation_files = tuple(PACKAGE_ROOT.glob("*.py"))
    taskview_root = REPOSITORY_ROOT / "taskview"
    taskview_files = tuple(taskview_root.glob("*.py"))
    runtime_files = tuple(PACKAGE_ROOT / name for name in V01_RUNTIME_FILES)
    return {
        "orientation_code_hashes": _hashes(orientation_files, root=REPOSITORY_ROOT),
        "taskview_runtime_hashes": _hashes(taskview_files, root=REPOSITORY_ROOT),
        "runtime_code_hashes": _hashes(runtime_files, root=REPOSITORY_ROOT),
    }


def _current_surface_hashes(original: dict[str, Any]) -> dict[str, Any]:
    schemas = json.loads((FROZEN_ROOT / "tool_schemas.json").read_text(encoding="utf-8"))
    native = provider_tools(schemas["native"])
    treatment = provider_tools(schemas["native"] + schemas["taskview"])
    return {
        "surface_version": "0.1",
        "parent_surface_version": "0",
        "tool_schema_hashes": {
            "native": original["tool_schema_hashes"]["native"],
            "raw_visible": original["tool_schema_hashes"]["raw_visible"],
            "taskview_v0_visible": original["tool_schema_hashes"]["taskview_visible"],
            "taskview_v01_provider_serialization": sha256_json(treatment),
            "provider_schema_map_v01": sha256_json(PROVIDER_TOOL_SCHEMAS),
        },
        "provider_serialization_sha256": {
            "RAW": sha256_json(native),
            "TASKVIEW_V01": sha256_json(treatment),
        },
        "changes": [
            "compact top-level describe catalog",
            "targeted describe(relation=...)",
            "targeted describe(why=...) without a catalog dump",
            "SELECT * accepted while hidden assertion IDs remain private",
            "assertion accepts unambiguous semantic/physical role aliases",
        ],
        "semantic_changes": [],
    }


def build_manifest() -> dict[str, Any]:
    original = json.loads(ORIGINAL_MANIFEST_PATH.read_text(encoding="utf-8"))
    original_hash = sha256_file(ORIGINAL_MANIFEST_PATH)
    code_hashes = _current_code_hashes()
    fixture_hashes = _semantic_fixture_hashes()
    answer_schema_hashes = {
        str(phase): sha256_json(answer_schema(phase)) for phase in range(1, 6)
    }
    binding = runtime_binding()
    episodes = [
        {**episode, "episode_id": episode["episode_id"].replace("-v1-", "-v01-")}
        for episode in original["stage1"]["episodes"]
    ]
    source_snapshot = copy.deepcopy(original["source_snapshot"])
    taskview = copy.deepcopy(original["taskview"])
    taskview.update(fixture_hashes)
    stage1 = {
        "arm_order": copy.deepcopy(original["stage1"]["arm_order"]),
        "episode_count": original["stage1"]["episode_count"],
        "episodes": episodes,
        "replicates_per_arm": original["stage1"]["replicates_per_arm"],
        "retry_policy": original["stage1"]["retry_policy"],
        "turns_per_episode": original["stage1"]["budgets"]["turns_per_episode"],
        "budgets": copy.deepcopy(original["stage1"]["budgets"]),
        "context_policy": original["stage1"]["context_policy"],
        "sampling": copy.deepcopy(original["stage1"]["sampling"]),
        "model": binding["model"],
        "model_version": binding["exact_model_version_identifier"],
        "provider": binding["provider"],
        "participant_config": binding,
        "phase_sequence": ["1", "2", "3", "4", "5"],
    }
    manifest = {
        "experiment_version": "taskview-orientation-v01-repeat",
        "status": "STAGE1_V01_REPEAT_AWAITING_FRESH_AUTHORIZATION",
        "participant_execution_authorized": False,
        "fresh_authorization_required": True,
        "lineage": {
            "kind": "replacement_repeat",
            "parent_manifest_path": str(ORIGINAL_MANIFEST_PATH),
            "parent_manifest_sha256": original_hash,
            "parent_experiment_version": original["experiment_version"],
            "historical_parent_immutable": True,
            "sealed_stage1_results_untouched": True,
        },
        "surface_revision": _current_surface_hashes(original),
        "all_frozen_input_hashes": copy.deepcopy(original["all_frozen_input_hashes"]),
        "source_snapshot": source_snapshot,
        "phase4_replacement_sha256": original["phase4_replacement_sha256"],
        "prompt_hashes": copy.deepcopy(original["prompt_hashes"]),
        "oracle": copy.deepcopy(original["oracle"]),
        "span_classification": copy.deepcopy(original["span_classification"]),
        "taskview": taskview,
        **code_hashes,
        "apparatus_code_hashes": {
            path: code_hashes["orientation_code_hashes"][path]
            for path in original["apparatus_code_hashes"]
        },
        "scientific_world": {
            "status": "UNCHANGED",
            "source_tree_sha256": source_snapshot["tree_sha256"],
            "phase4_replacement_sha256": original["phase4_replacement_sha256"],
            "taskview_database_sha256": fixture_hashes["database_sha256"],
            "semantic_snapshot_sha256": fixture_hashes["semantic_snapshot_sha256"],
            "derivations_sha256": fixture_hashes["derivations_sha256"],
            "completeness_contracts_sha256": fixture_hashes[
                "completeness_contracts_sha256"
            ],
            "prompt_hashes": copy.deepcopy(original["prompt_hashes"]),
            "oracle_sha256": original["oracle"]["sha256"],
            "span_classification_sha256": original["span_classification"]["sha256"],
            "raw_native_tool_schema_sha256": original["tool_schema_hashes"]["native"],
            "answer_schema_hashes": answer_schema_hashes,
            "phase_sequence": stage1["phase_sequence"],
        },
        "stage1": stage1,
        "arm_policy": {
            "kind": "blocked matched pairs",
            "arm_order": copy.deepcopy(original["stage1"]["arm_order"]),
            "replicates_per_arm": stage1["replicates_per_arm"],
            "retry_policy": stage1["retry_policy"],
            "same_case": True,
        },
        "unresolved_before_execution": [
            "Fresh authorization is required before any participant execution.",
            "No participant campaign has been run for this v0.1 lineage.",
        ],
        "manifest_integrity": {
            "algorithm": "sha256",
            "scope": "exact taskview-orientation-v01-repeat.json bytes",
            "sidecar": V01_SIDECAR_PATH.name,
        },
    }
    manifest["working_tree_snapshot_identifier"] = sha256_json(
        {
            "frozen_inputs": manifest["all_frozen_input_hashes"],
            "orientation_code": manifest["orientation_code_hashes"],
            "taskview_runtime": manifest["taskview_runtime_hashes"],
            "runtime_code": manifest["runtime_code_hashes"],
        }
    )
    return manifest


def write_manifest() -> tuple[Path, str]:
    manifest = build_manifest()
    _write_json(V01_MANIFEST_PATH, manifest)
    digest = sha256_file(V01_MANIFEST_PATH)
    V01_SIDECAR_PATH.write_text(f"{digest}  {V01_MANIFEST_PATH.name}\n", encoding="utf-8")
    return V01_MANIFEST_PATH, digest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if not args.write:
        print(json.dumps(build_manifest(), indent=2, sort_keys=True))
        return
    path, digest = write_manifest()
    print(json.dumps({"manifest": str(path), "sha256": digest}, sort_keys=True))


if __name__ == "__main__":
    main()
