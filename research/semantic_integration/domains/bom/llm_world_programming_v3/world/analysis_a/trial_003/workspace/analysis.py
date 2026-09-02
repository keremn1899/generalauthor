#!/usr/bin/env python3
"""Compute replacement state from the compiled semantic World."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from world_surface import open_world, relation_rows


ROOT = Path(__file__).resolve().parent


def logical_rows(world: Any, relation: str) -> list[dict[str, Any]]:
    """Return relation rows keyed by semantic role rather than SQL column."""
    role_for_column = {
        role["column"]: role["name"]
        for role in world.relation_schema(relation)["roles"]
    }
    return [
        {role_for_column[column]: value for column, value in row.items()}
        for row in relation_rows(world, relation)
    ]


def evidence_from_tuple(
    world: Any, relation: str, values: dict[str, str]
) -> list[dict[str, str]]:
    detail = world.inspect_tuple(relation, values) or {}
    evidence: list[dict[str, str]] = []
    for grounding in detail.get("grounding", []):
        if grounding.get("kind") != "SOURCE":
            continue
        try:
            source_detail = json.loads(grounding.get("detail", ""))
        except (TypeError, json.JSONDecodeError):
            source_detail = {}
        source = source_detail.get("native_handle") or source_detail.get("source")
        locator = source_detail.get("native_location") or source_detail.get(
            "source_native_location"
        )
        if source and locator:
            item = {"source": str(source), "locator": str(locator)}
            if item not in evidence:
                evidence.append(item)
    return evidence


def main() -> None:
    world = open_world()
    try:
        candidates = logical_rows(world, "candidate_replacement")
        deployments = logical_rows(world, "deployment_environment")
        requirements = logical_rows(world, "requires_type")
        part_types = logical_rows(world, "part_type")
        eligible_rows = logical_rows(world, "eligible_part")
        accepted_rows = logical_rows(world, "acceptable_replacement")
        obligations = world.obligations()

        types_by_part: dict[str, set[str]] = defaultdict(set)
        for row in part_types:
            types_by_part[row["part"]].add(row["part_type"])

        required_type_by_bom: dict[str, set[str]] = defaultdict(set)
        for row in requirements:
            required_type_by_bom[row["bom_item"]].add(row["part_type"])

        context_by_bom: dict[str, set[str]] = defaultdict(set)
        for row in deployments:
            context_by_bom[row["bom_item"]].add(row["environment"])

        eligible = {(row["part"], row["bom_item"]) for row in eligible_rows}
        accepted = {
            (row["new_part"], row["old_part"], row["context"])
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
            and {"new_part", "old_part", "context"} <= item.get("values", {}).keys()
        }

        applicable: dict[tuple[str, str, str], set[str]] = defaultdict(set)
        for candidate in candidates:
            new_part = candidate["new_part"]
            old_part = candidate["old_part"]
            replacement_types = types_by_part[old_part]
            for bom_item, required_types in required_type_by_bom.items():
                if replacement_types.isdisjoint(required_types):
                    continue
                for context in context_by_bom[bom_item]:
                    applicable[(new_part, old_part, context)].add(bom_item)

        cases: list[dict[str, Any]] = []
        for key, bom_set in applicable.items():
            new_part, old_part, context = key
            bom_items = sorted(bom_set)
            mechanically_suitable = all(
                (new_part, bom_item) in eligible for bom_item in bom_items
            )
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

        cases.sort(key=lambda case: (case["new_part"], case["old_part"], case["context"]))

        support: list[dict[str, Any]] = []
        for case in cases:
            key = (case["new_part"], case["old_part"], case["context"])
            if key not in accepted:
                continue
            values = {
                "new_part": case["new_part"],
                "old_part": case["old_part"],
                "context": case["context"],
            }
            evidence = evidence_from_tuple(world, "acceptable_replacement", values)
            if evidence:
                support.append(
                    {
                        "claim": (
                            f"acceptable_replacement({case['new_part']}, "
                            f"{case['old_part']}, {case['context']})"
                        ),
                        "evidence": evidence,
                    }
                )
                break

        result = {"task": "replacement_state", "cases": cases, "support": support}
        (ROOT / "output.json").write_text(
            json.dumps(result, indent=2, sort_keys=False) + "\n", encoding="utf-8"
        )
    finally:
        world.close()


if __name__ == "__main__":
    main()
