#!/usr/bin/env python3
"""Compute qualification bottlenecks from the compiled semantic World."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from taskview import TaskView
from taskview.model import TaskViewError
from world_surface import DB_PATH, World, open_world


OUTPUT_PATH = Path(__file__).resolve().parent / "output.json"


def open_compiled_world() -> World:
    """Open the World, tolerating a mismatched workspace adapter view ID."""

    try:
        return open_world()
    except TaskViewError as error:
        # This workspace's adapter names a different view than the database
        # metadata. Recover the database's own identity without changing it,
        # then retain the documented World query surface.
        if "database belongs to TaskView" not in str(error):
            raise
        uri = DB_PATH.resolve().as_uri() + "?mode=ro"
        with sqlite3.connect(uri, uri=True) as database:
            row = database.execute(
                "SELECT view_id FROM _tv_view WHERE singleton = 1"
            ).fetchone()
        if row is None:
            raise RuntimeError("compiled World has no TaskView identity") from error

        world = World.__new__(World)
        world.path = DB_PATH
        world._tv = TaskView(DB_PATH, view_id=str(row[0]))
        world._origins = {}
        return world


def tuple_set(
    world: World, relation: str, first: str, second: str
) -> set[tuple[str, str]]:
    rows = world.query_semantic(f"SELECT {first}, {second} FROM {relation}")
    return {(str(row[first]), str(row[second])) for row in rows}


def missing_is_negative(world: World, relation: str) -> bool:
    """Whether absence from a derived relation is a justified negative."""

    receipt = world.latest_completeness(relation)
    return bool(
        receipt
        and receipt["status"] == "COMPLETE"
        and not world.is_stale(relation)
    )


def compute_cases(world: World) -> list[dict[str, Any]]:
    relevant = world.query_semantic(
        """
        SELECT DISTINCT
            candidate.new_part_id,
            candidate.old_part_id,
            requirement.bom_item_id,
            deployment.environment_id
        FROM candidate_replacement AS candidate
        JOIN part_type AS old_type
          ON old_type.part_id = candidate.old_part_id
        JOIN requires_type AS requirement
          ON requirement.part_type = old_type.part_type
        JOIN deployment_environment AS deployment
          ON deployment.bom_item_id = requirement.bom_item_id
        """
    )

    voltage = tuple_set(
        world, "voltage_compatible", "part_id", "bom_item_id"
    )
    temperature = tuple_set(
        world, "temperature_compatible", "part_id", "bom_item_id"
    )
    accepted_contexts = {
        (
            str(row["new_part_id"]),
            str(row["old_part_id"]),
            str(row["context_id"]),
        )
        for row in world.query_semantic(
            """
            SELECT new_part_id, old_part_id, context_id
            FROM acceptable_replacement
            """
        )
    }

    lifecycle_rows = world.query_semantic("SELECT part_id, state FROM lifecycle")
    lifecycle_by_part: dict[str, set[str]] = {}
    for row in lifecycle_rows:
        lifecycle_by_part.setdefault(str(row["part_id"]), set()).add(str(row["state"]))

    unresolved = {
        (
            str(obligation["values"]["new_part"]),
            str(obligation["values"]["old_part"]),
            str(obligation["values"]["context"]),
        )
        for obligation in world.obligations()
        if obligation.get("relation") == "acceptable_replacement"
        and {"new_part", "old_part", "context"}
        <= set(obligation.get("values", {}))
    }

    voltage_closed = missing_is_negative(world, "voltage_compatible")
    temperature_closed = missing_is_negative(world, "temperature_compatible")
    cases: list[dict[str, Any]] = []

    for row in relevant:
        new_part = str(row["new_part_id"])
        old_part = str(row["old_part_id"])
        bom_item = str(row["bom_item_id"])
        context = str(row["environment_id"])
        pair = (new_part, bom_item)
        semantic_key = (new_part, old_part, context)

        voltage_compatible = pair in voltage
        temperature_compatible = pair in temperature
        new_lifecycle_states = lifecycle_by_part.get(new_part, set())
        new_part_lifecycle_active = "active" in new_lifecycle_states
        old_lifecycle_states = lifecycle_by_part.get(old_part, set())
        old_part_lifecycle = (
            sorted(old_lifecycle_states)[0] if old_lifecycle_states else "unknown"
        )

        if semantic_key in accepted_contexts:
            semantic_state = "accepted"
        elif semantic_key in unresolved:
            semantic_state = "unresolved"
        else:
            semantic_state = "not_established"

        prevents: list[str] = []
        uncertain: list[str] = []

        if not voltage_compatible:
            (prevents if voltage_closed else uncertain).append(
                "voltage_compatible"
            )
        if not temperature_compatible:
            (prevents if temperature_closed else uncertain).append(
                "temperature_compatible"
            )
        if not new_part_lifecycle_active:
            (prevents if new_lifecycle_states else uncertain).append(
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
                "voltage_compatible": voltage_compatible,
                "temperature_compatible": temperature_compatible,
                "new_part_lifecycle_active": new_part_lifecycle_active,
                "old_part_lifecycle": old_part_lifecycle,
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
    return cases


def main() -> None:
    world = open_compiled_world()
    try:
        result = {
            "task": "qualification_bottlenecks",
            "cases": compute_cases(world),
        }
    finally:
        world.close()
    OUTPUT_PATH.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
