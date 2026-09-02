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


def read_csv(name: str) -> list[dict[str, str]]:
    with (SOURCES / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def engineering_candidates(notes: str) -> list[dict[str, str]]:
    """Extract each Candidate relation and the prose belonging to its section."""
    sections = re.split(r"(?m)^##\s+", notes)[1:]
    candidates: list[dict[str, str]] = []
    pattern = re.compile(
        r"Candidate:\s*`([^`]+)`\s+replaces\s+`([^`]+)`\s*\.", re.IGNORECASE
    )
    for section in sections:
        match = pattern.search(section)
        if match:
            candidates.append(
                {
                    "new_part": match.group(1).strip(),
                    "old_part": match.group(2).strip(),
                    "prose": section[match.end() :].strip(),
                }
            )
    return candidates


def mentions_scope(prose: str, bom_item: str, context: str) -> bool:
    return (
        re.search(rf"\b{re.escape(bom_item)}\b", prose, re.IGNORECASE) is not None
        or re.search(rf"\b{re.escape(context)}\b", prose, re.IGNORECASE) is not None
    )


def semantic_judgment(
    prose: str, bom_item: str, context: str
) -> tuple[str, str | None]:
    """Return the semantic state and whether semantic acceptance fails/is uncertain."""
    if not mentions_scope(prose, bom_item, context):
        return "not_established", "uncertain"

    rejection = re.search(
        r"\b(?:not acceptable|unacceptable|rejected|must not be used|"
        r"does not qualify)\b",
        prose,
        re.IGNORECASE,
    )
    if rejection:
        return "not_established", "failed"

    positive = re.search(
        r"\b(?:acceptable substitute|accepted|acceptance judgment|"
        r"preferred fallback|approved)\b",
        prose,
        re.IGNORECASE,
    )
    if not positive:
        return "not_established", "uncertain"

    # A positive judgment that depends on an unmet/unknown qualifier is not a
    # categorical acceptance for this source set.
    conditional = re.search(
        r"\b(?:if|provided that|subject to|pending|unless)\b",
        prose,
        re.IGNORECASE,
    )
    if conditional:
        return "unresolved", "uncertain"
    return "accepted", None


def as_int(row: dict[str, str], field: str) -> int:
    return int(row[field])


def main() -> None:
    bom = read_csv("bom.csv")
    manufacturer_rows = read_csv("manufacturer.csv")
    parts = {row["part_number"]: row for row in manufacturer_rows}

    with (SOURCES / "suppliers.json").open(encoding="utf-8") as handle:
        supplier_data: dict[str, Any] = json.load(handle)
    represented_parts = {
        item["manufacturer_part_number"] for item in supplier_data["listings"]
    }

    notes = (SOURCES / "engineering_notes.md").read_text(encoding="utf-8")
    candidates = engineering_candidates(notes)
    cases: list[dict[str, Any]] = []

    for candidate in candidates:
        new_number = candidate["new_part"]
        old_number = candidate["old_part"]
        if new_number not in parts or old_number not in parts:
            continue
        # The task concerns represented candidates; supplier listings establish
        # that both sides are represented in the available parts data.
        if new_number not in represented_parts or old_number not in represented_parts:
            continue

        new = parts[new_number]
        old = parts[old_number]
        if new["part_type"] != old["part_type"]:
            continue

        for requirement in bom:
            if requirement["part_type"] != old["part_type"]:
                continue

            voltage_compatible = as_int(new, "rated_voltage_v") >= as_int(
                requirement, "required_voltage_v"
            )
            temperature_compatible = (
                as_int(new, "min_temp_c") <= as_int(requirement, "min_temp_c")
                and as_int(new, "max_temp_c") >= as_int(requirement, "max_temp_c")
            )
            lifecycle_active = new["lifecycle"].strip().lower() == "active"
            semantic_state, semantic_effect = semantic_judgment(
                candidate["prose"],
                requirement["bom_item"],
                requirement["deployment_environment"],
            )

            prevents: list[str] = []
            uncertain: list[str] = []
            if not voltage_compatible:
                prevents.append("voltage_compatible")
            if not temperature_compatible:
                prevents.append("temperature_compatible")
            if not lifecycle_active:
                prevents.append("lifecycle_active")
            if semantic_effect == "failed":
                prevents.append("semantic_acceptance")
            elif semantic_effect == "uncertain":
                uncertain.append("semantic_acceptance")

            cases.append(
                {
                    "new_part": f"part:{new_number}",
                    "old_part": f"part:{old_number}",
                    "bom_item": f"bom:{requirement['bom_item']}",
                    "context": f"context:{requirement['deployment_environment']}",
                    "voltage_compatible": voltage_compatible,
                    "temperature_compatible": temperature_compatible,
                    "new_part_lifecycle_active": lifecycle_active,
                    "old_part_lifecycle": old["lifecycle"],
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
    result = {"task": "qualification_bottlenecks", "cases": cases}
    (ROOT / "output.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
