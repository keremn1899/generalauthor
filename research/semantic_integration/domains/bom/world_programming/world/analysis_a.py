"""WORLD A: replacement-case state from compiled relations and obligation state."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from research.semantic_integration.core.kernel import SemanticWorld
from research.semantic_integration.domains.bom.world_programming.relation_rows import (
    relation_rows,
)


def demanded_replacement_cases(world: SemanticWorld) -> list[dict[str, str]]:
    return world.query_semantic(
        """
        SELECT DISTINCT
            cr.new_part_id AS new_part,
            cr.old_part_id AS old_part,
            de.environment_id AS context,
            de.bom_item_id AS bom_item
        FROM candidate_replacement AS cr
        JOIN part_type AS new_type ON new_type.part_id = cr.new_part_id
        JOIN part_type AS old_type
          ON old_type.part_id = cr.old_part_id
         AND old_type.part_type = new_type.part_type
        JOIN requires_type AS required
          ON required.part_type = new_type.part_type
        JOIN deployment_environment AS de
          ON de.bom_item_id = required.bom_item_id
        ORDER BY new_part, old_part, context, bom_item
        """
    )


def run(world: SemanticWorld, obligations: list[dict[str, Any]]) -> dict[str, Any]:
    accepted = {
        (row["new_part_id"], row["old_part_id"], row["context_id"])
        for row in relation_rows(world, "acceptable_replacement")
    }
    unresolved = {
        (
            item["values"]["new_part"],
            item["values"]["old_part"],
            item["values"]["context"],
        )
        for item in obligations
        if item["relation"] == "acceptable_replacement"
    }
    eligible = {
        (row["part_id"], row["bom_item_id"])
        for row in relation_rows(world, "eligible_part")
    }

    grouped: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    for row in demanded_replacement_cases(world):
        key = (row["new_part"], row["old_part"], row["context"])
        grouped[key].append(row["bom_item"])

    cases: list[dict[str, Any]] = []
    for key, bom_items in grouped.items():
        bom_items = sorted(set(bom_items))
        suitable = all((key[0], bom) in eligible for bom in bom_items)
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
                "new_part": key[0],
                "old_part": key[1],
                "context": key[2],
                "bom_items": bom_items,
                "mechanical_state": "suitable" if suitable else "unsuitable",
                "semantic_state": semantic_state,
                "epistemic": epistemic,
            }
        )
    cases.sort(key=lambda row: (row["new_part"], row["old_part"], row["context"]))
    return {"task": "replacement_state", "cases": cases}


def explain_tuple(
    world: SemanticWorld, relation: str, values: dict[str, str]
) -> dict[str, Any] | None:
    return world.inspect_tuple(relation, values)
