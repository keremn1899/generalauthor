"""WORLD B: multi-relation qualification bottlenecks over compiled World state."""

from __future__ import annotations

from typing import Any

from research.semantic_integration.core.kernel import SemanticWorld
from research.semantic_integration.domains.bom.world_programming.relation_rows import (
    relation_rows,
)
from research.semantic_integration.domains.bom.world_programming.world.analysis_a import (
    demanded_replacement_cases,
)


def _derived_miss_is_failure(world: SemanticWorld, relation: str) -> bool:
    receipt = world.latest_completeness(relation)
    return bool(
        receipt
        and receipt["status"] == "COMPLETE"
        and not world.is_stale(relation)
    )


def _holds(pairs: set[tuple[str, str]], part: str, bom: str) -> bool:
    return (part, bom) in pairs


def run(world: SemanticWorld, obligations: list[dict[str, Any]]) -> dict[str, Any]:
    voltage = {
        (row["part_id"], row["bom_item_id"])
        for row in relation_rows(world, "voltage_compatible")
    }
    temperature = {
        (row["part_id"], row["bom_item_id"])
        for row in relation_rows(world, "temperature_compatible")
    }
    lifecycle = {
        row["part_id"]: row["state"] for row in relation_rows(world, "lifecycle")
    }
    accepted = {
        (row["new_part_id"], row["old_part_id"], row["context_id"])
        for row in relation_rows(world, "acceptable_replacement")
    }
    unresolved = {
        (
            item["values"]["new_part"],
            item["values"]["old_part"],
            item["values"]["context"],
        )
        for item in obligations
        if item["relation"] == "acceptable_replacement"
    }

    cases: list[dict[str, Any]] = []
    for row in demanded_replacement_cases(world):
        new_part = row["new_part"]
        old_part = row["old_part"]
        bom = row["bom_item"]
        context = row["context"]
        voltage_ok = _holds(voltage, new_part, bom)
        temperature_ok = _holds(temperature, new_part, bom)
        active = lifecycle.get(new_part, "unknown") != "discontinued"
        key = (new_part, old_part, context)
        if key in accepted:
            semantic_state = "accepted"
        elif key in unresolved:
            semantic_state = "unresolved"
        else:
            semantic_state = "not_established"
        prevents: list[str] = []
        uncertain: list[str] = []
        if not voltage_ok:
            if _derived_miss_is_failure(world, "voltage_compatible"):
                prevents.append("voltage_compatible")
            else:
                uncertain.append("voltage_compatible")
        if not temperature_ok:
            if _derived_miss_is_failure(world, "temperature_compatible"):
                prevents.append("temperature_compatible")
            else:
                uncertain.append("temperature_compatible")
        if not active:
            prevents.append("lifecycle_active")
        if semantic_state == "unresolved":
            uncertain.append("semantic_acceptance")
        cases.append(
            {
                "new_part": new_part,
                "old_part": old_part,
                "bom_item": bom,
                "context": context,
                "voltage_compatible": voltage_ok,
                "temperature_compatible": temperature_ok,
                "new_part_lifecycle_active": active,
                "old_part_lifecycle": lifecycle.get(old_part, "unknown"),
                "semantic_state": semantic_state,
                "prevents_viability": prevents,
                "leaves_viability_uncertain": uncertain,
            }
        )
    cases.sort(
        key=lambda row: (
            row["new_part"],
            row["old_part"],
            row["bom_item"],
            row["context"],
        )
    )
    return {"task": "qualification_bottlenecks", "cases": cases}
