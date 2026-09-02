#!/usr/bin/env python3
"""Compute qualification bottlenecks from the compiled semantic World."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from taskview import TaskView
from taskview.model import TaskViewError
from world_surface import DB_PATH, OBLIGATIONS_PATH, open_world


ROOT = Path(__file__).resolve().parent


def open_compiled_world() -> Any:
    """Open through the documented surface, tolerating a mismatched wrapper ID."""

    try:
        return open_world()
    except TaskViewError as error:
        # Some packaged workspaces have a stale view_id in world_surface.py. Read
        # the compiled database's identity without changing it, then use the same
        # TaskView query implementation that backs the documented World surface.
        if "database belongs to TaskView" not in str(error):
            raise
        uri = f"{DB_PATH.resolve().as_uri()}?mode=ro"
        with sqlite3.connect(uri, uri=True) as database:
            row = database.execute(
                "SELECT view_id FROM _tv_view WHERE singleton = 1"
            ).fetchone()
        if row is None:
            raise RuntimeError("compiled World has no TaskView identity") from error
        return TaskView(DB_PATH, view_id=str(row[0]))


def is_complete_and_current(world: Any, relation: str) -> bool:
    receipt = world.latest_completeness(relation)
    return bool(
        receipt
        and receipt["status"] == "COMPLETE"
        and receipt["execution_status"] == "SUCCEEDED"
        and receipt["current"]
    )


def semantic_obligations(world: Any) -> list[dict[str, Any]]:
    if hasattr(world, "obligations"):
        return world.obligations()
    return json.loads(OBLIGATIONS_PATH.read_text(encoding="utf-8"))["obligations"]


def main() -> None:
    world = open_compiled_world()
    try:
        compatibility_is_complete = {
            relation: is_complete_and_current(world, relation)
            for relation in ("voltage_compatible", "temperature_compatible")
        }

        rows = world.query_semantic(
            """
            WITH relevant_cases AS (
                SELECT DISTINCT
                    candidate.new_part_id AS new_part,
                    candidate.old_part_id AS old_part,
                    requirement.bom_item_id AS bom_item,
                    deployment.environment_id AS context
                FROM candidate_replacement AS candidate
                JOIN part_type AS old_type
                  ON old_type.part_id = candidate.old_part_id
                JOIN requires_type AS requirement
                  ON requirement.part_type = old_type.part_type
                JOIN deployment_environment AS deployment
                  ON deployment.bom_item_id = requirement.bom_item_id
            )
            SELECT
                relevant.new_part,
                relevant.old_part,
                relevant.bom_item,
                relevant.context,
                EXISTS (
                    SELECT 1
                    FROM voltage_compatible AS compatible
                    WHERE compatible.part_id = relevant.new_part
                      AND compatible.bom_item_id = relevant.bom_item
                ) AS voltage_compatible,
                EXISTS (
                    SELECT 1
                    FROM temperature_compatible AS compatible
                    WHERE compatible.part_id = relevant.new_part
                      AND compatible.bom_item_id = relevant.bom_item
                ) AS temperature_compatible,
                (
                    SELECT state
                    FROM lifecycle
                    WHERE part_id = relevant.new_part
                    ORDER BY state
                    LIMIT 1
                ) AS new_part_lifecycle,
                (
                    SELECT state
                    FROM lifecycle
                    WHERE part_id = relevant.old_part
                    ORDER BY state
                    LIMIT 1
                ) AS old_part_lifecycle,
                EXISTS (
                    SELECT 1
                    FROM acceptable_replacement AS acceptable
                    WHERE acceptable.new_part_id = relevant.new_part
                      AND acceptable.old_part_id = relevant.old_part
                      AND acceptable.context_id = relevant.context
                ) AS semantically_accepted
            FROM relevant_cases AS relevant
            ORDER BY
                relevant.new_part,
                relevant.old_part,
                relevant.bom_item,
                relevant.context
            """
        )

        unresolved = {
            (
                obligation["values"].get("new_part"),
                obligation["values"].get("old_part"),
                obligation["values"].get("context"),
            )
            for obligation in semantic_obligations(world)
            if obligation.get("relation") == "acceptable_replacement"
        }

        cases = []
        for row in rows:
            accepted = bool(row["semantically_accepted"])
            semantic_key = (row["new_part"], row["old_part"], row["context"])
            semantic_state = (
                "accepted"
                if accepted
                else "unresolved"
                if semantic_key in unresolved
                else "not_established"
            )

            voltage_ok = bool(row["voltage_compatible"])
            temperature_ok = bool(row["temperature_compatible"])
            new_lifecycle = row["new_part_lifecycle"]
            lifecycle_active = new_lifecycle == "active"

            prevents: list[str] = []
            uncertain: list[str] = []
            for name, compatible in (
                ("voltage_compatible", voltage_ok),
                ("temperature_compatible", temperature_ok),
            ):
                if not compatible:
                    if compatibility_is_complete[name]:
                        prevents.append(name)
                    else:
                        uncertain.append(name)

            if not lifecycle_active:
                if new_lifecycle is None:
                    uncertain.append("lifecycle_active")
                else:
                    prevents.append("lifecycle_active")

            # Lack of a positive semantic judgment is uncertainty, not failure.
            if semantic_state != "accepted":
                uncertain.append("semantic_acceptance")

            cases.append(
                {
                    "new_part": row["new_part"],
                    "old_part": row["old_part"],
                    "bom_item": row["bom_item"],
                    "context": row["context"],
                    "voltage_compatible": voltage_ok,
                    "temperature_compatible": temperature_ok,
                    "new_part_lifecycle_active": lifecycle_active,
                    "old_part_lifecycle": row["old_part_lifecycle"] or "unknown",
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
            json.dumps(result, indent=2) + "\n", encoding="utf-8"
        )
    finally:
        world.close()


if __name__ == "__main__":
    main()
