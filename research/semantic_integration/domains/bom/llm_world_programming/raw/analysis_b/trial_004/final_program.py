#!/usr/bin/env python3
"""Compute qualification bottlenecks from the authoritative source files."""

from __future__ import annotations

import csv
import json
import re
from decimal import Decimal
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / "sources"

PAIR_PATTERN = re.compile(
    r"Candidate:\s*`(?P<new>[^`]+)`\s+replaces\s+`(?P<old>[^`]+)`\.",
    re.IGNORECASE,
)
SCOPE_PATTERN = re.compile(
    r"For\s+the\s+`(?P<context>[^`]+)`\s+context\s+used\s+by\s+"
    r"(?P<bom>BOM-[A-Za-z0-9_-]+)",
    re.IGNORECASE,
)
POSITIVE_JUDGMENT_PATTERN = re.compile(
    r"\b(?:preferred\s+fallback|engineering\s+acceptance\s+judgment|"
    r"acceptable\s+substitute)\b",
    re.IGNORECASE,
)


def read_csv(name: str) -> list[dict[str, str]]:
    with (SOURCES / name).open(newline="", encoding="utf-8") as source:
        return list(csv.DictReader(source))


def read_replacement_notes() -> list[dict[str, Any]]:
    """Extract represented replacement pairs and context-scoped judgments."""
    text = (SOURCES / "engineering_notes.md").read_text(encoding="utf-8")
    replacements: list[dict[str, Any]] = []

    for section in re.split(r"(?m)^##\s+", text)[1:]:
        pair = PAIR_PATTERN.search(section)
        if pair is None:
            continue

        scopes = {
            (match.group("bom"), match.group("context"))
            for match in SCOPE_PATTERN.finditer(section)
        }
        replacements.append(
            {
                "new": pair.group("new"),
                "old": pair.group("old"),
                "accepted_scopes": (
                    scopes if POSITIVE_JUDGMENT_PATTERN.search(section) else set()
                ),
            }
        )

    return replacements


def temperature_compatible(
    part: dict[str, str], bom: dict[str, str]
) -> bool:
    return (
        Decimal(part["min_temp_c"]) <= Decimal(bom["min_temp_c"])
        and Decimal(part["max_temp_c"]) >= Decimal(bom["max_temp_c"])
    )


def build_cases() -> list[dict[str, Any]]:
    parts = {
        row["part_number"]: row
        for row in read_csv("manufacturer.csv")
    }
    boms = read_csv("bom.csv")
    cases: list[dict[str, Any]] = []

    for replacement in read_replacement_notes():
        new_number = replacement["new"]
        old_number = replacement["old"]
        new_part = parts[new_number]
        old_part = parts[old_number]

        if new_part["part_type"] != old_part["part_type"]:
            continue

        for bom in boms:
            if bom["part_type"] != new_part["part_type"]:
                continue

            scope = (bom["bom_item"], bom["deployment_environment"])
            semantic_state = (
                "accepted"
                if scope in replacement["accepted_scopes"]
                else "unresolved"
            )
            voltage_ok = (
                Decimal(new_part["rated_voltage_v"])
                == Decimal(bom["required_voltage_v"])
            )
            temperature_ok = temperature_compatible(new_part, bom)
            lifecycle_ok = new_part["lifecycle"].strip().lower() == "active"

            prevents_viability: list[str] = []
            if not voltage_ok:
                prevents_viability.append("voltage_compatible")
            if not temperature_ok:
                prevents_viability.append("temperature_compatible")
            if not lifecycle_ok:
                prevents_viability.append("lifecycle_active")

            leaves_uncertain = (
                [] if semantic_state == "accepted" else ["semantic_acceptance"]
            )
            cases.append(
                {
                    "new_part": f"part:{new_number}",
                    "old_part": f"part:{old_number}",
                    "bom_item": f"bom:{bom['bom_item']}",
                    "context": f"context:{bom['deployment_environment']}",
                    "voltage_compatible": voltage_ok,
                    "temperature_compatible": temperature_ok,
                    "new_part_lifecycle_active": lifecycle_ok,
                    "old_part_lifecycle": old_part["lifecycle"],
                    "semantic_state": semantic_state,
                    "prevents_viability": prevents_viability,
                    "leaves_viability_uncertain": leaves_uncertain,
                }
            )

    return sorted(
        cases,
        key=lambda case: (
            case["new_part"],
            case["old_part"],
            case["bom_item"],
            case["context"],
        ),
    )


def main() -> None:
    output = {
        "task": "qualification_bottlenecks",
        "cases": build_cases(),
    }
    (ROOT / "output.json").write_text(
        json.dumps(output, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
