#!/usr/bin/env python3
"""Determine replacement state from authoritative workspace sources."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / "sources"


def load_bom() -> list[dict[str, str | int]]:
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
            parts[row["part_number"]] = {
                "part_number": row["part_number"],
                "part_type": row["part_type"],
                "rated_voltage_v": int(row["rated_voltage_v"]),
                "min_temp_c": int(row["min_temp_c"]),
                "max_temp_c": int(row["max_temp_c"]),
                "lifecycle": row["lifecycle"],
            }
    return parts


def parse_engineering_notes() -> list[dict[str, str]]:
    text = (SOURCES / "engineering_notes.md").read_text(encoding="utf-8")
    sections = re.split(r"(?=^## ER-\d+\s*$)", text, flags=re.MULTILINE)
    cases: list[dict[str, str]] = []

    candidate_re = re.compile(
        r"Candidate:\s*`(?P<new_part>[A-Z0-9]+)`\s+replaces\s+`(?P<old_part>[A-Z0-9]+)`\.",
        re.IGNORECASE,
    )
    context_re = re.compile(r"For the `(?P<context>[^`]+)` context")

    for section in sections:
        candidate_match = candidate_re.search(section)
        context_match = context_re.search(section)
        if not candidate_match or not context_match:
            continue
        er_id_match = re.search(r"^## ER-(\d+)", section, re.MULTILINE)
        cases.append(
            {
                "new_part": candidate_match.group("new_part"),
                "old_part": candidate_match.group("old_part"),
                "context": context_match.group("context"),
                "note_text": section.strip(),
                "er_id": er_id_match.group(1) if er_id_match else "",
            }
        )
    return cases


def bom_items_for_context(bom_rows: list[dict[str, str | int]], context: str) -> list[str]:
    items = [
        row["bom_item"]
        for row in bom_rows
        if row["deployment_environment"] == context
    ]
    return sorted(items)


def mechanically_suitable(
    part: dict[str, str | int], bom_item: dict[str, str | int]
) -> bool:
    if part["part_type"] != bom_item["part_type"]:
        return False
    if part["rated_voltage_v"] < bom_item["required_voltage_v"]:
        return False
    if part["min_temp_c"] > bom_item["min_temp_c"]:
        return False
    if part["max_temp_c"] < bom_item["max_temp_c"]:
        return False
    return True


def mechanical_state_for_case(
    new_part_number: str,
    bom_rows: list[dict[str, str | int]],
    context: str,
    parts: dict[str, dict[str, str | int]],
) -> str:
    new_part = parts[new_part_number]
    context_items = [
        row for row in bom_rows if row["deployment_environment"] == context
    ]
    if not context_items:
        return "unsuitable"
    for bom_item in context_items:
        if not mechanically_suitable(new_part, bom_item):
            return "unsuitable"
    return "suitable"


def normalize_note_text(note_text: str) -> str:
    return re.sub(r"\s+", " ", note_text.strip().lower())


def classify_semantic_and_epistemic(note_text: str) -> tuple[str, str]:
    normalized = normalize_note_text(note_text)

    acceptance_markers = (
        "acceptable substitute",
        "preferred fallback",
        "engineering acceptance judgment",
    )
    unresolved_markers = (
        "qualification was not repeated",
        "no numeric crosswalk appears in the available source set",
        "different supplier terminology",
    )

    if any(marker in normalized for marker in acceptance_markers):
        semantic_state = "accepted"
    elif any(
        phrase in normalized
        for phrase in ("not established", "no acceptance", "not accepted")
    ):
        semantic_state = "not_established"
    else:
        semantic_state = "unresolved"

    if any(marker in normalized for marker in unresolved_markers):
        epistemic = "UNRESOLVED"
    elif semantic_state == "accepted":
        epistemic = "ASSERTED_TRUE"
    elif semantic_state == "unresolved":
        epistemic = "UNRESOLVED"
    else:
        epistemic = "NOT_KNOWN"

    return semantic_state, epistemic


def build_support(case: dict) -> list[dict]:
    return [
        {
            "claim": (
                f"{case['new_part']} replaces {case['old_part']} in "
                f"{case['context']} with semantic_state={case['semantic_state']} "
                f"and mechanical_state={case['mechanical_state']}"
            ),
            "evidence": [
                {
                    "source": "sources/engineering_notes.md",
                    "locator": f"## ER-{case['er_id']}",
                },
                {
                    "source": "sources/bom.csv",
                    "locator": f"deployment_environment={case['context_name']}",
                },
                {
                    "source": "sources/manufacturer.csv",
                    "locator": f"part_number={case['new_part_number']}",
                },
            ],
        }
    ]


def main() -> None:
    bom_rows = load_bom()
    parts = load_parts()
    note_cases = parse_engineering_notes()

    cases: list[dict] = []
    for note_case in note_cases:
        context = note_case["context"]
        bom_items = bom_items_for_context(bom_rows, context)
        mech = mechanical_state_for_case(
            note_case["new_part"], bom_rows, context, parts
        )
        semantic_state, epistemic = classify_semantic_and_epistemic(note_case["note_text"])

        case = {
            "new_part": f"part:{note_case['new_part']}",
            "old_part": f"part:{note_case['old_part']}",
            "context": f"context:{context}",
            "bom_items": [f"bom:{item}" for item in bom_items],
            "mechanical_state": mech,
            "semantic_state": semantic_state,
            "epistemic": epistemic,
            "new_part_number": note_case["new_part"],
            "context_name": context,
            "er_id": note_case["er_id"],
        }
        cases.append(case)

    cases.sort(key=lambda item: (item["new_part"], item["old_part"], item["context"]))

    public_cases = [
        {
            "new_part": case["new_part"],
            "old_part": case["old_part"],
            "context": case["context"],
            "bom_items": case["bom_items"],
            "mechanical_state": case["mechanical_state"],
            "semantic_state": case["semantic_state"],
            "epistemic": case["epistemic"],
        }
        for case in cases
    ]

    support = build_support(cases[0]) if cases else []

    result = {
        "task": "replacement_state",
        "cases": public_cases,
        "support": support,
    }

    output_path = ROOT / "output.json"
    output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
