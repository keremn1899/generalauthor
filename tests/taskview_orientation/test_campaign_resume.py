"""Unit tests for campaign.py's same-manifest resume path.

These exercise _resume_state directly rather than run_campaign end to end,
since run_campaign always drives the real Cursor SDK adapter (DefaultSessionFactory)
and has no scripted/no-model seam. _resume_state is the piece with actual
correctness risk (hash verification, stray-episode cleanup, provenance
carryover); the rest of run_campaign's wiring around it is straightforward.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from research.taskview_orientation.campaign import _file_hashes, _resume_state
from research.taskview_orientation.freeze import sha256_file


MANIFEST_SHA = "a" * 64


def _seal_episode(episode_root: Path, *, episode_id: str, manifest_sha256: str) -> str:
    episode_root.mkdir(parents=True)
    (episode_root / "record.json").write_text('{"ok": true}\n', encoding="utf-8")
    file_hashes = _file_hashes(episode_root, exclude={"seal.json"})
    seal = {
        "campaign_episode_id": episode_id,
        "manifest_sha256": manifest_sha256,
        "file_hashes": file_hashes,
    }
    seal_path = episode_root / "seal.json"
    seal_path.write_text(json.dumps(seal, sort_keys=True), encoding="utf-8")
    return sha256_file(seal_path)


def _write_invalid(
    results_root: Path,
    *,
    manifest_sha256: str,
    episodes_completed: list[dict],
    failure_episode: dict,
) -> None:
    invalid = {
        "status": "PILOT_ABORTED",
        "valid": False,
        "manifest_sha256": manifest_sha256,
        "episodes_completed": episodes_completed,
        "failure_episode": failure_episode,
        "failure_type": "CursorRuntimeError",
        "failure": "example failure",
    }
    (results_root / "campaign_invalid.json").write_text(json.dumps(invalid), encoding="utf-8")


def test_resume_recovers_sealed_episodes_and_clears_the_stray_failure_dir(tmp_path):
    results_root = tmp_path / "campaign"
    results_root.mkdir()
    seal_sha = _seal_episode(
        results_root / "e01", episode_id="e01", manifest_sha256=MANIFEST_SHA
    )
    (results_root / "e02").mkdir()
    (results_root / "e02" / "partial.txt").write_text("incomplete", encoding="utf-8")
    _write_invalid(
        results_root,
        manifest_sha256=MANIFEST_SHA,
        episodes_completed=[{"episode_id": "e01", "episode_seal_sha256": seal_sha}],
        failure_episode={"episode_id": "e02"},
    )

    resumed, previous = _resume_state(results_root, MANIFEST_SHA)

    assert set(resumed) == {"e01"}
    assert previous["failure_episode"] == {"episode_id": "e02"}
    assert not (results_root / "e02").exists()
    assert not (results_root / "campaign_invalid.json").exists()


def test_resume_refuses_a_different_manifest(tmp_path):
    results_root = tmp_path / "campaign"
    results_root.mkdir()
    _write_invalid(
        results_root,
        manifest_sha256=MANIFEST_SHA,
        episodes_completed=[],
        failure_episode={"episode_id": "e01"},
    )
    with pytest.raises(RuntimeError, match="different authorized manifest"):
        _resume_state(results_root, "b" * 64)
    # Refusing to resume must not destroy the evidence of the aborted attempt.
    assert (results_root / "campaign_invalid.json").exists()


def test_resume_refuses_an_unrecognized_directory(tmp_path):
    results_root = tmp_path / "campaign"
    results_root.mkdir()
    (results_root / "unrelated.txt").write_text("hello", encoding="utf-8")
    with pytest.raises(FileExistsError, match="recognizable aborted-attempt marker"):
        _resume_state(results_root, MANIFEST_SHA)


def test_resume_refuses_a_drifted_seal(tmp_path):
    results_root = tmp_path / "campaign"
    results_root.mkdir()
    _seal_episode(results_root / "e01", episode_id="e01", manifest_sha256=MANIFEST_SHA)
    # Tamper with a sealed episode file after the fact.
    (results_root / "e01" / "record.json").write_text('{"ok": false}\n', encoding="utf-8")
    real_seal_sha = sha256_file(results_root / "e01" / "seal.json")
    _write_invalid(
        results_root,
        manifest_sha256=MANIFEST_SHA,
        episodes_completed=[{"episode_id": "e01", "episode_seal_sha256": real_seal_sha}],
        failure_episode={"episode_id": "e02"},
    )
    with pytest.raises(RuntimeError, match="file contents drifted"):
        _resume_state(results_root, MANIFEST_SHA)
