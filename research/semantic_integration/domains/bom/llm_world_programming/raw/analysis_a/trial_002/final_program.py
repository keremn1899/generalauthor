#!/usr/bin/env python3
"""Compute replacement state from the authoritative source files."""

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


def part_id(part_number: str) -> str:
    return f"part:{part_number}"


def bom_id(bom_item: str) -> str:
    return f"bom:{bom_item}"


def context_id(environment: str) -> str:
    return f"context:{environment}"


def parse_candidates(notes: str) -> list[dict[str, str]]:
    """Extract candidate, replaced part, context, and judgment from each note."""
    candidates: list[dict[str, str]] = []
    section_pattern = re.compile(
        r"^##\s+(?P<label>[^\n]+)\s*$"
        r"(?P<body>.*?)(?=^##\s+|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    candidate_pattern = re.compile(
        r"Candidate:\s*`(?P<new>[^`]+)`\s+replaces\s+`(?P<old>[^`]+)`\.",
        re.IGNORECASE,
    )
    context_pattern = re.compile(
        r"For\s+the\s+`(?P<context>[^`]+)`\s+context\b",
        re.IGNORECASE,
    )

    for section in section_pattern.finditer(notes):
        body = section.group("body")
        candidate = candidate_pattern.search(body)
        context = context_pattern.search(body)
        if candidate is None or context is None:
            continue
        candidates.append(
            {
                "label": section.group("label").strip(),
                "new": candidate.group("new").strip(),
                "old": candidate.group("old").strip(),
                "context": context.group("context").strip(),
                "judgment": body,
            }
        )
    return candidates


def semantic_state(judgment: str) -> str:
    """Classify only explicit semantic judgments; silence remains unknown."""
    text = " ".join(judgment.lower().split())

    negative_or_open_patterns = (
        r"\bnot\s+(?:an?\s+)?acceptable\b",
        r"\bnot\s+accepted\b",
        r"\bacceptance\s+(?:is\s+)?pending\b",
        r"\b(?:remains?|is)\s+unresolved\b",
        r"\brequires?\s+(?:further\s+)?(?:review|qualification)\b",
    )
    if any(re.search(pattern, text) for pattern in negative_or_open_patterns):
        return "unresolved"

    positive_patterns = (
        r"\bacceptable substitute\b",
        r"\bpreferred fallback\b",
        r"\bengineering acceptance judgment\b",
        r"\b(?:is|was|has been)\s+accepted\b",
        r"\b(?:is|was|has been)\s+approved\b",
    )
    if any(re.search(pattern, text) for pattern in positive_patterns):
        return "accepted"

    explicit_open_patterns = (
        r"\bpending\b",
        r"\buncertain\b",
        r"\bnot (?:yet )?determined\b",
        r"\bneeds? review\b",
    )
    if any(re.search(pattern, text) for pattern in explicit_open_patterns):
        return "unresolved"
    return "not_established"


def mechanically_suitable(part: dict[str, str], items: list[dict[str, str]]) -> bool:
    if not items:
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
    listings_by_part: dict[str, list[str]],
) -> list[dict[str, Any]]:
    evidence = [
        {
            "source": "sources/engineering_notes.md",
            "locator": candidate["label"],
        },
        {
            "source": "sources/manufacturer.csv",
            "locator": f"part_number={candidate['new']}",
        },
    ]
    evidence.extend(
        {
            "source": "sources/bom.csv",
            "locator": f"bom_item={item.removeprefix('bom:')}",
        }
        for item in case["bom_items"]
    )
    evidence.extend(
        {
            "source": "sources/suppliers.json",
            "locator": f"listing:{sku}",
        }
        for sku in listings_by_part.get(candidate["new"], [])
    )
    return [
        {
            "claim": (
                f"{case['new_part']} replaces {case['old_part']} in "
                f"{case['context']}; mechanical_state={case['mechanical_state']}; "
                f"semantic_state={case['semantic_state']}"
            ),
            "evidence": evidence,
        }
    ]


def main() -> None:
    manufacturer = {
        row["part_number"]: row for row in read_csv("manufacturer.csv")
    }
    bom_rows = read_csv("bom.csv")
    notes = (SOURCES / "engineering_notes.md").read_text(encoding="utf-8")
    with (SOURCES / "suppliers.json").open(encoding="utf-8") as handle:
        supplier_data = json.load(handle)

    listings_by_part: dict[str, list[str]] = {}
    for listing in supplier_data["listings"]:
        listings_by_part.setdefault(
            listing["manufacturer_part_number"], []
        ).append(listing["sku"])
    for skus in listings_by_part.values():
        skus.sort()

    parsed_candidates = parse_candidates(notes)
    cases: list[dict[str, Any]] = []
    candidate_by_key: dict[tuple[str, str, str], dict[str, str]] = {}

    for candidate in parsed_candidates:
        part = manufacturer.get(candidate["new"])
        if part is None:
            raise ValueError(
                f"Candidate {candidate['new']} has no manufacturer record"
            )
        context_items = [
            row
            for row in bom_rows
            if row["deployment_environment"] == candidate["context"]
        ]
        semantic = semantic_state(candidate["judgment"])
        case = {
            "new_part": part_id(candidate["new"]),
            "old_part": part_id(candidate["old"]),
            "context": context_id(candidate["context"]),
            "bom_items": sorted(bom_id(row["bom_item"]) for row in context_items),
            "mechanical_state": (
                "suitable"
                if mechanically_suitable(part, context_items)
                else "unsuitable"
            ),
            "semantic_state": semantic,
            "epistemic": {
                "accepted": "ASSERTED_TRUE",
                "unresolved": "UNRESOLVED",
                "not_established": "NOT_KNOWN",
            }[semantic],
        }
        cases.append(case)
        candidate_by_key[
            (case["new_part"], case["old_part"], case["context"])
        ] = candidate

    cases.sort(key=lambda case: (
        case["new_part"],
        case["old_part"],
        case["context"],
    ))

    support: list[dict[str, Any]] = []
    if cases:
        first = cases[0]
        key = (first["new_part"], first["old_part"], first["context"])
        support = build_support(first, candidate_by_key[key], listings_by_part)

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
