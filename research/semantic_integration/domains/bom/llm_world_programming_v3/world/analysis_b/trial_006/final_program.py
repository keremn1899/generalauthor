#!/usr/bin/env python3
"""Compute qualification bottlenecks from the compiled semantic World."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from world_surface import open_world, relation_rows


OUTPUT_PATH = Path(__file__).resolve().with_name("output.json")


def tuples(world: Any, relation: str, *columns: str) -> set[tuple[Any, ...]]:
    """Return selected semantic relation columns as a set of tuples."""
    return {
        tuple(row[column] for column in columns)
        for row in relation_rows(world, relation)
    }


def require_complete(world: Any, relation: str) -> None:
    """Ensure absence from a derived relation can be interpreted as failure."""
    receipt = world.latest_completeness(relation)
    if (
        receipt is None
        or receipt.get("status") != "COMPLETE"
        or not receipt.get("current")
        or receipt.get("stale")
        or world.is_stale(relation)
    ):
        raise RuntimeError(f"{relation} is not complete and current")


def single_value(mapping: dict[str, list[str]], key: str, label: str) -> str:
    values = mapping.get(key, [])
    if len(values) != 1:
        raise RuntimeError(
            f"Expected exactly one {label} for {key}, found {len(values)}"
        )
    return values[0]


def main() -> None:
    world = open_world()
    try:
        require_complete(world, "voltage_compatible")
        require_complete(world, "temperature_compatible")

        candidates = tuples(
            world, "candidate_replacement", "new_part_id", "old_part_id"
        )
        accepted = tuples(
            world,
            "acceptable_replacement",
            "new_part_id",
            "old_part_id",
            "context_id",
        )
        voltage_ok = tuples(
            world, "voltage_compatible", "part_id", "bom_item_id"
        )
        temperature_ok = tuples(
            world, "temperature_compatible", "part_id", "bom_item_id"
        )

        part_types: dict[str, list[str]] = {}
        for row in relation_rows(world, "part_type"):
            part_types.setdefault(row["part_id"], []).append(row["part_type"])

        required_types: dict[str, list[str]] = {}
        for row in relation_rows(world, "requires_type"):
            required_types.setdefault(row["bom_item_id"], []).append(row["part_type"])

        environments: dict[str, list[str]] = {}
        for row in relation_rows(world, "deployment_environment"):
            environments.setdefault(row["bom_item_id"], []).append(
                row["environment_id"]
            )

        lifecycles: dict[str, list[str]] = {}
        for row in relation_rows(world, "lifecycle"):
            lifecycles.setdefault(row["part_id"], []).append(row["state"])

        unresolved = {
            (
                obligation["values"]["new_part"],
                obligation["values"]["old_part"],
                obligation["values"]["context"],
            )
            for obligation in world.obligations()
            if obligation.get("relation") == "acceptable_replacement"
            and {"new_part", "old_part", "context"}
            <= obligation.get("values", {}).keys()
        }

        cases: list[dict[str, Any]] = []
        for new_part, old_part in candidates:
            old_type = single_value(part_types, old_part, "part type")
            new_lifecycle = single_value(lifecycles, new_part, "lifecycle state")
            old_lifecycle = single_value(lifecycles, old_part, "lifecycle state")

            # A BOM item is relevant when it calls for the type of the part
            # being replaced. Its deployment environment supplies the context.
            for bom_item, types in required_types.items():
                if old_type not in types:
                    continue
                context = single_value(
                    environments, bom_item, "deployment environment"
                )

                voltage_compatible = (new_part, bom_item) in voltage_ok
                temperature_compatible = (new_part, bom_item) in temperature_ok
                lifecycle_active = new_lifecycle == "active"
                semantic_key = (new_part, old_part, context)

                if semantic_key in accepted:
                    semantic_state = "accepted"
                elif semantic_key in unresolved:
                    semantic_state = "unresolved"
                else:
                    semantic_state = "not_established"

                prevents_viability = []
                if not voltage_compatible:
                    prevents_viability.append("voltage_compatible")
                if not temperature_compatible:
                    prevents_viability.append("temperature_compatible")
                if not lifecycle_active:
                    prevents_viability.append("lifecycle_active")

                leaves_viability_uncertain = []
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
                        "new_part_lifecycle_active": lifecycle_active,
                        "old_part_lifecycle": old_lifecycle,
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
