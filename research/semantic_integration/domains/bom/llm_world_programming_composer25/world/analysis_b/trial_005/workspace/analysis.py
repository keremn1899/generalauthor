#!/usr/bin/env python3
"""Qualification bottleneck analysis over the compiled semantic World."""

from __future__ import annotations

import json
from pathlib import Path

from world_surface import open_world, relation_rows

ROOT = Path(__file__).resolve().parent
OUTPUT_PATH = ROOT / "output.json"

CONSTRAINT_VOLTAGE = "voltage_compatible"
CONSTRAINT_TEMPERATURE = "temperature_compatible"
CONSTRAINT_LIFECYCLE = "lifecycle_active"
CONSTRAINT_SEMANTIC = "semantic_acceptance"


def _index_pairs(rows: list[dict[str, str]], *keys: str) -> set[tuple[str, ...]]:
    return {tuple(row[key] for key in keys) for row in rows}


def _bom_items_for_part(
    part_id: str,
    voltage_pairs: set[tuple[str, str]],
    temperature_pairs: set[tuple[str, str]],
    eligible_pairs: set[tuple[str, str]],
) -> set[str]:
    bom_items: set[str] = set()
    for part, bom_item in voltage_pairs | temperature_pairs | eligible_pairs:
        if part == part_id:
            bom_items.add(bom_item)
    return bom_items


def _derivation_complete(world, relation: str) -> bool:
    receipt = world.latest_completeness(relation)
    return receipt is not None and receipt.get("status") == "COMPLETE"


def _semantic_state(
    new_part: str,
    old_part: str,
    context: str,
    accepted: set[tuple[str, str, str]],
    obligations: list[dict],
) -> str:
    if (new_part, old_part, context) in accepted:
        return "accepted"
    for obligation in obligations:
        values = obligation.get("values", {})
        if (
            values.get("new_part") == new_part
            and values.get("old_part") == old_part
            and values.get("context") == context
        ):
            return "unresolved"
    return "not_established"


def main() -> None:
    world = open_world()
    try:
        candidates = relation_rows(world, "candidate_replacement")
        deployment = relation_rows(world, "deployment_environment")
        voltage_rows = relation_rows(world, "voltage_compatible")
        temperature_rows = relation_rows(world, "temperature_compatible")
        eligible_rows = relation_rows(world, "eligible_part")
        lifecycle_rows = relation_rows(world, "lifecycle")
        acceptable_rows = relation_rows(world, "acceptable_replacement")
        obligations = world.obligations()

        context_by_bom = {
            row["bom_item_id"]: row["environment_id"] for row in deployment
        }
        voltage_pairs = _index_pairs(voltage_rows, "part_id", "bom_item_id")
        temperature_pairs = _index_pairs(
            temperature_rows, "part_id", "bom_item_id"
        )
        eligible_pairs = _index_pairs(eligible_rows, "part_id", "bom_item_id")
        accepted = _index_pairs(
            acceptable_rows, "new_part_id", "old_part_id", "context_id"
        )
        lifecycle = {row["part_id"]: row["state"] for row in lifecycle_rows}

        voltage_complete = _derivation_complete(world, "voltage_compatible")
        temperature_complete = _derivation_complete(world, "temperature_compatible")

        cases: list[dict] = []

        for candidate in candidates:
            new_part = candidate["new_part_id"]
            old_part = candidate["old_part_id"]
            relevant_boms = _bom_items_for_part(
                old_part, voltage_pairs, temperature_pairs, eligible_pairs
            )

            for bom_item in sorted(relevant_boms):
                context = context_by_bom[bom_item]

                voltage_ok = (new_part, bom_item) in voltage_pairs
                temperature_ok = (new_part, bom_item) in temperature_pairs
                new_lifecycle = lifecycle.get(new_part, "")
                new_lifecycle_active = new_lifecycle == "active"
                old_lifecycle = lifecycle.get(old_part, "")

                semantic = _semantic_state(
                    new_part, old_part, context, accepted, obligations
                )

                prevents: list[str] = []
                uncertain: list[str] = []

                if voltage_complete and not voltage_ok:
                    prevents.append(CONSTRAINT_VOLTAGE)
                if temperature_complete and not temperature_ok:
                    prevents.append(CONSTRAINT_TEMPERATURE)
                if not new_lifecycle_active:
                    prevents.append(CONSTRAINT_LIFECYCLE)
                if semantic == "unresolved":
                    uncertain.append(CONSTRAINT_SEMANTIC)

                cases.append(
                    {
                        "new_part": new_part,
                        "old_part": old_part,
                        "bom_item": bom_item,
                        "context": context,
                        "voltage_compatible": voltage_ok,
                        "temperature_compatible": temperature_ok,
                        "new_part_lifecycle_active": new_lifecycle_active,
                        "old_part_lifecycle": old_lifecycle,
                        "semantic_state": semantic,
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

        result = {"task": "qualification_bottlenecks", "cases": cases}
        OUTPUT_PATH.write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8"
        )
    finally:
        world.close()


if __name__ == "__main__":
    main()
