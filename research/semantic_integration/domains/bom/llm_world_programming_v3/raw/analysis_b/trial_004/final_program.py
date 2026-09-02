#!/usr/bin/env python3
"""Compute qualification bottlenecks from the authoritative source files."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / "sources"


def read_csv(path: Path, key: str) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return {row[key]: row for row in csv.DictReader(handle)}


def candidate_notes(text: str) -> list[dict[str, str]]:
    """Extract replacement pairs and retain each pair's prose judgment."""
    sections = re.split(r"(?m)^##\s+", text)[1:]
    results: list[dict[str, str]] = []
    for section in sections:
        match = re.search(
            r"Candidate:\s*`([^`]+)`\s+replaces\s+`([^`]+)`", section
        )
        if match:
            results.append(
                {"new": match.group(1), "old": match.group(2), "text": section}
            )
    return results


def semantic_state(note: str, bom_item: str, context: str) -> str:
    """Classify only judgments that apply to this BOM/context.

    An unmentioned context has no established judgment.  If a relevant note
    discusses uncertainty without reaching an acceptance judgment, it remains
    unresolved.  Explicit engineering acceptance controls even where the note
    explains that tabulated terminology or ratings alone are inconclusive.
    """
    if context not in note and bom_item not in note:
        return "not_established"

    accepted_phrases = (
        r"\bacceptable substitute\b",
        r"\bpreferred fallback\b",
        r"\bacceptance judgment\b",
        r"\baccepted\b",
        r"\bapproved\b",
    )
    if any(re.search(pattern, note, re.IGNORECASE) for pattern in accepted_phrases):
        return "accepted"
    return "unresolved"


def main() -> None:
    parts = read_csv(SOURCES / "manufacturer.csv", "part_number")
    bom = read_csv(SOURCES / "bom.csv", "bom_item")

    with (SOURCES / "suppliers.json").open(encoding="utf-8") as handle:
        supplier_data = json.load(handle)
    represented_parts = {
        listing["manufacturer_part_number"]
        for listing in supplier_data["listings"]
    }

    notes_text = (SOURCES / "engineering_notes.md").read_text(encoding="utf-8")
    replacements = candidate_notes(notes_text)

    cases: list[dict[str, object]] = []
    for replacement in replacements:
        new_number = replacement["new"]
        old_number = replacement["old"]

        # A replacement candidate must be represented by a supplier listing,
        # and both sides need manufacturer records to evaluate qualification.
        if (
            new_number not in represented_parts
            or new_number not in parts
            or old_number not in parts
        ):
            continue

        new_part = parts[new_number]
        old_part = parts[old_number]
        if new_part["part_type"] != old_part["part_type"]:
            continue

        for bom_number, requirement in bom.items():
            if requirement["part_type"] != old_part["part_type"]:
                continue

            voltage_ok = (
                float(new_part["rated_voltage_v"])
                >= float(requirement["required_voltage_v"])
            )
            temperature_ok = (
                float(new_part["min_temp_c"])
                <= float(requirement["min_temp_c"])
                and float(new_part["max_temp_c"])
                >= float(requirement["max_temp_c"])
            )
            lifecycle_active = new_part["lifecycle"].strip().lower() == "active"
            state = semantic_state(
                replacement["text"],
                bom_number,
                requirement["deployment_environment"],
            )

            prevents: list[str] = []
            if not voltage_ok:
                prevents.append("voltage_compatible")
            if not temperature_ok:
                prevents.append("temperature_compatible")
            if not lifecycle_active:
                prevents.append("lifecycle_active")

            uncertain: list[str] = []
            if state != "accepted":
                uncertain.append("semantic_acceptance")

            cases.append(
                {
                    "new_part": f"part:{new_number}",
                    "old_part": f"part:{old_number}",
                    "bom_item": f"bom:{bom_number}",
                    "context": (
                        f"context:{requirement['deployment_environment']}"
                    ),
                    "voltage_compatible": voltage_ok,
                    "temperature_compatible": temperature_ok,
                    "new_part_lifecycle_active": lifecycle_active,
                    "old_part_lifecycle": old_part["lifecycle"],
                    "semantic_state": state,
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
    (ROOT / "output.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
