"""Execute and seal the authorized TaskView v0.1 eight-episode repeat."""

from __future__ import annotations

import hashlib
import json
import shutil
import time
from pathlib import Path
from typing import Any

from research.taskview_orientation.freeze import FROZEN_ROOT, REPOSITORY_ROOT, sha256_file
from research.taskview_orientation.runner import EpisodeRunner
from research.taskview_orientation.runtime_sdk import DefaultSessionFactory, runtime_binding


CAMPAIGN_ID = "taskview-orientation-stage1-cursor-v01-harness-v4"
AUTHORIZED_MANIFEST_PATH = (
    REPOSITORY_ROOT
    / "research/taskview_orientation/manifests/"
    "taskview-orientation-v01-harness-v4-authorized.json"
)
RESULTS_ROOT = (
    REPOSITORY_ROOT / "research/taskview_orientation/results/stage1-cursor-v01-harness-v4"
)


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_manifest() -> tuple[dict[str, Any], str]:
    manifest = json.loads(AUTHORIZED_MANIFEST_PATH.read_text(encoding="utf-8"))
    digest = hashlib.sha256(AUTHORIZED_MANIFEST_PATH.read_bytes()).hexdigest()
    sidecar = AUTHORIZED_MANIFEST_PATH.with_suffix(".sha256")
    if digest != sidecar.read_text(encoding="utf-8").split()[0]:
        raise RuntimeError("authorized manifest hash drift")
    if manifest.get("status") != "STAGE1_V01_RUNTIME_FROZEN_AUTHORIZED":
        raise RuntimeError("authorized manifest status is invalid")
    if manifest.get("participant_execution_authorized") is not True:
        raise RuntimeError("participant execution is not authorized")
    if manifest["execution_authorization"]["campaign_id"] != CAMPAIGN_ID:
        raise RuntimeError("campaign identity drift")
    parent = Path(manifest["lineage"]["parent_manifest_path"])
    if sha256_file(parent) != manifest["lineage"]["parent_manifest_sha256"]:
        raise RuntimeError("unauthorized runtime parent drift")
    for section in (
        "all_frozen_input_hashes",
        "apparatus_code_hashes",
        "taskview_runtime_hashes",
        "runtime_code_hashes",
        "execution_apparatus_hashes",
    ):
        for relative, expected in manifest[section].items():
            path = FROZEN_ROOT / relative if section == "all_frozen_input_hashes" else REPOSITORY_ROOT / relative
            if not path.is_file() or sha256_file(path) != expected:
                raise RuntimeError(f"{section} drift before execution: {relative}")
    if manifest["stage1"]["episode_count"] != 8:
        raise RuntimeError("episode count drift")
    if manifest["stage1"]["turns_per_episode"] != 5:
        raise RuntimeError("turn count drift")
    if manifest["stage1"]["retry_policy"] != "none":
        raise RuntimeError("retry policy drift")
    if manifest["arm_policy"]["old_raw_trajectories_reused_as_controls"] is not False:
        raise RuntimeError("historical RAW trajectories were selected as controls")
    return manifest, digest


def _load_events(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _episode_checks(root: Path, record: dict[str, Any]) -> dict[str, Any]:
    events = _load_events(root / "telemetry.jsonl")
    sessions = {event["session_id"] for event in events if event.get("session_id")}
    errors: list[str] = []
    if len(sessions) != 1 or record["session_id"] not in sessions:
        errors.append("episode did not preserve one session")
    if sum(event["event_type"] == "TURN_OUTPUT" for event in events) != 5:
        errors.append("episode did not preserve five turn outputs")
    if sum(event["event_type"] == "HARNESS_MUTATION" for event in events) != 1:
        errors.append("episode did not preserve exactly one Phase 4 mutation")
    reconciliations = [
        event for event in events if event["event_type"] == "ACCOUNTING_RECONCILIATION"
    ]
    if len(reconciliations) != 5:
        errors.append("episode did not preserve five identity accounting reconciliations")
    if any(event["accounting_model"] != "cursor-mcp-identity-v1" for event in reconciliations):
        errors.append("episode accounting model drifted")
    if any(
        event["unique_logical_calls"]
        != event["bridge_executions"] + event["provider_validation_rejections"]
        for event in reconciliations
    ):
        errors.append("logical calls did not reconcile to executions or validation rejections")
    state_records = _load_events(root / "runtime_state.jsonl")
    boundaries = {item["boundary"] for item in state_records}
    if boundaries != {
        "immediately_before_phase4_source_mutation",
        "immediately_after_phase4_source_mutation",
    }:
        errors.append("Phase 4 state boundaries drifted")
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "one_session": len(sessions) == 1,
        "turns": 5,
        "accounting_discrepancies": [
            event for event in events if event["event_type"] == "ACCOUNTING_DISCREPANCY"
        ],
        "accounting_reconciliations": reconciliations,
    }


def _file_hashes(root: Path, *, exclude: set[str] = frozenset()) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha256_file(path)
        for path in sorted(item for item in root.rglob("*") if item.is_file())
        if path.relative_to(root).as_posix() not in exclude
    }


def run_campaign(results_root: Path = RESULTS_ROOT) -> dict[str, Any]:
    manifest, manifest_sha256 = _load_manifest()
    if results_root.exists():
        raise FileExistsError(f"refusing to replace existing v0.1 results: {results_root}")
    results_root.mkdir(parents=True)
    episodes = manifest["stage1"]["episodes"]
    campaign = {
        "campaign_id": CAMPAIGN_ID,
        "status": "IN_PROGRESS",
        "valid": None,
        "manifest_sha256": manifest_sha256,
        "manifest_path": str(AUTHORIZED_MANIFEST_PATH.resolve()),
        "runtime_binding": runtime_binding(),
        "participant_campaign_calls": 0,
        "episodes_completed": [],
        "started_timestamp_ns": time.time_ns(),
    }
    _write(results_root / "campaign_progress.json", campaign)

    for episode in episodes:
        try:
            current_manifest, current_digest = _load_manifest()
            if current_digest != manifest_sha256 or current_manifest != manifest:
                raise RuntimeError("authorized manifest changed after campaign start")
            episode_root = results_root / episode["episode_id"]
            factory = DefaultSessionFactory(episode_root)
            runner = EpisodeRunner(session_factory=factory)
            started = time.time_ns()
            try:
                record = runner.run(
                    arm=episode["arm"],
                    replicate=episode["replicate"],
                    output_root=episode_root,
                )
            finally:
                factory.close()
            checks = _episode_checks(episode_root, record)
            if checks["status"] != "PASS":
                raise RuntimeError(f"episode validity checks failed: {checks['errors']}")
            record.update(
                {
                    "campaign_episode_id": episode["episode_id"],
                    "campaign_ordinal": episode["ordinal"],
                    "provider": runtime_binding()["provider"],
                    "model": runtime_binding()["model"],
                    "model_version": runtime_binding()["exact_model_version_identifier"],
                    "participant_model_invoked": True,
                    "apparatus_only": False,
                    "started_timestamp_ns": started,
                    "completed_timestamp_ns": time.time_ns(),
                    "execution_checks": checks,
                }
            )
            _write(episode_root / "record.json", record)
            shutil.copy2(episode_root / "record.json", episode_root / "runner_record.raw.json")
            episode_hashes = _file_hashes(episode_root, exclude={"seal.json"})
            seal = {
                "campaign_episode_id": episode["episode_id"],
                "sealed_timestamp_ns": time.time_ns(),
                "manifest_sha256": manifest_sha256,
                "file_hashes": episode_hashes,
                "content_sha256": hashlib.sha256(
                    json.dumps(episode_hashes, sort_keys=True, separators=(",", ":")).encode()
                ).hexdigest(),
            }
            _write(episode_root / "seal.json", seal)
            campaign["participant_campaign_calls"] += 5
            campaign["episodes_completed"].append(
                {
                    **episode,
                    "trajectory_episode_id": record["episode_id"],
                    "session_id": record["session_id"],
                    "episode_seal_sha256": sha256_file(episode_root / "seal.json"),
                }
            )
            _write(results_root / "campaign_progress.json", campaign)
        except BaseException as exc:
            campaign.update(
                {
                    "status": "PILOT_ABORTED",
                    "valid": False,
                    "aborted_timestamp_ns": time.time_ns(),
                    "failure_episode": episode,
                    "failure_type": type(exc).__name__,
                    "failure": str(exc),
                }
            )
            _write(results_root / "campaign_progress.json", campaign)
            _write(results_root / "campaign_invalid.json", campaign)
            raise

    campaign.update(
        {
            "status": "SEALED",
            "valid": True,
            "completed_timestamp_ns": time.time_ns(),
            "episode_count": 8,
            "participant_turn_count": 40,
        }
    )
    _write(results_root / "campaign_progress.json", campaign)
    final_seal = {
        "campaign_id": campaign["campaign_id"],
        "status": "SEALED",
        "valid": True,
        "manifest_sha256": manifest_sha256,
        "episode_seals": {
            item["episode_id"]: item["episode_seal_sha256"]
            for item in campaign["episodes_completed"]
        },
        "campaign_progress_sha256": sha256_file(results_root / "campaign_progress.json"),
        "sealed_timestamp_ns": time.time_ns(),
    }
    _write(results_root / "campaign_seal.json", final_seal)
    return final_seal


if __name__ == "__main__":
    print(json.dumps(run_campaign(), indent=2, sort_keys=True))
