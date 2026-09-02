#!/usr/bin/env python3
"""Report qualification bottlenecks for represented replacement candidates."""

from __future__ import annotations

import json
from pathlib import Path

from world_surface import open_world, relation_rows


OUTPUT_PATH = Path(__file__).resolve().parent / "output.json"


def tuples(world, relation: str, *columns: str) -> set[tuple[object, ...]]:
    """Return selected columns from a semantic relation as tuples."""
    return {
        tuple(row[column] for column in columns)
        for row in relation_rows(world, relation)
    }


def complete_and_current(world, relation: str) -> bool:
    receipt = world.latest_completeness(relation)
    return bool(
        receipt
        and receipt["status"] == "COMPLETE"
        and receipt["current"]
        and not receipt["stale"]
    )


def main() -> None:
    world = open_world()
    try:
        candidates = tuples(
            world, "candidate_replacement", "new_part_id", "old_part_id"
        )
        part_types = tuples(world, "part_type", "part_id", "part_type")
        required_types = tuples(
            world, "requires_type", "bom_item_id", "part_type"
        )
        environments = dict(
            tuples(
                world,
                "deployment_environment",
                "bom_item_id",
                "environment_id",
            )
        )
        voltage_ok = tuples(
            world, "voltage_compatible", "part_id", "bom_item_id"
        )
        temperature_ok = tuples(
            world, "temperature_compatible", "part_id", "bom_item_id"
        )
        lifecycle_rows = tuples(world, "lifecycle", "part_id", "state")
        lifecycle_by_part = {part: state for part, state in lifecycle_rows}
        accepted = tuples(
            world,
            "acceptable_replacement",
            "new_part_id",
            "old_part_id",
            "context_id",
        )

        unresolved = {
            (
                obligation["values"]["new_part"],
                obligation["values"]["old_part"],
                obligation["values"]["context"],
            )
            for obligation in world.obligations()
            if obligation["relation"] == "acceptable_replacement"
        }

        type_by_part = {part: part_type for part, part_type in part_types}
        boms_by_type: dict[object, set[object]] = {}
        for bom_item, part_type in required_types:
            boms_by_type.setdefault(part_type, set()).add(bom_item)

        voltage_complete = complete_and_current(world, "voltage_compatible")
        temperature_complete = complete_and_current(
            world, "temperature_compatible"
        )

        cases = []
        for new_part, old_part in candidates:
            old_type = type_by_part.get(old_part)
            for bom_item in boms_by_type.get(old_type, set()):
                context = environments[bom_item]
                voltage_compatible = (new_part, bom_item) in voltage_ok
                temperature_compatible = (new_part, bom_item) in temperature_ok
                new_lifecycle = lifecycle_by_part.get(new_part)
                new_part_lifecycle_active = new_lifecycle == "active"
                semantic_key = (new_part, old_part, context)

                if semantic_key in accepted:
                    semantic_state = "accepted"
                elif semantic_key in unresolved:
                    semantic_state = "unresolved"
                else:
                    semantic_state = "not_established"

                prevents_viability = []
                leaves_viability_uncertain = []

                if not voltage_compatible:
                    target = (
                        prevents_viability
                        if voltage_complete
                        else leaves_viability_uncertain
                    )
                    target.append("voltage_compatible")
                if not temperature_compatible:
                    target = (
                        prevents_viability
                        if temperature_complete
                        else leaves_viability_uncertain
                    )
                    target.append("temperature_compatible")
                if not new_part_lifecycle_active:
                    target = (
                        leaves_viability_uncertain
                        if new_lifecycle is None
                        else prevents_viability
                    )
                    target.append("lifecycle_active")

                # An absent positive semantic judgment is uncertainty, not failure.
                if semantic_state != "accepted":
                    leaves_viability_uncertain.append("semantic_acceptance")

                cases.append(
                    {
                        "new_part": new_part,
                        "old_part": old_part,
                        "bom_item": bom_item,
                        "context": context,
                        "voltage_compatible": voltage_compatible,
                        "temperature_compatible": temperature_compatible,
                        "new_part_lifecycle_active": new_part_lifecycle_active,
                        "old_part_lifecycle": lifecycle_by_part.get(
                            old_part, "unknown"
                        ),
                        "semantic_state": semantic_state,
                        "prevents_viability": prevents_viability,
                        "leaves_viability_uncertain": leaves_viability_uncertain,
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
        OUTPUT_PATH.write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8"
        )
    finally:
        world.close()


if __name__ == "__main__":
    main()
