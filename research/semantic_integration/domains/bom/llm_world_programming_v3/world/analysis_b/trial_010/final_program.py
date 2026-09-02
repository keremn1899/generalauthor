#!/usr/bin/env python3
"""Report qualification bottlenecks for represented replacement candidates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from world_surface import open_world, relation_rows


ROOT = Path(__file__).resolve().parent


def complete_relation(world: Any, relation: str) -> None:
    """Require evidence that a missing derived tuple is a negative result."""
    receipt = world.latest_completeness(relation)
    if (
        receipt is None
        or receipt["status"] != "COMPLETE"
        or not receipt["current"]
        or receipt["stale"]
    ):
        raise RuntimeError(f"{relation} does not have current complete results")


def unique_states(rows: list[dict[str, Any]]) -> dict[str, str]:
    states: dict[str, str] = {}
    for row in rows:
        part, state = row["part_id"], row["state"]
        if part in states and states[part] != state:
            raise RuntimeError(f"Conflicting lifecycle states for {part}")
        states[part] = state
    return states


def main() -> None:
    world = open_world()
    try:
        # Compatibility is represented positively, so only a complete,
        # current derivation permits absence to be interpreted as failure.
        complete_relation(world, "voltage_compatible")
        complete_relation(world, "temperature_compatible")

        candidates = relation_rows(world, "candidate_replacement")
        part_types = relation_rows(world, "part_type")
        required_types = relation_rows(world, "requires_type")
        environments = relation_rows(world, "deployment_environment")
        voltage_rows = relation_rows(world, "voltage_compatible")
        temperature_rows = relation_rows(world, "temperature_compatible")
        lifecycle = unique_states(relation_rows(world, "lifecycle"))
        acceptance_rows = relation_rows(world, "acceptable_replacement")
        obligations = world.obligations()
    finally:
        world.close()

    types_by_part: dict[str, set[str]] = {}
    for row in part_types:
        types_by_part.setdefault(row["part_id"], set()).add(row["part_type"])

    required_by_bom: dict[str, set[str]] = {}
    for row in required_types:
        required_by_bom.setdefault(row["bom_item_id"], set()).add(
            row["part_type"]
        )

    contexts_by_bom: dict[str, set[str]] = {}
    for row in environments:
        contexts_by_bom.setdefault(row["bom_item_id"], set()).add(
            row["environment_id"]
        )

    voltage_compatible = {
        (row["part_id"], row["bom_item_id"]) for row in voltage_rows
    }
    temperature_compatible = {
        (row["part_id"], row["bom_item_id"]) for row in temperature_rows
    }
    accepted = {
        (row["new_part_id"], row["old_part_id"], row["context_id"])
        for row in acceptance_rows
    }
    unresolved = {
        (
            obligation["values"]["new_part"],
            obligation["values"]["old_part"],
            obligation["values"]["context"],
        )
        for obligation in obligations
        if obligation["relation"] == "acceptable_replacement"
    }

    cases: list[dict[str, Any]] = []
    for candidate in candidates:
        new_part = candidate["new_part_id"]
        old_part = candidate["old_part_id"]
        if new_part not in lifecycle or old_part not in lifecycle:
            raise RuntimeError(
                f"Missing lifecycle state for candidate {new_part}, {old_part}"
            )

        # A BOM item is relevant to a replacement pair when it requires the
        # represented type of the part being replaced.
        old_types = types_by_part.get(old_part, set())
        relevant_boms = sorted(
            bom_item
            for bom_item, required in required_by_bom.items()
            if old_types & required
        )

        for bom_item in relevant_boms:
            for context in sorted(contexts_by_bom.get(bom_item, set())):
                voltage_ok = (new_part, bom_item) in voltage_compatible
                temperature_ok = (new_part, bom_item) in temperature_compatible
                lifecycle_active = lifecycle[new_part] == "active"
                semantic_key = (new_part, old_part, context)

                if semantic_key in accepted:
                    semantic_state = "accepted"
                elif semantic_key in unresolved:
                    semantic_state = "unresolved"
                else:
                    semantic_state = "not_established"

                prevents: list[str] = []
                if not voltage_ok:
                    prevents.append("voltage_compatible")
                if not temperature_ok:
                    prevents.append("temperature_compatible")
                if not lifecycle_active:
                    prevents.append("lifecycle_active")

                uncertain: list[str] = []
                if semantic_state != "accepted":
                    # Lack of positive semantic acceptance is uncertainty,
                    # rather than evidence that qualification failed.
                    uncertain.append("semantic_acceptance")

                cases.append(
                    {
                        "new_part": new_part,
                        "old_part": old_part,
                        "bom_item": bom_item,
                        "context": context,
                        "voltage_compatible": voltage_ok,
                        "temperature_compatible": temperature_ok,
                        "new_part_lifecycle_active": lifecycle_active,
                        "old_part_lifecycle": lifecycle[old_part],
                        "semantic_state": semantic_state,
                        "prevents_viability": prevents,
                        "leaves_viability_uncertain": uncertain,
                    }
                )

    cases.sort(
        key=lambda case: (
            case["new_part"],
            case["old_part"],
            case["bom_item"],
            case["context"],
        )
    )
    result = {"task": "qualification_bottlenecks", "cases": cases}
    (ROOT / "output.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
