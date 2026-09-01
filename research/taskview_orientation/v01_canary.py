"""Run and seal exactly one live TASKVIEW v0.1 infrastructure canary."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from research.taskview_orientation.freeze import REPOSITORY_ROOT, sha256_file
from research.taskview_orientation.runner import EpisodeRunner
from research.taskview_orientation.runtime_sdk import DefaultSessionFactory, runtime_binding
from research.taskview_orientation.v01_canary_manifest import (
    CANARY_ID,
    MANIFEST_PATH,
)


RESULTS_ROOT = REPOSITORY_ROOT / "research/taskview_orientation/results/stage1-cursor-v01-canary-v4-searchfix"


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _events(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _load_manifest() -> tuple[dict[str, Any], str]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    digest = sha256_file(MANIFEST_PATH)
    sidecar = MANIFEST_PATH.with_suffix(".sha256")
    if sidecar.read_text(encoding="utf-8").split()[0] != digest:
        raise RuntimeError("canary manifest sidecar drift")
    if manifest.get("status") != "CANARY_AUTHORIZED" or not manifest.get("participant_execution_authorized"):
        raise RuntimeError("canary is not authorized")
    if manifest.get("campaign_id") != CANARY_ID or not manifest.get("canary_only"):
        raise RuntimeError("canary identity drift")
    parent = Path(manifest["lineage"]["parent_v4_harness_manifest_path"])
    if sha256_file(parent) != manifest["lineage"]["parent_v4_harness_manifest_sha256"]:
        raise RuntimeError("parent v4 harness manifest drift")
    for relative, expected in manifest["runtime_code_hashes"].items():
        if sha256_file(REPOSITORY_ROOT / relative) != expected:
            raise RuntimeError(f"canary runtime drift: {relative}")
    return manifest, digest


def _search_report(root: Path) -> list[dict[str, Any]]:
    trajectory = _events(root / "provider_trajectory.jsonl")
    telemetry = _events(root / "telemetry.jsonl")
    skipped_by_signature = {
        (
            event["phase"],
            event.get("search_query"),
            event.get("search_scope"),
        ): event
        for event in telemetry
        if event["event_type"] == "SOURCE_SEARCH"
    }
    reports: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in trajectory:
        message = (item.get("event") or {}).get("sdk_message") or {}
        if message.get("type") != "tool_call" or message.get("status") not in {"completed", "error"}:
            continue
        args = message.get("args") or {}
        if args.get("toolName") != "search_source":
            continue
        call_id = str(message.get("call_id"))
        if call_id in seen:
            continue
        seen.add(call_id)
        tool_args = args.get("args") or {}
        result = message.get("result") or {}
        value = (result.get("value") or {}) if isinstance(result, dict) else {}
        is_error = bool(value.get("isError"))
        key = (item.get("phase"), tool_args.get("query"), tool_args.get("scope"))
        source_event = skipped_by_signature.get(key)
        payload = ((value.get("content") or [{}])[0].get("text") or {}).get("text", "")
        reports.append(
            {
                "phase": item.get("phase"),
                "call_id": call_id,
                "scope": tool_args.get("scope"),
                "pattern": tool_args.get("query"),
                "status": "error" if is_error else "success",
                "skipped_file_count": source_event.get("skipped_file_count", 0) if source_event else 0,
                "skipped_files": source_event.get("skipped_files", []) if source_event else [],
                "hits_returned": source_event.get("result_count", 0) if source_event else None,
                "error": payload if is_error else None,
            }
        )
    return reports


def _check(root: Path, record: dict[str, Any]) -> dict[str, Any]:
    events = _events(root / "telemetry.jsonl")
    errors: list[str] = []
    sessions = {event.get("session_id") for event in events if event.get("session_id")}
    if len(sessions) != 1 or record.get("session_id") not in sessions:
        errors.append("session identity was not stable")
    if sum(event["event_type"] == "TURN_OUTPUT" for event in events) != 5:
        errors.append("expected five turn outputs")
    reconciliations = [event for event in events if event["event_type"] == "ACCOUNTING_RECONCILIATION"]
    if len(reconciliations) != 5:
        errors.append("expected five accounting reconciliations")
    logical = bridge = delivered = 0
    bytes_total = 0
    for event in reconciliations:
        logical += int(event["unique_logical_calls"])
        bridge += int(event["bridge_executions"])
        delivered += int(event["model_visible_tool_results"])
        bytes_total += int(event["model_visible_tool_result_bytes"])
        if not (
            event["unique_logical_calls"] == event["bridge_executions"] == event["model_visible_tool_results"]
        ):
            errors.append(f"turn {event['phase']} count reconciliation failed")
    delivery_ids = [
        (event.get("provider_session_id"), event.get("provider_call_id"))
        for event in events
        if event["event_type"] == "TOOL_RESULT_DELIVERED_TO_MODEL"
    ]
    if len(delivery_ids) != len(set(delivery_ids)):
        errors.append("duplicate result delivery")
    execution_ids = [
        event.get("bridge_execution_id")
        for event in events
        if event["event_type"] in {"SOURCE_SEARCH", "SOURCE_READ", "TASKVIEW_TOOL", "SCRATCH_WRITE", "TOOL_ERROR"}
        and event.get("bridge_execution_id") is not None
    ]
    if len(execution_ids) != len(set(execution_ids)):
        errors.append("duplicate execution")
    if any(event["event_type"] == "ACCOUNTING_DISCREPANCY" for event in events):
        errors.append("accounting discrepancy emitted")
    if any(event["event_type"] == "PROVIDER_RETRY" for event in events):
        errors.append("provider retry emitted")
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "one_provider_session": len(sessions) == 1,
        "sdk_lifecycle_observations": sum(int(event["sdk_tool_lifecycle_observations"]) for event in reconciliations),
        "unique_logical_calls": logical,
        "bridge_executions": bridge,
        "terminal_results_delivered": delivered,
        "exact_delivered_bytes": bytes_total,
        "duplicate_executions": 0 if len(execution_ids) == len(set(execution_ids)) else len(execution_ids) - len(set(execution_ids)),
        "duplicate_deliveries": 0 if len(delivery_ids) == len(set(delivery_ids)) else len(delivery_ids) - len(set(delivery_ids)),
        "unexplained_residual": 0,
        "executed_error_results": sum(event["event_type"] == "TOOL_ERROR" for event in events),
        "successful_results": sum(
            event["event_type"] in {"SOURCE_SEARCH", "SOURCE_READ", "TASKVIEW_TOOL", "SCRATCH_WRITE"}
            for event in events
        ),
        "validation_rejections": sum(
            int(event.get("provider_validation_rejected", False))
            for event in events
            if event["event_type"] == "TOOL_RESULT_DELIVERED_TO_MODEL"
        ),
    }


def run_canary(results_root: Path = RESULTS_ROOT) -> dict[str, Any]:
    manifest, manifest_sha256 = _load_manifest()
    if results_root.exists():
        # A failed pre-session launch may leave only the copied fixture behind.
        # It can be finalized as failed evidence, but an existing trajectory or
        # receipt is never replaced.
        if any((results_root / name).exists() for name in ("provider_trajectory.jsonl", "canary_receipt.json")):
            raise FileExistsError(f"refusing to replace canary output: {results_root}")
    results_root.parent.mkdir(parents=True, exist_ok=True)
    started = time.time_ns()
    factory = DefaultSessionFactory(results_root)
    try:
        record = EpisodeRunner(session_factory=factory).run(
            arm="TASKVIEW", replicate=0, output_root=results_root
        )
    except Exception as exc:
        result = {
            "canary_id": CANARY_ID,
            "status": "FAIL",
            "valid": False,
            "canary_only": True,
            "manifest_sha256": manifest_sha256,
            "manifest_path": str(MANIFEST_PATH.resolve()),
            "runtime_binding": runtime_binding(),
            "started_timestamp_ns": started,
            "completed_timestamp_ns": time.time_ns(),
            "failure_type": type(exc).__name__,
            "failure": str(exc),
            "provider_session_created": False,
            "canary_participant_turns": 0,
            "scientific_campaign_participant_turns": 0,
        }
        _write(results_root / "canary_receipt.json", result)
        hashes = {
            path.relative_to(results_root).as_posix(): sha256_file(path)
            for path in sorted(item for item in results_root.rglob("*") if item.is_file())
        }
        _write(
            results_root / "canary_seal.json",
            {
                "canary_id": CANARY_ID,
                "manifest_sha256": manifest_sha256,
                "file_hashes": hashes,
                "content_sha256": hashlib.sha256(
                    json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode()
                ).hexdigest(),
                "sealed_timestamp_ns": time.time_ns(),
            },
        )
        return result
    finally:
        factory.close()
    checks = _check(results_root, record)
    search = _search_report(results_root)
    result = {
        "canary_id": CANARY_ID,
        "status": "PASS" if checks["status"] == "PASS" else "FAIL",
        "valid": checks["status"] == "PASS",
        "canary_only": True,
        "manifest_sha256": manifest_sha256,
        "manifest_path": str(MANIFEST_PATH.resolve()),
        "runtime_binding": runtime_binding(),
        "started_timestamp_ns": started,
        "completed_timestamp_ns": time.time_ns(),
        "record": record,
        "checks": checks,
        "search_source_calls": search,
        "scientific_campaign_participant_turns": 0,
    }
    _write(results_root / "canary_receipt.json", result)
    hashes = {
        path.relative_to(results_root).as_posix(): sha256_file(path)
        for path in sorted(item for item in results_root.rglob("*") if item.is_file())
        if path.name not in {"canary_seal.json"}
    }
    seal = {
        "canary_id": CANARY_ID,
        "manifest_sha256": manifest_sha256,
        "file_hashes": hashes,
        "content_sha256": hashlib.sha256(
            json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "sealed_timestamp_ns": time.time_ns(),
    }
    _write(results_root / "canary_seal.json", seal)
    return result


def finalize_blocked_canary(results_root: Path = RESULTS_ROOT) -> dict[str, Any]:
    """Seal a launch blocked before provider creation without retrying it."""
    _manifest, manifest_sha256 = _load_manifest()
    result = {
        "canary_id": CANARY_ID,
        "status": "FAIL",
        "valid": False,
        "canary_only": True,
        "manifest_sha256": manifest_sha256,
        "manifest_path": str(MANIFEST_PATH.resolve()),
        "runtime_binding": runtime_binding(),
        "failure_type": "CursorRuntimeError",
        "failure": "CURSOR_API_KEY is required by the Cursor SDK adapter",
        "provider_session_created": False,
        "canary_participant_turns": 0,
        "scientific_campaign_participant_turns": 0,
    }
    _write(results_root / "canary_receipt.json", result)
    hashes = {
        path.relative_to(results_root).as_posix(): sha256_file(path)
        for path in sorted(item for item in results_root.rglob("*") if item.is_file())
    }
    _write(
        results_root / "canary_seal.json",
        {
            "canary_id": CANARY_ID,
            "manifest_sha256": manifest_sha256,
            "file_hashes": hashes,
            "content_sha256": hashlib.sha256(
                json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest(),
            "sealed_timestamp_ns": time.time_ns(),
        },
    )
    return result


if __name__ == "__main__":
    import sys

    print(json.dumps(
        finalize_blocked_canary() if "--finalize-failure" in sys.argv else run_canary(),
        indent=2,
        sort_keys=True,
    ))
