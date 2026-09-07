"""Reconstructible source helpers. Not World semantics. No persistent Source IR."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from research.semantic_integration.core.source import AssertionGrounding, SourceObservation

_STRUCTURED = {".csv", ".json"}


def looks_numeric(value: Any) -> bool:
    text = str(value or "").strip().replace(",", "")
    if not text:
        return False
    try:
        float(text)
        return True
    except ValueError:
        return False


class Source:
    def __init__(self, root: str | Path = "sources") -> None:
        self.root = Path(root)

    def tables(self) -> list[str]:
        if not self.root.exists():
            return []
        return [
            path.name
            for path in sorted(self.root.iterdir())
            if path.suffix.lower() in _STRUCTURED
        ]

    def _load(self, table: str) -> list[dict[str, Any]]:
        path = self.root / table
        if not path.exists():
            raise FileNotFoundError(table)
        if path.suffix.lower() == ".json":
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, list):
                return [row if isinstance(row, dict) else {"value": row} for row in payload]
            if isinstance(payload, dict):
                return [payload]
            return []
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def rows(self, table: str) -> list[dict[str, Any]]:
        return self._load(table)

    def fields(self, table: str) -> list[str]:
        rows = self._load(table)
        if not rows:
            return []
        return list(rows[0].keys())

    def profile(self, table: str, field: str) -> dict[str, Any]:
        rows = self._load(table)
        values = ["" if row.get(field) is None else str(row.get(field)) for row in rows]
        nonempty = [value for value in values if value.strip()]
        return {
            "table": table,
            "field": field,
            "n": len(values),
            "n_empty": len(values) - len(nonempty),
            "n_distinct": len(set(nonempty)),
            "n_numeric": sum(1 for value in nonempty if looks_numeric(value)),
            "sample_distinct": sorted(set(nonempty), key=lambda item: (len(item), item))[:25],
        }

    def distinct_values(self, table: str, field: str, limit: int = 50) -> list[dict[str, Any]]:
        counts: Counter[str] = Counter()
        for row in self._load(table):
            counts[str(row.get(field) or "")] += 1
        return [{"value": value, "n": n} for value, n in counts.most_common(limit)]

    def join(self, left: str, right: str, on: list[tuple[str, str]]) -> list[dict[str, Any]]:
        index: dict[tuple, list[dict[str, Any]]] = defaultdict(list)
        for row in self._load(right):
            key = tuple(str(row.get(right_field) or "") for _, right_field in on)
            index[key].append(row)
        out: list[dict[str, Any]] = []
        for left_row in self._load(left):
            key = tuple(str(left_row.get(left_field) or "") for left_field, _ in on)
            for right_row in index.get(key, []):
                merged = {f"l.{key_}": value for key_, value in left_row.items()}
                merged.update({f"r.{key_}": value for key_, value in right_row.items()})
                out.append(merged)
        return out

    def read_text(self, name: str) -> str:
        return (self.root / name).read_text(encoding="utf-8")

    def file_hash(self, name: str) -> str:
        return hashlib.sha256((self.root / name).read_bytes()).hexdigest()

    def observation(self, table: str, location: str) -> SourceObservation:
        return SourceObservation(
            provider="file",
            native_handle=table,
            source_revision=self.file_hash(table),
            native_location=location,
        )

    def grounding(
        self,
        table: str,
        location: str,
        *,
        method: str = "",
        extra: dict[str, Any] | None = None,
    ) -> AssertionGrounding:
        return AssertionGrounding(
            observations=(self.observation(table, location),),
            construction_method=method,
            extra=extra,
        )
