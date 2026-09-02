#!/usr/bin/env python3
"""Derive contextual replacement state from the authoritative source files."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / "sources"


def read_csv(name: str, key: str) -> dict[str, dict[str, str]]:
    with (SOURCES / name).open(newline="", encoding="utf-8") as source:
        return {row[key]: row for row in csv.DictReader(source)}


def normalized_markdown(name: str) -> str:
    text = (SOURCES / name).read_text(encoding="utf-8")
    # Some exported evidence files annotate selected lines as ``10|...``.
    return re.sub(r"(?m)^\s*\d+\|", "", text)


def candidate_sections(text: str) -> list[tuple[str, str]]:
    headings = list(re.finditer(r"(?m)^##\s+([^\n]+?)\s*$", text))
    return [
        (
            match.group(1),
            text[
                match.end() : (
                    headings[index + 1].start()
                    if index + 1 < len(headings)
                    else len(text)
                )
            ],
        )
        for index, match in enumerate(headings)
    ]


def semantic_state(section: str) -> tuple[str, str]:
    prose = " ".join(section.lower().split())

    negative_or_open = (
        r"\b(?:not acceptable|unacceptable|rejected|not approved)\b",
        r"\b(?:unresolved|undecided|pending (?:review|approval|qualification))\b",
    )
    if any(re.search(pattern, prose) for pattern in negative_or_open):
        return "unresolved", "UNRESOLVED"

    positive = (
        r"\bacceptable substitute\b",
        r"\bpreferred fallback\b",
        r"\bengineering acceptance judgment\b",
        r"\b(?:accepted|approved) (?:replacement|substitute|fallback)\b",
    )
    if any(re.search(pattern, prose) for pattern in positive):
        return "accepted", "ASSERTED_TRUE"

    return "not_established", "NOT_KNOWN"


def mechanically_suitable(part: dict[str, str], item: dict[str, str]) -> bool:
    return (
        part["part_type"] == item["part_type"]
        and float(part["rated_voltage_v"]) == float(item["required_voltage_v"])
        and float(part["min_temp_c"]) <= float(item["min_temp_c"])
        and float(part["max_temp_c"]) >= float(item["max_temp_c"])
    )


def derive_cases(
    parts: dict[str, dict[str, str]],
    bom: dict[str, dict[str, str]],
    notes: str,
) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []

    for _, section in candidate_sections(notes):
        candidate = re.search(
            r"(?im)^\s*Candidate:\s*`([^`]+)`\s+replaces\s+`([^`]+)`\s*\.",
            section,
        )
        context_match = re.search(
            r"(?i)\bFor the\s+`([^`]+)`\s+context\b", section
        )
        if candidate is None or context_match is None:
            continue

        new_number, old_number = candidate.groups()
        context = context_match.group(1)
        context_items = sorted(
            (
                item
                for item in bom.values()
                if item["deployment_environment"] == context
            ),
            key=lambda item: item["bom_item"],
        )
        if new_number not in parts:
            raise ValueError(f"Candidate part {new_number!r} is absent from manufacturer.csv")
        if old_number not in parts:
            raise ValueError(f"Replaced part {old_number!r} is absent from manufacturer.csv")
        if not context_items:
            raise ValueError(f"Context {context!r} has no BOM items")

        semantic, epistemic = semantic_state(section)
        cases.append(
            {
                "new_part": f"part:{new_number}",
                "old_part": f"part:{old_number}",
                "context": f"context:{context}",
                "bom_items": [
                    f"bom:{item['bom_item']}" for item in context_items
                ],
                "mechanical_state": (
                    "suitable"
                    if all(
                        mechanically_suitable(parts[new_number], item)
                        for item in context_items
                    )
                    else "unsuitable"
                ),
                "semantic_state": semantic,
                "epistemic": epistemic,
            }
        )

    return sorted(
        cases,
        key=lambda case: (case["new_part"], case["old_part"], case["context"]),
    )


def evidence_for_first_case(
    case: dict[str, Any], notes: str
) -> list[dict[str, Any]]:
    new_number = case["new_part"].removeprefix("part:")
    old_number = case["old_part"].removeprefix("part:")
    context = case["context"].removeprefix("context:")

    section_name = next(
        name
        for name, section in candidate_sections(notes)
        if re.search(
            rf"(?im)^\s*Candidate:\s*`{re.escape(new_number)}`"
            rf"\s+replaces\s+`{re.escape(old_number)}`\s*\.",
            section,
        )
        and re.search(
            rf"(?i)\bFor the\s+`{re.escape(context)}`\s+context\b", section
        )
    )

    evidence = [
        {
            "source": "sources/engineering_notes.md",
            "locator": f"section={section_name}",
        },
        {
            "source": "sources/manufacturer.csv",
            "locator": f"part_number={new_number}",
        },
        {
            "source": "sources/manufacturer.csv",
            "locator": f"part_number={old_number}",
        },
    ]
    evidence.extend(
        {
            "source": "sources/bom.csv",
            "locator": f"bom_item={item.removeprefix('bom:')}",
        }
        for item in case["bom_items"]
    )

    claim = (
        f"{case['new_part']} replaces {case['old_part']} in {case['context']}; "
        f"BOM items {', '.join(case['bom_items'])}; "
        f"mechanical_state={case['mechanical_state']}; "
        f"semantic_state={case['semantic_state']}; epistemic={case['epistemic']}"
    )
    return [{"claim": claim, "evidence": evidence}]


def main() -> None:
    parts = read_csv("manufacturer.csv", "part_number")
    bom = read_csv("bom.csv", "bom_item")
    notes = normalized_markdown("engineering_notes.md")
    cases = derive_cases(parts, bom, notes)
    if not cases:
        raise ValueError("No replacement candidate/context cases were found")

    result = {
        "task": "replacement_state",
        "cases": cases,
        "support": evidence_for_first_case(cases[0], notes),
    }
    (ROOT / "output.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
