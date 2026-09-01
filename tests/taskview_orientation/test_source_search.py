from __future__ import annotations

import re
from pathlib import Path

import pytest

from research.taskview_orientation.telemetry import TelemetryRecorder
from research.taskview_orientation.tools import EpisodeTools


def _tools(source: Path) -> tuple[EpisodeTools, TelemetryRecorder]:
    telemetry = TelemetryRecorder(episode_id="search-regression", arm="TASKVIEW", replicate=0)
    tools = EpisodeTools(
        source_root=source,
        scratch_root=source.parent / "scratch",
        telemetry=telemetry,
        taskview=None,
    )
    tools.set_phase(1)
    return tools, telemetry


def _search_event(telemetry: TelemetryRecorder) -> dict:
    return next(event for event in telemetry.events if event["event_type"] == "SOURCE_SEARCH")


def test_search_skips_pyc_next_to_valid_source(tmp_path: Path):
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "x.pyc").write_bytes(b"\xf3\x00\xff")
    (tmp_path / "target.py").write_text("needle = True\n", encoding="utf-8")
    tools, telemetry = _tools(tmp_path)

    result = tools.search_source("needle", ".")

    assert result["results"][0]["path"] == "target.py"
    assert _search_event(telemetry)["skipped_file_count"] == 1


def test_search_skips_binary_before_matching_text(tmp_path: Path):
    (tmp_path / "a.bin").write_bytes(b"\x00\xff\x00")
    (tmp_path / "z.txt").write_text("needle\n", encoding="utf-8")
    tools, telemetry = _tools(tmp_path)

    result = tools.search_source("needle", ".")

    assert result["result_count"] == 1
    assert result["results"][0]["path"] == "z.txt"
    assert _search_event(telemetry)["skipped_file_count"] == 1


def test_search_skips_binary_after_matching_text(tmp_path: Path):
    (tmp_path / "a.txt").write_text("needle\n", encoding="utf-8")
    (tmp_path / "z.dat").write_bytes(b"\x00\xff")
    tools, telemetry = _tools(tmp_path)

    result = tools.search_source("needle", ".")

    assert result["result_count"] == 1
    assert result["results"][0]["path"] == "a.txt"
    assert _search_event(telemetry)["skipped_file_count"] == 1


def test_search_skips_multiple_binary_and_generated_files(tmp_path: Path):
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "x.pyc").write_bytes(b"cache")
    (tmp_path / "one.pyc").write_bytes(b"cache")
    (tmp_path / "two.bin").write_bytes(b"\x80\x81")
    (tmp_path / "target.md").write_text("needle\n", encoding="utf-8")
    tools, telemetry = _tools(tmp_path)

    result = tools.search_source("needle", ".")

    assert result["result_count"] == 1
    assert _search_event(telemetry)["skipped_file_count"] == 3


def test_search_skips_undecodable_non_pyc_file(tmp_path: Path):
    (tmp_path / "opaque.txt").write_bytes(b"\xff\xfe")
    (tmp_path / "target.txt").write_text("needle\n", encoding="utf-8")
    tools, telemetry = _tools(tmp_path)

    result = tools.search_source("needle", ".")

    assert result["result_count"] == 1
    assert _search_event(telemetry)["skipped_file_count"] == 1


def test_malformed_regex_remains_error(tmp_path: Path):
    tools, _ = _tools(tmp_path)

    with pytest.raises(re.error, match="unterminated|missing"):
        tools.search_source("decode(", ".")


def test_invalid_scope_remains_error(tmp_path: Path):
    tools, _ = _tools(tmp_path)

    with pytest.raises(FileNotFoundError):
        tools.search_source("needle", "missing")
