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
    with (SOURCES / name).open(newline="", encoding="utf-8") as handle:
        return {row[key]: row for row in csv.DictReader(handle)}


def represented_parts() -> set[str]:
    with (SOURCES / "suppliers.json").open(encoding="utf-8") as handle:
        data = json.load(handle)
    return {
        listing["manufacturer_part_number"]
        for listing in data["listings"]
        if listing.get("manufacturer_part_number")
    }


def note_sections(text: str) -> list[str]:
    return [
        section
        for section in re.split(r"(?m)^##\s+\S+.*$", text)
        if "Candidate:" in section
    ]


def semantic_state(section: str) -> str:
    """Classify the engineering judgment, not merely tabulated similarity."""
    accepted_patterns = (
        r"\bacceptable\s+substitute\b",
        r"\bengineering\s+acceptance\s+judgment\b",
        r"\bpreferred\s+fallback\b",
        r"\bapproved\s+(?:replacement|substitute|fallback)\b",
    )
    if any(re.search(pattern, section, re.IGNORECASE) for pattern in accepted_patterns):
        return "accepted"

    uncertainty_patterns = (
        r"\bunresolved\b",
        r"\buncertain\b",
        r"\bno\s+(?:numeric\s+)?crosswalk\b",
        r"\bnot\s+(?:yet\s+)?(?:qualified|resolved)\b",
        r"\brequires?\s+(?:further\s+)?(?:review|qualification)\b",
    )
    if any(
        re.search(pattern, section, re.IGNORECASE)
        for pattern in uncertainty_patterns
    ):
        return "unresolved"
    return "not_established"


def replacement_cases(notes: str) -> list[dict[str, str]]:
    cases: list[dict[str, str]] = []
    for section in note_sections(notes):
        replacement = re.search(
            r"Candidate:\s*`?([^`\s.]+)`?\s+replaces\s+`?([^`\s.]+)`?",
            section,
            re.IGNORECASE,
        )
        bom = re.search(r"\b(BOM-[A-Za-z0-9_-]+)\b", section)
        context = re.search(
            r"(?:For|In)\s+the\s+`([^`]+)`\s+context", section, re.IGNORECASE
        )
        if not (replacement and bom and context):
            raise ValueError(f"Incomplete replacement note:\n{section.strip()}")
        cases.append(
            {
                "new_part": replacement.group(1),
                "old_part": replacement.group(2),
                "bom_item": bom.group(1),
                "context": context.group(1),
                "semantic_state": semantic_state(section),
            }
        )
    return cases


def compatible_voltage(part: dict[str, str], bom: dict[str, str]) -> bool:
    # These are nominal operating-voltage fields, so compatibility is equality.
    return float(part["rated_voltage_v"]) == float(bom["required_voltage_v"])


def compatible_temperature(part: dict[str, str], bom: dict[str, str]) -> bool:
    return (
        float(part["min_temp_c"]) <= float(bom["min_temp_c"])
        and float(part["max_temp_c"]) >= float(bom["max_temp_c"])
    )


def build_output() -> dict[str, Any]:
    manufacturers = read_csv("manufacturer.csv", "part_number")
    bom_items = read_csv("bom.csv", "bom_item")
    listed_parts = represented_parts()
    notes = (SOURCES / "engineering_notes.md").read_text(encoding="utf-8")

    cases: list[dict[str, Any]] = []
    for relation in replacement_cases(notes):
        new_number = relation["new_part"]
        old_number = relation["old_part"]
        bom_number = relation["bom_item"]

        if new_number not in listed_parts or old_number not in listed_parts:
            continue
        new_part = manufacturers[new_number]
        old_part = manufacturers[old_number]
        bom = bom_items[bom_number]
        if bom["deployment_environment"] != relation["context"]:
            raise ValueError(
                f"{bom_number} context conflicts with its engineering note"
            )
        if not (
            new_part["part_type"]
            == old_part["part_type"]
            == bom["part_type"]
        ):
            raise ValueError(f"Part type mismatch for {new_number} replacing {old_number}")

        voltage_ok = compatible_voltage(new_part, bom)
        temperature_ok = compatible_temperature(new_part, bom)
        lifecycle_ok = new_part["lifecycle"].strip().lower() == "active"
        semantic = relation["semantic_state"]

        prevents: list[str] = []
        if not voltage_ok:
            prevents.append("voltage_compatible")
        if not temperature_ok:
            prevents.append("temperature_compatible")
        if not lifecycle_ok:
            prevents.append("lifecycle_active")

        uncertain: list[str] = []
        if semantic != "accepted":
            # Lack of a positive semantic judgment is uncertainty, not failure.
            uncertain.append("semantic_acceptance")

        cases.append(
            {
                "new_part": f"part:{new_number}",
                "old_part": f"part:{old_number}",
                "bom_item": f"bom:{bom_number}",
                "context": f"context:{relation['context']}",
                "voltage_compatible": voltage_ok,
                "temperature_compatible": temperature_ok,
                "new_part_lifecycle_active": lifecycle_ok,
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
    return {"task": "qualification_bottlenecks", "cases": cases}


def main() -> None:
    output = build_output()
    with (ROOT / "output.json").open("w", encoding="utf-8") as handle:
        json.dump(output, handle, indent=2)
        handle.write("\n")


if __name__ == "__main__":
    main()
