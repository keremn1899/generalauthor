#!/usr/bin/env python3
"""Compute replacement-candidate state from the authoritative source files."""

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


def parse_candidates(notes: str) -> list[dict[str, str]]:
    """Extract each candidate, its deployment context, and its judgment text."""
    sections = re.split(r"(?m)^##\s+", notes)[1:]
    candidates: list[dict[str, str]] = []

    for section in sections:
        heading, _, body = section.partition("\n")
        candidate_match = re.search(
            r"Candidate:\s*`([^`]+)`\s+replaces\s+`([^`]+)`", body
        )
        context_match = re.search(r"For the `([^`]+)` context", body)
        if not candidate_match or not context_match:
            continue
        candidates.append(
            {
                "section": heading.strip(),
                "new_part": candidate_match.group(1),
                "old_part": candidate_match.group(2),
                "context": context_match.group(1),
                "judgment": body,
            }
        )

    return candidates


def mechanical_state(
    part: dict[str, str], bom_items: list[dict[str, str]]
) -> str:
    """Check type, voltage, and temperature envelope for every BOM item."""
    suitable = all(
        part["part_type"] == item["part_type"]
        and float(part["rated_voltage_v"]) == float(item["required_voltage_v"])
        and float(part["min_temp_c"]) <= float(item["min_temp_c"])
        and float(part["max_temp_c"]) >= float(item["max_temp_c"])
        for item in bom_items
    )
    return "suitable" if suitable else "unsuitable"


def semantic_state(judgment: str) -> str:
    text = " ".join(judgment.lower().split())

    # Explicit positive engineering judgments remain acceptance judgments even
    # when the source says that tabulated data alone cannot establish them.
    positive = (
        r"\bacceptable substitute\b",
        r"\bpreferred fallback\b",
        r"\bacceptance judgment\b",
        r"\baccepted\b",
        r"\bapproved\b",
    )
    if any(re.search(pattern, text) for pattern in positive):
        return "accepted"

    unresolved = (
        r"\bunresolved\b",
        r"\bpending (?:review|qualification|approval)\b",
        r"\b(?:review|qualification|approval) (?:is )?pending\b",
        r"\bno (?:engineering )?(?:decision|judgment) has been made\b",
    )
    if any(re.search(pattern, text) for pattern in unresolved):
        return "unresolved"

    # Lack of a positive judgment is absence of knowledge, not rejection.
    return "not_established"


def epistemic_class(state: str) -> str:
    return {
        "accepted": "ASSERTED_TRUE",
        "unresolved": "UNRESOLVED",
        "not_established": "NOT_KNOWN",
    }[state]


def main() -> None:
    manufacturers = read_csv("manufacturer.csv", "part_number")
    bom = read_csv("bom.csv", "bom_item")
    notes = (SOURCES / "engineering_notes.md").read_text(encoding="utf-8")

    cases: list[dict[str, Any]] = []
    candidate_metadata: dict[tuple[str, str, str], dict[str, str]] = {}

    for candidate in parse_candidates(notes):
        new_number = candidate["new_part"]
        context_name = candidate["context"]
        contextual_bom = sorted(
            (
                row
                for row in bom.values()
                if row["deployment_environment"] == context_name
            ),
            key=lambda row: row["bom_item"],
        )
        state = semantic_state(candidate["judgment"])

        case = {
            "new_part": f"part:{new_number}",
            "old_part": f"part:{candidate['old_part']}",
            "context": f"context:{context_name}",
            "bom_items": [f"bom:{row['bom_item']}" for row in contextual_bom],
            "mechanical_state": mechanical_state(
                manufacturers[new_number], contextual_bom
            ),
            "semantic_state": state,
            "epistemic": epistemic_class(state),
        }
        cases.append(case)
        candidate_metadata[
            (case["new_part"], case["old_part"], case["context"])
        ] = candidate

    cases.sort(key=lambda case: (case["new_part"], case["old_part"], case["context"]))

    support: list[dict[str, Any]] = []
    if cases:
        case = cases[0]
        metadata = candidate_metadata[
            (case["new_part"], case["old_part"], case["context"])
        ]
        bom_locators = ", ".join(
            f"row {item.removeprefix('bom:')}" for item in case["bom_items"]
        )
        claim = (
            f"{case['new_part']} replaces {case['old_part']} in {case['context']}; "
            f"it applies to {', '.join(case['bom_items'])}, is mechanically "
            f"{case['mechanical_state']}, and is semantically "
            f"{case['semantic_state']}."
        )
        support.append(
            {
                "claim": claim,
                "evidence": [
                    {
                        "source": "sources/engineering_notes.md",
                        "locator": f"section {metadata['section']}",
                    },
                    {
                        "source": "sources/bom.csv",
                        "locator": bom_locators,
                    },
                    {
                        "source": "sources/manufacturer.csv",
                        "locator": (
                            f"row {metadata['new_part']} "
                            "(part type, voltage, and temperature ratings)"
                        ),
                    },
                ],
            }
        )

    result = {"task": "replacement_state", "cases": cases, "support": support}
    (ROOT / "output.json").write_text(
        json.dumps(result, indent=2, sort_keys=False) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
