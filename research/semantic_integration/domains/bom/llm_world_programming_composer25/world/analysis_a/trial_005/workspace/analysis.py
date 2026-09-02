#!/usr/bin/env python3
"""Determine replacement candidate state under applicable deployment contexts."""

from __future__ import annotations

import json
from pathlib import Path

from world_surface import open_world

ROOT = Path(__file__).resolve().parent
OUTPUT_PATH = ROOT / "output.json"


def load_cases(world) -> list[dict]:
    """Build candidate/context cases from World relations."""
    rows = world.query_semantic(
        """
        SELECT DISTINCT
            cr.new_part_id AS new_part,
            cr.old_part_id AS old_part,
            de.environment_id AS context
        FROM candidate_replacement AS cr
        JOIN voltage_compatible AS vc
          ON vc.part_id = cr.old_part_id
        JOIN temperature_compatible AS tc
          ON tc.part_id = cr.old_part_id
         AND tc.bom_item_id = vc.bom_item_id
        JOIN deployment_environment AS de
          ON de.bom_item_id = vc.bom_item_id
        ORDER BY cr.new_part_id, cr.old_part_id, de.environment_id
        """
    )

    accepted = {
        (row["new_part_id"], row["old_part_id"], row["context_id"])
        for row in world.query_semantic(
            "SELECT new_part_id, old_part_id, context_id FROM acceptable_replacement"
        )
    }

    obligations = {
        (
            obligation["values"]["new_part"],
            obligation["values"]["old_part"],
            obligation["values"]["context"],
        )
        for obligation in world.obligations()
        if obligation.get("relation") == "acceptable_replacement"
    }

    eligible = {
        (row["part_id"], row["bom_item_id"])
        for row in world.query_semantic("SELECT part_id, bom_item_id FROM eligible_part")
    }

    cases: list[dict] = []
    for row in rows:
        new_part = row["new_part"]
        old_part = row["old_part"]
        context = row["context"]

        bom_items = sorted(
            bom_row["bom_item_id"]
            for bom_row in world.query_semantic(
                """
                SELECT de.bom_item_id
                FROM deployment_environment AS de
                JOIN voltage_compatible AS vc
                  ON vc.bom_item_id = de.bom_item_id
                 AND vc.part_id = ?
                JOIN temperature_compatible AS tc
                  ON tc.bom_item_id = de.bom_item_id
                 AND tc.part_id = ?
                WHERE de.environment_id = ?
                """,
                (old_part, old_part, context),
            )
        )

        mechanical_state = (
            "suitable"
            if bom_items
            and all((new_part, bom_item) in eligible for bom_item in bom_items)
            else "unsuitable"
        )

        key = (new_part, old_part, context)
        if key in accepted:
            semantic_state = "accepted"
            epistemic = "ASSERTED_TRUE"
        elif key in obligations:
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
                "mechanical_state": mechanical_state,
                "semantic_state": semantic_state,
                "epistemic": epistemic,
            }
        )

    return cases


def build_support(world, case: dict) -> list[dict]:
    """Trace one case to authoritative evidence via tuple inspection."""
    detail = world.inspect_tuple(
        "acceptable_replacement",
        {
            "new_part": case["new_part"],
            "old_part": case["old_part"],
            "context": case["context"],
        },
    )
    if detail is None:
        return []

    claim = (
        f"{case['new_part']} is an acceptable replacement for "
        f"{case['old_part']} in {case['context']}"
    )
    evidence: list[dict] = []
    for pointer in detail.get("grounding", []):
        if pointer.get("kind") != "SOURCE":
            continue
        detail_json = json.loads(pointer.get("detail") or "{}")
        evidence.append(
            {
                "source": detail_json.get("native_handle") or pointer.get("reference", ""),
                "locator": detail_json.get("native_location") or pointer.get("reference", ""),
            }
        )
    return [{"claim": claim, "evidence": evidence}] if evidence else []


def main() -> None:
    world = open_world()
    try:
        cases = load_cases(world)
        support_case = next(
            (case for case in cases if case["semantic_state"] == "accepted"),
            cases[0] if cases else None,
        )
        support = build_support(world, support_case) if support_case else []
        result = {
            "task": "replacement_state",
            "cases": cases,
            "support": support,
        }
    finally:
        world.close()

    OUTPUT_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
