#!/usr/bin/env python3
"""Compute replacement state from the compiled semantic World."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from world_surface import open_world, relation_rows


ROOT = Path(__file__).resolve().parent


def tuples(rows: list[dict[str, Any]], *columns: str) -> set[tuple[str, ...]]:
    return {tuple(str(row[column]) for column in columns) for row in rows}


def direct_evidence(detail: dict[str, Any] | None) -> list[dict[str, str]]:
    """Convert authoritative SOURCE grounding pointers to the requested shape."""
    evidence: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    if not detail:
        return evidence

    for grounding in detail.get("grounding", []):
        if grounding.get("kind") != "SOURCE":
            continue
        try:
            metadata = json.loads(grounding.get("detail") or "{}")
        except json.JSONDecodeError:
            metadata = {}

        source = metadata.get("native_handle") or metadata.get("source")
        locator = (
            metadata.get("native_location")
            or metadata.get("source_native_location")
        )
        if not source:
            source = str(grounding.get("reference", ""))
        if not locator:
            locator = str(grounding.get("reference", ""))

        key = (str(source), str(locator))
        if key not in seen:
            seen.add(key)
            evidence.append({"source": key[0], "locator": key[1]})

    return evidence


def main() -> None:
    world = open_world()
    try:
        candidates = relation_rows(world, "candidate_replacement")
        deployments = relation_rows(world, "deployment_environment")
        temperature = tuples(
            relation_rows(world, "temperature_compatible"),
            "part_id",
            "bom_item_id",
        )
        voltage = tuples(
            relation_rows(world, "voltage_compatible"),
            "part_id",
            "bom_item_id",
        )
        eligible = tuples(
            relation_rows(world, "eligible_part"), "part_id", "bom_item_id"
        )
        accepted = tuples(
            relation_rows(world, "acceptable_replacement"),
            "new_part_id",
            "old_part_id",
            "context_id",
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

        cases: list[dict[str, Any]] = []
        for candidate in candidates:
            new_part = str(candidate["new_part_id"])
            old_part = str(candidate["old_part_id"])

            # Compatibility relations include the required part-type join.
            # Their intersection identifies BOM uses to which the old part,
            # and therefore this replacement candidate, applies. Lifecycle is
            # intentionally excluded so discontinued old parts remain relevant.
            applicable_boms = {
                bom
                for part, bom in temperature & voltage
                if part == old_part
            }
            boms_by_context: dict[str, list[str]] = defaultdict(list)
            for deployment in deployments:
                bom = str(deployment["bom_item_id"])
                if bom in applicable_boms:
                    boms_by_context[str(deployment["environment_id"])].append(bom)

            for context, bom_items in boms_by_context.items():
                bom_items.sort()
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

                cases.append(
                    {
                        "new_part": new_part,
                        "old_part": old_part,
                        "context": context,
                        "bom_items": bom_items,
                        "mechanical_state": (
                            "suitable"
                            if all((new_part, bom) in eligible for bom in bom_items)
                            else "unsuitable"
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
                if (
                    case["new_part"],
                    case["old_part"],
                    case["context"],
                )
                in accepted
            ),
            None,
        )
        if supported_case:
            values = {
                "new_part": supported_case["new_part"],
                "old_part": supported_case["old_part"],
                "context": supported_case["context"],
            }
            detail = world.inspect_tuple("acceptable_replacement", values)
            evidence = direct_evidence(detail)
            support.append(
                {
                    "claim": (
                        f'{supported_case["new_part"]} is an accepted replacement '
                        f'for {supported_case["old_part"]} in '
                        f'{supported_case["context"]}'
                    ),
                    "evidence": evidence,
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
