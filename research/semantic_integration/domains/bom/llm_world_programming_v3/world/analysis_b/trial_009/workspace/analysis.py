#!/usr/bin/env python3
"""Compute qualification bottlenecks from the compiled semantic World."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from world_surface import open_world, relation_rows


ROOT = Path(__file__).resolve().parent


def tuples(world: Any, relation: str, *columns: str) -> set[tuple[Any, ...]]:
    return {
        tuple(row[column] for column in columns)
        for row in relation_rows(world, relation)
    }


def complete_and_current(world: Any, relation: str) -> bool:
    receipt = world.latest_completeness(relation)
    return bool(
        receipt
        and receipt["status"] == "COMPLETE"
        and receipt.get("current", not receipt.get("stale", False))
        and not world.is_stale(relation)
    )


def one_state(states: dict[str, set[str]], part: str) -> str | None:
    values = states.get(part, set())
    if len(values) > 1:
        raise RuntimeError(f"ambiguous lifecycle states for {part}: {sorted(values)}")
    return next(iter(values), None)


def main() -> None:
    world = open_world()
    try:
        relevant_cases = world.query_semantic(
            """
            SELECT DISTINCT
                candidate_replacement.new_part_id AS new_part,
                candidate_replacement.old_part_id AS old_part,
                requires_type.bom_item_id AS bom_item,
                deployment_environment.environment_id AS context
            FROM candidate_replacement
            JOIN part_type
              ON part_type.part_id = candidate_replacement.old_part_id
            JOIN requires_type
              ON requires_type.part_type = part_type.part_type
            JOIN deployment_environment
              ON deployment_environment.bom_item_id = requires_type.bom_item_id
            """
        )

        voltage = tuples(
            world, "voltage_compatible", "part_id", "bom_item_id"
        )
        temperature = tuples(
            world, "temperature_compatible", "part_id", "bom_item_id"
        )
        accepted = tuples(
            world,
            "acceptable_replacement",
            "new_part_id",
            "old_part_id",
            "context_id",
        )

        lifecycle_states: dict[str, set[str]] = {}
        for row in relation_rows(world, "lifecycle"):
            lifecycle_states.setdefault(row["part_id"], set()).add(row["state"])

        unresolved = {
            (
                obligation["values"]["new_part"],
                obligation["values"]["old_part"],
                obligation["values"]["context"],
            )
            for obligation in world.obligations()
            if obligation["relation"] == "acceptable_replacement"
        }

        voltage_complete = complete_and_current(world, "voltage_compatible")
        temperature_complete = complete_and_current(
            world, "temperature_compatible"
        )

        cases = []
        for row in relevant_cases:
            new_part = row["new_part"]
            old_part = row["old_part"]
            bom_item = row["bom_item"]
            context = row["context"]

            voltage_ok = (new_part, bom_item) in voltage
            temperature_ok = (new_part, bom_item) in temperature
            new_lifecycle = one_state(lifecycle_states, new_part)
            old_lifecycle = one_state(lifecycle_states, old_part)
            lifecycle_active = new_lifecycle == "active"
            semantic_key = (new_part, old_part, context)

            if semantic_key in accepted:
                semantic_state = "accepted"
            elif semantic_key in unresolved:
                semantic_state = "unresolved"
            else:
                semantic_state = "not_established"

            prevents: list[str] = []
            uncertain: list[str] = []

            if not voltage_ok:
                (prevents if voltage_complete else uncertain).append(
                    "voltage_compatible"
                )
            if not temperature_ok:
                (prevents if temperature_complete else uncertain).append(
                    "temperature_compatible"
                )
            if not lifecycle_active:
                (prevents if new_lifecycle is not None else uncertain).append(
                    "lifecycle_active"
                )
            if semantic_state != "accepted":
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
                    "old_part_lifecycle": old_lifecycle or "unknown",
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
    finally:
        world.close()


if __name__ == "__main__":
    main()
