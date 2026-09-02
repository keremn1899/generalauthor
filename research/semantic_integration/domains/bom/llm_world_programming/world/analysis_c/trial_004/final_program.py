#!/usr/bin/env python3
"""Build a specification-conflict review from the compiled semantic World."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from taskview import TaskView
from taskview.model import TaskViewError
from world_surface import DB_PATH, open_world


ROOT = Path(__file__).resolve().parent
OUTPUT_PATH = ROOT / "output.json"


def open_compiled_world() -> Any:
    """Use the public facade, recovering from a stale packaged view ID."""

    try:
        return open_world()
    except TaskViewError:
        uri = f"{DB_PATH.resolve().as_uri()}?mode=ro"
        with sqlite3.connect(uri, uri=True) as database:
            row = database.execute(
                "SELECT view_id FROM _tv_view WHERE singleton = 1"
            ).fetchone()
        if row is None:
            raise RuntimeError("compiled World has no TaskView identity")
        return TaskView(DB_PATH, view_id=str(row[0]))


def columns(world: Any, relation: str) -> dict[str, str]:
    return {
        role["name"]: role["column"]
        for role in world.relation_schema(relation)["roles"]
    }


def source_name(grounding: dict[str, Any]) -> str:
    """Return the source handle's human-readable file name."""

    try:
        source = json.loads(grounding.get("detail") or "{}").get("source")
    except (json.JSONDecodeError, AttributeError):
        source = None
    if source:
        return str(source)

    reference = str(grounding.get("reference") or "")
    return reference.removeprefix("fixture://").split("@", 1)[0]


def build_result(world: Any) -> dict[str, Any]:
    stale = set(world.stale_relations())
    required_derived = {"spec_conflict", "eligible_part"}
    if stale & required_derived:
        raise RuntimeError(
            f"required derived relations are stale: {sorted(stale & required_derived)}"
        )

    conflict = columns(world, "spec_conflict")
    voltage = columns(world, "rated_voltage")
    part_type = columns(world, "part_type")
    required_type = columns(world, "requires_type")
    required_voltage = columns(world, "requires_voltage")
    eligible = columns(world, "eligible_part")
    listing_of = columns(world, "listing_of")
    availability = columns(world, "listing_availability")

    conflict_rows = world.query_semantic(
        f"""
        SELECT {conflict['part']} AS part,
               {conflict['property']} AS property
        FROM spec_conflict
        """
    )

    reviews: list[dict[str, Any]] = []
    for conflict_row in conflict_rows:
        part = conflict_row["part"]
        prop = conflict_row["property"]
        if prop != "rated_voltage_v":
            raise RuntimeError(f"unsupported represented conflict property: {prop}")

        observations = world.query_semantic(
            f"""
            SELECT {voltage['volts']} AS volts
            FROM rated_voltage
            WHERE {voltage['part']} = ?
            """,
            (part,),
        )
        values = sorted({row["volts"] for row in observations})

        matching_rows = world.query_semantic(
            f"""
            SELECT DISTINCT requirement.{required_voltage['bom_item']} AS bom_item
            FROM requires_voltage AS requirement
            JOIN requires_type AS required_kind
              ON required_kind.{required_type['bom_item']}
               = requirement.{required_voltage['bom_item']}
            JOIN part_type AS actual_kind
              ON actual_kind.{part_type['part_type']}
               = required_kind.{required_type['part_type']}
            JOIN rated_voltage AS observation
              ON observation.{voltage['part']} = actual_kind.{part_type['part']}
             AND observation.{voltage['volts']}
               = requirement.{required_voltage['volts']}
            WHERE actual_kind.{part_type['part']} = ?
            """,
            (part,),
        )

        eligible_rows = world.query_semantic(
            f"""
            SELECT {eligible['bom_item']} AS bom_item
            FROM eligible_part
            WHERE {eligible['part']} = ?
            """,
            (part,),
        )

        listing_rows = world.query_semantic(
            f"""
            SELECT owned.{listing_of['listing']} AS listing,
                   status.{availability['state']} AS availability
            FROM listing_of AS owned
            JOIN listing_availability AS status
              ON status.{availability['listing']} = owned.{listing_of['listing']}
            WHERE owned.{listing_of['part']} = ?
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

        source_records: set[tuple[int | float, str]] = set()
        for volts in values:
            detail = world.inspect_tuple(
                "rated_voltage", {"part": part, "volts": volts}
            )
            if detail is None:
                continue
            for grounding in detail.get("grounding", []):
                if grounding.get("kind") == "SOURCE":
                    source = source_name(grounding)
                    if source:
                        source_records.add((volts, source))

        reviews.append(
            {
                "part": part,
                "property": prop,
                "values": values,
                "matching_bom_items": sorted(
                    {row["bom_item"] for row in matching_rows}
                ),
                "eligible_bom_items": sorted(
                    {row["bom_item"] for row in eligible_rows}
                ),
                "listings_of_part": listings,
                "observation_sources": [
                    {"volts": volts, "source": source}
                    for volts, source in sorted(source_records)
                ],
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
