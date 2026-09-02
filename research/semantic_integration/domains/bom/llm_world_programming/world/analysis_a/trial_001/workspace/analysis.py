#!/usr/bin/env python3
"""Compute replacement state from the compiled semantic World."""

from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Any

from taskview import TaskView, TaskViewError
from world_surface import DB_PATH, ORIGINS_PATH, World, open_world, relation_rows


def open_available_world() -> World:
    """Open the World, tolerating the fixture's mismatched stored view ID."""

    try:
        return open_world()
    except TaskViewError as error:
        if "database belongs to TaskView" not in str(error):
            raise

        uri = f"{DB_PATH.resolve().as_uri()}?mode=ro"
        with sqlite3.connect(uri, uri=True) as database:
            row = database.execute(
                "SELECT view_id FROM _tv_view WHERE singleton = 1"
            ).fetchone()
        if row is None:
            raise

        world = World.__new__(World)
        world.path = DB_PATH
        world._tv = TaskView(DB_PATH, view_id=str(row[0]))
        world._origins = {}
        if ORIGINS_PATH.exists():
            world._origins = dict(
                json.loads(ORIGINS_PATH.read_text(encoding="utf-8")).get(
                    "assertions", {}
                )
            )
        return world


def demanded_case_rows(world: World) -> list[dict[str, Any]]:
    return world.query_semantic(
        """
        SELECT DISTINCT
            candidates.new_part_id AS new_part,
            candidates.old_part_id AS old_part,
            environments.environment_id AS context,
            environments.bom_item_id AS bom_item
        FROM candidate_replacement AS candidates
        JOIN part_type AS new_type
          ON new_type.part_id = candidates.new_part_id
        JOIN part_type AS old_type
          ON old_type.part_id = candidates.old_part_id
         AND old_type.part_type = new_type.part_type
        JOIN requires_type AS requirements
          ON requirements.part_type = new_type.part_type
        JOIN deployment_environment AS environments
          ON environments.bom_item_id = requirements.bom_item_id
        ORDER BY new_part, old_part, context, bom_item
        """
    )


def evidence_from(detail: dict[str, Any] | None) -> list[dict[str, str]]:
    evidence: list[dict[str, str]] = []
    for grounding in (detail or {}).get("grounding", []):
        if grounding.get("kind") != "SOURCE":
            continue
        try:
            payload = json.loads(grounding.get("detail", ""))
        except (TypeError, json.JSONDecodeError):
            payload = {}
        source = (
            payload.get("native_handle")
            or payload.get("source")
            or grounding.get("reference")
        )
        locator = (
            payload.get("native_location")
            or payload.get("source_native_location")
            or grounding.get("reference")
        )
        if source and locator:
            evidence.append({"source": str(source), "locator": str(locator)})
    return sorted(evidence, key=lambda item: (item["source"], item["locator"]))


def main() -> None:
    world = open_available_world()
    try:
        completeness = world.latest_completeness("eligible_part")
        if (
            world.is_stale("eligible_part")
            or not completeness
            or not completeness.get("current")
            or completeness.get("status") != "COMPLETE"
            or completeness.get("execution_status") != "SUCCEEDED"
        ):
            raise RuntimeError(
                "eligible_part is not current and complete; mechanical misses "
                "cannot be classified"
            )

        accepted = {
            (row["new_part_id"], row["old_part_id"], row["context_id"])
            for row in relation_rows(world, "acceptable_replacement")
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
        eligible = {
            (row["part_id"], row["bom_item_id"])
            for row in relation_rows(world, "eligible_part")
        }

        grouped: dict[tuple[str, str, str], set[str]] = defaultdict(set)
        for row in demanded_case_rows(world):
            grouped[
                (row["new_part"], row["old_part"], row["context"])
            ].add(row["bom_item"])

        cases: list[dict[str, Any]] = []
        for key in sorted(grouped):
            bom_items = sorted(grouped[key])
            mechanically_suitable = all(
                (key[0], bom_item) in eligible for bom_item in bom_items
            )
            if key in accepted:
                semantic_state, epistemic = "accepted", "ASSERTED_TRUE"
            elif key in unresolved:
                semantic_state, epistemic = "unresolved", "UNRESOLVED"
            else:
                semantic_state, epistemic = "not_established", "NOT_KNOWN"
            cases.append(
                {
                    "new_part": key[0],
                    "old_part": key[1],
                    "context": key[2],
                    "bom_items": bom_items,
                    "mechanical_state": (
                        "suitable" if mechanically_suitable else "unsuitable"
                    ),
                    "semantic_state": semantic_state,
                    "epistemic": epistemic,
                }
            )

        supported_case = next(
            case for case in cases if case["semantic_state"] == "accepted"
        )
        tuple_values = {
            "new_part": supported_case["new_part"],
            "old_part": supported_case["old_part"],
            "context": supported_case["context"],
        }
        detail = world.inspect_tuple("acceptable_replacement", tuple_values)
        support = [
            {
                "claim": (
                    f"{supported_case['new_part']} replaces "
                    f"{supported_case['old_part']} in "
                    f"{supported_case['context']}: "
                    f"{supported_case['mechanical_state']} and accepted"
                ),
                "evidence": evidence_from(detail),
            }
        ]

        result = {
            "task": "replacement_state",
            "cases": cases,
            "support": support,
        }
        output_path = Path(__file__).resolve().parent / "output.json"
        output_path.write_text(
            json.dumps(result, indent=2, sort_keys=False) + "\n",
            encoding="utf-8",
        )
    finally:
        world.close()


if __name__ == "__main__":
    main()
