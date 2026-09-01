"""Create the separately sealed execution-authorized v0.1 manifest."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import time
from pathlib import Path
from typing import Any

from research.taskview_orientation.freeze import REPOSITORY_ROOT, sha256_file
from research.taskview_orientation.v01_runtime_manifest import (
    RUNTIME_MANIFEST_PATH,
    RUNTIME_SIDECAR_PATH,
)


PACKAGE_ROOT = RUNTIME_MANIFEST_PATH.parent.parent
AUTHORIZED_MANIFEST_PATH = (
    RUNTIME_MANIFEST_PATH.parent / "taskview-orientation-v01-authorized.json"
)
AUTHORIZED_SIDECAR_PATH = AUTHORIZED_MANIFEST_PATH.with_suffix(".sha256")
LINEAGE_NOTE_PATH = RUNTIME_MANIFEST_PATH.parent / "taskview-v01-lineage-note.md"
CAMPAIGN_CODE = REPOSITORY_ROOT / "research/taskview_orientation/v01_campaign.py"
REPORT_CODE = REPOSITORY_ROOT / "research/taskview_orientation/v01_report.py"


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_manifest() -> dict[str, Any]:
    parent = json.loads(RUNTIME_MANIFEST_PATH.read_text(encoding="utf-8"))
    parent_hash = sha256_file(RUNTIME_MANIFEST_PATH)
    manifest = copy.deepcopy(parent)
    manifest.update(
        {
            "experiment_version": "taskview-orientation-v01-repeat-authorized",
            "status": "STAGE1_V01_RUNTIME_FROZEN_AUTHORIZED",
            "participant_execution_authorized": True,
            "fresh_authorization_required": False,
            "lineage": {
                "kind": "execution_authorized_descendant",
                "parent_manifest_path": str(RUNTIME_MANIFEST_PATH),
                "parent_manifest_sha256": parent_hash,
                "parent_experiment_version": parent["experiment_version"],
                "historical_stage1_manifest_sha256": parent["lineage"][
                    "historical_stage1_manifest_sha256"
                ],
                "historical_parent_immutable": True,
                "unauthorized_parent_immutable": True,
                "sealed_stage1_results_untouched": True,
            },
            "provenance": {
                "lineage_note_path": str(LINEAGE_NOTE_PATH),
                "lineage_note_sha256": sha256_file(LINEAGE_NOTE_PATH),
                "attested_unavailable_transient_manifest_sha256": (
                    "6e3f5498aaafa50da949857d3061525d2aa51afaa4e45a03b47b00af774c83e1"
                ),
                "attested_transient_bytes_available": False,
                "historical_fields_inferred": False,
            },
            "execution_authorization": {
                "authorized_timestamp_ns": time.time_ns(),
                "authorization_basis": (
                    "Fresh user authorization after exact retained-lineage and scientific-integrity check."
                ),
                "campaign_id": "taskview-orientation-stage1-cursor-v01",
                "results_root": "research/taskview_orientation/results/stage1-cursor-v01",
                "report_module": "research.taskview_orientation.v01_report",
                "retry_policy": "none",
                "within_episode_retry": False,
                "selective_reruns": False,
            },
            "execution_apparatus_hashes": {
                "research/taskview_orientation/v01_campaign.py": sha256_file(CAMPAIGN_CODE),
                "research/taskview_orientation/v01_report.py": sha256_file(REPORT_CODE),
            },
        }
    )
    manifest["runtime_preflight"] = {
        **copy.deepcopy(parent["runtime_preflight"]),
        "status": "PASS",
        "receipt_path": str(
            PACKAGE_ROOT / "preflight" / "taskview-orientation-v01-runtime.json"
        ),
        "receipt_sha256": sha256_file(
            PACKAGE_ROOT / "preflight" / "taskview-orientation-v01-runtime.json"
        ),
        "participant_campaign_calls_before_authorization": 0,
    }
    manifest["unresolved_before_execution"] = []
    manifest["manifest_integrity"] = {
        "algorithm": "sha256",
        "scope": "exact taskview-orientation-v01-authorized.json bytes",
        "sidecar": AUTHORIZED_SIDECAR_PATH.name,
    }
    return manifest


def write_manifest() -> tuple[Path, str]:
    if AUTHORIZED_MANIFEST_PATH.exists() or AUTHORIZED_SIDECAR_PATH.exists():
        raise FileExistsError("authorized v0.1 manifest is already sealed")
    if sha256_file(RUNTIME_MANIFEST_PATH) != RUNTIME_SIDECAR_PATH.read_text().split()[0]:
        raise RuntimeError("unauthorized runtime parent manifest is not hash-valid")
    manifest = build_manifest()
    _write(AUTHORIZED_MANIFEST_PATH, manifest)
    digest = hashlib.sha256(AUTHORIZED_MANIFEST_PATH.read_bytes()).hexdigest()
    AUTHORIZED_SIDECAR_PATH.write_text(
        f"{digest}  {AUTHORIZED_MANIFEST_PATH.name}\n", encoding="utf-8"
    )
    return AUTHORIZED_MANIFEST_PATH, digest


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
