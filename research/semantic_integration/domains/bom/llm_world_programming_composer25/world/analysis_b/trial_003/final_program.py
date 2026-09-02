#!/usr/bin/env python3
"""Qualification bottleneck analysis over the compiled semantic World."""

from __future__ import annotations

import json
from pathlib import Path

from world_surface import open_world

ROOT = Path(__file__).resolve().parent
OUTPUT_PATH = ROOT / "output.json"

DERIVED_CONSTRAINTS = ("voltage_compatible", "temperature_compatible")


def completeness_is_definitive(world, relation: str) -> bool:
    receipt = world.latest_completeness(relation)
    if receipt is None:
        return False
    return receipt.get("status") == "COMPLETE" and receipt.get("execution_status") == "SUCCEEDED"


def load_sets(world):
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
    accepted = {
        (row["new_part_id"], row["old_part_id"], row["context_id"])
        for row in world.query_semantic(
            "SELECT new_part_id, old_part_id, context_id FROM acceptable_replacement"
        )
    }
    lifecycle = {
        row["part_id"]: row["state"]
        for row in world.query_semantic("SELECT part_id, state FROM lifecycle")
    }
    return voltage, temperature, accepted, lifecycle


def load_obligations(world) -> set[tuple[str, str, str]]:
    unresolved: set[tuple[str, str, str]] = set()
    for obligation in world.obligations():
        if obligation.get("relation") != "acceptable_replacement":
            continue
        values = obligation.get("values", {})
        unresolved.add(
            (
                values["new_part"],
                values["old_part"],
                values["context"],
            )
        )
    return unresolved


def semantic_state(
    new_part: str,
    old_part: str,
    context: str,
    accepted: set[tuple[str, str, str]],
    unresolved: set[tuple[str, str, str]],
) -> str:
    key = (new_part, old_part, context)
    if key in accepted:
        return "accepted"
    if key in unresolved:
        return "unresolved"
    return "not_established"


def evaluate_constraint(
    *,
    compatible: bool,
    derivation_complete: bool,
    constraint_name: str,
    prevents: list[str],
    uncertain: list[str],
) -> None:
    if compatible:
        return
    if derivation_complete:
        prevents.append(constraint_name)
    else:
        uncertain.append(constraint_name)


def main() -> None:
    world = open_world()
    try:
        voltage, temperature, accepted, lifecycle = load_sets(world)
        unresolved = load_obligations(world)

        voltage_complete = completeness_is_definitive(world, "voltage_compatible")
        temperature_complete = completeness_is_definitive(
            world, "temperature_compatible"
        )

        cases = world.query_semantic(
            """
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
        )

        results = []
        for case in cases:
            new_part = case["new_part"]
            old_part = case["old_part"]
            bom_item = case["bom_item"]
            context = case["context"]

            voltage_ok = (new_part, bom_item) in voltage
            temperature_ok = (new_part, bom_item) in temperature
            new_lifecycle = lifecycle.get(new_part, "")
            new_part_lifecycle_active = new_lifecycle == "active"
            old_part_lifecycle = lifecycle.get(old_part, "")

            state = semantic_state(new_part, old_part, context, accepted, unresolved)

            prevents: list[str] = []
            uncertain: list[str] = []

            evaluate_constraint(
                compatible=voltage_ok,
                derivation_complete=voltage_complete,
                constraint_name="voltage_compatible",
                prevents=prevents,
                uncertain=uncertain,
            )
            evaluate_constraint(
                compatible=temperature_ok,
                derivation_complete=temperature_complete,
                constraint_name="temperature_compatible",
                prevents=prevents,
                uncertain=uncertain,
            )
            if not new_part_lifecycle_active:
                prevents.append("lifecycle_active")

            if state == "unresolved":
                uncertain.append("semantic_acceptance")

            results.append(
                {
                    "new_part": new_part,
                    "old_part": old_part,
                    "bom_item": bom_item,
                    "context": context,
                    "voltage_compatible": voltage_ok,
                    "temperature_compatible": temperature_ok,
                    "new_part_lifecycle_active": new_part_lifecycle_active,
                    "old_part_lifecycle": old_part_lifecycle,
                    "semantic_state": state,
                    "prevents_viability": prevents,
                    "leaves_viability_uncertain": uncertain,
                }
            )

        output = {"task": "qualification_bottlenecks", "cases": results}
        OUTPUT_PATH.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    finally:
        world.close()


if __name__ == "__main__":
    main()
