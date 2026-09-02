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
    with path.open(newline="", encoding="utf-8") as source:
        return {row[key]: row for row in csv.DictReader(source)}


def candidate_sections(notes: str) -> list[tuple[str, str, str]]:
    """Return (new part, old part, section text) for documented candidates."""
    sections = re.split(r"(?=^##\s+)", notes, flags=re.MULTILINE)
    candidates: list[tuple[str, str, str]] = []
    pattern = re.compile(
        r"Candidate:\s*`?([A-Za-z0-9._-]+)`?\s+replaces\s+"
        r"`?([A-Za-z0-9._-]+)`?\.",
        flags=re.IGNORECASE,
    )
    for section in sections:
        match = pattern.search(section)
        if match:
            candidates.append((match.group(1), match.group(2), section))
    return candidates


def semantic_state(
    section: str, bom_item: str, context: str, known_bom_items: set[str]
) -> str:
    """Classify the contextual engineering judgment in a candidate section."""
    mentioned_boms = {
        item
        for item in known_bom_items
        if re.search(rf"\b{re.escape(item)}\b", section)
    }
    context_is_mentioned = re.search(rf"`?{re.escape(context)}`?", section) is not None

    # A judgment naming another BOM/context does not establish acceptance here.
    if bom_item not in mentioned_boms and not context_is_mentioned:
        return "not_established"

    positive_judgment = re.search(
        r"\b(?:acceptable substitute|acceptance judgment|"
        r"accepted substitute|approved substitute|preferred fallback)\b",
        section,
        flags=re.IGNORECASE,
    )
    if positive_judgment:
        return "accepted"
    return "unresolved"


def main() -> None:
    parts = read_csv(SOURCES / "manufacturer.csv", "part_number")

    with (SOURCES / "bom.csv").open(newline="", encoding="utf-8") as source:
        bom_rows = list(csv.DictReader(source))

    with (SOURCES / "suppliers.json").open(encoding="utf-8") as source:
        supplier_data = json.load(source)
    represented_parts = {
        listing["manufacturer_part_number"]
        for listing in supplier_data["listings"]
    }

    notes = (SOURCES / "engineering_notes.md").read_text(encoding="utf-8")
    candidates = candidate_sections(notes)
    known_bom_items = {row["bom_item"] for row in bom_rows}

    cases: list[dict[str, object]] = []
    for new_number, old_number, section in candidates:
        if new_number not in represented_parts:
            continue
        if new_number not in parts or old_number not in parts:
            raise ValueError(
                f"Candidate {new_number} -> {old_number} lacks manufacturer data"
            )

        new_part = parts[new_number]
        old_part = parts[old_number]
        if new_part["part_type"] != old_part["part_type"]:
            raise ValueError(
                f"Candidate {new_number} and old part {old_number} have "
                "different part types"
            )

        # A documented replacement is relevant to every BOM requirement for
        # that part type; semantic judgments remain scoped to their named
        # BOM/context.
        for bom in bom_rows:
            if bom["part_type"] != old_part["part_type"]:
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
                section,
                bom["bom_item"],
                bom["deployment_environment"],
                known_bom_items,
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
                    "new_part": f"part:{new_number}",
                    "old_part": f"part:{old_number}",
                    "bom_item": f"bom:{bom['bom_item']}",
                    "context": f"context:{bom['deployment_environment']}",
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
