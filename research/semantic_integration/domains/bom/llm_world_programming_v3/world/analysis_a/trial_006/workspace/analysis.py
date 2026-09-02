#!/usr/bin/env python3
"""Compute replacement state from the workspace's compiled semantic World."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from world_surface import open_world, relation_rows


ROOT = Path(__file__).resolve().parent


def semantic_rows(world: Any, relation: str) -> list[dict[str, Any]]:
    """Return relation tuples keyed by semantic role rather than SQL column."""
    schema = world.relation_schema(relation)
    raw_rows = relation_rows(world, relation)
    return [
        {role["name"]: row[role["column"]] for role in schema["roles"]}
        for row in raw_rows
    ]


def source_evidence(tuple_detail: dict[str, Any]) -> list[dict[str, str]]:
    """Extract source handles and native locators from tuple provenance."""
    evidence: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for grounding in tuple_detail.get("grounding", []):
        if grounding.get("kind") != "SOURCE":
            continue
        try:
            detail = json.loads(grounding.get("detail") or "{}")
        except json.JSONDecodeError:
            detail = {}

        source = detail.get("native_handle") or detail.get("source")
        locator = detail.get("native_location") or detail.get(
            "source_native_location"
        )
        if not source:
            source = grounding.get("reference", "unknown")
        if not locator:
            locator = grounding.get("reference", "unknown")

        key = (str(source), str(locator))
        if key not in seen:
            seen.add(key)
            evidence.append({"source": key[0], "locator": key[1]})

    return evidence


def main() -> None:
    world = open_world()
    try:
        candidates = semantic_rows(world, "candidate_replacement")
        accepted_rows = semantic_rows(world, "acceptable_replacement")
        part_types = semantic_rows(world, "part_type")
        requirements = semantic_rows(world, "requires_type")
        deployments = semantic_rows(world, "deployment_environment")
        eligible_rows = semantic_rows(world, "eligible_part")
        obligations = world.obligations()

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
        types_by_part: dict[str, set[str]] = {}
        for row in part_types:
            types_by_part.setdefault(row["part"], set()).add(row["part_type"])
        required_type_by_bom: dict[str, set[str]] = {}
        for row in requirements:
            required_type_by_bom.setdefault(row["bom_item"], set()).add(
                row["part_type"]
            )
        contexts_by_bom: dict[str, set[str]] = {}
        for row in deployments:
            contexts_by_bom.setdefault(row["bom_item"], set()).add(
                row["environment"]
            )
        eligible = {(row["part"], row["bom_item"]) for row in eligible_rows}

        cases: list[dict[str, Any]] = []
        for candidate in candidates:
            new_part = candidate["new_part"]
            old_part = candidate["old_part"]
            old_types = types_by_part.get(old_part, set())

            applicable_by_context: dict[str, set[str]] = {}
            for bom_item, required_types in required_type_by_bom.items():
                if old_types.isdisjoint(required_types):
                    continue
                for context in contexts_by_bom.get(bom_item, set()):
                    applicable_by_context.setdefault(context, set()).add(bom_item)

            # Preserve semantically represented candidate/context cases even if
            # their mechanical applicability data is incomplete.
            represented_contexts = {
                context
                for new, old, context in accepted | unresolved
                if new == new_part and old == old_part
            }
            for context in represented_contexts:
                applicable_by_context.setdefault(context, set())

            for context, item_set in applicable_by_context.items():
                bom_items = sorted(item_set)
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

                mechanically_suitable = bool(bom_items) and all(
                    (new_part, bom_item) in eligible for bom_item in bom_items
                )
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

        cases.sort(key=lambda case: (
            case["new_part"],
            case["old_part"],
            case["context"],
        ))

        support: list[dict[str, Any]] = []
        supported_case = next(
            (
                case
                for case in cases
                if case["semantic_state"] == "accepted"
            ),
            None,
        )
        if supported_case is not None:
            values = {
                "new_part": supported_case["new_part"],
                "old_part": supported_case["old_part"],
                "context": supported_case["context"],
            }
            detail = world.inspect_tuple("acceptable_replacement", values)
            if detail is not None:
                support.append(
                    {
                        "claim": (
                            f'{values["new_part"]} is an accepted replacement '
                            f'for {values["old_part"]} in {values["context"]}'
                        ),
                        "evidence": source_evidence(detail),
                    }
                )

        result = {
            "task": "replacement_state",
            "cases": cases,
            "support": support,
        }
        (ROOT / "output.json").write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8"
        )
    finally:
        world.close()


if __name__ == "__main__":
    main()
