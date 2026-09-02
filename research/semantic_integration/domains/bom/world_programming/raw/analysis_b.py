"""RAW B: qualification bottlenecks for candidate replacements."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from research.semantic_integration.domains.bom.world_programming.raw.io import (
    bom_id,
    context_id,
    lifecycle_active,
    part_id,
    read_bom,
    read_engineering_notes,
    read_manufacturer,
    temperature_compatible,
    voltage_compatible,
)
from research.taskview_bom.experiment import FIXTURES


def run(source_dir: Path = FIXTURES) -> dict[str, Any]:
    parts = {row["part_number"]: row for row in read_manufacturer(source_dir / "manufacturer.csv")}
    bom_rows = read_bom(source_dir / "bom.csv")
    notes = read_engineering_notes(source_dir / "engineering_notes.md")
    environments = {row["deployment_environment"] for row in bom_rows}
    accepted: set[tuple[str, str, str]] = set()
    for section in notes:
        for quoted in section["quoted"]:
            if quoted in environments:
                accepted.add(
                    (
                        part_id(section["new_part"]),
                        part_id(section["old_part"]),
                        context_id(quoted),
                    )
                )

    cases: list[dict[str, Any]] = []
    for section in notes:
        new_part = parts[section["new_part"]]
        old_part = parts[section["old_part"]]
        if new_part["part_type"] != old_part["part_type"]:
            continue
        matching = [row for row in bom_rows if row["part_type"] == new_part["part_type"]]
        for bom in matching:
            key = (
                part_id(section["new_part"]),
                part_id(section["old_part"]),
                context_id(bom["deployment_environment"]),
            )
            voltage = voltage_compatible(new_part, bom)
            temperature = temperature_compatible(new_part, bom)
            active = lifecycle_active(new_part)
            if key in accepted:
                semantic_state = "accepted"
            else:
                semantic_state = "unresolved"
            prevents: list[str] = []
            uncertain: list[str] = []
            if not voltage:
                prevents.append("voltage_compatible")
            if not temperature:
                prevents.append("temperature_compatible")
            if not active:
                prevents.append("lifecycle_active")
            if semantic_state == "unresolved":
                uncertain.append("semantic_acceptance")
            cases.append(
                {
                    "new_part": key[0],
                    "old_part": key[1],
                    "bom_item": bom_id(bom["bom_item"]),
                    "context": key[2],
                    "voltage_compatible": voltage,
                    "temperature_compatible": temperature,
                    "new_part_lifecycle_active": active,
                    "old_part_lifecycle": old_part["lifecycle"],
                    "semantic_state": semantic_state,
                    "prevents_viability": prevents,
                    "leaves_viability_uncertain": uncertain,
                }
            )
    cases.sort(
        key=lambda row: (
            row["new_part"],
            row["old_part"],
            row["bom_item"],
            row["context"],
        )
    )
    return {"task": "qualification_bottlenecks", "cases": cases}
