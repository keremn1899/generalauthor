#!/usr/bin/env python3
"""Determine replacement candidate state from authoritative workspace sources."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / "sources"


def load_bom() -> list[dict]:
    with (SOURCES / "bom.csv").open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_manufacturer_parts() -> dict[str, dict]:
    with (SOURCES / "manufacturer.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    parts: dict[str, dict] = {}
    for row in rows:
        parts[row["part_number"]] = {
            "part_number": row["part_number"],
            "part_type": row["part_type"],
            "rated_voltage_v": int(row["rated_voltage_v"]),
            "min_temp_c": int(row["min_temp_c"]),
            "max_temp_c": int(row["max_temp_c"]),
            "lifecycle": row["lifecycle"],
            "description": row["description"],
        }
    return parts


def load_engineering_notes() -> str:
    return (SOURCES / "engineering_notes.md").read_text(encoding="utf-8")


def parse_replacement_candidates(notes: str) -> list[dict]:
    candidates: list[dict] = []
    for match in re.finditer(
        r"## (ER-\d+)\s*\n(.*?)(?=\n## ER-|\Z)",
        notes,
        flags=re.DOTALL,
    ):
        section_id = match.group(1)
        body = match.group(2)

        candidate_match = re.search(
            r"Candidate:\s*`([^`]+)`\s+replaces\s+`([^`]+)`",
            body,
        )
        if not candidate_match:
            continue

        context_match = re.search(r"For the `([^`]+)` context", body)
        if not context_match:
            continue

        candidates.append(
            {
                "section_id": section_id,
                "new_part": candidate_match.group(1),
                "old_part": candidate_match.group(2),
                "context": context_match.group(1),
                "body": body.strip(),
            }
        )
    return candidates


def bom_items_for_context(bom_rows: list[dict], context: str) -> list[str]:
    return sorted(
        row["bom_item"]
        for row in bom_rows
        if row["deployment_environment"] == context
    )


def bom_requirements(bom_rows: list[dict], bom_item: str) -> dict:
    for row in bom_rows:
        if row["bom_item"] == bom_item:
            return {
                "part_type": row["part_type"],
                "required_voltage_v": int(row["required_voltage_v"]),
                "min_temp_c": int(row["min_temp_c"]),
                "max_temp_c": int(row["max_temp_c"]),
                "deployment_environment": row["deployment_environment"],
            }
    raise KeyError(f"Unknown BOM item: {bom_item}")


def mechanical_state(part: dict, bom_rows: list[dict], bom_items: list[str]) -> str:
    for bom_item in bom_items:
        req = bom_requirements(bom_rows, bom_item)
        if part["part_type"] != req["part_type"]:
            return "unsuitable"
        if part["rated_voltage_v"] < req["required_voltage_v"]:
            return "unsuitable"
        if part["min_temp_c"] > req["min_temp_c"]:
            return "unsuitable"
        if part["max_temp_c"] < req["max_temp_c"]:
            return "unsuitable"
    return "suitable"


def normalized_text(body: str) -> str:
    return re.sub(r"\s+", " ", body).strip().lower()


def semantic_state(body: str) -> str:
    lowered = normalized_text(body)
    if "qualification was not repeated" in lowered:
        return "unresolved"
    if "acceptable substitute" in lowered or "preferred fallback" in lowered:
        return "accepted"
    return "not_established"


def epistemic_class(body: str) -> str:
    lowered = normalized_text(body)
    if "team treats" in lowered and "acceptable substitute" in lowered:
        return "ASSERTED_TRUE"
    if "qualification was not repeated" in lowered:
        return "UNRESOLVED"
    if "engineering acceptance judgment" in lowered:
        return "UNRESOLVED"
    if "no numeric crosswalk" in lowered or "not appear in the available source" in lowered:
        return "NOT_KNOWN"
    return "NOT_KNOWN"


def build_support(case: dict, bom_rows: list[dict], parts: dict[str, dict]) -> list[dict]:
    bom_item = case["bom_items"][0].removeprefix("bom:")
    req = bom_requirements(bom_rows, bom_item)
    new_part_number = case["new_part"].removeprefix("part:")
    part = parts[new_part_number]

    return [
        {
            "claim": (
                f"{case['new_part']} is mechanically {case['mechanical_state']} "
                f"for {case['bom_items'][0]} in {case['context']}"
            ),
            "evidence": [
                {
                    "source": "sources/manufacturer.csv",
                    "locator": f"part_number:{new_part_number}",
                },
                {
                    "source": "sources/bom.csv",
                    "locator": f"bom_item:{bom_item}",
                },
                {
                    "source": "sources/engineering_notes.md",
                    "locator": f"section:{case['section_id']}",
                },
            ],
        },
        {
            "claim": (
                f"semantic acceptance for {case['new_part']} replacing "
                f"{case['old_part']} in {case['context']} is {case['semantic_state']}"
            ),
            "evidence": [
                {
                    "source": "sources/engineering_notes.md",
                    "locator": f"section:{case['section_id']}",
                },
            ],
        },
        {
            "claim": (
                f"rated_voltage_v for {case['new_part']} is {part['rated_voltage_v']} "
                f"and required_voltage_v for {case['bom_items'][0]} is "
                f"{req['required_voltage_v']}"
            ),
            "evidence": [
                {
                    "source": "sources/manufacturer.csv",
                    "locator": f"part_number:{new_part_number},field:rated_voltage_v",
                },
                {
                    "source": "sources/bom.csv",
                    "locator": f"bom_item:{bom_item},field:required_voltage_v",
                },
            ],
        },
    ]


def main() -> None:
    bom_rows = load_bom()
    parts = load_manufacturer_parts()
    notes = load_engineering_notes()
    candidates = parse_replacement_candidates(notes)

    cases: list[dict] = []
    for candidate in candidates:
        context = candidate["context"]
        bom_items = bom_items_for_context(bom_rows, context)
        new_part = parts[candidate["new_part"]]

        case = {
            "section_id": candidate["section_id"],
            "new_part": f"part:{candidate['new_part']}",
            "old_part": f"part:{candidate['old_part']}",
            "context": f"context:{context}",
            "bom_items": [f"bom:{item}" for item in bom_items],
            "mechanical_state": mechanical_state(new_part, bom_rows, bom_items),
            "semantic_state": semantic_state(candidate["body"]),
            "epistemic": epistemic_class(candidate["body"]),
        }
        cases.append(case)

    cases.sort(key=lambda item: (item["new_part"], item["old_part"], item["context"]))

    support = build_support(cases[0], bom_rows, parts) if cases else []

    output = {
        "task": "replacement_state",
        "cases": [
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
        ],
        "support": support,
    }

    (ROOT / "output.json").write_text(
        json.dumps(output, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
