#!/usr/bin/env python3
"""Derive replacement-candidate state from the authoritative source files."""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / "sources"


@dataclass(frozen=True)
class Candidate:
    new_part: str
    old_part: str
    contexts: tuple[str, ...]
    section: str
    text: str


def read_csv(name: str, key: str) -> dict[str, dict[str, str]]:
    with (SOURCES / name).open(newline="", encoding="utf-8") as stream:
        return {row[key]: row for row in csv.DictReader(stream)}


def parse_candidates(notes: str, known_contexts: set[str]) -> list[Candidate]:
    headings = list(re.finditer(r"^##\s+(.+?)\s*$", notes, flags=re.MULTILINE))
    candidates: list[Candidate] = []

    for index, heading in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(notes)
        section_text = notes[heading.end() : end].strip()
        match = re.search(
            r"Candidate:\s*`?([A-Za-z0-9._-]+)`?\s+replaces\s+"
            r"`?([A-Za-z0-9._-]+)`?",
            section_text,
            flags=re.IGNORECASE,
        )
        if not match:
            continue

        mentioned_contexts = tuple(
            sorted(
                context
                for context in known_contexts
                if re.search(rf"`?{re.escape(context)}`?", section_text)
            )
        )
        candidates.append(
            Candidate(
                new_part=match.group(1),
                old_part=match.group(2),
                contexts=mentioned_contexts,
                section=heading.group(1),
                text=section_text,
            )
        )

    return candidates


def mechanically_suitable(part: dict[str, str], item: dict[str, str]) -> bool:
    return (
        part["part_type"] == item["part_type"]
        and Decimal(part["rated_voltage_v"]) == Decimal(item["required_voltage_v"])
        and Decimal(part["min_temp_c"]) <= Decimal(item["min_temp_c"])
        and Decimal(part["max_temp_c"]) >= Decimal(item["max_temp_c"])
    )


def semantic_state(text: str) -> tuple[str, str]:
    normalized = " ".join(text.lower().split())

    # Positive engineering judgments take precedence over caveats explaining
    # why the judgment cannot be inferred from tabulated specifications alone.
    accepted_cues = (
        "acceptable substitute",
        "engineering acceptance judgment",
        "accepted substitute",
        "approved substitute",
        "preferred fallback",
    )
    unresolved_cues = (
        "unresolved",
        "pending review",
        "under review",
        "acceptance pending",
    )

    if any(cue in normalized for cue in accepted_cues):
        return "accepted", "ASSERTED_TRUE"
    if any(cue in normalized for cue in unresolved_cues):
        return "unresolved", "UNRESOLVED"
    return "not_established", "NOT_KNOWN"


def part_id(part_number: str) -> str:
    return f"part:{part_number}"


def bom_id(bom_item: str) -> str:
    return f"bom:{bom_item}"


def context_id(context: str) -> str:
    return f"context:{context}"


def main() -> None:
    bom = read_csv("bom.csv", "bom_item")
    manufacturer = read_csv("manufacturer.csv", "part_number")
    notes = (SOURCES / "engineering_notes.md").read_text(encoding="utf-8")
    known_contexts = {row["deployment_environment"] for row in bom.values()}
    candidates = parse_candidates(notes, known_contexts)

    cases: list[dict[str, object]] = []
    case_sources: dict[tuple[str, str, str], tuple[Candidate, list[str]]] = {}

    for candidate in candidates:
        for context in candidate.contexts:
            item_names = sorted(
                name
                for name, row in bom.items()
                if row["deployment_environment"] == context
            )
            part = manufacturer.get(candidate.new_part)
            suitable = bool(part) and all(
                mechanically_suitable(part, bom[item_name])
                for item_name in item_names
            )
            semantic, epistemic = semantic_state(candidate.text)

            case = {
                "new_part": part_id(candidate.new_part),
                "old_part": part_id(candidate.old_part),
                "context": context_id(context),
                "bom_items": [bom_id(name) for name in item_names],
                "mechanical_state": "suitable" if suitable else "unsuitable",
                "semantic_state": semantic,
                "epistemic": epistemic,
            }
            cases.append(case)
            case_sources[(candidate.new_part, candidate.old_part, context)] = (
                candidate,
                item_names,
            )

    cases.sort(key=lambda case: (case["new_part"], case["old_part"], case["context"]))

    support: list[dict[str, object]] = []
    if cases:
        traced = cases[0]
        key = (
            str(traced["new_part"]).removeprefix("part:"),
            str(traced["old_part"]).removeprefix("part:"),
            str(traced["context"]).removeprefix("context:"),
        )
        candidate, item_names = case_sources[key]
        item_locators = [
            {
                "source": "sources/bom.csv",
                "locator": f"record bom_item={item_name}",
            }
            for item_name in item_names
        ]
        support = [
            {
                "claim": (
                    f"{traced['new_part']} replaces {traced['old_part']} in "
                    f"{traced['context']}"
                ),
                "evidence": [
                    {
                        "source": "sources/engineering_notes.md",
                        "locator": f"section {candidate.section}",
                    }
                ],
            },
            {
                "claim": (
                    f"{traced['context']} contains "
                    f"{', '.join(str(item) for item in traced['bom_items'])}"
                ),
                "evidence": item_locators,
            },
            {
                "claim": (
                    f"{traced['new_part']} has mechanical state "
                    f"{traced['mechanical_state']} for the traced BOM items"
                ),
                "evidence": [
                    {
                        "source": "sources/manufacturer.csv",
                        "locator": f"record part_number={candidate.new_part}",
                    },
                    *item_locators,
                ],
            },
            {
                "claim": (
                    f"{traced['new_part']} has semantic state "
                    f"{traced['semantic_state']} in {traced['context']}"
                ),
                "evidence": [
                    {
                        "source": "sources/engineering_notes.md",
                        "locator": f"section {candidate.section}",
                    }
                ],
            },
        ]

    result = {"task": "replacement_state", "cases": cases, "support": support}
    with (ROOT / "output.json").open("w", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")


if __name__ == "__main__":
    main()
