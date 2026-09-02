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


def read_csv(filename: str) -> list[dict[str, str]]:
    with (SOURCES / filename).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def identifier(kind: str, value: str) -> str:
    return f"{kind}:{value}"


def parse_candidate_notes(notes: str) -> list[tuple[str, str, str]]:
    """Return (new part, old part, note section) for every review candidate."""
    heading = re.compile(r"(?m)^##\s+.+$")
    sections = heading.split(notes)
    candidates: list[tuple[str, str, str]] = []
    candidate_pattern = re.compile(
        r"Candidate:\s*`?([A-Za-z0-9._-]+)`?\s+replaces\s+"
        r"`?([A-Za-z0-9._-]+)`?",
        re.IGNORECASE,
    )

    for section in sections:
        match = candidate_pattern.search(section)
        if match:
            candidates.append((match.group(1), match.group(2), section))
    return candidates


def semantic_state(
    note_section: str,
    new_part: str,
    bom_item: str,
    context: str,
) -> str:
    """Interpret a context-specific engineering judgment without inferring one."""
    context_is_discussed = (
        re.search(rf"\b{re.escape(bom_item)}\b", note_section, re.IGNORECASE)
        is not None
        and re.search(rf"`?{re.escape(context)}`?", note_section, re.IGNORECASE)
        is not None
    )
    if not context_is_discussed:
        return "not_established"

    positive_patterns = (
        rf"\b{re.escape(new_part)}\b[^.\n]*\bpreferred\s+fallback\b",
        rf"\b{re.escape(new_part)}\b[^.\n]*\bacceptable\s+substitute\b",
        r"\bengineering\s+acceptance\s+judgment\b",
        r"\btreats?\b[^.\n]*\bas\s+an?\s+acceptable\b",
    )
    if any(
        re.search(pattern, note_section, re.IGNORECASE)
        for pattern in positive_patterns
    ):
        return "accepted"
    return "unresolved"


def main() -> None:
    manufacturer_rows = read_csv("manufacturer.csv")
    bom_rows = read_csv("bom.csv")
    parts = {row["part_number"]: row for row in manufacturer_rows}

    with (SOURCES / "suppliers.json").open(encoding="utf-8") as handle:
        supplier_data: dict[str, Any] = json.load(handle)
    represented_parts = {
        listing["manufacturer_part_number"]
        for listing in supplier_data["listings"]
    }

    notes = (SOURCES / "engineering_notes.md").read_text(encoding="utf-8")
    candidates = parse_candidate_notes(notes)
    cases: list[dict[str, Any]] = []

    for new_number, old_number, note_section in candidates:
        if new_number not in parts or old_number not in parts:
            continue
        if new_number not in represented_parts or old_number not in represented_parts:
            continue

        new_part = parts[new_number]
        old_part = parts[old_number]
        if new_part["part_type"] != old_part["part_type"]:
            continue

        relevant_boms = (
            row for row in bom_rows if row["part_type"] == new_part["part_type"]
        )
        for bom in relevant_boms:
            voltage_compatible = (
                float(new_part["rated_voltage_v"]) >= float(bom["required_voltage_v"])
            )
            temperature_compatible = (
                float(new_part["min_temp_c"]) <= float(bom["min_temp_c"])
                and float(new_part["max_temp_c"]) >= float(bom["max_temp_c"])
            )
            lifecycle_active = new_part["lifecycle"].strip().lower() == "active"
            state = semantic_state(
                note_section,
                new_number,
                bom["bom_item"],
                bom["deployment_environment"],
            )

            prevents: list[str] = []
            if not voltage_compatible:
                prevents.append("voltage_compatible")
            if not temperature_compatible:
                prevents.append("temperature_compatible")
            if not lifecycle_active:
                prevents.append("lifecycle_active")

            uncertain: list[str] = []
            if state != "accepted":
                uncertain.append("semantic_acceptance")

            cases.append(
                {
                    "new_part": identifier("part", new_number),
                    "old_part": identifier("part", old_number),
                    "bom_item": identifier("bom", bom["bom_item"]),
                    "context": identifier(
                        "context", bom["deployment_environment"]
                    ),
                    "voltage_compatible": voltage_compatible,
                    "temperature_compatible": temperature_compatible,
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
        json.dumps(result, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
