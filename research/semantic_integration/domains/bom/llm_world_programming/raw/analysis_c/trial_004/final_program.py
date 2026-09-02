#!/usr/bin/env python3
"""Report conflicting represented part voltages and their BOM impact."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / "sources"


def parse_number(value: str | int | float) -> int | float:
    """Parse a number while preserving integral values as JSON integers."""
    parsed = float(value)
    return int(parsed) if parsed.is_integer() else parsed


def read_csv(name: str) -> list[dict[str, str]]:
    with (SOURCES / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def is_eligible(part: dict[str, str], bom: dict[str, str]) -> bool:
    return (
        part["part_type"] == bom["part_type"]
        and parse_number(part["rated_voltage_v"])
        == parse_number(bom["required_voltage_v"])
        and parse_number(part["min_temp_c"]) <= parse_number(bom["min_temp_c"])
        and parse_number(part["max_temp_c"]) >= parse_number(bom["max_temp_c"])
        and part["lifecycle"] != "discontinued"
    )


def analyze() -> dict[str, Any]:
    manufacturer_rows = read_csv("manufacturer.csv")
    bom_rows = read_csv("bom.csv")
    supplier_document = json.loads(
        (SOURCES / "suppliers.json").read_text(encoding="utf-8")
    )
    listings = supplier_document["listings"]

    parts = {row["part_number"]: row for row in manufacturer_rows}
    observations: dict[str, list[tuple[int | float, str]]] = defaultdict(list)

    for part_number, part in parts.items():
        observations[part_number].append(
            (parse_number(part["rated_voltage_v"]), "manufacturer.csv")
        )

    for listing in listings:
        if "observed_voltage_v" in listing:
            observations[listing["manufacturer_part_number"]].append(
                (parse_number(listing["observed_voltage_v"]), "suppliers.json")
            )

    conflicts: list[dict[str, Any]] = []
    for part_number, part_observations in observations.items():
        values = sorted({volts for volts, _ in part_observations})
        if len(values) < 2 or part_number not in parts:
            continue

        part = parts[part_number]
        matching_boms = [
            row for row in bom_rows if row["part_type"] == part["part_type"]
        ]
        related_listings = [
            {
                "listing": f"listing:{listing['sku']}",
                "availability": listing["availability"],
            }
            for listing in listings
            if listing["manufacturer_part_number"] == part_number
        ]
        unique_observations = sorted(
            set(part_observations), key=lambda observation: (observation[0], observation[1])
        )

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
                    if is_eligible(part, row)
                ),
                "listings_of_part": sorted(
                    related_listings, key=lambda row: row["listing"]
                ),
                "observation_sources": [
                    {"volts": volts, "source": source}
                    for volts, source in unique_observations
                ],
                "review": "conflicting_rated_voltage_observations",
            }
        )

    conflicts.sort(key=lambda conflict: (conflict["part"], conflict["property"]))
    return {"task": "spec_conflict_review", "conflicts": conflicts}


def main() -> None:
    output = analyze()
    (ROOT / "output.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
