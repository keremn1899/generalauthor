"""Mechanical source-content grounding receipts.  No semantic reinterpretation."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any


SOURCE_REFERENCE_RE = re.compile(
    r"^source://(?P<path>[^#]+)#L(?P<start>\d+)-L(?P<end>\d+)"
    r"(?:@sha256:(?P<digest>[0-9a-fA-F]+))?$"
)

FRESH = "FRESH"
CHANGED = "CHANGED"
UNKNOWN = "UNKNOWN"
FRESHNESS_KEYS = frozenset(
    {"grounding_state", "content_digest_at_grounding_time", "current_source_digest"}
)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def parse_source_reference(reference: str) -> dict[str, Any] | None:
    match = SOURCE_REFERENCE_RE.match(str(reference or ""))
    if match is None:
        return None
    return {
        "path": match.group("path"),
        "start_line": int(match.group("start")),
        "end_line": int(match.group("end")),
        "content_digest_at_grounding_time": (
            match.group("digest").lower() if match.group("digest") else None
        ),
    }


def receipt_for_reference(reference: str, source_root: Path) -> dict[str, Any]:
    parsed = parse_source_reference(reference)
    if parsed is None:
        return {
            "source_reference": reference,
            "content_digest_at_grounding_time": None,
            "current_source_digest": None,
            "grounding_state": UNKNOWN,
        }
    path = source_root / parsed["path"]
    current = sha256_file(path) if path.is_file() else None
    grounded = parsed["content_digest_at_grounding_time"]
    if grounded is None or current is None:
        state = UNKNOWN
    elif grounded == current:
        state = FRESH
    else:
        state = CHANGED
    return {
        "source_reference": reference,
        "content_digest_at_grounding_time": grounded,
        "current_source_digest": current,
        "grounding_state": state,
    }


def aggregate_state(states: list[str]) -> str:
    if any(state == CHANGED for state in states):
        return CHANGED
    if not states or any(state == UNKNOWN for state in states):
        return UNKNOWN
    return FRESH


def annotate_groundings(
    groundings: list[dict[str, Any]], source_root: Path
) -> tuple[list[dict[str, Any]], str]:
    annotated: list[dict[str, Any]] = []
    states: list[str] = []
    for item in groundings:
        reference = item.get("reference")
        if not isinstance(reference, str):
            receipt = {
                "source_reference": reference,
                "content_digest_at_grounding_time": None,
                "current_source_digest": None,
                "grounding_state": UNKNOWN,
            }
        else:
            receipt = receipt_for_reference(reference, source_root)
        annotated.append({**item, **receipt})
        states.append(str(receipt["grounding_state"]))
    return annotated, aggregate_state(states)


def payload_has_freshness_fields(payload: Any) -> bool:
    if isinstance(payload, dict):
        if FRESHNESS_KEYS & set(payload):
            return True
        return any(payload_has_freshness_fields(value) for value in payload.values())
    if isinstance(payload, list):
        return any(payload_has_freshness_fields(item) for item in payload)
    return False
