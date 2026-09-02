#!/usr/bin/env python3
"""Compute qualification bottlenecks from the compiled semantic World."""

import json
from pathlib import Path

from world_surface import open_world, relation_rows


OUTPUT_PATH = Path(__file__).resolve().parent / "output.json"


def tuples(world, relation, *columns):
    """Return selected semantic relation columns as a set of tuples."""
    return {
        tuple(row[column] for column in columns)
        for row in relation_rows(world, relation)
    }


def main():
    world = open_world()
    try:
        candidates = tuples(
            world, "candidate_replacement", "new_part_id", "old_part_id"
        )
        environments = tuples(
            world, "deployment_environment", "bom_item_id", "environment_id"
        )
        required_types = dict(
            tuples(world, "requires_type", "bom_item_id", "part_type")
        )
        part_types = dict(tuples(world, "part_type", "part_id", "part_type"))
        voltage_ok = tuples(
            world, "voltage_compatible", "part_id", "bom_item_id"
        )
        temperature_ok = tuples(
            world, "temperature_compatible", "part_id", "bom_item_id"
        )
        lifecycle = dict(tuples(world, "lifecycle", "part_id", "state"))
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

        cases = []
        for new_part, old_part in candidates:
            for bom_item, context in environments:
                # A BOM item is relevant to a replacement pair when its required
                # part type is the type of both the old and replacement parts.
                required_type = required_types.get(bom_item)
                if (
                    required_type is None
                    or part_types.get(old_part) != required_type
                    or part_types.get(new_part) != required_type
                ):
                    continue

                voltage_compatible = (new_part, bom_item) in voltage_ok
                temperature_compatible = (new_part, bom_item) in temperature_ok
                lifecycle_active = lifecycle.get(new_part) == "active"
                semantic_key = (new_part, old_part, context)
                if semantic_key in accepted:
                    semantic_state = "accepted"
                elif semantic_key in unresolved:
                    semantic_state = "unresolved"
                else:
                    semantic_state = "not_established"

                prevents = []
                if not voltage_compatible:
                    prevents.append("voltage_compatible")
                if not temperature_compatible:
                    prevents.append("temperature_compatible")
                if not lifecycle_active:
                    prevents.append("lifecycle_active")

                uncertain = []
                if semantic_state != "accepted":
                    uncertain.append("semantic_acceptance")

                cases.append(
                    {
                        "new_part": new_part,
                        "old_part": old_part,
                        "bom_item": bom_item,
                        "context": context,
                        "voltage_compatible": voltage_compatible,
                        "temperature_compatible": temperature_compatible,
                        "new_part_lifecycle_active": lifecycle_active,
                        "old_part_lifecycle": lifecycle.get(old_part, "unknown"),
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
        OUTPUT_PATH.write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8"
        )
    finally:
        world.close()


if __name__ == "__main__":
    main()
