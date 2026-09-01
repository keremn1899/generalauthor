"""Execute and seal the authorized compiled-projection live campaign."""

from __future__ import annotations

import hashlib
import json
import shutil
import time
from pathlib import Path
from typing import Any

from research.taskview_orientation.compiled_projection import (
    CAMPAIGN_ID,
    MODEL,
    MODEL_FAST_FORBIDDEN,
    PARTICIPANT_INFERENCE_AUTHORIZED,
)
from research.taskview_orientation.compiled_projection.delivery import (
    initial_delivery_bytes,
    system_prompt_suffix,
)
from research.taskview_orientation.compiled_projection.entitlement import episode_matrix
from research.taskview_orientation.compiled_projection.metrics import score_episode
from research.taskview_orientation.compiled_projection.preflight import run_preflight
from research.taskview_orientation.fixture import copy_frozen_task_view
from research.taskview_orientation.freeze import REPOSITORY_ROOT, sha256_file
from research.taskview_orientation.runner import CLASSIFICATION_PATH, EpisodeRunner
from research.taskview_orientation.runtime import (
    CursorSessionFactory,
    MODEL as RUNTIME_MODEL,
    runtime_binding,
)
from research.taskview_orientation.surface import ExperimentTaskViewSurface
from research.taskview_orientation.telemetry import FrozenSpanClassifier


RESULTS_ROOT = (
    REPOSITORY_ROOT / "research/taskview_orientation/results/compiled-projection-v1"
)
AUTHORIZED_MANIFEST_PATH = (
    REPOSITORY_ROOT
    / "research/taskview_orientation/manifests/"
    "taskview-orientation-compiled-projection-v1-authorized.json"
)


class LiveInferenceBlocked(RuntimeError):
    pass


_SUFFIX_CACHE: dict[str, str] = {}
_DELIVERY_CACHE: dict[str, int] = {}


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_events(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _file_hashes(root: Path, *, exclude: set[str] = frozenset()) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha256_file(path)
        for path in sorted(item for item in root.rglob("*") if item.is_file())
        if path.relative_to(root).as_posix() not in exclude
    }


def condition_suffix(condition: str) -> str:
    cached = _SUFFIX_CACHE.get(condition)
    if cached is not None:
        return cached
    import tempfile

    with tempfile.TemporaryDirectory(prefix="compiled-projection-contract-") as directory:
        view = copy_frozen_task_view(Path(directory) / "taskview.sqlite")
        try:
            surface = ExperimentTaskViewSurface(view)
            text = system_prompt_suffix(surface, condition)
            _DELIVERY_CACHE[condition] = initial_delivery_bytes(surface, condition)
        finally:
            view.close()
    _SUFFIX_CACHE[condition] = text
    return text


def _load_manifest() -> tuple[dict[str, Any], str]:
    if not AUTHORIZED_MANIFEST_PATH.is_file():
        raise LiveInferenceBlocked("authorized manifest is absent")
    manifest = json.loads(AUTHORIZED_MANIFEST_PATH.read_text(encoding="utf-8"))
    digest = hashlib.sha256(AUTHORIZED_MANIFEST_PATH.read_bytes()).hexdigest()
    sidecar = AUTHORIZED_MANIFEST_PATH.with_suffix(".sha256")
    if not sidecar.is_file() or digest != sidecar.read_text(encoding="utf-8").split()[0]:
        raise LiveInferenceBlocked("authorized manifest hash drift")
    if manifest.get("status") != "COMPILED_PROJECTION_V1_LIVE_AUTHORIZED":
        raise LiveInferenceBlocked("authorized manifest status is invalid")
    if manifest.get("participant_execution_authorized") is not True:
        raise LiveInferenceBlocked("participant execution is not authorized")
    if manifest["campaign_id"] != CAMPAIGN_ID:
        raise LiveInferenceBlocked("campaign identity drift")
    if manifest["participant_model"] != MODEL or "fast" in manifest["participant_model"]:
        raise LiveInferenceBlocked("authorized participant model is not composer-2.5")
    if manifest["stage1"]["retry_policy"] != "none":
        raise LiveInferenceBlocked("retry policy drift")
    if manifest["stage1"]["within_episode_retry"] is not False:
        raise LiveInferenceBlocked("within-episode retry is not permitted")
    if manifest["stage1"]["selective_reruns"] is not False:
        raise LiveInferenceBlocked("selective reruns are not permitted")
    if manifest["stage1"]["episodes"] != episode_matrix():
        raise LiveInferenceBlocked("episode matrix drift")
    for section in ("experiment_code_hashes", "apparatus_code_hashes"):
        for relative, expected in manifest[section].items():
            path = REPOSITORY_ROOT / relative
            if not path.is_file() or sha256_file(path) != expected:
                raise LiveInferenceBlocked(f"{section} drift: {relative}")
    return manifest, digest


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
    allowed = {
        "search_source",
        "read_source",
        "write_scratch",
        "describe",
        "query_sql",
        "assertion",
        "rerun",
    }
    actual_tools = {
        event["tool_name"] for event in events if event["event_type"] == "TOOL_CALL"
    }
    if not actual_tools <= allowed:
        errors.append(f"undeclared tools in telemetry: {sorted(actual_tools - allowed)}")
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
    }


def _resume_state(
    results_root: Path, manifest_sha256: str
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
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
            "refusing to resume: sealed under a different authorized manifest"
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


def _score_record(episode_root: Path, record: dict[str, Any], condition: str) -> dict[str, Any]:
    events = _load_events(episode_root / "telemetry.jsonl")
    classifier = FrozenSpanClassifier.load(CLASSIFICATION_PATH)
    condition_suffix(condition)
    record["compiled_projection"] = score_episode(
        events,
        record["answers"],
        record["oracle_scores"],
        classifier,
        initial_delivery_bytes=_DELIVERY_CACHE[condition],
    )
    return record


def run_campaign(results_root: Path = RESULTS_ROOT) -> dict[str, Any]:
    if MODEL != "composer-2.5" or MODEL == MODEL_FAST_FORBIDDEN:
        raise LiveInferenceBlocked("scientific participant must be composer-2.5, not fast")
    if RUNTIME_MODEL != MODEL or "fast" in RUNTIME_MODEL:
        raise LiveInferenceBlocked("Cursor CLI adapter model is not composer-2.5")
    if not PARTICIPANT_INFERENCE_AUTHORIZED:
        raise LiveInferenceBlocked(
            f"{CAMPAIGN_ID}: participant inference is not authorized."
        )
    preflight = run_preflight()
    if preflight["status"] != "PASS":
        raise LiveInferenceBlocked(
            "deterministic preflight failed; live inference is blocked: "
            + "; ".join(preflight["errors"])
        )
    manifest, manifest_sha256 = _load_manifest()
    episodes = manifest["stage1"]["episodes"]
    if results_root.exists():
        resumed_episodes, previous = _resume_state(results_root, manifest_sha256)
    else:
        results_root.mkdir(parents=True)
        resumed_episodes, previous = {}, {}
    campaign = {
        "campaign_id": CAMPAIGN_ID,
        "status": "IN_PROGRESS",
        "valid": None,
        "manifest_sha256": manifest_sha256,
        "manifest_path": str(AUTHORIZED_MANIFEST_PATH.resolve()),
        "runtime_binding": runtime_binding(),
        "participant_campaign_calls": 5 * len(resumed_episodes),
        "episodes_completed": [
            resumed_episodes[episode["episode_id"]]
            for episode in episodes
            if episode["episode_id"] in resumed_episodes
        ],
        "started_timestamp_ns": previous.get("started_timestamp_ns", time.time_ns()),
        "retry_policy": "none",
        "within_episode_retry": False,
        "selective_reruns": False,
    }
    if previous:
        campaign["resumed_from"] = {
            "aborted_timestamp_ns": previous.get("aborted_timestamp_ns"),
            "failure_episode": previous.get("failure_episode"),
            "failure_type": previous.get("failure_type"),
            "failure": previous.get("failure"),
            "episodes_already_completed": len(resumed_episodes),
        }
        if previous.get("resumed_from"):
            campaign["resumed_from"]["resumed_from"] = previous["resumed_from"]
    _write(results_root / "campaign_progress.json", campaign)

    for episode in episodes:
        if episode["episode_id"] in resumed_episodes:
            continue
        try:
            current_manifest, current_digest = _load_manifest()
            if current_digest != manifest_sha256 or current_manifest != manifest:
                raise RuntimeError("authorized manifest changed after campaign start")
            episode_root = results_root / episode["episode_id"]
            print(
                f"[compiled-projection] starting {episode['episode_id']} "
                f"block={episode['block']} condition={episode['condition']}",
                flush=True,
            )
            factory = CursorSessionFactory(episode_root, condition=episode["condition"])
            runner = EpisodeRunner(session_factory=factory)
            started = time.time_ns()
            try:
                record = runner.run(
                    arm=episode["arm"],
                    replicate=episode["replicate"],
                    output_root=episode_root,
                    condition=episode["condition"],
                    system_prompt_suffix=condition_suffix(episode["condition"]),
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
                    "block": episode["block"],
                    "condition": episode["condition"],
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
            record = _score_record(episode_root, record, episode["condition"])
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
            print(
                f"[compiled-projection] sealed {episode['episode_id']} "
                f"({len(campaign['episodes_completed'])}/6)",
                flush=True,
            )
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
            "episode_count": 6,
            "participant_turn_count": 30,
        }
    )
    _write(results_root / "campaign_progress.json", campaign)
    from research.taskview_orientation.compiled_projection.report import write_report

    report = write_report(results_root)
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
        "report_sha256": sha256_file(results_root / "campaign_report.json"),
        "sealed_timestamp_ns": time.time_ns(),
        "participant_turn_count": 30,
        "episode_count": 6,
    }
    _write(results_root / "campaign_seal.json", final_seal)
    return {
        "seal": final_seal,
        "report_path": str(results_root / "campaign_report.json"),
        "report": report,
    }
