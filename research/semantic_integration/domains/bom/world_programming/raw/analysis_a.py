"""RAW A: replacement-case state from heterogeneous sources."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from research.semantic_integration.domains.bom.world_programming.raw.io import (
    bom_id,
    context_id,
    eligible,
    part_id,
    read_bom,
    read_engineering_notes,
    read_manufacturer,
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
        by_context: dict[str, list[str]] = {}
        for bom in matching:
            by_context.setdefault(bom["deployment_environment"], []).append(bom["bom_item"])
        for environment, bom_items in sorted(by_context.items()):
            key = (
                part_id(section["new_part"]),
                part_id(section["old_part"]),
                context_id(environment),
            )
            suitable = all(
                eligible(new_part, bom)
                for bom in matching
                if bom["deployment_environment"] == environment
            )
            if key in accepted:
                semantic_state = "accepted"
                epistemic = "ASSERTED_TRUE"
            else:
                semantic_state = "unresolved"
                epistemic = "UNRESOLVED"
            cases.append(
                {
                    "new_part": key[0],
                    "old_part": key[1],
                    "context": key[2],
                    "bom_items": [bom_id(item) for item in sorted(bom_items)],
                    "mechanical_state": "suitable" if suitable else "unsuitable",
                    "semantic_state": semantic_state,
                    "epistemic": epistemic,
                }
            )
    cases.sort(key=lambda row: (row["new_part"], row["old_part"], row["context"]))
    return {"task": "replacement_state", "cases": cases}
