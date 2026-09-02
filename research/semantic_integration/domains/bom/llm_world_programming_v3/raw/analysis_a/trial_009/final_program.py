#!/usr/bin/env python3
"""Compute replacement state from the authoritative workspace sources."""

from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / "sources"


def read_csv(name: str) -> list[dict[str, str]]:
    with (SOURCES / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def parse_engineering_notes() -> list[dict[str, str]]:
    text = (SOURCES / "engineering_notes.md").read_text(encoding="utf-8")
    sections = re.split(r"(?m)^##\s+", text)[1:]
    records: list[dict[str, str]] = []

    for section in sections:
        heading, _, body = section.partition("\n")
        candidate = re.search(
            r"Candidate:\s*`([^`]+)`\s+replaces\s+`([^`]+)`", body
        )
        application = re.search(
            r"For the\s+`([^`]+)`\s+context used by\s+(BOM-[A-Za-z0-9_-]+)",
            body,
        )
        if not candidate or not application:
            continue

        normalized = " ".join(body.split())
        # A stated substitute/fallback is accepted only when it is not
        # contingent on an unestablished condition.  A conditional judgment is
        # represented as unresolved, rather than silently promoted or rejected.
        conditional = bool(
            re.search(
                r"\b(?:preferred fallback|acceptable substitute)\b[^.]*\bif\b",
                normalized,
                flags=re.IGNORECASE,
            )
        )
        positive = bool(
            re.search(
                r"\b(?:preferred fallback|acceptable substitute|acceptance judgment)\b",
                normalized,
                flags=re.IGNORECASE,
            )
        )
        semantic = (
            "unresolved" if conditional else "accepted" if positive else "not_established"
        )
        records.append(
            {
                "section": heading.strip(),
                "new_part": candidate.group(1),
                "old_part": candidate.group(2),
                "context": application.group(1),
                "named_bom_item": application.group(2),
                "semantic_state": semantic,
            }
        )
    return records


def mechanically_suitable(part: dict[str, str], item: dict[str, str]) -> bool:
    return (
        part["part_type"] == item["part_type"]
        and float(part["rated_voltage_v"]) == float(item["required_voltage_v"])
        and float(part["min_temp_c"]) <= float(item["min_temp_c"])
        and float(part["max_temp_c"]) >= float(item["max_temp_c"])
    )


def main() -> None:
    bom = read_csv("bom.csv")
    parts = {row["part_number"]: row for row in read_csv("manufacturer.csv")}
    notes = parse_engineering_notes()

    noted_state = {
        (record["new_part"], record["old_part"], record["context"]): record
        for record in notes
    }
    candidates = sorted({(r["new_part"], r["old_part"]) for r in notes})

    # A replacement pair applies to BOM requirements having the old part's
    # part type. Group those requirements by their deployment context.
    cases: list[dict[str, object]] = []
    raw_cases: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for new_number, old_number in candidates:
        old_part = parts[old_number]
        for item in bom:
            if item["part_type"] == old_part["part_type"]:
                raw_cases[
                    (new_number, old_number, item["deployment_environment"])
                ].append(item)

    epistemic_for = {
        "accepted": "ASSERTED_TRUE",
        "unresolved": "UNRESOLVED",
        "not_established": "NOT_KNOWN",
    }
    for (new_number, old_number, context), items in raw_cases.items():
        note = noted_state.get((new_number, old_number, context))
        semantic = note["semantic_state"] if note else "not_established"
        suitable = all(mechanically_suitable(parts[new_number], item) for item in items)
        cases.append(
            {
                "new_part": f"part:{new_number}",
                "old_part": f"part:{old_number}",
                "context": f"context:{context}",
                "bom_items": sorted(f"bom:{item['bom_item']}" for item in items),
                "mechanical_state": "suitable" if suitable else "unsuitable",
                "semantic_state": semantic,
                "epistemic": epistemic_for[semantic],
            }
        )

    cases.sort(key=lambda case: (case["new_part"], case["old_part"], case["context"]))

    # Trace an asserted case through the note, BOM requirement, and ratings.
    support: list[dict[str, object]] = []
    supported_note = next(
        (record for record in notes if record["semantic_state"] == "accepted"), None
    )
    if supported_note:
        new_number = supported_note["new_part"]
        old_number = supported_note["old_part"]
        context = supported_note["context"]
        item_number = supported_note["named_bom_item"]
        support.append(
            {
                "claim": (
                    f"part:{new_number} replaces part:{old_number} for "
                    f"bom:{item_number} in context:{context}; the replacement is "
                    "mechanically suitable and semantically accepted"
                ),
                "evidence": [
                    {
                        "source": "sources/engineering_notes.md",
                        "locator": f"section {supported_note['section']}",
                    },
                    {
                        "source": "sources/bom.csv",
                        "locator": f"row bom_item={item_number}",
                    },
                    {
                        "source": "sources/manufacturer.csv",
                        "locator": f"row part_number={new_number}",
                    },
                ],
            }
        )

    result = {"task": "replacement_state", "cases": cases, "support": support}
    (ROOT / "output.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
