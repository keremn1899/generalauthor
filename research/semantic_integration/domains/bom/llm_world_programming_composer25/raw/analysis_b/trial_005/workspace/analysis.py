#!/usr/bin/env python3
"""Qualification bottleneck analysis for BOM replacement candidates."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent
SOURCES = WORKSPACE / "sources"


def load_bom() -> dict[str, dict]:
    bom: dict[str, dict] = {}
    with (SOURCES / "bom.csv").open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            bom[row["bom_item"]] = {
                "part_type": row["part_type"],
                "required_voltage_v": int(row["required_voltage_v"]),
                "min_temp_c": int(row["min_temp_c"]),
                "max_temp_c": int(row["max_temp_c"]),
                "deployment_environment": row["deployment_environment"],
            }
    return bom


def load_manufacturer() -> dict[str, dict]:
    parts: dict[str, dict] = {}
    with (SOURCES / "manufacturer.csv").open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            parts[row["part_number"]] = {
                "part_type": row["part_type"],
                "rated_voltage_v": int(row["rated_voltage_v"]),
                "min_temp_c": int(row["min_temp_c"]),
                "max_temp_c": int(row["max_temp_c"]),
                "lifecycle": row["lifecycle"],
            }
    return parts


def load_engineering_notes() -> str:
    return (SOURCES / "engineering_notes.md").read_text(encoding="utf-8")


def parse_replacement_candidates(notes: str, bom: dict[str, dict]) -> list[dict]:
    """Extract replacement candidate records from engineering notes."""
    candidates: list[dict] = []
    sections = re.split(r"\n## ER-\d+\n", notes)
    for section in sections[1:]:
        pair_match = re.search(
            r"Candidate:\s*`([^`]+)`\s+replaces\s+`([^`]+)`\.",
            section,
        )
        if not pair_match:
            continue
        new_part, old_part = pair_match.group(1), pair_match.group(2)

        context_match = re.search(r"`([a-z_]+)`\s+context", section, re.IGNORECASE)
        bom_match = re.search(r"BOM-([A-Z])", section)
        context = None
        bom_item = None
        if context_match:
            context = context_match.group(1)
        if bom_match:
            bom_item = f"BOM-{bom_match.group(1)}"

        if bom_item is None and context is not None:
            for item, spec in bom.items():
                if spec["deployment_environment"] == context:
                    bom_item = item
                    break
        if context is None and bom_item is not None:
            context = bom[bom_item]["deployment_environment"]

        candidates.append(
            {
                "new_part": new_part,
                "old_part": old_part,
                "bom_item": bom_item,
                "context": context,
                "note_text": section.strip(),
            }
        )
    return candidates


def voltage_compatible(part: dict, bom_spec: dict) -> bool:
    return part["rated_voltage_v"] == bom_spec["required_voltage_v"]


def temperature_compatible(part: dict, bom_spec: dict) -> bool:
    return (
        part["min_temp_c"] <= bom_spec["min_temp_c"]
        and part["max_temp_c"] >= bom_spec["max_temp_c"]
    )


def classify_semantic_state(note_text: str) -> tuple[str, bool]:
    """
    Return (semantic_state, has_semantic_uncertainty).

    A missing positive judgment is not a failure; uncertainty is tracked separately.
    """
    lower = note_text.lower()

    acceptance_markers = (
        "acceptable substitute",
        "treats",
        "preferred fallback",
    )
    unresolved_markers = (
        "qualification was not repeated",
        "engineering acceptance judgment",
        "not repeated after",
    )
    uncertainty_markers = (
        "different supplier terminology",
        "no numeric crosswalk",
        "rather than a conclusion from the tabulated ratings alone",
        "qualification was not repeated",
        "engineering acceptance judgment",
    )

    has_acceptance = any(marker in lower for marker in acceptance_markers)
    has_unresolved = any(marker in lower for marker in unresolved_markers)
    has_uncertainty = any(marker in lower for marker in uncertainty_markers)

    if has_unresolved and not (
        "acceptable substitute" in lower and "no numeric crosswalk" in lower
    ):
        return "unresolved", has_uncertainty

    if has_acceptance:
        return "accepted", has_uncertainty

    if has_uncertainty:
        return "unresolved", True

    return "not_established", False


def build_case(
    candidate: dict,
    bom: dict[str, dict],
    parts: dict[str, dict],
) -> dict:
    new_part_num = candidate["new_part"]
    old_part_num = candidate["old_part"]
    bom_item = candidate["bom_item"]
    context = candidate["context"]

    new_part = parts[new_part_num]
    old_part = parts[old_part_num]
    bom_spec = bom[bom_item]

    volt_ok = voltage_compatible(new_part, bom_spec)
    temp_ok = temperature_compatible(new_part, bom_spec)
    lifecycle_active = new_part["lifecycle"] == "active"

    semantic_state, has_semantic_uncertainty = classify_semantic_state(
        candidate["note_text"]
    )

    prevents: list[str] = []
    uncertain: list[str] = []

    if not volt_ok:
        prevents.append("voltage_compatible")
    if not temp_ok:
        prevents.append("temperature_compatible")
    if not lifecycle_active:
        prevents.append("lifecycle_active")

    if semantic_state in ("unresolved", "not_established") or has_semantic_uncertainty:
        uncertain.append("semantic_acceptance")

    return {
        "new_part": f"part:{new_part_num}",
        "old_part": f"part:{old_part_num}",
        "bom_item": f"bom:{bom_item}",
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
    bom = load_bom()
    parts = load_manufacturer()
    notes = load_engineering_notes()
    candidates = parse_replacement_candidates(notes, bom)

    cases = [build_case(candidate, bom, parts) for candidate in candidates]
    cases.sort(
        key=lambda c: (c["new_part"], c["old_part"], c["bom_item"], c["context"])
    )

    result = {
        "task": "qualification_bottlenecks",
        "cases": cases,
    }

    output_path = WORKSPACE / "output.json"
    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)
        fh.write("\n")


if __name__ == "__main__":
    main()
