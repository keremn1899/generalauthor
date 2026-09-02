#!/usr/bin/env python3
"""Compute replacement state from the authoritative files in sources/."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / "sources"


def read_csv(name: str) -> list[dict[str, str]]:
    with (SOURCES / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def identifier(kind: str, value: str) -> str:
    return f"{kind}:{value}"


def parse_candidates(notes: str) -> list[dict[str, str]]:
    """Extract candidate records while retaining each note's evidence section."""
    sections = re.split(r"(?m)^##\s+", notes)
    candidates: list[dict[str, str]] = []

    for section in sections[1:]:
        heading, _, body = section.partition("\n")
        match = re.search(
            r"Candidate:\s*`([^`]+)`\s+replaces\s+`([^`]+)`\.", body
        )
        context_match = re.search(r"`([^`]+)`\s+context\s+used\s+by\s+([A-Za-z0-9_-]+)", body)
        if not match or not context_match:
            continue
        candidates.append(
            {
                "new_part": match.group(1),
                "old_part": match.group(2),
                "context": context_match.group(1),
                "named_bom": context_match.group(2),
                "section": heading.strip(),
                "text": body,
            }
        )
    return candidates


def semantic_state(text: str) -> tuple[str, str]:
    """Classify explicit judgments without equating absent approval with rejection."""
    normalized = " ".join(text.lower().split())
    positive_patterns = (
        r"\bacceptable substitute\b",
        r"\bacceptance judgment\b",
        r"\baccepted\b",
        r"\bapproved\b",
    )
    unresolved_patterns = (
        r"\bunresolved\b",
        r"\bpending (?:review|approval|qualification)\b",
        r"\bno consensus\b",
    )

    if any(re.search(pattern, normalized) for pattern in positive_patterns):
        return "accepted", "ASSERTED_TRUE"
    if any(re.search(pattern, normalized) for pattern in unresolved_patterns):
        return "unresolved", "UNRESOLVED"
    return "not_established", "NOT_KNOWN"


def is_mechanically_suitable(part: dict[str, str], bom: dict[str, str]) -> bool:
    """Test the mechanical/electrical requirements represented in the tables."""
    return (
        part["part_type"] == bom["part_type"]
        and float(part["rated_voltage_v"]) >= float(bom["required_voltage_v"])
        and float(part["min_temp_c"]) <= float(bom["min_temp_c"])
        and float(part["max_temp_c"]) >= float(bom["max_temp_c"])
    )


def csv_locator(filename: str, key: str, value: str) -> str:
    return f"{filename} row where {key}={value}"


def main() -> None:
    bom_rows = read_csv("bom.csv")
    parts = {
        row["part_number"]: row
        for row in read_csv("manufacturer.csv")
    }
    notes = (SOURCES / "engineering_notes.md").read_text(encoding="utf-8")
    candidates = parse_candidates(notes)

    cases: list[dict[str, Any]] = []
    case_metadata: list[dict[str, Any]] = []
    for candidate in candidates:
        context_boms = [
            row for row in bom_rows
            if row["deployment_environment"] == candidate["context"]
        ]
        new_part = parts[candidate["new_part"]]
        mechanical = all(
            is_mechanically_suitable(new_part, bom) for bom in context_boms
        )
        semantic, epistemic = semantic_state(candidate["text"])

        case = {
            "new_part": identifier("part", candidate["new_part"]),
            "old_part": identifier("part", candidate["old_part"]),
            "context": identifier("context", candidate["context"]),
            "bom_items": sorted(
                identifier("bom", row["bom_item"]) for row in context_boms
            ),
            "mechanical_state": "suitable" if mechanical else "unsuitable",
            "semantic_state": semantic,
            "epistemic": epistemic,
        }
        cases.append(case)
        case_metadata.append(
            {"case": case, "candidate": candidate, "boms": context_boms}
        )

    cases.sort(key=lambda row: (row["new_part"], row["old_part"], row["context"]))

    # Trace the first sorted case through the note and both requirement tables.
    support: list[dict[str, Any]] = []
    if cases:
        selected_case = cases[0]
        metadata = next(item for item in case_metadata if item["case"] is selected_case)
        candidate = metadata["candidate"]
        support.append(
            {
                "claim": (
                    f"{selected_case['new_part']} replaces {selected_case['old_part']} "
                    f"in {selected_case['context']}; semantic state is "
                    f"{selected_case['semantic_state']}."
                ),
                "evidence": [
                    {
                        "source": "sources/engineering_notes.md",
                        "locator": (
                            f"section {candidate['section']}, Candidate line and "
                            "deployment-context judgment"
                        ),
                    }
                ],
            }
        )
        mechanical_evidence = [
            {
                "source": "sources/manufacturer.csv",
                "locator": csv_locator(
                    "manufacturer.csv", "part_number", candidate["new_part"]
                ),
            }
        ]
        mechanical_evidence.extend(
            {
                "source": "sources/bom.csv",
                "locator": csv_locator("bom.csv", "bom_item", bom["bom_item"]),
            }
            for bom in metadata["boms"]
        )
        support.append(
            {
                "claim": (
                    f"{selected_case['new_part']} is mechanically "
                    f"{selected_case['mechanical_state']} for "
                    f"{', '.join(selected_case['bom_items'])}."
                ),
                "evidence": mechanical_evidence,
            }
        )

    result = {
        "task": "replacement_state",
        "cases": cases,
        "support": support,
    }
    with (ROOT / "output.json").open("w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")


if __name__ == "__main__":
    main()
