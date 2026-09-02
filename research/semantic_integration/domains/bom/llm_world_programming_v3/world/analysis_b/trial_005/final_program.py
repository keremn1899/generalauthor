#!/usr/bin/env python3
"""Compute qualification bottlenecks from the compiled semantic World."""

from __future__ import annotations

import json
from pathlib import Path

from world_surface import open_world


ROOT = Path(__file__).resolve().parent
OUTPUT_PATH = ROOT / "output.json"


def require_complete(world, relation: str) -> None:
    """Ensure absence from a derived relation can safely be read as false."""
    receipt = world.latest_completeness(relation)
    if (
        receipt is None
        or receipt.get("status") != "COMPLETE"
        or not receipt.get("current")
        or receipt.get("stale")
    ):
        raise RuntimeError(
            f"{relation} does not have a current COMPLETE derivation receipt"
        )


def main() -> None:
    world = open_world()
    try:
        require_complete(world, "voltage_compatible")
        require_complete(world, "temperature_compatible")

        # A candidate pair is relevant to BOM items requiring the old part's
        # represented type. Each item's deployment environment supplies context.
        rows = world.query_semantic(
            """
            SELECT
                cr.new_part_id AS new_part,
                cr.old_part_id AS old_part,
                rt.bom_item_id AS bom_item,
                de.environment_id AS context,
                CASE WHEN vc.part_id IS NULL THEN 0 ELSE 1 END
                    AS voltage_compatible,
                CASE WHEN tc.part_id IS NULL THEN 0 ELSE 1 END
                    AS temperature_compatible,
                nl.state AS new_lifecycle,
                ol.state AS old_lifecycle,
                CASE WHEN ar.new_part_id IS NULL THEN 0 ELSE 1 END
                    AS semantically_accepted
            FROM candidate_replacement AS cr
            JOIN part_type AS opt
              ON opt.part_id = cr.old_part_id
            JOIN requires_type AS rt
              ON rt.part_type = opt.part_type
            JOIN deployment_environment AS de
              ON de.bom_item_id = rt.bom_item_id
            LEFT JOIN voltage_compatible AS vc
              ON vc.part_id = cr.new_part_id
             AND vc.bom_item_id = rt.bom_item_id
            LEFT JOIN temperature_compatible AS tc
              ON tc.part_id = cr.new_part_id
             AND tc.bom_item_id = rt.bom_item_id
            LEFT JOIN lifecycle AS nl
              ON nl.part_id = cr.new_part_id
            LEFT JOIN lifecycle AS ol
              ON ol.part_id = cr.old_part_id
            LEFT JOIN acceptable_replacement AS ar
              ON ar.new_part_id = cr.new_part_id
             AND ar.old_part_id = cr.old_part_id
             AND ar.context_id = de.environment_id
            ORDER BY
                cr.new_part_id,
                cr.old_part_id,
                rt.bom_item_id,
                de.environment_id
            """
        )

        unresolved = {
            (
                obligation["values"].get("new_part"),
                obligation["values"].get("old_part"),
                obligation["values"].get("context"),
            )
            for obligation in world.obligations()
            if obligation.get("relation") == "acceptable_replacement"
        }

        cases = []
        for row in rows:
            voltage_ok = bool(row["voltage_compatible"])
            temperature_ok = bool(row["temperature_compatible"])
            new_lifecycle = row["new_lifecycle"]
            lifecycle_active = new_lifecycle == "active"
            lifecycle_known = new_lifecycle is not None

            semantic_key = (
                row["new_part"],
                row["old_part"],
                row["context"],
            )
            if row["semantically_accepted"]:
                semantic_state = "accepted"
            elif semantic_key in unresolved:
                semantic_state = "unresolved"
            else:
                semantic_state = "not_established"

            prevents = []
            uncertain = []
            if not voltage_ok:
                prevents.append("voltage_compatible")
            if not temperature_ok:
                prevents.append("temperature_compatible")
            if not lifecycle_active:
                if lifecycle_known:
                    prevents.append("lifecycle_active")
                else:
                    uncertain.append("lifecycle_active")
            if semantic_state != "accepted":
                uncertain.append("semantic_acceptance")

            cases.append(
                {
                    "new_part": row["new_part"],
                    "old_part": row["old_part"],
                    "bom_item": row["bom_item"],
                    "context": row["context"],
                    "voltage_compatible": voltage_ok,
                    "temperature_compatible": temperature_ok,
                    "new_part_lifecycle_active": lifecycle_active,
                    "old_part_lifecycle": row["old_lifecycle"] or "unknown",
                    "semantic_state": semantic_state,
                    "prevents_viability": prevents,
                    "leaves_viability_uncertain": uncertain,
                }
            )

        result = {"task": "qualification_bottlenecks", "cases": cases}
        OUTPUT_PATH.write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8"
        )
    finally:
        world.close()


if __name__ == "__main__":
    main()
