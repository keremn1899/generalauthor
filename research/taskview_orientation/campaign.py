"""Execute and seal the single authorized eight-episode Stage 1 campaign."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import time
from pathlib import Path
from typing import Any

from research.taskview_orientation.freeze import FROZEN_ROOT, REPOSITORY_ROOT, sha256_file
from research.taskview_orientation.recovery_manifest import NEXT_MANIFEST_PATH
from research.taskview_orientation.runner import EpisodeRunner
from research.taskview_orientation.runtime_sdk import DefaultSessionFactory, runtime_binding
from research.taskview_orientation.runtime_manifest import EPISODES


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _manifest_digest() -> str:
    return hashlib.sha256(NEXT_MANIFEST_PATH.read_bytes()).hexdigest()


def _verify_manifest() -> tuple[dict[str, Any], str]:
    manifest = json.loads(NEXT_MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("status") != "STAGE1_CURSOR_RUNTIME_FROZEN_AUTHORIZED":
        raise RuntimeError("runtime manifest is not authorized")
    if not manifest.get("participant_execution_authorized"):
        raise RuntimeError("participant execution is not authorized")
    sidecar = NEXT_MANIFEST_PATH.with_suffix(".sha256")
    expected = sidecar.read_text(encoding="utf-8").split()[0]
    actual = _manifest_digest()
    if actual != expected:
        raise RuntimeError(f"runtime manifest hash drift: {actual} != {expected}")
    for relative, digest in manifest["all_frozen_input_hashes"].items():
        path = FROZEN_ROOT / relative
        if not path.is_file() or sha256_file(path) != digest:
            raise RuntimeError(f"frozen input drift before execution: {relative}")
    for relative, digest in manifest["apparatus_code_hashes"].items():
        path = REPOSITORY_ROOT / relative
        if not path.is_file() or sha256_file(path) != digest:
            raise RuntimeError(f"frozen apparatus code drift before execution: {relative}")
    for relative, digest in manifest["taskview_runtime_hashes"].items():
        path = REPOSITORY_ROOT / relative
        if not path.is_file() or sha256_file(path) != digest:
            raise RuntimeError(f"TaskView runtime drift before execution: {relative}")
    for relative, digest in manifest["runtime_code_hashes"].items():
        path = REPOSITORY_ROOT / relative
        if not path.is_file() or sha256_file(path) != digest:
            raise RuntimeError(f"runtime adapter drift before execution: {relative}")
    if manifest["stage1"]["episodes"] != EPISODES:
        raise RuntimeError("episode matrix drift")
    return manifest, actual


def _load_events(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _episode_checks(root: Path, record: dict[str, Any]) -> dict[str, Any]:
    events = _load_events(root / "telemetry.jsonl")
    sessions = {event["session_id"] for event in events if event.get("session_id")}
    errors = []
    if len(sessions) != 1 or record["session_id"] not in sessions:
        errors.append("episode did not preserve one session")
    if sum(event["event_type"] == "TURN_OUTPUT" for event in events) != 5:
        errors.append("episode did not preserve five turn outputs")
    if sum(event["event_type"] == "HARNESS_MUTATION" for event in events) != 1:
        errors.append("episode did not preserve exactly one Phase 4 mutation")
    allowed = {"search_source", "read_source", "write_scratch"}
    if record["arm"] == "TASKVIEW":
        allowed |= {"describe", "query_sql", "assertion", "rerun"}
    actual_tools = {event["tool_name"] for event in events if event["event_type"] == "TOOL_CALL"}
    if not actual_tools <= allowed:
        errors.append(f"undeclared tools in telemetry: {sorted(actual_tools - allowed)}")
    state_records = _load_events(root / "runtime_state.jsonl")
    boundaries = {item["boundary"] for item in state_records}
    expected_boundaries = {
        "immediately_before_phase4_source_mutation",
        "immediately_after_phase4_source_mutation",
    }
    if boundaries != expected_boundaries:
        errors.append(f"Phase 4 state boundary records differ: {sorted(boundaries)}")
    mutation = next(event for event in events if event["event_type"] == "HARNESS_MUTATION")
    before_state = next(
        item for item in state_records if item["boundary"].startswith("immediately_before")
    )
    after_state = next(
        item for item in state_records if item["boundary"].startswith("immediately_after")
    )
    accounting_discrepancies = [
        event for event in events if event["event_type"] == "ACCOUNTING_DISCREPANCY"
    ]
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "one_session": len(sessions) == 1,
        "turns": 5,
        "mutation": mutation,
        "notification_delivered": any(
            event["event_type"] == "TURN_INPUT" and event["phase"] == 4 for event in events
        ),
        "taskview_state_immediately_before": before_state["taskview_state"],
        "taskview_state_immediately_after": after_state["taskview_state"],
        "accounting_discrepancies": accounting_discrepancies,
    }


def _file_hashes(root: Path, *, exclude: set[str] = frozenset()) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha256_file(path)
        for path in sorted(item for item in root.rglob("*") if item.is_file())
        if path.relative_to(root).as_posix() not in exclude
    }


def _resume_state(
    results_root: Path, manifest_sha256: str
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Validate a previous aborted attempt at results_root for safe resumption.

    Only ever resumes episodes sealed under the *exact* manifest hash about to
    run again -- a code fix mints a new manifest_sha256 (authorize_cursor_recovery_vN
    bumps participant_authorized_timestamp_ns unconditionally), so this only
    fires for a same-manifest retry, never across a fix. That is deliberate:
    whether an already-sealed episode remains valid after a code change is not
    something to infer, so a changed manifest always starts results_root fresh.
    Raises rather than silently proceeding if results_root cannot be fully
    accounted for as a resumable aborted attempt.
    """
    invalid_path = results_root / "campaign_invalid.json"
    if not invalid_path.is_file():
        raise FileExistsError(
            f"refusing to replace campaign results: {results_root} exists without a "
            "recognizable aborted-attempt marker"
        )
    previous = json.loads(invalid_path.read_text(encoding="utf-8"))
    if previous.get("status") != "PILOT_ABORTED" or previous.get("valid") is not False:
        raise RuntimeError(f"refusing to resume {results_root}: not marked PILOT_ABORTED")
    if previous.get("manifest_sha256") != manifest_sha256:
        raise RuntimeError(
            f"refusing to resume {results_root}: sealed under a different authorized manifest"
        )
    resumed: dict[str, dict[str, Any]] = {}
    for item in previous.get("episodes_completed", []):
        episode_root = results_root / item["episode_id"]
        seal_path = episode_root / "seal.json"
        if not seal_path.is_file() or sha256_file(seal_path) != item["episode_seal_sha256"]:
            raise RuntimeError(f"resume candidate seal missing or drifted: {episode_root}")
        seal = json.loads(seal_path.read_text(encoding="utf-8"))
        if seal.get("manifest_sha256") != manifest_sha256:
            raise RuntimeError(f"resume candidate sealed under a different manifest: {episode_root}")
        if _file_hashes(episode_root, exclude={"seal.json"}) != seal["file_hashes"]:
            raise RuntimeError(f"resume candidate file contents drifted: {episode_root}")
        resumed[item["episode_id"]] = item
    failure_episode = previous.get("failure_episode")
    if failure_episode and failure_episode["episode_id"] not in resumed:
        stray = results_root / failure_episode["episode_id"]
        if stray.exists():
            shutil.rmtree(stray)
    invalid_path.unlink()
    (results_root / "campaign_invalid_seal.json").unlink(missing_ok=True)
    return resumed, previous


def run_campaign(results_root: Path) -> dict[str, Any]:
    manifest, manifest_sha256 = _verify_manifest()
    if results_root.exists():
        resumed_episodes, previous = _resume_state(results_root, manifest_sha256)
    else:
        results_root.mkdir(parents=True)
        resumed_episodes, previous = {}, {}
    campaign = {
        "campaign_id": "taskview-orientation-stage1-cursor-v3",
        "status": "IN_PROGRESS",
        "valid": None,
        "manifest_sha256": manifest_sha256,
        "runtime_binding": runtime_binding(),
        "started_timestamp_ns": previous.get("started_timestamp_ns", time.time_ns()),
        "episodes_completed": [
            resumed_episodes[episode["episode_id"]]
            for episode in EPISODES
            if episode["episode_id"] in resumed_episodes
        ],
    }
    if previous:
        campaign["resumed_from"] = {
            "aborted_timestamp_ns": previous.get("aborted_timestamp_ns"),
            "failure_episode": previous.get("failure_episode"),
            "failure_type": previous.get("failure_type"),
            "failure": previous.get("failure"),
            "episodes_already_completed": len(resumed_episodes),
        }
    first_participant_call_timestamp_ns = previous.get("first_participant_call_timestamp_ns")
    if first_participant_call_timestamp_ns is not None:
        campaign["first_participant_call_timestamp_ns"] = first_participant_call_timestamp_ns
    _write(results_root / "campaign_progress.json", campaign)
    for episode in EPISODES:
        if episode["episode_id"] in resumed_episodes:
            continue
        try:
            _verify_manifest()
            episode_root = results_root / episode["episode_id"]
            factory = DefaultSessionFactory(episode_root)
            runner = EpisodeRunner(session_factory=factory)
            started = time.time_ns()
            if first_participant_call_timestamp_ns is None:
                first_participant_call_timestamp_ns = started
                campaign["first_participant_call_timestamp_ns"] = started
                _write(results_root / "campaign_progress.json", campaign)
            try:
                record = runner.run(
                    arm=episode["arm"],
                    replicate=episode["replicate"],
                    output_root=episode_root,
                )
            finally:
                factory.close()
            completed = time.time_ns()
            shutil.copy2(episode_root / "record.json", episode_root / "runner_record.raw.json")
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
                    "completed_timestamp_ns": completed,
                    "execution_checks": checks,
                }
            )
            _write(episode_root / "record.json", record)
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
            campaign["episodes_completed"].append(
                {
                    **episode,
                    "trajectory_episode_id": record["episode_id"],
                    "session_id": record["session_id"],
                    "episode_seal_sha256": sha256_file(episode_root / "seal.json"),
                    "completed_timestamp_ns": completed,
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
    episode_seals = {
        item["episode_id"]: item["episode_seal_sha256"]
        for item in campaign["episodes_completed"]
    }
    final_seal = {
        "campaign_id": campaign["campaign_id"],
        "status": "SEALED",
        "valid": True,
        "manifest_sha256": manifest_sha256,
        "episode_seals": episode_seals,
        "campaign_progress_sha256": sha256_file(results_root / "campaign_progress.json"),
        "sealed_timestamp_ns": time.time_ns(),
    }
    _write(results_root / "campaign_seal.json", final_seal)
    return final_seal


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run_campaign(args.results), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
