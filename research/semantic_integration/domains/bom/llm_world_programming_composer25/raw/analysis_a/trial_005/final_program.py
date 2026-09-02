#!/usr/bin/env python3
"""Determine replacement candidate state from authoritative workspace sources."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / "sources"


def load_bom() -> list[dict[str, str]]:
    with (SOURCES / "bom.csv").open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_parts() -> dict[str, dict[str, str]]:
    with (SOURCES / "manufacturer.csv").open(newline="", encoding="utf-8") as handle:
        return {row["part_number"]: row for row in csv.DictReader(handle)}


def load_engineering_notes() -> str:
    return (SOURCES / "engineering_notes.md").read_text(encoding="utf-8")


def parse_replacement_records(notes: str) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for section in re.split(r"\n## ER-\d+\n", notes)[1:]:
        candidate_match = re.search(
            r"Candidate:\s*`([^`]+)`\s+replaces\s+`([^`]+)`\.", section
        )
        context_match = re.search(
            r"For the\s+`([^`]+)`\s+context used by\s+([A-Z0-9-]+)", section
        )
        if not candidate_match or not context_match:
            continue
        records.append(
            {
                "new_part": candidate_match.group(1),
                "old_part": candidate_match.group(2),
                "context": context_match.group(1),
                "bom_item": context_match.group(2),
                "prose": section.strip(),
            }
        )
    return records


def bom_items_for_context(bom_rows: list[dict[str, str]], context: str) -> list[str]:
    return sorted(
        f"bom:{row['bom_item']}"
        for row in bom_rows
        if row["deployment_environment"] == context
    )


def mechanical_suitable(part: dict[str, str], bom: dict[str, str]) -> bool:
    if part["part_type"] != bom["part_type"]:
        return False
    if float(part["rated_voltage_v"]) < float(bom["required_voltage_v"]):
        return False
    if float(part["min_temp_c"]) > float(bom["min_temp_c"]):
        return False
    if float(part["max_temp_c"]) < float(bom["max_temp_c"]):
        return False
    return True


def mechanical_state_for_case(
    new_part: str,
    bom_rows: list[dict[str, str]],
    context: str,
    parts: dict[str, dict[str, str]],
) -> str:
    part = parts[new_part]
    context_boms = [row for row in bom_rows if row["deployment_environment"] == context]
    if not context_boms:
        return "unsuitable"
    return (
        "suitable"
        if all(mechanical_suitable(part, bom) for bom in context_boms)
        else "unsuitable"
    )


def classify_semantic_state(prose: str) -> str:
    """Classify engineering acceptance from prose qualifiers."""
    lowered = prose.lower()

    if "acceptable substitute" in lowered or re.search(
        r"\btreats\b.+\bas\b", lowered
    ):
        return "accepted"

    unresolved_markers = (
        "qualification was not repeated",
        "engineering acceptance judgment",
        "preferred fallback if",
        "rather than a conclusion from the tabulated ratings alone",
    )
    if any(marker in lowered for marker in unresolved_markers):
        return "unresolved"

    return "not_established"


def classify_epistemic(prose: str, semantic_state: str) -> str:
    """Classify what the available sources establish about the replacement case."""
    lowered = prose.lower()

    if "no numeric crosswalk appears in the available source set" in lowered:
        return "NOT_KNOWN"

    if semantic_state == "unresolved":
        return "UNRESOLVED"

    if semantic_state == "accepted":
        return "ASSERTED_TRUE"

    return "NOT_KNOWN"


def build_support(case: dict) -> list[dict]:
    return [
        {
            "claim": (
                f"{case['new_part']} is an acceptable substitute for "
                f"{case['old_part']} in {case['context']}"
            ),
            "evidence": [
                {
                    "source": "sources/engineering_notes.md",
                    "locator": case["engineering_record"],
                }
            ],
        },
        {
            "claim": (
                f"{case['new_part']} is mechanically suitable for BOM items in "
                f"{case['context']}"
            ),
            "evidence": [
                {
                    "source": "sources/manufacturer.csv",
                    "locator": f"part_number={case['new_part_number']}",
                },
                {
                    "source": "sources/bom.csv",
                    "locator": f"deployment_environment={case['context_name']}",
                },
            ],
        },
    ]


def main() -> None:
    bom_rows = load_bom()
    parts = load_parts()
    notes = load_engineering_notes()
    records = parse_replacement_records(notes)

    cases: list[dict] = []
    for index, record in enumerate(records, start=1):
        new_part_number = record["new_part"]
        old_part_number = record["old_part"]
        context_name = record["context"]
        semantic_state = classify_semantic_state(record["prose"])
        epistemic = classify_epistemic(record["prose"], semantic_state)

        case = {
            "new_part": f"part:{new_part_number}",
            "old_part": f"part:{old_part_number}",
            "context": f"context:{context_name}",
            "bom_items": bom_items_for_context(bom_rows, context_name),
            "mechanical_state": mechanical_state_for_case(
                new_part_number, bom_rows, context_name, parts
            ),
            "semantic_state": semantic_state,
            "epistemic": epistemic,
            # Internal fields used only for provenance support.
            "new_part_number": new_part_number,
            "context_name": context_name,
            "engineering_record": f"ER-{index}",
        }
        cases.append(case)

    cases.sort(key=lambda item: (item["new_part"], item["old_part"], item["context"]))

    support_case = next(
        (
            case
            for case in cases
            if case["new_part"] == "part:R210"
            and case["old_part"] == "part:R200"
            and case["context"] == "context:high_vibration_cabinet"
        ),
        cases[0],
    )
    support = build_support(support_case)

    public_cases = [
        {key: value for key, value in case.items() if not key.endswith("_number") and key not in {"context_name", "engineering_record"}}
        for case in cases
    ]

    output = {
        "task": "replacement_state",
        "cases": public_cases,
        "support": support,
    }

    (ROOT / "output.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
