#!/usr/bin/env python3
"""Qualification bottleneck analysis over the compiled semantic World."""

from __future__ import annotations

import json
from pathlib import Path

from world_surface import open_world

ROOT = Path(__file__).resolve().parent
OUTPUT_PATH = ROOT / "output.json"

RELEVANT_CASES_SQL = """
SELECT
    cr.new_part_id AS new_part,
    cr.old_part_id AS old_part,
    de.bom_item_id AS bom_item,
    de.environment_id AS context
FROM candidate_replacement AS cr
JOIN part_type AS pt ON pt.part_id = cr.old_part_id
JOIN requires_type AS rt ON rt.part_type = pt.part_type
JOIN deployment_environment AS de ON de.bom_item_id = rt.bom_item_id
ORDER BY cr.new_part_id, cr.old_part_id, de.bom_item_id, de.environment_id
"""


def _obligation_key(obligation: dict) -> tuple[str, str, str]:
    values = obligation["values"]
    return (
        values["new_part"],
        values["old_part"],
        values["context"],
    )


def _semantic_state(
    new_part: str,
    old_part: str,
    context: str,
    accepted: set[tuple[str, str, str]],
    obligated: set[tuple[str, str, str]],
) -> str:
    key = (new_part, old_part, context)
    if key in accepted:
        return "accepted"
    if key in obligated:
        return "unresolved"
    return "not_established"


def main() -> None:
    world = open_world()
    try:
        voltage_complete = (
            world.latest_completeness("voltage_compatible") or {}
        ).get("status") == "COMPLETE"
        temperature_complete = (
            world.latest_completeness("temperature_compatible") or {}
        ).get("status") == "COMPLETE"

        cases = world.query_semantic(RELEVANT_CASES_SQL)

        voltage_compatible = {
            (row["part_id"], row["bom_item_id"])
            for row in world.query_semantic(
                "SELECT part_id, bom_item_id FROM voltage_compatible"
            )
        }
        temperature_compatible = {
            (row["part_id"], row["bom_item_id"])
            for row in world.query_semantic(
                "SELECT part_id, bom_item_id FROM temperature_compatible"
            )
        }
        lifecycle = {
            row["part_id"]: row["state"]
            for row in world.query_semantic("SELECT part_id, state FROM lifecycle")
        }
        accepted = {
            (row["new_part_id"], row["old_part_id"], row["context_id"])
            for row in world.query_semantic(
                "SELECT new_part_id, old_part_id, context_id FROM acceptable_replacement"
            )
        }
        obligated = {
            _obligation_key(obligation)
            for obligation in world.obligations()
            if obligation.get("relation") == "acceptable_replacement"
        }

        results = []
        for case in cases:
            new_part = case["new_part"]
            old_part = case["old_part"]
            bom_item = case["bom_item"]
            context = case["context"]

            voltage_ok = (new_part, bom_item) in voltage_compatible
            temperature_ok = (new_part, bom_item) in temperature_compatible
            new_lifecycle = lifecycle.get(new_part, "")
            new_lifecycle_active = new_lifecycle == "active"
            old_lifecycle = lifecycle.get(old_part, "")

            semantic = _semantic_state(
                new_part, old_part, context, accepted, obligated
            )

            prevents_viability: list[str] = []
            leaves_viability_uncertain: list[str] = []

            if voltage_complete and not voltage_ok:
                prevents_viability.append("voltage_compatible")
            if temperature_complete and not temperature_ok:
                prevents_viability.append("temperature_compatible")
            if not new_lifecycle_active:
                prevents_viability.append("lifecycle_active")
            if semantic == "unresolved":
                leaves_viability_uncertain.append("semantic_acceptance")

            results.append(
                {
                    "new_part": new_part,
                    "old_part": old_part,
                    "bom_item": bom_item,
                    "context": context,
                    "voltage_compatible": voltage_ok,
                    "temperature_compatible": temperature_ok,
                    "new_part_lifecycle_active": new_lifecycle_active,
                    "old_part_lifecycle": old_lifecycle,
                    "semantic_state": semantic,
                    "prevents_viability": prevents_viability,
                    "leaves_viability_uncertain": leaves_viability_uncertain,
                }
            )

        output = {
            "task": "qualification_bottlenecks",
            "cases": results,
        }
        OUTPUT_PATH.write_text(
            json.dumps(output, indent=2, sort_keys=False) + "\n",
            encoding="utf-8",
        )
    finally:
        world.close()


if __name__ == "__main__":
    main()
