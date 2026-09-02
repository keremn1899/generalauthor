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
    with (SOURCES / name).open(newline="", encoding="utf-8") as source:
        return {row[key]: row for row in csv.DictReader(source)}


def read_bom() -> list[dict[str, str]]:
    with (SOURCES / "bom.csv").open(newline="", encoding="utf-8") as source:
        return list(csv.DictReader(source))


def parse_candidates() -> list[dict[str, str]]:
    text = (SOURCES / "engineering_notes.md").read_text(encoding="utf-8")
    sections = re.finditer(
        r"^##\s+(?P<record>[^\n]+)\s*$"
        r"(?P<body>.*?)(?=^##\s+|\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    candidates: list[dict[str, str]] = []
    for section in sections:
        body = section.group("body")
        pair = re.search(
            r"Candidate:\s*`(?P<new>[^`]+)`\s+replaces\s+`(?P<old>[^`]+)`",
            body,
            flags=re.IGNORECASE,
        )
        context = re.search(
            r"(?:For|In)\s+the\s+`(?P<context>[^`]+)`\s+context\b",
            body,
            flags=re.IGNORECASE,
        )
        if pair and context:
            candidates.append(
                {
                    "record": section.group("record").strip(),
                    "new": pair.group("new").strip(),
                    "old": pair.group("old").strip(),
                    "context": context.group("context").strip(),
                    "judgment": body,
                }
            )
    return candidates


def semantic_state(judgment: str) -> tuple[str, str]:
    judgment = " ".join(judgment.split())
    positive = (
        r"\bpreferred fallback\b",
        r"\bacceptable substitute\b",
        r"\baccepted\b",
        r"\bapproved\b",
        r"\bengineering acceptance judgment\b",
    )
    unresolved = (
        r"\bunresolved\b",
        r"\bpending (?:review|qualification|approval)\b",
        r"\b(?:acceptance|suitability) (?:is )?not (?:yet )?determined\b",
        r"\bconflicting (?:judgments|evidence)\b",
    )
    if any(re.search(pattern, judgment, re.IGNORECASE) for pattern in positive):
        return "accepted", "ASSERTED_TRUE"
    if any(re.search(pattern, judgment, re.IGNORECASE) for pattern in unresolved):
        return "unresolved", "UNRESOLVED"
    return "not_established", "NOT_KNOWN"


def mechanically_suitable(part: dict[str, str] | None, items: list[dict[str, str]]) -> bool:
    if part is None or not items:
        return False
    return all(
        part["part_type"] == item["part_type"]
        and float(part["rated_voltage_v"]) == float(item["required_voltage_v"])
        and float(part["min_temp_c"]) <= float(item["min_temp_c"])
        and float(part["max_temp_c"]) >= float(item["max_temp_c"])
        for item in items
    )


def build_support(
    case: dict[str, Any],
    candidate: dict[str, str],
) -> list[dict[str, Any]]:
    new_number = case["new_part"].removeprefix("part:")
    bom_numbers = [item.removeprefix("bom:") for item in case["bom_items"]]
    return [
        {
            "claim": (
                f"{case['new_part']} is an accepted replacement for "
                f"{case['old_part']} in {case['context']}."
            ),
            "evidence": [
                {
                    "source": "sources/engineering_notes.md",
                    "locator": f"section {candidate['record']}",
                }
            ],
        },
        {
            "claim": (
                f"{', '.join(case['bom_items'])} applies in {case['context']}."
            ),
            "evidence": [
                {
                    "source": "sources/bom.csv",
                    "locator": f"rows {', '.join(bom_numbers)}",
                }
            ],
        },
        {
            "claim": (
                f"{case['new_part']} is mechanically suitable for "
                f"{', '.join(case['bom_items'])}."
            ),
            "evidence": [
                {
                    "source": "sources/manufacturer.csv",
                    "locator": f"row {new_number}",
                },
                {
                    "source": "sources/bom.csv",
                    "locator": f"rows {', '.join(bom_numbers)}",
                },
            ],
        },
    ]


def main() -> None:
    parts = read_csv("manufacturer.csv", "part_number")
    bom = read_bom()
    candidates = parse_candidates()

    cases: list[dict[str, Any]] = []
    candidate_by_key: dict[tuple[str, str, str], dict[str, str]] = {}
    for candidate in candidates:
        items = [
            item
            for item in bom
            if item["deployment_environment"] == candidate["context"]
        ]
        semantic, epistemic = semantic_state(candidate["judgment"])
        case = {
            "new_part": f"part:{candidate['new']}",
            "old_part": f"part:{candidate['old']}",
            "context": f"context:{candidate['context']}",
            "bom_items": sorted(f"bom:{item['bom_item']}" for item in items),
            "mechanical_state": (
                "suitable"
                if mechanically_suitable(parts.get(candidate["new"]), items)
                else "unsuitable"
            ),
            "semantic_state": semantic,
            "epistemic": epistemic,
        }
        cases.append(case)
        candidate_by_key[
            (case["new_part"], case["old_part"], case["context"])
        ] = candidate

    cases.sort(key=lambda case: (case["new_part"], case["old_part"], case["context"]))
    support = (
        build_support(
            cases[0],
            candidate_by_key[
                (cases[0]["new_part"], cases[0]["old_part"], cases[0]["context"])
            ],
        )
        if cases
        else []
    )
    result = {"task": "replacement_state", "cases": cases, "support": support}
    (ROOT / "output.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
