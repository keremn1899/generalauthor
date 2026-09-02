"""Mechanical validation and fail-closed runner for frozen C2 packets."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from research.taskview_bom_scaling import (
    SEMANTIC_FRONTIER_INFERENCE_AUTHORIZED,
)


class LiveInferenceBlocked(RuntimeError):
    """C2 inference was attempted without explicit authorization."""


ROOT = Path(__file__).resolve().parent


def participant_request(packet: Mapping[str, Any]) -> dict[str, Any]:
    """Build the exact model-visible request without an oracle disposition."""

    validate_packet(packet)
    return {
        "protocol": json.loads((ROOT / "protocol.json").read_text(encoding="utf-8")),
        "packet_schema": json.loads(
            (ROOT / "packet_schema.json").read_text(encoding="utf-8")
        ),
        "output_schema": json.loads(
            (ROOT / "output_schema.json").read_text(encoding="utf-8")
        ),
        "packet": dict(packet),
    }


def validate_packet(packet: Mapping[str, Any]) -> None:
    required = {
        "candidate_assertion",
        "relevant_referents",
        "known_mechanical_facts",
        "evidence",
        "conflicts",
        "missing_information",
    }
    if set(packet) != required:
        raise ValueError("packet fields differ from the frozen packet schema")
    assertion = packet["candidate_assertion"]
    if set(assertion) != {"relation", "tuple"}:
        raise ValueError("candidate assertion fields are invalid")
    if assertion["relation"] != "acceptable_replacement":
        raise ValueError("C2 adjudicates only acceptable_replacement")
    if len(assertion["tuple"]) != 3:
        raise ValueError("acceptable_replacement requires three roles")
    if list(packet["relevant_referents"]) != list(assertion["tuple"]):
        raise ValueError("packet referents differ from candidate assertion roles")
    if not packet["evidence"]:
        raise ValueError("packet must contain selected evidence")
    for evidence in packet["evidence"]:
        if set(evidence) != {
            "source",
            "source_fingerprint",
            "native_location",
            "record",
        }:
            raise ValueError("evidence fields differ from the frozen packet schema")
        fingerprint = evidence["source_fingerprint"]
        if (
            not isinstance(fingerprint, str)
            or not fingerprint.startswith("sha256:")
            or len(fingerprint) != 71
        ):
            raise ValueError("evidence fingerprint is invalid")


def validate_output(
    result: Mapping[str, Any],
    packet: Mapping[str, Any],
) -> dict[str, Any]:
    validate_packet(packet)
    if set(result) != {"decision", "grounds", "reason"}:
        raise ValueError("result fields differ from the frozen output schema")
    if result["decision"] not in {"ACCEPT", "REJECT", "UNRESOLVED"}:
        raise ValueError("decision is outside the frozen enum")
    if not isinstance(result["reason"], str) or not result["reason"].strip():
        raise ValueError("reason must be a non-empty string")
    if len(result["reason"]) > 1000:
        raise ValueError("reason exceeds the frozen limit")
    available = {
        (item["source"], item["native_location"]) for item in packet["evidence"]
    }
    grounds = result["grounds"]
    if not isinstance(grounds, list) or not grounds:
        raise ValueError("at least one ground is required")
    for ground in grounds:
        if set(ground) != {"source", "record_or_span"}:
            raise ValueError("ground fields differ from the frozen output schema")
        if (ground["source"], ground["record_or_span"]) not in available:
            raise ValueError("ground does not resolve to supplied packet evidence")
    return dict(result)


def run_c2(
    provider: Callable[[dict[str, Any]], Mapping[str, Any]],
    packet: dict[str, Any],
) -> dict[str, Any]:
    """Invoke an injected provider only after the repository flag is authorized."""

    if not SEMANTIC_FRONTIER_INFERENCE_AUTHORIZED:
        raise LiveInferenceBlocked(
            "SEMANTIC_FRONTIER_INFERENCE_AUTHORIZED is False"
        )
    request = participant_request(packet)
    return validate_output(provider(request), packet)
