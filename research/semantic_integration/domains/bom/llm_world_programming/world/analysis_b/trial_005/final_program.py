#!/usr/bin/env python3
"""Report qualification bottlenecks for represented replacement candidates."""

from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Any

from taskview import TaskView
from taskview.model import TaskViewError
from world_surface import DB_PATH, OBLIGATIONS_PATH, open_world


ROOT = Path(__file__).resolve().parent
OUTPUT_PATH = ROOT / "output.json"


class _TaskViewWorld:
    """Compatibility adapter for a compiled DB whose stored view ID moved."""

    def __init__(self, taskview: TaskView) -> None:
        self.taskview = taskview

    def query_semantic(
        self, sql: str, parameters: tuple[Any, ...] = ()
    ) -> list[dict[str, Any]]:
        return self.taskview.query_semantic(sql, parameters)

    def latest_completeness(self, relation: str) -> dict[str, Any] | None:
        return self.taskview.latest_completeness(relation)

    def obligations(self) -> list[dict[str, Any]]:
        payload = json.loads(OBLIGATIONS_PATH.read_text(encoding="utf-8"))
        return payload["obligations"]

    def close(self) -> None:
        self.taskview.close()


def open_compiled_world() -> Any:
    """Use the documented opener, tolerating a stale workspace view ID."""

    try:
        return open_world()
    except TaskViewError:
        # Discover identity read-only; TaskView still supplies all semantic queries.
        connection = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
        try:
            row = connection.execute(
                "SELECT view_id FROM _tv_view WHERE singleton = 1"
            ).fetchone()
        finally:
            connection.close()
        if row is None:
            raise RuntimeError("compiled World has no TaskView identity")
        return _TaskViewWorld(TaskView(DB_PATH, view_id=str(row[0])))


def relation_pairs(world: Any, relation: str) -> set[tuple[str, str]]:
    rows = world.query_semantic(
        f"SELECT part_id AS part, bom_item_id AS bom_item FROM {relation}"
    )
    return {(row["part"], row["bom_item"]) for row in rows}


def negative_is_established(world: Any, relation: str) -> bool:
    receipt = world.latest_completeness(relation)
    return bool(
        receipt
        and receipt["status"] == "COMPLETE"
        and receipt["execution_status"] == "SUCCEEDED"
        and receipt["current"]
    )


def main() -> None:
    world = open_compiled_world()
    try:
        # A candidate is relevant to each deployed BOM item that calls for the
        # old part's represented type. Compatibility derivations evaluate the
        # candidate against that item's complete requirements.
        represented_cases = world.query_semantic(
            """
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
            """
        )

        voltage_pairs = relation_pairs(world, "voltage_compatible")
        temperature_pairs = relation_pairs(world, "temperature_compatible")
        voltage_negative_known = negative_is_established(
            world, "voltage_compatible"
        )
        temperature_negative_known = negative_is_established(
            world, "temperature_compatible"
        )

        lifecycle_by_part: dict[str, set[str]] = defaultdict(set)
        for row in world.query_semantic(
            "SELECT part_id AS part, state FROM lifecycle"
        ):
            lifecycle_by_part[row["part"]].add(row["state"])

        accepted = {
            (row["new_part"], row["old_part"], row["context"])
            for row in world.query_semantic(
                """
                SELECT new_part_id AS new_part, old_part_id AS old_part,
                       context_id AS context
                FROM acceptable_replacement
                """
            )
        }
        unresolved = {
            (
                obligation["values"]["new_part"],
                obligation["values"]["old_part"],
                obligation["values"]["context"],
            )
            for obligation in world.obligations()
            if obligation.get("relation") == "acceptable_replacement"
            and {"new_part", "old_part", "context"}
            <= obligation.get("values", {}).keys()
        }

        cases = []
        for represented in represented_cases:
            new_part = represented["new_part"]
            old_part = represented["old_part"]
            bom_item = represented["bom_item"]
            context = represented["context"]
            part_item = (new_part, bom_item)
            semantic_key = (new_part, old_part, context)

            voltage_compatible = part_item in voltage_pairs
            temperature_compatible = part_item in temperature_pairs
            new_lifecycle_states = lifecycle_by_part.get(new_part, set())
            new_part_lifecycle_active = "active" in new_lifecycle_states
            old_lifecycle_states = lifecycle_by_part.get(old_part, set())
            old_part_lifecycle = (
                next(iter(old_lifecycle_states))
                if len(old_lifecycle_states) == 1
                else "unknown"
                if not old_lifecycle_states
                else "|".join(sorted(old_lifecycle_states))
            )

            prevents: list[str] = []
            uncertain: list[str] = []

            if not voltage_compatible:
                (prevents if voltage_negative_known else uncertain).append(
                    "voltage_compatible"
                )
            if not temperature_compatible:
                (prevents if temperature_negative_known else uncertain).append(
                    "temperature_compatible"
                )
            if not new_part_lifecycle_active:
                if new_lifecycle_states:
                    prevents.append("lifecycle_active")
                else:
                    uncertain.append("lifecycle_active")

            if semantic_key in accepted:
                semantic_state = "accepted"
            elif semantic_key in unresolved:
                semantic_state = "unresolved"
                uncertain.append("semantic_acceptance")
            else:
                semantic_state = "not_established"
                # Absence is uncertainty, not a failed qualification constraint.
                uncertain.append("semantic_acceptance")

            cases.append(
                {
                    "new_part": new_part,
                    "old_part": old_part,
                    "bom_item": bom_item,
                    "context": context,
                    "voltage_compatible": voltage_compatible,
                    "temperature_compatible": temperature_compatible,
                    "new_part_lifecycle_active": new_part_lifecycle_active,
                    "old_part_lifecycle": old_part_lifecycle,
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
        OUTPUT_PATH.write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    finally:
        world.close()


if __name__ == "__main__":
    main()
