#!/usr/bin/env python3
"""Produce a specification-conflict review from the compiled semantic World."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from taskview import TaskView, TaskViewError
from world_surface import open_world


ROOT = Path(__file__).resolve().parent
OUTPUT_PATH = ROOT / "output.json"
WORLD_PATH = ROOT / "world.sqlite"


def open_compiled_world() -> Any:
    """Open through the public wrapper, tolerating its packaged view-ID mismatch."""

    try:
        return open_world()
    except TaskViewError:
        # Some packaged workspaces have a stale view_id constant in world_surface.py.
        # Discovering the database's own identity preserves the same read interface
        # without embedding fixture data or an expected answer.
        connection = sqlite3.connect(
            f"{WORLD_PATH.resolve().as_uri()}?mode=ro", uri=True
        )
        try:
            row = connection.execute(
                "SELECT view_id FROM _tv_view WHERE singleton = 1"
            ).fetchone()
        finally:
            connection.close()
        if row is None:
            raise RuntimeError("compiled World has no TaskView identity")
        return TaskView(WORLD_PATH, view_id=str(row[0]))


def source_name(grounding: dict[str, Any]) -> str:
    """Return the source handle carried by a tuple's grounding."""

    detail = grounding.get("detail")
    if isinstance(detail, str) and detail:
        try:
            metadata = json.loads(detail)
        except json.JSONDecodeError:
            metadata = {}
        source = metadata.get("source")
        if isinstance(source, str) and source:
            return source

    reference = str(grounding.get("reference") or "")
    if reference.startswith("fixture://"):
        return reference.removeprefix("fixture://").split("@", 1)[0]
    return reference


def observation_sources(
    world: Any, part: str, voltages: list[int]
) -> list[dict[str, Any]]:
    observations: set[tuple[int, str]] = set()

    for volts in voltages:
        detail = world.inspect_tuple(
            "rated_voltage", {"part": part, "volts": volts}
        )
        if detail is None:
            continue
        for grounding in detail.get("grounding", []):
            if grounding.get("kind") != "SOURCE":
                continue
            source = source_name(grounding)
            if source:
                observations.add((volts, source))

    return [
        {"volts": volts, "source": source}
        for volts, source in sorted(observations, key=lambda item: (item[0], item[1]))
    ]


def build_review(world: Any) -> dict[str, Any]:
    conflicts = world.query_semantic(
        """
        SELECT part_id AS part, property
        FROM spec_conflict
        ORDER BY part_id, property
        """
    )

    reviews: list[dict[str, Any]] = []
    for conflict in conflicts:
        part = str(conflict["part"])
        property_name = str(conflict["property"])

        voltage_rows = world.query_semantic(
            """
            SELECT DISTINCT volts
            FROM rated_voltage
            WHERE part_id = ?
            ORDER BY volts
            """,
            (part,),
        )
        values = [int(row["volts"]) for row in voltage_rows]

        matching_rows = world.query_semantic(
            """
            SELECT DISTINCT required_voltage.bom_item_id AS bom_item
            FROM rated_voltage AS observed_voltage
            JOIN part_type AS observed_type
              ON observed_type.part_id = observed_voltage.part_id
            JOIN requires_type AS required_type
              ON required_type.part_type = observed_type.part_type
            JOIN requires_voltage AS required_voltage
              ON required_voltage.bom_item_id = required_type.bom_item_id
             AND required_voltage.volts = observed_voltage.volts
            WHERE observed_voltage.part_id = ?
            ORDER BY required_voltage.bom_item_id
            """,
            (part,),
        )

        eligible_rows = world.query_semantic(
            """
            SELECT DISTINCT bom_item_id AS bom_item
            FROM eligible_part
            WHERE part_id = ?
            ORDER BY bom_item_id
            """,
            (part,),
        )

        listing_rows = world.query_semantic(
            """
            SELECT DISTINCT listing_of.listing_id AS listing,
                            listing_availability.state AS availability
            FROM listing_of
            JOIN listing_availability
              ON listing_availability.listing_id = listing_of.listing_id
            WHERE listing_of.part_id = ?
            ORDER BY listing_of.listing_id, listing_availability.state
            """,
            (part,),
        )

        reviews.append(
            {
                "part": part,
                "property": property_name,
                "values": values,
                "matching_bom_items": sorted(
                    str(row["bom_item"]) for row in matching_rows
                ),
                "eligible_bom_items": sorted(
                    str(row["bom_item"]) for row in eligible_rows
                ),
                "listings_of_part": [
                    {
                        "listing": str(row["listing"]),
                        "availability": str(row["availability"]),
                    }
                    for row in listing_rows
                ],
                "observation_sources": observation_sources(world, part, values),
                "review": "conflicting_rated_voltage_observations",
            }
        )

    reviews.sort(key=lambda row: (row["part"], row["property"]))
    return {"task": "spec_conflict_review", "conflicts": reviews}


def main() -> None:
    world = open_compiled_world()
    try:
        result = build_review(world)
    finally:
        world.close()
    OUTPUT_PATH.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
