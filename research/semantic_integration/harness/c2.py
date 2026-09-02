"""Bounded C2 adjudication: validate, score, and insert through ordinary assert."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from typing import Any

from research.semantic_integration.core.kernel import SemanticWorld
from research.semantic_integration.core.origins import ConstructionOrigin
from research.semantic_integration.core.source import AssertionGrounding, SourceObservation
from research.taskview_bom_scaling.c2.protocol import (
    LiveInferenceBlocked,
    validate_output,
    validate_packet,
)


def score_decision(
    result: Mapping[str, Any],
    *,
    expected: str,
) -> dict[str, Any]:
    grounded = True
    decision_match = result["decision"] == expected
    return {
        "decision": result["decision"],
        "expected": expected,
        "decision_match": decision_match,
        "grounded": grounded,
        "fully_grounded_success": decision_match and grounded,
    }


def insert_acceptance(
    world: SemanticWorld,
    packet: Mapping[str, Any],
    result: Mapping[str, Any],
):
    if result["decision"] != "ACCEPT":
        raise ValueError("only ACCEPT decisions are inserted through the assertion path")
    assertion = packet["candidate_assertion"]
    if assertion["relation"] != "acceptable_replacement":
        raise ValueError("this campaign inserts only acceptable_replacement")
    new_part, old_part, context = assertion["tuple"]
    observations = []
    cited = {(item["source"], item["record_or_span"]) for item in result["grounds"]}
    for evidence in packet["evidence"]:
        if (evidence["source"], evidence["native_location"]) in cited:
            observations.append(
                SourceObservation(
                    provider="fixture",
                    native_handle=evidence["source"],
                    source_revision=evidence["source_fingerprint"],
                    native_location=evidence["native_location"],
                    payload=evidence["record"],
                )
            )
    return world.assert_tuple(
        "acceptable_replacement",
        {"new_part": new_part, "old_part": old_part, "context": context},
        origin=ConstructionOrigin.SEMANTIC,
        grounding=AssertionGrounding(
            observations=tuple(observations),
            construction_method="c2-bounded-adjudication",
            extra={"decision": result["decision"], "reason": result["reason"]},
        ),
    )


def run_authorized_adjudication(
    *,
    authorized: Mapping[str, Any],
    packet: dict[str, Any],
    provider: Callable[[dict[str, Any]], Mapping[str, Any]],
    live: bool,
) -> dict[str, Any]:
    from research.taskview_bom_scaling.c2.protocol import participant_request

    validate_packet(packet)
    assertion = packet["candidate_assertion"]
    key = [assertion["relation"], *assertion["tuple"]]
    allowed = [list(item) for item in authorized["authorized_assertions"]]
    if key not in allowed:
        raise LiveInferenceBlocked("assertion is outside the authorized C2 set")
    if not live:
        raise LiveInferenceBlocked("C2 live inference is not enabled for this run")
    request = participant_request(packet)
    parsed = validate_output(provider(request), packet)
    return dict(parsed)
