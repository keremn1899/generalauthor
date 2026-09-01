"""Deterministic, non-participant preflight for the TaskView v0.1 repeat."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

from research.taskview_orientation.fixture import (
    FROZEN_ROOT,
    SOURCE_ROOT,
    copy_frozen_task_view,
)
from research.taskview_orientation.freeze import REPOSITORY_ROOT, sha256_file, sha256_json
from research.taskview_orientation.runtime import answer_schema
from research.taskview_orientation.surface import ExperimentTaskViewSurface
from research.taskview_orientation.telemetry import (
    TelemetryRecorder,
    taskview_variant,
    visible_bytes,
)
from research.taskview_orientation.tools import EpisodeTools
from research.taskview_orientation.v01_manifest import (
    ORIGINAL_MANIFEST_PATH,
    V01_MANIFEST_PATH,
    V01_SIDECAR_PATH,
    _completeness_contracts,
    _semantic_fixture_hashes,
)
from taskview import TaskViewError
from taskview.migration_example import build_migration_view


PREFLIGHT_PATH = (
    V01_MANIFEST_PATH.parent.parent / "preflight" / "taskview-orientation-v01-deterministic.json"
)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _check_hashes(manifest: dict[str, Any], original: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    parent_hash = sha256_file(ORIGINAL_MANIFEST_PATH)
    if parent_hash != manifest["lineage"]["parent_manifest_sha256"]:
        errors.append("parent manifest hash drift")
    if sha256_file(V01_MANIFEST_PATH) != V01_SIDECAR_PATH.read_text().split()[0]:
        errors.append("v0.1 manifest sidecar drift")
    if manifest["participant_execution_authorized"] is not False:
        errors.append("v0.1 manifest is participant-authorized")
    if manifest["surface_revision"]["surface_version"] != "0.1":
        errors.append("v0.1 surface revision is not explicit")

    for relative, expected in manifest["all_frozen_input_hashes"].items():
        actual = sha256_file(FROZEN_ROOT / relative)
        if actual != expected:
            errors.append(f"frozen input drift: {relative}: {actual} != {expected}")
    # The v0.1 scientific preflight remains usable after a runtime-only
    # successor. Runtime identity is checked by v01_harness_manifest instead;
    # the sealed historical runtime hashes are deliberately not rewritten.
    for section in ("taskview_runtime_hashes",):
        for relative, expected in manifest[section].items():
            actual = sha256_file(REPOSITORY_ROOT / relative)
            if actual != expected:
                errors.append(f"{section} drift: {relative}: {actual} != {expected}")

    if manifest["all_frozen_input_hashes"] != original["all_frozen_input_hashes"]:
        errors.append("v0.1 manifest changed the frozen input hash set")
    if manifest["source_snapshot"] != original["source_snapshot"]:
        errors.append("source snapshot differs from original manifest")
    if manifest["phase4_replacement_sha256"] != original["phase4_replacement_sha256"]:
        errors.append("Phase 4 replacement differs from original manifest")
    if manifest["prompt_hashes"] != original["prompt_hashes"]:
        errors.append("prompt hashes differ from original manifest")
    if manifest["oracle"] != original["oracle"]:
        errors.append("oracle differs from original manifest")
    if manifest["span_classification"] != original["span_classification"]:
        errors.append("span classification differs from original manifest")
    return errors


def _check_scientific_contracts(
    manifest: dict[str, Any], original: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    current_fixture = manifest["taskview"]
    actual_fixture = _semantic_fixture_hashes()
    for field in (
        "database_sha256",
        "fixture_revision",
        "semantic_snapshot_sha256",
        "derivations_sha256",
        "completeness_contracts_sha256",
    ):
        if current_fixture[field] != actual_fixture[field]:
            errors.append(f"TaskView fixture hash drift: {field}")
    for field in (
        "database_sha256",
        "fixture_revision",
        "semantic_snapshot_sha256",
        "derivations_sha256",
    ):
        if current_fixture[field] != original["taskview"][field]:
            errors.append(f"TaskView semantic fixture drift: {field}")
    if current_fixture["database_sha256"] != sha256_file(FROZEN_ROOT / "taskview.sqlite"):
        errors.append("TaskView database hash drift")
    if manifest["taskview"]["completeness_contracts_sha256"] != sha256_json(
        _completeness_contracts()
    ):
        errors.append("completeness contract drift")
    for phase in range(1, 6):
        if sha256_json(answer_schema(phase)) != manifest["scientific_world"].get(
            "answer_schema_hashes", {}
        ).get(str(phase)):
            errors.append(f"answer schema drift: phase {phase}")
    return errors


def _surface_smoke() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="taskview-v01-preflight-") as directory:
        view = copy_frozen_task_view(Path(directory) / "taskview.sqlite")
        surface = ExperimentTaskViewSurface(view)
        try:
            catalog = surface.describe()
            relation = surface.describe(relation="protected_by")
            why = surface.describe(
                why={
                    "relation": "protected_by",
                    "tuple": {
                        "service": "service:reporting",
                        "adapter": "adapter:reporting-json-v3",
                    },
                }
            )
            star = surface.query_sql("SELECT * FROM protected_by")
            semantic_assert = surface.assertion(
                action="ASSERT",
                relation="protected_by",
                values={
                    "service": "service:reporting",
                    "adapter": "adapter:reporting-json-v3",
                },
            )
            alias_retract = surface.assertion(
                action="RETRACT",
                relation="verified_by",
                values={
                    "service_id": "service:checkout",
                    "test_id": "test:checkout-contract",
                },
            )
            stale = surface.describe(relation="verification_gap")
            rerun = surface.rerun("verification_gap")
            try:
                surface.rerun("verification_gap", status="COMPLETE")
            except TaskViewError:
                completeness_guard = "PASS"
            else:
                completeness_guard = "FAIL"
            return {
                "participant_calls": 0,
                "catalog_bytes": visible_bytes(catalog),
                "targeted_relation_bytes": visible_bytes(relation),
                "targeted_why_bytes": visible_bytes(why),
                "select_star_bytes": visible_bytes(star),
                "catalog_ceiling_bytes": 1500,
                "catalog_within_ceiling": visible_bytes(catalog) < 1500,
                "catalog_has_no_hidden_plane": "_tv_" not in json.dumps(catalog),
                "relation_is_scoped": "compatible_via" not in json.dumps(relation),
                "why_has_grounding": bool(why["why"]["grounding"]),
                "semantic_assertion": semantic_assert,
                "alias_retract_removed": alias_retract["removed"],
                "stale_state": stale["relation"]["state"],
                "rerun_row_count": rerun["row_count"],
                "rerun_state": rerun["completeness"]["state"],
                "completeness_guard": completeness_guard,
            }
        finally:
            view.close()


def _telemetry_smoke() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="taskview-v01-telemetry-") as directory:
        view = build_migration_view(Path(directory) / "migration.sqlite")
        telemetry = TelemetryRecorder(episode_id="v01-preflight", arm="TASKVIEW", replicate=0)
        tools = EpisodeTools(
            source_root=SOURCE_ROOT,
            scratch_root=Path(directory) / "scratch",
            telemetry=telemetry,
            taskview=ExperimentTaskViewSurface(view),
        )
        tools.scratch_root.mkdir()
        tools.set_phase(1)
        tools.describe()
        tools.describe(relation="protected_by")
        tools.describe(
            why={
                "relation": "protected_by",
                "tuple": {
                    "service": "service:reporting",
                    "adapter": "adapter:reporting-json-v3",
                },
            }
        )
        tools.query_sql("SELECT * FROM protected_by")
        tools.assertion(
            action="ASSERT",
            relation="protected_by",
            values={"service": "service:reporting", "adapter": "adapter:reporting-json-v3"},
        )
        tools.rerun("verification_gap")
        by_operation: dict[str, int] = {}
        by_variant: dict[str, int] = {}
        for event in telemetry.events:
            if event["event_type"] == "TASKVIEW_TOOL":
                operation = event["tool_name"]
                by_operation[operation] = by_operation.get(operation, 0) + int(
                    event["model_visible_output_bytes"]
                )
                variant = taskview_variant(event)
                by_variant[variant] = by_variant.get(variant, 0) + int(
                    event["model_visible_output_bytes"]
                )
        view.close()
        expected = {"describe", "query_sql", "assertion", "rerun"}
        expected_variants = {
            "describe_catalog",
            "describe_relation",
            "describe_why",
            "query_sql",
            "assertion",
            "rerun",
        }
        return {
            "operations_seen": sorted(by_operation),
            "all_four_operations_seen": set(by_operation) == expected,
            "visible_bytes_by_operation": by_operation,
            "variants_seen": sorted(by_variant),
            "all_v01_describe_variants_seen": set(by_variant) == expected_variants,
            "visible_bytes_by_variant": by_variant,
            "participant_calls": 0,
        }


def run_preflight() -> dict[str, Any]:
    manifest = _load(V01_MANIFEST_PATH)
    original = _load(ORIGINAL_MANIFEST_PATH)
    errors = _check_hashes(manifest, original)
    errors.extend(_check_scientific_contracts(manifest, original))
    smoke = _surface_smoke()
    telemetry = _telemetry_smoke()
    if not smoke["catalog_within_ceiling"]:
        errors.append("compact catalog exceeds 1500-byte ceiling")
    if smoke["completeness_guard"] != "PASS":
        errors.append("completeness guard failed")
    if not telemetry["all_four_operations_seen"]:
        errors.append("telemetry did not distinguish all four TaskView operations")
    if not telemetry["all_v01_describe_variants_seen"]:
        errors.append("telemetry did not distinguish v0.1 describe variants")
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "manifest": str(V01_MANIFEST_PATH),
        "manifest_sha256": sha256_file(V01_MANIFEST_PATH),
        "parent_manifest_sha256": sha256_file(ORIGINAL_MANIFEST_PATH),
        "participant_calls": 0,
        "surface_smoke": smoke,
        "telemetry_smoke": telemetry,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result = run_preflight()
    if args.write:
        PREFLIGHT_PATH.parent.mkdir(parents=True, exist_ok=True)
        PREFLIGHT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
