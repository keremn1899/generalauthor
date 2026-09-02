from __future__ import annotations

import json

import pytest

from research.taskview_orientation.freeze import sha256_file
from research.taskview_orientation.read_surface_replay import SEALED_RESULTS_ROOT
from research.taskview_orientation.trajectory_export import EXPORT_ROOT
from research.taskview_orientation.trajectory_export.export import run


@pytest.mark.requires_path(
    "research/taskview_orientation/results/stage1-cursor-v01-v4-searchfix/campaign_seal.json"
)
def test_verbatim_export_integrity_and_sealed_sources():
    receipt = run()
    assert receipt["participant_inference_calls"] == 0
    assert receipt["integrity_all_pass"] is True
    assert set(receipt["export_hashes"]) == {
        "raw-r2.txt",
        "taskview-r2.txt",
        "raw-r4.txt",
        "taskview-r4.txt",
    }
    seal = json.loads((SEALED_RESULTS_ROOT / "campaign_seal.json").read_text(encoding="utf-8"))
    assert sha256_file(SEALED_RESULTS_ROOT / "campaign_progress.json") == seal[
        "campaign_progress_sha256"
    ]
    for episode_id, expected in seal["episode_seals"].items():
        assert sha256_file(SEALED_RESULTS_ROOT / episode_id / "seal.json") == expected
    for filename, checks in receipt["integrity_check_results"].items():
        assert checks["event_ordering_preserved"] is True
        assert checks["logical_tool_call_count_preserved"] is True
        assert checks["model_visible_tool_result_bytes_preserved"] is True
        assert checks["phase_boundaries_preserved"] is True
        assert checks["final_answers_byte_text_equivalent"] is True
        text = (EXPORT_ROOT / filename).read_text(encoding="utf-8")
        assert "=== FROZEN PHASE-4 MUTATION APPLIED ===" in text
        assert "[141 bytes]" not in text
        assert "[2 rows]" not in text
        assert "[successful]" not in text
        assert text.count("PHASE 1") == 1
        assert text.count("PHASE 5") == 1
        assert text.count("[PARTICIPANT ANSWER]") == 5
    taskview = (EXPORT_ROOT / "taskview-r2.txt").read_text(encoding="utf-8")
    assert "[TOOL CALL: describe]" in taskview
    assert "[TOOL CALL: query_sql]" in taskview
    assert "SELECT *" in taskview
    assert '"roles"' in taskview
    raw = (EXPORT_ROOT / "raw-r2.txt").read_text(encoding="utf-8")
    assert "[TOOL CALL: read_source]" in raw
    assert "[TOOL CALL: search_source]" in raw
    assert "[TOOL CALL: describe]" not in raw
