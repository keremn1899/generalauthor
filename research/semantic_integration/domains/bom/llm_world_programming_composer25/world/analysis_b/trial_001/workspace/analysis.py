#!/usr/bin/env python3
"""Qualification bottleneck analysis over the compiled semantic World."""

from __future__ import annotations

import json
from pathlib import Path

from world_surface import open_world, relation_rows


def _index_by(rows: list[dict], *keys: str) -> set[tuple]:
    return {tuple(row[k] for k in keys) for row in rows}


def _map_by(rows: list[dict], key: str, value: str) -> dict:
    return {row[key]: row[value] for row in rows}


def main() -> None:
    world = open_world()
    try:
        candidates = relation_rows(world, "candidate_replacement")
        deployments = relation_rows(world, "deployment_environment")
        part_types = _map_by(relation_rows(world, "part_type"), "part_id", "part_type")
        bom_requires_type = _map_by(
            relation_rows(world, "requires_type"), "bom_item_id", "part_type"
        )
        voltage_ok = _index_by(relation_rows(world, "voltage_compatible"), "part_id", "bom_item_id")
        temp_ok = _index_by(
            relation_rows(world, "temperature_compatible"), "part_id", "bom_item_id"
        )
        lifecycle = _map_by(relation_rows(world, "lifecycle"), "part_id", "state")
        accepted = _index_by(
            relation_rows(world, "acceptable_replacement"),
            "new_part_id",
            "old_part_id",
            "context_id",
        )
        obligations = world.obligations()
        unresolved_semantic = {
            (o["values"]["new_part"], o["values"]["old_part"], o["values"]["context"])
            for o in obligations
            if o.get("relation") == "acceptable_replacement"
        }

        cases: list[dict] = []

        for candidate in candidates:
            new_part = candidate["new_part_id"]
            old_part = candidate["old_part_id"]
            old_type = part_types.get(old_part)

            for deployment in deployments:
                bom_item = deployment["bom_item_id"]
                context = deployment["environment_id"]

                if bom_requires_type.get(bom_item) != old_type:
                    continue

                voltage_compatible = (new_part, bom_item) in voltage_ok
                temperature_compatible = (new_part, bom_item) in temp_ok
                new_part_lifecycle_active = lifecycle.get(new_part) == "active"
                old_part_lifecycle = lifecycle.get(old_part, "unknown")

                semantic_key = (new_part, old_part, context)
                if semantic_key in accepted:
                    semantic_state = "accepted"
                elif semantic_key in unresolved_semantic:
                    semantic_state = "unresolved"
                else:
                    semantic_state = "not_established"

                prevents_viability: list[str] = []
                leaves_viability_uncertain: list[str] = []

                if not voltage_compatible:
                    prevents_viability.append("voltage_compatible")
                if not temperature_compatible:
                    prevents_viability.append("temperature_compatible")
                if not new_part_lifecycle_active:
                    prevents_viability.append("lifecycle_active")
                if semantic_state == "unresolved":
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
                        "old_part_lifecycle": old_part_lifecycle,
                        "semantic_state": semantic_state,
                        "prevents_viability": prevents_viability,
                        "leaves_viability_uncertain": leaves_viability_uncertain,
                    }
                )

        cases.sort(key=lambda c: (c["new_part"], c["old_part"], c["bom_item"], c["context"]))

        result = {"task": "qualification_bottlenecks", "cases": cases}
    finally:
        world.close()

    output_path = Path(__file__).resolve().parent / "output.json"
    output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
