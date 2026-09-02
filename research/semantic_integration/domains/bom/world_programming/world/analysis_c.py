"""WORLD C: spec-conflict review from compiled conflict and rating relations."""

from __future__ import annotations

import json
from typing import Any

from research.semantic_integration.core.kernel import SemanticWorld
from research.semantic_integration.domains.bom.world_programming.relation_rows import (
    relation_rows,
)


def _source_name(world: SemanticWorld, relation: str, values: dict[str, Any]) -> str | None:
    inspected = world.inspect_tuple(relation, values)
    if inspected is None:
        return None
    for ground in inspected.get("grounding", []):
        if ground["kind"] != "SOURCE":
            continue
        detail = json.loads(ground["detail"])
        return detail.get("source") or detail.get("native_handle")
    return None


def run(world: SemanticWorld, obligations: list[dict[str, Any]]) -> dict[str, Any]:
    del obligations
    conflicts_in = relation_rows(world, "spec_conflict")
    voltages = relation_rows(world, "rated_voltage")
    types = {row["part_id"]: row["part_type"] for row in relation_rows(world, "part_type")}
    required = relation_rows(world, "requires_type")
    eligible = {
        (row["part_id"], row["bom_item_id"])
        for row in relation_rows(world, "eligible_part")
    }
    listings = relation_rows(world, "listing_of")
    availability = {
        row["listing_id"]: row["state"]
        for row in relation_rows(world, "listing_availability")
    }

    by_part: dict[str, list[int]] = {}
    for row in voltages:
        by_part.setdefault(row["part_id"], []).append(int(row["volts"]))

    conflicts: list[dict[str, Any]] = []
    for row in conflicts_in:
        part = row["part_id"]
        values = sorted(set(by_part.get(part, [])))
        part_type = types[part]
        matching = [
            item["bom_item_id"]
            for item in required
            if item["part_type"] == part_type
        ]
        related = [
            {
                "listing": item["listing_id"],
                "availability": availability.get(item["listing_id"], "unknown"),
            }
            for item in listings
            if item["part_id"] == part
        ]
        conflicts.append(
            {
                "part": part,
                "property": row["property"],
                "values": values,
                "matching_bom_items": sorted(matching),
                "eligible_bom_items": sorted(
                    bom for bom in matching if (part, bom) in eligible
                ),
                "listings_of_part": sorted(related, key=lambda item: row_key(item)),
                "review": "conflicting_rated_voltage_observations",
                "observation_sources": sorted(
                    [
                        {
                            "volts": volts,
                            "source": _source_name(
                                world,
                                "rated_voltage",
                                {"part": part, "volts": volts},
                            ),
                        }
                        for volts in values
                    ],
                    key=lambda item: (item["volts"], item["source"] or ""),
                ),
            }
        )
    conflicts.sort(key=lambda item: (item["part"], item["property"]))
    return {"task": "spec_conflict_review", "conflicts": conflicts}


def row_key(item: dict[str, str]) -> str:
    return item["listing"]
