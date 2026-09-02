"""Pair helpers and hidden-oracle matching. Evaluator-only after ordinary runs."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from research.semantic_integration.domains.diligence.evaluator import load_json

DILIGENCE = Path(__file__).resolve().parent.parent
HIDDEN = DILIGENCE / "hidden"

ID_RE = re.compile(
    r"(crm:[A-Za-z0-9-]+|billing:[^\"'\s,]+|registry:[A-Za-z0-9 -]+|contract:[A-Za-z0-9-]+)"
)


def canon_id(value: str) -> str:
    text = value.strip()
    text = text.replace("billing:billing:", "billing:")
    return text


def pair_key(left: str, right: str) -> tuple[str, str]:
    a, b = canon_id(left), canon_id(right)
    return (a, b) if a <= b else (b, a)


def oracle_identity() -> dict[str, set[tuple[str, str]]]:
    payload = json.loads((HIDDEN / "annotations" / "identity_dispositions.json").read_text())
    out: dict[str, set[tuple[str, str]]] = {
        "SAME_ENTITY": set(),
        "DISTINCT": set(),
        "UNRESOLVED": set(),
    }
    mapping = {
        "SAME_ENTITY": "same_entity",
        "DISTINCT": "distinct",
        "UNRESOLVED": "unresolved",
    }
    for kind, key in mapping.items():
        for left, right in payload[key]:
            out[kind].add(pair_key(left, right))
    return out


def all_oracle_pairs() -> dict[tuple[str, str], str]:
    result: dict[tuple[str, str], str] = {}
    for kind, pairs in oracle_identity().items():
        for pair in pairs:
            result[pair] = kind
    return result


def extract_ids_from_obj(obj: Any) -> list[str]:
    found: list[str] = []
    if isinstance(obj, dict):
        for key in ("left", "right", "left_id", "right_id"):
            val = obj.get(key)
            if isinstance(val, str) and ":" in val:
                found.append(val)
        values = obj.get("values")
        if isinstance(values, dict):
            found.extend(extract_ids_from_obj(values))
        blob = json.dumps(obj)
        found.extend(ID_RE.findall(blob))
    elif isinstance(obj, str):
        found.extend(ID_RE.findall(obj))
    return [canon_id(item) for item in found]


def pair_from_obj(obj: Any) -> tuple[str, str] | None:
    ids = []
    seen: set[str] = set()
    for item in extract_ids_from_obj(obj):
        if item not in seen:
            seen.add(item)
            ids.append(item)
    if len(ids) >= 2:
        return pair_key(ids[0], ids[1])
    return None


def load_obligations(path: Path) -> list[dict[str, Any]]:
    payload = load_json(path)
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict) and isinstance(payload.get("obligations"), list):
        return payload["obligations"]
    return []


def load_dispositions(path: Path) -> list[dict[str, Any]]:
    payload = load_json(path)
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict) and isinstance(payload.get("dispositions"), list):
        return payload["dispositions"]
    return []
