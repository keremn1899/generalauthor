#!/usr/bin/env python3
"""Find conflicting part-voltage observations in the workspace sources."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / "sources"


def read_csv(name: str) -> list[dict[str, str]]:
    with (SOURCES / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def as_int(row: dict[str, str], field: str) -> int:
    return int(row[field])


def is_eligible(part: dict[str, str], bom: dict[str, str]) -> bool:
    return (
        part["part_type"] == bom["part_type"]
        and as_int(part, "rated_voltage_v") == as_int(bom, "required_voltage_v")
        and as_int(part, "min_temp_c") <= as_int(bom, "min_temp_c")
        and as_int(part, "max_temp_c") >= as_int(bom, "max_temp_c")
        and part["lifecycle"] != "discontinued"
    )


def build_result() -> dict[str, Any]:
    manufacturer_rows = read_csv("manufacturer.csv")
    bom_rows = read_csv("bom.csv")
    supplier_document = json.loads(
        (SOURCES / "suppliers.json").read_text(encoding="utf-8")
    )
    listings = supplier_document["listings"]

    parts = {row["part_number"]: row for row in manufacturer_rows}
    observations: dict[str, set[tuple[int, str]]] = defaultdict(set)

    for part_number, part in parts.items():
        observations[part_number].add(
            (as_int(part, "rated_voltage_v"), "manufacturer.csv")
        )

    for listing in listings:
        if "observed_voltage_v" in listing:
            observations[listing["manufacturer_part_number"]].add(
                (int(listing["observed_voltage_v"]), "suppliers.json")
            )

    conflicts: list[dict[str, Any]] = []
    for part_number, part_observations in observations.items():
        values = sorted({volts for volts, _source in part_observations})
        if len(values) < 2:
            continue

        part = parts[part_number]
        matching = [
            bom for bom in bom_rows if bom["part_type"] == part["part_type"]
        ]
        listings_of_part = [
            {
                "listing": f'listing:{listing["sku"]}',
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
                    f'bom:{bom["bom_item"]}' for bom in matching
                ),
                "eligible_bom_items": sorted(
                    f'bom:{bom["bom_item"]}'
                    for bom in matching
                    if is_eligible(part, bom)
                ),
                "listings_of_part": sorted(
                    listings_of_part, key=lambda item: item["listing"]
                ),
                "observation_sources": [
                    {"volts": volts, "source": source}
                    for volts, source in sorted(part_observations)
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
