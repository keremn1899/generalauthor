#!/usr/bin/env python3
"""Compute qualification bottlenecks from the authoritative source files."""

from __future__ import annotations

import csv
import io
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / "sources"
LINE_MARKER = re.compile(r"^\s*\d+\|")


def read_clean_text(path: Path) -> str:
    """Remove display line markers that may be embedded in source exports."""
    return "\n".join(LINE_MARKER.sub("", line) for line in path.read_text().splitlines())


def read_csv(path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(read_clean_text(path))))


def part_id(part_number: str) -> str:
    return f"part:{part_number}"


def bom_id(bom_item: str) -> str:
    return f"bom:{bom_item}"


def context_id(environment: str) -> str:
    return f"context:{environment}"


def parse_engineering_notes(
    text: str,
) -> tuple[set[str], dict[tuple[str, str, str, str], str]]:
    """Return replaced parts and contextual semantic judgments.

    A note that expressly calls a candidate a fallback/substitute (or labels
    the conclusion an acceptance judgment) is a positive semantic judgment,
    even when the prose explains that it is not based on tabulated ratings.
    A represented note without such a judgment remains unresolved.
    """
    replaced_parts: set[str] = set()
    judgments: dict[tuple[str, str, str, str], str] = {}

    sections = re.split(r"(?m)^##\s+", text)
    for section in sections[1:]:
        relation = re.search(
            r"Candidate:\s*`([^`]+)`\s+replaces\s+`([^`]+)`", section, re.I
        )
        if relation is None:
            continue

        new_part, old_part = relation.groups()
        replaced_parts.add(old_part)

        scope = re.search(
            r"`([^`]+)`\s+context\s+used\s+by\s+(BOM-[A-Za-z0-9_-]+)",
            section,
            re.I,
        )
        if scope is None:
            continue

        environment, bom_item = scope.groups()
        positive = re.search(
            r"\b(preferred\s+fallback|acceptable\s+substitute|"
            r"acceptance\s+judgment)\b",
            section,
            re.I,
        )
        state = "accepted" if positive else "unresolved"
        judgments[(new_part, old_part, bom_item, environment)] = state

    return replaced_parts, judgments


def main() -> None:
    manufacturer_rows = read_csv(SOURCES / "manufacturer.csv")
    bom_rows = read_csv(SOURCES / "bom.csv")
    supplier_data: dict[str, Any] = json.loads(
        read_clean_text(SOURCES / "suppliers.json")
    )
    notes = read_clean_text(SOURCES / "engineering_notes.md")

    parts = {row["part_number"]: row for row in manufacturer_rows}
    represented_parts = {
        listing["manufacturer_part_number"]
        for listing in supplier_data["listings"]
        if listing["manufacturer_part_number"] in parts
    }
    replaced_parts, semantic_judgments = parse_engineering_notes(notes)

    cases: list[dict[str, Any]] = []
    for old_number in replaced_parts:
        old = parts.get(old_number)
        if old is None:
            continue

        candidate_numbers = sorted(
            number
            for number in represented_parts
            if number != old_number
            and parts[number]["part_type"] == old["part_type"]
        )
        relevant_boms = (
            row for row in bom_rows if row["part_type"] == old["part_type"]
        )

        for bom in relevant_boms:
            required_voltage = float(bom["required_voltage_v"])
            required_min_temp = float(bom["min_temp_c"])
            required_max_temp = float(bom["max_temp_c"])

            for new_number in candidate_numbers:
                new = parts[new_number]
                voltage_compatible = (
                    float(new["rated_voltage_v"]) >= required_voltage
                )
                temperature_compatible = (
                    float(new["min_temp_c"]) <= required_min_temp
                    and float(new["max_temp_c"]) >= required_max_temp
                )
                lifecycle_active = new["lifecycle"].strip().lower() == "active"
                semantic_state = semantic_judgments.get(
                    (
                        new_number,
                        old_number,
                        bom["bom_item"],
                        bom["deployment_environment"],
                    ),
                    "not_established",
                )

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
                        "new_part": part_id(new_number),
                        "old_part": part_id(old_number),
                        "bom_item": bom_id(bom["bom_item"]),
                        "context": context_id(bom["deployment_environment"]),
                        "voltage_compatible": voltage_compatible,
                        "temperature_compatible": temperature_compatible,
                        "new_part_lifecycle_active": lifecycle_active,
                        "old_part_lifecycle": old["lifecycle"],
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
    (ROOT / "output.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
