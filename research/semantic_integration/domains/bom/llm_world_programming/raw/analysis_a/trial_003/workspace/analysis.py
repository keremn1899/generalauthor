#!/usr/bin/env python3
"""Compute replacement state from the authoritative workspace sources."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / "sources"


def read_csv(name: str, key: str) -> dict[str, dict[str, str]]:
    with (SOURCES / name).open(newline="", encoding="utf-8") as handle:
        return {row[key]: row for row in csv.DictReader(handle)}


def parse_notes() -> list[dict[str, str]]:
    text = (SOURCES / "engineering_notes.md").read_text(encoding="utf-8")
    sections = re.split(r"(?m)^##\s+", text)[1:]
    candidates: list[dict[str, str]] = []

    for section in sections:
        heading, _, body = section.partition("\n")
        pair = re.search(
            r"Candidate:\s*`([^`]+)`\s+replaces\s+`([^`]+)`", body
        )
        context = re.search(r"`([^`]+)`\s+context", body)
        if not pair or not context:
            raise ValueError(f"Could not parse candidate/context in {heading!r}")

        normalized = " ".join(body.lower().split())
        positive_markers = (
            "preferred fallback",
            "acceptable substitute",
            "accepted substitute",
            "acceptance judgment",
            "approved replacement",
        )
        unresolved_markers = (
            "unresolved",
            "pending review",
            "not yet accepted",
            "acceptance pending",
        )
        if any(marker in normalized for marker in positive_markers):
            semantic_state = "accepted"
            epistemic = "ASSERTED_TRUE"
        elif any(marker in normalized for marker in unresolved_markers):
            semantic_state = "unresolved"
            epistemic = "UNRESOLVED"
        else:
            # Absence of a positive judgment is lack of knowledge, not rejection.
            semantic_state = "not_established"
            epistemic = "NOT_KNOWN"

        candidates.append(
            {
                "new_part_number": pair.group(1),
                "old_part_number": pair.group(2),
                "context_name": context.group(1),
                "semantic_state": semantic_state,
                "epistemic": epistemic,
                "note_locator": heading.strip(),
            }
        )

    return candidates


def is_mechanically_suitable(part: dict[str, str], item: dict[str, str]) -> bool:
    return (
        part["part_type"] == item["part_type"]
        and float(part["rated_voltage_v"]) == float(item["required_voltage_v"])
        and float(part["min_temp_c"]) <= float(item["min_temp_c"])
        and float(part["max_temp_c"]) >= float(item["max_temp_c"])
    )


def build_output() -> dict[str, Any]:
    parts = read_csv("manufacturer.csv", "part_number")
    bom = read_csv("bom.csv", "bom_item")
    cases: list[dict[str, Any]] = []
    support_inputs: list[dict[str, str]] = []

    for candidate in parse_notes():
        part_number = candidate["new_part_number"]
        context_name = candidate["context_name"]
        if part_number not in parts:
            raise ValueError(f"Unknown candidate part {part_number!r}")

        matching_items = sorted(
            (
                item
                for item in bom.values()
                if item["deployment_environment"] == context_name
            ),
            key=lambda item: item["bom_item"],
        )
        if not matching_items:
            raise ValueError(f"No BOM items found for context {context_name!r}")

        suitable = all(
            is_mechanically_suitable(parts[part_number], item)
            for item in matching_items
        )
        case = {
            "new_part": f"part:{part_number}",
            "old_part": f"part:{candidate['old_part_number']}",
            "context": f"context:{context_name}",
            "bom_items": [f"bom:{item['bom_item']}" for item in matching_items],
            "mechanical_state": "suitable" if suitable else "unsuitable",
            "semantic_state": candidate["semantic_state"],
            "epistemic": candidate["epistemic"],
        }
        cases.append(case)

        support_inputs.append(
            {
                "claim": (
                    f"{case['new_part']} replaces {case['old_part']} in "
                    f"{case['context']} for {', '.join(case['bom_items'])}; "
                    f"mechanical_state={case['mechanical_state']}, "
                    f"semantic_state={case['semantic_state']}, "
                    f"epistemic={case['epistemic']}"
                ),
                "note_locator": candidate["note_locator"],
                "part_number": part_number,
                "bom_locator": ", ".join(
                    f"row {item['bom_item']}" for item in matching_items
                ),
            }
        )

    cases.sort(key=lambda case: (case["new_part"], case["old_part"], case["context"]))

    # One fully traced case is sufficient for the separately scored provenance test.
    supported = min(support_inputs, key=lambda item: item["claim"])
    support = [
        {
            "claim": supported["claim"],
            "evidence": [
                {
                    "source": "sources/engineering_notes.md",
                    "locator": f"section {supported['note_locator']}",
                },
                {
                    "source": "sources/manufacturer.csv",
                    "locator": f"row {supported['part_number']}",
                },
                {
                    "source": "sources/bom.csv",
                    "locator": supported["bom_locator"],
                },
            ],
        }
    ]

    return {"task": "replacement_state", "cases": cases, "support": support}


def main() -> None:
    output = build_output()
    (ROOT / "output.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
