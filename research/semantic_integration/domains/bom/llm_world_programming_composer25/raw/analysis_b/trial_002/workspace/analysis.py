#!/usr/bin/env python3
"""Qualification bottlenecks analysis from authoritative source files."""

import csv
import json
import re
from pathlib import Path

SOURCES = Path(__file__).resolve().parent / "sources"
OUTPUT = Path(__file__).resolve().parent / "output.json"


def load_manufacturer_parts():
    parts = {}
    with open(SOURCES / "manufacturer.csv", newline="") as f:
        for row in csv.DictReader(f):
            parts[row["part_number"]] = {
                "part_type": row["part_type"],
                "rated_voltage_v": int(row["rated_voltage_v"]),
                "min_temp_c": int(row["min_temp_c"]),
                "max_temp_c": int(row["max_temp_c"]),
                "lifecycle": row["lifecycle"],
            }
    return parts


def load_bom_rows():
    rows = []
    with open(SOURCES / "bom.csv", newline="") as f:
        for row in csv.DictReader(f):
            rows.append(
                {
                    "bom_item": row["bom_item"],
                    "part_type": row["part_type"],
                    "required_voltage_v": int(row["required_voltage_v"]),
                    "min_temp_c": int(row["min_temp_c"]),
                    "max_temp_c": int(row["max_temp_c"]),
                    "deployment_environment": row["deployment_environment"],
                }
            )
    return rows


def load_supplier_listings():
    with open(SOURCES / "suppliers.json") as f:
        data = json.load(f)
    listings = {}
    for listing in data["listings"]:
        listings[listing["manufacturer_part_number"]] = listing
    return listings


def classify_semantic_section(section_text: str) -> str:
    lower = section_text.lower()
    if re.search(r"\bacceptable substitute\b", lower):
        return "accepted"
    unresolved_markers = (
        "qualification was not repeated",
        "engineering acceptance judgment",
        "judgment rather than a conclusion",
    )
    if any(marker in lower for marker in unresolved_markers):
        return "unresolved"
    return "not_established"


def parse_engineering_replacements():
    text = (SOURCES / "engineering_notes.md").read_text()
    records = []
    for section in re.findall(r"## ER-\d+\s+(.*?)(?=## ER-\d+|\Z)", text, re.DOTALL):
        match = re.search(
            r"Candidate:\s*`([^`]+)`\s+replaces\s*`([^`]+)`",
            section,
        )
        if not match:
            continue
        new_part, old_part = match.group(1), match.group(2)
        context_match = re.search(
            r"`([^`]+)`\s+context\s+used\s+by\s+(BOM-\w+)",
            section,
        )
        records.append(
            {
                "new_part": new_part,
                "old_part": old_part,
                "context": context_match.group(1) if context_match else None,
                "semantic_in_documented_context": classify_semantic_section(section),
            }
        )
    return records


def voltage_compatible(part, bom) -> bool:
    return part["rated_voltage_v"] >= bom["required_voltage_v"]


def temperature_compatible(part, bom) -> bool:
    return (
        part["min_temp_c"] <= bom["min_temp_c"]
        and part["max_temp_c"] >= bom["max_temp_c"]
    )


def part_meets_bom(part, bom) -> bool:
    return voltage_compatible(part, bom) and temperature_compatible(part, bom)


def is_replacement_target(part, listing) -> bool:
    if part["lifecycle"] == "discontinued":
        return True
    if listing and listing.get("availability") == "obsolete":
        return True
    return False


def discover_replacement_pairs(parts, listings, engineering_records):
    pairs = set()
    for record in engineering_records:
        pairs.add((record["new_part"], record["old_part"]))

    represented_parts = {
        pn for pn in parts if pn in listings and parts[pn]["lifecycle"] == "active"
    }

    for old_pn, old_part in parts.items():
        listing = listings.get(old_pn)
        if not is_replacement_target(old_part, listing):
            continue
        for new_pn in represented_parts:
            if new_pn == old_pn:
                continue
            if parts[new_pn]["part_type"] != old_part["part_type"]:
                continue
            pairs.add((new_pn, old_pn))

    return pairs


def semantic_state_for_pair(
    new_part: str,
    old_part: str,
    bom_context: str,
    engineering_records,
) -> str:
    for record in engineering_records:
        if record["new_part"] != new_part or record["old_part"] != old_part:
            continue
        if record["context"] == bom_context:
            return record["semantic_in_documented_context"]
    return "not_established"


def build_constraint_lists(
    voltage_ok: bool,
    temperature_ok: bool,
    lifecycle_active: bool,
    semantic_state: str,
) -> tuple[list[str], list[str]]:
    prevents = []
    uncertain = []

    if not voltage_ok:
        prevents.append("voltage_compatible")
    if not temperature_ok:
        prevents.append("temperature_compatible")
    if not lifecycle_active:
        prevents.append("lifecycle_active")

    # Missing or unresolved semantic acceptance creates uncertainty, not a hard failure.
    if semantic_state in ("unresolved", "not_established"):
        uncertain.append("semantic_acceptance")

    return prevents, uncertain


def evaluate_cases(parts, bom_rows, replacement_pairs, engineering_records):
    cases = []
    for new_pn, old_pn in replacement_pairs:
        if new_pn not in parts or old_pn not in parts:
            continue

        new_part = parts[new_pn]
        old_part = parts[old_pn]

        for bom in bom_rows:
            if bom["part_type"] != new_part["part_type"]:
                continue
            if not part_meets_bom(old_part, bom):
                continue

            context = bom["deployment_environment"]
            semantic_state = semantic_state_for_pair(
                new_pn, old_pn, context, engineering_records
            )
            voltage_ok = voltage_compatible(new_part, bom)
            temperature_ok = temperature_compatible(new_part, bom)
            lifecycle_active = new_part["lifecycle"] == "active"
            prevents, uncertain = build_constraint_lists(
                voltage_ok,
                temperature_ok,
                lifecycle_active,
                semantic_state,
            )

            cases.append(
                {
                    "new_part": f"part:{new_pn}",
                    "old_part": f"part:{old_pn}",
                    "bom_item": f"bom:{bom['bom_item']}",
                    "context": f"context:{context}",
                    "voltage_compatible": voltage_ok,
                    "temperature_compatible": temperature_ok,
                    "new_part_lifecycle_active": lifecycle_active,
                    "old_part_lifecycle": old_part["lifecycle"],
                    "semantic_state": semantic_state,
                    "prevents_viability": prevents,
                    "leaves_viability_uncertain": uncertain,
                }
            )

    cases.sort(key=lambda c: (c["new_part"], c["old_part"], c["bom_item"], c["context"]))
    return cases


def main():
    parts = load_manufacturer_parts()
    bom_rows = load_bom_rows()
    listings = load_supplier_listings()
    engineering_records = parse_engineering_replacements()
    replacement_pairs = discover_replacement_pairs(
        parts, listings, engineering_records
    )
    cases = evaluate_cases(parts, bom_rows, replacement_pairs, engineering_records)

    result = {
        "task": "qualification_bottlenecks",
        "cases": cases,
    }

    with open(OUTPUT, "w") as f:
        json.dump(result, f, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
