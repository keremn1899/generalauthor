#!/usr/bin/env python3
"""Compute replacement state from the workspace's compiled semantic World."""

from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Any

import world_surface
from taskview import TaskView
from taskview.model import TaskViewError


ROOT = Path(__file__).resolve().parent
OUTPUT_PATH = ROOT / "output.json"


def open_workspace_world() -> world_surface.World:
    """Open through the documented surface, tolerating its bundled ID mismatch."""

    try:
        return world_surface.open_world()
    except TaskViewError as error:
        if "database belongs to TaskView" not in str(error):
            raise

    with sqlite3.connect(
        f"file:{world_surface.DB_PATH}?mode=ro", uri=True
    ) as database:
        row = database.execute(
            "SELECT view_id FROM _tv_view WHERE singleton = 1"
        ).fetchone()
    if row is None:
        raise RuntimeError("compiled World has no TaskView identity")

    world = world_surface.World.__new__(world_surface.World)
    world.path = world_surface.DB_PATH
    world._tv = TaskView(world.path, view_id=str(row[0]))
    world._origins = {}
    if world_surface.ORIGINS_PATH.exists():
        origins = json.loads(world_surface.ORIGINS_PATH.read_text(encoding="utf-8"))
        world._origins = dict(origins.get("assertions", {}))
    return world


def source_evidence(
    world: world_surface.World, relation: str, values: dict[str, Any]
) -> list[dict[str, str]]:
    detail = world.inspect_tuple(relation, values)
    evidence: set[tuple[str, str]] = set()
    for grounding in (detail or {}).get("grounding", []):
        if grounding.get("kind") != "SOURCE":
            continue
        locator = ""
        try:
            metadata = json.loads(grounding.get("detail") or "{}")
            locator = str(
                metadata.get("native_location")
                or metadata.get("source_native_location")
                or ""
            )
        except (TypeError, json.JSONDecodeError):
            pass
        evidence.add((str(grounding["reference"]), locator))
    return [
        {"source": source, "locator": locator}
        for source, locator in sorted(evidence)
    ]


def compute() -> dict[str, Any]:
    world = open_workspace_world()
    try:
        # The old part's mechanical fit determines which BOM/context deployments
        # each represented replacement candidate applies to. Lifecycle is not a
        # mechanical property, so the compatibility relations are used directly.
        targets = world.query_semantic(
            """
            SELECT c.new_part_id AS new_part,
                   c.old_part_id AS old_part,
                   d.environment_id AS context,
                   d.bom_item_id AS bom_item
            FROM candidate_replacement AS c
            JOIN voltage_compatible AS v
              ON v.part_id = c.old_part_id
            JOIN temperature_compatible AS t
              ON t.part_id = c.old_part_id
             AND t.bom_item_id = v.bom_item_id
            JOIN deployment_environment AS d
              ON d.bom_item_id = v.bom_item_id
            ORDER BY c.new_part_id, c.old_part_id, d.environment_id, d.bom_item_id
            """
        )

        grouped: dict[tuple[str, str, str], set[str]] = defaultdict(set)
        for row in targets:
            grouped[(row["new_part"], row["old_part"], row["context"])].add(
                row["bom_item"]
            )

        compatible_rows = world.query_semantic(
            """
            SELECT v.part_id AS part, v.bom_item_id AS bom_item
            FROM voltage_compatible AS v
            JOIN temperature_compatible AS t
              ON t.part_id = v.part_id
             AND t.bom_item_id = v.bom_item_id
            """
        )
        mechanically_compatible = {
            (row["part"], row["bom_item"]) for row in compatible_rows
        }

        accepted_rows = world.query_semantic(
            """
            SELECT new_part_id AS new_part,
                   old_part_id AS old_part,
                   context_id AS context
            FROM acceptable_replacement
            """
        )
        accepted = {
            (row["new_part"], row["old_part"], row["context"])
            for row in accepted_rows
        }
        unresolved = {
            (
                obligation["values"]["new_part"],
                obligation["values"]["old_part"],
                obligation["values"]["context"],
            )
            for obligation in world.obligations()
            if obligation.get("relation") == "acceptable_replacement"
        }

        cases: list[dict[str, Any]] = []
        for key in sorted(grouped):
            new_part, old_part, context = key
            bom_items = sorted(grouped[key])
            if key in accepted:
                semantic_state = "accepted"
                epistemic = "ASSERTED_TRUE"
            elif key in unresolved:
                semantic_state = "unresolved"
                epistemic = "UNRESOLVED"
            else:
                semantic_state = "not_established"
                epistemic = "NOT_KNOWN"

            cases.append(
                {
                    "new_part": new_part,
                    "old_part": old_part,
                    "context": context,
                    "bom_items": bom_items,
                    "mechanical_state": (
                        "suitable"
                        if all(
                            (new_part, bom_item) in mechanically_compatible
                            for bom_item in bom_items
                        )
                        else "unsuitable"
                    ),
                    "semantic_state": semantic_state,
                    "epistemic": epistemic,
                }
            )

        support: list[dict[str, Any]] = []
        supported_case = next(
            (case for case in cases if case["semantic_state"] == "accepted"), None
        )
        if supported_case is not None:
            values = {
                "new_part": supported_case["new_part"],
                "old_part": supported_case["old_part"],
                "context": supported_case["context"],
            }
            support.append(
                {
                    "claim": (
                        f"{supported_case['new_part']} is accepted as a replacement "
                        f"for {supported_case['old_part']} in "
                        f"{supported_case['context']}"
                    ),
                    "evidence": source_evidence(
                        world, "acceptable_replacement", values
                    ),
                }
            )

        return {"task": "replacement_state", "cases": cases, "support": support}
    finally:
        world.close()


def main() -> None:
    OUTPUT_PATH.write_text(
        json.dumps(compute(), indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
