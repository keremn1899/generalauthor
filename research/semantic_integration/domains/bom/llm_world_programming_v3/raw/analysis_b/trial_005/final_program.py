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
    with (SOURCES / name).open(newline="", encoding="utf-8") as source:
        return list(csv.DictReader(source))


def extract_replacement_reviews(
    notes: str, known_contexts: set[str]
) -> list[dict[str, object]]:
    """Extract candidate pairs and context-specific semantic judgments."""
    sections = re.split(r"(?=^##\s+)", notes, flags=re.MULTILINE)
    reviews: list[dict[str, object]] = []

    for section in sections:
        pair = re.search(
            r"Candidate:\s*`([^`]+)`\s+replaces\s+`([^`]+)`", section
        )
        if pair is None:
            continue

        mentioned_contexts = {
            context
            for context in known_contexts
            if re.search(rf"`{re.escape(context)}`", section)
        }
        lowered = section.lower()
        positive_judgment = any(
            phrase in lowered
            for phrase in (
                "acceptable substitute",
                "preferred fallback",
                "acceptance judgment",
            )
        )
        unresolved_judgment = any(
            phrase in lowered
            for phrase in (
                "acceptance unresolved",
                "acceptability unresolved",
                "pending engineering review",
                "could not determine",
            )
        )

        if positive_judgment:
            state = "accepted"
        elif unresolved_judgment:
            state = "unresolved"
        else:
            state = "not_established"

        reviews.append(
            {
                "new_part": pair.group(1),
                "old_part": pair.group(2),
                "context_states": {
                    context: state for context in mentioned_contexts
                },
            }
        )

    return reviews


def part_id(part_number: str) -> str:
    return f"part:{part_number}"


def main() -> None:
    bom_rows = read_csv("bom.csv")
    manufacturer_rows = read_csv("manufacturer.csv")
    parts = {row["part_number"]: row for row in manufacturer_rows}
    contexts = {row["deployment_environment"] for row in bom_rows}
    notes = (SOURCES / "engineering_notes.md").read_text(encoding="utf-8")
    reviews = extract_replacement_reviews(notes, contexts)

    cases: list[dict[str, object]] = []
    for review in reviews:
        new_number = str(review["new_part"])
        old_number = str(review["old_part"])
        new_part = parts[new_number]
        old_part = parts[old_number]
        context_states = review["context_states"]
        assert isinstance(context_states, dict)

        # A replacement relationship applies to BOM requirements of the same
        # part type. Semantic judgments remain specific to their named context.
        relevant_boms = (
            row for row in bom_rows if row["part_type"] == new_part["part_type"]
        )
        for bom in relevant_boms:
            context_name = bom["deployment_environment"]
            voltage_compatible = float(new_part["rated_voltage_v"]) >= float(
                bom["required_voltage_v"]
            )
            temperature_compatible = (
                float(new_part["min_temp_c"]) <= float(bom["min_temp_c"])
                and float(new_part["max_temp_c"]) >= float(bom["max_temp_c"])
            )
            lifecycle_active = new_part["lifecycle"].strip().lower() == "active"
            semantic_state = str(
                context_states.get(context_name, "not_established")
            )

            prevents: list[str] = []
            if not voltage_compatible:
                prevents.append("voltage_compatible")
            if not temperature_compatible:
                prevents.append("temperature_compatible")
            if not lifecycle_active:
                prevents.append("lifecycle_active")

            uncertain: list[str] = []
            if semantic_state in {"unresolved", "not_established"}:
                uncertain.append("semantic_acceptance")

            cases.append(
                {
                    "new_part": part_id(new_number),
                    "old_part": part_id(old_number),
                    "bom_item": f'bom:{bom["bom_item"]}',
                    "context": f"context:{context_name}",
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
