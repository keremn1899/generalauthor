#!/usr/bin/env python3
"""Compute replacement states from the authoritative workspace sources."""

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


def engineering_candidates(notes: str) -> list[dict[str, str]]:
    """Extract each candidate and its context from an engineering-note section."""
    sections = re.split(r"(?m)^##\s+", notes)[1:]
    candidates: list[dict[str, str]] = []

    for section in sections:
        heading, _, body = section.partition("\n")
        candidate = re.search(
            r"Candidate:\s*`([^`]+)`\s+replaces\s+`([^`]+)`", body, re.I
        )
        context = re.search(r"(?:For|In)\s+the\s+`([^`]+)`\s+context", body, re.I)
        if not candidate or not context:
            continue

        normalized = " ".join(body.lower().split())
        positive = (
            "preferred fallback",
            "acceptable substitute",
            "accepted substitute",
            "approved substitute",
            "accepted replacement",
            "approved replacement",
        )
        unresolved = (
            "acceptance is unresolved",
            "acceptance remains unresolved",
            "pending acceptance",
            "pending review",
            "not yet resolved",
        )

        if any(phrase in normalized for phrase in positive):
            semantic_state = "accepted"
            epistemic = "ASSERTED_TRUE"
        elif any(phrase in normalized for phrase in unresolved):
            semantic_state = "unresolved"
            epistemic = "UNRESOLVED"
        else:
            # Silence is lack of knowledge, not a negative acceptance judgment.
            semantic_state = "not_established"
            epistemic = "NOT_KNOWN"

        candidates.append(
            {
                "new_part": candidate.group(1),
                "old_part": candidate.group(2),
                "context": context.group(1),
                "semantic_state": semantic_state,
                "epistemic": epistemic,
                "note_locator": heading.strip(),
            }
        )

    return candidates


def mechanically_suitable(part: dict[str, str], bom_rows: list[dict[str, str]]) -> bool:
    """Return whether one part satisfies every tabulated BOM requirement."""
    return all(
        part["part_type"] == bom["part_type"]
        and float(part["rated_voltage_v"]) == float(bom["required_voltage_v"])
        and float(part["min_temp_c"]) <= float(bom["min_temp_c"])
        and float(part["max_temp_c"]) >= float(bom["max_temp_c"])
        for bom in bom_rows
    )


def make_support(
    case: dict[str, Any],
    candidate: dict[str, str],
    bom_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    case_name = (
        f"{case['new_part']} replacing {case['old_part']} "
        f"in {case['context']}"
    )
    bom_evidence = [
        {
            "source": "sources/bom.csv",
            "locator": f"row bom_item={row['bom_item']}",
        }
        for row in sorted(bom_rows, key=lambda row: row["bom_item"])
    ]

    return [
        {
            "claim": f"{case_name} is an engineering replacement candidate "
            f"with semantic state {case['semantic_state']}",
            "evidence": [
                {
                    "source": "sources/engineering_notes.md",
                    "locator": f"section {candidate['note_locator']}",
                }
            ],
        },
        {
            "claim": f"{case['context']} contains {', '.join(case['bom_items'])}",
            "evidence": bom_evidence,
        },
        {
            "claim": f"{case['new_part']} is mechanically {case['mechanical_state']} "
            f"for the BOM items in {case['context']}",
            "evidence": [
                {
                    "source": "sources/manufacturer.csv",
                    "locator": f"row part_number={candidate['new_part']}",
                },
                *bom_evidence,
            ],
        },
    ]


def main() -> None:
    manufacturers = read_csv("manufacturer.csv", "part_number")
    bom = read_csv("bom.csv", "bom_item")
    notes = (SOURCES / "engineering_notes.md").read_text(encoding="utf-8")
    candidates = engineering_candidates(notes)

    cases: list[dict[str, Any]] = []
    source_by_case: dict[tuple[str, str, str], tuple[dict[str, str], list[dict[str, str]]]] = {}

    for candidate in candidates:
        context = candidate["context"]
        context_bom = [
            row for row in bom.values() if row["deployment_environment"] == context
        ]
        new_part = candidate["new_part"]
        if new_part not in manufacturers:
            raise ValueError(f"Candidate part {new_part!r} is absent from manufacturer.csv")
        if not context_bom:
            raise ValueError(f"Context {context!r} has no BOM items")

        case = {
            "new_part": f"part:{new_part}",
            "old_part": f"part:{candidate['old_part']}",
            "context": f"context:{context}",
            "bom_items": sorted(f"bom:{row['bom_item']}" for row in context_bom),
            "mechanical_state": (
                "suitable"
                if mechanically_suitable(manufacturers[new_part], context_bom)
                else "unsuitable"
            ),
            "semantic_state": candidate["semantic_state"],
            "epistemic": candidate["epistemic"],
        }
        cases.append(case)
        source_by_case[(case["new_part"], case["old_part"], case["context"])] = (
            candidate,
            context_bom,
        )

    cases.sort(key=lambda case: (case["new_part"], case["old_part"], case["context"]))
    support: list[dict[str, Any]] = []
    if cases:
        first = cases[0]
        key = (first["new_part"], first["old_part"], first["context"])
        support = make_support(first, *source_by_case[key])

    result = {"task": "replacement_state", "cases": cases, "support": support}
    (ROOT / "output.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
