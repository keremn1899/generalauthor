#!/usr/bin/env python3
"""Compute qualification bottlenecks from the compiled semantic World."""

from __future__ import annotations

import json
from pathlib import Path

from world_surface import open_world, relation_rows


OUTPUT_PATH = Path(__file__).resolve().with_name("output.json")


def row_tuples(world, relation: str, *columns: str) -> set[tuple]:
    """Return selected relation columns as tuples."""
    return {
        tuple(row[column] for column in columns)
        for row in relation_rows(world, relation)
    }


def require_complete(world, relation: str) -> None:
    """Ensure absence from a derived qualification relation is meaningful."""
    receipt = world.latest_completeness(relation)
    if (
        receipt is None
        or receipt.get("status") != "COMPLETE"
        or not receipt.get("current")
        or receipt.get("stale")
        or receipt.get("execution_status") != "SUCCEEDED"
    ):
        raise RuntimeError(
            f"{relation} lacks a current, successful COMPLETE receipt"
        )


def main() -> None:
    world = open_world()
    try:
        require_complete(world, "voltage_compatible")
        require_complete(world, "temperature_compatible")

        candidates = row_tuples(
            world, "candidate_replacement", "new_part_id", "old_part_id"
        )
        part_types = row_tuples(world, "part_type", "part_id", "part_type")
        required_types = row_tuples(
            world, "requires_type", "bom_item_id", "part_type"
        )
        environments = dict(
            row_tuples(
                world,
                "deployment_environment",
                "bom_item_id",
                "environment_id",
            )
        )
        voltage_ok = row_tuples(
            world, "voltage_compatible", "part_id", "bom_item_id"
        )
        temperature_ok = row_tuples(
            world, "temperature_compatible", "part_id", "bom_item_id"
        )
        lifecycle = dict(row_tuples(world, "lifecycle", "part_id", "state"))
        accepted = row_tuples(
            world,
            "acceptable_replacement",
            "new_part_id",
            "old_part_id",
            "context_id",
        )

        unresolved = {
            (
                item["values"]["new_part"],
                item["values"]["old_part"],
                item["values"]["context"],
            )
            for item in world.obligations()
            if item.get("relation") == "acceptable_replacement"
            and {"new_part", "old_part", "context"}
            <= item.get("values", {}).keys()
        }

        types_by_part: dict[str, set[str]] = {}
        for part, part_type in part_types:
            types_by_part.setdefault(part, set()).add(part_type)

        boms_by_type: dict[str, set[str]] = {}
        for bom_item, part_type in required_types:
            boms_by_type.setdefault(part_type, set()).add(bom_item)

        cases = []
        for new_part, old_part in candidates:
            # A BOM item is relevant when it requires the represented old
            # part's type. Eligibility is deliberately not used here because
            # a discontinued old part can be the reason replacement is needed.
            relevant_boms = set()
            for old_type in types_by_part.get(old_part, set()):
                relevant_boms.update(boms_by_type.get(old_type, set()))

            for bom_item in relevant_boms:
                context = environments[bom_item]
                voltage_compatible = (new_part, bom_item) in voltage_ok
                temperature_compatible = (new_part, bom_item) in temperature_ok
                new_part_lifecycle_active = lifecycle.get(new_part) == "active"
                semantic_key = (new_part, old_part, context)

                if semantic_key in accepted:
                    semantic_state = "accepted"
                elif semantic_key in unresolved:
                    semantic_state = "unresolved"
                else:
                    semantic_state = "not_established"

                prevents_viability = []
                if not voltage_compatible:
                    prevents_viability.append("voltage_compatible")
                if not temperature_compatible:
                    prevents_viability.append("temperature_compatible")
                if not new_part_lifecycle_active:
                    prevents_viability.append("lifecycle_active")

                leaves_viability_uncertain = []
                if semantic_state != "accepted":
                    leaves_viability_uncertain.append("semantic_acceptance")

                cases.append(
                    {
                        "new_part": new_part,
                        "old_part": old_part,
                        "bom_item": bom_item,
                        "context": context,
                        "voltage_compatible": voltage_compatible,
                        "temperature_compatible": temperature_compatible,
                        "new_part_lifecycle_active": new_part_lifecycle_active,
                        "old_part_lifecycle": lifecycle.get(old_part, "unknown"),
                        "semantic_state": semantic_state,
                        "prevents_viability": prevents_viability,
                        "leaves_viability_uncertain": leaves_viability_uncertain,
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
        OUTPUT_PATH.write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8"
        )
    finally:
        world.close()


if __name__ == "__main__":
    main()
