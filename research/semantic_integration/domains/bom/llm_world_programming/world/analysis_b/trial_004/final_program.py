#!/usr/bin/env python3
"""Compute qualification bottlenecks from the compiled semantic World."""

from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Any

from taskview import TaskView, TaskViewError
from world_surface import DB_PATH, OBLIGATIONS_PATH, open_world, relation_rows


ROOT = Path(__file__).resolve().parent


def open_compiled_world() -> Any:
    """Open through the documented surface, tolerating a mismatched wrapper ID."""

    try:
        return open_world()
    except TaskViewError:
        # The workspace wrapper can be copied with a stale view_id.  Read the
        # compiled database's own identity, then open the same TaskView surface.
        uri = f"file:{DB_PATH.resolve()}?mode=ro"
        with sqlite3.connect(uri, uri=True) as connection:
            row = connection.execute(
                "SELECT view_id FROM _tv_view WHERE singleton = 1"
            ).fetchone()
        if row is None:
            raise RuntimeError("compiled World has no TaskView identity")
        return TaskView(DB_PATH, view_id=str(row[0]))


def rows_by_relation(world: Any, name: str) -> list[dict[str, Any]]:
    return relation_rows(world, name)


def current_complete(world: Any, relation: str) -> bool:
    receipt = world.latest_completeness(relation)
    return bool(
        receipt
        and receipt["status"] == "COMPLETE"
        and receipt["execution_status"] == "SUCCEEDED"
        and receipt["current"]
        and not world.is_stale(relation)
    )


def lifecycle_text(states: set[str]) -> str:
    if not states:
        return "unknown"
    if len(states) == 1:
        return next(iter(states))
    return "conflicting:" + ",".join(sorted(states))


def compute(world: Any) -> dict[str, Any]:
    candidates = rows_by_relation(world, "candidate_replacement")
    part_types = rows_by_relation(world, "part_type")
    requirements = rows_by_relation(world, "requires_type")
    environments = rows_by_relation(world, "deployment_environment")
    lifecycle_rows = rows_by_relation(world, "lifecycle")

    type_by_part: dict[str, set[str]] = defaultdict(set)
    for row in part_types:
        type_by_part[row["part_id"]].add(row["part_type"])

    items_by_type: dict[str, set[str]] = defaultdict(set)
    for row in requirements:
        items_by_type[row["part_type"]].add(row["bom_item_id"])

    contexts_by_item: dict[str, set[str]] = defaultdict(set)
    for row in environments:
        contexts_by_item[row["bom_item_id"]].add(row["environment_id"])

    lifecycle_by_part: dict[str, set[str]] = defaultdict(set)
    for row in lifecycle_rows:
        lifecycle_by_part[row["part_id"]].add(row["state"])

    voltage_pairs = {
        (row["part_id"], row["bom_item_id"])
        for row in rows_by_relation(world, "voltage_compatible")
    }
    temperature_pairs = {
        (row["part_id"], row["bom_item_id"])
        for row in rows_by_relation(world, "temperature_compatible")
    }
    accepted = {
        (row["new_part_id"], row["old_part_id"], row["context_id"])
        for row in rows_by_relation(world, "acceptable_replacement")
    }

    obligations = json.loads(OBLIGATIONS_PATH.read_text(encoding="utf-8"))[
        "obligations"
    ]
    unresolved = {
        (
            obligation["values"]["new_part"],
            obligation["values"]["old_part"],
            obligation["values"]["context"],
        )
        for obligation in obligations
        if obligation.get("relation") == "acceptable_replacement"
    }

    voltage_complete = current_complete(world, "voltage_compatible")
    temperature_complete = current_complete(world, "temperature_compatible")

    cases: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for candidate in candidates:
        new_part = candidate["new_part_id"]
        old_part = candidate["old_part_id"]

        # A replacement is relevant to BOM items requiring the old part's
        # represented type. Qualification relations then test the new part.
        relevant_items: set[str] = set()
        for old_type in type_by_part.get(old_part, set()):
            relevant_items.update(items_by_type.get(old_type, set()))

        for bom_item in relevant_items:
            for context in contexts_by_item.get(bom_item, set()):
                identity = (new_part, old_part, bom_item, context)
                if identity in seen:
                    continue
                seen.add(identity)

                voltage_ok = (new_part, bom_item) in voltage_pairs
                temperature_ok = (new_part, bom_item) in temperature_pairs
                new_states = lifecycle_by_part.get(new_part, set())
                old_states = lifecycle_by_part.get(old_part, set())
                lifecycle_active = new_states == {"active"}

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
                if not lifecycle_active:
                    if not new_states or "active" in new_states:
                        uncertain.append("lifecycle_active")
                    else:
                        prevents.append("lifecycle_active")
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
                        "new_part_lifecycle_active": lifecycle_active,
                        "old_part_lifecycle": lifecycle_text(old_states),
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
    return {"task": "qualification_bottlenecks", "cases": cases}


def main() -> None:
    world = open_compiled_world()
    try:
        result = compute(world)
    finally:
        world.close()
    (ROOT / "output.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
