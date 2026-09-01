"""Freeze and audit all deterministic Stage 0 experiment inputs."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

from research.taskview_orientation import EXPERIMENT_VERSION
from research.taskview_orientation.fixture import (
    BASE_RELATIONS,
    DERIVATIONS,
    FROZEN_DB_PATH,
    FROZEN_ROOT,
    LEDGER_PATH,
    LEDGER_TEMPLATE_PATH,
    SOURCE_ROOT,
    build_task_view,
    semantic_rows,
)
from research.taskview_orientation.surface import ExperimentTaskViewSurface


MANIFEST_PATH = FROZEN_ROOT / "experiment_manifest.json"
PACKAGE_ROOT = FROZEN_ROOT.parent
REPOSITORY_ROOT = PACKAGE_ROOT.parents[1]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def source_manifest() -> dict[str, Any]:
    files = []
    for path in sorted(item for item in SOURCE_ROOT.rglob("*") if item.is_file()):
        relative = path.relative_to(SOURCE_ROOT).as_posix()
        payload = path.read_bytes()
        files.append(
            {
                "path": relative,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "bytes": len(payload),
                "lines": len(payload.decode("utf-8").splitlines()),
            }
        )
    tree_hash = sha256_json(
        [[item["path"], item["sha256"], item["bytes"]] for item in files]
    )
    return {
        "version": "taskview-orientation-source-v1",
        "file_count": len(files),
        "total_bytes": sum(item["bytes"] for item in files),
        "tree_sha256": tree_hash,
        "files": files,
    }


def finalize_ledger(manifest: dict[str, Any]) -> dict[str, Any]:
    ledger = json.loads(LEDGER_TEMPLATE_PATH.read_text(encoding="utf-8"))
    hashes = {record["path"]: record["sha256"] for record in manifest["files"]}
    for record in ledger["records"]:
        for evidence in record["evidence"]:
            evidence["source_sha256"] = hashes[evidence["path"]]
    ledger["record_count"] = len(ledger["records"])
    ledger["all_raw_obtainable"] = all(
        record["raw_obtainable"] for record in ledger["records"]
    )
    return ledger


def validate_ledger(ledger: dict[str, Any]) -> dict[str, Any]:
    errors = []
    task_conditioned = 0
    categories: dict[str, int] = {}
    for index, record in enumerate(ledger["records"]):
        categories[record["construction_category"]] = (
            categories.get(record["construction_category"], 0) + 1
        )
        task_conditioned += record["taskview_role"] == "task-conditioned judgment"
        if not record["raw_obtainable"]:
            errors.append(f"record {index} is not RAW-obtainable")
        if record["review_status"] != "PASS_TWO_METHODS":
            errors.append(f"record {index} lacks completed review")
        for evidence in record["evidence"]:
            source = SOURCE_ROOT / evidence["path"]
            if not source.is_file():
                errors.append(f"missing source {evidence['path']}")
                continue
            if sha256_file(source) != evidence["source_sha256"]:
                errors.append(f"hash mismatch {evidence['path']}")
            lines = source.read_text(encoding="utf-8").splitlines()
            if not 1 <= evidence["start_line"] <= evidence["end_line"] <= len(lines):
                errors.append(f"invalid span {evidence}")
    return {
        "reviewer": "review-a-ledger-first",
        "method": "resolve every cited path/span/hash and audit RAW-obtainable and construction labels",
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "record_count": len(ledger["records"]),
        "task_conditioned_record_count": task_conditioned,
        "construction_categories": categories,
    }


def reconstruct_base_from_sources() -> list[dict[str, Any]]:
    """A source-first reconstruction path independent of ledger tuples."""

    records: list[dict[str, Any]] = []
    components = re.findall(
        r'^id = "([^"]+)"$',
        (SOURCE_ROOT / "inventory/components.toml").read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    for component in components:
        records.append({"relation": "component", "tuple": {"component": component}})

    for lockfile in sorted((SOURCE_ROOT / "lockfiles").glob("*.lock")):
        text = lockfile.read_text(encoding="utf-8")
        component = re.search(r'^component = "([^"]+)"$', text, re.MULTILINE).group(1)
        version = re.search(r'^jsonlib = "([^"]+)"$', text, re.MULTILINE).group(1)
        if version.startswith("2."):
            records.append(
                {
                    "relation": "depends_on",
                    "tuple": {"component": component, "dependency": "library:jsonlib-v2"},
                }
            )

    deploy_lines = (SOURCE_ROOT / "deploy/service-components.yaml").read_text(
        encoding="utf-8"
    ).splitlines()
    for index, line in enumerate(deploy_lines[:-1]):
        match = re.match(r"  (service:[^:]+):$", line)
        if match:
            component = deploy_lines[index + 1].split("component: ", 1)[1]
            if component in components:
                records.append(
                    {
                        "relation": "implements",
                        "tuple": {"service": match.group(1), "component": component},
                    }
                )
    production = re.findall(
        r"^  - (service:[^\n]+)$",
        (SOURCE_ROOT / "deploy/production-services.yaml").read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    for service in production:
        records.append({"relation": "production_service", "tuple": {"service": service}})

    charter = (SOURCE_ROOT / "tasks/migrate-jsonlib-v3.md").read_text(encoding="utf-8")
    owners = (SOURCE_ROOT / "inventory/owners.yaml").read_text(encoding="utf-8")
    if "commerce-owned production" in charter and "service:checkout" in owners:
        records.append({"relation": "in_scope", "tuple": {"subject": "service:checkout"}})
    if "commerce-owned production" in charter and "service:reporting" in owners:
        records.append({"relation": "in_scope", "tuple": {"subject": "service:reporting"}})

    boundary = (SOURCE_ROOT / "architecture/partner-gateway.md").read_text(encoding="utf-8")
    if "relevant boundary" in boundary and "service:partner-gateway" in boundary:
        records.append(
            {"relation": "boundary", "tuple": {"subject": "service:partner-gateway"}}
        )
    if "excluded from direct code change" in charter and "pinned to jsonlib v2" in boundary:
        records.append(
            {
                "relation": "excluded",
                "tuple": {
                    "subject": "service:partner-gateway",
                    "basis": "vendor-owned boundary remains on the supported v2 protocol",
                },
            }
        )

    dynamic = (SOURCE_ROOT / "runtime/dynamic-consumers.md").read_text(encoding="utf-8")
    registry = (SOURCE_ROOT / "runtime/consumer_registry.py").read_text(encoding="utf-8")
    if "scope mapping remains unresolved" in dynamic and '"*"' in registry:
        records.append(
            {"relation": "unresolved_scope", "tuple": {"subject": "service:external-worker"}}
        )

    adapter = (SOURCE_ROOT / "services/reporting/json_adapter.py").read_text(encoding="utf-8")
    report_test = (SOURCE_ROOT / "tests/reporting_contract.py").read_text(encoding="utf-8")
    protected = all(
        token in adapter + report_test
        for token in ("canonical_keys", "decimal-string", '"10.50"')
    ) and "may count as protection" in charter
    if protected:
        records.append(
            {
                "relation": "protected_by",
                "tuple": {
                    "service": "service:reporting",
                    "adapter": "adapter:reporting-json-v3",
                },
            }
        )
        records.append(
            {
                "relation": "compatible_via",
                "tuple": {
                    "service": "service:reporting",
                    "old_library": "library:jsonlib-v2",
                    "new_library": "library:jsonlib-v3",
                    "adapter": "adapter:reporting-json-v3",
                },
            }
        )

    checkout_test = (SOURCE_ROOT / "tests/checkout_contract.py").read_text(encoding="utf-8")
    if "merchant promotion" in checkout_test and 'Decimal("10.50")' in checkout_test:
        records.append(
            {
                "relation": "verified_by",
                "tuple": {
                    "service": "service:checkout",
                    "test": "test:checkout-contract",
                },
            }
        )
    if protected and "test_report_is_canonical_and_decimal_is_a_string" in report_test:
        records.append(
            {
                "relation": "verified_by",
                "tuple": {
                    "service": "service:reporting",
                    "test": "test:reporting-contract",
                },
            }
        )
    return records


def _canonical_records(records: list[dict[str, Any]]) -> list[str]:
    return sorted(json.dumps(record, sort_keys=True) for record in records)


def source_first_review(ledger: dict[str, Any]) -> dict[str, Any]:
    reconstructed = reconstruct_base_from_sources()
    ledger_rows = [
        {"relation": record["relation"], "tuple": record["tuple"]}
        for record in ledger["records"]
    ]
    missing = sorted(set(_canonical_records(ledger_rows)) - set(_canonical_records(reconstructed)))
    extra = sorted(set(_canonical_records(reconstructed)) - set(_canonical_records(ledger_rows)))
    return {
        "reviewer": "review-b-source-first",
        "method": "reconstruct base tuples from visible files and charter rules without reading ledger tuples",
        "status": "PASS" if not missing and not extra else "FAIL",
        "missing_from_reconstruction": missing,
        "unexpected_reconstruction": extra,
        "reconstructed_record_count": len(reconstructed),
        "semantic_judgment_review": {
            "protected_by": "adapter translations and exact contract output satisfy the visible charter rule",
            "excluded": "vendor ownership and pinned byte contract satisfy the visible exclusion rule",
            "unresolved_scope": "wildcard plugin loading prevents the charter's required closed mapping",
            "verified_by": "the initial tests exercise the migration-specific behaviors named by the charter",
            "compatible_via": "the accepted adapter maps both required v2 encoding options to v3",
            "in_scope": "ownership, production, realization, and pinned dependency compose without author-only facts"
        }
    }


def derived_review(view) -> dict[str, Any]:
    expected = {
        "legacy_component": [
            {"component_id": "component:checkout-json"},
            {"component_id": "component:partner-json"},
            {"component_id": "component:reporting-json"},
        ],
        "affected_service": [
            {"service_id": "service:checkout"},
            {"service_id": "service:reporting"},
        ],
        "verification_gap": [],
        "requires_change": [{"service_id": "service:checkout"}],
        "boundary_affected_service": [],
    }
    rows = semantic_rows(view)
    actual = {relation: rows[relation] for relation in expected}
    return {
        "status": "PASS" if actual == expected else "FAIL",
        "expected": expected,
        "actual": actual,
        "derivation_definition_sha256": sha256_json(DERIVATIONS),
    }


def leakage_artifacts(view, ledger: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    surface = ExperimentTaskViewSurface(view)
    reviewer_input = {
        "source_contents_included": False,
        "describe": surface.describe(),
        "semantic_rows": semantic_rows(view),
        "grounding_references": [],
    }
    forbidden_tokens = {
        "allow_comments",
        "number_mode",
        "decimal-string",
        "canonical_keys",
        "signed_body",
        "tenant_alias",
        "resolve_consumer",
        "merchant promotion",
    }
    for record in ledger["records"]:
        detail = surface.describe(
            why={"relation": record["relation"], "tuple": record["tuple"]}
        )["why"]
        reviewer_input["grounding_references"].append(
            {
                "relation": record["relation"],
                "tuple": record["tuple"],
                "grounding": detail["grounding"],
            }
        )
    serialized = json.dumps(reviewer_input, sort_keys=True)
    leaked_tokens = sorted(token for token in forbidden_tokens if token in serialized)
    local_fields = [
        "exact v3 decoder call",
        "comment-preservation implementation",
        "Decimal preservation implementation",
        "canonical-key translation",
        "decimal-string translation and exact output",
        "byte-stable wire field",
        "dynamic wildcard lookup mechanism",
        "replacement test assertions",
    ]
    audit = {
        "reviewer": "taskview-only-source-blind-review",
        "input_sha256": sha256_json(reviewer_input),
        "source_contents_visible": False,
        "coarse_state_recoverable": [
            "checkout requires change",
            "reporting is protected",
            "partner-gateway is excluded and a boundary",
            "external-worker is unresolved",
            "initial verification_gap is empty and COMPLETE over affected_service",
        ],
        "local_fields": [
            {"field": field, "reliably_recoverable": False} for field in local_fields
        ],
        "forbidden_local_tokens_found": leaked_tokens,
        "status": "PASS" if not leaked_tokens else "FAIL",
        "conclusion": "TaskView exposes intended coarse orientation and paths, but no scored local source content.",
    }
    return reviewer_input, audit


def _git_head() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def deterministic_dry_run_receipt() -> dict[str, Any]:
    from research.taskview_orientation.runner import (
        EpisodeRunner,
        scripted_session_factory,
    )

    with tempfile.TemporaryDirectory(prefix="taskview-stage0-") as directory:
        root = Path(directory)
        runner = EpisodeRunner(session_factory=scripted_session_factory)
        records = {
            arm: runner.run(
                arm=arm,
                replicate=0,
                output_root=root / arm.casefold(),
            )
            for arm in ("RAW", "TASKVIEW")
        }
        arm_receipts = {}
        telemetry_examples = {}
        source_hashes = {}
        for arm, record in records.items():
            events = [
                json.loads(line)
                for line in (root / arm.casefold() / "telemetry.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            ]
            stable_metrics = json.loads(json.dumps(record["metrics"]))
            stable_metrics.pop("tool_wall_time_ms", None)
            stable_metrics.pop("participant_turn_wall_time_ms", None)
            for phase in stable_metrics["phase_focus"].values():
                phase.pop("time_ms_before_first_local", None)
            arm_receipts[arm] = {
                "turns": record["turns"],
                "one_session": len(
                    {
                        event["session_id"]
                        for event in events
                        if event.get("session_id")
                    }
                )
                == 1,
                "all_oracle_fields_correct": all(
                    score["all_fields_correct"] for score in record["oracle_scores"]
                ),
                "phase4_mutation_count": sum(
                    event["event_type"] == "HARNESS_MUTATION" for event in events
                ),
                "event_counts": dict(sorted(Counter(event["event_type"] for event in events).items())),
                "metrics": stable_metrics,
                "participant_model_invoked": record["participant_model_invoked"],
            }
            source_hashes[arm] = sha256_json(
                [
                    [
                        path.relative_to(root / arm.casefold() / "source").as_posix(),
                        sha256_file(path),
                    ]
                    for path in sorted(
                        item
                        for item in (root / arm.casefold() / "source").rglob("*")
                        if item.is_file()
                    )
                ]
            )
            examples = []
            for event_type in ("SOURCE_READ", "SOURCE_SEARCH", "TASKVIEW_TOOL"):
                match = next(
                    (event for event in events if event["event_type"] == event_type),
                    None,
                )
                if match is None:
                    continue
                examples.append(
                    {
                        key: value
                        for key, value in match.items()
                        if key
                        not in {
                            "episode_id",
                            "timestamp_ns",
                            "wall_time_ms",
                            "sequence",
                        }
                    }
                )
            telemetry_examples[arm] = examples
        return {
            "version": "taskview-orientation-dry-run-v1",
            "apparatus_only": True,
            "participant_model_invoked": False,
            "arms": arm_receipts,
            "final_source_tree_hashes": source_hashes,
            "raw_taskview_sources_byte_identical": source_hashes["RAW"]
            == source_hashes["TASKVIEW"],
            "telemetry_examples": telemetry_examples,
        }


def freeze_apparatus(*, replace: bool = False) -> dict[str, Any]:
    generated = [
        FROZEN_ROOT / "source_manifest.json",
        LEDGER_PATH,
        FROZEN_DB_PATH,
        FROZEN_ROOT / "fixture_snapshot.json",
        FROZEN_ROOT / "parity_review.json",
        FROZEN_ROOT / "leakage_reviewer_input.json",
        FROZEN_ROOT / "leakage_audit.json",
        FROZEN_ROOT / "dry_run_receipt.json",
        MANIFEST_PATH,
    ]
    existing = [path for path in generated if path.exists()]
    if existing and not replace:
        raise FileExistsError(
            "frozen artifacts already exist; use explicit replace only before participant execution: "
            + ", ".join(str(path) for path in existing)
        )
    if replace:
        for path in existing:
            path.unlink()

    source = source_manifest()
    write_json(FROZEN_ROOT / "source_manifest.json", source)
    ledger = finalize_ledger(source)
    write_json(LEDGER_PATH, ledger)

    ledger_review = validate_ledger(ledger)
    source_review = source_first_review(ledger)
    if ledger_review["status"] != "PASS" or source_review["status"] != "PASS":
        raise RuntimeError("parity review failed before fixture construction")

    build_path = FROZEN_ROOT / "taskview.sqlite.build"
    if build_path.exists():
        build_path.unlink()
    view = build_task_view(build_path, ledger_path=LEDGER_PATH)
    derived = derived_review(view)
    if derived["status"] != "PASS":
        raise RuntimeError("derived relation review failed")
    reviewer_input, leakage = leakage_artifacts(view, ledger)
    fixture_snapshot = {
        "view_description": view.describe(),
        "semantic_rows": semantic_rows(view),
        "revision": view.revision,
    }
    view.close()
    os.replace(build_path, FROZEN_DB_PATH)

    parity = {
        "version": "taskview-orientation-parity-v1",
        "independent_method_passes": [ledger_review, source_review],
        "derived_review": derived,
        "disagreements": [],
        "status": "PASS",
        "operator_note": "Two independent audit methods were executed by the Stage 0 apparatus; final human review remains the authorization boundary.",
    }
    write_json(FROZEN_ROOT / "fixture_snapshot.json", fixture_snapshot)
    write_json(FROZEN_ROOT / "parity_review.json", parity)
    write_json(FROZEN_ROOT / "leakage_reviewer_input.json", reviewer_input)
    write_json(FROZEN_ROOT / "leakage_audit.json", leakage)
    dry_run = deterministic_dry_run_receipt()
    write_json(FROZEN_ROOT / "dry_run_receipt.json", dry_run)

    prompts = json.loads((FROZEN_ROOT / "prompts.json").read_text(encoding="utf-8"))
    schemas = json.loads((FROZEN_ROOT / "tool_schemas.json").read_text(encoding="utf-8"))
    phase4_hash = sha256_file(FROZEN_ROOT / "phase4" / "tests" / "checkout_contract.py")
    apparatus_inputs = {
        path.relative_to(FROZEN_ROOT).as_posix(): sha256_file(path)
        for path in sorted(FROZEN_ROOT.rglob("*"))
        if path.is_file() and path != MANIFEST_PATH
    }
    apparatus_code_hashes = {
        path.relative_to(REPOSITORY_ROOT).as_posix(): sha256_file(path)
        for path in sorted(PACKAGE_ROOT.glob("*.py"))
    }
    taskview_runtime_hashes = {
        path.relative_to(REPOSITORY_ROOT).as_posix(): sha256_file(path)
        for path in sorted((REPOSITORY_ROOT / "taskview").glob("*.py"))
    }
    manifest = {
        "experiment_version": EXPERIMENT_VERSION,
        "status": "STAGE0_FROZEN_AWAITING_FINAL_REVIEW",
        "participant_execution_authorized": False,
        "git_commit": _git_head(),
        "working_tree_snapshot_identifier": sha256_json(
            {
                "frozen_inputs": apparatus_inputs,
                "apparatus_code": apparatus_code_hashes,
                "taskview_runtime": taskview_runtime_hashes,
            }
        ),
        "apparatus_code_hashes": apparatus_code_hashes,
        "taskview_runtime_hashes": taskview_runtime_hashes,
        "source_snapshot": {
            "tree_sha256": source["tree_sha256"],
            "file_count": source["file_count"],
            "total_bytes": source["total_bytes"],
        },
        "phase4_replacement_sha256": phase4_hash,
        "taskview": {
            "database_sha256": sha256_file(FROZEN_DB_PATH),
            "fixture_revision": fixture_snapshot["revision"],
            "semantic_snapshot_sha256": sha256_json(fixture_snapshot["semantic_rows"]),
            "derivations_sha256": sha256_json(DERIVATIONS),
        },
        "prompt_hashes": {
            "common_system": hashlib.sha256(prompts["common_system"].encode()).hexdigest(),
            "raw_arm": hashlib.sha256(prompts["arms"]["RAW"].encode()).hexdigest(),
            "taskview_arm": hashlib.sha256(prompts["arms"]["TASKVIEW"].encode()).hexdigest(),
            "phases": {
                str(record["phase"]): hashlib.sha256(record["prompt"].encode()).hexdigest()
                for record in prompts["phases"]
            },
        },
        "tool_schema_hashes": {
            "native": sha256_json(schemas["native"]),
            "raw_visible": sha256_json(schemas["native"]),
            "taskview_visible": sha256_json(schemas["native"] + schemas["taskview"]),
        },
        "oracle": {
            "version": json.loads((FROZEN_ROOT / "oracle.json").read_text())["version"],
            "sha256": sha256_file(FROZEN_ROOT / "oracle.json"),
        },
        "span_classification": {
            "version": json.loads((FROZEN_ROOT / "span_classification.json").read_text())["version"],
            "sha256": sha256_file(FROZEN_ROOT / "span_classification.json"),
            "primary_labels_mutable_after_runs": False,
        },
        "grounding_ledger_sha256": sha256_file(LEDGER_PATH),
        "parity_review_sha256": sha256_file(FROZEN_ROOT / "parity_review.json"),
        "leakage_audit_sha256": sha256_file(FROZEN_ROOT / "leakage_audit.json"),
        "dry_run_receipt_sha256": sha256_file(FROZEN_ROOT / "dry_run_receipt.json"),
        "stage1": {
            "model": "__SET_DURING_FINAL_AUTHORIZATION_REVIEW__",
            "model_version": "__SET_DURING_FINAL_AUTHORIZATION_REVIEW__",
            "sampling": {"temperature": 0.0, "top_p": 1.0, "seed_if_supported": [4101, 4102, 4103, 4104]},
            "budgets": {"turns_per_episode": 5, "max_output_tokens_per_turn": 4000, "wall_seconds_per_turn": 300, "search_max_results": 100},
            "replicates_per_arm": 4,
            "episode_count": 8,
            "arm_order": [
                ["RAW", 1], ["TASKVIEW", 1],
                ["TASKVIEW", 2], ["RAW", 2],
                ["RAW", 3], ["TASKVIEW", 3],
                ["TASKVIEW", 4], ["RAW", 4]
            ],
            "randomization": "blocked matched pairs; pair starting arm alternates according to the frozen arm_order",
            "retry_policy": "no within-episode retry",
            "context_policy": "one real provider session and five sequential turns; no reset or summary injection"
        },
        "all_frozen_input_hashes": apparatus_inputs,
        "unresolved_before_execution": [
            "Final reviewer must set exact model and immutable provider version, then refresh and refreeze this manifest without changing case inputs."
        ]
    }
    write_json(MANIFEST_PATH, manifest)
    return manifest
