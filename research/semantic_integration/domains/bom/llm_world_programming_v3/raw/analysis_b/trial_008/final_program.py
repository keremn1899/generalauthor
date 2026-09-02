#!/usr/bin/env python3
"""Compute qualification bottlenecks from the authoritative workspace sources."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / "sources"


def read_csv(name: str) -> list[dict[str, str]]:
    with (SOURCES / name).open(newline="", encoding="utf-8") as source:
        return list(csv.DictReader(source))


def engineering_candidates(notes: str) -> list[dict[str, object]]:
    """Extract replacement assertions and their context-specific judgments."""
    sections = re.split(r"(?m)^##\s+", notes)[1:]
    candidates: list[dict[str, object]] = []

    for section in sections:
        pair = re.search(
            r"Candidate:\s*`([^`]+)`\s+replaces\s+`([^`]+)`", section
        )
        if not pair:
            continue

        new_part, old_part = pair.groups()
        context_matches = re.findall(
            r"`([^`]+)`\s+context\s+used\s+by\s+(BOM-[A-Za-z0-9_-]+)",
            section,
        )

        # A conditional recommendation does not establish that its condition is
        # met. An unqualified explicit acceptance does establish acceptance,
        # even if the underlying terminology or numeric evidence is incomplete.
        lower = section.lower()
        if re.search(r"\b(preferred|acceptable|acceptance)\b[^.]*\bif\b", lower):
            state = "unresolved"
        elif (
            "acceptable substitute" in lower
            or "engineering acceptance judgment" in lower
        ):
            state = "accepted"
        else:
            state = "unresolved"

        candidates.append(
            {
                "new_part": new_part,
                "old_part": old_part,
                "judgments": {
                    (bom_item, context): state
                    for context, bom_item in context_matches
                },
            }
        )

    return candidates


def main() -> None:
    parts = {row["part_number"]: row for row in read_csv("manufacturer.csv")}
    bom_rows = read_csv("bom.csv")

    with (SOURCES / "suppliers.json").open(encoding="utf-8") as source:
        represented_parts = {
            listing["manufacturer_part_number"]
            for listing in json.load(source)["listings"]
        }

    notes = (SOURCES / "engineering_notes.md").read_text(encoding="utf-8")
    candidates = engineering_candidates(notes)
    cases: list[dict[str, object]] = []

    for candidate in candidates:
        new_number = str(candidate["new_part"])
        old_number = str(candidate["old_part"])
        if (
            new_number not in represented_parts
            or old_number not in represented_parts
            or new_number not in parts
            or old_number not in parts
        ):
            continue

        new_part = parts[new_number]
        old_part = parts[old_number]
        if new_part["part_type"] != old_part["part_type"]:
            continue

        judgments = candidate["judgments"]
        assert isinstance(judgments, dict)

        for bom in bom_rows:
            if bom["part_type"] != new_part["part_type"]:
                continue

            voltage_compatible = float(new_part["rated_voltage_v"]) >= float(
                bom["required_voltage_v"]
            )
            temperature_compatible = (
                float(new_part["min_temp_c"]) <= float(bom["min_temp_c"])
                and float(new_part["max_temp_c"]) >= float(bom["max_temp_c"])
            )
            lifecycle_active = new_part["lifecycle"].strip().lower() == "active"
            semantic_state = judgments.get(
                (bom["bom_item"], bom["deployment_environment"]),
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
                    "new_part": f"part:{new_number}",
                    "old_part": f"part:{old_number}",
                    "bom_item": f"bom:{bom['bom_item']}",
                    "context": f"context:{bom['deployment_environment']}",
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
    (ROOT / "output.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
