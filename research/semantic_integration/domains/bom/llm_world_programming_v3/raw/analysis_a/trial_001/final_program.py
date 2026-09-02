#!/usr/bin/env python3
"""Compute replacement-candidate states from the authoritative source files."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / "sources"


def read_csv(name: str, key: str) -> dict[str, dict[str, str]]:
    with (SOURCES / name).open(newline="", encoding="utf-8") as stream:
        return {row[key]: row for row in csv.DictReader(stream)}


def identifier(kind: str, value: str) -> str:
    return f"{kind}:{value}"


def parse_candidates(notes: str) -> list[dict[str, str]]:
    sections = re.split(r"(?=^##\s+ER-\d+\s*$)", notes, flags=re.MULTILINE)
    candidates: list[dict[str, str]] = []

    for section in sections:
        heading = re.search(r"^##\s+(ER-\d+)\s*$", section, re.MULTILINE)
        pair = re.search(
            r"Candidate:\s*`([^`]+)`\s+replaces\s+`([^`]+)`", section
        )
        context = re.search(r"`([^`]+)`\s+context", section)
        if not (heading and pair and context):
            continue
        prose = " ".join(section.split())

        # These phrases express an affirmative engineering judgment. Ratings
        # alone, or the mere presence of a candidate record, do not.
        accepted = bool(
            re.search(
                r"\bacceptable substitute\b|\bpreferred fallback\b|"
                r"\bengineering acceptance judgment\b",
                prose,
                flags=re.IGNORECASE,
            )
        )
        unresolved = bool(
            re.search(
                r"\b(?:acceptance|substitution)\s+(?:is\s+)?unresolved\b|"
                r"\bpending (?:engineering )?(?:review|acceptance)\b",
                prose,
                flags=re.IGNORECASE,
            )
        )

        if unresolved:
            semantic_state, epistemic = "unresolved", "UNRESOLVED"
        elif accepted:
            semantic_state, epistemic = "accepted", "ASSERTED_TRUE"
        else:
            semantic_state, epistemic = "not_established", "NOT_KNOWN"

        candidates.append(
            {
                "record": heading.group(1),
                "new_part": pair.group(1),
                "old_part": pair.group(2),
                "context": context.group(1),
                "semantic_state": semantic_state,
                "epistemic": epistemic,
            }
        )

    return candidates


def mechanically_suitable(part: dict[str, str], bom_rows: list[dict[str, str]]) -> bool:
    return all(
        part["part_type"] == item["part_type"]
        and int(part["rated_voltage_v"]) == int(item["required_voltage_v"])
        and int(part["min_temp_c"]) <= int(item["min_temp_c"])
        and int(part["max_temp_c"]) >= int(item["max_temp_c"])
        for item in bom_rows
    )


def main() -> None:
    parts = read_csv("manufacturer.csv", "part_number")
    bom = read_csv("bom.csv", "bom_item")
    notes = (SOURCES / "engineering_notes.md").read_text(encoding="utf-8")

    # Supplier listings are read as an authoritative input and checked for
    # referential integrity, even though availability is not a suitability or
    # acceptance criterion in the requested output.
    with (SOURCES / "suppliers.json").open(encoding="utf-8") as stream:
        supplier_data: dict[str, Any] = json.load(stream)
    listed_parts = {
        row["manufacturer_part_number"] for row in supplier_data["listings"]
    }

    cases: list[dict[str, Any]] = []
    parsed = parse_candidates(notes)
    for candidate in parsed:
        new_number = candidate["new_part"]
        old_number = candidate["old_part"]
        if new_number not in parts or old_number not in parts:
            raise ValueError(f"Unknown part in {candidate['record']}")
        if new_number not in listed_parts:
            raise ValueError(f"No supplier listing for candidate {new_number}")

        context = candidate["context"]
        context_bom = sorted(
            (
                item
                for item in bom.values()
                if item["deployment_environment"] == context
            ),
            key=lambda item: item["bom_item"],
        )
        if not context_bom:
            raise ValueError(f"No BOM items for context {context}")

        cases.append(
            {
                "new_part": identifier("part", new_number),
                "old_part": identifier("part", old_number),
                "context": identifier("context", context),
                "bom_items": [
                    identifier("bom", item["bom_item"]) for item in context_bom
                ],
                "mechanical_state": (
                    "suitable"
                    if mechanically_suitable(parts[new_number], context_bom)
                    else "unsuitable"
                ),
                "semantic_state": candidate["semantic_state"],
                "epistemic": candidate["epistemic"],
            }
        )

    cases.sort(key=lambda case: (case["new_part"], case["old_part"], case["context"]))

    support: list[dict[str, Any]] = []
    if cases:
        first = cases[0]
        raw = next(
            item
            for item in parsed
            if identifier("part", item["new_part"]) == first["new_part"]
            and identifier("part", item["old_part"]) == first["old_part"]
            and identifier("context", item["context"]) == first["context"]
        )
        part_number = raw["new_part"]
        bom_numbers = [value.removeprefix("bom:") for value in first["bom_items"]]
        support = [
            {
                "claim": (
                    f"{first['new_part']} replaces {first['old_part']} in "
                    f"{first['context']} with semantic state "
                    f"{first['semantic_state']}."
                ),
                "evidence": [
                    {
                        "source": "sources/engineering_notes.md",
                        "locator": f"section {raw['record']}",
                    }
                ],
            },
            {
                "claim": (
                    f"{first['new_part']} is mechanically {first['mechanical_state']} "
                    f"for {', '.join(first['bom_items'])}."
                ),
                "evidence": [
                    {
                        "source": "sources/manufacturer.csv",
                        "locator": f"part_number={part_number}",
                    },
                    *[
                        {
                            "source": "sources/bom.csv",
                            "locator": f"bom_item={bom_number}",
                        }
                        for bom_number in bom_numbers
                    ],
                ],
            },
        ]

    result = {"task": "replacement_state", "cases": cases, "support": support}
    (ROOT / "output.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
