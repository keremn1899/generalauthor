#!/usr/bin/env python3
"""Produce the specification-conflict review from the compiled semantic World."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from taskview import TaskView


ROOT = Path(__file__).resolve().parent
WORLD_PATH = ROOT / "world.sqlite"
OUTPUT_PATH = ROOT / "output.json"


def open_compiled_world() -> TaskView:
    """Open the packaged TaskView using the identity stored in the database.

    The workspace's world_surface.py currently contains a different fixture ID,
    so reading the database's own identity avoids coupling this analysis to
    either identifier.
    """

    uri = f"{WORLD_PATH.resolve().as_uri()}?mode=ro"
    with sqlite3.connect(uri, uri=True) as database:
        row = database.execute(
            "SELECT view_id FROM _tv_view WHERE singleton = 1"
        ).fetchone()
    if row is None:
        raise RuntimeError("compiled World has no TaskView identity")
    return TaskView(WORLD_PATH, view_id=str(row[0]))


def relation_columns(world: TaskView, relation: str) -> dict[str, str]:
    return {
        role["name"]: role["column"]
        for role in world.relation_schema(relation)["roles"]
    }


def source_name(grounding: dict[str, Any]) -> str:
    detail = grounding.get("detail", "")
    if detail:
        try:
            source = json.loads(detail).get("source")
            if source:
                return str(source)
        except (json.JSONDecodeError, AttributeError):
            pass

    reference = str(grounding.get("reference", ""))
    if reference.startswith("fixture://"):
        reference = reference.removeprefix("fixture://")
    return reference.split("@", 1)[0]


def build_result(world: TaskView) -> dict[str, Any]:
    conflict_columns = relation_columns(world, "spec_conflict")
    voltage_columns = relation_columns(world, "rated_voltage")
    type_columns = relation_columns(world, "part_type")
    required_type_columns = relation_columns(world, "requires_type")
    required_voltage_columns = relation_columns(world, "requires_voltage")
    eligible_columns = relation_columns(world, "eligible_part")
    listing_columns = relation_columns(world, "listing_of")
    availability_columns = relation_columns(world, "listing_availability")

    conflicts = world.query_semantic(
        f"""
        SELECT
            {conflict_columns['part']} AS part,
            {conflict_columns['property']} AS property
        FROM spec_conflict
        """
    )

    reviews: list[dict[str, Any]] = []
    for conflict in conflicts:
        part = conflict["part"]

        observations = world.query_semantic(
            f"""
            SELECT {voltage_columns['volts']} AS volts
            FROM rated_voltage
            WHERE {voltage_columns['part']} = ?
            """,
            (part,),
        )
        values = sorted({row["volts"] for row in observations})

        matching_rows = world.query_semantic(
            f"""
            SELECT DISTINCT rv.{required_voltage_columns['bom_item']} AS bom_item
            FROM requires_voltage AS rv
            JOIN requires_type AS rt
              ON rt.{required_type_columns['bom_item']}
               = rv.{required_voltage_columns['bom_item']}
            JOIN part_type AS pt
              ON pt.{type_columns['part_type']}
               = rt.{required_type_columns['part_type']}
            JOIN rated_voltage AS observed
              ON observed.{voltage_columns['part']} = pt.{type_columns['part']}
             AND observed.{voltage_columns['volts']}
               = rv.{required_voltage_columns['volts']}
            WHERE pt.{type_columns['part']} = ?
            """,
            (part,),
        )
        matching_bom_items = sorted({row["bom_item"] for row in matching_rows})

        eligible_rows = world.query_semantic(
            f"""
            SELECT {eligible_columns['bom_item']} AS bom_item
            FROM eligible_part
            WHERE {eligible_columns['part']} = ?
            """,
            (part,),
        )
        eligible_bom_items = sorted({row["bom_item"] for row in eligible_rows})

        listing_rows = world.query_semantic(
            f"""
            SELECT
                lo.{listing_columns['listing']} AS listing,
                availability.{availability_columns['state']} AS availability
            FROM listing_of AS lo
            JOIN listing_availability AS availability
              ON availability.{availability_columns['listing']}
               = lo.{listing_columns['listing']}
            WHERE lo.{listing_columns['part']} = ?
            """,
            (part,),
        )
        listings = sorted(
            (
                {
                    "listing": row["listing"],
                    "availability": row["availability"],
                }
                for row in listing_rows
            ),
            key=lambda row: (row["listing"], row["availability"]),
        )

        observation_sources: list[dict[str, Any]] = []
        for volts in values:
            detail = world.inspect_tuple(
                "rated_voltage", {"part": part, "volts": volts}
            )
            if detail is None:
                continue
            sources = {
                source_name(ground)
                for ground in detail.get("grounding", [])
                if ground.get("kind") == "SOURCE"
            }
            observation_sources.extend(
                {"volts": volts, "source": source}
                for source in sources
                if source
            )
        observation_sources.sort(key=lambda row: (row["volts"], row["source"]))

        reviews.append(
            {
                "part": part,
                "property": conflict["property"],
                "values": values,
                "matching_bom_items": matching_bom_items,
                "eligible_bom_items": eligible_bom_items,
                "listings_of_part": listings,
                "observation_sources": observation_sources,
                "review": "conflicting_rated_voltage_observations",
            }
        )

    reviews.sort(key=lambda row: (row["part"], row["property"]))
    return {"task": "spec_conflict_review", "conflicts": reviews}


def main() -> None:
    world = open_compiled_world()
    try:
        result = build_result(world)
    finally:
        world.close()
    OUTPUT_PATH.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
