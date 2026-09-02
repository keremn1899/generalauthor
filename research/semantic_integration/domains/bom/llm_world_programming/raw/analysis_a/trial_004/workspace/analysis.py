#!/usr/bin/env python3
"""Compute context-scoped replacement state from the authoritative sources."""

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
    """Extract each replacement review record and its deployment context."""
    sections = re.split(r"(?m)^##\s+", notes)[1:]
    candidates: list[dict[str, str]] = []

    for section in sections:
        heading, _, body = section.partition("\n")
        candidate = re.search(
            r"Candidate:\s*`([^`]+)`\s+replaces\s+`([^`]+)`", body
        )
        context = re.search(r"`([^`]+)`\s+context\b", body)
        if not candidate or not context:
            continue
        candidates.append(
            {
                "section": heading.strip(),
                "new_part": candidate.group(1),
                "old_part": candidate.group(2),
                "context": context.group(1),
                "judgment": body,
            }
        )

    return candidates


def semantic_state(judgment: str) -> tuple[str, str]:
    """Classify explicit prose judgments without turning absence into rejection."""
    normalized = " ".join(judgment.lower().split())

    negative = (
        r"\bnot\s+(?:an?\s+)?acceptable\b",
        r"\bunacceptable\b",
        r"\breject(?:ed|s|ion)?\b",
        r"\bmust\s+not\s+(?:be\s+)?(?:use|used|substitute|replace)\b",
    )
    positive = (
        r"\bacceptable substitute\b",
        r"\baccepted replacement\b",
        r"\bengineering acceptance judgment\b",
        r"\bpreferred fallback\b",
        r"\bapproved\b",
    )
    uncertainty = (
        r"\bunder review\b",
        r"\b(?:remains?|is)\s+unresolved\b",
        r"\bpending\b",
        r"\bnot yet (?:determined|decided|established)\b",
    )

    if any(re.search(pattern, normalized) for pattern in negative):
        return "not_established", "NOT_KNOWN"
    if any(re.search(pattern, normalized) for pattern in positive):
        return "accepted", "ASSERTED_TRUE"
    if any(re.search(pattern, normalized) for pattern in uncertainty):
        return "unresolved", "UNRESOLVED"
    return "not_established", "NOT_KNOWN"


def mechanically_suitable(
    part: dict[str, str] | None, bom_items: list[dict[str, str]]
) -> bool:
    if part is None or not bom_items:
        return False

    rated_voltage = float(part["rated_voltage_v"])
    part_min_temp = float(part["min_temp_c"])
    part_max_temp = float(part["max_temp_c"])

    return all(
        part["part_type"] == item["part_type"]
        and rated_voltage == float(item["required_voltage_v"])
        and part_min_temp <= float(item["min_temp_c"])
        and part_max_temp >= float(item["max_temp_c"])
        for item in bom_items
    )


def build_support(
    case: dict[str, Any], candidate: dict[str, str]
) -> list[dict[str, Any]]:
    section = candidate["section"]
    bom_locators = [item.removeprefix("bom:") for item in case["bom_items"]]
    evidence = [
        {"source": "sources/engineering_notes.md", "locator": section},
        {
            "source": "sources/manufacturer.csv",
            "locator": f"part_number={candidate['new_part']}",
        },
    ]
    evidence.extend(
        {
            "source": "sources/bom.csv",
            "locator": f"bom_item={bom_item}",
        }
        for bom_item in bom_locators
    )
    return [
        {
            "claim": (
                f"{case['new_part']} replaces {case['old_part']} in "
                f"{case['context']}; its BOM items are "
                f"{', '.join(case['bom_items'])}; mechanical state is "
                f"{case['mechanical_state']} and semantic state is "
                f"{case['semantic_state']}."
            ),
            "evidence": evidence,
        }
    ]


def main() -> None:
    manufacturer_rows = read_csv("manufacturer.csv")
    bom_rows = read_csv("bom.csv")
    parts = {row["part_number"]: row for row in manufacturer_rows}
    notes = (SOURCES / "engineering_notes.md").read_text(encoding="utf-8")
    candidates = parse_candidates(notes)

    cases: list[dict[str, Any]] = []
    candidate_by_key: dict[tuple[str, str, str], dict[str, str]] = {}

    for candidate in candidates:
        context = candidate["context"]
        context_items = [
            row for row in bom_rows if row["deployment_environment"] == context
        ]
        semantic, epistemic = semantic_state(candidate["judgment"])
        case = {
            "new_part": identifier("part", candidate["new_part"]),
            "old_part": identifier("part", candidate["old_part"]),
            "context": identifier("context", context),
            "bom_items": sorted(
                identifier("bom", row["bom_item"]) for row in context_items
            ),
            "mechanical_state": (
                "suitable"
                if mechanically_suitable(parts.get(candidate["new_part"]), context_items)
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
    support: list[dict[str, Any]] = []
    if cases:
        first = cases[0]
        key = (first["new_part"], first["old_part"], first["context"])
        support = build_support(first, candidate_by_key[key])

    result = {"task": "replacement_state", "cases": cases, "support": support}
    with (ROOT / "output.json").open("w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")


if __name__ == "__main__":
    main()
