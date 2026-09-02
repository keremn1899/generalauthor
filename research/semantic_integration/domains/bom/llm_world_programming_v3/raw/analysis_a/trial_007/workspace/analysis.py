#!/usr/bin/env python3
"""Derive replacement state from the authoritative workspace sources."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / "sources"


def read_csv(name: str, key: str) -> dict[str, dict[str, str]]:
    with (SOURCES / name).open(newline="", encoding="utf-8") as handle:
        return {row[key]: row for row in csv.DictReader(handle)}


def line_number(text: str, needle: str) -> int:
    for number, line in enumerate(text.splitlines(), 1):
        if needle in line:
            return number
    raise ValueError(f"{needle!r} was not found")


def mechanically_suitable(part: dict[str, str], items: list[dict[str, str]]) -> bool:
    return all(
        part["part_type"] == item["part_type"]
        and float(part["rated_voltage_v"]) >= float(item["required_voltage_v"])
        and float(part["min_temp_c"]) <= float(item["min_temp_c"])
        and float(part["max_temp_c"]) >= float(item["max_temp_c"])
        for item in items
    )


def semantic_state(section: str) -> tuple[str, str]:
    normalized = re.sub(r"\s+", " ", section).lower()

    # Explicit judgments take precedence over gaps in tabulated qualification
    # data: acceptance is semantic evidence, not a derived mechanical rating.
    positive = (
        r"\bacceptable substitute\b",
        r"\bengineering acceptance judgment\b",
        r"\bpreferred fallback\b",
    )
    unresolved = (
        r"\bacceptance (?:is |remains )?unresolved\b",
        r"\bpending (?:engineering )?(?:review|approval)\b",
        r"\bno (?:acceptance|decision) has been reached\b",
    )
    negative = (
        r"\bnot (?:an )?acceptable substitute\b",
        r"\brejected as (?:a )?substitute\b",
        r"\bnot approved\b",
    )

    if any(re.search(pattern, normalized) for pattern in negative):
        return "not_established", "ASSERTED_TRUE"
    if any(re.search(pattern, normalized) for pattern in positive):
        return "accepted", "ASSERTED_TRUE"
    if any(re.search(pattern, normalized) for pattern in unresolved):
        return "unresolved", "UNRESOLVED"
    return "not_established", "NOT_KNOWN"


def parse_candidates(notes: str) -> list[dict[str, str]]:
    sections = re.split(r"(?=^##\s+ER-[^\n]+\s*$)", notes, flags=re.MULTILINE)
    candidates: list[dict[str, str]] = []

    for section in sections:
        heading = re.search(r"^##\s+(ER-[^\n]+)\s*$", section, re.MULTILINE)
        candidate = re.search(
            r"Candidate:\s*`([^`]+)`\s+replaces\s+`([^`]+)`", section
        )
        scope = re.search(
            r"For the\s+`([^`]+)`\s+context used by\s+([A-Za-z0-9_-]+)",
            section,
        )
        if heading and candidate and scope:
            semantic, epistemic = semantic_state(section)
            candidates.append(
                {
                    "section": heading.group(1),
                    "new": candidate.group(1),
                    "old": candidate.group(2),
                    "context": scope.group(1),
                    "mentioned_bom": scope.group(2),
                    "semantic": semantic,
                    "epistemic": epistemic,
                }
            )
    return candidates


def main() -> None:
    parts = read_csv("manufacturer.csv", "part_number")
    bom = read_csv("bom.csv", "bom_item")
    notes = (SOURCES / "engineering_notes.md").read_text(encoding="utf-8")
    candidates = parse_candidates(notes)

    cases: list[dict[str, object]] = []
    for candidate in candidates:
        context_items = sorted(
            (
                item
                for item in bom.values()
                if item["deployment_environment"] == candidate["context"]
            ),
            key=lambda item: item["bom_item"],
        )
        suitable = mechanically_suitable(parts[candidate["new"]], context_items)
        cases.append(
            {
                "new_part": f"part:{candidate['new']}",
                "old_part": f"part:{candidate['old']}",
                "context": f"context:{candidate['context']}",
                "bom_items": [
                    f"bom:{item['bom_item']}" for item in context_items
                ],
                "mechanical_state": "suitable" if suitable else "unsuitable",
                "semantic_state": candidate["semantic"],
                "epistemic": candidate["epistemic"],
            }
        )

    cases.sort(key=lambda case: (case["new_part"], case["old_part"], case["context"]))

    support: list[dict[str, object]] = []
    if cases:
        first = cases[0]
        candidate = next(
            item
            for item in candidates
            if f"part:{item['new']}" == first["new_part"]
            and f"part:{item['old']}" == first["old_part"]
            and f"context:{item['context']}" == first["context"]
        )
        bom_ids = [item.removeprefix("bom:") for item in first["bom_items"]]
        candidate_line = line_number(
            notes, f"Candidate: `{candidate['new']}`"
        )
        context_line = line_number(
            notes, f"For the `{candidate['context']}` context"
        )
        support = [
            {
                "claim": (
                    f"{first['new_part']} replaces {first['old_part']} in "
                    f"{first['context']}, with semantic state "
                    f"{first['semantic_state']}."
                ),
                "evidence": [
                    {
                        "source": "sources/engineering_notes.md",
                        "locator": (
                            f"{candidate['section']}, lines "
                            f"{candidate_line} and {context_line}"
                        ),
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
                        "locator": f"row part_number={candidate['new']}",
                    },
                    *[
                        {
                            "source": "sources/bom.csv",
                            "locator": f"row bom_item={bom_id}",
                        }
                        for bom_id in bom_ids
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
