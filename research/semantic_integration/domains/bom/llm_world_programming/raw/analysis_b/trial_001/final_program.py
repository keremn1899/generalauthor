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

CONSTRAINT_ORDER = (
    "voltage_compatible",
    "temperature_compatible",
    "lifecycle_active",
    "semantic_acceptance",
)


def read_csv(name: str) -> list[dict[str, str]]:
    with (SOURCES / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def parse_replacement_notes(text: str) -> list[dict[str, Any]]:
    """Extract candidate pairs and their context-scoped engineering judgments."""
    candidate_matches = list(
        re.finditer(
            r"(?im)^Candidate:\s*`([^`]+)`\s+replaces\s+`([^`]+)`\s*\.\s*$",
            text,
        )
    )
    replacements: list[dict[str, Any]] = []

    for index, match in enumerate(candidate_matches):
        block_end = (
            candidate_matches[index + 1].start()
            if index + 1 < len(candidate_matches)
            else len(text)
        )
        block = text[match.end() : block_end]

        scopes = [
            (context, bom_item)
            for context, bom_item in re.findall(
                r"`([^`]+)`\s+context\s+used\s+by\s+(BOM-[A-Za-z0-9_-]+)",
                block,
                flags=re.IGNORECASE,
            )
        ]

        lowered = block.lower()
        positive_judgment = any(
            phrase in lowered
            for phrase in (
                "acceptable substitute",
                "accepted substitute",
                "preferred fallback",
                "acceptance judgment",
                "approved substitute",
            )
        )
        unresolved_judgment = any(
            phrase in lowered
            for phrase in (
                "acceptance is unresolved",
                "acceptance remains unresolved",
                "not yet determined",
                "under review",
            )
        )

        if positive_judgment:
            scoped_state = "accepted"
        elif unresolved_judgment:
            scoped_state = "unresolved"
        else:
            scoped_state = "not_established"

        replacements.append(
            {
                "new_part": match.group(1),
                "old_part": match.group(2),
                "scoped_states": {
                    (bom_item, context): scoped_state
                    for context, bom_item in scopes
                },
            }
        )

    return replacements


def main() -> None:
    manufacturers = {
        row["part_number"]: row for row in read_csv("manufacturer.csv")
    }
    bom_rows = read_csv("bom.csv")

    with (SOURCES / "suppliers.json").open(encoding="utf-8") as handle:
        supplier_data = json.load(handle)
    represented_parts = {
        listing["manufacturer_part_number"]
        for listing in supplier_data["listings"]
    }

    notes = (SOURCES / "engineering_notes.md").read_text(encoding="utf-8")
    replacements = parse_replacement_notes(notes)

    cases: list[dict[str, Any]] = []
    for replacement in replacements:
        new_number = replacement["new_part"]
        old_number = replacement["old_part"]

        if (
            new_number not in represented_parts
            or old_number not in represented_parts
            or new_number not in manufacturers
            or old_number not in manufacturers
        ):
            continue

        new_part = manufacturers[new_number]
        old_part = manufacturers[old_number]

        for bom in bom_rows:
            if (
                bom["part_type"] != new_part["part_type"]
                or bom["part_type"] != old_part["part_type"]
            ):
                continue

            voltage_compatible = (
                float(new_part["rated_voltage_v"])
                >= float(bom["required_voltage_v"])
            )
            temperature_compatible = (
                float(new_part["min_temp_c"]) <= float(bom["min_temp_c"])
                and float(new_part["max_temp_c"]) >= float(bom["max_temp_c"])
            )
            lifecycle_active = new_part["lifecycle"].strip().lower() == "active"
            semantic_state = replacement["scoped_states"].get(
                (bom["bom_item"], bom["deployment_environment"]),
                "not_established",
            )

            failed = {
                "voltage_compatible": not voltage_compatible,
                "temperature_compatible": not temperature_compatible,
                "lifecycle_active": not lifecycle_active,
            }
            uncertain = {
                "semantic_acceptance": semantic_state != "accepted",
            }

            cases.append(
                {
                    "new_part": f"part:{new_number}",
                    "old_part": f"part:{old_number}",
                    "bom_item": f"bom:{bom['bom_item']}",
                    "context": f"context:{bom['deployment_environment']}",
                    "voltage_compatible": voltage_compatible,
                    "temperature_compatible": temperature_compatible,
                    "new_part_lifecycle_active": lifecycle_active,
                    "old_part_lifecycle": old_part["lifecycle"],
                    "semantic_state": semantic_state,
                    "prevents_viability": [
                        name
                        for name in CONSTRAINT_ORDER
                        if failed.get(name, False)
                    ],
                    "leaves_viability_uncertain": [
                        name
                        for name in CONSTRAINT_ORDER
                        if uncertain.get(name, False)
                    ],
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
