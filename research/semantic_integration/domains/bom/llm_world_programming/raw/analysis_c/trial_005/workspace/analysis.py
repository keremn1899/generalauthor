#!/usr/bin/env python3
"""Find conflicting represented voltage specifications and their BOM impact."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / "sources"


def number(value: str | int | float) -> int | float:
    """Convert source numbers while keeping integral values as JSON integers."""
    parsed = float(value)
    return int(parsed) if parsed.is_integer() else parsed


def read_csv(filename: str) -> list[dict[str, str]]:
    with (SOURCES / filename).open(encoding="utf-8", newline="") as source:
        return list(csv.DictReader(source))


def eligible(part: dict[str, str], bom_item: dict[str, str]) -> bool:
    """Return whether the manufacturer specification satisfies a BOM item."""
    return (
        part["part_type"] == bom_item["part_type"]
        and number(part["rated_voltage_v"])
        == number(bom_item["required_voltage_v"])
        and number(part["min_temp_c"]) <= number(bom_item["min_temp_c"])
        and number(part["max_temp_c"]) >= number(bom_item["max_temp_c"])
        and part["lifecycle"] != "discontinued"
    )


def analyze() -> dict[str, Any]:
    manufacturer_rows = read_csv("manufacturer.csv")
    bom_rows = read_csv("bom.csv")
    supplier_data = json.loads(
        (SOURCES / "suppliers.json").read_text(encoding="utf-8")
    )
    listings = supplier_data["listings"]
    parts = {row["part_number"]: row for row in manufacturer_rows}

    observations: dict[str, set[tuple[int | float, str]]] = defaultdict(set)
    for part_number, part in parts.items():
        observations[part_number].add(
            (number(part["rated_voltage_v"]), "manufacturer.csv")
        )
    for listing in listings:
        if "observed_voltage_v" in listing:
            observations[listing["manufacturer_part_number"]].add(
                (number(listing["observed_voltage_v"]), "suppliers.json")
            )

    conflicts: list[dict[str, Any]] = []
    for part_number, observed in observations.items():
        values = sorted({volts for volts, _source in observed})
        if len(values) < 2 or part_number not in parts:
            continue

        part = parts[part_number]
        matching_boms = [
            row for row in bom_rows if row["part_type"] == part["part_type"]
        ]
        part_listings = [
            {
                "listing": f"listing:{listing['sku']}",
                "availability": listing["availability"],
            }
            for listing in listings
            if listing["manufacturer_part_number"] == part_number
        ]

        conflicts.append(
            {
                "part": f"part:{part_number}",
                "property": "rated_voltage_v",
                "values": values,
                "matching_bom_items": sorted(
                    f"bom:{row['bom_item']}" for row in matching_boms
                ),
                "eligible_bom_items": sorted(
                    f"bom:{row['bom_item']}"
                    for row in matching_boms
                    if eligible(part, row)
                ),
                "listings_of_part": sorted(
                    part_listings, key=lambda row: row["listing"]
                ),
                "observation_sources": [
                    {"volts": volts, "source": source}
                    for volts, source in sorted(
                        observed, key=lambda item: (item[0], item[1])
                    )
                ],
                "review": "conflicting_rated_voltage_observations",
            }
        )

    conflicts.sort(key=lambda row: (row["part"], row["property"]))
    return {"task": "spec_conflict_review", "conflicts": conflicts}


def main() -> None:
    (ROOT / "output.json").write_text(
        json.dumps(analyze(), indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
