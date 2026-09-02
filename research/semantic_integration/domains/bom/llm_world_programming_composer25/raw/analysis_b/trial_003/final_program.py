#!/usr/bin/env python3
"""Qualification bottlenecks analysis from authoritative source files."""

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / "sources"

UNCERTAINTY_MARKERS = [
    "qualification was not repeated",
    "no numeric crosswalk",
    "different supplier terminology",
    "engineering acceptance judgment",
    "not a conclusion from the tabulated ratings",
]

ACCEPTANCE_MARKERS = [
    "acceptable substitute",
    "preferred fallback",
    "treats ",
    " as an acceptable",
]


def load_manufacturer_parts():
    parts = {}
    with (SOURCES / "manufacturer.csv").open(newline="") as f:
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
    items = {}
    with (SOURCES / "bom.csv").open(newline="") as f:
        for row in csv.DictReader(f):
            items[row["bom_item"]] = {
                "part_type": row["part_type"],
                "required_voltage_v": int(row["required_voltage_v"]),
                "min_temp_c": int(row["min_temp_c"]),
                "max_temp_c": int(row["max_temp_c"]),
                "deployment_environment": row["deployment_environment"],
            }
    return items


def parse_engineering_notes():
    text = (SOURCES / "engineering_notes.md").read_text()
    pattern = re.compile(
        r"## ER-\d+\s*\n+"
        r"Candidate:\s*`([^`]+)`\s+replaces\s+`([^`]+)`\.\s*\n+"
        r"For the\s+`([^`]+)`\s+context used by\s+(BOM-[A-Z])",
        re.MULTILINE,
    )
    candidates = []
    for match in pattern.finditer(text):
        new_part, old_part, context, bom_item = match.groups()
        section_start = match.start()
        next_section = text.find("## ER-", match.end())
        section_text = text[section_start:next_section if next_section != -1 else len(text)]
        candidates.append(
            {
                "new_part": new_part,
                "old_part": old_part,
                "context": context,
                "bom_item": bom_item,
                "section_text": section_text,
            }
        )
    return candidates


def semantic_state(section_text: str) -> str:
    normalized = re.sub(r"\s+", " ", section_text.lower())
    if any(marker in normalized for marker in UNCERTAINTY_MARKERS):
        return "unresolved"
    if any(marker in normalized for marker in ACCEPTANCE_MARKERS):
        return "accepted"
    return "not_established"


def voltage_compatible(part: dict, bom: dict) -> bool:
    if part["part_type"] != bom["part_type"]:
        return False
    return part["rated_voltage_v"] >= bom["required_voltage_v"]


def temperature_compatible(part: dict, bom: dict) -> bool:
    if part["part_type"] != bom["part_type"]:
        return False
    return (
        part["min_temp_c"] <= bom["min_temp_c"]
        and part["max_temp_c"] >= bom["max_temp_c"]
    )


def build_case(candidate, parts, bom_items):
    new_pn = candidate["new_part"]
    old_pn = candidate["old_part"]
    bom_id = candidate["bom_item"]
    context = candidate["context"]

    new_part = parts[new_pn]
    old_part = parts[old_pn]
    bom = bom_items[bom_id]

    if bom["deployment_environment"] != context:
        raise ValueError(
            f"BOM {bom_id} environment {bom['deployment_environment']} "
            f"does not match noted context {context}"
        )

    v_compat = voltage_compatible(new_part, bom)
    t_compat = temperature_compatible(new_part, bom)
    lifecycle_active = new_part["lifecycle"] == "active"
    semantic = semantic_state(candidate["section_text"])

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
        "new_part": f"part:{new_pn}",
        "old_part": f"part:{old_pn}",
        "bom_item": f"bom:{bom_id}",
        "context": f"context:{context}",
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
    candidates = parse_engineering_notes()

    cases = [build_case(c, parts, bom_items) for c in candidates]
    cases.sort(key=lambda c: (c["new_part"], c["old_part"], c["bom_item"], c["context"]))

    result = {
        "task": "qualification_bottlenecks",
        "cases": cases,
    }

    out_path = ROOT / "output.json"
    out_path.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
