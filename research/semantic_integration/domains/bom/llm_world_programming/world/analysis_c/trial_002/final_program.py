#!/usr/bin/env python3
"""Produce the represented BOM specification-conflict review."""

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


class FallbackWorld:
    """Expose the needed World operations when the facade has a stale view ID."""

    def __init__(self, taskview: TaskView) -> None:
        self._taskview = taskview

    def query_semantic(
        self, sql: str, parameters: tuple[Any, ...] = ()
    ) -> list[dict[str, Any]]:
        return self._taskview.query_semantic(sql, parameters)

    def inspect_tuple(
        self, relation: str, values: dict[str, Any]
    ) -> dict[str, Any] | None:
        return self._taskview.inspect_tuple(relation, values)

    def close(self) -> None:
        self._taskview.close()


def open_compiled_world() -> Any:
    """Use the documented facade, with a fallback for its bundled ID mismatch."""

    try:
        return open_world()
    except TaskViewError as error:
        if "database belongs to TaskView" not in str(error):
            raise

        uri = DB_PATH.resolve().as_uri() + "?mode=ro"
        with sqlite3.connect(uri, uri=True) as database:
            row = database.execute(
                "SELECT view_id FROM _tv_view WHERE singleton = 1"
            ).fetchone()
        if row is None:
            raise RuntimeError("compiled World has no TaskView identity") from error
        return FallbackWorld(TaskView(DB_PATH, view_id=str(row[0])))


def grounding_source(grounding: dict[str, Any]) -> str:
    """Extract the represented source name from a grounding pointer."""

    try:
        detail = json.loads(grounding.get("detail", ""))
    except (json.JSONDecodeError, TypeError):
        detail = {}
    if isinstance(detail, dict) and detail.get("source"):
        return str(detail["source"])
    return str(grounding["reference"])


def build_result(world: Any) -> dict[str, Any]:
    conflict_rows = world.query_semantic(
        """
        SELECT part_id AS part, property
        FROM spec_conflict
        ORDER BY part_id, property
        """
    )
    conflicts: list[dict[str, Any]] = []

    for conflict_row in conflict_rows:
        part = str(conflict_row["part"])
        property_name = str(conflict_row["property"])

        voltage_rows = world.query_semantic(
            """
            SELECT volts
            FROM rated_voltage
            WHERE part_id = ?
            ORDER BY volts
            """,
            (part,),
        )
        values = sorted({row["volts"] for row in voltage_rows})

        # A BOM item matches the conflicted part's represented part type.
        matching_rows = world.query_semantic(
            """
            SELECT DISTINCT requirement.bom_item_id AS bom_item
            FROM requires_type AS requirement
            JOIN part_type AS classification
              ON classification.part_type = requirement.part_type
            WHERE classification.part_id = ?
            ORDER BY requirement.bom_item_id
            """,
            (part,),
        )
        matching_bom_items = sorted(
            {str(row["bom_item"]) for row in matching_rows}
        )

        eligible_rows = world.query_semantic(
            """
            SELECT bom_item_id AS bom_item
            FROM eligible_part
            WHERE part_id = ?
            ORDER BY bom_item_id
            """,
            (part,),
        )
        eligible_bom_items = sorted(
            {str(row["bom_item"]) for row in eligible_rows}
        )

        listing_rows = world.query_semantic(
            """
            SELECT relation.listing_id AS listing,
                   availability.state AS availability
            FROM listing_of AS relation
            JOIN listing_availability AS availability
              ON availability.listing_id = relation.listing_id
            WHERE relation.part_id = ?
            ORDER BY relation.listing_id, availability.state
            """,
            (part,),
        )
        listings_of_part = sorted(
            (
                {
                    "listing": str(row["listing"]),
                    "availability": str(row["availability"]),
                }
                for row in listing_rows
            ),
            key=lambda row: (row["listing"], row["availability"]),
        )

        observation_sources: list[dict[str, Any]] = []
        for voltage_row in voltage_rows:
            volts = voltage_row["volts"]
            detail = world.inspect_tuple(
                "rated_voltage", {"part": part, "volts": volts}
            )
            if detail is None:
                continue
            for grounding in detail.get("grounding", []):
                if grounding.get("kind") == "SOURCE":
                    observation_sources.append(
                        {
                            "volts": volts,
                            "source": grounding_source(grounding),
                        }
                    )

        observation_sources = list(
            {
                (row["volts"], row["source"]): row
                for row in observation_sources
            }.values()
        )
        observation_sources.sort(key=lambda row: (row["volts"], row["source"]))

        conflicts.append(
            {
                "part": part,
                "property": property_name,
                "values": values,
                "matching_bom_items": matching_bom_items,
                "eligible_bom_items": eligible_bom_items,
                "listings_of_part": listings_of_part,
                "observation_sources": observation_sources,
                "review": "conflicting_rated_voltage_observations",
            }
        )

    conflicts.sort(key=lambda row: (row["part"], row["property"]))
    return {"task": "spec_conflict_review", "conflicts": conflicts}


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
