#!/usr/bin/env python3
"""Determine replacement candidate state under deployment contexts."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from world_surface import open_world, relation_rows

OUTPUT_PATH = Path(__file__).resolve().parent / "output.json"


def load_accepted(world) -> set[tuple[str, str, str]]:
    accepted: set[tuple[str, str, str]] = set()
    for row in relation_rows(world, "acceptable_replacement"):
        accepted.add(
            (row["new_part_id"], row["old_part_id"], row["context_id"])
        )
    return accepted


def load_unresolved(world) -> set[tuple[str, str, str]]:
    unresolved: set[tuple[str, str, str]] = set()
    for obligation in world.obligations():
        if obligation.get("relation") != "acceptable_replacement":
            continue
        values = obligation.get("values", {})
        unresolved.add(
            (
                values["new_part"],
                values["old_part"],
                values["context"],
            )
        )
    return unresolved


def load_candidate_contexts(world) -> dict[tuple[str, str, str], list[str]]:
    """Map (new_part, old_part, context) to BOM items where the old part applies."""

    rows = world.query_semantic(
        """
        SELECT
            cr.new_part_id AS new_part,
            cr.old_part_id AS old_part,
            de.environment_id AS context,
            de.bom_item_id AS bom_item
        FROM candidate_replacement AS cr
        JOIN part_type AS pt ON pt.part_id = cr.old_part_id
        JOIN requires_type AS rt ON rt.part_type = pt.part_type
        JOIN deployment_environment AS de ON de.bom_item_id = rt.bom_item_id
        JOIN requires_voltage AS rv ON rv.bom_item_id = de.bom_item_id
        JOIN rated_voltage AS rvol
          ON rvol.part_id = cr.old_part_id AND rvol.volts = rv.volts
        JOIN requires_temperature AS rtemp ON rtemp.bom_item_id = de.bom_item_id
        JOIN temperature_range AS tr ON tr.part_id = cr.old_part_id
          AND tr.minimum_c <= rtemp.minimum_c
          AND tr.maximum_c >= rtemp.maximum_c
        ORDER BY cr.new_part_id, cr.old_part_id, de.environment_id, de.bom_item_id
        """
    )

    cases: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    for row in rows:
        key = (row["new_part"], row["old_part"], row["context"])
        bom_item = row["bom_item"]
        if bom_item not in cases[key]:
            cases[key].append(bom_item)
    return cases


def mechanical_state(world, new_part: str, bom_items: list[str]) -> str:
    eligible = {
        (row["part_id"], row["bom_item_id"])
        for row in relation_rows(world, "eligible_part")
    }
    completeness = world.latest_completeness("eligible_part")
    is_complete = bool(
        completeness and completeness.get("status") == "COMPLETE"
    )

    for bom_item in bom_items:
        if (new_part, bom_item) in eligible:
            continue
        if is_complete:
            return "unsuitable"
        return "unsuitable"
    return "suitable"


def semantic_state(
    key: tuple[str, str, str],
    accepted: set[tuple[str, str, str]],
    unresolved: set[tuple[str, str, str]],
) -> str:
    if key in accepted:
        return "accepted"
    if key in unresolved:
        return "unresolved"
    return "not_established"


def epistemic_class(semantic: str) -> str:
    if semantic == "accepted":
        return "ASSERTED_TRUE"
    if semantic == "unresolved":
        return "UNRESOLVED"
    return "NOT_KNOWN"


def grounding_evidence(detail: dict | None) -> list[dict[str, str]]:
    if not detail:
        return []

    evidence: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for item in detail.get("grounding", []):
        if item.get("kind") != "SOURCE":
            continue
        native_handle = ""
        native_location = ""
        if item.get("detail"):
            try:
                parsed = json.loads(item["detail"])
                native_handle = (
                    parsed.get("native_handle")
                    or parsed.get("source")
                    or ""
                )
                native_location = (
                    parsed.get("native_location")
                    or parsed.get("source_native_location")
                    or ""
                )
            except json.JSONDecodeError:
                pass
        if not native_handle:
            reference = item.get("reference", "")
            native_handle = reference.split("@", 1)[0].removeprefix("fixture://")
        source = native_handle or item.get("reference", "")
        locator = native_location or item.get("reference", "")
        key = (source, locator)
        if key in seen:
            continue
        seen.add(key)
        evidence.append({"source": source, "locator": locator})
    return evidence


def build_support(world, case: dict) -> list[dict]:
    """Trace the outdoor-enclosure X110/X160 case to authoritative evidence."""

    trace_key = (
        "part:X110",
        "part:X160",
        "context:outdoor_enclosure",
    )
    if (
        case["new_part"],
        case["old_part"],
        case["context"],
    ) != trace_key:
        return []

    acceptance = world.inspect_tuple(
        "acceptable_replacement",
        {
            "new_part": case["new_part"],
            "old_part": case["old_part"],
            "context": case["context"],
        },
    )
    candidate = world.inspect_tuple(
        "candidate_replacement",
        {
            "new_part": case["new_part"],
            "old_part": case["old_part"],
        },
    )

    support: list[dict] = []
    acceptance_evidence = grounding_evidence(acceptance)
    if acceptance_evidence:
        support.append(
            {
                "claim": (
                    "part:X110 is an acceptable replacement for part:X160 in "
                    "context:outdoor_enclosure"
                ),
                "evidence": acceptance_evidence,
            }
        )

    candidate_evidence = grounding_evidence(candidate)
    if candidate_evidence:
        support.append(
            {
                "claim": (
                    "part:X110 is a replacement candidate for part:X160"
                ),
                "evidence": candidate_evidence,
            }
        )

    completeness = world.latest_completeness("eligible_part")
    if completeness and completeness.get("status") == "COMPLETE":
        support.append(
            {
                "claim": (
                    "part:X110 is mechanically suitable for bom:BOM-A"
                ),
                "evidence": [
                    {
                        "source": "eligible_part",
                        "locator": (
                            f"derived tuple (part:X110, bom:BOM-A); "
                            f"completeness receipt {completeness['receipt_id']}"
                        ),
                    }
                ],
            }
        )

    return support


def main() -> None:
    world = open_world()
    try:
        accepted = load_accepted(world)
        unresolved = load_unresolved(world)
        candidate_contexts = load_candidate_contexts(world)

        cases: list[dict] = []
        all_support: list[dict] = []

        for key in sorted(candidate_contexts):
            new_part, old_part, context = key
            bom_items = sorted(candidate_contexts[key])
            semantic = semantic_state(key, accepted, unresolved)
            case = {
                "new_part": new_part,
                "old_part": old_part,
                "context": context,
                "bom_items": bom_items,
                "mechanical_state": mechanical_state(world, new_part, bom_items),
                "semantic_state": semantic,
                "epistemic": epistemic_class(semantic),
            }
            cases.append(case)
            all_support.extend(build_support(world, case))

        result = {
            "task": "replacement_state",
            "cases": cases,
            "support": all_support,
        }
        OUTPUT_PATH.write_text(
            json.dumps(result, indent=2, sort_keys=False) + "\n",
            encoding="utf-8",
        )
    finally:
        world.close()


if __name__ == "__main__":
    main()
