"""Canonical output helpers.  Comparable payload only; no provenance sidecar."""

from __future__ import annotations

import json
from typing import Any


def dump(document: dict[str, Any]) -> str:
    return json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def fingerprint_cases(document: dict[str, Any]) -> list[dict[str, Any]]:
    return document["cases"] if "cases" in document else document.get("conflicts", [])
