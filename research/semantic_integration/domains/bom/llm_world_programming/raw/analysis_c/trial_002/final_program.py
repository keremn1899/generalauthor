#!/usr/bin/env python3
"""Report conflicting manufacturer and supplier voltage observations."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / "sources"


def number(value: str | int | float) -> int | float:
    """Parse a JSON number while retaining integral values as integers."""
    parsed = float(value)
    return int(parsed) if parsed.is_integer() else parsed


def read_csv(name: str) -> list[dict[str, str]]:
    with (SOURCES / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def is_eligible(part: dict[str, str], bom: dict[str, str]) -> bool:
    """Apply all represented type, rating, and lifecycle requirements."""
    return (
        part["part_type"] == bom["part_type"]
        and number(part["rated_voltage_v"]) == number(bom["required_voltage_v"])
        and number(part["min_temp_c"]) <= number(bom["min_temp_c"])
        and number(part["max_temp_c"]) >= number(bom["max_temp_c"])
        and part["lifecycle"] == "active"
    )


def build_result() -> dict[str, Any]:
    manufacturer_rows = read_csv("manufacturer.csv")
    bom_rows = read_csv("bom.csv")
    with (SOURCES / "suppliers.json").open(encoding="utf-8") as handle:
        listings = json.load(handle)["listings"]

    parts = {row["part_number"]: row for row in manufacturer_rows}
    observations: dict[str, list[tuple[int | float, str]]] = defaultdict(list)
    listings_by_part: dict[str, list[dict[str, str]]] = defaultdict(list)

    for part_number, part in parts.items():
        observations[part_number].append(
            (number(part["rated_voltage_v"]), "manufacturer.csv")
        )

    for listing in listings:
        part_number = listing["manufacturer_part_number"]
        listings_by_part[part_number].append(
            {
                "listing": f"listing:{listing['sku']}",
                "availability": listing["availability"],
            }
        )
        if listing.get("observed_voltage_v") is not None:
            observations[part_number].append(
                (number(listing["observed_voltage_v"]), "suppliers.json")
            )

    conflicts: list[dict[str, Any]] = []
    for part_number, observed in observations.items():
        values = sorted({volts for volts, _source in observed})
        if len(values) < 2 or part_number not in parts:
            continue

        part = parts[part_number]
        matching_bom_items = sorted(
            f"bom:{bom['bom_item']}"
            for bom in bom_rows
            if bom["part_type"] == part["part_type"]
        )
        eligible_bom_items = sorted(
            f"bom:{bom['bom_item']}"
            for bom in bom_rows
            if is_eligible(part, bom)
        )

        conflicts.append(
            {
                "part": f"part:{part_number}",
                "property": "rated_voltage_v",
                "values": values,
                "matching_bom_items": matching_bom_items,
                "eligible_bom_items": eligible_bom_items,
                "listings_of_part": sorted(
                    listings_by_part[part_number],
                    key=lambda item: (item["listing"], item["availability"]),
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

    conflicts.sort(key=lambda item: (item["part"], item["property"]))
    return {"task": "spec_conflict_review", "conflicts": conflicts}


def main() -> None:
    result = build_result()
    (ROOT / "output.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
