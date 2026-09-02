#!/usr/bin/env python3
"""Compute qualification bottlenecks from the authoritative workspace sources."""

from __future__ import annotations

import csv
import json
import re
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / "sources"

CANDIDATE_RE = re.compile(
    r"Candidate:\s*`(?P<new>[^`]+)`\s+replaces\s+`(?P<old>[^`]+)`\.",
    re.IGNORECASE,
)
CONTEXT_RE = re.compile(
    r"For\s+the\s+`(?P<context>[^`]+)`\s+context\s+used\s+by\s+"
    r"(?P<bom>BOM-[A-Za-z0-9_-]+)",
    re.IGNORECASE,
)
ACCEPTANCE_RE = re.compile(
    r"\b(?:acceptable substitute|acceptance judgment|preferred fallback)\b",
    re.IGNORECASE,
)


def read_csv(name: str) -> list[dict[str, str]]:
    with (SOURCES / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def candidate_notes() -> list[dict[str, object]]:
    """Extract replacement pairs and their context-scoped engineering judgments."""
    text = (SOURCES / "engineering_notes.md").read_text(encoding="utf-8")
    records: list[dict[str, object]] = []

    for section in re.split(r"(?m)^##\s+", text)[1:]:
        candidate_match = CANDIDATE_RE.search(section)
        if candidate_match is None:
            continue

        judgments = []
        for context_match in CONTEXT_RE.finditer(section):
            judgments.append(
                {
                    "bom": context_match.group("bom"),
                    "context": context_match.group("context"),
                    # The notes explicitly call both conditional/prose conclusions
                    # engineering acceptance; ratings alone do not decide semantics.
                    "accepted": ACCEPTANCE_RE.search(section) is not None,
                }
            )

        records.append(
            {
                "new": candidate_match.group("new"),
                "old": candidate_match.group("old"),
                "judgments": judgments,
            }
        )

    return records


def covers_temperature(part: dict[str, str], bom: dict[str, str]) -> bool:
    return (
        Decimal(part["min_temp_c"]) <= Decimal(bom["min_temp_c"])
        and Decimal(part["max_temp_c"]) >= Decimal(bom["max_temp_c"])
    )


def build_cases() -> list[dict[str, object]]:
    manufacturer = {
        row["part_number"]: row for row in read_csv("manufacturer.csv")
    }
    boms = read_csv("bom.csv")

    cases: list[dict[str, object]] = []
    for candidate in candidate_notes():
        new_number = str(candidate["new"])
        old_number = str(candidate["old"])

        new_part = manufacturer[new_number]
        old_part = manufacturer[old_number]
        if new_part["part_type"] != old_part["part_type"]:
            continue

        judgment_by_scope = {
            (str(item["bom"]), str(item["context"])): bool(item["accepted"])
            for item in candidate["judgments"]  # type: ignore[union-attr]
        }

        for bom in boms:
            if bom["part_type"] != new_part["part_type"]:
                continue

            scope = (bom["bom_item"], bom["deployment_environment"])
            if scope not in judgment_by_scope:
                # The replacement relationship is represented, but no judgment
                # resolves semantic acceptance for this particular context.
                semantic_state = "unresolved"
            elif judgment_by_scope[scope]:
                semantic_state = "accepted"
            else:
                semantic_state = "unresolved"

            voltage_compatible = (
                Decimal(new_part["rated_voltage_v"])
                == Decimal(bom["required_voltage_v"])
            )
            temperature_compatible = covers_temperature(new_part, bom)
            lifecycle_active = new_part["lifecycle"].strip().lower() == "active"

            prevents_viability = []
            if not voltage_compatible:
                prevents_viability.append("voltage_compatible")
            if not temperature_compatible:
                prevents_viability.append("temperature_compatible")
            if not lifecycle_active:
                prevents_viability.append("lifecycle_active")

            leaves_viability_uncertain = []
            if semantic_state != "accepted":
                leaves_viability_uncertain.append("semantic_acceptance")

            cases.append(
                {
                    "new_part": f"part:{new_number}",
                    "old_part": f"part:{old_number}",
                    "bom_item": f"bom:{bom['bom_item']}",
                    "context": f"context:{bom['deployment_environment']}",
                    "voltage_compatible": voltage_compatible,
                    "temperature_compatible": temperature_compatible,
                    "new_part_lifecycle_active": lifecycle_active,
                    "old_part_lifecycle": old_part["lifecycle"],
                    "semantic_state": semantic_state,
                    "prevents_viability": prevents_viability,
                    "leaves_viability_uncertain": leaves_viability_uncertain,
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
    result = {
        "task": "qualification_bottlenecks",
        "cases": build_cases(),
    }
    (ROOT / "output.json").write_text(
        json.dumps(result, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
