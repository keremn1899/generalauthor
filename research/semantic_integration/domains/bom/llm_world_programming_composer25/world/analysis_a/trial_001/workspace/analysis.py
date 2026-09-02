#!/usr/bin/env python3
"""Analyze replacement candidate state from the compiled semantic World."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from world_surface import open_world

ROOT = Path(__file__).resolve().parent
OUTPUT_PATH = ROOT / "output.json"


def _group_cases(world) -> list[dict]:
    """Build candidate/context cases from World relations."""

    rows = world.query_semantic(
        """
        WITH old_bom AS (
            SELECT vc.part_id AS old_part_id, vc.bom_item_id
            FROM voltage_compatible AS vc
            JOIN temperature_compatible AS tc
              ON tc.part_id = vc.part_id
             AND tc.bom_item_id = vc.bom_item_id
        )
        SELECT cr.new_part_id AS new_part,
               cr.old_part_id AS old_part,
               de.environment_id AS context,
               de.bom_item_id AS bom_item
        FROM candidate_replacement AS cr
        JOIN old_bom AS ob ON ob.old_part_id = cr.old_part_id
        JOIN deployment_environment AS de ON de.bom_item_id = ob.bom_item_id
        ORDER BY cr.new_part_id, cr.old_part_id, de.environment_id, de.bom_item_id
        """
    )

    grouped: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    for row in rows:
        key = (row["new_part"], row["old_part"], row["context"])
        grouped[key].append(row["bom_item"])

    eligible = {
        (row["part_id"], row["bom_item_id"])
        for row in world.query_semantic("SELECT part_id, bom_item_id FROM eligible_part")
    }

    accepted = {
        (row["new_part_id"], row["old_part_id"], row["context_id"])
        for row in world.query_semantic(
            "SELECT new_part_id, old_part_id, context_id FROM acceptable_replacement"
        )
    }

    obligations = {
        (
            ob["values"]["new_part"],
            ob["values"]["old_part"],
            ob["values"]["context"],
        )
        for ob in world.obligations()
        if ob.get("relation") == "acceptable_replacement"
    }

    cases: list[dict] = []
    for (new_part, old_part, context), bom_items in sorted(grouped.items()):
        bom_items_sorted = sorted(bom_items)
        mechanically_suitable = all(
            (new_part, bom_item) in eligible for bom_item in bom_items_sorted
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
                "bom_items": bom_items_sorted,
                "mechanical_state": "suitable" if mechanically_suitable else "unsuitable",
                "semantic_state": semantic_state,
                "epistemic": epistemic,
            }
        )

    return cases


def _build_support(world) -> list[dict]:
    """Trace one accepted case to authoritative source evidence."""

    trace_case = {
        "new_part": "part:R210",
        "old_part": "part:R200",
        "context": "context:high_vibration_cabinet",
    }
    detail = world.inspect_tuple("acceptable_replacement", trace_case)
    if detail is None:
        return []

    claim = (
        f"{trace_case['new_part']} is an acceptable replacement for "
        f"{trace_case['old_part']} in {trace_case['context']}"
    )

    evidence: list[dict[str, str]] = []
    for pointer in detail.get("grounding", []):
        if pointer.get("kind") != "SOURCE":
            continue
        reference = pointer.get("reference", "")
        source = reference.split("@", 1)[0] if reference else ""
        locator = ""
        detail_text = pointer.get("detail", "")
        if detail_text:
            try:
                parsed = json.loads(detail_text)
                locator = parsed.get("native_location", "")
            except json.JSONDecodeError:
                locator = detail_text
        if source:
            evidence.append({"source": source, "locator": locator})

    return [{"claim": claim, "evidence": evidence}]


def main() -> None:
    world = open_world()
    try:
        result = {
            "task": "replacement_state",
            "cases": _group_cases(world),
            "support": _build_support(world),
        }
    finally:
        world.close()

    OUTPUT_PATH.write_text(
        json.dumps(result, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
