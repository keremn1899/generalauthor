"""RAW C: spec-conflict engineering review from manufacturer vs supplier voltages."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from research.semantic_integration.domains.bom.world_programming.raw.io import (
    bom_id,
    eligible,
    listing_id,
    part_id,
    read_bom,
    read_manufacturer,
    read_suppliers,
)
from research.taskview_bom.experiment import FIXTURES


def run(source_dir: Path = FIXTURES) -> dict[str, Any]:
    parts = {row["part_number"]: row for row in read_manufacturer(source_dir / "manufacturer.csv")}
    listings = read_suppliers(source_dir / "suppliers.json")
    bom_rows = read_bom(source_dir / "bom.csv")

    voltages: dict[str, set[int]] = defaultdict(set)
    for part_number, part in parts.items():
        voltages[part_number].add(part["rated_voltage_v"])
    for listing in listings:
        if "observed_voltage_v" in listing:
            voltages[listing["manufacturer_part_number"]].add(listing["observed_voltage_v"])

    conflicts: list[dict[str, Any]] = []
    for part_number, values in sorted(voltages.items()):
        if len(values) < 2:
            continue
        part = parts[part_number]
        matching = [bom for bom in bom_rows if bom["part_type"] == part["part_type"]]
        related_listings = [
            {
                "listing": listing_id(item["sku"]),
                "availability": item["availability"],
            }
            for item in listings
            if item["manufacturer_part_number"] == part_number
        ]
        observation_sources = [
            {"volts": part["rated_voltage_v"], "source": "manufacturer.csv"}
        ]
        for item in listings:
            if item["manufacturer_part_number"] == part_number and "observed_voltage_v" in item:
                observation_sources.append(
                    {
                        "volts": item["observed_voltage_v"],
                        "source": "suppliers.json",
                    }
                )
        observation_sources = sorted(
            { (row["volts"], row["source"]): row for row in observation_sources }.values(),
            key=lambda row: (row["volts"], row["source"]),
        )
        conflicts.append(
            {
                "part": part_id(part_number),
                "property": "rated_voltage_v",
                "values": sorted(values),
                "matching_bom_items": [bom_id(item["bom_item"]) for item in matching],
                "eligible_bom_items": [
                    bom_id(item["bom_item"])
                    for item in matching
                    if eligible(part, item)
                ],
                "listings_of_part": sorted(
                    related_listings, key=lambda row: row["listing"]
                ),
                "observation_sources": observation_sources,
                "review": "conflicting_rated_voltage_observations",
            }
        )
    return {"task": "spec_conflict_review", "conflicts": conflicts}
