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


def parse_number(value: str | int | float) -> int | float:
    """Return a JSON-compatible number, using an integer when exact."""
    parsed = float(value)
    return int(parsed) if parsed.is_integer() else parsed


def read_csv(filename: str) -> list[dict[str, str]]:
    with (SOURCES / filename).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def is_eligible(part: dict[str, str], bom_item: dict[str, str]) -> bool:
    """Evaluate every machine-readable BOM requirement for a part."""
    return (
        part["part_type"] == bom_item["part_type"]
        and parse_number(part["rated_voltage_v"])
        == parse_number(bom_item["required_voltage_v"])
        and parse_number(part["min_temp_c"]) <= parse_number(bom_item["min_temp_c"])
        and parse_number(part["max_temp_c"]) >= parse_number(bom_item["max_temp_c"])
        and part["lifecycle"] != "discontinued"
    )


def analyze() -> dict[str, Any]:
    manufacturer_rows = read_csv("manufacturer.csv")
    bom_rows = read_csv("bom.csv")
    with (SOURCES / "suppliers.json").open(encoding="utf-8") as handle:
        supplier_listings = json.load(handle)["listings"]

    parts = {row["part_number"]: row for row in manufacturer_rows}
    observations: dict[str, list[tuple[int | float, str]]] = defaultdict(list)
    listings_by_part: dict[str, list[dict[str, str]]] = defaultdict(list)

    for part_number, part in parts.items():
        observations[part_number].append(
            (parse_number(part["rated_voltage_v"]), "manufacturer.csv")
        )

    for listing in supplier_listings:
        part_number = listing["manufacturer_part_number"]
        listings_by_part[part_number].append(
            {
                "listing": f"listing:{listing['sku']}",
                "availability": listing["availability"],
            }
        )
        if "observed_voltage_v" in listing:
            observations[part_number].append(
                (
                    parse_number(listing["observed_voltage_v"]),
                    "suppliers.json",
                )
            )

    conflicts: list[dict[str, Any]] = []
    for part_number, part in parts.items():
        observed = observations[part_number]
        values = sorted({volts for volts, _ in observed})
        if len(values) < 2:
            continue

        matching_bom_rows = [
            row for row in bom_rows if row["part_type"] == part["part_type"]
        ]
        conflicts.append(
            {
                "part": f"part:{part_number}",
                "property": "rated_voltage_v",
                "values": values,
                "matching_bom_items": sorted(
                    f"bom:{row['bom_item']}" for row in matching_bom_rows
                ),
                "eligible_bom_items": sorted(
                    f"bom:{row['bom_item']}"
                    for row in matching_bom_rows
                    if is_eligible(part, row)
                ),
                "listings_of_part": sorted(
                    listings_by_part[part_number],
                    key=lambda row: (row["listing"], row["availability"]),
                ),
                "observation_sources": [
                    {"volts": volts, "source": source}
                    for volts, source in sorted(
                        set(observed), key=lambda item: (item[0], item[1])
                    )
                ],
                "review": "conflicting_rated_voltage_observations",
            }
        )

    conflicts.sort(key=lambda row: (row["part"], row["property"]))
    return {"task": "spec_conflict_review", "conflicts": conflicts}


def main() -> None:
    output = analyze()
    (ROOT / "output.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
