#!/usr/bin/env python3
"""Compute replacement_state from authoritative workspace sources."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / "sources"

ACCEPTANCE_PATTERNS = (
    r"acceptable substitute",
    r"preferred fallback",
    r"acceptance judgment",
    r"treats .+ as",
)


def part_id(part_number: str) -> str:
    return f"part:{part_number}"


def bom_id(bom_item: str) -> str:
    return f"bom:{bom_item}"


def context_id(deployment_environment: str) -> str:
    return f"context:{deployment_environment}"


def load_bom_rows() -> list[dict[str, str | int]]:
    rows: list[dict[str, str | int]] = []
    with (SOURCES / "bom.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            rows.append(
                {
                    "bom_item": row["bom_item"],
                    "part_type": row["part_type"],
                    "required_voltage_v": int(row["required_voltage_v"]),
                    "min_temp_c": int(row["min_temp_c"]),
                    "max_temp_c": int(row["max_temp_c"]),
                    "deployment_environment": row["deployment_environment"],
                }
            )
    return rows


def load_parts() -> dict[str, dict[str, str | int]]:
    parts: dict[str, dict[str, str | int]] = {}
    with (SOURCES / "manufacturer.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            part_number = row["part_number"]
            parts[part_number] = {
                "part_number": part_number,
                "part_type": row["part_type"],
                "rated_voltage_v": int(row["rated_voltage_v"]),
                "min_temp_c": int(row["min_temp_c"]),
                "max_temp_c": int(row["max_temp_c"]),
                "lifecycle": row["lifecycle"],
            }
    return parts


def parse_engineering_notes(text: str) -> tuple[list[tuple[str, str]], dict[tuple[str, str, str], dict]]:
    """Return candidate pairs and per-context acceptance records keyed by (new, old, context)."""
    candidates: list[tuple[str, str]] = []
    seen_pairs: set[tuple[str, str]] = set()
    acceptance_by_case: dict[tuple[str, str, str], dict] = {}

    sections = re.split(r"(?=^## ER-\d+\s*$)", text, flags=re.MULTILINE)
    for section in sections:
        candidate_match = re.search(
            r"Candidate:\s*`([^`]+)`\s+replaces\s+`([^`]+)`",
            section,
            flags=re.IGNORECASE,
        )
        if not candidate_match:
            continue

        new_part, old_part = candidate_match.group(1), candidate_match.group(2)
        pair = (new_part, old_part)
        if pair not in seen_pairs:
            seen_pairs.add(pair)
            candidates.append(pair)

        context_match = re.search(r"`([a-z_]+)`\s+context", section, flags=re.IGNORECASE)
        if not context_match:
            continue

        context = context_match.group(1)
        accepted = any(
            re.search(pattern, section, flags=re.IGNORECASE) for pattern in ACCEPTANCE_PATTERNS
        )
        if not accepted:
            continue

        heading_match = re.match(r"^## (ER-\d+)\s*$", section.strip(), flags=re.MULTILINE)
        record_id = heading_match.group(1) if heading_match else "engineering_notes"
        start = text.find(section.strip())
        line_start = text.count("\n", 0, start) + 1 if start >= 0 else 1
        line_end = line_start + len(section.strip().splitlines()) - 1

        acceptance_by_case[(new_part, old_part, context)] = {
            "semantic_state": "accepted",
            "epistemic": "ASSERTED_TRUE",
            "evidence": [
                {
                    "source": "sources/engineering_notes.md",
                    "locator": f"lines {line_start}-{line_end} ({record_id})",
                }
            ],
        }

    return candidates, acceptance_by_case


def bom_items_for_context(
    bom_rows: list[dict[str, str | int]],
    context: str,
    part_type: str,
) -> list[str]:
    items = [
        bom_id(str(row["bom_item"]))
        for row in bom_rows
        if row["deployment_environment"] == context and row["part_type"] == part_type
    ]
    return sorted(items)


def contexts_for_old_part(
    bom_rows: list[dict[str, str | int]],
    old_part: dict[str, str | int],
) -> list[str]:
    contexts = sorted(
        {
            str(row["deployment_environment"])
            for row in bom_rows
            if row["part_type"] == old_part["part_type"]
        }
    )
    return contexts


def is_mechanically_suitable(
    new_part: dict[str, str | int],
    bom_rows: list[dict[str, str | int]],
    bom_items: list[str],
) -> bool:
    bom_by_id = {bom_id(str(row["bom_item"])): row for row in bom_rows}
    for item in bom_items:
        bom = bom_by_id[item]
        if new_part["part_type"] != bom["part_type"]:
            return False
        if new_part["rated_voltage_v"] < bom["required_voltage_v"]:
            return False
        if new_part["min_temp_c"] > bom["min_temp_c"]:
            return False
        if new_part["max_temp_c"] < bom["max_temp_c"]:
            return False
    return True


def build_support(
    case: dict,
    acceptance_by_case: dict[tuple[str, str, str], dict],
    bom_rows: list[dict[str, str | int]],
) -> list[dict]:
    new = case["new_part"].removeprefix("part:")
    old = case["old_part"].removeprefix("part:")
    context = case["context"].removeprefix("context:")

    support: list[dict] = []
    key = (new, old, context)
    if key in acceptance_by_case:
        record = acceptance_by_case[key]
        support.append(
            {
                "claim": (
                    f"{case['new_part']} is semantically accepted as a replacement for "
                    f"{case['old_part']} in {case['context']}"
                ),
                "evidence": list(record["evidence"]),
            }
        )

    for bom_item in case["bom_items"]:
        bom_name = bom_item.removeprefix("bom:")
        row_number = next(
            index + 2
            for index, row in enumerate(bom_rows)
            if row["bom_item"] == bom_name
        )
        support.append(
            {
                "claim": f"{bom_item} is in {case['context']}",
                "evidence": [
                    {
                        "source": "sources/bom.csv",
                        "locator": f"row {row_number} (bom_item={bom_name})",
                    }
                ],
            }
        )

    new_part_number = case["new_part"].removeprefix("part:")
    with (SOURCES / "manufacturer.csv").open(newline="", encoding="utf-8") as handle:
        part_rows = list(csv.DictReader(handle))
    part_row_number = next(
        index + 2
        for index, row in enumerate(part_rows)
        if row["part_number"] == new_part_number
    )
    support.append(
        {
            "claim": (
                f"{case['new_part']} is mechanically {case['mechanical_state']} for "
                f"{', '.join(case['bom_items'])}"
            ),
            "evidence": [
                {
                    "source": "sources/manufacturer.csv",
                    "locator": f"row {part_row_number} (part_number={new_part_number})",
                },
                {
                    "source": "sources/bom.csv",
                    "locator": f"rows for {', '.join(case['bom_items'])}",
                },
            ],
        }
    )

    return support


def main() -> None:
    bom_rows = load_bom_rows()
    parts = load_parts()
    notes_text = (SOURCES / "engineering_notes.md").read_text(encoding="utf-8")
    candidates, acceptance_by_case = parse_engineering_notes(notes_text)

    cases: list[dict] = []
    for new_part_number, old_part_number in candidates:
        old_part = parts[old_part_number]
        new_part = parts[new_part_number]

        for context in contexts_for_old_part(bom_rows, old_part):
            bom_items = bom_items_for_context(bom_rows, context, str(old_part["part_type"]))
            if not bom_items:
                continue

            mechanical_state = (
                "suitable"
                if is_mechanically_suitable(new_part, bom_rows, bom_items)
                else "unsuitable"
            )

            acceptance = acceptance_by_case.get((new_part_number, old_part_number, context))
            if acceptance:
                semantic_state = acceptance["semantic_state"]
                epistemic = acceptance["epistemic"]
            else:
                semantic_state = "unresolved"
                epistemic = "UNRESOLVED"

            cases.append(
                {
                    "new_part": part_id(new_part_number),
                    "old_part": part_id(old_part_number),
                    "context": context_id(context),
                    "bom_items": bom_items,
                    "mechanical_state": mechanical_state,
                    "semantic_state": semantic_state,
                    "epistemic": epistemic,
                }
            )

    cases.sort(key=lambda case: (case["new_part"], case["old_part"], case["context"]))

    traced_case = next(
        (
            case
            for case in cases
            if case["new_part"] == part_id("X110")
            and case["old_part"] == part_id("X160")
            and case["context"] == context_id("outdoor_enclosure")
        ),
        cases[0],
    )

    result = {
        "task": "replacement_state",
        "cases": cases,
        "support": build_support(traced_case, acceptance_by_case, bom_rows),
    }

    (ROOT / "output.json").write_text(
        json.dumps(result, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
