#!/usr/bin/env python3
"""Compute replacement state from the compiled semantic World."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from taskview import TaskView, TaskViewError
from world_surface import open_world, relation_rows


ROOT = Path(__file__).resolve().parent


def open_compiled_world() -> Any:
    """Open through the documented surface, tolerating a packaged ID mismatch."""

    try:
        return open_world()
    except TaskViewError:
        database = ROOT / "world.sqlite"
        with sqlite3.connect(f"file:{database}?mode=ro", uri=True) as connection:
            row = connection.execute(
                "SELECT view_id FROM _tv_view WHERE singleton = 1"
            ).fetchone()
        if row is None:
            raise RuntimeError("compiled World has no TaskView identity")
        return TaskView(database, view_id=row[0])


def obligations(world: Any) -> list[dict[str, Any]]:
    if hasattr(world, "obligations"):
        return world.obligations()
    document = json.loads((ROOT / "obligations.json").read_text(encoding="utf-8"))
    return document["obligations"]


def source_evidence(detail: dict[str, Any] | None) -> list[dict[str, str]]:
    evidence: set[tuple[str, str]] = set()
    for grounding in (detail or {}).get("grounding", []):
        if grounding.get("kind") != "SOURCE":
            continue
        try:
            metadata = json.loads(grounding.get("detail", ""))
        except (TypeError, json.JSONDecodeError):
            metadata = {}
        source = metadata.get("native_handle") or metadata.get("source")
        locator = metadata.get("native_location") or metadata.get(
            "source_native_location"
        )
        if source and locator:
            evidence.add((str(source), str(locator)))
        else:
            evidence.add(
                (str(grounding.get("reference", "")), str(grounding.get("detail", "")))
            )
    return [
        {"source": source, "locator": locator}
        for source, locator in sorted(evidence)
    ]


def main() -> None:
    world = open_compiled_world()
    try:
        receipt = world.latest_completeness("eligible_part")
        if (
            not receipt
            or receipt["status"] != "COMPLETE"
            or not receipt["current"]
            or receipt["execution_status"] != "SUCCEEDED"
        ):
            raise RuntimeError("eligible_part is not backed by current completeness")

        candidates = {
            (row["new_part_id"], row["old_part_id"])
            for row in relation_rows(world, "candidate_replacement")
        }
        accepted = {
            (row["new_part_id"], row["old_part_id"], row["context_id"])
            for row in relation_rows(world, "acceptable_replacement")
            if (row["new_part_id"], row["old_part_id"]) in candidates
        }

        unresolved = set()
        for item in obligations(world):
            if item.get("relation") != "acceptable_replacement":
                continue
            values = item.get("values", {})
            pair = (values.get("new_part"), values.get("old_part"))
            if pair in candidates and values.get("context"):
                unresolved.add((*pair, values["context"]))

        represented_cases = accepted | unresolved

        bom_by_context: dict[str, list[str]] = {}
        for row in relation_rows(world, "deployment_environment"):
            bom_by_context.setdefault(row["environment_id"], []).append(
                row["bom_item_id"]
            )
        for items in bom_by_context.values():
            items.sort()

        eligible = {
            (row["part_id"], row["bom_item_id"])
            for row in relation_rows(world, "eligible_part")
        }

        cases = []
        for new_part, old_part, context in sorted(represented_cases):
            bom_items = bom_by_context.get(context, [])
            mechanically_suitable = bool(bom_items) and all(
                (new_part, bom_item) in eligible for bom_item in bom_items
            )
            key = (new_part, old_part, context)
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
                        "suitable" if mechanically_suitable else "unsuitable"
                    ),
                    "semantic_state": semantic_state,
                    "epistemic": epistemic,
                }
            )

        support = []
        supported = next(
            (case for case in cases if case["semantic_state"] == "accepted"), None
        )
        if supported is not None:
            values = {
                "new_part": supported["new_part"],
                "old_part": supported["old_part"],
                "context": supported["context"],
            }
            detail = world.inspect_tuple("acceptable_replacement", values)
            support.append(
                {
                    "claim": (
                        f"{supported['new_part']} is an accepted replacement for "
                        f"{supported['old_part']} in {supported['context']}"
                    ),
                    "evidence": source_evidence(detail),
                }
            )

        result = {"task": "replacement_state", "cases": cases, "support": support}
        (ROOT / "output.json").write_text(
            json.dumps(result, indent=2, sort_keys=False) + "\n", encoding="utf-8"
        )
    finally:
        world.close()


if __name__ == "__main__":
    main()
