#!/usr/bin/env python3
"""Report qualification bottlenecks for represented replacement candidates."""

from __future__ import annotations

import json
from pathlib import Path

from world_surface import open_world


OUTPUT_PATH = Path(__file__).resolve().with_name("output.json")


def require_complete(world, relation: str) -> None:
    """Ensure absence from a derived relation can be treated as a negative."""
    receipt = world.latest_completeness(relation)
    if (
        receipt is None
        or receipt.get("status") != "COMPLETE"
        or not receipt.get("current")
        or receipt.get("stale")
    ):
        raise RuntimeError(f"{relation} does not have current COMPLETE coverage")


def one_state(states: dict[str, set[str]], part: str) -> str | None:
    values = states.get(part, set())
    if len(values) > 1:
        raise RuntimeError(f"ambiguous lifecycle states for {part}: {sorted(values)}")
    return next(iter(values), None)


def main() -> None:
    world = open_world()
    try:
        require_complete(world, "voltage_compatible")
        require_complete(world, "temperature_compatible")

        # A BOM item is relevant to a candidate when it requires the old
        # part's represented type. Its deployment environment supplies the
        # context in which semantic replacement acceptance is judged.
        relevant = world.query_semantic(
            """
            SELECT DISTINCT
                c.new_part_id AS new_part,
                c.old_part_id AS old_part,
                r.bom_item_id AS bom_item,
                d.environment_id AS context
            FROM candidate_replacement AS c
            JOIN part_type AS old_type
              ON old_type.part_id = c.old_part_id
            JOIN requires_type AS r
              ON r.part_type = old_type.part_type
            JOIN deployment_environment AS d
              ON d.bom_item_id = r.bom_item_id
            """
        )

        voltage = {
            (row["part_id"], row["bom_item_id"])
            for row in world.query_semantic(
                "SELECT part_id, bom_item_id FROM voltage_compatible"
            )
        }
        temperature = {
            (row["part_id"], row["bom_item_id"])
            for row in world.query_semantic(
                "SELECT part_id, bom_item_id FROM temperature_compatible"
            )
        }

        lifecycle: dict[str, set[str]] = {}
        for row in world.query_semantic("SELECT part_id, state FROM lifecycle"):
            lifecycle.setdefault(row["part_id"], set()).add(row["state"])

        accepted = {
            (row["new_part_id"], row["old_part_id"], row["context_id"])
            for row in world.query_semantic(
                """
                SELECT new_part_id, old_part_id, context_id
                FROM acceptable_replacement
                """
            )
        }
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

        cases = []
        for row in relevant:
            new_part = row["new_part"]
            old_part = row["old_part"]
            bom_item = row["bom_item"]
            context = row["context"]

            voltage_ok = (new_part, bom_item) in voltage
            temperature_ok = (new_part, bom_item) in temperature
            new_lifecycle = one_state(lifecycle, new_part)
            old_lifecycle = one_state(lifecycle, old_part)
            lifecycle_active = new_lifecycle == "active"

            semantic_key = (new_part, old_part, context)
            if semantic_key in accepted:
                semantic_state = "accepted"
            elif semantic_key in unresolved:
                semantic_state = "unresolved"
            else:
                semantic_state = "not_established"

            prevents = []
            uncertain = []
            if not voltage_ok:
                prevents.append("voltage_compatible")
            if not temperature_ok:
                prevents.append("temperature_compatible")
            if new_lifecycle is None:
                uncertain.append("lifecycle_active")
            elif not lifecycle_active:
                prevents.append("lifecycle_active")
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
        OUTPUT_PATH.write_text(
            json.dumps(result, indent=2, sort_keys=False) + "\n",
            encoding="utf-8",
        )
    finally:
        world.close()


if __name__ == "__main__":
    main()
