#!/usr/bin/env python3
"""Qualification bottleneck analysis over the compiled semantic World."""

from __future__ import annotations

import json
from pathlib import Path

from world_surface import open_world

ROOT = Path(__file__).resolve().parent
OUTPUT_PATH = ROOT / "output.json"


def _completeness_allows_negative(world, relation: str) -> bool:
    receipt = world.latest_completeness(relation)
    return receipt is not None and receipt.get("status") == "COMPLETE"


def _semantic_state(
    accepted: set[tuple[str, str, str]],
    obligations: set[tuple[str, str, str]],
    new_part: str,
    old_part: str,
    context: str,
) -> str:
    key = (new_part, old_part, context)
    if key in accepted:
        return "accepted"
    if key in obligations:
        return "unresolved"
    return "not_established"


def main() -> None:
    world = open_world()
    try:
        voltage_complete = _completeness_allows_negative(world, "voltage_compatible")
        temperature_complete = _completeness_allows_negative(
            world, "temperature_compatible"
        )

        rows = world.query_semantic(
            """
            SELECT
                cr.new_part_id AS new_part,
                cr.old_part_id AS old_part,
                de.bom_item_id AS bom_item,
                de.environment_id AS context,
                CASE WHEN nvc.part_id IS NOT NULL THEN 1 ELSE 0 END AS new_voltage_ok,
                CASE WHEN ntc.part_id IS NOT NULL THEN 1 ELSE 0 END AS new_temperature_ok,
                nl.state AS new_lifecycle_state,
                ol.state AS old_lifecycle_state
            FROM candidate_replacement AS cr
            JOIN deployment_environment AS de ON 1 = 1
            JOIN voltage_compatible AS ovc
              ON ovc.part_id = cr.old_part_id
             AND ovc.bom_item_id = de.bom_item_id
            JOIN temperature_compatible AS otc
              ON otc.part_id = cr.old_part_id
             AND otc.bom_item_id = de.bom_item_id
            LEFT JOIN voltage_compatible AS nvc
              ON nvc.part_id = cr.new_part_id
             AND nvc.bom_item_id = de.bom_item_id
            LEFT JOIN temperature_compatible AS ntc
              ON ntc.part_id = cr.new_part_id
             AND ntc.bom_item_id = de.bom_item_id
            LEFT JOIN lifecycle AS nl ON nl.part_id = cr.new_part_id
            LEFT JOIN lifecycle AS ol ON ol.part_id = cr.old_part_id
            """
        )

        accepted = {
            (row["new_part_id"], row["old_part_id"], row["context_id"])
            for row in world.query_semantic(
                "SELECT new_part_id, old_part_id, context_id FROM acceptable_replacement"
            )
        }

        obligations: set[tuple[str, str, str]] = set()
        for obligation in world.obligations():
            if obligation.get("relation") != "acceptable_replacement":
                continue
            values = obligation.get("values", {})
            obligations.add(
                (
                    values["new_part"],
                    values["old_part"],
                    values["context"],
                )
            )

        cases = []
        for row in rows:
            new_part = row["new_part"]
            old_part = row["old_part"]
            bom_item = row["bom_item"]
            context = row["context"]

            voltage_compatible = bool(row["new_voltage_ok"])
            temperature_compatible = bool(row["new_temperature_ok"])
            new_lifecycle_state = row["new_lifecycle_state"]
            new_part_lifecycle_active = (
                new_lifecycle_state is not None
                and new_lifecycle_state != "discontinued"
            )

            semantic = _semantic_state(
                accepted, obligations, new_part, old_part, context
            )

            prevents_viability: list[str] = []
            leaves_viability_uncertain: list[str] = []

            if voltage_complete and not voltage_compatible:
                prevents_viability.append("voltage_compatible")
            if temperature_complete and not temperature_compatible:
                prevents_viability.append("temperature_compatible")
            if not new_part_lifecycle_active:
                prevents_viability.append("lifecycle_active")
            if semantic == "unresolved":
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
                    "old_part_lifecycle": row["old_lifecycle_state"] or "",
                    "semantic_state": semantic,
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

        result = {
            "task": "qualification_bottlenecks",
            "cases": cases,
        }
    finally:
        world.close()

    OUTPUT_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
