#!/usr/bin/env python3
"""Compute qualification bottlenecks from the authoritative source files."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / "sources"


def read_csv(name: str) -> list[dict[str, str]]:
    with (SOURCES / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def prefixed(kind: str, value: str) -> str:
    return f"{kind}:{value}"


def candidate_sections(notes: str) -> list[dict[str, str]]:
    """Extract candidate pairs and retain each pair's scoped prose."""
    sections = re.split(r"(?=^##\s+)", notes, flags=re.MULTILINE)
    candidates: list[dict[str, str]] = []
    pattern = re.compile(
        r"Candidate:\s*`(?P<new>[^`]+)`\s+replaces\s+`(?P<old>[^`]+)`",
        re.IGNORECASE,
    )
    for section in sections:
        match = pattern.search(section)
        if match:
            candidates.append(
                {
                    "new": match.group("new").strip(),
                    "old": match.group("old").strip(),
                    "prose": section,
                }
            )
    return candidates


def semantic_state(prose: str, bom_item: str, context: str) -> str:
    """Interpret only judgments explicitly scoped to this BOM/context."""
    lowered = " ".join(prose.lower().split())
    scoped = bom_item.lower() in lowered and context.lower() in lowered
    if not scoped:
        return "not_established"

    positive = any(
        phrase in lowered
        for phrase in (
            "acceptable substitute",
            "acceptance judgment",
            "preferred fallback",
        )
    )
    # A conditional recommendation with explicitly incomplete qualification is
    # not an unconditional acceptance for the represented context.
    conditional = re.search(r"\bif\b", lowered) is not None
    incomplete_qualification = any(
        phrase in lowered
        for phrase in (
            "qualification was not repeated",
            "qualification is incomplete",
            "qualification remains open",
        )
    )
    if positive and not (conditional and incomplete_qualification):
        return "accepted"
    return "unresolved"


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

    cases: list[dict[str, object]] = []
    for candidate in candidate_sections(notes):
        new_number = candidate["new"]
        old_number = candidate["old"]
        if new_number not in represented_parts:
            continue
        new_part = manufacturers[new_number]
        old_part = manufacturers[old_number]

        for bom in bom_rows:
            if bom["part_type"] != new_part["part_type"]:
                continue

            voltage_compatible = (
                float(new_part["rated_voltage_v"])
                == float(bom["required_voltage_v"])
            )
            temperature_compatible = (
                float(new_part["min_temp_c"]) <= float(bom["min_temp_c"])
                and float(new_part["max_temp_c"]) >= float(bom["max_temp_c"])
            )
            lifecycle_active = new_part["lifecycle"].strip().lower() == "active"
            state = semantic_state(
                candidate["prose"],
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
                    "new_part": prefixed("part", new_number),
                    "old_part": prefixed("part", old_number),
                    "bom_item": prefixed("bom", bom["bom_item"]),
                    "context": prefixed(
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
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
