#!/usr/bin/env python3
"""Compute contextual replacement states from the compiled semantic World."""

from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Any

from taskview import TaskView
from world_surface import DB_PATH, World, open_world, relation_rows


ROOT = Path(__file__).resolve().parent
OUTPUT_PATH = ROOT / "output.json"


def open_packaged_world() -> World:
    """Open the World, tolerating a mismatched view ID in the packaged wrapper."""
    try:
        return open_world()
    except ValueError:
        # The wrapper in some packaged workspaces names a different TaskView.
        # Read the database's own identity, then expose it through the same World API.
        with sqlite3.connect(f"file:{DB_PATH.resolve()}?mode=ro", uri=True) as database:
            row = database.execute(
                "SELECT view_id FROM _tv_view WHERE singleton = 1"
            ).fetchone()
        if row is None:
            raise RuntimeError("The compiled World has no TaskView identity")

        world = World.__new__(World)
        world.path = DB_PATH
        world._tv = TaskView(DB_PATH, view_id=row[0])
        world._origins = {}
        return world


def source_evidence(tuple_detail: dict[str, Any]) -> list[dict[str, str]]:
    """Convert tuple grounding pointers to the requested source/locator shape."""
    evidence: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for grounding in tuple_detail.get("grounding", []):
        if grounding.get("kind") != "SOURCE":
            continue

        raw_detail = grounding.get("detail", "")
        try:
            detail = json.loads(raw_detail)
        except (TypeError, json.JSONDecodeError):
            detail = {}

        source = (
            detail.get("native_handle")
            or detail.get("source")
            or grounding.get("reference")
            or "unknown"
        )
        locator = (
            detail.get("native_location")
            or detail.get("source_native_location")
            or raw_detail
            or grounding.get("reference")
            or "unknown"
        )
        pair = (str(source), str(locator))
        if pair not in seen:
            seen.add(pair)
            evidence.append({"source": pair[0], "locator": pair[1]})

    return evidence


def main() -> None:
    world = open_packaged_world()
    try:
        candidates = relation_rows(world, "candidate_replacement")
        deployments = relation_rows(world, "deployment_environment")
        eligible_rows = relation_rows(world, "eligible_part")
        accepted_rows = relation_rows(world, "acceptable_replacement")
        obligations = world.obligations()

        eligibility_receipt = world.latest_completeness("eligible_part")
        if (
            eligibility_receipt is None
            or eligibility_receipt.get("status") != "COMPLETE"
            or not eligibility_receipt.get("current")
        ):
            raise RuntimeError(
                "Mechanical unsuitability cannot be concluded from incomplete "
                "or stale eligibility results"
            )

        bom_by_context: dict[str, set[str]] = defaultdict(set)
        for row in deployments:
            bom_by_context[row["environment_id"]].add(row["bom_item_id"])

        eligible = {
            (row["part_id"], row["bom_item_id"]) for row in eligible_rows
        }
        accepted = {
            (row["new_part_id"], row["old_part_id"], row["context_id"])
            for row in accepted_rows
        }
        unresolved = {
            (
                item["values"]["new_part"],
                item["values"]["old_part"],
                item["values"]["context"],
            )
            for item in obligations
            if item.get("relation") == "acceptable_replacement"
        }

        cases: list[dict[str, Any]] = []
        for candidate in candidates:
            new_part = candidate["new_part_id"]
            old_part = candidate["old_part_id"]
            for context, bom_set in bom_by_context.items():
                bom_items = sorted(bom_set)
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
                            "suitable"
                            if all((new_part, bom_item) in eligible for bom_item in bom_items)
                            else "unsuitable"
                        ),
                        "semantic_state": semantic_state,
                        "epistemic": epistemic,
                    }
                )

        cases.sort(key=lambda case: (
            case["new_part"],
            case["old_part"],
            case["context"],
        ))

        supported_case = next(
            case for case in cases if case["semantic_state"] == "accepted"
        )
        detail = world.inspect_tuple(
            "acceptable_replacement",
            {
                "new_part": supported_case["new_part"],
                "old_part": supported_case["old_part"],
                "context": supported_case["context"],
            },
        )
        if detail is None:
            raise RuntimeError("Accepted replacement tuple lacks provenance")

        claim = (
            f"{supported_case['new_part']} replaces {supported_case['old_part']} "
            f"in {supported_case['context']} for "
            f"{', '.join(supported_case['bom_items'])}; "
            f"mechanical_state={supported_case['mechanical_state']}; "
            "semantic_state=accepted"
        )
        result = {
            "task": "replacement_state",
            "cases": cases,
            "support": [
                {
                    "claim": claim,
                    "evidence": source_evidence(detail),
                }
            ],
        }
        OUTPUT_PATH.write_text(
            json.dumps(result, indent=2, sort_keys=False) + "\n",
            encoding="utf-8",
        )
    finally:
        world.close()


if __name__ == "__main__":
    main()
