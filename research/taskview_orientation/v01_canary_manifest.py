"""Create the runtime-only manifest for the single v4 search-fix canary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from research.taskview_orientation.freeze import REPOSITORY_ROOT, sha256_file
from research.taskview_orientation.runtime_accounting import ACCOUNTING_MODEL_VERSION
from research.taskview_orientation.runtime_sdk import runtime_binding
from research.taskview_orientation.v01_harness_manifest import HARNESS_MANIFEST_PATH


PACKAGE_ROOT = Path(__file__).parent
MANIFEST_PATH = PACKAGE_ROOT / "manifests/taskview-orientation-v01-canary-v4-searchfix.json"
SIDECAR_PATH = MANIFEST_PATH.with_suffix(".sha256")
CANARY_ID = "taskview-orientation-stage1-cursor-v01-canary-v4-searchfix"
RUNTIME_FILES = (
    "research/taskview_orientation/tools.py",
    "research/taskview_orientation/runtime_accounting.py",
    "research/taskview_orientation/runtime_sdk.py",
    "research/taskview_orientation/cursor_tool_server.py",
    "research/taskview_orientation/telemetry.py",
    "research/taskview_orientation/runner.py",
    "research/taskview_orientation/v01_canary.py",
)


def build_manifest(*, authorized: bool = False) -> dict[str, Any]:
    parent = json.loads(HARNESS_MANIFEST_PATH.read_text(encoding="utf-8"))
    parent_hash = sha256_file(HARNESS_MANIFEST_PATH)
    return {
        "experiment_version": "taskview-orientation-v01-canary-v4-searchfix",
        "status": "CANARY_AUTHORIZED" if authorized else "CANARY_DETERMINISTIC_VALIDATED_UNAUTHORIZED",
        "participant_execution_authorized": authorized,
        "canary_only": True,
        "campaign_id": CANARY_ID,
        "lineage": {
            "kind": "search_source_binary_skip_runtime_fix",
            "parent_v4_harness_manifest_path": str(HARNESS_MANIFEST_PATH),
            "parent_v4_harness_manifest_sha256": parent_hash,
            "scientific_world_changed": False,
            "taskview_semantics_changed": False,
            "participant_prompts_changed": False,
        },
        "runtime_binding": runtime_binding(),
        "accounting_model": ACCOUNTING_MODEL_VERSION,
        "runtime_code_hashes": {
            relative: sha256_file(REPOSITORY_ROOT / relative)
            for relative in RUNTIME_FILES
        },
        "search_source_fix": {
            "skips_generated_cache_directories": ["__pycache__", ".pytest_cache", ".mypy_cache"],
            "skips_known_binary_suffixes": True,
            "skips_only_unicode_decode_errors": True,
            "propagates_other_io_errors": True,
            "preserves_regex_scope_order_limit_semantics": True,
        },
        "source_snapshot": parent["source_snapshot"],
        "all_frozen_input_hashes": parent["all_frozen_input_hashes"],
        "taskview": parent["taskview"],
        "stage1": {"turns_per_canary": 5, "scientific_campaign_turns": 0},
        "next_action": "run exactly one fresh five-phase TASKVIEW canary; never use as campaign data",
    }


def write_manifest(*, authorized: bool) -> tuple[Path, str]:
    manifest = build_manifest(authorized=authorized)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    digest = sha256_file(MANIFEST_PATH)
    SIDECAR_PATH.write_text(f"{digest}  {MANIFEST_PATH.name}\n", encoding="utf-8")
    return MANIFEST_PATH, digest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authorize", action="store_true")
    args = parser.parse_args()
    path, digest = write_manifest(authorized=args.authorize)
    print(json.dumps({"manifest": str(path), "sha256": digest, "authorized": args.authorize}, sort_keys=True))


if __name__ == "__main__":
    main()
