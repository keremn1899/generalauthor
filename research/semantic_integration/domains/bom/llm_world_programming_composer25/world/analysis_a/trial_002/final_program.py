#!/usr/bin/env python3
"""Compute replacement_state from the compiled semantic World."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from world_surface import open_world

ROOT = Path(__file__).resolve().parent
OUTPUT_PATH = ROOT / "output.json"

CASES_SQL = """
SELECT
    cr.new_part_id AS new_part,
    cr.old_part_id AS old_part,
    de.environment_id AS context,
    de.bom_item_id AS bom_item
FROM candidate_replacement AS cr
JOIN voltage_compatible AS vc
  ON vc.part_id = cr.old_part_id
JOIN temperature_compatible AS tc
  ON tc.part_id = cr.old_part_id
 AND tc.bom_item_id = vc.bom_item_id
JOIN deployment_environment AS de
  ON de.bom_item_id = vc.bom_item_id
ORDER BY cr.new_part_id, cr.old_part_id, de.environment_id, de.bom_item_id
"""


def _obligation_key(values: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(values["new_part"]),
        str(values["old_part"]),
        str(values["context"]),
    )


def _source_evidence(grounding: dict[str, Any]) -> dict[str, str] | None:
    detail = grounding.get("detail")
    if not detail:
        return None
    if isinstance(detail, str):
        detail = json.loads(detail)
    handle = detail.get("native_handle") or detail.get("source")
    locator = detail.get("native_location") or detail.get("source_native_location")
    if not handle or not locator:
        return None
    return {"source": str(handle), "locator": str(locator)}


def _support_for_case(world: Any, case: dict[str, Any]) -> list[dict[str, Any]]:
    tuple_values = {
        "new_part": case["new_part"],
        "old_part": case["old_part"],
        "context": case["context"],
    }
    detail = world.inspect_tuple("acceptable_replacement", tuple_values)
    if detail is None:
        return []

    evidence: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for grounding in detail.get("grounding", []):
        if grounding.get("kind") != "SOURCE":
            continue
        item = _source_evidence(grounding)
        if item is None:
            continue
        key = (item["source"], item["locator"])
        if key in seen:
            continue
        seen.add(key)
        evidence.append(item)

    if not evidence:
        return []

    claim = (
        f"{case['new_part']} is an acceptable replacement for {case['old_part']} "
        f"in {case['context']}"
    )
    return [{"claim": claim, "evidence": evidence}]


def main() -> None:
    world = open_world()
    try:
        obligations = {
            _obligation_key(item["values"]): item for item in world.obligations()
        }
        accepted = {
            (
                row["new_part_id"],
                row["old_part_id"],
                row["context_id"],
            )
            for row in world.query_semantic(
                "SELECT new_part_id, old_part_id, context_id FROM acceptable_replacement"
            )
        }

        grouped: dict[tuple[str, str, str], list[str]] = defaultdict(list)
        for row in world.query_semantic(CASES_SQL):
            key = (row["new_part"], row["old_part"], row["context"])
            grouped[key].append(row["bom_item"])

        cases: list[dict[str, Any]] = []
        for (new_part, old_part, context), bom_items in sorted(grouped.items()):
            bom_items_sorted = sorted(bom_items)
            eligible_rows = world.query_semantic(
                """
                SELECT bom_item_id
                FROM eligible_part
                WHERE part_id = ? AND bom_item_id IN ({})
                """.format(",".join("?" * len(bom_items_sorted))),
                (new_part, *bom_items_sorted),
            )
            eligible = {row["bom_item_id"] for row in eligible_rows}
            mechanical_state = (
                "suitable"
                if all(bom_item in eligible for bom_item in bom_items_sorted)
                else "unsuitable"
            )

            case_key = (new_part, old_part, context)
            if case_key in accepted:
                semantic_state = "accepted"
                epistemic = "ASSERTED_TRUE"
            elif case_key in obligations:
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
                    "bom_items": bom_items_sorted,
                    "mechanical_state": mechanical_state,
                    "semantic_state": semantic_state,
                    "epistemic": epistemic,
                }
            )

        support: list[dict[str, Any]] = []
        for case in cases:
            if case["semantic_state"] == "accepted":
                support = _support_for_case(world, case)
                break

        result = {
            "task": "replacement_state",
            "cases": cases,
            "support": support,
        }
        OUTPUT_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    finally:
        world.close()


if __name__ == "__main__":
    main()
