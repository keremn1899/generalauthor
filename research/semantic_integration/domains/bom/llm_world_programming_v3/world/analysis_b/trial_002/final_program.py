#!/usr/bin/env python3
"""Report qualification bottlenecks for represented replacement candidates."""

from __future__ import annotations

import json
from pathlib import Path

from world_surface import open_world, relation_rows


OUTPUT_PATH = Path(__file__).resolve().parent / "output.json"
CONSTRAINT_ORDER = (
    "voltage_compatible",
    "temperature_compatible",
    "lifecycle_active",
    "semantic_acceptance",
)


def tuples(rows: list[dict[str, object]], *columns: str) -> set[tuple[object, ...]]:
    return {tuple(row[column] for column in columns) for row in rows}


def main() -> None:
    world = open_world()
    try:
        candidates = relation_rows(world, "candidate_replacement")
        part_types = {
            row["part_id"]: row["part_type"]
            for row in relation_rows(world, "part_type")
        }
        required_types = relation_rows(world, "requires_type")
        environments = {
            row["bom_item_id"]: row["environment_id"]
            for row in relation_rows(world, "deployment_environment")
        }
        lifecycle = {
            row["part_id"]: row["state"]
            for row in relation_rows(world, "lifecycle")
        }
        voltage_ok = tuples(
            relation_rows(world, "voltage_compatible"), "part_id", "bom_item_id"
        )
        temperature_ok = tuples(
            relation_rows(world, "temperature_compatible"), "part_id", "bom_item_id"
        )
        accepted = tuples(
            relation_rows(world, "acceptable_replacement"),
            "new_part_id",
            "old_part_id",
            "context_id",
        )
        unresolved = {
            (
                item["values"]["new_part"],
                item["values"]["old_part"],
                item["values"]["context"],
            )
            for item in world.obligations()
            if item["relation"] == "acceptable_replacement"
        }

        cases: list[dict[str, object]] = []
        for candidate in candidates:
            new_part = candidate["new_part_id"]
            old_part = candidate["old_part_id"]

            # A BOM item is relevant when its required part type matches the
            # represented replacement candidate's type.
            for requirement in required_types:
                bom_item = requirement["bom_item_id"]
                if part_types.get(new_part) != requirement["part_type"]:
                    continue
                context = environments[bom_item]

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

                failed = {
                    "voltage_compatible": not voltage_compatible,
                    "temperature_compatible": not temperature_compatible,
                    "lifecycle_active": not lifecycle_active,
                }
                uncertain = {
                    "semantic_acceptance": semantic_state != "accepted",
                }

                cases.append(
                    {
                        "new_part": new_part,
                        "old_part": old_part,
                        "bom_item": bom_item,
                        "context": context,
                        "voltage_compatible": voltage_compatible,
                        "temperature_compatible": temperature_compatible,
                        "new_part_lifecycle_active": lifecycle_active,
                        "old_part_lifecycle": lifecycle[old_part],
                        "semantic_state": semantic_state,
                        "prevents_viability": [
                            name for name in CONSTRAINT_ORDER if failed.get(name, False)
                        ],
                        "leaves_viability_uncertain": [
                            name
                            for name in CONSTRAINT_ORDER
                            if uncertain.get(name, False)
                        ],
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
        OUTPUT_PATH.write_text(
            json.dumps(
                {"task": "qualification_bottlenecks", "cases": cases},
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    finally:
        world.close()


if __name__ == "__main__":
    main()
