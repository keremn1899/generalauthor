#!/usr/bin/env python3
"""Compute replacement state from the workspace's compiled semantic World."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from world_surface import open_world, relation_rows


ROOT = Path(__file__).resolve().parent


def tuples(world: Any, relation: str, *roles: str) -> set[tuple[str, ...]]:
    schema = world.relation_schema(relation)
    columns = {role["name"]: role["column"] for role in schema["roles"]}
    return {
        tuple(str(row[columns[role]]) for role in roles)
        for row in relation_rows(world, relation)
    }


def source_evidence(detail: dict[str, Any] | None) -> list[dict[str, str]]:
    """Convert tuple grounding pointers to the requested source/locator shape."""
    evidence: list[dict[str, str]] = []
    if detail is None:
        return evidence

    for grounding in detail.get("grounding", []):
        if grounding.get("kind") != "SOURCE":
            continue
        metadata = json.loads(grounding.get("detail") or "{}")
        source = metadata.get("native_handle") or metadata.get("source")
        locator = metadata.get("native_location") or metadata.get(
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
        candidates = tuples(
            world, "candidate_replacement", "new_part", "old_part"
        )
        deployments = tuples(
            world, "deployment_environment", "bom_item", "environment"
        )
        part_types = dict(tuples(world, "part_type", "part", "part_type"))
        required_types = dict(
            tuples(world, "requires_type", "bom_item", "part_type")
        )
        voltage_ok = tuples(
            world, "voltage_compatible", "part", "bom_item"
        )
        temperature_ok = tuples(
            world, "temperature_compatible", "part", "bom_item"
        )
        accepted = tuples(
            world,
            "acceptable_replacement",
            "new_part",
            "old_part",
            "context",
        )
        unresolved = {
            (
                str(item["values"]["new_part"]),
                str(item["values"]["old_part"]),
                str(item["values"]["context"]),
            )
            for item in world.obligations()
            if item.get("relation") == "acceptable_replacement"
        }

        # A replacement applies to BOM positions requiring the old part's type.
        grouped: dict[tuple[str, str, str], list[str]] = {}
        for new_part, old_part in candidates:
            old_type = part_types.get(old_part)
            for bom_item, context in deployments:
                if old_type is not None and required_types.get(bom_item) == old_type:
                    grouped.setdefault(
                        (new_part, old_part, context), []
                    ).append(bom_item)

        cases: list[dict[str, Any]] = []
        for key in sorted(grouped):
            new_part, old_part, context = key
            bom_items = sorted(set(grouped[key]))
            mechanically_suitable = all(
                (new_part, bom_item) in voltage_ok
                and (new_part, bom_item) in temperature_ok
                for bom_item in bom_items
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

        support: list[dict[str, Any]] = []
        supported_case = next(
            (case for case in cases if case["semantic_state"] == "accepted"),
            None,
        )
        if supported_case is not None:
            values = {
                "new_part": supported_case["new_part"],
                "old_part": supported_case["old_part"],
                "context": supported_case["context"],
            }
            detail = world.inspect_tuple("acceptable_replacement", values)
            support.append(
                {
                    "claim": (
                        f"{supported_case['new_part']} replacing "
                        f"{supported_case['old_part']} in "
                        f"{supported_case['context']} is accepted"
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
