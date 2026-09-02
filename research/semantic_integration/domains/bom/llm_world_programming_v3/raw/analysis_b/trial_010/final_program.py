#!/usr/bin/env python3
"""Compute qualification bottlenecks from the authoritative source files."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / "sources"


def read_csv(name: str, key: str) -> dict[str, dict[str, str]]:
    with (SOURCES / name).open(newline="", encoding="utf-8") as source:
        return {row[key]: row for row in csv.DictReader(source)}


def identifier(kind: str, value: str) -> str:
    return f"{kind}:{value}"


def note_sections(text: str) -> list[str]:
    """Split the notes into ER sections while excluding the introduction."""
    return [
        section
        for section in re.split(r"(?=^##\s+ER-\d+\s*$)", text, flags=re.MULTILINE)
        if re.search(r"^##\s+ER-\d+\s*$", section, flags=re.MULTILINE)
    ]


def candidate_relationship(section: str) -> tuple[str, str] | None:
    match = re.search(
        r"Candidate:\s*`([^`]+)`\s+replaces\s+`([^`]+)`", section
    )
    return (match.group(1), match.group(2)) if match else None


def mentions_scope(section: str, bom_item: str, context: str) -> bool:
    """A judgment is scoped by an explicit context, BOM item, or both."""
    context_mentioned = re.search(
        rf"`{re.escape(context)}`\s+context", section, flags=re.IGNORECASE
    )
    bom_mentioned = re.search(
        rf"\b{re.escape(bom_item)}\b", section, flags=re.IGNORECASE
    )
    return bool(context_mentioned or bom_mentioned)


def semantic_state(section: str, bom_item: str, context: str) -> str:
    if not mentions_scope(section, bom_item, context):
        return "not_established"

    positive_judgment = re.search(
        r"\b("
        r"acceptable\s+substitute|"
        r"preferred\s+fallback|"
        r"engineering\s+acceptance\s+judgment|"
        r"approved\s+(?:replacement|substitute)"
        r")\b",
        section,
        flags=re.IGNORECASE,
    )
    if positive_judgment:
        return "accepted"

    unresolved_language = re.search(
        r"\b("
        r"unresolved|uncertain|pending|not (?:yet )?(?:qualified|resolved)|"
        r"requires? (?:further )?(?:review|qualification)"
        r")\b",
        section,
        flags=re.IGNORECASE,
    )
    return "unresolved" if unresolved_language else "not_established"


def main() -> None:
    parts = read_csv("manufacturer.csv", "part_number")
    boms = read_csv("bom.csv", "bom_item")

    with (SOURCES / "suppliers.json").open(encoding="utf-8") as source:
        supplier_data: dict[str, Any] = json.load(source)
    represented_parts = {
        listing["manufacturer_part_number"]
        for listing in supplier_data["listings"]
    }

    notes = (SOURCES / "engineering_notes.md").read_text(encoding="utf-8")
    cases: list[dict[str, Any]] = []

    for section in note_sections(notes):
        relationship = candidate_relationship(section)
        if relationship is None:
            continue
        new_number, old_number = relationship

        # "Represented" candidates have a supplier listing and manufacturer data.
        if new_number not in represented_parts or new_number not in parts:
            continue
        if old_number not in parts:
            continue

        new_part = parts[new_number]
        old_part = parts[old_number]
        for bom_name, bom in boms.items():
            if not (
                bom["part_type"] == new_part["part_type"] == old_part["part_type"]
            ):
                continue

            voltage_compatible = (
                float(new_part["rated_voltage_v"]) >= float(bom["required_voltage_v"])
            )
            temperature_compatible = (
                float(new_part["min_temp_c"]) <= float(bom["min_temp_c"])
                and float(new_part["max_temp_c"]) >= float(bom["max_temp_c"])
            )
            lifecycle_active = new_part["lifecycle"].strip().lower() == "active"
            semantic = semantic_state(
                section, bom_name, bom["deployment_environment"]
            )

            prevents: list[str] = []
            if not voltage_compatible:
                prevents.append("voltage_compatible")
            if not temperature_compatible:
                prevents.append("temperature_compatible")
            if not lifecycle_active:
                prevents.append("lifecycle_active")

            uncertain: list[str] = []
            if semantic != "accepted":
                uncertain.append("semantic_acceptance")

            cases.append(
                {
                    "new_part": identifier("part", new_number),
                    "old_part": identifier("part", old_number),
                    "bom_item": identifier("bom", bom_name),
                    "context": identifier(
                        "context", bom["deployment_environment"]
                    ),
                    "voltage_compatible": voltage_compatible,
                    "temperature_compatible": temperature_compatible,
                    "new_part_lifecycle_active": lifecycle_active,
                    "old_part_lifecycle": old_part["lifecycle"],
                    "semantic_state": semantic,
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
    with (ROOT / "output.json").open("w", encoding="utf-8") as destination:
        json.dump(result, destination, indent=2)
        destination.write("\n")


if __name__ == "__main__":
    main()
