#!/usr/bin/env python3
"""Compute qualification bottlenecks from the compiled semantic World."""

from __future__ import annotations

import json
from pathlib import Path

from world_surface import open_world, relation_rows


ROOT = Path(__file__).resolve().parent


def tuple_set(world, relation: str, *columns: str) -> set[tuple[object, ...]]:
    return {
        tuple(row[column] for column in columns)
        for row in relation_rows(world, relation)
    }


def main() -> None:
    world = open_world()
    try:
        # A BOM item is relevant to an old part when it requires that part's
        # represented type. Its deployment relation supplies the case context.
        relevant_cases = world.query_semantic(
            """
            SELECT DISTINCT
                c.new_part_id,
                c.old_part_id,
                r.bom_item_id,
                d.environment_id
            FROM candidate_replacement AS c
            JOIN part_type AS p
              ON p.part_id = c.old_part_id
            JOIN requires_type AS r
              ON r.part_type = p.part_type
            JOIN deployment_environment AS d
              ON d.bom_item_id = r.bom_item_id
            """
        )

        voltage = tuple_set(
            world, "voltage_compatible", "part_id", "bom_item_id"
        )
        temperature = tuple_set(
            world, "temperature_compatible", "part_id", "bom_item_id"
        )
        accepted = tuple_set(
            world,
            "acceptable_replacement",
            "new_part_id",
            "old_part_id",
            "context_id",
        )

        lifecycle_by_part: dict[str, set[str]] = {}
        for row in relation_rows(world, "lifecycle"):
            lifecycle_by_part.setdefault(row["part_id"], set()).add(row["state"])

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
        for row in relevant_cases:
            new_part = row["new_part_id"]
            old_part = row["old_part_id"]
            bom_item = row["bom_item_id"]
            context = row["environment_id"]

            voltage_ok = (new_part, bom_item) in voltage
            temperature_ok = (new_part, bom_item) in temperature
            new_lifecycle_active = "active" in lifecycle_by_part.get(new_part, set())

            old_states = lifecycle_by_part.get(old_part, set())
            if len(old_states) != 1:
                raise ValueError(
                    f"Expected one lifecycle state for {old_part}, got {old_states}"
                )
            old_lifecycle = next(iter(old_states))

            semantic_key = (new_part, old_part, context)
            if semantic_key in accepted:
                semantic_state = "accepted"
            elif semantic_key in unresolved:
                semantic_state = "unresolved"
            else:
                semantic_state = "not_established"

            prevents_viability = []
            if not voltage_ok:
                prevents_viability.append("voltage_compatible")
            if not temperature_ok:
                prevents_viability.append("temperature_compatible")
            if not new_lifecycle_active:
                prevents_viability.append("lifecycle_active")

            # Lack of a positive semantic judgment is uncertainty, not a
            # demonstrated qualification failure.
            leaves_viability_uncertain = []
            if semantic_state != "accepted":
                leaves_viability_uncertain.append("semantic_acceptance")

            cases.append(
                {
                    "new_part": new_part,
                    "old_part": old_part,
                    "bom_item": bom_item,
                    "context": context,
                    "voltage_compatible": voltage_ok,
                    "temperature_compatible": temperature_ok,
                    "new_part_lifecycle_active": new_lifecycle_active,
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
        (ROOT / "output.json").write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8"
        )
    finally:
        world.close()


if __name__ == "__main__":
    main()
