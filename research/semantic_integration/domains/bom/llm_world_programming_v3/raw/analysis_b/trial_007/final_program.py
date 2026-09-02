#!/usr/bin/env python3
"""Compute qualification bottlenecks from the authoritative source files."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / "sources"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def identifier(kind: str, value: str) -> str:
    return f"{kind}:{value}"


def replacement_reviews(notes: str) -> list[dict[str, object]]:
    """Extract candidate pairs and their context-scoped semantic judgments."""
    sections = re.split(r"(?m)^##\s+", notes)
    reviews: list[dict[str, object]] = []

    for section in sections:
        pair = re.search(
            r"Candidate:\s*`([^`]+)`\s+replaces\s+`([^`]+)`", section
        )
        if pair is None:
            continue

        contexts = set(
            re.findall(r"`([^`]+)`\s+context\b", section, flags=re.IGNORECASE)
        )
        normalized = " ".join(section.lower().split())
        positive_judgment = any(
            phrase in normalized
            for phrase in (
                "acceptable substitute",
                "accepted substitute",
                "preferred fallback",
                "approved substitute",
            )
        )
        reviews.append(
            {
                "new_part": pair.group(1),
                "old_part": pair.group(2),
                "contexts": contexts,
                "positive_judgment": positive_judgment,
            }
        )

    return reviews


def main() -> None:
    manufacturer_rows = read_csv(SOURCES / "manufacturer.csv")
    bom_rows = read_csv(SOURCES / "bom.csv")
    notes = (SOURCES / "engineering_notes.md").read_text(encoding="utf-8")
    with (SOURCES / "suppliers.json").open(encoding="utf-8") as handle:
        supplier_data = json.load(handle)

    parts = {row["part_number"]: row for row in manufacturer_rows}
    represented_parts = {
        listing["manufacturer_part_number"]
        for listing in supplier_data["listings"]
    }

    cases: list[dict[str, object]] = []
    for review in replacement_reviews(notes):
        new_number = str(review["new_part"])
        old_number = str(review["old_part"])

        # A represented replacement has manufacturer data and at least one
        # supplier listing for both sides of its explicit replacement pair.
        if (
            new_number not in parts
            or old_number not in parts
            or new_number not in represented_parts
            or old_number not in represented_parts
        ):
            continue

        new_part = parts[new_number]
        old_part = parts[old_number]
        if new_part["part_type"] != old_part["part_type"]:
            continue

        for bom in bom_rows:
            if bom["part_type"] != old_part["part_type"]:
                continue

            required_voltage = float(bom["required_voltage_v"])
            required_min_temp = float(bom["min_temp_c"])
            required_max_temp = float(bom["max_temp_c"])

            voltage_compatible = float(new_part["rated_voltage_v"]) >= required_voltage
            temperature_compatible = (
                float(new_part["min_temp_c"]) <= required_min_temp
                and float(new_part["max_temp_c"]) >= required_max_temp
            )
            lifecycle_active = new_part["lifecycle"].strip().lower() == "active"

            context_reviewed = bom["deployment_environment"] in review["contexts"]
            if context_reviewed and review["positive_judgment"]:
                semantic_state = "accepted"
            elif context_reviewed:
                semantic_state = "unresolved"
            else:
                semantic_state = "not_established"

            prevents: list[str] = []
            if not voltage_compatible:
                prevents.append("voltage_compatible")
            if not temperature_compatible:
                prevents.append("temperature_compatible")
            if not lifecycle_active:
                prevents.append("lifecycle_active")

            uncertain: list[str] = []
            if semantic_state != "accepted":
                uncertain.append("semantic_acceptance")

            cases.append(
                {
                    "new_part": identifier("part", new_number),
                    "old_part": identifier("part", old_number),
                    "bom_item": identifier("bom", bom["bom_item"]),
                    "context": identifier("context", bom["deployment_environment"]),
                    "voltage_compatible": voltage_compatible,
                    "temperature_compatible": temperature_compatible,
                    "new_part_lifecycle_active": lifecycle_active,
                    "old_part_lifecycle": old_part["lifecycle"],
                    "semantic_state": semantic_state,
                    "prevents_viability": prevents,
                    "leaves_viability_uncertain": uncertain,
                }
            )

    cases.sort(
        key=lambda case: (
            case["new_part"],
            case["old_part"],
            case["bom_item"],
            case["context"],
        )
    )
    result = {"task": "qualification_bottlenecks", "cases": cases}
    with (ROOT / "output.json").open("w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")


if __name__ == "__main__":
    main()
