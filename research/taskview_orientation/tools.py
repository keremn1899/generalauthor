"""Participant-visible native and TaskView tools with raw telemetry."""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any

from taskview import TaskViewError

from research.taskview_orientation.surface import ExperimentTaskViewSurface
from research.taskview_orientation.telemetry import TelemetryRecorder, visible_bytes


class EpisodeTools:
    _GENERATED_CACHE_DIRS = frozenset({"__pycache__", ".pytest_cache", ".mypy_cache"})
    _BINARY_SUFFIXES = frozenset(
        {
            ".pyc", ".pyo", ".so", ".dll", ".dylib", ".a", ".o", ".obj",
            ".class", ".exe", ".bin", ".dat", ".db", ".sqlite", ".sqlite3",
            ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".gz",
            ".tar", ".wasm",
        }
    )

    def __init__(
        self,
        *,
        source_root: Path,
        scratch_root: Path,
        telemetry: TelemetryRecorder,
        taskview: ExperimentTaskViewSurface | None,
    ) -> None:
        self.source_root = source_root.resolve()
        self.scratch_root = scratch_root.resolve()
        self.telemetry = telemetry
        self.taskview = taskview
        self.phase = 0
        self.source_version = "initial"

    def set_phase(self, phase: int) -> None:
        self.phase = phase

    def mark_phase4_source(self) -> None:
        self.source_version = "phase4"

    @staticmethod
    def _safe_relative(path: str) -> Path:
        candidate = Path(path)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise ValueError("path must remain inside the experiment workspace")
        return candidate

    def _source_path(self, path: str) -> Path:
        candidate = (self.source_root / self._safe_relative(path)).resolve()
        if not candidate.is_relative_to(self.source_root) or not candidate.is_file():
            raise FileNotFoundError(path)
        return candidate

    def _line_segments(self, path: str, lines: list[str], first_line: int) -> list[dict[str, Any]]:
        version = (
            self.source_version
            if path == "tests/checkout_contract.py"
            else "initial"
        )
        return [
            {
                "path": path,
                "line": first_line + offset,
                "bytes": len(line.encode("utf-8")),
                "source_version": version,
            }
            for offset, line in enumerate(lines)
        ]

    def read_source(self, path: str, start_line: int = 1, end_line: int = 10_000) -> dict[str, Any]:
        started_ns = time.perf_counter_ns()
        started = self.telemetry.record(
            "TOOL_CALL",
            phase=self.phase,
            tool_name="read_source",
            tool_arguments={"path": path, "start_line": start_line, "end_line": end_line},
        )
        source = self._source_path(path)
        lines = source.read_text(encoding="utf-8").splitlines(keepends=True)
        if start_line < 1 or end_line < start_line:
            raise ValueError("invalid inclusive line range")
        selected = lines[start_line - 1 : min(end_line, len(lines))]
        actual_end = start_line + len(selected) - 1
        result = {
            "path": path,
            "start_line": start_line,
            "end_line": actual_end,
            "content": "".join(selected),
        }
        self.telemetry.record(
            "SOURCE_READ",
            phase=self.phase,
            tool_name="read_source",
            tool_arguments=started["tool_arguments"],
            source_path=path,
            line_range=[start_line, actual_end],
            byte_range=None,
            segments=self._line_segments(path, selected, start_line),
            model_visible_output_bytes=visible_bytes(result),
            wall_time_ms=(time.perf_counter_ns() - started_ns) / 1_000_000,
        )
        return result

    def search_source(self, query: str, scope: str = ".") -> dict[str, Any]:
        started_ns = time.perf_counter_ns()
        arguments = {"query": query, "scope": scope}
        self.telemetry.record(
            "TOOL_CALL",
            phase=self.phase,
            tool_name="search_source",
            tool_arguments=arguments,
        )
        pattern = re.compile(query)
        relative_scope = self._safe_relative(scope)
        root = (self.source_root / relative_scope).resolve()
        if not root.is_relative_to(self.source_root) or not root.exists():
            raise FileNotFoundError(scope)
        files = [root] if root.is_file() else sorted(path for path in root.rglob("*") if path.is_file())
        results = []
        segments = []
        skipped_files: list[str] = []
        for file_path in files:
            relative = file_path.relative_to(self.source_root).as_posix()
            if (
                any(part in self._GENERATED_CACHE_DIRS for part in file_path.relative_to(self.source_root).parts)
                or file_path.suffix.lower() in self._BINARY_SUFFIXES
            ):
                skipped_files.append(relative)
                continue
            try:
                lines = file_path.read_text(encoding="utf-8").splitlines(keepends=True)
            except UnicodeDecodeError:
                skipped_files.append(relative)
                continue
            for index, line in enumerate(lines, start=1):
                if pattern.search(line):
                    text = line.rstrip("\r\n")
                    results.append({"path": relative, "line": index, "text": text})
                    segments.extend(self._line_segments(relative, [line], index))
                    if len(results) == 100:
                        break
            if len(results) == 100:
                break
        response = {"results": results, "result_count": len(results), "truncated": len(results) == 100}
        self.telemetry.record(
            "SOURCE_SEARCH",
            phase=self.phase,
            tool_name="search_source",
            tool_arguments=arguments,
            search_scope=scope,
            search_query=query,
            result_count=len(results),
            truncated=len(results) == 100,
            skipped_file_count=len(skipped_files),
            skipped_files=skipped_files,
            segments=segments,
            model_visible_output_bytes=visible_bytes(response),
            wall_time_ms=(time.perf_counter_ns() - started_ns) / 1_000_000,
        )
        return response

    def write_scratch(self, path: str, content: str) -> dict[str, Any]:
        started_ns = time.perf_counter_ns()
        relative = self._safe_relative(path)
        target = (self.scratch_root / relative).resolve()
        if not target.is_relative_to(self.scratch_root):
            raise ValueError("scratch path escapes scratch root")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        result = {"path": relative.as_posix(), "bytes_written": len(content.encode("utf-8"))}
        self.telemetry.record(
            "SCRATCH_WRITE",
            phase=self.phase,
            tool_name="write_scratch",
            tool_arguments={"path": path, "content_bytes": result["bytes_written"]},
            model_visible_output_bytes=visible_bytes(result),
            wall_time_ms=(time.perf_counter_ns() - started_ns) / 1_000_000,
        )
        return result

    def _taskview_call(self, operation: str, callback, arguments: dict[str, Any]) -> dict[str, Any]:
        if self.taskview is None:
            raise TaskViewError("TaskView tools are unavailable in RAW")
        started_ns = time.perf_counter_ns()
        self.telemetry.record(
            "TOOL_CALL",
            phase=self.phase,
            tool_name=operation,
            tool_arguments=arguments,
        )
        result = callback()
        rows = result.get("row_count")
        if rows is None and isinstance(result.get("rows"), list):
            rows = len(result["rows"])
        self.telemetry.record(
            "TASKVIEW_TOOL",
            phase=self.phase,
            tool_name=operation,
            tool_arguments=arguments,
            taskview_operation=operation,
            taskview_rows_returned=rows,
            model_visible_output_bytes=visible_bytes(result),
            wall_time_ms=(time.perf_counter_ns() - started_ns) / 1_000_000,
        )
        return result

    def describe(
        self,
        *,
        relation: str | None = None,
        why: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._taskview_call(
            "describe",
            lambda: self.taskview.describe(relation=relation, why=why),
            {"relation": relation, "why": why},
        )

    def query_sql(self, sql: str, parameters: tuple[Any, ...] = ()) -> dict[str, Any]:
        return self._taskview_call(
            "query_sql",
            lambda: self.taskview.query_sql(sql, parameters),
            {"sql": sql, "parameters": list(parameters)},
        )

    def assertion(
        self,
        *,
        action: str,
        relation: str,
        values: dict[str, Any],
        grounding: tuple[dict[str, Any], ...] = (),
    ) -> dict[str, Any]:
        if self.phase == 5 and action.upper() == "ASSERT" and relation == "verified_by":
            raise TaskViewError(
                "Phase 5 proposed verification is answer-only and cannot mutate retained state"
            )
        return self._taskview_call(
            "assertion",
            lambda: self.taskview.assertion(
                action=action,
                relation=relation,
                values=values,
                grounding=grounding,
            ),
            {"action": action, "relation": relation, "values": values},
        )

    def rerun(self, relation: str, **attempted_contract: Any) -> dict[str, Any]:
        return self._taskview_call(
            "rerun",
            lambda: self.taskview.rerun(relation, **attempted_contract),
            {"relation": relation, **attempted_contract},
        )
