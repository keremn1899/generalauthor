"""Boring structural source helpers. No domain meaning. Seeded into participant workspaces."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

_DATE_FMTS = ("%m/%d/%Y", "%Y-%m-%d", "%m/%d/%y")


def parse_date(value: Any) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    for fmt in _DATE_FMTS:
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def interval_contains(point: Any, begin: Any, end: Any) -> bool:
    p, b, e = parse_date(point), parse_date(begin), parse_date(end)
    if p is None or b is None or e is None:
        return False
    return b <= p <= e


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
    def __init__(self, root: str | Path = "sources"):
        self.root = Path(root)

    def tables(self) -> list[str]:
        names = []
        if not self.root.exists():
            return names
        for path in sorted(self.root.iterdir()):
            if path.suffix.lower() in {".csv", ".json"}:
                names.append(path.name)
        return names

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
        with path.open(encoding="utf-8", newline="") as fh:
            return list(csv.DictReader(fh))

    def rows(self, table: str) -> list[dict[str, Any]]:
        return self._load(table)

    def fields(self, table: str) -> list[str]:
        rows = self._load(table)
        if not rows:
            return []
        return list(rows[0].keys())

    def n_rows(self, table: str) -> int:
        return len(self._load(table))

    def profile(self, table: str, field: str) -> dict[str, Any]:
        rows = self._load(table)
        values = ["" if row.get(field) is None else str(row.get(field)) for row in rows]
        nonempty = [v for v in values if v.strip()]
        distinct = sorted(set(nonempty), key=lambda x: (len(x), x))
        numeric_n = sum(1 for v in nonempty if looks_numeric(v))
        date_n = sum(1 for v in nonempty if parse_date(v))
        return {
            "table": table,
            "field": field,
            "n": len(values),
            "n_empty": len(values) - len(nonempty),
            "n_distinct": len(set(nonempty)),
            "n_numeric": numeric_n,
            "n_parseable_date": date_n,
            "min_len": min((len(v) for v in nonempty), default=0),
            "max_len": max((len(v) for v in nonempty), default=0),
            "sample_distinct": distinct[:25],
        }

    def distinct_values(self, table: str, field: str, limit: int = 50) -> list[dict[str, Any]]:
        rows = self._load(table)
        counts: Counter[str] = Counter()
        for row in rows:
            counts[str(row.get(field) or "")] += 1
        out = [{"value": value, "n": n} for value, n in counts.most_common(limit)]
        return out

    def key_candidates(self, table: str, max_combo: int = 3) -> list[dict[str, Any]]:
        rows = self._load(table)
        fields = self.fields(table)
        n = len(rows)
        singles = []
        for field in fields:
            values = [str(row.get(field) or "") for row in rows]
            n_distinct = len(set(values))
            n_empty = sum(1 for v in values if not v.strip())
            singles.append(
                {
                    "fields": [field],
                    "n_distinct": n_distinct,
                    "n_empty": n_empty,
                    "unique": n_distinct == n and n_empty == 0,
                }
            )
        singles.sort(key=lambda row: (-int(row["unique"]), -row["n_distinct"], row["fields"][0]))
        return singles[:20]

    def value_overlap(self, left: tuple[str, str], right: tuple[str, str]) -> dict[str, Any]:
        left_vals = {str(row.get(left[1]) or "") for row in self._load(left[0])}
        right_vals = {str(row.get(right[1]) or "") for row in self._load(right[0])}
        left_vals.discard("")
        right_vals.discard("")
        inter = left_vals & right_vals
        return {
            "left": {"table": left[0], "field": left[1], "n_distinct": len(left_vals)},
            "right": {"table": right[0], "field": right[1], "n_distinct": len(right_vals)},
            "n_overlap": len(inter),
            "overlap_sample": sorted(inter)[:20],
        }

    def join(self, left: str, right: str, on: list[tuple[str, str]]) -> list[dict[str, Any]]:
        left_rows = self._load(left)
        right_rows = self._load(right)
        index: dict[tuple, list[dict[str, Any]]] = defaultdict(list)
        for row in right_rows:
            key = tuple(str(row.get(r) or "") for _, r in on)
            index[key].append(row)
        out = []
        for lrow in left_rows:
            key = tuple(str(lrow.get(l) or "") for l, _ in on)
            for rrow in index.get(key, []):
                merged = {f"l.{k}": v for k, v in lrow.items()}
                merged.update({f"r.{k}": v for k, v in rrow.items()})
                out.append(merged)
        return out

    def join_profile(self, left: str, right: str, on: list[tuple[str, str]]) -> dict[str, Any]:
        left_rows = self._load(left)
        right_rows = self._load(right)
        index: dict[tuple, int] = Counter()
        for row in right_rows:
            key = tuple(str(row.get(r) or "") for _, r in on)
            index[key] += 1
        matches = []
        unmatched_left = 0
        for lrow in left_rows:
            key = tuple(str(lrow.get(l) or "") for l, _ in on)
            n = index.get(key, 0)
            if n == 0:
                unmatched_left += 1
            matches.append(n)
        joined = sum(matches)
        return {
            "left": left,
            "right": right,
            "on": on,
            "left_rows": len(left_rows),
            "right_rows": len(right_rows),
            "joined_rows": joined,
            "left_unmatched": unmatched_left,
            "n_left_with_gt1": sum(1 for n in matches if n > 1),
            "max_matches_per_left": max(matches) if matches else 0,
        }

    def document_inventory(self) -> list[dict[str, Any]]:
        return self._load("document_inventory.json")
