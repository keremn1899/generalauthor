"""R3: does cited evidence license the proposed disposition under the relation contract?

Generic. No fixture entity names. Does not search sources. Does not modify the candidate.
"""

from __future__ import annotations

import re
from typing import Any

# Establishing identity, not mere compatibility.
_SAME_CUES = (
    "same legal entity",
    "the same legal entity",
    "is the same entity",
    "are the same",
    "that is the same",
    "same company",
    "did not change",
    "number did not change",
)

_DISTINCT_CUES = (
    "different company",
    "a different company",
    "is a different",
    "are distinct",
    "not the same",
    "has no current",
)

_UNRESOLVED_PRESERVE_CUES = (
    "has not determined",
    "have not determined",
    "has not been determined",
    "cannot be established",
    "cannot determine",
    "treat that registry link as unresolved",
    "treat as unresolved",
    "remain unresolved",
    "multiple live candidates",
)


def _blob(packet: dict[str, Any], claim: str) -> str:
    parts = [claim or ""]
    for obs in packet.get("selected_observations") or []:
        if isinstance(obs, dict):
            parts.append(str(obs.get("excerpt") or ""))
            parts.append(str(obs.get("location") or ""))
        else:
            parts.append(str(obs))
    parts.append(str(packet.get("selection_rationale") or ""))
    parts.append(json_dumps_packet(packet))
    return " ".join(parts).lower()


def json_dumps_packet(packet: dict[str, Any]) -> str:
    import json

    return json.dumps(packet, default=str).lower()


def _mentions_registry(left: str, right: str) -> bool:
    return "registry:" in f"{left} {right}"


def verify_identity_disposition(
    *,
    left: str,
    right: str,
    proposed: str,
    packet: dict[str, Any],
    support_claim: str,
) -> dict[str, Any]:
    text = _blob(packet, support_claim)
    proposed = (proposed or "UNRESOLVED").upper()
    if proposed not in {"SAME_ENTITY", "DISTINCT", "UNRESOLVED"}:
        return {
            "result": "NOT_SUPPORTED",
            "reason": "disposition not in identity contract",
        }
    if proposed == "UNRESOLVED":
        return {"result": "SUPPORTED", "reason": "unresolved is always licensed"}

    preserves = any(cue in text for cue in _UNRESOLVED_PRESERVE_CUES)
    if preserves and _mentions_registry(left, right) and proposed in {"SAME_ENTITY", "DISTINCT"}:
        return {
            "result": "NOT_SUPPORTED",
            "reason": "packet preserves unresolved registry identity; closure not licensed",
        }

    if proposed == "SAME_ENTITY":
        if any(cue in text for cue in _SAME_CUES):
            return {"result": "SUPPORTED", "reason": "packet contains identity-establishing language"}
        return {
            "result": "NOT_SUPPORTED",
            "reason": "compatibility or absence of contradiction does not license SAME_ENTITY",
        }
    if any(cue in text for cue in _DISTINCT_CUES):
        return {"result": "SUPPORTED", "reason": "packet contains distinctness-establishing language"}
    return {
        "result": "NOT_SUPPORTED",
        "reason": "absence of identity evidence does not license DISTINCT",
    }


def admit(proposed: str, verification: dict[str, Any], unresolved: str = "UNRESOLVED") -> str:
    if verification.get("result") == "SUPPORTED":
        return proposed
    return unresolved
