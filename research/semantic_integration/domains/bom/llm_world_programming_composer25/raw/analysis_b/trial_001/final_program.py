#!/usr/bin/env python3
"""Qualification bottleneck analysis for BOM replacement candidates."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / "sources"


def load_bom() -> dict[str, dict]:
    rows: dict[str, dict] = {}
    with (SOURCES / "bom.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            bom_item = row["bom_item"]
            rows[bom_item] = {
                "part_type": row["part_type"],
                "required_voltage_v": int(row["required_voltage_v"]),
                "min_temp_c": int(row["min_temp_c"]),
                "max_temp_c": int(row["max_temp_c"]),
                "deployment_environment": row["deployment_environment"],
            }
    return rows


def load_manufacturer() -> dict[str, dict]:
    rows: dict[str, dict] = {}
    with (SOURCES / "manufacturer.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            part_number = row["part_number"]
            rows[part_number] = {
                "part_type": row["part_type"],
                "rated_voltage_v": int(row["rated_voltage_v"]),
                "min_temp_c": int(row["min_temp_c"]),
                "max_temp_c": int(row["max_temp_c"]),
                "lifecycle": row["lifecycle"],
            }
    return rows


def parse_engineering_notes(text: str) -> list[dict]:
    """Extract replacement candidates and their ER sections from engineering notes."""
    candidates: list[dict] = []
    sections = re.split(r"(?=^## ER-\d+\s*$)", text, flags=re.MULTILINE)
    for section in sections:
        if not section.strip():
            continue
        match = re.search(
            r"Candidate:\s*`([^`]+)`\s+replaces\s+`([^`]+)`",
            section,
            flags=re.IGNORECASE,
        )
        if not match:
            continue
        new_part, old_part = match.group(1), match.group(2)
        context_match = re.search(r"For the `([^`]+)` context", section)
        bom_match = re.search(r"used by (BOM-[A-Z]+)", section)
        candidates.append(
            {
                "new_part": new_part,
                "old_part": old_part,
                "context": context_match.group(1) if context_match else None,
                "bom_item": bom_match.group(1) if bom_match else None,
                "section_text": section,
            }
        )
    return candidates


ACCEPTANCE_MARKERS = (
    "acceptable substitute",
    "preferred fallback",
    "engineering acceptance judgment",
    "engineering acceptance",
    "treats",
    "as an acceptable",
)

UNCERTAINTY_MARKERS = (
    "qualification was not repeated",
    "not repeated after",
    "different supplier terminology",
    "no numeric crosswalk",
    "rather than a conclusion from the tabulated ratings alone",
)


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def analyze_semantic(section_text: str) -> tuple[str, list[str]]:
    """Return semantic_state and semantic uncertainty constraints."""
    lowered = normalize_text(section_text)
    has_acceptance = any(marker in lowered for marker in ACCEPTANCE_MARKERS)
    has_uncertainty = any(marker in lowered for marker in UNCERTAINTY_MARKERS)

    if has_acceptance:
        state = "accepted"
    elif has_uncertainty:
        state = "unresolved"
    else:
        state = "not_established"

    uncertain: list[str] = []
    if has_uncertainty:
        uncertain.append("semantic_acceptance")
    elif state == "not_established":
        uncertain.append("semantic_acceptance")

    return state, uncertain


def voltage_compatible(part: dict, bom: dict) -> bool:
    return part["rated_voltage_v"] >= bom["required_voltage_v"]


def temperature_compatible(part: dict, bom: dict) -> bool:
    return (
        part["min_temp_c"] <= bom["min_temp_c"]
        and part["max_temp_c"] >= bom["max_temp_c"]
    )


def build_case(
    candidate: dict,
    bom_rows: dict[str, dict],
    manufacturer: dict[str, dict],
) -> dict:
    new_part_id = candidate["new_part"]
    old_part_id = candidate["old_part"]
    bom_item_id = candidate["bom_item"]
    context = candidate["context"]

    if bom_item_id is None:
        raise ValueError(f"No BOM item found for candidate {new_part_id} -> {old_part_id}")
    if context is None:
        raise ValueError(f"No context found for candidate {new_part_id} -> {old_part_id}")

    bom = bom_rows[bom_item_id]
    new_part = manufacturer[new_part_id]
    old_part = manufacturer[old_part_id]

    if bom["deployment_environment"] != context:
        raise ValueError(
            f"Context mismatch for {bom_item_id}: note={context!r}, bom={bom['deployment_environment']!r}"
        )

    volt_ok = voltage_compatible(new_part, bom)
    temp_ok = temperature_compatible(new_part, bom)
    lifecycle_active = new_part["lifecycle"] == "active"

    semantic_state, semantic_uncertain = analyze_semantic(candidate["section_text"])

    prevents: list[str] = []
    uncertain: list[str] = []

    if not volt_ok:
        prevents.append("voltage_compatible")
    if not temp_ok:
        prevents.append("temperature_compatible")
    if not lifecycle_active:
        prevents.append("lifecycle_active")

    for constraint in semantic_uncertain:
        if constraint not in prevents:
            uncertain.append(constraint)

    return {
        "new_part": f"part:{new_part_id}",
        "old_part": f"part:{old_part_id}",
        "bom_item": f"bom:{bom_item_id}",
        "context": f"context:{context}",
        "voltage_compatible": volt_ok,
        "temperature_compatible": temp_ok,
        "new_part_lifecycle_active": lifecycle_active,
        "old_part_lifecycle": old_part["lifecycle"],
        "semantic_state": semantic_state,
        "prevents_viability": prevents,
        "leaves_viability_uncertain": uncertain,
    }


def main() -> None:
    bom_rows = load_bom()
    manufacturer = load_manufacturer()
    notes_text = (SOURCES / "engineering_notes.md").read_text(encoding="utf-8")
    candidates = parse_engineering_notes(notes_text)

    cases = [build_case(candidate, bom_rows, manufacturer) for candidate in candidates]
    cases.sort(key=lambda case: (case["new_part"], case["old_part"], case["bom_item"], case["context"]))

    output = {
        "task": "qualification_bottlenecks",
        "cases": cases,
    }

    output_path = ROOT / "output.json"
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(output, handle, indent=2)
        handle.write("\n")

    print(f"Wrote {len(cases)} case(s) to {output_path}")


if __name__ == "__main__":
    main()
