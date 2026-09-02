#!/usr/bin/env python3
"""Qualification bottlenecks analysis for BOM replacement candidates."""

import csv
import json
import re
from pathlib import Path

SOURCES = Path(__file__).resolve().parent / "sources"


def load_manufacturer_parts():
    parts = {}
    with open(SOURCES / "manufacturer.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            parts[row["part_number"]] = {
                "part_type": row["part_type"],
                "rated_voltage_v": int(row["rated_voltage_v"]),
                "min_temp_c": int(row["min_temp_c"]),
                "max_temp_c": int(row["max_temp_c"]),
                "lifecycle": row["lifecycle"],
            }
    return parts


def load_bom_items():
    items = []
    with open(SOURCES / "bom.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            items.append(
                {
                    "bom_item": row["bom_item"],
                    "part_type": row["part_type"],
                    "required_voltage_v": int(row["required_voltage_v"]),
                    "min_temp_c": int(row["min_temp_c"]),
                    "max_temp_c": int(row["max_temp_c"]),
                    "deployment_environment": row["deployment_environment"],
                }
            )
    return items


def parse_replacement_candidates(notes_text):
    """Extract replacement pairs and linked contexts from engineering notes."""
    candidates = []
    sections = re.split(r"\n## ER-\d+\n", notes_text)
    for section in sections[1:]:
        pair_match = re.search(
            r"Candidate:\s*`([^`]+)`\s*replaces\s*`([^`]+)`", section
        )
        if not pair_match:
            continue
        new_part, old_part = pair_match.group(1), pair_match.group(2)

        context_match = re.search(r"`([a-z0-9_]+)`\s+context", section)
        bom_match = re.search(r"context used by\s+(BOM-[A-Z0-9]+)", section)
        context = context_match.group(1) if context_match else None
        bom_item = bom_match.group(1) if bom_match else None

        semantic_state = "not_established"
        normalized = re.sub(r"\s+", " ", section.lower())
        if "acceptable substitute" in normalized or (
            "treats" in normalized and "acceptable" in normalized
        ):
            semantic_state = "accepted"
        elif (
            "qualification was not repeated" in normalized
            or "engineering acceptance judgment" in normalized
        ):
            semantic_state = "unresolved"

        candidates.append(
            {
                "new_part": new_part,
                "old_part": old_part,
                "noted_context": context,
                "noted_bom_item": bom_item,
                "noted_semantic_state": semantic_state,
            }
        )
    return candidates


def relevant_bom_items(bom_items, part_type):
    return [item for item in bom_items if item["part_type"] == part_type]


def voltage_compatible(part, bom):
    return part["rated_voltage_v"] >= bom["required_voltage_v"]


def temperature_compatible(part, bom):
    return (
        part["min_temp_c"] <= bom["min_temp_c"]
        and part["max_temp_c"] >= bom["max_temp_c"]
    )


def semantic_state_for_case(candidate, bom):
    if (
        candidate["noted_context"] == bom["deployment_environment"]
        and candidate["noted_bom_item"] == bom["bom_item"]
    ):
        return candidate["noted_semantic_state"]
    return "not_established"


def build_case(candidate, bom, parts):
    new_part = parts[candidate["new_part"]]
    old_part = parts[candidate["old_part"]]

    v_compat = voltage_compatible(new_part, bom)
    t_compat = temperature_compatible(new_part, bom)
    lifecycle_active = new_part["lifecycle"] == "active"
    semantic = semantic_state_for_case(candidate, bom)

    prevents = []
    uncertain = []

    if not v_compat:
        prevents.append("voltage_compatible")
    if not t_compat:
        prevents.append("temperature_compatible")
    if not lifecycle_active:
        prevents.append("lifecycle_active")
    if semantic in ("unresolved", "not_established"):
        uncertain.append("semantic_acceptance")

    return {
        "new_part": f"part:{candidate['new_part']}",
        "old_part": f"part:{candidate['old_part']}",
        "bom_item": f"bom:{bom['bom_item']}",
        "context": f"context:{bom['deployment_environment']}",
        "voltage_compatible": v_compat,
        "temperature_compatible": t_compat,
        "new_part_lifecycle_active": lifecycle_active,
        "old_part_lifecycle": old_part["lifecycle"],
        "semantic_state": semantic,
        "prevents_viability": prevents,
        "leaves_viability_uncertain": uncertain,
    }


def main():
    parts = load_manufacturer_parts()
    bom_items = load_bom_items()
    notes_text = (SOURCES / "engineering_notes.md").read_text(encoding="utf-8")
    candidates = parse_replacement_candidates(notes_text)

    cases = []
    for candidate in candidates:
        old_part = parts[candidate["old_part"]]
        for bom in relevant_bom_items(bom_items, old_part["part_type"]):
            cases.append(build_case(candidate, bom, parts))

    cases.sort(
        key=lambda c: (c["new_part"], c["old_part"], c["bom_item"], c["context"])
    )

    output = {"task": "qualification_bottlenecks", "cases": cases}
    out_path = Path(__file__).resolve().parent / "output.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
