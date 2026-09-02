"""Runtime trace of raw fixture-source reads by analysis code."""

from __future__ import annotations

import builtins
from collections.abc import Callable
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from research.taskview_bom.experiment import FIXTURES, SOURCE_NAMES


class SourceAccessLog:
    def __init__(self) -> None:
        self._seen: set[str] = set()
        self.files: list[str] = []
        self.bytes_by_file: dict[str, int] = {}

    @property
    def file_count(self) -> int:
        return len(self.files)

    @property
    def bytes_consumed(self) -> int:
        return sum(self.bytes_by_file.values())

    def record(self, path: Path | str) -> None:
        candidate = Path(path)
        name = candidate.name
        if name not in SOURCE_NAMES:
            return
        try:
            resolved = str(candidate.resolve())
        except OSError:
            resolved = str(candidate)
        if resolved in self._seen:
            return
        self._seen.add(resolved)
        self.files.append(name)
        try:
            size = candidate.stat().st_size
        except OSError:
            size = 0
        self.bytes_by_file[name] = size


@contextmanager
def trace_source_access(
    fixture_dir: Path = FIXTURES,
) -> Iterator[SourceAccessLog]:
    log = SourceAccessLog()
    original_open = builtins.open
    original_path_open = Path.open

    def tracked_open(file: Any, *args: Any, **kwargs: Any):
        if not isinstance(file, int):
            log.record(file)
        return original_open(file, *args, **kwargs)

    def tracked_path_open(self, *args: Any, **kwargs: Any):
        log.record(self)
        return original_path_open(self, *args, **kwargs)

    builtins.open = tracked_open  # type: ignore[assignment]
    Path.open = tracked_path_open  # type: ignore[method-assign]
    try:
        yield log
    finally:
        builtins.open = original_open
        Path.open = original_path_open


def analysis_opened_sources(
    func: Callable[..., Any], *args: Any, **kwargs: Any
) -> tuple[Any, SourceAccessLog]:
    with trace_source_access() as log:
        result = func(*args, **kwargs)
    return result, log
