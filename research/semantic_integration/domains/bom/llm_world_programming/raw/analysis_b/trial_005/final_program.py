#!/usr/bin/env python3
"""Compute qualification bottlenecks from the authoritative source files."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / "sources"

CANDIDATE_RE = re.compile(
    r"Candidate:\s*`(?P<new>[^`]+)`\s+replaces\s+`(?P<old>[^`]+)`\s*\.",
    re.IGNORECASE,
)
SECTION_RE = re.compile(
    r"^##\s+.+?\n(?P<body>.*?)(?=^##\s+|\Z)",
    re.MULTILINE | re.DOTALL,
)
POSITIVE_ACCEPTANCE_RE = re.compile(
    r"\b(?:preferred\s+fallback|acceptable\s+substitute|"
    r"accept(?:ed|able|ance)(?:\s+replacement|\s+judgment)?)\b",
    re.IGNORECASE,
)


def read_csv(name: str) -> list[dict[str, str]]:
    with (SOURCES / name).open(newline="", encoding="utf-8") as source:
        return list(csv.DictReader(source))


def number(value: str) -> float:
    return float(value)


def parse_candidates(notes: str) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for section_match in SECTION_RE.finditer(notes):
        body = section_match.group("body")
        candidate_match = CANDIDATE_RE.search(body)
        if candidate_match is None:
            continue
        candidates.append(
            {
                "new": candidate_match.group("new"),
                "old": candidate_match.group("old"),
                "body": body,
            }
        )
    return candidates


def has_semantic_acceptance(section: str, environment: str) -> bool:
    """Return whether this section records acceptance for this environment."""
    context_is_scoped = re.search(
        rf"`{re.escape(environment)}`(?:\s+context)?\b", section
    )
    return bool(context_is_scoped and POSITIVE_ACCEPTANCE_RE.search(section))


def qualification_cases() -> list[dict[str, Any]]:
    parts = {row["part_number"]: row for row in read_csv("manufacturer.csv")}
    bom_rows = read_csv("bom.csv")
    notes = (SOURCES / "engineering_notes.md").read_text(encoding="utf-8")

    cases: list[dict[str, Any]] = []
    for candidate in parse_candidates(notes):
        new_part = parts.get(candidate["new"])
        old_part = parts.get(candidate["old"])
        if new_part is None or old_part is None:
            continue
        if new_part["part_type"] != old_part["part_type"]:
            continue

        for bom in bom_rows:
            if bom["part_type"] != new_part["part_type"]:
                continue

            voltage_ok = (
                number(new_part["rated_voltage_v"])
                == number(bom["required_voltage_v"])
            )
            temperature_ok = (
                number(new_part["min_temp_c"]) <= number(bom["min_temp_c"])
                and number(new_part["max_temp_c"]) >= number(bom["max_temp_c"])
            )
            lifecycle_ok = new_part["lifecycle"].strip().lower() != "discontinued"
            semantic_state = (
                "accepted"
                if has_semantic_acceptance(
                    candidate["body"], bom["deployment_environment"]
                )
                else "unresolved"
            )

            prevents: list[str] = []
            if not voltage_ok:
                prevents.append("voltage_compatible")
            if not temperature_ok:
                prevents.append("temperature_compatible")
            if not lifecycle_ok:
                prevents.append("lifecycle_active")

            uncertain: list[str] = []
            if semantic_state != "accepted":
                uncertain.append("semantic_acceptance")

            cases.append(
                {
                    "new_part": f"part:{new_part['part_number']}",
                    "old_part": f"part:{old_part['part_number']}",
                    "bom_item": f"bom:{bom['bom_item']}",
                    "context": f"context:{bom['deployment_environment']}",
                    "voltage_compatible": voltage_ok,
                    "temperature_compatible": temperature_ok,
                    "new_part_lifecycle_active": lifecycle_ok,
                    "old_part_lifecycle": old_part["lifecycle"],
                    "semantic_state": semantic_state,
                    "prevents_viability": prevents,
                    "leaves_viability_uncertain": uncertain,
                }
            )

    cases.sort(
        key=lambda case: (
            case["new_part"],
            case["old_part"],
            case["bom_item"],
            case["context"],
        )
    )
    return cases


def main() -> None:
    result = {
        "task": "qualification_bottlenecks",
        "cases": qualification_cases(),
    }
    (ROOT / "output.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
