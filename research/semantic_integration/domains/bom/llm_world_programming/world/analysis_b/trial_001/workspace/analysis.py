#!/usr/bin/env python3
"""Report qualification bottlenecks for represented replacement candidates."""

from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Any

from taskview import TaskView, TaskViewError
from world_surface import DB_PATH, OBLIGATIONS_PATH, open_world, relation_rows


ROOT = Path(__file__).resolve().parent


def open_packaged_world() -> tuple[Any, list[dict[str, Any]]]:
    """Open through the public surface, tolerating the supplied view-ID mismatch."""

    try:
        world = open_world()
        return world, world.obligations()
    except TaskViewError as exc:
        if "database belongs to TaskView" not in str(exc):
            raise

    uri = f"{DB_PATH.resolve().as_uri()}?mode=ro"
    with sqlite3.connect(uri, uri=True) as database:
        row = database.execute(
            "SELECT view_id FROM _tv_view WHERE singleton = 1"
        ).fetchone()
    if row is None:
        raise RuntimeError("compiled World has no TaskView identity")

    world = TaskView(DB_PATH, view_id=str(row[0]))
    obligations = json.loads(OBLIGATIONS_PATH.read_text(encoding="utf-8"))[
        "obligations"
    ]
    return world, obligations


def semantic_rows(world: Any, relation: str) -> list[dict[str, Any]]:
    """Return relation rows keyed by semantic role rather than SQL column name."""

    schema = world.relation_schema(relation)
    roles = schema["roles"]
    return [
        {role["name"]: row[role["column"]] for role in roles}
        for row in relation_rows(world, relation)
    ]


def relation_is_complete(world: Any, relation: str) -> bool:
    receipt = world.latest_completeness(relation)
    return bool(
        receipt
        and receipt["status"] == "COMPLETE"
        and receipt.get("current", not receipt.get("stale", False))
        and not receipt.get("stale", False)
    )


def main() -> None:
    world, obligations = open_packaged_world()
    try:
        candidates = semantic_rows(world, "candidate_replacement")
        part_types = semantic_rows(world, "part_type")
        requirements = semantic_rows(world, "requires_type")
        environments = semantic_rows(world, "deployment_environment")
        voltage_rows = semantic_rows(world, "voltage_compatible")
        temperature_rows = semantic_rows(world, "temperature_compatible")
        lifecycle_rows = semantic_rows(world, "lifecycle")
        acceptance_rows = semantic_rows(world, "acceptable_replacement")

        types_by_part: dict[str, set[str]] = defaultdict(set)
        for row in part_types:
            types_by_part[row["part"]].add(row["part_type"])

        boms_by_type: dict[str, set[str]] = defaultdict(set)
        for row in requirements:
            boms_by_type[row["part_type"]].add(row["bom_item"])

        contexts_by_bom: dict[str, set[str]] = defaultdict(set)
        for row in environments:
            contexts_by_bom[row["bom_item"]].add(row["environment"])

        lifecycle_by_part: dict[str, set[str]] = defaultdict(set)
        for row in lifecycle_rows:
            lifecycle_by_part[row["part"]].add(row["state"])

        voltage_compatible = {
            (row["part"], row["bom_item"]) for row in voltage_rows
        }
        temperature_compatible = {
            (row["part"], row["bom_item"]) for row in temperature_rows
        }
        accepted = {
            (row["new_part"], row["old_part"], row["context"])
            for row in acceptance_rows
        }
        unresolved = {
            (
                obligation["values"].get("new_part"),
                obligation["values"].get("old_part"),
                obligation["values"].get("context"),
            )
            for obligation in obligations
            if obligation.get("relation") == "acceptable_replacement"
        }

        voltage_complete = relation_is_complete(world, "voltage_compatible")
        temperature_complete = relation_is_complete(world, "temperature_compatible")
        cases: list[dict[str, Any]] = []

        for candidate in candidates:
            new_part = candidate["new_part"]
            old_part = candidate["old_part"]
            relevant_boms: set[str] = set()
            for part_type in types_by_part[old_part]:
                relevant_boms.update(boms_by_type[part_type])

            for bom_item in relevant_boms:
                for context in contexts_by_bom[bom_item]:
                    voltage_ok = (new_part, bom_item) in voltage_compatible
                    temperature_ok = (new_part, bom_item) in temperature_compatible
                    new_lifecycle_states = lifecycle_by_part[new_part]
                    new_active = "active" in new_lifecycle_states
                    old_lifecycle_states = lifecycle_by_part[old_part]
                    old_lifecycle = (
                        next(iter(old_lifecycle_states))
                        if len(old_lifecycle_states) == 1
                        else "unknown"
                    )

                    semantic_key = (new_part, old_part, context)
                    if semantic_key in accepted:
                        semantic_state = "accepted"
                    elif semantic_key in unresolved:
                        semantic_state = "unresolved"
                    else:
                        semantic_state = "not_established"

                    prevents: list[str] = []
                    uncertain: list[str] = []
                    if not voltage_ok:
                        (prevents if voltage_complete else uncertain).append(
                            "voltage_compatible"
                        )
                    if not temperature_ok:
                        (prevents if temperature_complete else uncertain).append(
                            "temperature_compatible"
                        )
                    if not new_active:
                        (
                            prevents if new_lifecycle_states else uncertain
                        ).append("lifecycle_active")
                    if semantic_state != "accepted":
                        uncertain.append("semantic_acceptance")

                    cases.append(
                        {
                            "new_part": new_part,
                            "old_part": old_part,
                            "bom_item": bom_item,
                            "context": context,
                            "voltage_compatible": voltage_ok,
                            "temperature_compatible": temperature_ok,
                            "new_part_lifecycle_active": new_active,
                            "old_part_lifecycle": old_lifecycle,
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
