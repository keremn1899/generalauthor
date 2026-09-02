#!/usr/bin/env python3
"""Compute replacement state from the compiled semantic World."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from taskview import TaskView, TaskViewError
from world_surface import open_world


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "world.sqlite"
OBLIGATIONS_PATH = ROOT / "obligations.json"


def open_compatible_world() -> Any:
    """Use the documented wrapper, tolerating its mismatched fixture view ID."""

    try:
        return open_world()
    except TaskViewError:
        # Read the compiled World's own identity rather than assuming an ID.
        with sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True) as db:
            row = db.execute(
                "SELECT view_id FROM _tv_view WHERE singleton = 1"
            ).fetchone()
        if row is None:
            raise RuntimeError("compiled World has no TaskView identity")
        return TaskView(DB_PATH, view_id=str(row[0]))


def semantic_rows(world: Any, relation: str) -> list[dict[str, Any]]:
    schema = world.relation_schema(relation)
    columns = [role["column"] for role in schema["roles"]]
    return world.query_semantic(
        f"SELECT {', '.join(columns)} FROM {relation}"
    )


def source_evidence(detail: dict[str, Any] | None) -> list[dict[str, str]]:
    evidence: set[tuple[str, str]] = set()
    for grounding in (detail or {}).get("grounding", []):
        if grounding.get("kind") != "SOURCE":
            continue
        source = str(grounding.get("reference", ""))
        locator = str(grounding.get("detail", ""))
        try:
            pointer = json.loads(locator)
        except (TypeError, json.JSONDecodeError):
            pointer = {}
        source = str(pointer.get("native_handle") or source)
        locator = str(pointer.get("native_location") or locator)
        evidence.add((source, locator))
    return [
        {"source": source, "locator": locator}
        for source, locator in sorted(evidence)
    ]


def main() -> None:
    world = open_compatible_world()
    try:
        candidates = {
            (row["new_part_id"], row["old_part_id"])
            for row in semantic_rows(world, "candidate_replacement")
        }
        environments = {
            row["bom_item_id"]: row["environment_id"]
            for row in semantic_rows(world, "deployment_environment")
        }
        voltage_compatible = {
            (row["part_id"], row["bom_item_id"])
            for row in semantic_rows(world, "voltage_compatible")
        }
        temperature_compatible = {
            (row["part_id"], row["bom_item_id"])
            for row in semantic_rows(world, "temperature_compatible")
        }
        eligible = {
            (row["part_id"], row["bom_item_id"])
            for row in semantic_rows(world, "eligible_part")
        }
        accepted = {
            (row["new_part_id"], row["old_part_id"], row["context_id"])
            for row in semantic_rows(world, "acceptable_replacement")
        }

        receipt = world.latest_completeness("eligible_part")
        if (
            receipt is None
            or receipt.get("status") != "COMPLETE"
            or not receipt.get("current")
            or world.is_stale("eligible_part")
        ):
            raise RuntimeError(
                "eligible_part is not current and complete; suitability is indeterminate"
            )

        obligations = json.loads(
            OBLIGATIONS_PATH.read_text(encoding="utf-8")
        ).get("obligations", [])
        unresolved = {
            (
                item["values"]["new_part"],
                item["values"]["old_part"],
                item["values"]["context"],
            )
            for item in obligations
            if item.get("relation") == "acceptable_replacement"
        }

        # A replacement applies to the BOM items that its old part can
        # mechanically serve. Deployment metadata then supplies each context.
        grouped: dict[tuple[str, str, str], set[str]] = {}
        for new_part, old_part in candidates:
            old_items = {
                bom_item
                for part, bom_item in voltage_compatible & temperature_compatible
                if part == old_part and bom_item in environments
            }
            for bom_item in old_items:
                key = (new_part, old_part, environments[bom_item])
                grouped.setdefault(key, set()).add(bom_item)

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
                        if all((new_part, item) in eligible for item in bom_items)
                        else "unsuitable"
                    ),
                    "semantic_state": semantic_state,
                    "epistemic": epistemic,
                }
            )

        support: list[dict[str, Any]] = []
        supported_key = next(
            (
                (case["new_part"], case["old_part"], case["context"])
                for case in cases
                if case["semantic_state"] == "accepted"
            ),
            None,
        )
        if supported_key is not None:
            values = {
                "new_part": supported_key[0],
                "old_part": supported_key[1],
                "context": supported_key[2],
            }
            evidence = source_evidence(
                world.inspect_tuple("acceptable_replacement", values)
            )
            if evidence:
                support.append(
                    {
                        "claim": (
                            f"{supported_key[0]} is an accepted replacement for "
                            f"{supported_key[1]} in {supported_key[2]}"
                        ),
                        "evidence": evidence,
                    }
                )

        result = {
            "task": "replacement_state",
            "cases": cases,
            "support": support,
        }
        (ROOT / "output.json").write_text(
            json.dumps(result, indent=2, sort_keys=False) + "\n",
            encoding="utf-8",
        )
    finally:
        world.close()


if __name__ == "__main__":
    main()
